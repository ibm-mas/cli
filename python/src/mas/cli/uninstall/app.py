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
from prompt_toolkit.completion import WordCompleter

from openshift.dynamic.exceptions import NotFoundError, ResourceNotFoundError

from ..cli import BaseApp
from ..validators import InstanceIDValidator
from .argParser import uninstallArgParser

from mas.devops.ocp import createNamespace
from mas.devops.mas import listMasInstances, verifyMasInstance
from mas.devops.tekton import installOpenShiftPipelines, updateTektonDefinitions, launchUninstallPipeline


logger = logging.getLogger(__name__)


class UninstallApp(BaseApp):
    def uninstall(self, argv):
        """
        Uninstall MAS instance
        """
        args = uninstallArgParser.parse_args(args=argv)
        instanceId = args.mas_instance_id
        droNamespace = args.dro_namespace
        self.noConfirm = args.no_confirm

        if args.uninstall_all_deps:
            uninstallGrafana = True
            uninstallIBMCatalog = True
            uninstallCommonServices = True
            uninstallCertManager = True
            uninstallUDS = True
            uninstallMongoDb = True
            uninstallSLS = True
        else:
            uninstallGrafana = args.uninstall_grafana
            uninstallIBMCatalog = args.uninstall_ibm_catalog
            uninstallCommonServices = args.uninstall_common_services
            uninstallCertManager = args.uninstall_cert_manager
            uninstallUDS = args.uninstall_uds
            uninstallMongoDb = args.uninstall_mongodb
            uninstallSLS = args.uninstall_sls

        if instanceId is None:
            self.printH1("Set Target OpenShift Cluster")
            # Connect to the target cluster
            self.connect()
        else:
            logger.debug("MAS instance ID is set, so we assume already connected to the desired OCP")

        if self.dynamicClient is None:
            self.fatalError("The Kubernetes dynamic Client is not available.  See log file for details")

        if instanceId is None:
            # Interactive mode
            self.printH1("Instance Selection")
            self.printDescription(["Select a MAS instance to uninstall from the list below:"])

            suiteOptions = []
            try:
                suites = listMasInstances(self.dynamicClient)
                for suite in suites:
                    self.printDescription([f"- <u>{suite['metadata']['name']}</u> v{suite['status']['versions']['reconciled']}"])
                    suiteOptions.append(suite['metadata']['name'])
            except ResourceNotFoundError:
                self.fatalError("No MAS instances were detected on the cluster (Suite.core.mas.ibm.com/v1 API is not available).  See log file for details")

            if len(suiteOptions) == 0:
                self.fatalError("No MAS instances were detected on the cluster (No instances of Suite.core.mas.ibm.com/v1 found).  See log file for details")

            suiteCompleter = WordCompleter(suiteOptions)
            print()
            instanceId = self.promptForString("MAS instance ID", completer=suiteCompleter, validator=InstanceIDValidator())

            self.printH1("Uninstall MAS Dependencies")
            self.printDescription([
                "If you choose to uninstall Certificate Manager, all other options will be automatically set to uninstall",
                "Other workload on the cluster may be dependant on the Certificate Manager installation, so proceed with caution when choosing 'Yes'"
            ])
            uninstallCertManager = self.yesOrNo("Uninstall Certificate Manager")
            if uninstallCertManager:
                # If you choose to uninstall Cert-Manager, everything will be uninstalled
                uninstallGrafana = True
                uninstallIBMCatalog = True
                uninstallCommonServices = True
                uninstallUDS = True
                uninstallMongoDb = True
                uninstallSLS = True
            else:
                self.printDescription(["If you choose to uninstall MongoDb, IBM Suite License Service will be automatically set to uninstall as well"])
                uninstallMongoDb = self.yesOrNo("Uninstall MongoDb")
                if uninstallMongoDb:
                    # If you are removing MongoDb then SLS needs to be uninstalled too
                    uninstallSLS = True
                else:
                    uninstallSLS = self.yesOrNo("Uninstall IBM Suite Licensing Service")

                uninstallGrafana = self.yesOrNo("Uninstall Grafana")
                self.printDescription(["If you choose to uninstall the IBM Operator Catalog, IBM Common Services, IBM User Data Services, &amp; IBM Suite License Service will be automatically set to uninstall as well"])
                uninstallIBMCatalog = self.yesOrNo("Uninstall IBM operator Catalog")
                if uninstallIBMCatalog:
                    # If you choose to uninstall IBM Operator Catalog, everything from the catalog will be uninstalled
                    uninstallCommonServices = True
                    uninstallUDS = True
                    uninstallSLS = True
                else:
                    uninstallCommonServices = self.yesOrNo("Uninstall IBM Common Services")
                    uninstallUDS = self.yesOrNo("Uninstall IBM User Data Services")

        else:
            # Non-interactive mode
            if not verifyMasInstance(self.dynamicClient, instanceId):
                self.fatalError(f"MAS Instance {instanceId} not found on this cluster</Red>")

        # Default to Red Hat Cert-Manager, and check if IBM cert-manager is installed
        certManagerProvider = "redhat"
        try:
            # Check if 'ibm-common-services' namespace exist, this will throw NotFoundError exception when not found.
            namespaceAPI = self.dynamicClient.resources.get(api_version="v1", kind="Namespace")
            namespaceAPI.get(name="ibm-common-services")

            podsAPI = self.dynamicClient.resources.get(api_version="v1", kind="Pod")
            podsList = podsAPI.get(namespace="ibm-common-services")
            for pod in podsList.items:
                if pod is not None and "cert-manager-cainjector" in pod.metadata.name:
                    certManagerProvider = "ibm"
        except NotFoundError:
            print()
            # ibm cert manager not found, proceed with default redhat.

        self.printH1("Review Settings")
        self.printSummary("Instance ID", instanceId)
        self.printSummary("Uninstall Cert-Manager", f"{uninstallCertManager} ({certManagerProvider})")
        self.printSummary("Uninstall Grafana", uninstallGrafana)
        self.printSummary("Uninstall IBM Operator Catalog", uninstallIBMCatalog)
        self.printSummary("Uninstall IBM Common Services", uninstallCommonServices)
        self.printSummary("Uninstall UDS", uninstallUDS)
        self.printSummary("Uninstall MongoDb", uninstallMongoDb)
        self.printSummary("Uninstall SLS", uninstallSLS)

        if not self.noConfirm:
            print()
            continueWithUninstall = self.yesOrNo("Proceed with these settings")

        if self.noConfirm or continueWithUninstall:
            self.createTektonFileWithDigest()

            self.printH1("Launch uninstall")
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

            with Halo(text=f'Submitting PipelineRun for {instanceId} uninstall', spinner=self.spinner) as h:
                pipelineURL = launchUninstallPipeline(
                    dynClient=self.dynamicClient,
                    instanceId=instanceId,
                    certManagerProvider="redhat",
                    uninstallCertManager=uninstallCertManager,
                    uninstallGrafana=uninstallGrafana,
                    uninstallCatalog=uninstallCommonServices,
                    uninstallCommonServices=uninstallCommonServices,
                    uninstallUDS=uninstallUDS,
                    uninstallMongoDb=uninstallMongoDb,
                    uninstallSLS=uninstallSLS,
                    droNamespace=droNamespace
                )
                if pipelineURL is not None:
                    h.stop_and_persist(symbol=self.successIcon, text=f"PipelineRun for {instanceId} uninstall submitted")
                    print_formatted_text(HTML(f"\nView progress:\n  <Cyan><u>{pipelineURL}</u></Cyan>\n"))
                else:
                    h.stop_and_persist(symbol=self.failureIcon, text=f"Failed to submit PipelineRun for {instanceId} uninstall, see log file for details")
                    print()
