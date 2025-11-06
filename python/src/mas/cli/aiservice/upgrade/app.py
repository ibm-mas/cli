#!/usr/bin/env python
# *****************************************************************************
# Copyright (c) 2024, 2025 IBM Corporation and other Contributors.
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

from ...cli import BaseApp
from ...validators import AiserviceInstanceIDValidator
from .argParser import upgradeArgParser

from mas.devops.ocp import createNamespace
from mas.devops.mas import listAiServiceInstances, getAiserviceChannel
from mas.devops.tekton import installOpenShiftPipelines, updateTektonDefinitions, launchAiServiceUpgradePipeline
from openshift.dynamic.exceptions import ResourceNotFoundError
logger = logging.getLogger(__name__)


class AiServiceUpgradeApp(BaseApp):
    def upgrade(self, argv):
        """
        Upgrade AI Service instance
        """
        args = upgradeArgParser.parse_args(args=argv)
        aiserviceInstanceId = args.aiservice_instance_id
        self.noConfirm = args.no_confirm
        self.skipPreCheck = args.skip_pre_check
        self.licenseAccepted = args.accept_license
        self.devMode = args.dev_mode

        if aiserviceInstanceId is None:
            self.printH1("Set Target OpenShift Cluster")
            # Connect to the target cluster
            self.connect()
        else:
            logger.debug("AI Service instance ID is set, so we assume already connected to the desired OCP")
            # Need to lookup target architecture because configDb2 will try to access self.architecture
            self.lookupTargetArchitecture()

        if self.dynamicClient is None:
            print_formatted_text(HTML("<Red>Error: The Kubernetes dynamic Client is not available.  See log file for details</Red>"))
            sys.exit(1)

        if aiserviceInstanceId is None:
            # Interactive mode
            self.printH1("AI Service Instance Selection")
            print_formatted_text(HTML("<LightSlateGrey>Select a AI Service instance to upgrade from the list below:</LightSlateGrey>"))
            try:
                aiserviceInstances = listAiServiceInstances(self.dynamicClient)
            except ResourceNotFoundError:
                aiserviceInstances = []
            aiserviceOptions = []

            if len(aiserviceInstances) == 0:
                print_formatted_text(HTML("<Red>Error: No AI Service instances detected on this cluster</Red>"))
                sys.exit(1)

            for aiservice in aiserviceInstances:
                print_formatted_text(HTML(f"- <u>{aiservice['metadata']['name']}</u> v{aiservice['status']['versions']['reconciled']}"))
                aiserviceOptions.append(aiservice['metadata']['name'])

            aiserviceCompleter = WordCompleter(aiserviceOptions)
            print()
            aiserviceInstanceId = prompt(HTML('<Yellow>Enter AI Service instance ID: </Yellow>'), completer=aiserviceCompleter, validator=AiserviceInstanceIDValidator(), validate_while_typing=False)

        currentAiserviceChannel = getAiserviceChannel(self.dynamicClient, aiserviceInstanceId)
        if currentAiserviceChannel is not None:
            if self.devMode:
                # this enables upgrade of custom channel for AI service
                nextAiserviceChannel = prompt(HTML('<Yellow>Custom channel</Yellow> '))
            else:
                if currentAiserviceChannel not in self.upgrade_path:
                    self.fatalError(f"No upgrade available, {aiserviceInstanceId} is are already on the latest release {currentAiserviceChannel}")
                nextAiserviceChannel = self.upgrade_path[currentAiserviceChannel]

        if not self.licenseAccepted and not self.devMode:
            self.printH1("License Terms")
            self.printDescription([
                "To continue with the upgrade, you must accept the license terms:",
                self.licenses[nextAiserviceChannel]
            ])

            if self.noConfirm:
                self.fatalError("You must accept the license terms with --accept-license when using the --no-confirm flag")
            else:
                if not self.yesOrNo("Do you accept the license terms"):
                    exit(1)

        self.printH1("Review Settings")
        print_formatted_text(HTML(f"<LightSlateGrey>AI Service Instance ID ..................... {aiserviceInstanceId}</LightSlateGrey>"))
        print_formatted_text(HTML(f"<LightSlateGrey>Current AI Service Channel ............. {currentAiserviceChannel}</LightSlateGrey>"))
        print_formatted_text(HTML(f"<LightSlateGrey>Next AI Service Channel ................ {nextAiserviceChannel}</LightSlateGrey>"))
        print_formatted_text(HTML(f"<LightSlateGrey>Skip Pre-Upgrade Checks ......... {self.skipPreCheck}</LightSlateGrey>"))

        if not self.noConfirm:
            print()
            continueWithUpgrade = self.yesOrNo("Proceed with these settings")

        if self.noConfirm or continueWithUpgrade:
            self.createTektonFileWithDigest()

            self.printH1("Launch Upgrade")
            pipelinesNamespace = f"aiservice-{aiserviceInstanceId}-pipelines"

            with Halo(text='Validating OpenShift Pipelines installation', spinner=self.spinner) as h:
                if installOpenShiftPipelines(self.dynamicClient):
                    h.stop_and_persist(symbol=self.successIcon, text="OpenShift Pipelines Operator is installed and ready to use")
                else:
                    h.stop_and_persist(symbol=self.successIcon, text="OpenShift Pipelines Operator installation failed")
                    self.fatalError("Installation failed")

            with Halo(text=f'Preparing namespace ({pipelinesNamespace})', spinner=self.spinner) as h:
                createNamespace(self.dynamicClient, pipelinesNamespace)
                h.stop_and_persist(symbol=self.successIcon, text=f"Namespace is ready ({pipelinesNamespace})")

            with Halo(text=f'Installing latest Tekton definitions (v{self.version})', spinner=self.spinner) as h:
                updateTektonDefinitions(pipelinesNamespace, self.tektonDefsPath)
                h.stop_and_persist(symbol=self.successIcon, text=f"Latest Tekton definitions are installed (v{self.version})")

            with Halo(text='Submitting PipelineRun for {aiserviceInstanceId} upgrade', spinner=self.spinner) as h:
                pipelineURL = launchAiServiceUpgradePipeline(self.dynamicClient, aiserviceInstanceId, self.skipPreCheck, aiserviceChannel=nextAiserviceChannel, params=self.params)
                if pipelineURL is not None:
                    h.stop_and_persist(symbol=self.successIcon, text=f"PipelineRun for {aiserviceInstanceId} upgrade submitted")
                    print_formatted_text(HTML(f"\nView progress:\n  <Cyan><u>{pipelineURL}</u></Cyan>\n"))
                else:
                    h.stop_and_persist(symbol=self.failureIcon, text=f"Failed to submit PipelineRun for {aiserviceInstanceId} upgrade, see log file for details")
                    print()
