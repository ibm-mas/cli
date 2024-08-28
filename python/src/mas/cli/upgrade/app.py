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

from ..cli import BaseApp, getHelpFormatter
from ..validators import InstanceIDValidator, YesNoValidator
from .argParser import upgradeArgParser

from mas.devops.ocp import createNamespace
from mas.devops.mas import listMasInstances, verifyMasInstance
from mas.devops.tekton import installOpenShiftPipelines, updateTektonDefinitions, launchUpgradePipeline

logger = logging.getLogger(__name__)

class UpgradeApp(BaseApp):
    def upgrade(self, argv):
        """
        Upgrade MAS instance
        """
        args = upgradeArgParser.parse_args(args=argv)
        instanceId = args.mas_instance_id
        self.noConfirm = args.no_confirm
        self.skipPreCheck = args.skip_pre_check

        if instanceId is None:
            self.printH1("Set Target OpenShift Cluster")
            # Connect to the target cluster
            self.connect()
        else:
            logger.debug("MAS instance ID is set, so we assume already connected to the desired OCP")

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
                print_formatted_text(HTML(f"<Red>Error: No MAS instances detected on this cluster</Red>"))
                sys.exit(1)

            for suite in suites:
                print_formatted_text(HTML(f"- <u>{suite['metadata']['name']}</u> v{suite['status']['versions']['reconciled']}"))
                suiteOptions.append(suite['metadata']['name'])

            suiteCompleter = WordCompleter(suiteOptions)
            print()
            instanceId = prompt(HTML(f'<Yellow>Enter MAS instance ID: </Yellow>'), completer=suiteCompleter, validator=InstanceIDValidator(), validate_while_typing=False)
        else:
            # Non-interactive mode
            if not verifyMasInstance(self.dynamicClient, instanceId):
                print_formatted_text(HTML(f"<Red>Error: MAS instance {instanceId} not found on this cluster</Red>"))
                sys.exit(1)

        self.printH1("Review Settings")
        print_formatted_text(HTML(f"<LightSlateGrey>Instance ID ..................... {instanceId}</LightSlateGrey>"))
        print_formatted_text(HTML(f"<LightSlateGrey>Skip Pre-Upgrade Checks ......... {self.skipPreCheck}</LightSlateGrey>"))

        if not self.noConfirm:
            print()
            continueWithUpgrade = prompt(HTML(f'<Yellow>Proceed with these settings?</Yellow> '), validator=YesNoValidator(), validate_while_typing=False)

        if self.noConfirm or continueWithUpgrade in ["y", "yes"]:
            self.createTektonFileWithDigest()

            self.printH1("Launch Upgrade")
            pipelinesNamespace = f"mas-{instanceId}-pipelines"

            with Halo(text='Validating OpenShift Pipelines installation', spinner=self.spinner) as h:
                installOpenShiftPipelines(self.dynamicClient)
                h.stop_and_persist(symbol=self.successIcon, text=f"OpenShift Pipelines Operator is installed and ready to use")

            with Halo(text=f'Preparing namespace ({pipelinesNamespace})', spinner=self.spinner) as h:
                createNamespace(self.dynamicClient, pipelinesNamespace)
                h.stop_and_persist(symbol=self.successIcon, text=f"Namespace is ready ({pipelinesNamespace})")

            with Halo(text=f'Installing latest Tekton definitions (v{self.version})', spinner=self.spinner) as h:
                updateTektonDefinitions(pipelinesNamespace, self.tektonDefsPath)
                h.stop_and_persist(symbol=self.successIcon, text=f"Latest Tekton definitions are installed (v{self.version})")

            with Halo(text='Submitting PipelineRun for {instanceId} upgrade', spinner=self.spinner) as h:
                pipelineURL = launchUpgradePipeline(self.dynamicClient, instanceId, self.skipPreCheck)
                if pipelineURL is not None:
                    h.stop_and_persist(symbol=self.successIcon, text=f"PipelineRun for {instanceId} upgrade submitted")
                    print_formatted_text(HTML(f"\nView progress:\n  <Cyan><u>{pipelineURL}</u></Cyan>\n"))
                else:
                    h.stop_and_persist(symbol=self.failureIcon, text=f"Failed to submit PipelineRun for {instanceId} upgrade, see log file for details")
                    print()
