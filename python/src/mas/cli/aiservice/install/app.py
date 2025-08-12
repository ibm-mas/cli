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

import logging
from sys import exit
from os import path, getenv
import re
import calendar

from openshift.dynamic.exceptions import NotFoundError

from prompt_toolkit import prompt, print_formatted_text, HTML
from prompt_toolkit.completion import WordCompleter

from tabulate import tabulate

from halo import Halo

from ...cli import BaseApp
from .argBuilder import aiServiceInstallArgBuilderMixin
from .argParser import aiServiceinstallArgParser
from .summarizer import aiServiceInstallSummarizerMixin
from .params import requiredParams, optionalParams

from ...install.catalogs import supportedCatalogs

# AI Service relies on SLS, which in turn depends on MongoDB.
# SLS will utilize the shared MongoDB resource that would be used by MAS if it were deployed within the same OpenShift cluster.
# AI Service utilizes two distinct databases: DB2 is employed by the AiBroker component.
# By default, AiService will deploy DB2 within the same namespace as MAS (db2u), but it will be configured as a separate DB2 instance.

from ...install.settings.mongodbSettings import MongoDbSettingsMixin
from ...install.settings.db2Settings import Db2SettingsMixin
from ...install.settings.additionalConfigs import AdditionalConfigsMixin

from mas.cli.validators import (
    InstanceIDFormatValidator,
    StorageClassValidator
)

from mas.devops.ocp import createNamespace, getStorageClasses
from mas.devops.mas import (
    getCurrentCatalog,
    getDefaultStorageClasses
)
from mas.devops.sls import findSLSByNamespace
from mas.devops.data import getCatalog
from mas.devops.tekton import (
    installOpenShiftPipelines,
    updateTektonDefinitions,
    prepareAiServicePipelinesNamespace,
    prepareInstallSecrets,
    testCLI,
    launchAiServiceInstallPipeline
)

logger = logging.getLogger(__name__)


def logMethodCall(func):
    def wrapper(self, *args, **kwargs):
        logger.debug(f">>> InstallApp.{func.__name__}")
        result = func(self, *args, **kwargs)
        logger.debug(f"<<< InstallApp.{func.__name__}")
        return result
    return wrapper


class AiServiceInstallApp(BaseApp, aiServiceInstallArgBuilderMixin, aiServiceInstallSummarizerMixin, MongoDbSettingsMixin, Db2SettingsMixin, AdditionalConfigsMixin):
    @logMethodCall
    def processCatalogChoice(self) -> list:
        self.catalogDigest = self.chosenCatalog["catalog_digest"]
        self.catalogMongoDbVersion = self.chosenCatalog["mongo_extras_version_default"]
        applications = {
            "Aibroker": "aiservice_version",
        }

        self.catalogReleases = {}
        self.catalogTable = []

        # Dynamically fetch the channels from the chosen catalog
        # based on mas core
        for channel in self.chosenCatalog["mas_core_version"]:
            # {"9.1-feature": "9.1.x-feature"}
            self.catalogReleases.update({channel.replace('.x', ''): channel})

        # Generate catalogTable
        for application, key in applications.items():
            # Add 9.1-feature channel based off 9.0 to those apps that have not onboarded yet
            tempChosenCatalog = self.chosenCatalog[key].copy()
            self.catalogTable.append({"": application} | {key.replace(".x", ""): value for key, value in sorted(tempChosenCatalog.items(), reverse=True)})

        if self.architecture == "s390x":
            summary = [
                "",
                "<u>Catalog Details</u>",
                f"Catalog Image:         icr.io/cpopen/ibm-maximo-operator-catalog:{self.getParam('mas_catalog_version')}",
                f"Catalog Digest:        {self.catalogDigest}",
                f"MAS Releases:          {', '.join(sorted(self.catalogReleases, reverse=True))}",
                f"MongoDb:               {self.catalogMongoDbVersion}",
            ]
        else:
            summary = [
                "",
                "<u>Catalog Details</u>",
                f"Catalog Image:         icr.io/cpopen/ibm-maximo-operator-catalog:{self.getParam('mas_catalog_version')}",
                f"Catalog Digest:        {self.catalogDigest}",
                f"MAS Releases:          {', '.join(sorted(self.catalogReleases, reverse=True))}",
                f"MongoDb:               {self.catalogMongoDbVersion}",
            ]

        return summary

    @logMethodCall
    def configAibroker(self):
        self.printH1("Configure AI Service Instance")
        self.printDescription([
            "Instance ID restrictions:",
            " - Must be 3-12 characters long",
            " - Must only use lowercase letters, numbers, and hypen (-) symbol",
            " - Must start with a lowercase letter",
            " - Must end with a lowercase letter or a number"
        ])
        self.promptForString("Instance ID", "aiservice_instance_id", validator=InstanceIDFormatValidator())

        if self.slsMode == 2 and not self.getParam("sls_namespace"):
            self.setParam("sls_namespace", f"mas-{self.getParam('aiservice_instance_id')}-sls")

        self.configOperationMode()

    @logMethodCall
    def interactiveMode(self, simplified: bool, advanced: bool) -> None:
        # Interactive mode
        self.interactiveMode = True

        self.storageClassProvider = "custom"
        self.slsLicenseFileLocal = None
        self.showAdvancedOptions = True

        # Catalog
        self.configCatalog()
        if not self.devMode:
            self.validateCatalogSource()
            self.licensePrompt()

        # Storage Classes
        self.configStorageClasses()

        # Licensing (SLS and DRO)
        self.configSLS()
        self.configDRO()
        self.configICRCredentials()

        self.configCertManager()
        self.configAibroker()
        if self.devMode:
            self.configAppChannel("aibroker")

        self.aiServiceSettings()
        self.aiServiceTenantSettings()
        self.aiServiceIntegrations()

        # Dependencies
        self.configMongoDb()
        self.setDB2DefaultSettings()

    @logMethodCall
    def nonInteractiveMode(self) -> None:
        self.interactiveMode = False

        # Set defaults
        # ---------------------------------------------------------------------
        # Unless a config file named "mongodb-system.yaml" is provided via the additional configs mechanism we will be installing a new MongoDb instance
        self.setParam("mongodb_action", "install")

        self.storageClassProvider = "custom"
        self.slsLicenseFileLocal = None

        self.approvals = {
            "approval_aiservice": {"id": "aiservice"},
        }

        self.setDB2DefaultSettings()

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

            elif key == "install_minio_aiservice":
                incompatibleWithMinioInstall = [
                    "aiservice_storage_provider",
                    "aiservice_storage_accesskey",
                    "aiservice_storage_secretkey",
                    "aiservice_storage_host",
                    "aiservice_storage_port",
                    "aiservice_storage_ssl",
                    "aiservice_s3_endpoint_url",
                    "aiservice_storage_region",
                    "aiservice_tenant_s3_access_key",
                    "aiservice_tenant_s3_secret_key",
                    "aiservice_tenant_s3_endpoint_url",
                    "aiservice_tenant_s3_region"
                ]
                if value is None:
                    for uKey in incompatibleWithMinioInstall:
                        if vars(self.args)[uKey] is None:
                            self.fatalError(f"Parameter is required when --install-minio is not set: {uKey}")
                elif value is not None and value == "true":
                    # If user is installing Minio in-cluster then we know how to connect to it already
                    for uKey in incompatibleWithMinioInstall:
                        if vars(self.args)[uKey] is not None:
                            self.fatalError(f"Unsupported parameter for --install-minio: {uKey}")
                    for rKey in ["minio_root_user", "minio_root_password"]:
                        if vars(self.args)[rKey] is None:
                            self.fatalError(f"Missing required parameter for --install-minio: {rKey}")

                    self.setParam("aiservice_storage_provider", "minio")

                    self.setParam("aiservice_storage_accesskey", self.args.minio_root_user)
                    self.setParam("aiservice_storage_secretkey", self.args.minio_root_password)

                    # TODO: Duplication -- we already have the URL, why do we need all the individual parts,
                    # especially when we don't need them for the tenant?
                    self.setParam("aiservice_storage_host", "minio-service.minio.svc.cluster.local")
                    self.setParam("aiservice_storage_port", "9000")
                    self.setParam("aiservice_storage_ssl", "false")
                    self.setParam("aiservice_s3_endpoint_url", "http://minio-service.minio.svc.cluster.local:9000")
                    self.setParam("aiservice_storage_region", "none")

                    self.setParam("aiservice_tenant_s3_access_key", self.args.minio_root_user)
                    self.setParam("aiservice_tenant_s3_secret_key", self.args.minio_root_password)
                    self.setParam("aiservice_tenant_s3_endpoint_url", "http://minio-service.minio.svc.cluster.local:9000")
                    self.setParam("aiservice_tenant_s3_region", "none")
                else:
                    self.fatalError(f"Unsupported value for --install-minio: {value}")

            elif key == "non_prod":
                if not value:
                    self.operationalMode = 1
                    self.setParam("environment_type", "production")
                else:
                    self.operationalMode = 2
                    self.setParam("mas_annotations", "mas.ibm.com/operationalMode=nonproduction")
                    self.setParam("environment_type", "non-production")

            elif key == "additional_configs":
                self.localConfigDir = value
                # If there is a file named mongodb-system.yaml we will use this as a BYO MongoDB datasource
                if self.localConfigDir is not None and path.exists(path.join(self.localConfigDir, "mongodb-system.yaml")):
                    self.setParam("mongodb_action", "byo")
                    self.setParam("sls_mongodb_cfg_file", "/workspace/additional-configs/mongodb-system.yaml")

            elif key == "pod_templates":
                # For the named configurations we will convert into the path
                if value in ["best-effort", "guaranteed"]:
                    self.setParam("mas_pod_templates_dir", path.join(self.templatesDir, "pod-templates", value))
                else:
                    self.setParam("mas_pod_templates_dir", value)

            # We check for both None and "" values for the application channel parameters
            # value = None means the parameter wasn't set at all
            # value = "" means the parameter was explicitly set to "don't install this application"
            elif key == "aiservice_channel":
                if value is not None and value != "":
                    self.setParam("aiservice_channel", value)

            # MongoDB
            elif key == "mongodb_namespace":
                if value is not None and value != "":
                    self.setParam(key, value)
                    self.setParam("sls_mongodb_cfg_file", f"/workspace/configs/mongo-{value}.yml")

            # SLS
            elif key == "license_file":
                if value is not None and value != "":
                    self.slsLicenseFileLocal = value
                    self.setParam("sls_action", "install")
            elif key == "dedicated_sls":
                if value:
                    self.setParam("sls_namespace", f"mas-{self.args.aiservice_instance_id}-sls")

            # These settings are used by the CLI rather than passed to the PipelineRun
            elif key == "storage_accessmode":
                if value is None:
                    self.fatalError(f"{key} must be set")
                self.pipelineStorageAccessMode = value
            elif key == "storage_pipeline":
                if value is None:
                    self.fatalError(f"{key} must be set")
                self.pipelineStorageClass = value

            elif key.startswith("approval_"):
                if key not in self.approvals:
                    raise KeyError(f"{key} is not a supported approval workflow ID: {self.approvals.keys()}")

                if value != "":
                    valueParts = value.split(":")
                    if len(valueParts) != 3:
                        self.fatalError(f"Unsupported format for {key} ({value}).  Expected MAX_RETRIES:RETRY_DELAY:IGNORE_FAILURE")
                    else:
                        try:
                            self.approvals[key]["maxRetries"] = int(valueParts[0])
                            self.approvals[key]["retryDelay"] = int(valueParts[1])
                            self.approvals[key]["ignoreFailure"] = bool(valueParts[2])
                        except ValueError:
                            self.fatalError(f"Unsupported format for {key} ({value}).  Expected int:int:boolean")

            # Arguments that we don't need to do anything with
            elif key in ["accept_license", "dev_mode", "skip_pre_check", "skip_grafana_install", "no_confirm", "no_wait_for_pvc", "help", "advanced", "simplified"]:
                pass

            elif key == "manual_certificates":
                if value is not None:
                    self.setParam("mas_manual_cert_mgmt", True)
                    self.manualCertsDir = value
                else:
                    self.setParam("mas_manual_cert_mgmt", False)
                    self.manualCertsDir = None

            elif key == "enable_ipv6":
                self.setParam("enable_ipv6", True)

            # Fail if there's any arguments we don't know how to handle
            else:
                print(f"Unknown option: {key} {value}")
                self.fatalError(f"Unknown option: {key} {value}")

        # Load the catalog information
        self.chosenCatalog = getCatalog(self.getParam("mas_catalog_version"))

        # License file is only optional for existing SLS instance
        if self.slsLicenseFileLocal is None:
            self.fatalError("--license-file must be set for new SLS install")

        # Once we've processed the inputs, we should validate the catalog source & prompt to accept the license terms
        if not self.devMode:
            self.validateCatalogSource()
            self.licensePrompt()

    @logMethodCall
    def install(self, argv):
        """
        Install Aiservice
        """
        args = aiServiceinstallArgParser.parse_args(args=argv)

        # We use the presence of --mas-instance-id to determine whether
        # the CLI is being started in interactive mode or not
        instanceId = args.aiservice_instance_id

        # Properties for arguments that control the behavior of the CLI
        self.noConfirm = args.no_confirm
        self.waitForPVC = not args.no_wait_for_pvc
        self.licenseAccepted = args.accept_license
        self.devMode = args.dev_mode

        self.printDescription([
            "<B><U>AI Broker 9.0 Deprecation Notice</U></B>",
            "",
            "Maximo AI Broker (introduced with MAS 9.0) has been replaced with Maximo AI Service as of Aug 1 2025",
            "To continue using the features that were enabled by the AI broker after that time, you must deploy and use Maximo AI Service 9.1:",
            " - Maximo AI Service 9.1 is compatible with both Maximo Application Suite 9.0 and 9.1 releases",
            " - If Maximo AI Service is deployed with Maximo Application Suite 9.0, you can use only the AI features that were included in Maximo Application Suite 9.0",
            "",
            "Note: Maximo AI Service 9.1 includes a limited-use license to watsonx.ai and incurs an additional AppPoint cost"
        ])

        if not self.devMode:
            self.printDescription([
                "",
                "<ForestGreen>Coming Soon!  We are busy putting the finishing touches on Maximo AI Service 9.1 ahead of a re-launch planned for the 28 August 2025 catalog update</ForestGreen>",
                ""
            ])
            exit(1)

        # Set image_pull_policy of the CLI in interactive mode
        if args.image_pull_policy and args.image_pull_policy != "":
            self.setParam("image_pull_policy", args.image_pull_policy)

        self.approvals = {}

        # Store all args
        self.args = args

        # These flags work for setting params in both interactive and non-interactive modes
        if args.skip_pre_check:
            self.setParam("skip_pre_check", "true")

        if instanceId is None:
            self.printH1("Set Target OpenShift Cluster")
            # Connect to the target cluster
            self.connect()
        else:
            logger.debug("Aiservice instance ID is set, so we assume already connected to the desired OCP")
            self.lookupTargetArchitecture()

        if self.dynamicClient is None:
            print_formatted_text(HTML("<Red>Error: The Kubernetes dynamic Client is not available.  See log file for details</Red>"))
            exit(1)

        # Perform a check whether the cluster is set up for airgap install, this will trigger an early failure if the cluster is using the now
        # deprecated MaximoApplicationSuite ImageContentSourcePolicy instead of the new ImageDigestMirrorSet
        self.isAirgap()

        # Configure the installOptions for the appropriate architecture
        self.catalogOptions = supportedCatalogs[self.architecture]

        # Basic settings before the user provides any input
        self.configICR()
        self.deployCP4D = False

        # UDS install has not been supported since the January 2024 catalog update
        self.setParam("uds_action", "install-dro")

        # Install Db2 for AI Service
        self.setParam("db2_action_aiservice", "install")

        # User must either provide the configuration via numerous command line arguments, or the interactive prompts
        if instanceId is None:
            self.interactiveMode(simplified=args.simplified, advanced=args.advanced)
        else:
            self.nonInteractiveMode()

        # Set up the sls license file
        self.slsLicenseFile()

        # Show a summary of the installation configuration
        self.printH1("Non-Interactive Install Command")
        self.printDescription([
            "Save and re-use the following script to re-run this install without needing to answer the interactive prompts again",
            "",
            self.buildCommand()
        ])

        self.displayInstallSummary()

        if not self.noConfirm:
            print()
            self.printDescription([
                "Please carefully review your choices above, correcting mistakes now is much easier than after the install has begun"
            ])
            continueWithInstall = self.yesOrNo("Proceed with these settings")

        # Prepare the namespace and launch the installation pipeline
        if self.noConfirm or continueWithInstall:
            self.createTektonFileWithDigest()

            self.printH1("Launch Install")
            pipelinesNamespace = f"aiservice-{self.getParam('aiservice_instance_id')}-pipelines"

            if not self.noConfirm:
                self.printDescription(["If you are using storage classes that utilize 'WaitForFirstConsumer' binding mode choose 'No' at the prompt below"])
                wait = self.yesOrNo("Wait for PVCs to bind")
            else:
                wait = False

            with Halo(text='Validating OpenShift Pipelines installation', spinner=self.spinner) as h:
                installOpenShiftPipelines(self.dynamicClient)
                h.stop_and_persist(symbol=self.successIcon, text="OpenShift Pipelines Operator is installed and ready to use")

            with Halo(text=f'Preparing namespace ({pipelinesNamespace})', spinner=self.spinner) as h:
                createNamespace(self.dynamicClient, pipelinesNamespace)
                prepareAiServicePipelinesNamespace(
                    dynClient=self.dynamicClient,
                    instanceId=self.getParam("aiservice_instance_id"),
                    storageClass=self.pipelineStorageClass,
                    accessMode=self.pipelineStorageAccessMode,
                    waitForBind=wait,
                    configureRBAC=(self.getParam("service_account_name") == "")
                )
                prepareInstallSecrets(
                    dynClient=self.dynamicClient,
                    namespace=pipelinesNamespace,
                    slsLicenseFile=self.slsLicenseFileSecret,
                    additionalConfigs=self.additionalConfigsSecret,
                    podTemplates=self.podTemplatesSecret,
                    certs=self.certsSecret
                )

                self.setupApprovals(pipelinesNamespace)

                h.stop_and_persist(symbol=self.successIcon, text=f"Namespace is ready ({pipelinesNamespace})")

            with Halo(text='Testing availability of MAS CLI image in cluster', spinner=self.spinner) as h:
                testCLI()
                h.stop_and_persist(symbol=self.successIcon, text="MAS CLI image deployment test completed")

            with Halo(text=f'Installing latest Tekton definitions (v{self.version})', spinner=self.spinner) as h:
                updateTektonDefinitions(pipelinesNamespace, self.tektonDefsPath)
                h.stop_and_persist(symbol=self.successIcon, text=f"Latest Tekton definitions are installed (v{self.version})")

            with Halo(text=f"Submitting PipelineRun for {self.getParam('aiservice_instance_id')} install", spinner=self.spinner) as h:
                pipelineURL = launchAiServiceInstallPipeline(dynClient=self.dynamicClient, params=self.params)
                if pipelineURL is not None:
                    h.stop_and_persist(symbol=self.successIcon, text=f"PipelineRun for {self.getParam('aiservice_instance_id')} install submitted")
                    print_formatted_text(HTML(f"\nView progress:\n  <Cyan><u>{pipelineURL}</u></Cyan>\n"))
                else:
                    h.stop_and_persist(symbol=self.failureIcon, text=f"Failed to submit PipelineRun for {self.getParam('aiservice_instance_id')} install, see log file for details")
                    print()

    @logMethodCall
    def setupApprovals(self, namespace: str) -> None:
        """
        Ensure the supported approval configmaps are in the expected state for the start of the run:
         - not present (if approval is not required)
         - present with the chosen state field initialized to ""
        """
        for approval in self.approvals.values():
            if "maxRetries" in approval:
                # Enable this approval workload
                logger.debug(f"Approval workflow for {approval['id']} will be enabled during install ({approval['maxRetries']} / {approval['retryDelay']}s / {approval['ignoreFailure']})")
                self.initializeApprovalConfigMap(namespace, approval['id'], True, approval['maxRetries'], approval['retryDelay'], approval['ignoreFailure'])

    def aiServiceSettings(self) -> None:
        self.printH1("AI Service Settings")

        # Ask about MinIO installation FIRST (moved from aiServiceDependencies)
        self.printH2("Storage Configuration")
        self.printDescription(["AI Service requires object storage for pipelines, tenants, and templates. You can either install MinIO in-cluster or connect to external storage."])

        if self.yesOrNo("Install Minio"):
            # Only ask for MinIO credentials
            self.promptForString("minio root username", "minio_root_user")
            self.promptForString("minio root password", "minio_root_password", isPassword=True)

            # Auto-set MinIO storage defaults (same as non-interactive mode)
            self._setMinioStorageDefaults()
        else:
            # Ask for external storage configuration
            self.printDescription(["Configure your external object storage (S3-compatible) connection details:"])
            s3Completer = WordCompleter(["aws", "minio"])
            s3Provider = self.promptForString("Storage provider", completer=s3Completer)
            self.setParam("aiservice_storage_provider", s3Provider)
            self.promptForString("Storage access key", "aiservice_storage_accesskey")
            self.promptForString("Storage secret key", "aiservice_storage_secretkey", isPassword=True)
            self.promptForString("Storage host", "aiservice_storage_host")
            self.promptForString("Storage port", "aiservice_storage_port")
            self.promptForString("Storage ssl", "aiservice_storage_ssl")
            self.promptForString("Storage region", "aiservice_storage_region")
            self.promptForString("Storage pipelines bucket", "aiservice_storage_pipelines_bucket")
            self.promptForString("Storage tenants bucket", "aiservice_storage_tenants_bucket")
            self.promptForString("Storage templates bucket", "aiservice_storage_templates_bucket")

        # S3 parameters are now auto-derived from storage configuration
        self._deriveS3ParametersFromStorage()

    def aiServiceTenantSettings(self) -> None:
        self.printH1("AI Service Tenant Settings")
        self.promptForString("Tenant entitlement type", "tenant_entitlement_type")
        self.promptForString("Tenant start date", "tenant_entitlement_start_date")
        self.promptForString("Tenant end date", "tenant_entitlement_end_date")

    def _deriveS3ParametersFromStorage(self) -> None:
        """
        Auto-derive S3 and tenant S3 parameters from the aiservice_storage_* parameters.
        This reuses the values provided for kmodel object storage to avoid redundant prompts.
        """
        storage_provider = self.getParam("aiservice_storage_provider")
        storage_host = self.getParam("aiservice_storage_host")
        storage_port = self.getParam("aiservice_storage_port")
        storage_ssl = self.getParam("aiservice_storage_ssl")
        storage_region = self.getParam("aiservice_storage_region")
        storage_accesskey = self.getParam("aiservice_storage_accesskey")
        storage_secretkey = self.getParam("aiservice_storage_secretkey")

        # Build endpoint URL from storage configuration
        protocol = "https" if storage_ssl == "true" else "http"

        if storage_provider == "minio":
            endpoint_url = f"{protocol}://{storage_host}:{storage_port}"
        elif storage_provider == "s3":
            # For AWS S3, construct proper endpoint
            if storage_region and storage_region != "none":
                endpoint_url = f"{protocol}://s3.{storage_region}.amazonaws.com"
            else:
                endpoint_url = f"{protocol}://s3.amazonaws.com"
        else:
            # For other providers, construct basic endpoint
            endpoint_url = f"{protocol}://{storage_host}:{storage_port}" if storage_port else f"{protocol}://{storage_host}"

        # Set S3 parameters (reusing storage configuration)
        self.setParam("aiservice_s3_bucket_prefix", "aiservice")  # Default prefix
        if endpoint_url:
            self.setParam("aiservice_s3_endpoint_url", endpoint_url)
        self.setParam("aiservice_s3_region", storage_region if storage_region else "none")

        # Set tenant S3 parameters (reusing same storage configuration)
        self.setParam("aiservice_tenant_s3_bucket_prefix", "tenant")  # Default tenant prefix
        self.setParam("aiservice_tenant_s3_access_key", storage_accesskey)
        self.setParam("aiservice_tenant_s3_secret_key", storage_secretkey)
        if endpoint_url:
            self.setParam("aiservice_tenant_s3_endpoint_url", endpoint_url)
        self.setParam("aiservice_tenant_s3_region", storage_region if storage_region else "none")

    def _setMinioStorageDefaults(self) -> None:
        """
        Set MinIO storage defaults when MinIO is being installed in-cluster.
        This mirrors the logic from non-interactive mode.
        """
        self.setParam("aiservice_storage_provider", "minio")
        self.setParam("aiservice_storage_accesskey", self.getParam("minio_root_user"))
        self.setParam("aiservice_storage_secretkey", self.getParam("minio_root_password"))
        self.setParam("aiservice_storage_host", "minio-service.minio.svc.cluster.local")
        self.setParam("aiservice_storage_port", "9000")
        self.setParam("aiservice_storage_ssl", "false")
        self.setParam("aiservice_storage_region", "none")

        # Set default bucket names
        self.setParam("aiservice_storage_pipelines_bucket", "km-pipelines")
        self.setParam("aiservice_storage_tenants_bucket", "km-tenants")
        self.setParam("aiservice_storage_templates_bucket", "km-templates")

    def aiServiceIntegrations(self) -> None:
        self.printH1("WatsonX Integration")
        self.printDescription([
            "This CLI section configures the integration between the AI Service and IBM watsonx.ai. AI Service",
            "uses watsonx for model deployment and inferencing.",
            "",
            "The WatsonX API key must be a **platform API key** associated with a user that has at least:",
            "- **Editor permission** for the project",
            "- **Viewer permission** for the space",
            "You can generate this key by following IBM's documentation: https://www.ibm.com/docs/en/watsonx/w-and-w/2.2.0?topic=tutorials-generating-api-keys#api-keys__platform__title__1",
            "",
            "The endpoint URL is your WatsonX Machine Learning service URL. It can be found in the watsonx.ai",
            "documentation: https://cloud.ibm.com/apidocs/watsonx-ai-cp/watsonx-ai-cp-2.2.0#endpoint-url",
            "",
            "The project ID refers to your specific watsonx.ai project where your ML models and assets are stored.",
            "",
        ])
        self.promptForString("Watsonxai api key", "aiservice_watsonxai_apikey", isPassword=True)
        self.promptForString("Watsonxai machine learning url", "aiservice_watsonxai_url")
        self.promptForString("Watsonxai project id", "aiservice_watsonxai_project_id")

        self.printH1("RSL Integration")
        self.printDescription([
            "RSL (Reliable Strategy Library) connects to strategic asset management via STRATEGIZEAPI.",
            "",
            "RSL URL: https://api.rsl-service.suite.maximo.com (standard for all customers)",
            "Org ID: Get from MAS Manage > System Properties > 'mxe.rs.rslorgid'",
            "Token: Use your IBM entitlement key (same as MAS installation)",
            "",
            "Note: Future versions will auto-configure these from MAS Manage.",
            ""
        ])
        self.promptForString("RSL url", "rsl_url")
        self.promptForString("ORG Id of RSL", "rsl_org_id")
        self.promptForString("Token for RSL", "rsl_token", isPassword=True)

    # These are all candidates to centralise in a new mixin used by both install and aiservice-install

    @logMethodCall
    def configICR(self):
        if self.devMode:
            self.setParam("mas_icr_cp", getenv("MAS_ICR_CP", "docker-na-public.artifactory.swg-devops.com/wiotp-docker-local"))
            self.setParam("mas_icr_cpopen", getenv("MAS_ICR_CPOPEN", "docker-na-public.artifactory.swg-devops.com/wiotp-docker-local/cpopen"))
            self.setParam("sls_icr_cpopen", getenv("SLS_ICR_CPOPEN", "docker-na-public.artifactory.swg-devops.com/wiotp-docker-local/cpopen"))
        else:
            self.setParam("mas_icr_cp", getenv("MAS_ICR_CP", "cp.icr.io/cp"))
            self.setParam("mas_icr_cpopen", getenv("MAS_ICR_CPOPEN", "icr.io/cpopen"))
            self.setParam("sls_icr_cpopen", getenv("SLS_ICR_CPOPEN", "icr.io/cpopen"))

    @logMethodCall
    def configICRCredentials(self):
        self.printH1("Configure IBM Container Registry")
        self.promptForString("IBM entitlement key", "ibm_entitlement_key", isPassword=True)
        if self.devMode:
            self.promptForString("Artifactory username", "artifactory_username")
            self.promptForString("Artifactory token", "artifactory_token", isPassword=True)

    @logMethodCall
    def configCertManager(self):
        # Only install of Red Hat Cert-Manager has been supported since the January 2025 catalog update
        self.setParam("cert_manager_provider", "redhat")
        self.setParam("cert_manager_action", "install")

    def formatCatalog(self, name: str) -> str:
        # Convert "v9-241107-amd64" into "November 2024 Update (v9-241107-amd64)"
        date = name.split("-")[1]
        month = int(date[2:4])
        monthName = calendar.month_name[month]
        year = date[:2]
        return f" - {monthName} 20{year} Update\n   <Orange><u>https://ibm-mas.github.io/cli/catalogs/{name}</u></Orange>"

    @logMethodCall
    def configCatalog(self):
        self.printH1("IBM Maximo Operator Catalog Selection")
        if self.devMode:
            self.promptForString("Select catalog source", "mas_catalog_version", default="v9-master-amd64")
        else:
            catalogInfo = getCurrentCatalog(self.dynamicClient)

            if catalogInfo is None:
                self.printDescription([
                    "The catalog you choose dictates the version of everything that is installed, with Maximo Application Suite this is the only version you need to remember; all other versions are determined by this choice.",
                    "Older catalogs can still be used, but we recommend using an older version of the CLI that aligns with the release date of the catalog.",
                    " - Learn more: <Orange><u>https://ibm-mas.github.io/cli/catalogs/</u></Orange>",
                    ""
                ])
                print("Supported Catalogs:")
                for catalog in self.catalogOptions:
                    catalogString = self.formatCatalog(catalog)
                    print_formatted_text(HTML(f"{catalogString}"))
                print()

                catalogCompleter = WordCompleter(self.catalogOptions)
                catalogSelection = self.promptForString("Select catalog", completer=catalogCompleter)
                self.setParam("mas_catalog_version", catalogSelection)
            else:
                self.printDescription([
                    f"The IBM Maximo Operator Catalog is already installed in this cluster ({catalogInfo['catalogId']}).  If you wish to install MAS using a newer version of the catalog please first update the catalog using mas update."
                ])
                self.setParam("mas_catalog_version", catalogInfo["catalogId"])

            self.chosenCatalog = getCatalog(self.getParam("mas_catalog_version"))
            catalogSummary = self.processCatalogChoice()
            self.printDescription(catalogSummary)
            self.printDescription([
                "",
                "Two types of release are available:",
                " - GA releases of Maximo Application Suite are supported under IBM's standard 3+1+3 support lifecycle policy.",
                " - 'Feature' releases allow early access to new features for evaluation in non-production environments and are only supported through to the next GA release.",
                ""
            ])

            print(tabulate(self.catalogTable, headers="keys", tablefmt="simple_grid"))

            releaseCompleter = WordCompleter(sorted(self.catalogReleases, reverse=True))
            releaseSelection = self.promptForString("Select release", completer=releaseCompleter)

            self.setParam("aiservice_channel", self.catalogReleases[releaseSelection])

    @logMethodCall
    def validateCatalogSource(self):
        catalogsAPI = self.dynamicClient.resources.get(api_version="operators.coreos.com/v1alpha1", kind="CatalogSource")
        try:
            catalog = catalogsAPI.get(name="ibm-operator-catalog", namespace="openshift-marketplace")
            catalogDisplayName = catalog.spec.displayName

            m = re.match(r".+(?P<catalogId>v[89]-(?P<catalogVersion>[0-9]+)-amd64)", catalogDisplayName)
            if m:
                # catalogId = v8-yymmdd-amd64
                # catalogVersion = yymmdd
                catalogId = m.group("catalogId")
            elif re.match(r".+v8-amd64", catalogDisplayName):
                catalogId = "v8-amd64"
            else:
                self.fatalError(f"IBM Maximo Operator Catalog is already installed on this cluster. However, it is not possible to identify its version. If you wish to install a new MAS instance using the {self.getParam('mas_catalog_version')} catalog please first run 'mas update' to switch to this catalog, this will ensure the appropriate actions are performed as part of the catalog update")

            if catalogId != self.getParam("mas_catalog_version"):
                self.fatalError(f"IBM Maximo Operator Catalog {catalogId} is already installed on this cluster, if you wish to install a new MAS instance using the {self.getParam('mas_catalog_version')} catalog please first run 'mas update' to switch to this catalog, this will ensure the appropriate actions are performed as part of the catalog update")
        except NotFoundError:
            # There's no existing catalog installed
            pass

    # TODO: update licenses for aiservice 9.1.x
    @logMethodCall
    def licensePrompt(self):
        if not self.licenseAccepted:
            self.printH1("License Terms")
            self.printDescription([
                "To continue with the installation, you must accept the license terms:",
                self.licenses[f"aibroker-{self.getParam('aiservice_channel')}"]
            ])

            if self.noConfirm:
                self.fatalError("You must accept the license terms with --accept-license when using the --no-confirm flag")
            else:
                if not self.yesOrNo("Do you accept the license terms"):
                    exit(1)

    @logMethodCall
    def configStorageClasses(self):
        self.printH1("Configure Storage Class Usage")
        self.printDescription([
            "Maximo Application Suite and it's dependencies require storage classes that support ReadWriteOnce (RWO) and ReadWriteMany (RWX) access modes:",
            "  - ReadWriteOnce volumes can be mounted as read-write by multiple pods on a single node.",
            "  - ReadWriteMany volumes can be mounted as read-write by multiple pods across many nodes.",
            ""
        ])
        defaultStorageClasses = getDefaultStorageClasses(self.dynamicClient)
        if defaultStorageClasses.provider is not None:
            print_formatted_text(HTML(f"<MediumSeaGreen>Storage provider auto-detected: {defaultStorageClasses.providerName}</MediumSeaGreen>"))
            print_formatted_text(HTML(f"<LightSlateGrey>  - Storage class (ReadWriteOnce): {defaultStorageClasses.rwo}</LightSlateGrey>"))
            print_formatted_text(HTML(f"<LightSlateGrey>  - Storage class (ReadWriteMany): {defaultStorageClasses.rwx}</LightSlateGrey>"))
            self.storageClassProvider = defaultStorageClasses.provider
            self.params["storage_class_rwo"] = defaultStorageClasses.rwo
            self.params["storage_class_rwx"] = defaultStorageClasses.rwx

        overrideStorageClasses = False
        if "storage_class_rwx" in self.params and self.params["storage_class_rwx"] != "":
            overrideStorageClasses = not self.yesOrNo("Use the auto-detected storage classes")

        if "storage_class_rwx" not in self.params or self.params["storage_class_rwx"] == "" or overrideStorageClasses:
            self.storageClassProvider = "custom"

            self.printDescription([
                "Select the ReadWriteOnce and ReadWriteMany storage classes to use from the list below:",
                "Enter 'none' for the ReadWriteMany storage class if you do not have a suitable class available in the cluster, however this will limit what can be installed"
            ])
            for storageClass in getStorageClasses(self.dynamicClient):
                print_formatted_text(HTML(f"<LightSlateGrey>  - {storageClass.metadata.name}</LightSlateGrey>"))

            self.params["storage_class_rwo"] = prompt(HTML('<Yellow>ReadWriteOnce (RWO) storage class</Yellow> '), validator=StorageClassValidator(), validate_while_typing=False)
            self.params["storage_class_rwx"] = prompt(HTML('<Yellow>ReadWriteMany (RWX) storage class</Yellow> '), validator=StorageClassValidator(), validate_while_typing=False)

        # Configure storage class for pipeline PVC
        # We prefer to use ReadWriteMany, but we can cope with ReadWriteOnce if necessary
        if self.isSNO() or self.params["storage_class_rwx"] == "none":
            self.pipelineStorageClass = self.getParam("storage_class_rwo")
            self.pipelineStorageAccessMode = "ReadWriteOnce"
        else:
            self.pipelineStorageClass = self.getParam("storage_class_rwx")
            self.pipelineStorageAccessMode = "ReadWriteMany"

    @logMethodCall
    def configSLS(self) -> None:
        self.printH1("Configure AppPoint Licensing")
        self.printDescription(
            [
                "By default the MAS instance will be configured to use a cluster-shared License, this provides a shared pool of AppPoints available to all MAS instances on the cluster.",
                "",
            ]
        )

        self.slsMode = 1
        self.slsLicenseFileLocal = None

        if self.showAdvancedOptions:
            self.printDescription(
                [
                    "Alternatively you may choose to install using a dedicated license only available to this MAS instance.",
                    "  1. Install MAS with Cluster-Shared License (AppPoints)",
                    "  2. Install MAS with Dedicated License (AppPoints)",
                ]
            )
            self.slsMode = self.promptForInt("SLS Mode", default=1)

            if self.slsMode not in [1, 2]:
                self.fatalError(f"Invalid selection: {self.slsMode}")

        if not (self.slsMode == 2 and not self.getParam("sls_namespace")):
            sls_namespace = "ibm-sls" if self.slsMode == 1 else self.getParam("sls_namespace")
            if findSLSByNamespace(sls_namespace, dynClient=self.dynamicClient):
                print_formatted_text(HTML(f"<MediumSeaGreen>SLS auto-detected: {sls_namespace}</MediumSeaGreen>"))
                print()
                if not self.yesOrNo("Upload/Replace the license file"):
                    self.setParam("sls_action", "gencfg")
                    return

        self.slsLicenseFileLocal = self.promptForFile("License file", mustExist=True, envVar="SLS_LICENSE_FILE_LOCAL")
        self.setParam("sls_action", "install")

    @logMethodCall
    def configDRO(self) -> None:
        self.promptForString("Contact e-mail address", "uds_contact_email")
        self.promptForString("Contact first name", "uds_contact_firstname")
        self.promptForString("Contact last name", "uds_contact_lastname")

        if self.showAdvancedOptions:
            self.promptForString("IBM Data Reporter Operator (DRO) Namespace", "dro_namespace", default="redhat-marketplace")

    @logMethodCall
    def configAppChannel(self, appId):
        self.params["aiservice_channel"] = prompt(HTML('<Yellow>Custom channel for AI Service</Yellow> '))

    @logMethodCall
    def configOperationMode(self):
        self.printH1("Configure Operational Mode")
        self.printDescription([
            "Maximo Application Suite can be installed in a non-production mode for internal development and testing, this setting cannot be changed after installation:",
            " - All applications, add-ons, and solutions have 0 (zero) installation AppPoints in non-production installations.",
            " - These specifications are also visible in the metrics that are shared with IBM and in the product UI.",
            "",
            "  1. Production",
            "  2. Non-Production"
        ])
        self.operationalMode = self.promptForInt("Operational Mode", default=1)
        if self.operationalMode == 1:
            self.setParam("environment_type", "production")
        else:
            self.setParam("environment_type", "non-production")
