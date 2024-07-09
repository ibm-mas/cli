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

import re
import logging
import logging.handlers
from halo import Halo
from prompt_toolkit import print_formatted_text, HTML
from prompt_toolkit.completion import WordCompleter

from openshift.dynamic.exceptions import NotFoundError, ResourceNotFoundError

from ..cli import BaseApp
from ..validators import StorageClassValidator
from .argParser import updateArgParser

from mas.devops.ocp import createNamespace, getStorageClasses
from mas.devops.mas import listMasInstances
from mas.devops.tekton import preparePipelinesNamespace, installOpenShiftPipelines, updateTektonDefinitions, launchUpdatePipeline


logger = logging.getLogger(__name__)

class UpdateApp(BaseApp):

    def update(self, argv):
        """
        Uninstall MAS instance
        """
        args = updateArgParser.parse_args(args=argv)
        self.noConfirm = args.no_confirm

        if args.mas_catalog_version:
            # Non-interactive mode
            logger.debug("Maximo Operator Catalog version is set, so we assume already connected to the desired OCP")
        else:
            # Interactive mode
            self.printH1("Set Target OpenShift Cluster")
            # Connect to the target cluster
            self.connect()

        if self.dynamicClient is None:
            self.fatalError("The Kubernetes dynamic Client is not available.  See log file for details")

        if args.mas_catalog_version is not None:
            # Non-Interactive mode
            pass
        else:
            # Interactive mode
            self.reviewCurrentCatalog()
            self.reviewMASInstance()
            self.chooseCatalog()

            self.validateCatalog()

            # Validations
            self.printH1("Dependency Update Checks")
            with Halo(text='Checking for IBM Watson Discovery', spinner=self.spinner) as h:
                if self.isWatsonDiscoveryInstalled():
                    h.stop_and_persist(symbol=self.failureIcon, text=f"IBM Watson Discovery is installed")
                    self.fatalError("Watson Discovery is currently installed in the instance of Cloud Pak for Data that is managed by the MAS CLI (in the ibm-cpd namespace), this is no longer supported and the update can not proceed as a result. Please contact IBM support for assistance")
                else:
                    h.stop_and_persist(symbol=self.successIcon, text=f"IBM Watson Discovery is not installed")

            with Halo(text='Checking for IBM Certificate-Manager', spinner=self.spinner) as h:
                if self.isIBMCertManagerInstalled():
                    h.stop_and_persist(symbol=self.successIcon, text=f"IBM Certificate-Manager will be replaced by Red Hat Certificate-Manager")
                    self.setParam("cert_manager_action", "install")
                    self.setParam("cert_manager_provider", "redhat")
                    self.printHighlight([
                        "<u>Migration Notice</u>",
                        "IBM Certificate-Manager is currently running in the ${CERT_MANAGER_NAMESPACE} namespace",
                        "This will be uninstalled and replaced by Red Hat Certificate-Manager as part of this update",
                        ""
                    ])
                else:
                    h.stop_and_persist(symbol=self.successIcon, text=f"IBM Certificate-Manager is not installed")

            self.detectUDS()
            self.detectGrafana4()
            self.detectMongoDb()
            self.detectCP4D()

            print()
            print("Params:")
            for param in self.params:
                print(f"{param} = {self.getParam(param)}")


        if not self.noConfirm:
            print()
            self.printDescription([
                "Please carefully review your choices above, correcting mistakes now is much easier than after the update has begun"
            ])
            continueWithUpdate = self.yesOrNo("Proceed with these settings")

        # Prepare the namespace and launch the installation pipeline
        if self.noConfirm or continueWithUpdate:
            self.printH1("Launch Update")
            pipelinesNamespace = f"mas-pipelines"

            with Halo(text='Validating OpenShift Pipelines installation', spinner=self.spinner) as h:
                installOpenShiftPipelines(self.dynamicClient)
                h.stop_and_persist(symbol=self.successIcon, text=f"OpenShift Pipelines Operator is installed and ready to use")

            with Halo(text=f'Preparing namespace ({pipelinesNamespace})', spinner=self.spinner) as h:
                createNamespace(self.dynamicClient, pipelinesNamespace)
                preparePipelinesNamespace(dynClient=self.dynamicClient)
                h.stop_and_persist(symbol=self.successIcon, text=f"Namespace is ready ({pipelinesNamespace})")

            with Halo(text=f'Installing latest Tekton definitions (v{self.version})', spinner=self.spinner) as h:
                updateTektonDefinitions(pipelinesNamespace, self.tektonDefsPath)
                h.stop_and_persist(symbol=self.successIcon, text=f"Latest Tekton definitions are installed (v{self.version})")

            with Halo(text=f"Submitting PipelineRun for MAS update", spinner=self.spinner) as h:
                pipelineURL = launchUpdatePipeline(dynClient=self.dynamicClient, params=self.params)
                if pipelineURL is not None:
                    h.stop_and_persist(symbol=self.successIcon, text=f"PipelineRun for MAS update submitted")
                    print_formatted_text(HTML(f"\nView progress:\n  <Cyan><u>{pipelineURL}</u></Cyan>\n"))
                else:
                    h.stop_and_persist(symbol=self.failureIcon, text=f"Failed to submit PipelineRun for MAS update, see log file for details")
                    print()

    def reviewCurrentCatalog(self) -> None:
        catalogsAPI = self.dynamicClient.resources.get(api_version="operators.coreos.com/v1alpha1", kind="CatalogSource")
        try:
            catalog = catalogsAPI.get(name="ibm-operator-catalog", namespace="openshift-marketplace")
            catalogDisplayName = catalog.spec.displayName
            catalogImage = catalog.spec.image

            m = re.match(r".+(?P<catalogId>v[89]-(?P<catalogVersion>[0-9]+)-amd64)", catalogDisplayName)
            if m:
                # catalogId = v8-yymmdd-amd64
                # catalogVersion = yymmdd
                self.installedCatalogId = m.group("catalogId")
            elif re.match(r".+v8-amd64", catalogDisplayName):
                self.installedCatalogId = "v8-amd64"
            else:
                self.installedCatalogId = None
                self.printWarning(f"Unable to determine identity & version of currently installed ibm-maximo-operator-catalog")

            self.printH1("Review Installed Catalog")
            self.printDescription([
                f"The currently installed Maximo Operator Catalog is <u>{catalogDisplayName}</u>",
                f" <u>{catalogImage}</u>"
            ])
        except NotFoundError as e:
            self.fatalError("Unable to locate existing install of the IBM Maximo Operator Catalog", e)

    def reviewMASInstance(self) -> None:
        self.printH1("Review MAS Instances")
        self.printDescription(["The following MAS intances are installed on the target cluster and will be affected by the catalog update:"])
        try:
            suites = listMasInstances(self.dynamicClient)
            for suite in suites:
                self.printDescription([f"- <u>{suite['metadata']['name']}</u> v{suite['status']['versions']['reconciled']}"])
        except ResourceNotFoundError as e:
            self.fatalError("No MAS instances were detected on the cluster (Suite.core.mas.ibm.com/v1 API is not available).  See log file for details")

    def chooseCatalog(self) -> None:
        self.printH1("Select IBM Maximo Operator Catalog Version")
        self.printDescription([
            "Select MAS Catalog",
            "  1) June 25 2024 Update (MAS 9.0.0, 8.11.12, &amp; 8.10.15)",
            "  2) May 28 2024 Update (MAS 8.11.11 &amp; 8.10.14)"
        ])

        catalogOptions = [
           "v9-240625-amd64", "v8-240528-amd64"
        ]
        self.promptForListSelect("Select catalog version", catalogOptions, "mas_catalog_version", default=1)

    def validateCatalog(self) -> None:
        if self.installedCatalogId is not None and self.installedCatalogId > self.getParam("mas_catalog_version"):
            self.fatalError(f"Selected catalog is older than the currently installed catalog.  Unable to update catalog from {self.installedCatalogId} to {self.getParam('mas_catalog_version')}")

    def isWatsonDiscoveryInstalled(self) -> bool:
        try:
            wdAPI = self.dynamicClient.resources.get(api_version="discovery.watson.ibm.com/v1", kind="WatsonDiscovery")
            wds = wdAPI.get(namespace="ibm-cpd").to_dict()['items']
            if len(wds) > 0:
                return True
            return False
        except (ResourceNotFoundError, NotFoundError) as e:
            # Watson Discovery has never been installed on this cluster
            return False

    def isIBMCertManagerInstalled(self) -> bool:
        """
        Check whether the deprecated IBM Certificate-Manager is installed, if it is then we will
        automatically migrate to Red Hat Certificate-Manager
        """

        try:
            # Check if 'ibm-common-services' namespace exist, this will throw NotFoundError exception when not found
            namespaceAPI = self.dynamicClient.resources.get(api_version="v1", kind="Namespace")
            namespaceAPI.get(name="ibm-common-services")

            podsAPI = self.dynamicClient.resources.get(api_version="v1", kind="Pod")
            podsList = podsAPI.get(namespace="ibm-common-services")
            for pod in podsList.items:
                if pod is not None and "cert-manager-cainjector" in pod.metadata.name:
                    logger.debug("Found IBM Certificate-Manager in ibm-common-services namespace")
                    return True
            logger.debug("There is an ibm-common-services namespace, but we did not find the IBM Certificate-Manager installation")
            return False
        except NotFoundError:
            logger.debug("There is no ibm-common-services namespace")
            return False

    def detectGrafana4(self) -> bool:
        with Halo(text='Checking for Grafana Operator v4', spinner=self.spinner) as h:
            try:
                grafanaAPI = self.dynamicClient.resources.get(api_version="integreatly.org/v1alpha1", kind="Grafana")
                grafanaVersion4s = grafanaAPI.get().to_dict()["items"]

                # For testing, comment out the lines above and set grafanaVersion4s to a simple list
                # grafanaVersion4s = ["hello"]
                if len(grafanaVersion4s) > 0:
                    h.stop_and_persist(symbol=self.successIcon, text=f"Grafana Operator v4 instance will be updated to v5")
                    self.printDescription([
                        "<u>Dependency Upgrade Notice</u>",
                        "Grafana Operator v4 is currently installed and will be updated to v5",
                        "- Grafana v5 instance will have a new URL and admin password",
                        "- User accounts set up in the v4 instance will not be migrated"
                    ])
                    self.setParam("grafana_v5_upgrade", "true")
                else:
                    h.stop_and_persist(symbol=self.successIcon, text=f"Grafana Operator v4 is not installed")
                return
            except (ResourceNotFoundError, NotFoundError) as e:
                h.stop_and_persist(symbol=self.successIcon, text=f"Grafana Operator v4 is not installed")

    def detectMongoDb(self) -> None:
        with Halo(text='Checking for MongoDb CE', spinner=self.spinner) as h:
            # TODO: Replace this with a lookup to just use whatever is already set up
            # because we should not be changing the scale of the mongodb cluster during
            # and update
            if self.isSNO():
                self.setParam("mongodb_replicas", "1")
            else:
                self.setParam("mongodb_replicas", "3")

            # Determine the namespace
            try:
                mongoDbAPI = self.dynamicClient.resources.get(api_version="mongodbcommunity.mongodb.com/v1", kind="MongoDBCommunity")
                mongoClusters = mongoDbAPI.get().to_dict()["items"]

                if len(mongoClusters) > 0:
                    mongoNamespace = mongoClusters[0]["metadata"]["namespace"]
                    currentMongoVersion = mongoClusters[0]["status"]["version"]

                    self.setParam("mongodb_namespace", mongoNamespace)

                    # Important:
                    # This CLI can run independent of the ibm.mas_devops collection, so we cannot reference
                    # the case bundles in there anymore
                    # Longer term we will centralise this information inside the mas-devops python collection,
                    # where it can be made available to both the ansible collection and this python package.
                    mongoVersions = {
                        "v8-240528-amd64": "5.0.23",
                        "v9-240625-amd64": "6.0.12"
                    }

                    targetMongoVersion = mongoVersions[self.getParam('mas_catalog_version')]
                    self.setParam("mongodb_version", targetMongoVersion)

                    targetMongoVersionMajor = targetMongoVersion.split(".")[0]
                    currentMongoVersionMajor = currentMongoVersion.split(".")[0]

                    if targetMongoVersionMajor > currentMongoVersionMajor:
                        # Let users know that Mongo will be upgraded if existing MongoDb major.minor version
                        # is lower than the target major version
                        # We don't show this message for normal updates, e.g. 5.0.1 to 5.0.2
                        if self.noConfirm and self.getParam(f"mongodb_v{targetMongoVersionMajor}_upgrade") != "true":
                            # The user has chosen not to provide confirmation but has not provided the flag to pre-approve the mongo major version update
                            h.stop_and_persist(symbol=self.failureIcon, text=f"MongoDb CE {currentMongoVersion} needs to be updated to {targetMongoVersion}")
                            self.showMongoDependencyUpdateNotice(currentMongoVersion, targetMongoVersion)
                            self.fatalError(f"By choosing {self.getParam('mas_catalog_version')} you must confirm MongoDb update to version {targetMongoVersionMajor} using '--mongodb-v{targetMongoVersionMajor}-upgrade' when using '--no-confirm'")
                        elif self.getParam(f"mongodb_v{targetMongoVersionMajor}_upgrade") != "true":
                            # The user has not pre-approved the major version update
                            h.stop_and_persist(symbol=self.successIcon, text=f"MongoDb CE {currentMongoVersion} needs to be updated to {targetMongoVersion}")
                            self.showMongoDependencyUpdateNotice(currentMongoVersion, targetMongoVersion)
                            if not self.yesOrNo(f"Confirm update from MongoDb {currentMongoVersion} to {targetMongoVersion}", f"mongodb_v{targetMongoVersionMajor}_upgrade"):
                                # If the user did not approve the update, abort
                                exit(1)
                        else:
                            h.stop_and_persist(symbol=self.successIcon, text=f"MongoDb CE will be updated from {currentMongoVersion} to {targetMongoVersion}")
                            self.showMongoDependencyUpdateNotice(currentMongoVersion, targetMongoVersion)
                    elif targetMongoVersion < currentMongoVersion:
                        h.stop_and_persist(symbol=self.failureIcon, text=f"MongoDb CE {currentMongoVersion} cannot be downgraded to {targetMongoVersion}")
                        self.showMongoDependencyUpdateNotice(currentMongoVersion, targetMongoVersion)
                        self.fatalError(f"Existing MongoDB Community Edition installation at version {currentMongoVersion} cannot be downgraded to version {targetMongoVersion}")
                    else:
                        h.stop_and_persist(symbol=self.successIcon, text=f"MongoDb CE is aleady installed at version {targetMongoVersion}")
                else:
                    # There's no MongoDb instance installed in the cluster, so nothing to do
                    h.stop_and_persist(symbol=self.successIcon, text=f"No MongoDb CE instances found")
            except (ResourceNotFoundError, NotFoundError) as e:
                # There's no MongoDb instance installed in the cluster, so nothing to do
                h.stop_and_persist(symbol=self.successIcon, text=f"MongoDb CE is not installed")

    def showMongoDependencyUpdateNotice(self, currentMongoVersion, targetMongoVersion) -> None:
        self.printHighlight([
            "",
            "<u>Dependency Update Notice</u>",
            f"MongoDB Community Edition is currently running version {currentMongoVersion} and will be updated to {targetMongoVersion}",
            "It is recommended that you backup your MongoDB instance before proceeding:",
            "  <u>https://www.ibm.com/docs/en/mas-cd/continuous-delivery?topic=suite-backing-up-mongodb-maximo-application</u>",
            ""
        ])

    def showUDSUpdateNotice(self) -> None:
        self.printHighlight([
            "",
            "<u>Dependency Update Notice</u>",
            "IBM User Data Services (UDS) is currently installed and will be replaced by IBM Data Reporter Operator (DRO)",
            "UDS will be uninstalled and <u>all MAS instances</u> will be re-configured to use DRO",
            ""
        ])

    def detectUDS(self) -> None:
        with Halo(text='Checking for IBM User Data Services', spinner=self.spinner) as h:
            try:
                analyticsProxyAPI = self.dynamicClient.resources.get(api_version="uds.ibm.com/v1", kind="AnalyticsProxy")
                analyticsProxies = analyticsProxyAPI.get(namespace="ibm-common-services").to_dict()['items']

                # Useful for testing: comment out the two lines above and set analyticsProxies to a
                # simple list to trigger to UDS migration logic.
                # analyticsProxies = ["foo"]
                if len(analyticsProxies) == 0:
                    logger.debug("UDS is not currently installed on this cluster")
                    h.stop_and_persist(symbol=self.successIcon, text=f"IBM User Data Services is not installed")
                else:
                    h.stop_and_persist(symbol=self.successIcon, text=f"IBM User Data Services must be migrated to IBM Data Reporter Operator")

                    if self.noConfirm and self.getParam("dro_migration") != "true":
                        # The user has chosen not to provide confirmation but has not provided the flag to pre-approve the migration
                        h.stop_and_persist(symbol=self.failureIcon, text=f"IBM User Data Services needs to be migrated to IBM Data Reporter Operator")
                        self.showUDSUpdateNotice()
                        self.fatalError(f"By choosing {self.getParam('mas_catalog_version')} you must confirm the migration to DRO using '--dro-migration' when using '--no-confirm'")
                    elif self.noConfirm and self.getParam("dro_storage_class") is None:
                        # The user has not provided the storage class to use for DRO, but has disabled confirmations/interactive prompts
                        h.stop_and_persist(symbol=self.failureIcon, text=f"IBM User Data Services needs to be migrated to IBM Data Reporter Operator")
                        self.showUDSUpdateNotice()
                        self.fatalError(f"By choosing {self.getParam('mas_catalog_version')} you must provide the storage class to use for the migration to DRO using '--dro-storage-class' when using '--no-confirm'")
                    else:
                        h.stop_and_persist(symbol=self.successIcon, text="IBM User Data Services needs to be migrated to IBM Data Reporter Operator")
                        self.showUDSUpdateNotice()
                        if not self.yesOrNo("Confirm migration from UDS to DRO", "dro_migration"):
                            # If the user did not approve the update, abort
                            exit(1)
                        self.printDescription([
                            "",
                            "Select the storage class for DRO to use from the list below:"
                        ])
                        for storageClass in getStorageClasses(self.dynamicClient):
                            print_formatted_text(HTML(f"<LightSlateGrey>  - {storageClass.metadata.name}</LightSlateGrey>"))
                        self.promptForString("DRO storage class", "dro_storage_class", validator=StorageClassValidator())

            except (ResourceNotFoundError, NotFoundError) as e:
                # UDS has never been installed on this cluster
                logger.debug("UDS has not been installed on this cluster before")
                h.stop_and_persist(symbol=self.successIcon, text=f"IBM User Data Services is not installed")

    def detectCP4D(self) -> bool:
        # Important:
        # This CLI can run independent of the ibm.mas_devops collection, so we cannot reference
        # the case bundles in there anymore
        # Longer term we will centralise this information inside the mas-devops python collection,
        # where it can be made available to both the ansible collection and this python package.
        cp4dVersions = {
            "v8-240528-amd64": "4.8.0",
            "v9-240625-amd64": "4.6.6"
        }

        with Halo(text='Checking for IBM Cloud Pak for Data', spinner=self.spinner) as h:
            try:
                # cpdAPI = self.dynamicClient.resources.get(api_version="cpd.ibm.com/v1", kind="Ibmcpd")
                # cpds = cpdAPI.get().to_dict()["items"]

                # For testing, comment out the lines above and set cpds to a simple list
                cpds = [{
                    "metadata": {"namespace": "ibm-cpd" },
                    "spec": {
                        "version": "4.6.6",
                        "storageClass": "default",
                        "zenCoreMetadbStorageClass": "default"
                    }
                }]


                if len(cpds) > 0:
                    cpdInstanceNamespace = cpds[0]["metadata"]["namespace"]
                    cpdInstanceVersion = cpds[0]["spec"]["version"]
                    cpdTargetVersion = cp4dVersions[self.getParam("mas_catalog_version")]

                    currentCpdVersionMajorMinor = f"{cpdInstanceVersion.split('.')[0]}.{cpdInstanceVersion.split('.')[1]}"
                    targetCpdVersionMajorMinor = f"{cpdTargetVersion.split('.')[0]}.{cpdTargetVersion.split('.')[1]}"

                    if currentCpdVersionMajorMinor < targetCpdVersionMajorMinor:
                        # We only show the "backup first" notice for minor CP4D updates
                        self.printHighlight([
                            "<u>Dependency Update Notice</u>",
                            f"Cloud Pak For Data is currently running version {cpdInstanceVersion} and will be updated to version {targetCpdVersionMajorMinor}",
                            "It is recommended that you backup your Cloud Pak for Data instance before proceeding:"
                            "  <u>https://www.ibm.com/docs/en/cloud-paks/cp-data/4.8.x?topic=administering-backing-up-restoring-cloud-pak-data</u>"
                        ])

                    if cpdInstanceVersion < cpdTargetVersion:
                        # We have to update CP4D

                        # Lookup the storage classes already used by CP4D
                        # Note: this should be done by the Ansible role, but isn't
                        if "storageClass" in cpds[0]["spec"]:
                            cpdFileStorage = cpds[0]["spec"]["storageClass"]
                        elif "fileStorageClass" in cpds[0]["spec"]:
                            cpdFileStorage = cpds[0]["spec"]["fileStorageClass"]
                        else:
                            self.fatalError("Unable to determine the file storage class used in IBM Cloud Pak for Data")

                        if "zenCoreMetadbStorageClass" in cpds[0]["spec"]:
                            cpdBlockStorage = cpds[0]["spec"]["zenCoreMetadbStorageClass"]
                        elif "blockStorageClass" in cpds[0]["spec"]:
                            cpdBlockStorage = cpds[0]["spec"]["blockStorageClass"]
                        else:
                            self.fatalError("Unable to determine the block storage class used in IBM Cloud Pak for Data")

                        # Set the desired storage classes (the same ones already in use)
                        self.setParam("storage_class_rwx", cpdFileStorage)
                        self.setParam("storage_class_rwo", cpdBlockStorage)

                        # Set the desired target version
                        self.setParam("cpd_product_version", cpdTargetVersion)
                        self.setParam("cp4d_update", "true")
                        self.setParam("skip_entitlement_key_flag", "true")

                        self.detectCpdService('ws.ws.cpd.ibm.com/v1', 'Watson Studio', 'ws')
                        self.detectCpdService('wmlbases.wml.cpd.ibm.com/v1', 'Watson Machine Learning', 'wml')
                        self.detectCpdService('analyticsengines.ae.cpd.ibm.com/v1', 'Analytics Engine', 'analyticsengine')
                        self.detectCpdService('woservices.wos.cpd.ibm.com/v1', 'Watson Openscale', 'openscale')
                        self.detectCpdService('spss.spssmodeler.cpd.ibm.com/v1', 'SPSS Modeler', 'spss')
                        self.detectCpdService('caservices.ca.cpd.ibm.com/v1', 'Cognos Analytics', 'cognos_analytics')

                        h.stop_and_persist(symbol=self.successIcon, text=f"Grafana Operator v4 instance will be updated to v5")
                        self.printDescription([
                            "<u>Dependency Upgrade Notice</u>",
                            "Grafana Operator v4 is currently installed and will be updated to v5",
                            "- Grafana v5 instance will have a new URL and admin password",
                            "- User accounts set up in the v4 instance will not be migrated"
                        ])
                        self.setParam("grafana_v5_upgrade", "true")
                    else:
                    h.stop_and_persist(symbol=self.successIcon, text=f"Grafana Operator v4 is not installed")
                return
            except (ResourceNotFoundError, NotFoundError) as e:
                h.stop_and_persist(symbol=self.successIcon, text=f"Grafana Operator v4 is not installed")

    def detectCpdService(self, api: str, name: str, kind: str) -> None:
        try:
            # cpdServiceAPI = self.dynamicClient.resources.get(api_version=api, kind=kind)
            # cpdServices = cpdServiceAPI.get().to_dict()["items"]

            # For testing, comment out the lines above and set cpds to a simple list
            cpdServices = [{
                "spec": {
                    "version": "4.6.6",
                }
            }]

        except (ResourceNotFoundError, NotFoundError) as e:
            # No action required for this service
            pass
