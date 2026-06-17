#!/usr/bin/env python
# *****************************************************************************
# Copyright (c) 2024, 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

import sys
import logging
import logging.handlers
from prompt_toolkit import prompt, print_formatted_text, HTML
from prompt_toolkit.completion import WordCompleter

from halo import Halo

from ..cli import BaseApp
from ..validators import InstanceIDValidator
from .argParser import upgradeArgParser
from .settings import UpgradeSettingsMixin

from mas.devops.ocp import createNamespace
from mas.devops.mas import (
    listMasInstances,
    getMasChannel,
    getAppsSubscriptionChannel,
    getWorkspaceId,
    verifyAppInstance,
    getPermissionMode,
    getInstalledApps,
)
from mas.devops.utils import isVersionEqualOrAfter
from mas.devops.tekton import installOpenShiftPipelines, updateTektonDefinitions, launchUpgradePipeline
from mas.devops.pre_install import applyPreInstallMASRBAC
from ..rbac_utils import evaluatePreinstallRBACAccess

logger = logging.getLogger(__name__)


class UpgradeApp(BaseApp, UpgradeSettingsMixin):
    def computeMonitorInstallOrderForUpgrade(self, instanceId):
        """
        Determine the installation order for Monitor relative to IoT based on TARGET Monitor version.
        This is needed for upgrade scenarios where Monitor >= 9.2.0 must upgrade before IoT.
        For upgrades, we check the TARGET channel (where we're going), not current channel.
        """
        installedApps = getAppsSubscriptionChannel(self.dynamicClient, instanceId)
        hasMonitor = False
        hasIoT = False

        for app in installedApps:
            if app["appId"] == "monitor":
                hasMonitor = True
            elif app["appId"] == "iot":
                hasIoT = True

        if hasMonitor and hasIoT:
            # For upgrade, check the TARGET channel (self.nextChannel), not current channel
            # If upgrading TO 9.2.x or higher, Monitor must upgrade before IoT
            if self.nextChannel and isVersionEqualOrAfter("9.2.0", self.nextChannel):
                # Upgrading to Monitor >= 9.2.0: Monitor must upgrade before IoT
                self.setParam("mas_monitor_install_order", "before-iot")
                logger.debug(f"Upgrading to MAS {self.nextChannel} (>= 9.2.0): Monitor will upgrade before IoT")
            else:
                # Upgrading to Monitor < 9.2.0: Monitor upgrades after IoT (legacy)
                self.setParam("mas_monitor_install_order", "after-iot")
                logger.debug(f"Upgrading to MAS {self.nextChannel} (< 9.2.0): Monitor will upgrade after IoT (legacy behavior)")
        elif hasMonitor:
            # Only Monitor, no IoT - order doesn't matter but set default
            self.setParam("mas_monitor_install_order", "before-iot")
        else:
            # No Monitor installed - set default
            self.setParam("mas_monitor_install_order", "after-iot")

    def validateKafkaForCivilUpgrade(self, instanceId):
        """
        Validate Kafka requirements when upgrading Manage with Civil to 9.2+.
        Civil >= 9.2 requires Kafka configuration.
        Warns user and gives option to proceed without Kafka (Defect Detection will not function).
        """
        # Check if upgrading TO Manage 9.2+ (use TARGET channel, not current)
        if not self.nextChannel or not isVersionEqualOrAfter("9.2.0", self.nextChannel):
            return

        # Query the ManageWorkspace CR to check if Civil component is installed
        workspaceId = getWorkspaceId(self.dynamicClient, instanceId)
        if not workspaceId:
            logger.debug("Could not determine workspace ID, skipping Civil Kafka validation")
            return

        try:
            # Query ManageWorkspace CR
            workspaceAPI = self.dynamicClient.resources.get(api_version="apps.mas.ibm.com/v1", kind="ManageWorkspace")
            workspace = workspaceAPI.get(name=f"{instanceId}-{workspaceId}", namespace=f"mas-{instanceId}-manage")

            # Check if Civil component is in the workspace spec
            components = workspace.get("spec", {}).get("components", {})
            hasCivil = "civil" in components

            if hasCivil:
                logger.debug(f"Civil component detected, upgrading to {self.nextChannel} (>= 9.2.0): Kafka required")

                # Validate Kafka configuration exists
                kafkaAction = self.getParam("kafka_action_system")
                hasKafkaConfig = kafkaAction in ["install", "byo"]

                if not hasKafkaConfig:
                    # Warn user but give option to proceed
                    print_formatted_text(HTML("<Yellow>⚠ Warning: Kafka Configuration Required</Yellow>"))
                    print_formatted_text(
                        HTML(
                            f"<LightSlateGrey>Upgrading to Manage {self.nextChannel} with Civil Infrastructure component "
                            "requires Kafka configuration. Civil versions >= 9.2.0 require a shared system-scope Kafka instance.</LightSlateGrey>"
                        )
                    )
                    print_formatted_text(
                        HTML(
                            "<LightSlateGrey>Without Kafka, the Defect Detection functionality within Civil Infrastructure will not work, "
                            "but other Civil and Manage components will continue to function.</LightSlateGrey>"
                        )
                    )
                    print()

                    if self.noConfirm:
                        # In non-interactive mode, log warning and proceed
                        logger.warning(
                            f"Upgrading to Manage {self.nextChannel} with Civil component without Kafka configuration. "
                            "Defect Detection functionality will not work."
                        )
                    else:
                        # In interactive mode, ask user if they want to proceed
                        if not self.yesOrNo("Do you want to proceed with the upgrade without Kafka? (Defect Detection will not work)"):
                            self.fatalError("Upgrade cancelled. Please configure Kafka before upgrading.")

        except Exception as e:
            logger.warning(f"Could not query ManageWorkspace CR for Civil component check: {e}")
            # Don't fail the upgrade if we can't query - let ansible handle it

    def upgrade(self, argv):
        """
        Upgrade MAS instance
        """
        args = upgradeArgParser.parse_args(args=argv)
        instanceId = args.mas_instance_id
        self.noConfirm = args.no_confirm
        self.skipPreCheck = args.skip_pre_check
        self.licenseAccepted = args.accept_license
        self.nextChannel = args.next_channel
        self.devMode = args.dev_mode
        self.applyPreInstallMASRBAC = False
        self.selectedAppsForRBAC = []

        # Set image_pull_policy if provided
        if args.image_pull_policy and args.image_pull_policy != "":
            self.setParam("image_pull_policy", args.image_pull_policy)

        if instanceId is None:
            self.printH1("Set Target OpenShift Cluster")
            # Connect to the target cluster
            self.connect()
        else:
            logger.debug("MAS instance ID is set, so we assume already connected to the desired OCP")
            # Need to lookup target architecture because configDb2 will try to access self.architecture
            self.lookupTargetArchitecture()

        if self.dynamicClient is None:
            print_formatted_text(HTML("<Red>Error: Not successfully connected to a Kubernetes cluster.  See log file for details</Red>"))
            sys.exit(1)

        if instanceId is None:
            # Interactive mode
            self.printH1("Instance Selection")
            print_formatted_text(HTML("<LightSlateGrey>Select a MAS instance to upgrade from the list below:</LightSlateGrey>"))
            suites = listMasInstances(self.dynamicClient)
            suiteOptions = []

            if len(suites) == 0:
                print_formatted_text(HTML("<Red>Error: No MAS instances detected on this cluster</Red>"))
                sys.exit(1)

            for suite in suites:
                print_formatted_text(HTML(f"- <u>{suite['metadata']['name']}</u> v{suite['status']['versions']['reconciled']}"))
                suiteOptions.append(suite["metadata"]["name"])

            suiteCompleter = WordCompleter(suiteOptions)
            print()
            instanceId = prompt(
                HTML("<Yellow>Enter MAS instance ID: </Yellow>"), completer=suiteCompleter, validator=InstanceIDValidator(), validate_while_typing=False
            )

        currentChannel = getMasChannel(self.dynamicClient, instanceId)
        if currentChannel is not None:
            if self.devMode:
                # This is mainly used for the scenario where Manage Foundation would be installed, because core-upgrade does not use the value of nextChannel,
                # it uses a compatibility_matrix object in ansible-devops to determine the next channel, so nextChannel is only informative for core upgrade purposes
                self.nextChannel = prompt(HTML("<Yellow>Custom channel</Yellow> "))
            else:
                if self.nextChannel != "":
                    # --next-channel was explicitly provided by the user
                    if self.nextChannel == currentChannel:
                        # Retry scenario: MAS core already on target channel, but some apps may still be behind
                        print_formatted_text(
                            HTML(
                                f"<LightSlateGrey>Next Channel {self.nextChannel} equals Current MAS Core Channel {currentChannel}. "
                                f"Retrying upgrade to {self.nextChannel} — apps may still need to be upgraded.</LightSlateGrey>"
                            )
                        )
                    elif self.nextChannel == self.upgrade_path.get(currentChannel):
                        # Valid upgrade path: currentChannel -> nextChannel
                        pass
                    else:
                        self.fatalError(f"No upgrade path available from {currentChannel} to {self.nextChannel}")
                else:
                    # No --next-channel given: derive from upgrade_path
                    if currentChannel not in self.upgrade_path:
                        self.fatalError(f"No upgrade available, {instanceId} is already on the latest release {currentChannel}")
                    self.nextChannel = self.upgrade_path[currentChannel]

                # Validate installed apps compatibility with the target channel
                if self.nextChannel in self.compatibilityMatrix:
                    installedAppsChannel = getAppsSubscriptionChannel(self.dynamicClient, instanceId)
                    incompatibleApps = []

                    for installedApp in installedAppsChannel:
                        appId = installedApp["appId"]
                        appChannel = installedApp["channel"]

                        # Check if app is supported in the target channel
                        if appId not in self.compatibilityMatrix[self.nextChannel]:
                            if "feature" in self.nextChannel:
                                incompatibleApps.append(f"  - {appId}: Not available in feature channel {self.nextChannel}")
                            else:
                                incompatibleApps.append(f"  - {appId}: Not supported in {self.nextChannel}")
                        else:
                            # Check if current app channel is compatible with target MAS channel
                            compatibleAppChannels = self.compatibilityMatrix[self.nextChannel][appId]
                            if appChannel not in compatibleAppChannels:
                                incompatibleApps.append(
                                    f"  - {appId} (currently on {appChannel}): Must be on one of {compatibleAppChannels} to upgrade to MAS {self.nextChannel}"
                                )

                    if len(incompatibleApps) > 0:
                        errorMsg = f"Cannot upgrade to {self.nextChannel}. The following apps have compatibility issues:\n" + "\n".join(incompatibleApps)
                        self.fatalError(errorMsg)

        else:
            # We still allow the upgrade to proceed even though we can't detect the MAS instance.  The upgrade may be being
            # queued up to run after install for instance
            currentChannel = "Unknown"
            if self.nextChannel == "":
                self.nextChannel = "Unknown"

        if not self.licenseAccepted and not self.devMode:
            self.printH1("License Terms")
            self.printDescription(["To continue with the upgrade, you must accept the license terms:", self.licenses[self.nextChannel]])

            if self.noConfirm:
                self.fatalError("You must accept the license terms with --accept-license when using the --no-confirm flag")
            else:
                if not self.yesOrNo("Do you accept the license terms"):
                    exit(1)

        # The only scenario where Manage Foundation needs to be installed during an upgrade is from 9.0.x to 9.1.x (if Manage was not already installed in 9.0.x).
        self.setParam("should_install_manage_foundation", "false")
        if self.nextChannel.startswith("9.1") and not verifyAppInstance(self.dynamicClient, instanceId, "manage"):
            self.manageAppName = "Manage foundation"
            self.showAdvancedOptions = False
            self.installIoT = False
            self.installFacilities = False
            self.installManage = True
            self.isManageFoundation = True
            self.printDescription(
                [f"{self.manageAppName} installs the following capabilities: User, Security groups, Application configurator and Mobile configurator."]
            )
            self.printH1("Configure IBM Container Registry")
            self.promptForString("IBM entitlement key", "ibm_entitlement_key", isPassword=True)
            if self.devMode:
                self.promptForString("Artifactory username", "artifactory_username")
                self.promptForString("Artifactory token", "artifactory_token", isPassword=True)
            self.setParam("should_install_manage_foundation", "true")
            self.setParam("mas_appws_components", "")
            self.setParam("mas_app_settings_aio_flag", "false")
            self.setParam("mas_app_channel_manage", self.nextChannel)
            self.setParam("mas_workspace_id", getWorkspaceId(self.dynamicClient, instanceId))
            # It has been decided that we don't need to ask for any specific Manage Settings
            # self.manageSettings()
            self.configDb2(silentMode=True)

        # Compute Monitor install order for upgrade
        self.computeMonitorInstallOrderForUpgrade(instanceId)

        # Validate Kafka requirements for Civil component during upgrade
        self.validateKafkaForCivilUpgrade(instanceId)

        detectedMode = None

        # Determine admin mode based on upgrade path
        if self.nextChannel and isVersionEqualOrAfter("9.3.0", self.nextChannel) and currentChannel and isVersionEqualOrAfter("9.2.0", currentChannel):
            # Upgrading TO 9.3.x+ FROM 9.2.x+: detect existing permission mode
            logger.info(f"Upgrading from {currentChannel} to {self.nextChannel}: detecting existing permission mode")
            detectedMode = getPermissionMode(self.dynamicClient, instanceId)

        elif self.nextChannel and self.nextChannel.startswith("9.2"):
            # Upgrading TO 9.2.x: default to cluster mode
            # (covers both 9.1.x→9.2.x and 9.2.x-feature→9.2.x)
            logger.info("Upgrading to 9.2.x: defaulting to cluster mode")
            detectedMode = "cluster"

        # Evaluate RBAC access
        if detectedMode:
            self.applyPreInstallMASRBAC = evaluatePreinstallRBACAccess(
                dynamicClient=self.dynamicClient,
                masChannel=self.nextChannel,
                adminMode=detectedMode,
                instanceId=instanceId,
                noConfirm=self.noConfirm,
                printH1Func=self.printH1,
                printDescriptionFunc=self.printDescription,
                yesOrNoFunc=self.yesOrNo,
                fatalErrorFunc=self.fatalError,
                operation="upgrade",
            )

        self.printH1("Review Settings")
        print_formatted_text(HTML(f"<LightSlateGrey>Instance ID ..................... {instanceId}</LightSlateGrey>"))
        print_formatted_text(HTML(f"<LightSlateGrey>Current MAS Channel ............. {currentChannel}</LightSlateGrey>"))
        print_formatted_text(HTML(f"<LightSlateGrey>Next MAS Channel ................ {self.nextChannel}</LightSlateGrey>"))
        print_formatted_text(HTML(f"<LightSlateGrey>Skip Pre-Upgrade Checks ......... {self.skipPreCheck}</LightSlateGrey>"))

        if not self.noConfirm:
            print()
            continueWithUpgrade = self.yesOrNo("Proceed with these settings")

        if self.noConfirm or continueWithUpgrade:
            self.createTektonFileWithDigest()

            self.printH1("Launch Upgrade")
            pipelinesNamespace = f"mas-{instanceId}-pipelines"

            with Halo(text="Validating OpenShift Pipelines installation", spinner=self.spinner) as h:
                successfullyInstalledPipelines = installOpenShiftPipelines(self.dynamicClient)
                if successfullyInstalledPipelines:
                    h.stop_and_persist(symbol=self.successIcon, text="OpenShift Pipelines Operator is installed and ready to use")
                else:
                    h.stop_and_persist(symbol=self.successIcon, text="OpenShift Pipelines Operator installation failed")
                    self.fatalError("Installation failed")

            # Apply pre-install RBAC if user has permissions
            if self.applyPreInstallMASRBAC and detectedMode:
                self.selectedAppsForRBAC = getInstalledApps(self.dynamicClient, instanceId)
                with Halo(text="Applying pre-install MAS RBAC for target version", spinner=self.spinner) as h:
                    applyPreInstallMASRBAC(
                        dynClient=self.dynamicClient,
                        masVersion=".".join(self.nextChannel.split(".")[:2]),
                        masInstanceId=instanceId,
                        adminMode=detectedMode,
                        selectedApps=self.selectedAppsForRBAC,
                    )
                    h.stop_and_persist(
                        symbol=self.successIcon, text=f"Pre-install MAS RBAC applied for target version {self.nextChannel} (mode: {detectedMode})"
                    )

            with Halo(text=f"Preparing namespace ({pipelinesNamespace})", spinner=self.spinner) as h:
                createNamespace(self.dynamicClient, pipelinesNamespace)
                h.stop_and_persist(symbol=self.successIcon, text=f"Namespace is ready ({pipelinesNamespace})")

            with Halo(text=f"Installing latest Tekton definitions (v{self.version})", spinner=self.spinner) as h:
                updateTektonDefinitions(self.dynamicClient, pipelinesNamespace, self.tektonDefsPath)
                h.stop_and_persist(symbol=self.successIcon, text=f"Latest Tekton definitions are installed (v{self.version})")

            with Halo(text="Submitting PipelineRun for {instanceId} upgrade", spinner=self.spinner) as h:
                # Determine masChannel parameter based on scenario:
                # - Regular upgrade: pass currentChannel so ansible looks up the next channel
                # - Retry scenario: pass previous channel so ansible upgrades apps to current channel
                # - No --next-channel: pass empty string to let ansible auto-determine
                if args.next_channel != "" and currentChannel != "Unknown":
                    if self.nextChannel == currentChannel:
                        # Retry scenario: core already on target, apps need upgrading
                        # Find previous channel: which channel has upgrade_path[X] = currentChannel?
                        previousChannel = None
                        for prevCh, nextCh in self.upgrade_path.items():
                            if nextCh == currentChannel:
                                previousChannel = prevCh
                                break
                        # Pass previous channel so ansible upgrades apps from previous to current
                        masChannelParam = previousChannel if previousChannel else currentChannel
                    else:
                        # Regular upgrade with explicit --next-channel
                        masChannelParam = currentChannel
                else:
                    # No --next-channel provided: let ansible auto-determine
                    masChannelParam = ""

                pipelineURL = launchUpgradePipeline(self.dynamicClient, instanceId, self.skipPreCheck, masChannel=masChannelParam, params=self.params)
                if pipelineURL is not None:
                    h.stop_and_persist(symbol=self.successIcon, text=f"PipelineRun for {instanceId} upgrade submitted")
                    print_formatted_text(HTML(f"\nView progress:\n  <Cyan><u>{pipelineURL}</u></Cyan>\n"))
                else:
                    h.stop_and_persist(symbol=self.failureIcon, text=f"Failed to submit PipelineRun for {instanceId} upgrade, see log file for details")
                    print()
