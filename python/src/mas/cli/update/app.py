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

from mas.devops.ocp import createNamespace, getStorageClasses, getConsoleURL
from mas.devops.mas import listMasInstances
from mas.devops.tekton import preparePipelinesNamespace, installOpenShiftPipelines, updateTektonDefinitions, launchUpdatePipeline


logger = logging.getLogger(__name__)

class UpdateApp(BaseApp):

    def update(self, argv):
        """
        Uninstall MAS instance
        """
        self.args = updateArgParser.parse_args(args=argv)
        self.noConfirm = self.args.no_confirm
        self.devMode = self.args.dev_mode

        if self.args.mas_catalog_version:
            # Non-interactive mode
            logger.debug("Maximo Operator Catalog version is set, so we assume already connected to the desired OCP")
            requiredParams = ["mas_catalog_version"]
            optionalParams = [
                "db2_namespace",
                "mongodb_namespace",
                "mongodb_v5_upgrade",
                "mongodb_v6_upgrade",
                "mongodb_v7_upgrade",
                "kafka_namespace",
                "kafka_provider",
                "dro_migration",
                "dro_storage_class",
                "dro_namespace",
                "skip_pre_check",
                "dev_mode",
                "cpd_product_version",
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
                elif key in [ "no_confirm", "help"]:
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

        self.reviewCurrentCatalog()
        self.reviewMASInstance()

        if self.args.mas_catalog_version is None:
            # Interactive mode
            self.chooseCatalog()

        # Validations
        if not self.devMode:
            self.validateCatalog()

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
        self.detectDb2uOrKafka("db2")
        self.detectDb2uOrKafka("kafka")
        self.detectCP4D()

        print()

        self.printH1("Review Settings")
        self.printDescription([
            "Connected to:",
            f" - <u>{getConsoleURL(self.dynamicClient)}</u>"
        ])

        self.printH2("IBM Maximo Operator Catalog")
        self.printSummary("Installed Catalog", self.installedCatalogId)
        self.printSummary("Updated Catalog", self.getParam("mas_catalog_version"))

        self.printH2("Supported Dependency Updates")
        if self.getParam("db2_namespace") != "":
            self.printSummary("IBM Db2", f"All Db2uCluster instances in {self.getParam('db2_namespace')}")
        else:
            self.printSummary("IBM Db2", "No action required")

        if self.getParam("mongodb_namespace") != "":
            self.printSummary("MongoDb CE", f"All MongoDbCommunity instances in {self.getParam('mongodb_namespace')}")
        else:
            self.printSummary("MongoDb CE", "No action required")

        if self.getParam("kafka_namespace") != "":
            self.printSummary("Apache Kafka", f"All Kafka instances in {self.getParam('kafka_namespace')}")
        else:
            self.printSummary("Apache Kafka", "No action required")

        if self.getParam("cp4d_update") != "":
            self.printSummary("IBM Cloud Pak for Data", f"Platform and services in ibm-cpd")
        else:
            self.printSummary("IBM Cloud Pak for Data", "No action required")

        self.printH2("Required Migrations")
        self.printSummary("IBM Certificate-Manager", "Migrate to Red Hat Certificate-Manager" if self.getParam("cert_manager_action") != "" else "No action required")
        self.printSummary("IBM User Data Services", "Migrate to IBM Data Reporter Operator" if self.getParam("dro_migration") != "" else "No action required")
        self.printSummary("Grafana v4 Operator", "Migrate to Grafana v5 Operator" if self.getParam("grafana_v5_upgrade") != "" else "No action required")

        if not self.noConfirm:
            print()
            self.printDescription([
                "Please carefully review your choices above, correcting mistakes now is much easier than after the update has begun"
            ])
            continueWithUpdate = self.yesOrNo("Proceed with these settings")
        # Prepare the namespace and launch the installation pipeline
        if self.noConfirm or continueWithUpdate:
            self.createTektonFileWithDigest()

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
            "  1) Oct 03 2024 Update (MAS 9.0.3, 8.11.15, &amp; 8.10.18)",
            "  2) Aug 27 2024 Update (MAS 9.0.2, 8.11.14, &amp; 8.10.17)",
            "  3) July 30 2024 Update (MAS 9.0.1, 8.11.13, &amp; 8.10.16)"
        ])

        catalogOptions = [
           "v9-241003-amd64", "v9-240827-amd64", "v9-240730-amd64"
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
                    defaultMongoVersion = "6.0.12"
                    mongoVersions = {
                        "v9-240625-amd64": "6.0.12",
                        "v9-240730-amd64": "6.0.12",
                        "v9-240827-amd64": "6.0.12",
                        "v9-241003-amd64": "6.0.12"
                    }
                    catalogVersion = self.getParam('mas_catalog_version')
                    if catalogVersion in mongoVersions:
                        targetMongoVersion = mongoVersions[self.getParam('mas_catalog_version')]
                    else:
                        targetMongoVersion = defaultMongoVersion

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
                            print()
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
                        if self.getParam("dro_migration") == "true" and self.getParam("dro_storage_class") is None:  
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

                if self.getParam("dro_migration") == "true":
                    self.setParam("uds_action", "install-dro")

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
            "v9-240625-amd64": "4.8.0",
            "v9-240730-amd64": "4.8.0",
            "v9-240827-amd64": "4.8.0",
            "v9-241003-amd64": "4.8.0"
            
        }

        with Halo(text='Checking for IBM Cloud Pak for Data', spinner=self.spinner) as h:
            try:
                cpdAPI = self.dynamicClient.resources.get(api_version="cpd.ibm.com/v1", kind="Ibmcpd")
                cpds = cpdAPI.get().to_dict()["items"]

                # For testing, comment out the lines above and set cpds to a simple list
                # cpds = [{
                #     "metadata": {"namespace": "ibm-cpd" },
                #     "spec": {
                #         "version": "4.6.6",
                #         "storageClass": "default",
                #         "zenCoreMetadbStorageClass": "default"
                #     }
                # }]

                if len(cpds) > 0:
                    cpdInstanceNamespace = cpds[0]["metadata"]["namespace"]
                    cpdInstanceVersion = cpds[0]["spec"]["version"]
                    if self.args.cpd_product_version:
                        cpdTargetVersion = self.getParam("cpd_product_version")
                    else:
                        cpdTargetVersion = cp4dVersions[self.getParam("mas_catalog_version")]

                    currentCpdVersionMajorMinor = f"{cpdInstanceVersion.split('.')[0]}.{cpdInstanceVersion.split('.')[1]}"
                    targetCpdVersionMajorMinor = f"{cpdTargetVersion.split('.')[0]}.{cpdTargetVersion.split('.')[1]}"

                    if cpdInstanceVersion < cpdTargetVersion:
                        # We have to update CP4D
                        h.stop_and_persist(symbol=self.successIcon, text=f"IBM Cloud Pak for Data {cpdInstanceVersion} needs to be updated to {cpdTargetVersion}")

                        if currentCpdVersionMajorMinor < targetCpdVersionMajorMinor:
                            # We only show the "backup first" notice for minor CP4D updates
                            self.printHighlight([
                                ""
                                "<u>Dependency Update Notice</u>",
                                f"Cloud Pak For Data is currently running version {cpdInstanceVersion} and will be updated to version {cpdTargetVersion}",
                                "It is recommended that you backup your Cloud Pak for Data instance before proceeding:",
                                "  <u>https://www.ibm.com/docs/en/cloud-paks/cp-data/5.0.x?topic=administering-backing-up-restoring-cloud-pak-data</u>"
                            ])

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

                        self.detectCpdService('WS', 'ws.cpd.ibm.com/v1beta1', 'Watson Studio', "cp4d_update_ws")
                        self.detectCpdService('WmlBase', 'wml.cpd.ibm.com/v1beta1', 'Watson Machine Learning', "cp4d_update_wml")
                        self.detectCpdService('AnalyticsEngine', 'ae.cpd.ibm.com/v1', 'Analytics Engine', "cp4d_update_spark")
                        self.detectCpdService('WOService', 'wos.cpd.ibm.com/v1', 'Watson Openscale', "cp4d_update_wos")
                        self.detectCpdService('Spss', 'spssmodeler.cpd.ibm.com/v1', 'SPSS Modeler', "cp4d_update_spss")
                        self.detectCpdService('CAService', 'ca.cpd.ibm.com/v1', 'Cognos Analytics', "cp4d_update_cognos")
                    else:
                        h.stop_and_persist(symbol=self.successIcon, text=f"IBM Cloud Pak for Data is already installed at version {cpdTargetVersion}")
                else:
                    h.stop_and_persist(symbol=self.successIcon, text=f"No IBM Cloud Pak for Data instance found")
            except (ResourceNotFoundError, NotFoundError) as e:
                h.stop_and_persist(symbol=self.successIcon, text=f"IBM Cloud Pak for Data is not installed")

    def detectCpdService(self, kind: str, api: str, name: str, param: str) -> None:
        try:
            cpdServiceAPI = self.dynamicClient.resources.get(api_version=api, kind=kind)
            cpdServices = cpdServiceAPI.get().to_dict()["items"]

            if len(cpdServices) > 0:
                logger.debug(f"{name} is included in CP4D update")
                self.setParam(param, "true")
            else:
                logger.debug(f"{name} is not included in CP4D update")
                self.setParam(param, "false")

        except (ResourceNotFoundError, NotFoundError) as e:
            # No action required for this service
            logger.debug(f"{name} is not included in CP4D update: {e}")
            self.setParam(param, "false")

    def detectDb2uOrKafka(self, mode: str) -> bool:
        if mode == "db2":
            haloStartingMessage = "Checking for Db2uCluster instances to update"
            apiVersion = "db2u.databases.ibm.com/v1"
            kind = "Db2uCluster"
            paramName = "db2_namespace"
        elif mode == "kafka":
            haloStartingMessage = "Checking for Kafka instances to update"
            apiVersion = "kafka.strimzi.io/v1beta2"
            kind = "Kafka"
            paramName = "kafka_namespace"
        else:
            self.fatalError("Unexpected error")

        with Halo(text=haloStartingMessage, spinner=self.spinner) as h:
            try:
                k8sAPI = self.dynamicClient.resources.get(api_version=apiVersion, kind=kind)
                instances = k8sAPI.get().to_dict()["items"]

                logger.debug(f"Found {len(instances)} {kind} instances on the cluster")
                if len(instances) > 0:
                    # If the user provided the namespace using --db2-namespace then we don't have any work to do here
                    if self.getParam(paramName) == "":
                        namespaces = set()
                        for instance in instances:
                            namespaces.add(instance["metadata"]["namespace"])

                        if len(namespaces) == 1:
                            # If db2u is only in one namespace, we will update that
                            h.stop_and_persist(symbol=self.successIcon, text=f"{len(instances)} {kind}s ({apiVersion}) in namespace '{list(namespaces)[0]}' will be updated")
                            logger.debug(f"There is only one namespace containing {kind}s so we will target that one: {namespaces}")
                            self.setParam(paramName, list(namespaces)[0])
                        elif self.noConfirm:
                            # If db2u is in multiple namespaces and user has disabled prompts then we must error
                            h.stop_and_persist(symbol=self.failureIcon, text=f"{len(instances)} {kind}s ({apiVersion}) were found in multiple namespaces")
                            logger.warning(f"There are multiple namespaces containing {kind}s and user has enable --no-confirm without setting --{mode}-namespace: {namespaces.keys()}")
                            self.fatalError(f"{kind}s are installed in multiple namespaces.  You must instruct which one to update using the '--{mode}-namespace' argument")
                        else:
                            # Otherwise, provide user the list of namespaces we found and ask them to pick on
                            h.stop_and_persist(symbol=self.successIcon, text=f"{len(instances)} {kind}s ({apiVersion}) found in multiple namespaces")
                            logger.debug(f"There are multiple namespaces containing {kind}s, user must choose: {namespaces}")
                            self.printDescription([
                                f"{kind}s were found in multiple namespaces, select the namespace to target from the list below:"
                            ])
                            for index, ns in enumerate(sorted(namespaces), start=1):
                                self.printDescription([f"{index}. {ns}"])
                            self.promptForListSelect("Select namespace", sorted(namespaces), paramName)
                else:
                    logger.debug(f"Found no instances of {kind} to update")
                    h.stop_and_persist(symbol=self.successIcon, text=f"Found no {kind} ({apiVersion}) instances to update")
            except (ResourceNotFoundError, NotFoundError) as e:
                logger.debug(f"{kind}.{apiVersion} is not available in the cluster")
                h.stop_and_persist(symbol=self.successIcon, text=f"{kind}.{apiVersion} is not available in the cluster")

            # With Kafka we also have to determine the provider (strimzi or redhat)
            if mode == "kafka" and self.getParam("kafka_namespace") != "" and self.getParam("kafka_provider") == "":
                try:
                    subAPI = self.dynamicClient.resources.get(api_version="operators.coreos.com/v1alpha1", kind="Subscription")
                    subs = subAPI.get().to_dict()["items"]

                    for sub in subs:
                        if sub["spec"]["name"] == "amq-streams":
                            self.setParam("kafka_provider", "redhat")
                        elif sub["spec"]["name"] == "strimzi-kafka-operator":
                            self.setParam("kafka_provider", "strimzi")
                except (ResourceNotFoundError, NotFoundError) as e:
                    pass

                # If the param is still undefined then there is a big problem
                if self.getParam("kafka_provider") == "":
                    self.fatalError("Unable to determine whether the installed Kafka instance is managed by Strimzi or Red Hat AMQ Streams")
