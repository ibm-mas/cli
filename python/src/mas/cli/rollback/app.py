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

import logging
import logging.handlers
from halo import Halo
from prompt_toolkit import print_formatted_text, HTML

from openshift.dynamic.exceptions import ResourceNotFoundError

from ..cli import BaseApp
from ..validators import StorageClassValidator
from .argParser import rollbackArgParser

from mas.devops.ocp import createNamespace, getConsoleURL
from mas.devops.mas import listMasInstances, getCurrentCatalog
from mas.devops.tekton import preparePipelinesNamespace, installOpenShiftPipelines, updateTektonDefinitions, launchRollbackPipeline


logger = logging.getLogger(__name__)


class RollbackApp(BaseApp):

    def rollback(self, argv):
        """
        Rollback MAS instance
        """
        self.args = rollbackArgParser.parse_args(args=argv)
        self.noConfirm = self.args.no_confirm
        self.devMode = self.args.dev_mode

        if self.args.mas_catalog_version:
            # Non-interactive mode
            logger.debug("Maximo Operator Catalog version is set, so we assume already connected to the desired OCP")
            requiredParams = ["mas_catalog_version", "mas_instance_id", "mas_channel", "mas_app_channel_manage", "mas_app_channel_iot"]
            optionalParams = [
                "skip_pre_check",
                "dev_mode",
                # Dev Mode
                "artifactory_username",
                "artifactory_token"

            ]
            for key, value in vars(self.args).items():
                # These fields we just pass straight through to the parameters and fail if they are not set
                if key in requiredParams:
                    if value is None:
                        self.fatalError(f"{key} must be set")
                    self.setParam(key, value)

                # These fields we just pass straight through to the parameters
                elif key in optionalParams:
                    if value is not None:
                        self.setParam(key, value)

                # Arguments that we don't need to do anything with
                elif key in ["no_confirm", "help"]:
                    pass

                # Fail if there's any arguments we don't know how to handle
                else:
                    print(f"Unknown option: {key} {value}")
                    self.fatalError(f"Unknown option: {key} {value}")
        else:
            # Interactive mode
            self.printH1("Set Target OpenShift Cluster")
            # Connect to the target cluster
            self.connect()

        if self.dynamicClient is None:
            self.fatalError("The Kubernetes dynamic Client is not available.  See log file for details")

        # Perform a check whether the cluster is set up for airgap install, this will trigger an early failure if the cluster is using the now
        # deprecated MaximoApplicationSuite ImageContentSourcePolicy instead of the new ImageDigestMirrorSet
        self.isAirgap()
        self.reviewCurrentCatalog()
        self.reviewMASInstance()

        if self.args.mas_catalog_version is None:
            # Interactive mode
            self.chooseCatalog()

        # Validations
        if not self.devMode:
            self.validateCatalog()

        print()

        self.printH1("Review Settings")
        self.printDescription([
            "Connected to:",
            f" - <u>{getConsoleURL(self.dynamicClient)}</u>"
        ])

        self.printH2("IBM Maximo Operator Catalog")
        self.printSummary("Installed Catalog", self.installedCatalogId)
        self.printSummary("Rollback Catalog", self.getParam("mas_catalog_version"))
        self.printSummary("Current Instance ID", self.getParam("mas_instance_id"))
        self.printSummary("Rollback Channel for Core Platform", self.getParam("mas_channel"))

        self.printSummary("Rollback Channel for Maximo Manage", self.getParam("mas_app_channel_manage"))

        self.printSummary("Rollback Channel for Maximo IoT", self.getParam("mas_app_channel_iot"))        
        
        if not self.noConfirm:
            print()
            self.printDescription([
                "Please carefully review your choices above, correcting mistakes now is much easier than after the update has begun"
            ])
            continueWithUpdate = self.yesOrNo("Proceed with these settings")
        # Prepare the namespace and launch the installation pipeline
        if self.noConfirm or continueWithUpdate:
            self.createTektonFileWithDigest()

            self.printH1("Launch Rollback")
            pipelinesNamespace = f"mas-{self.getParam('mas_instance_id')}-pipelines"

            with Halo(text='Validating OpenShift Pipelines installation', spinner=self.spinner) as h:
                installOpenShiftPipelines(self.dynamicClient)
                h.stop_and_persist(symbol=self.successIcon, text="OpenShift Pipelines Operator is installed and ready to use")

            with Halo(text=f'Preparing namespace ({pipelinesNamespace})', spinner=self.spinner) as h:
                createNamespace(self.dynamicClient, pipelinesNamespace)
                preparePipelinesNamespace(dynClient=self.dynamicClient)
                h.stop_and_persist(symbol=self.successIcon, text=f"Namespace is ready ({pipelinesNamespace})")

            with Halo(text=f'Installing latest Tekton definitions (v{self.version})', spinner=self.spinner) as h:
                updateTektonDefinitions(pipelinesNamespace, self.tektonDefsPath)
                h.stop_and_persist(symbol=self.successIcon, text=f"Latest Tekton definitions are installed (v{self.version})")

            with Halo(text="Submitting PipelineRun for MAS Rollback", spinner=self.spinner) as h:
                pipelineURL = launchRollbackPipeline(dynClient=self.dynamicClient, params=self.params)
                if pipelineURL is not None:
                    h.stop_and_persist(symbol=self.successIcon, text="PipelineRun for MAS rollback submitted")
                    print_formatted_text(HTML(f"\nView progress:\n  <Cyan><u>{pipelineURL}</u></Cyan>\n"))
                else:
                    h.stop_and_persist(symbol=self.failureIcon, text="Failed to submit PipelineRun for MAS rollback, see log file for details")
                    print()

    def reviewCurrentCatalog(self) -> None:
        catalogInfo = getCurrentCatalog(self.dynamicClient)
        self.installedCatalogId = None
        if catalogInfo is None:
            self.fatalError("Unable to locate existing install of the IBM Maximo Operator Catalog")
        elif catalogInfo["catalogId"] is None:
            self.printWarning("Unable to determine identity & version of currently installed ibm-maximo-operator-catalog")
        else:
            self.installedCatalogId = catalogInfo["catalogId"]
            self.printH1("Review Installed Catalog")
            self.printDescription([
                f"The currently installed Maximo Operator Catalog is <u>{catalogInfo['displayName']}</u>",
                f" <u>{catalogInfo['image']}</u>"
            ])

    def reviewMASInstance(self) -> None:
        self.printH1("Review MAS Instances")
        self.printDescription(["The following MAS intances are installed on the target cluster and will be affected by the catalog rollback:"])
        try:
            suites = listMasInstances(self.dynamicClient)
            for suite in suites:
                self.printDescription([f"- <u>{suite['metadata']['name']}</u> v{suite['status']['versions']['reconciled']}"])
        except ResourceNotFoundError:
            self.fatalError("No MAS instances were detected on the cluster (Suite.core.mas.ibm.com/v1 API is not available).  See log file for details")

    def validateCatalog(self) -> None:
        if self.installedCatalogId is not None and self.installedCatalogId < self.getParam("mas_catalog_version"):
            self.fatalError(f"Selected catalog is newer than the currently installed catalog.  Unable to rollback catalog from {self.installedCatalogId} to {self.getParam('mas_catalog_version')}")

