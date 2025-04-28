#!/usr/bin/env python
# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
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
from mas.devops.mas import listMasInstances, getMasChannel, getWorkspaceId, verifyAppInstance
from mas.devops.tekton import installOpenShiftPipelines, updateTektonDefinitions, launchUpgradePipeline

logger = logging.getLogger(__name__)


class UpgradeApp(BaseApp, UpgradeSettingsMixin):
    def upgrade(self, argv):
        """
        Upgrade MAS instance
        """
        args = upgradeArgParser.parse_args(args=argv)
        instanceId = args.mas_instance_id
        self.noConfirm = args.no_confirm
        self.skipPreCheck = args.skip_pre_check
        self.licenseAccepted = args.accept_license
        self.devMode = args.dev_mode

        if instanceId is None:
            self.printH1("Set Target OpenShift Cluster")
            # Connect to the target cluster
            self.connect()
        else:
            logger.debug("MAS instance ID is set, so we assume already connected to the desired OCP")
            # Need to lookup target architecture because configDb2 will try to access self.architecture
            self.lookupTargetArchitecture()

        if self.dynamicClient is None:
            print_formatted_text(HTML("<Red>Error: The Kubernetes dynamic Client is not available.  See log file for details</Red>"))
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
                suiteOptions.append(suite['metadata']['name'])

            suiteCompleter = WordCompleter(suiteOptions)
            print()
            instanceId = prompt(HTML('<Yellow>Enter MAS instance ID: </Yellow>'), completer=suiteCompleter, validator=InstanceIDValidator(), validate_while_typing=False)

        currentChannel = getMasChannel(self.dynamicClient, instanceId)
        if currentChannel is not None:
            if self.devMode:
                # This is mainly used for the scenario where Manage Foundation would be installed, because core-upgrade does not use the value of nextChannel,
                # it uses a compatibility_matrix object in ansible-devops to determine the next channel, so nextChannel is only informative for core upgrade purposes
                nextChannel = prompt(HTML('<Yellow>Custom channel</Yellow> '))
            else:
                if currentChannel not in self.upgrade_path:
                    self.fatalError(f"No upgrade available, {instanceId} is are already on the latest release {currentChannel}")
                nextChannel = self.upgrade_path[currentChannel]
        else:
            # We still allow the upgrade to proceed even though we can't detect the MAS instance.  The upgrade may be being
            # queued up to run after install for instance
            currentChannel = "Unknown"
            nextChannel = "Unknown"

        if not self.licenseAccepted and not self.devMode:
            self.printH1("License Terms")
            self.printDescription([
                "To continue with the upgrade, you must accept the license terms:",
                self.licenses[nextChannel]
            ])

            if self.noConfirm:
                self.fatalError("You must accept the license terms with --accept-license when using the --no-confirm flag")
            else:
                if not self.yesOrNo("Do you accept the license terms"):
                    exit(1)

        # The only scenario where Manage Foundation needs to be installed during an upgrade is from 9.0.x to 9.1.x (if Manage was not already installed in 9.0.x).
        self.setParam("should_install_manage_foundation", "false")
        if nextChannel.startswith("9.1") and not verifyAppInstance(self.dynamicClient, instanceId, "manage"):
            self.manageAppName = "Manage foundation"
            self.showAdvancedOptions = False
            self.installIoT = False
            self.installManage = True
            self.isManageFoundation = True
            self.printDescription([f"{self.manageAppName} installs the following capabilities: User, Security groups, Application configurator and Mobile configurator."])
            self.printH1("Configure IBM Container Registry")
            self.promptForString("IBM entitlement key", "ibm_entitlement_key", isPassword=True)
            if self.devMode:
                self.promptForString("Artifactory username", "artifactory_username")
                self.promptForString("Artifactory token", "artifactory_token", isPassword=True)
            self.setParam("should_install_manage_foundation", "true")
            self.setParam("is_full_manage", "false")
            self.setParam("mas_appws_components", "")
            self.setParam("mas_app_settings_aio_flag", "false")
            self.setParam("mas_app_channel_manage", nextChannel)
            self.setParam("mas_workspace_id", getWorkspaceId(self.dynamicClient, instanceId))
            # It has been decided that we don't need to ask for any specific Manage Settings
            # self.manageSettings()
            self.configDb2(silentMode=True)

        self.printH1("Review Settings")
        print_formatted_text(HTML(f"<LightSlateGrey>Instance ID ..................... {instanceId}</LightSlateGrey>"))
        print_formatted_text(HTML(f"<LightSlateGrey>Current MAS Channel ............. {currentChannel}</LightSlateGrey>"))
        print_formatted_text(HTML(f"<LightSlateGrey>Next MAS Channel ................ {nextChannel}</LightSlateGrey>"))
        print_formatted_text(HTML(f"<LightSlateGrey>Skip Pre-Upgrade Checks ......... {self.skipPreCheck}</LightSlateGrey>"))

        if not self.noConfirm:
            print()
            continueWithUpgrade = self.yesOrNo("Proceed with these settings")

        if self.noConfirm or continueWithUpgrade:
            self.createTektonFileWithDigest()

            self.printH1("Launch Upgrade")
            pipelinesNamespace = f"mas-{instanceId}-pipelines"

            with Halo(text='Validating OpenShift Pipelines installation', spinner=self.spinner) as h:
                installOpenShiftPipelines(self.dynamicClient)
                h.stop_and_persist(symbol=self.successIcon, text="OpenShift Pipelines Operator is installed and ready to use")

            with Halo(text=f'Preparing namespace ({pipelinesNamespace})', spinner=self.spinner) as h:
                createNamespace(self.dynamicClient, pipelinesNamespace)
                h.stop_and_persist(symbol=self.successIcon, text=f"Namespace is ready ({pipelinesNamespace})")

            with Halo(text=f'Installing latest Tekton definitions (v{self.version})', spinner=self.spinner) as h:
                updateTektonDefinitions(pipelinesNamespace, self.tektonDefsPath)
                h.stop_and_persist(symbol=self.successIcon, text=f"Latest Tekton definitions are installed (v{self.version})")

            with Halo(text='Submitting PipelineRun for {instanceId} upgrade', spinner=self.spinner) as h:
                pipelineURL = launchUpgradePipeline(self.dynamicClient, instanceId, self.skipPreCheck, params=self.params)
                if pipelineURL is not None:
                    h.stop_and_persist(symbol=self.successIcon, text=f"PipelineRun for {instanceId} upgrade submitted")
                    print_formatted_text(HTML(f"\nView progress:\n  <Cyan><u>{pipelineURL}</u></Cyan>\n"))
                else:
                    h.stop_and_persist(symbol=self.failureIcon, text=f"Failed to submit PipelineRun for {instanceId} upgrade, see log file for details")
                    print()
