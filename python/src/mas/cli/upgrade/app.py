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
from typing import Callable, Optional
from prompt_toolkit import prompt, print_formatted_text, HTML
from prompt_toolkit.completion import WordCompleter

from halo import Halo

from ..cli import BaseApp
from ..common.commandBuilder import offerCommandScript
from ..validators import InstanceIDValidator, StorageClassValidator
from .argBuilder import upgradeArgBuilderMixin
from .argParser import upgradeArgParser
from .settings import UpgradeSettingsMixin

from mas.devops.ocp import createNamespace, getStorageClasses, getStorageClass
from mas.devops.mas import (
    listMasInstances,
    getMasChannel,
    getAppsSubscriptionChannel,
    getDefaultStorageClasses,
    getWorkspaceId,
    verifyAppInstance,
    getPermissionMode,
    getInstalledApps,
)
from mas.devops.utils import isVersionEqualOrAfter
from mas.devops.tekton import (
    preparePipelinesNamespace,
    installOpenShiftPipelines,
    updateTektonDefinitions,
    launchUpgradePipeline,
    lookupPipelineStorageClass,
    prepareUpgradeSecrets,
)
from mas.devops.pre_install import applyPreInstallMASRBAC
from ..rbac_utils import evaluatePreinstallRBACAccess

logger = logging.getLogger(__name__)


class UpgradeApp(BaseApp, upgradeArgBuilderMixin, UpgradeSettingsMixin):
    """Orchestrator for the ``mas-cli upgrade`` command.

    The ``upgrade()`` method drives both the non-interactive path
    (``--mas-instance-id`` and friends) and the legacy interactive prompt
    path.  The Textual TUI path (``mas-cli upgrade`` with no arguments)
    drives the same logic through the workflow definition in
    ``upgrade/workflow.py`` via ``fetchInstalledInstanceIds``,
    ``prepareUpgrade``, ``prepareManageFoundation`` and ``launchUpgrade``.
    """

    def __init__(self) -> None:
        """Initialise UpgradeApp with safe defaults for all instance variables.

        All attributes read by the TUI execution path (which constructs
        ``UpgradeApp()`` directly without calling ``upgrade()``) are set here.
        The ``upgrade()`` method overwrites these as needed.
        """
        super().__init__()
        self.noConfirm: bool = False
        self.skipPreCheck: bool = False
        self.licenseAccepted: bool = False
        self.devMode: bool = False
        self.isInteractiveMode: bool = False
        self.masInstanceId: Optional[str] = None
        # Channel state populated by prepareUpgrade() on the TUI path (and
        # inline in upgrade() on the CLI path)
        self.nextChannel: str = ""
        self.currentChannel: str = ""
        self.effectiveCurrentChannel: str = ""
        # RBAC state populated by prepareUpgrade() / upgrade() and consumed
        # by launchUpgrade() / the launch section of upgrade()
        self.applyPreInstallMASRBAC: bool = False
        self.selectedAppsForRBAC: list = []
        self.detectedMode: Optional[str] = None
        # Manage Foundation state: isManageFoundation is set by prepareUpgrade()
        # when the 9.0.x -> 9.1.x upgrade needs to install Manage; the
        # install flags and app name are set by prepareManageFoundation()
        # (and inline in upgrade()) for configDb2 to read
        self.isManageFoundation: bool = False
        self.installIoT: bool = False
        self.installMonitor: bool = False
        self.installFacilities: bool = False
        self.installManage: bool = False
        self.manageAppName: Optional[str] = None
        self.showAdvancedOptions: bool = False
        # Pipeline storage class resolved by configPipelineStorageClass()
        self.pipelineStorageClass: Optional[str] = None
        self.pipelineStorageAccessMode: Optional[str] = None

    def prepareUpgrade(self) -> None:
        """Detect the upgrade path and validate compatibility for the selected instance.

        Called as the ``validator`` on the TUI instance-selection step.  Reads
        ``mas_instance_id`` from ``self.params``, then runs the channel
        detection, compatibility validation, Monitor install order, Civil
        Kafka validation, routing-mode pre-flight check, RBAC evaluation,
        and pipeline storage class resolution that the classic ``upgrade()``
        method performs — raising ``RuntimeError`` on failure so the TUI
        displays the error inline and the step does not advance.  License
        acceptance is deliberately not enforced here: the conditional
        license-acceptance step collects it once the target channel is
        known (see ``licenseAcceptancePending``).

        On success, populates ``self.currentChannel``, ``self.nextChannel``,
        ``self.effectiveCurrentChannel``, ``self.detectedMode``,
        ``self.applyPreInstallMASRBAC`` and the pipeline storage class
        attributes so the review screen and ``buildCommand()`` have the right
        data.

        Raises:
            RuntimeError: If the instance is already fully upgraded, the
                upgrade path is invalid, or apps are incompatible with the
                target channel.  License acceptance and the Manage Foundation
                inputs are not enforced here — the conditional
                license-acceptance and manage-foundation steps collect them
                after this validator has run (see ``licenseAcceptancePending``
                and ``manageFoundationPending``).
        """
        instanceId = self.params.get("mas_instance_id", "")
        self.masInstanceId = instanceId

        # The TUI cannot run interactive prompts, so every check below uses
        # its non-interactive variant (matching the classic --no-confirm
        # behaviour).
        self.noConfirm = True

        self.lookupTargetArchitecture()

        currentChannel = getMasChannel(self.dynamicClient, instanceId)
        if currentChannel is not None:
            # Fetch all installed app subscription channels once — used for
            # both channel resolution and compatibility validation below
            installedAppsChannel = getAppsSubscriptionChannel(self.dynamicClient, instanceId)

            if self.nextChannel != "":
                # --next-channel was explicitly provided by the user
                if self.nextChannel == currentChannel:
                    # Retry scenario: MAS core already on target channel, but some apps may still be behind
                    pass
                elif self.nextChannel == self.upgrade_path.get(currentChannel):
                    # Valid upgrade path: currentChannel -> nextChannel
                    pass
                else:
                    raise RuntimeError(f"No upgrade path available from {currentChannel} to {self.nextChannel}")

                # Only block when Core AND every installed app are already on
                # the target channel; if any app is behind, the pipeline
                # launches normally.
                if self.nextChannel == currentChannel and all(app["channel"] == self.nextChannel for app in installedAppsChannel):
                    raise RuntimeError(f"No action required, {instanceId} is already fully upgraded. All components are on channel {self.nextChannel}.")
            else:
                # No --next-channel given: derive from upgrade_path using the
                # oldest channel across Core + all installed apps (see the
                # equivalent block in upgrade() for the rationale).
                allChannels = [currentChannel] + [app["channel"] for app in installedAppsChannel]

                def channelOrder(ch):
                    keys = list(self.upgrade_path.keys())
                    return keys.index(ch) if ch in keys else -1

                self.effectiveCurrentChannel = max(allChannels, key=channelOrder)

                if self.effectiveCurrentChannel not in self.upgrade_path and all(ch == self.effectiveCurrentChannel for ch in allChannels):
                    raise RuntimeError(
                        f"No action required, {instanceId} is already fully upgraded. All components are on channel {self.effectiveCurrentChannel}."
                    )

                if self.effectiveCurrentChannel not in self.upgrade_path:
                    raise RuntimeError(f"No upgrade available, {instanceId} is already on the latest release {self.effectiveCurrentChannel}")

                self.nextChannel = self.upgrade_path[self.effectiveCurrentChannel]

            # Validate installed apps compatibility with the target channel
            if self.nextChannel in self.compatibilityMatrix:
                incompatibleApps = []
                for installedApp in installedAppsChannel:
                    appId = installedApp["appId"]
                    appChannel = installedApp["channel"]

                    if appId not in self.compatibilityMatrix[self.nextChannel]:
                        if "feature" in self.nextChannel:
                            incompatibleApps.append(f"  - {appId}: Not available in feature channel {self.nextChannel}")
                        elif appId == "assist":
                            incompatibleApps.append(
                                f"  - {appId}: Not supported in {self.nextChannel} (Assist has been replaced by the Collaborate add-on in MAS 9.2+)"
                            )
                        else:
                            incompatibleApps.append(f"  - {appId}: Not supported in {self.nextChannel}")
                    else:
                        compatibleAppChannels = self.compatibilityMatrix[self.nextChannel][appId]
                        if appChannel not in compatibleAppChannels:
                            incompatibleApps.append(
                                f"  - {appId} (currently on {appChannel}): Must be on one of {compatibleAppChannels} to upgrade to MAS {self.nextChannel}"
                            )

                if incompatibleApps:
                    raise RuntimeError(f"Cannot upgrade to {self.nextChannel}. The following apps have compatibility issues:\n" + "\n".join(incompatibleApps))
        else:
            # We still allow the upgrade to proceed even though we can't detect the MAS instance
            # (e.g. the upgrade may be queued up to run after install)
            currentChannel = "Unknown"
            if self.nextChannel == "":
                self.nextChannel = "Unknown"

        self.currentChannel = currentChannel

        # The channel-based checks below compare versions, which cannot parse
        # the "Unknown" placeholder — skip them when the channel was not
        # detectable (the classic path has the same effective behaviour: the
        # checks are all no-ops for an undetectable target).
        knownChannel = self.nextChannel not in ("", "Unknown")

        # License acceptance is NOT enforced here: the workflow's conditional
        # license-acceptance step collects it (see licenseAcceptancePending)
        # after this validator has run, so the remaining checks below always
        # execute and the review screen has the full upgrade state.

        # The only scenario where Manage Foundation needs to be installed during an upgrade is
        # from 9.0.x to 9.1.x (if Manage was not already installed in 9.0.x).  The conditional
        # manage-foundation step collects the inputs that path needs (entitlement key and
        # storage classes — see manageFoundationPending / prepareManageFoundation).
        self.isManageFoundation = False
        if knownChannel and self.nextChannel.startswith("9.1") and not verifyAppInstance(self.dynamicClient, instanceId, "manage"):
            self.isManageFoundation = True
        else:
            # Reset on re-validation (e.g. the user went back and selected a
            # different instance) so the manage-foundation step is not shown
            # and the pipeline param carries the correct value.
            self.setParam("should_install_manage_foundation", "false")

        # Compute Monitor install order for upgrade
        if knownChannel:
            self.computeMonitorInstallOrderForUpgrade(instanceId)

            # Validate Kafka requirements for Civil component during upgrade
            self.validateKafkaForCivilUpgrade(instanceId)

            # Block upgrade if Suite CR has a stale routingMode=path from a pre-9.2 install
            self.checkRoutingModeForUpgrade(instanceId, currentChannel)

        detectedMode = None

        # Determine admin mode based on upgrade path
        if knownChannel and isVersionEqualOrAfter("9.3.0", self.nextChannel) and currentChannel and isVersionEqualOrAfter("9.2.0", currentChannel):
            detectedMode = getPermissionMode(self.dynamicClient, instanceId)
        elif knownChannel and self.nextChannel.startswith("9.2"):
            detectedMode = "cluster"

        # Evaluate RBAC access — stored so launchUpgrade() can apply the
        # pre-install RBAC when the pipeline is submitted
        if detectedMode:
            self.detectedMode = detectedMode
            self.applyPreInstallMASRBAC = evaluatePreinstallRBACAccess(
                dynamicClient=self.dynamicClient,
                masChannel=self.nextChannel,
                adminMode=detectedMode,
                instanceId=instanceId,
                noConfirm=True,
                printH1Func=self.printH1,
                printDescriptionFunc=self.printDescription,
                yesOrNoFunc=self.yesOrNo,
                fatalErrorFunc=self.fatalError,
                operation="upgrade",
            )

        # Resolve the pipeline storage class now (normally read from the
        # existing config-pvc created at install time) so the review screen
        # summary and the generated non-interactive command include it
        self.configPipelineStorageClass(instanceId)

    def licenseAcceptancePending(self) -> bool:
        """Return True when the target release's license still needs accepting.

        Drives the ``condition`` of the TUI license-acceptance step: the step
        is only shown when ``prepareUpgrade`` has resolved a target channel
        carrying a license that has not been accepted yet (the TUI equivalent
        of the classic wizard's license yes/no prompt, and of
        ``--accept-license`` on the non-interactive path).  Re-evaluated by
        the shell whenever a step completes, so it always reflects the
        currently selected instance's target channel.

        Returns:
            bool: True when the license-acceptance step must be shown.
        """
        return not self.licenseAccepted and not self.devMode and self.nextChannel in self.licenses

    def manageFoundationPending(self) -> bool:
        """Return True when the manage-foundation step must be shown.

        Drives the ``condition`` of the TUI manage-foundation step: the step
        is only shown when ``prepareUpgrade`` detected that this upgrade
        needs to install Manage Foundation (9.0.x to 9.1.x without Manage)
        and its inputs have not been collected yet.  Once
        ``prepareManageFoundation`` completes, ``should_install_manage_foundation``
        is set and the step is skipped on re-navigation (e.g. going back to
        instance-selection and returning).

        Returns:
            bool: True when the manage-foundation step must be shown.
        """
        return self.isManageFoundation and self.getParam("should_install_manage_foundation") != "true"

    def prepareManageFoundation(self) -> None:
        """Validate the Manage Foundation inputs and configure its installation.

        Called as the ``validator`` on the TUI manage-foundation step, after
        the entitlement key and (optionally) the storage classes have been
        written to ``self.params``.  Performs the same configuration as the
        classic wizard's Manage Foundation block: sets the install flags and
        pipeline params, resolves the Db2 storage classes (validating any
        provided values against the cluster, auto-detecting the rest), and
        runs the silent-mode Db2 configuration.

        The entitlement key is validated against the IBM Container Registry
        on a warn-only basis (matching the classic ``--no-confirm``
        behaviour) so that air-gapped environments are not blocked.

        Raises:
            RuntimeError: When a provided storage class does not exist on
                the cluster, or no storage classes can be resolved.
        """
        instanceId = self.params.get("mas_instance_id", "")

        # The TUI cannot run interactive prompts, so every configuration
        # below uses its non-interactive variant (matching the classic
        # --no-confirm behaviour).
        self.noConfirm = True

        # Validate the entitlement key against the registry.  Warn-only: an
        # invalid key surfaces again at pipeline launch, and blocking here
        # would make the TUI unusable where the registry is unreachable
        # (air-gapped clusters).
        entitlementKey = self.getParam("ibm_entitlement_key")
        if entitlementKey and not self.validateEntitlementKey(entitlementKey):
            logger.warning(
                "IBM entitlement key validation against the IBM Container Registry failed - continuing, but the upgrade pipeline will fail if the key is invalid"
            )

        # Attributes configDb2 reads (the same ones the classic wizard sets)
        self.manageAppName = "Manage foundation"
        self.showAdvancedOptions = False
        self.installIoT = False
        self.installMonitor = False
        self.installFacilities = False
        self.installManage = True

        self.setParam("mas_appws_components", "")
        self.setParam("mas_app_settings_aio_flag", "false")
        self.setParam("mas_app_channel_manage", self.nextChannel)
        self.setParam("mas_workspace_id", getWorkspaceId(self.dynamicClient, instanceId))

        # Storage classes for the Manage Foundation Db2 instances: validates
        # the provided values against the cluster, auto-detecting when left
        # blank (or failing with guidance to enter them on this step)
        self.configStorageClasses()

        # Silent-mode Db2 configuration: defaults for everything the classic
        # wizard prompts for (dedicated Db2 Warehouse instance for Manage)
        self.configDb2(silentMode=True)

        # Mark the Manage Foundation installation configured only now that
        # every input has validated — a failure above leaves the step
        # pending so the user can correct the inputs and retry
        self.setParam("should_install_manage_foundation", "true")

    def fetchInstalledInstanceIds(self) -> None:
        """Fetch and cache the MAS instance IDs from the connected cluster.

        Run as ``post_connect`` on the TUI connect-cluster step, in the worker
        thread immediately after a successful connection.  Raises
        ``RuntimeError`` when no MAS instances are found so the error
        surfaces on the connect screen rather than leaving the
        instance-selection step empty.

        Raises:
            RuntimeError: When no MAS Suite instances are found on the cluster.
        """
        suites = listMasInstances(self.dynamicClient)
        instanceIds = sorted([suite["metadata"]["labels"]["mas.ibm.com/instanceId"] for suite in suites])
        if not instanceIds:
            raise RuntimeError("No MAS instances were found on this cluster.")
        self._installedInstanceIds = instanceIds

    # ------------------------------------------------------------------
    # Pipeline launch (TUI path)
    # ------------------------------------------------------------------

    def _validateOpenShiftPipelines(self) -> tuple[bool, str]:
        """Validate OpenShift Pipelines installation.

        Returns:
            tuple[bool, str]: (success, detail_message)
        """
        if installOpenShiftPipelines(self.dynamicClient):
            return True, "OpenShift Pipelines Operator is installed and ready to use"
        return False, "OpenShift Pipelines Operator installation failed"

    def _prepareUpgradeNamespace(self, namespace: str, instanceId: str) -> tuple[bool, str]:
        """Create and prepare the upgrade pipelines namespace and secrets.

        Args:
            namespace (str): Pipelines namespace (``mas-<instanceId>-pipelines``).
            instanceId (str): The MAS instance being upgraded.

        Returns:
            tuple[bool, str]: (success, detail_message)
        """
        createNamespace(self.dynamicClient, namespace)
        preparePipelinesNamespace(
            dynClient=self.dynamicClient,
            instanceId=instanceId,
            storageClass=self.pipelineStorageClass,
            accessMode=self.pipelineStorageAccessMode,
        )
        prepareUpgradeSecrets(
            dynClient=self.dynamicClient,
            namespace=namespace,
            ibm_entitlement_key=self.getParam("ibm_entitlement_key"),
            artifactory_token=self.getParam("artifactory_token"),
            artifactory_username=self.getParam("artifactory_username"),
        )
        return True, namespace

    def _installTektonDefinitions(self, namespace: str) -> tuple[bool, str]:
        """Install Tekton definitions.

        Args:
            namespace (str): Namespace to install definitions in

        Returns:
            tuple[bool, str]: (success, detail_message)
        """
        updateTektonDefinitions(self.dynamicClient, namespace, self.tektonDefsPath)
        return True, f"v{self.version}"

    def _submitUpgradePipelineRun(self) -> tuple[bool, str]:
        """Submit the upgrade PipelineRun.

        Determines the ``masChannel`` parameter the same way the classic
        ``upgrade()`` method does: the retry scenario (next channel equals
        current channel) passes the previous channel so Ansible upgrades the
        remaining apps; otherwise the effective current channel (the oldest
        channel across Core and all installed apps, computed by
        ``prepareUpgrade``) is passed so Ansible targets the correct hop.

        Returns:
            tuple[bool, str]: (success, detail_message — the pipeline run URL on success)
        """
        if self.currentChannel not in ("", "Unknown") and self.nextChannel == self.currentChannel:
            # Retry scenario: core already on target, apps need upgrading.
            # Find the previous channel: which channel has upgrade_path[X] = currentChannel?
            previousChannel = None
            for prevCh, nextCh in self.upgrade_path.items():
                if nextCh == self.currentChannel:
                    previousChannel = prevCh
                    break
            masChannelParam = previousChannel if previousChannel else self.currentChannel
        else:
            masChannelParam = self.effectiveCurrentChannel

        pipelineURL = launchUpgradePipeline(self.dynamicClient, self.masInstanceId, self.skipPreCheck, masChannel=masChannelParam, params=self.params)
        if pipelineURL:
            return True, pipelineURL
        return False, "Failed — see log file for details"

    def launchUpgrade(self, progressCallback: Optional[Callable] = None, startCallback: Optional[Callable] = None) -> None:
        """Submit the Tekton upgrade pipeline with unified progress reporting.

        Uses the ProgressReporter abstraction to share one execution path
        between the CLI (Halo spinners) and TUI (callbacks) — the same
        pattern as ``UpdateApp.launchUpdate``.  Stages: Tekton definitions
        with digest, OpenShift Pipelines validation, optional pre-install
        RBAC, namespace preparation, Tekton definitions install, and
        PipelineRun submission.

        Args:
            progressCallback (Callable, optional): TUI callback (label, ok, detail) -> None
            startCallback (Callable, optional): TUI start callback (label) -> None
        """
        from mas.cli.common.progress import HaloProgressReporter, CallbackProgressReporter

        if progressCallback is not None:
            reporter = CallbackProgressReporter(progressCallback, startCallback)
        else:
            reporter = HaloProgressReporter(self.spinner, self.successIcon, self.failureIcon)

        # Tekton definitions with digest (no-op unless airgap / CLI digest);
        # shared by both execution paths as in the classic launch section
        self.createTektonFileWithDigest()

        instanceId = self.params.get("mas_instance_id", "")
        pipelinesNamespace = f"mas-{instanceId}-pipelines"

        # Stage 1: Validate OpenShift Pipelines
        reporter.start("Validate OpenShift Pipelines")
        success, detail = self._validateOpenShiftPipelines()
        if success:
            reporter.success("Validate OpenShift Pipelines", detail)
        else:
            reporter.failure("Validate OpenShift Pipelines", detail)
            self.fatalError("Installation failed")

        # Stage 2: Apply pre-install RBAC (if needed)
        if self.applyPreInstallMASRBAC and self.detectedMode:
            label = "Apply pre-install MAS RBAC"
            reporter.start(label)
            self.selectedAppsForRBAC = getInstalledApps(self.dynamicClient, instanceId)
            applyPreInstallMASRBAC(
                dynClient=self.dynamicClient,
                masVersion=".".join(self.nextChannel.split(".")[:2]),
                masInstanceId=instanceId,
                adminMode=self.detectedMode,
                selectedApps=self.selectedAppsForRBAC,
            )
            reporter.success(label, f"Pre-install MAS RBAC applied for target version {self.nextChannel} (mode: {self.detectedMode})")

        # Stage 3: Prepare pipelines namespace
        reporter.start("Prepare pipelines namespace")
        success, detail = self._prepareUpgradeNamespace(pipelinesNamespace, instanceId)
        reporter.success("Prepare pipelines namespace", detail)

        # Stage 4: Install Tekton definitions
        reporter.start("Install Tekton definitions")
        success, detail = self._installTektonDefinitions(pipelinesNamespace)
        reporter.success("Install Tekton definitions", f"Latest Tekton definitions are installed ({detail})")

        # Stage 5: Submit PipelineRun
        reporter.start("Submit PipelineRun")
        success, detail = self._submitUpgradePipelineRun()
        if success:
            # ``detail`` is the pipeline run URL: the TUI renders it beneath
            # the step list and the Copy URL button copies it (see
            # LaunchScreen._on_checklist_done).
            reporter.success("Submit PipelineRun", detail)
        else:
            reporter.failure("Submit PipelineRun", f"Failed to submit PipelineRun for {instanceId} upgrade, see log file for details")

    def configPipelineStorageClass(self, instanceId: str) -> None:
        """
        Determine the storage class and access mode for the upgrade pipeline config-pvc.
        Sets self.pipelineStorageClass and self.pipelineStorageAccessMode.
        """

        if self.pipelineStorageClass and self.pipelineStorageAccessMode:
            if getStorageClass(self.dynamicClient, self.pipelineStorageClass) is None:
                self.fatalError(f"Storage class '{self.pipelineStorageClass}' specified via --storage-pipeline is not available on this cluster.")
            logger.debug(f"Using pipeline storage class from CLI args: {self.pipelineStorageClass} ({self.pipelineStorageAccessMode})")
            return

        # Read storage class from existing config-pvc on the cluster.
        # This is the normal upgrade path - the PVC was created during the original
        # install and already has the correct storage class for this cluster.
        existingStorageClass, existingAccessMode = lookupPipelineStorageClass(self.dynamicClient, instanceId)
        if existingStorageClass:
            self.pipelineStorageClass = existingStorageClass
            self.pipelineStorageAccessMode = existingAccessMode or ("ReadWriteOnce" if self.isSNO() else "ReadWriteMany")
            logger.debug(f"Using pipeline storage class from existing config-pvc: {self.pipelineStorageClass} ({self.pipelineStorageAccessMode})")
            return

        # No existing config-pvc found — MAS was not installed via the CLI.
        # Prompt the user to configure a storage class for the pipeline PVC,
        self.printH1("Configure Pipeline Storage Class")
        self.printDescription(
            [
                "The upgrade pipeline requires a PersistentVolumeClaim (config-pvc) to store pipeline data.",
                "No existing config-pvc was found in the pipelines namespace.",
            ]
        )

        # Try to auto-detect a known storage provider as a default suggestion
        suggestedStorageClass = None
        suggestedAccessMode = None
        defaultStorageClasses = getDefaultStorageClasses(self.dynamicClient)

        if defaultStorageClasses.provider is not None:
            if self.isSNO() or defaultStorageClasses.rwx is None:
                suggestedStorageClass = defaultStorageClasses.rwo
                suggestedAccessMode = "ReadWriteOnce"
            else:
                suggestedStorageClass = defaultStorageClasses.rwx
                suggestedAccessMode = "ReadWriteMany"

            if not self.tuiMode:
                print_formatted_text(HTML(f"<MediumSeaGreen>Storage provider auto-detected: {defaultStorageClasses.providerName}</MediumSeaGreen>"))
                print_formatted_text(HTML(f"<LightSlateGrey>  - Storage class : {suggestedStorageClass}</LightSlateGrey>"))
                print_formatted_text(HTML(f"<LightSlateGrey>  - Access mode   : {suggestedAccessMode}</LightSlateGrey>"))

        # Accept the suggestion, or fall through to manual prompt
        useDetected = False
        if suggestedStorageClass:
            if self.noConfirm:
                # Non-interactive mode: accept auto-detected value without prompting
                self.pipelineStorageClass = suggestedStorageClass
                self.pipelineStorageAccessMode = suggestedAccessMode
                return
            useDetected = self.yesOrNo("Use the auto-detected storage class")

        if not useDetected:
            # No provider detected or user declined - fail fast in non-interactive mode
            if self.noConfirm:
                if self.tuiMode:
                    self.fatalError(
                        "No storage class could be detected for the pipeline config-pvc. "
                        "The upgrade pipeline requires one to create the config-pvc; re-run with --storage-pipeline and --storage-accessmode."
                    )
                self.fatalError(
                    "No storage class could be detected for the pipeline config-pvc and --no-confirm is set. "
                    "Please re-run with --storage-pipeline and --storage-accessmode."
                )

            # Customer declined the suggested class — keep the suggested access mode,
            # show the full list and let them pick a different storage class name.
            accessMode = suggestedAccessMode or ("ReadWriteOnce" if self.isSNO() else "ReadWriteMany")
            self.pipelineStorageAccessMode = accessMode

            self.printDescription([f"Select a {accessMode} storage class from the list below:"])
            for storageClass in getStorageClasses(self.dynamicClient):
                print_formatted_text(HTML(f"<LightSlateGrey>  - {storageClass.metadata.name}</LightSlateGrey>"))
            print()

            self.pipelineStorageClass = prompt(
                HTML(f"<Yellow>Enter the name of the {accessMode} storage class</Yellow> "),
                validator=StorageClassValidator(),
                validate_while_typing=False,
            )
        else:
            self.pipelineStorageClass = suggestedStorageClass
            self.pipelineStorageAccessMode = suggestedAccessMode

    def configStorageClasses(self) -> None:
        """
        Determine storage_class_rwo and storage_class_rwx for Manage Foundation Db2/PVC provisioning.
        Only called when Manage Foundation is being installed during upgrade (9.0 → 9.1).

        Priority:
          1. CLI args (--storage-class-rwo / --storage-class-rwx) — already set in self.params
          2. Auto-detected from getDefaultStorageClasses()
          3. Interactive prompt (falls back to fatalError in --no-confirm mode)
        """
        # 1. Validate any CLI args already provided (independently — partial args are allowed)
        if self.getParam("storage_class_rwo"):
            if getStorageClass(self.dynamicClient, self.getParam("storage_class_rwo")) is None:
                self.fatalError(f"Storage class '{self.getParam('storage_class_rwo')}' specified via --storage-class-rwo is not available on this cluster.")
                return
        if self.getParam("storage_class_rwx"):
            if getStorageClass(self.dynamicClient, self.getParam("storage_class_rwx")) is None:
                self.fatalError(f"Storage class '{self.getParam('storage_class_rwx')}' specified via --storage-class-rwx is not available on this cluster.")
                return

        # Both provided and valid — nothing more to do
        if self.getParam("storage_class_rwo") and self.getParam("storage_class_rwx"):
            logger.debug(f"Using storage classes from CLI args: RWO={self.getParam('storage_class_rwo')} RWX={self.getParam('storage_class_rwx')}")
            return

        # 2. Try auto-detection
        defaultStorageClasses = getDefaultStorageClasses(self.dynamicClient)
        if defaultStorageClasses.provider is not None:
            if not self.tuiMode:
                print_formatted_text(HTML(f"<MediumSeaGreen>Storage provider auto-detected: {defaultStorageClasses.providerName}</MediumSeaGreen>"))
                print_formatted_text(HTML(f"<LightSlateGrey>  - Storage class (ReadWriteOnce): {defaultStorageClasses.rwo}</LightSlateGrey>"))
                print_formatted_text(HTML(f"<LightSlateGrey>  - Storage class (ReadWriteMany): {defaultStorageClasses.rwx}</LightSlateGrey>"))

            useDetected = True
            if not self.noConfirm:
                useDetected = self.yesOrNo("Use the auto-detected storage classes")

            if useDetected:
                self.params["storage_class_rwo"] = defaultStorageClasses.rwo
                self.params["storage_class_rwx"] = defaultStorageClasses.rwx
                logger.debug(f"Using auto-detected storage classes: RWO={defaultStorageClasses.rwo} RWX={defaultStorageClasses.rwx}")
                return

        # 3. No provider detected or user declined — fail in non-interactive mode
        if self.noConfirm:
            if self.tuiMode:
                # The manage-foundation step's storage class fields are the
                # TUI equivalent of the CLI flags named in the classic message
                self.fatalError(
                    "No storage classes could be detected for the Manage Foundation Db2 instances. "
                    "Enter the ReadWriteOnce and ReadWriteMany storage classes to use on this step."
                )
            self.fatalError(
                "No storage classes could be detected for Manage Foundation Db2 instances and --no-confirm is set. "
                "Please re-run with --storage-class-rwo and --storage-class-rwx."
            )
            return

        self.printDescription(["Select the ReadWriteOnce and ReadWriteMany storage classes to use from the list below:"])
        for storageClass in getStorageClasses(self.dynamicClient):
            print_formatted_text(HTML(f"<LightSlateGrey>  - {storageClass.metadata.name}</LightSlateGrey>"))
        print()

        validator = StorageClassValidator()
        if not self.getParam("storage_class_rwo"):
            self.params["storage_class_rwo"] = prompt(
                HTML("<Yellow>ReadWriteOnce (RWO) storage class</Yellow> "),
                validator=validator,
                validate_while_typing=False,
            )
        if not self.getParam("storage_class_rwx"):
            self.params["storage_class_rwx"] = prompt(
                HTML("<Yellow>ReadWriteMany (RWX) storage class</Yellow> "),
                validator=validator,
                validate_while_typing=False,
            )

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

    def checkRoutingModeForUpgrade(self, instanceId: str, currentChannel: str) -> None:
        """Block the upgrade when a pre-9.2 Suite CR has spec.settings.routingMode set to "path".

        A routingMode value was accidentally written to Suite CRs on pre-9.2 instances.
        If that stale value is present when upgrading from pre-9.2 to 9.2+, the pipeline will
        attempt an unintended routing mode switch. This check fails early with clear remediation guidance.

        Upgrades where the current channel is already 9.2+ are not blocked — routingMode=path
        on a 9.2+ instance was set intentionally and must be preserved.

        Args:
            instanceId (str): The MAS instance ID to inspect.
            currentChannel (str): The currently installed MAS channel.
        """
        # Only relevant when upgrading TO 9.2+
        if not self.nextChannel or not isVersionEqualOrAfter("9.2.0", self.nextChannel):
            return

        # Already on 9.2+: routingMode=path was set intentionally, do not block
        if currentChannel and isVersionEqualOrAfter("9.2.0", currentChannel):
            return

        try:
            suiteAPI = self.dynamicClient.resources.get(api_version="core.mas.ibm.com/v1", kind="Suite")
            suite = suiteAPI.get(name=instanceId, namespace=f"mas-{instanceId}-core")
            routingMode = suite.get("spec", {}).get("settings", {}).get("routingMode")

            if routingMode == "path":
                self.fatalError(
                    f'Cannot upgrade to {self.nextChannel}: spec.settings.routingMode is set to "path" on the Suite CR.\n\n'
                    "This value was accidentally written to pre-9.2 Suite CRs and will cause the upgrade\n"
                    "pipeline to attempt an unintended routing mode switch.\n\n"
                    "To resolve this, remove the field from the Suite CR before retrying the upgrade:\n\n"
                    f"  oc patch suite {instanceId} -n mas-{instanceId}-core --type=json \\\n"
                    '    -p \'[{"op":"remove","path":"/spec/settings/routingMode"}]\'\n\n'
                    "After applying the patch, re-run the upgrade."
                )
        except Exception as e:
            logger.warning(f"Could not query Suite CR to check routingMode for upgrade pre-flight check: {e}")

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
        self.isInteractiveMode = instanceId is None

        # Pre-populate pipeline storage class from CLI args so configPipelineStorageClass
        self.pipelineStorageClass = args.storage_pipeline or None
        self.pipelineStorageAccessMode = args.storage_accessmode or None

        # Pre-populate RWO/RWX storage classes from CLI args (used for Manage Foundation Db2 instances)
        if args.storage_class_rwo:
            self.params["storage_class_rwo"] = args.storage_class_rwo
        if args.storage_class_rwx:
            self.params["storage_class_rwx"] = args.storage_class_rwx

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
                instanceId = suite["metadata"]["name"]
                reconciledVersion = self.getReconciledVersion(suite)

                print_formatted_text(HTML(f"- <u>{instanceId}</u> v{reconciledVersion}"))
                suiteOptions.append(instanceId)

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
                # Fetch all installed app subscription channels once — used for both
                # channel resolution and compatibility validation below
                installedAppsChannel = getAppsSubscriptionChannel(self.dynamicClient, instanceId)

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
                    # No --next-channel given: derive from upgrade_path using the
                    # oldest channel across Core + all installed apps.
                    # This handles partial upgrade resumption correctly — e.g. if Core
                    # reached 9.1.x but Manage is still on 9.0.x, effectiveCurrentChannel
                    # will be 9.0.x and the target will be 9.1.x instead of 9.2.x.
                    allChannels = [currentChannel] + [app["channel"] for app in installedAppsChannel]

                    def channelOrder(ch):
                        keys = list(self.upgrade_path.keys())
                        return keys.index(ch) if ch in keys else -1

                    self.effectiveCurrentChannel = max(allChannels, key=channelOrder)

                    # Early-exit BEFORE upgrade_path lookup:
                    # If every component is on the same channel and that channel has no
                    # further upgrade target, the instance is fully upgraded — exit cleanly
                    # without needing a self-referencing entry (e.g. "9.2.x":"9.2.x") in upgrade_path.
                    if self.effectiveCurrentChannel not in self.upgrade_path and all(ch == self.effectiveCurrentChannel for ch in allChannels):
                        print_formatted_text(
                            HTML(
                                f"<LightSlateGrey>No action required, {instanceId} is already fully upgraded. "
                                f"All components are on channel {self.effectiveCurrentChannel}.</LightSlateGrey>"
                            )
                        )
                        return

                    if self.effectiveCurrentChannel not in self.upgrade_path:
                        self.fatalError(f"No upgrade available, {instanceId} is already on the latest release {self.effectiveCurrentChannel}")
                    self.nextChannel = self.upgrade_path[self.effectiveCurrentChannel]

                # Check if all components are already on the target channel.
                # Covers both auto-detect and --next-channel paths.
                # Only exits if Core AND every installed app are already on nextChannel.
                # If any app is behind, this condition is False and pipeline launches normally.
                if self.nextChannel == currentChannel and all(app["channel"] == self.nextChannel for app in installedAppsChannel):
                    print_formatted_text(
                        HTML(
                            f"<LightSlateGrey>No action required, {instanceId} is already fully upgraded. "
                            f"All components are on channel {self.nextChannel}.</LightSlateGrey>"
                        )
                    )
                    return

                # Validate installed apps compatibility with the target channel
                if self.nextChannel in self.compatibilityMatrix:
                    incompatibleApps = []

                    for installedApp in installedAppsChannel:
                        appId = installedApp["appId"]
                        appChannel = installedApp["channel"]

                        # Check if app is supported in the target channel
                        if appId not in self.compatibilityMatrix[self.nextChannel]:
                            if "feature" in self.nextChannel:
                                incompatibleApps.append(f"  - {appId}: Not available in feature channel {self.nextChannel}")
                            elif appId == "assist":
                                # Assist was withdrawn in MAS 9.2; its functionality was migrated to the Collaborate add-on
                                incompatibleApps.append(
                                    f"  - {appId}: Not supported in {self.nextChannel} (Assist has been replaced by the Collaborate add-on in MAS 9.2+)"
                                )
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
            self.installMonitor = False
            self.installFacilities = False
            self.installManage = True
            self.isManageFoundation = True
            self.printDescription(
                [f"{self.manageAppName} installs the following capabilities: User, Security groups, Application configurator and Mobile configurator."]
            )

            # TODO: Why do we need to ask the user from their entitlement key, we should look it up from the cluster.
            self.printH1("Configure IBM Container Registry")
            self.promptForEntitlementKey("IBM entitlement key", "ibm_entitlement_key")
            if self.devMode:
                self.promptForString("Artifactory username", "artifactory_username")
                self.promptForString("Artifactory token", "artifactory_token", isPassword=True)

            self.setParam("should_install_manage_foundation", "true")
            self.setParam("mas_appws_components", "")
            self.setParam("mas_app_settings_aio_flag", "false")
            self.setParam("mas_app_channel_manage", self.nextChannel)
            self.setParam("mas_workspace_id", getWorkspaceId(self.dynamicClient, instanceId))
            self.configStorageClasses()
            self.configDb2(silentMode=True)

        # Compute Monitor install order for upgrade
        self.computeMonitorInstallOrderForUpgrade(instanceId)

        # Validate Kafka requirements for Civil component during upgrade
        self.validateKafkaForCivilUpgrade(instanceId)

        # Block upgrade if Suite CR has a stale routingMode=path from a pre-9.2 install
        self.checkRoutingModeForUpgrade(instanceId, currentChannel)

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

        self.configPipelineStorageClass(instanceId)

        # Show the equivalent non-interactive command before the review screen
        self.masInstanceId = instanceId
        nonInteractiveCommand = self.buildCommand()
        self.printH1("Non-Interactive Upgrade Command")
        self.printDescription(
            [
                "Save and re-use the following script to re-run this upgrade without needing to answer the interactive prompts again",
                "",
                nonInteractiveCommand,
            ]
        )
        if self.isInteractiveMode:
            offerCommandScript(self, nonInteractiveCommand, f"mas-upgrade-{instanceId}.sh")

        self.printH1("Review Settings")
        print_formatted_text(HTML(f"<LightSlateGrey>Instance ID ..................... {instanceId}</LightSlateGrey>"))
        print_formatted_text(HTML(f"<LightSlateGrey>Current MAS Channel ............. {currentChannel}</LightSlateGrey>"))
        print_formatted_text(HTML(f"<LightSlateGrey>Next MAS Channel ................ {self.nextChannel}</LightSlateGrey>"))
        print_formatted_text(HTML(f"<LightSlateGrey>Skip Pre-Upgrade Checks ......... {self.skipPreCheck}</LightSlateGrey>"))
        print_formatted_text(HTML(f"<LightSlateGrey>Pipeline Storage Class .......... {self.pipelineStorageClass}</LightSlateGrey>"))
        print_formatted_text(HTML(f"<LightSlateGrey>Pipeline Storage Access Mode .... {self.pipelineStorageAccessMode}</LightSlateGrey>"))

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
                preparePipelinesNamespace(
                    dynClient=self.dynamicClient,
                    instanceId=instanceId,
                    storageClass=self.pipelineStorageClass,
                    accessMode=self.pipelineStorageAccessMode,
                )
                prepareUpgradeSecrets(
                    dynClient=self.dynamicClient,
                    namespace=pipelinesNamespace,
                    ibm_entitlement_key=self.getParam("ibm_entitlement_key"),
                    artifactory_token=self.getParam("artifactory_token"),
                    artifactory_username=self.getParam("artifactory_username"),
                )
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
                    # No --next-channel provided: pass the effectiveCurrentChannel computed
                    # earlier so Ansible targets the correct hop based on all component
                    # channels, not just Core's channel.
                    masChannelParam = self.effectiveCurrentChannel if hasattr(self, "effectiveCurrentChannel") else ""

                pipelineURL = launchUpgradePipeline(self.dynamicClient, instanceId, self.skipPreCheck, masChannel=masChannelParam, params=self.params)
                if pipelineURL is not None:
                    h.stop_and_persist(symbol=self.successIcon, text=f"PipelineRun for {instanceId} upgrade submitted")
                    print_formatted_text(HTML(f"\nView progress:\n  <Cyan><u>{pipelineURL}</u></Cyan>\n"))
                else:
                    h.stop_and_persist(symbol=self.failureIcon, text=f"Failed to submit PipelineRun for {instanceId} upgrade, see log file for details")
                    print()

            # Re-print the command so it is not lost in the scrollback above the
            # pipeline launch output
            self.printDescription(
                [
                    "For reference, the non-interactive command equivalent to this upgrade:",
                    "",
                    nonInteractiveCommand,
                ]
            )
