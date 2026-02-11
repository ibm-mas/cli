#!/usr/bin/env python
# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

import logging
from os import path
from base64 import b64encode
from glob import glob
from halo import Halo
from prompt_toolkit import print_formatted_text, HTML

from ..cli import BaseApp
from ..validators import InstanceIDFormatValidator, FileExistsValidator
from .argParser import restoreArgParser
from mas.devops.ocp import createNamespace, getConsoleURL
from mas.devops.mas import getDefaultStorageClasses
from mas.devops.tekton import preparePipelinesNamespace, installOpenShiftPipelines, updateTektonDefinitions, launchRestorePipeline, prepareRestoreSecrets

logger = logging.getLogger(__name__)


class RestoreApp(BaseApp):

    def restore(self, argv):
        """
        Restore MAS instance
        """
        self.args = restoreArgParser.parse_args(args=argv)
        self.noConfirm = self.args.no_confirm
        self.devMode = self.args.dev_mode
        self.interactive_mode = True

        if self.args.skip_pre_check:
            self.setParam("skip_pre_check", "true")

        if self.args.mas_instance_id:
            # Non-interactive mode
            self.interactive_mode = False
            logger.debug("MAS Instance ID is set, so we assume already connected to the desired OCP")
            requiredParams = ["mas_instance_id", "restore_version"]
            optionalParams = [
                "mas_domain_on_restore",
                "include_slscfg_from_backup",
                "include_drocfg_from_backup",
                "sls_url_on_restore",
                "sls_cfg_file",
                "dro_url_on_restore",
                "dro_cfg_file",
                "backup_storage_size",
                "clean_backup",
                "include_sls",
                "include_grafana",
                "include_dro",
                "skip_pre_check",
                "dev_mode",
                # SLS
                "sls_domain",
                # DRO Configuration
                "dro_namespace",
                "dro_contact_email",
                "dro_contact_firstname",
                "dro_contact_lastname",
                "dro_contact_company_name",
                "ibm_entitlement_key",
                # Dev Mode
                "artifactory_username",
                "artifactory_token",
                # Download Configuration
                "download_backup",
                "backup_archive_name",
                "aws_access_key_id",
                "aws_secret_access_key",
                "s3_bucket_name",
                "s3_region",
                "artifactory_url",
                "artifactory_repository",
                # Manage App Restore
                "restore_manage_app",
                "restore_manage_db",
                "manage_db_override_storageclass",
                "manage_db_meta_storage_class",
                "manage_db_data_storage_class",
                "manage_db_backup_storage_class",
                "manage_db_logs_storage_class",
                "manage_db_temp_storage_class"
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
                elif key in ["no_confirm", "help", "download_destination"]:
                    pass

                # Fail if there's any arguments we don't know how to handle
                else:
                    print(f"Unknown option: {key} {value}")
                    self.fatalError(f"Unknown option: {key} {value}")
        else:
            # Interactive mode
            self.interactive_mode = True
            self.printH1("Set Target OpenShift Cluster")
            # Connect to the target cluster
            self.connect()

        if self.dynamicClient is None:
            self.fatalError("The Kubernetes dynamic Client is not available.  See log file for details")

        # Perform a check whether the cluster is set up for airgap install
        self.isAirgap()

        # If instance ID not provided, prompt for it
        if self.interactive_mode:

            if self.args.mas_instance_id is None:
                self.promptForInstanceId()

            # Prompt for backup version if not provided
            if self.args.restore_version is None:
                self.promptForBackupVersion()

            # Prompt for Grafana install
            self.promptForIncludeGrafana()

            # Prompt for SLS install
            self.promptForIncludeSLS()

            # Prompt for DRO install
            self.promptForIncludeDRO()

            if self.args.mas_domain_on_restore is None:
                self.promptForMASConfiguration()

            if self.args.include_slscfg_from_backup is None:
                self.promptForSLSConfiguration()

            if self.args.include_drocfg_from_backup is None:
                self.promptForDROConfiguration()

            # Prompt for Manage app restore
            self.promptForManageAppRestore()

            # Prompt for backup storage size if not provided
            if self.args.backup_storage_size is None:
                self.promptForBackupStorageSize()

            self.promptForDownloadConfiguration()

        # Set default values for optional parameters if not provided
        self.setDefaultParams()

        print()

        self.printH1("Review Settings")
        self.printDescription([
            "Connected to:",
            f" - <u>{getConsoleURL(self.dynamicClient)}</u>"
        ])

        self.printH2("MAS Instance Configuration")
        self.printSummary("Instance ID", self.getParam("mas_instance_id"))
        if self.getParam("mas_domain_on_restore") is not None and self.getParam("mas_domain_on_restore") != "":
            self.printSummary("Suite Domain", self.getParam("mas_domain_on_restore"))
        if self.getParam("sls_url_on_restore") is not None and self.getParam("sls_url_on_restore") != "":
            self.printSummary("SLS URL", self.getParam("sls_url_on_restore"))
        if self.getParam("sls_cfg_file") is not None and self.getParam("sls_cfg_file") != "":
            self.printSummary("Custom SLS Config File", self.getParam("sls_cfg_file"))
        if self.getParam("dro_url_on_restore") is not None and self.getParam("dro_url_on_restore") != "":
            self.printSummary("DRO URL", self.getParam("dro_url_on_restore"))
        if self.getParam("dro_cfg_file") is not None and self.getParam("dro_cfg_file") != "":
            self.printSummary("Custom DRO Config File", self.getParam("dro_cfg_file"))

        self.printH2("Restore Configuration")
        self.printSummary("Backup Directory", "/workspace/backups (hardcoded)")
        self.printSummary("Config Directory", "/workspace/configs (hardcoded)")
        self.printSummary("Backup Storage Size", self.getParam("backup_storage_size"))
        self.printSummary("Backup Version to restore", self.getParam("restore_version"))
        if self.getParam("backup_archive_name") is not None and self.getParam("backup_archive_name") != "":
            self.printSummary("Backup custom archive name", self.getParam("backup_archive_name"))

        self.printH2("Components")
        self.printSummary("Include Grafana", self.getParam("include_grafana") if self.getParam("include_grafana") else "true")
        self.printSummary("Include SLS", self.getParam("include_sls") if self.getParam("include_sls") else "true")
        self.printSummary("Include DRO", self.getParam("include_dro") if self.getParam("include_dro") else "true")

        if self.getParam("restore_manage_app") == "true":
            self.printH2("Manage Application Restore")
            self.printSummary("Restore Manage App", "Yes")
            self.printSummary("Restore Manage incluster Db2 Database", "Yes" if self.getParam("restore_manage_db") == "true" else "No")

        if self.getParam("sls_domain") is not None and self.getParam("sls_domain") != "":
            self.printH2("SLS Configuration")
            self.printSummary("SLS Domain", self.getParam("dro_namespace"))

        if self.getParam("include_dro") is not None and self.getParam("include_dro") == "true":
            self.printH2("DRO Configuration")
            self.printSummary("DRO Namespace", self.getParam("dro_namespace"))
            self.printSummary("Contact Email", self.getParam("dro_contact_email"))
            self.printSummary("Contact First Name", self.getParam("dro_contact_firstname"))
            self.printSummary("Contact Last Name", self.getParam("dro_contact_lastname"))

        continueWithRestore = True
        if not self.noConfirm:
            print()
            self.printDescription([
                "Please carefully review your choices above, correcting mistakes now is much easier than after the restore has begun"
            ])
            continueWithRestore = self.yesOrNo("Proceed with these settings")

        # Prepare the namespace and launch the restore pipeline
        if self.noConfirm or continueWithRestore:
            self.createTektonFileWithDigest()

            # Create secrets for config files if provided
            self.createConfigSecrets()

            self.printH1("Launch Restore")
            instanceId = self.getParam("mas_instance_id")
            pipelinesNamespace = f"mas-{instanceId}-pipelines"

            # Determine storage class and access mode for pipeline PVCs
            defaultStorageClasses = getDefaultStorageClasses(self.dynamicClient)
            if self.isSNO() or defaultStorageClasses.rwx == "none":
                self.pipelineStorageClass = defaultStorageClasses.rwo
                self.pipelineStorageAccessMode = "ReadWriteOnce"
            else:
                self.pipelineStorageClass = defaultStorageClasses.rwx
                self.pipelineStorageAccessMode = "ReadWriteMany"

            with Halo(text='Validating OpenShift Pipelines installation', spinner=self.spinner) as h:
                if installOpenShiftPipelines(self.dynamicClient):
                    h.stop_and_persist(symbol=self.successIcon, text="OpenShift Pipelines Operator is installed and ready to use")
                else:
                    h.stop_and_persist(symbol=self.failureIcon, text="OpenShift Pipelines Operator installation failed")
                    self.fatalError("Installation failed")

            with Halo(text=f'Preparing namespace ({pipelinesNamespace})', spinner=self.spinner) as h:
                createNamespace(self.dynamicClient, pipelinesNamespace)
                backupStorageSize = self.getParam("backup_storage_size") if self.getParam("backup_storage_size") else "20Gi"
                preparePipelinesNamespace(
                    dynClient=self.dynamicClient,
                    instanceId=instanceId,
                    storageClass=self.pipelineStorageClass,
                    accessMode=self.pipelineStorageAccessMode,
                    createBackupPVC=True,
                    backupStorageSize=backupStorageSize
                )

                # Apply config file secrets to the namespace
                prepareRestoreSecrets(dynClient=self.dynamicClient, namespace=pipelinesNamespace, restoreConfigs=self.configSecret)

                h.stop_and_persist(symbol=self.successIcon, text=f"Namespace is ready ({pipelinesNamespace})")

            with Halo(text=f'Installing latest Tekton definitions (v{self.version})', spinner=self.spinner) as h:
                updateTektonDefinitions(pipelinesNamespace, self.tektonDefsPath)
                h.stop_and_persist(symbol=self.successIcon, text=f"Latest Tekton definitions are installed (v{self.version})")

            with Halo(text="Submitting PipelineRun for MAS Restore", spinner=self.spinner) as h:
                pipelineURL = launchRestorePipeline(dynClient=self.dynamicClient, params=self.params)
                if pipelineURL is not None:
                    h.stop_and_persist(symbol=self.successIcon, text="PipelineRun for MAS restore submitted")
                    print_formatted_text(HTML(f"\nView progress:\n  <Cyan><u>{pipelineURL}</u></Cyan>\n"))
                else:
                    h.stop_and_persist(symbol=self.failureIcon, text="Failed to submit PipelineRun for MAS Restore, see log file for details")
                    print()

    def promptForInstanceId(self) -> None:
        self.printH1("Enter the MAS instance ID to restore from the backup")
        self.printDescription([" - Note: Use the same MAS instance ID as the backup you are restoring from."])
        self.promptForString(message="Instance ID", param="mas_instance_id", validator=InstanceIDFormatValidator())

    def promptForMASConfiguration(self) -> None:
        self.printH1("Maximo Application Suite Configuration")
        changeDomain = self.yesOrNo("Would you like to change the MAS domain in the Suite CR")
        if changeDomain:
            self.promptForString(message="MAS Domain", param="mas_domain_on_restore")

    def promptForSLSConfiguration(self) -> None:
        self.printH1("Suite-level SLS Configuration")
        # promt user to include slscfg from backup. if yes, promt for sls_url, if not prompt for sls_cfg_file.
        includeSLSCfg = self.yesOrNo("Would you like to restore Suite-level SLSCfg from backup")
        if includeSLSCfg:
            self.setParam("include_slscfg_from_backup", "true")
            changeSLSUrl = self.yesOrNo("Would you like to change the SLS URL in the Suite's SLSCfg CR")
            if changeSLSUrl:
                self.promptForString(message="SLS URL", param="sls_url_on_restore")
            else:
                self.setParam("sls_url_on_restore", "")
        else:
            self.setParam("include_slscfg_from_backup", "false")
            self.promptForString(message="SLS Configuration File, must be provided when not restoring from backup", param="sls_cfg_file", validator=FileExistsValidator())

    def promptForDROConfiguration(self) -> None:
        self.printH1("Suite-level DRO/BAS Configuration")
        # promt user to include bascfg from backup. if yes, promt for bas_url, if not prompt for dro_cfg_file.
        includeDROCfg = self.yesOrNo("Would you like to restore Suite-level BASCfg from backup")
        if includeDROCfg:
            self.setParam("include_drocfg_from_backup", "true")
            changeDROUrl = self.yesOrNo("Would you like to change the DRO URL in the Suite's BASCfg CR")
            if changeDROUrl:
                self.promptForString(message="BAS URL", param="dro_url_on_restore")
            else:
                self.setParam("dro_url_on_restore", "")
        else:
            self.setParam("include_drocfg_from_backup", "false")
            self.promptForString(message="DRO/BAS Configuration File, must be provided when not restoring from backup", param="dro_cfg_file", validator=FileExistsValidator())

    def promptForIncludeSLS(self) -> None:
        self.printH1("SLS Configuration")
        self.printDescription([" - You can restore SLS instance or bring your own SLS."])
        includeSLS: bool = self.yesOrNo("Would you like to restore SLS instance from backup")
        if includeSLS:
            self.setParam("include_sls", "true")
            # Prompt user to enter custom SLS Domain
            customSLSDomain: bool = self.yesOrNo("Would you like to change SLS Domain to use in SLS instance")
            if customSLSDomain:
                slsDomain = self.promptForString("Enter the SLS Domain to use in License Service CR")
                self.setParam("sls_domain", slsDomain)
            else:
                self.setParam("sls_domain", "")
        else:
            self.setParam("include_sls", "false")

    def promptForIncludeDRO(self) -> None:
        self.printH1("IBM Data Reporting Operator Configuration")
        self.printDescription([" - DRO is not part of backup/restore. You can install DRO instance or bring your own DRO."])
        includeDRO: bool = self.yesOrNo("Would you like the pipeline to install DRO instance")
        if includeDRO:
            self.setParam("include_dro", "true")
            self.promptForString("IBM entitlement key", "ibm_entitlement_key", isPassword=True)
            self.promptForString("Contact e-mail address", "dro_contact_email")
            self.promptForString("Contact first name", "dro_contact_firstname")
            self.promptForString("Contact last name", "dro_contact_lastname")
            self.promptForString("IBM Data Reporter Operator (DRO) Namespace", "dro_namespace", default="redhat-marketplace")
        else:
            self.setParam("include_dro", "false")

    def promptForIncludeGrafana(self) -> None:
        self.printH1("Grafana Configuration")
        self.printDescription([" - Grafana is not part of backup/restore. You can install Grafana instance or skip it."])
        includeGrafana: bool = self.yesOrNo("Would you like the pipeline to install Grafana instance")
        if includeGrafana:
            self.setParam("include_grafana", "true")
        else:
            self.setParam("include_grafana", "false")

    def promptForBackupStorageSize(self) -> None:
        self.printH1("Backup Storage Configuration")
        storageSize = self.promptForString("Enter PVC storage size, must be bigger than backup archive size.", default="20Gi")
        self.setParam("backup_storage_size", storageSize)

    def promptForBackupVersion(self) -> None:
        self.printH1("Backup Version Configuration")
        # Prompt user to enter custom backup version
        restore_version = self.promptForString("Set the backup version to use for this restore operation. (e.g. 2020260117-191701)")
        self.setParam("restore_version", restore_version)

    def setDefaultParams(self) -> None:
        """Set default values for optional parameters if not already set"""
        if not self.getParam("include_sls"):
            self.setParam("include_sls", "true")
        if not self.getParam("include_grafana"):
            self.setParam("include_grafana", "true")
        if not self.getParam("include_dro"):
            self.setParam("include_dro", "true")
        if not self.getParam("backup_storage_size"):
            self.setParam("backup_storage_size", "20Gi")
        if not self.getParam("include_slscfg_from_backup"):
            self.setParam("include_slscfg_from_backup", "true")
        if not self.getParam("include_drocfg_from_backup"):
            self.setParam("include_drocfg_from_backup", "true")
        if not self.getParam("clean_backup"):
            self.setParam("clean_backup", "true")

    def promptForDownloadConfiguration(self) -> None:
        """Prompt user for backup download configuration"""
        self.printH1("Backup Download Configuration")

        # Ask if user wants to download the backup
        downloadBackup = self.yesOrNo("Do you want to download the backup archive before restore")

        if downloadBackup:
            self.setParam("download_backup", "true")

            # Confirm backup archive name.
            confirmBackupArchiveName = self.yesOrNo(f"Confirm backup archive name - 'mas-{self.getParam('mas_instance_id')}-backup-{self.getParam('restore_version')}.tar.gz'")
            if not confirmBackupArchiveName:
                self.promptForString("Enter Custom backup archive name including tar.gz extension", "backup_archive_name")
            # Determine download destination based on dev_mode
            if self.devMode:
                self.printDescription([
                    "Development mode is enabled. Choose download location:"
                ])
                downloadDestination = self.promptForListSelect(
                    "Select download location",
                    ["S3", "Artifactory"],
                    "download_destination",
                    default=1
                )
            else:
                # Non-dev mode defaults to S3
                downloadDestination = "S3"
                self.printDescription(["Download Location: S3"])

            if downloadDestination == "S3":
                # Prompt for S3 credentials
                self.printH2("S3 Configuration")
                awsAccessKeyId = self.promptForString("AWS Access Key ID")
                self.setParam("aws_access_key_id", awsAccessKeyId)

                awsSecretAccessKey = self.promptForString("AWS Secret Access Key", isPassword=True)
                self.setParam("aws_secret_access_key", awsSecretAccessKey)

                s3BucketName = self.promptForString("S3 Bucket Name")
                self.setParam("s3_bucket_name", s3BucketName)

                s3Region = self.promptForString("AWS Region", default="us-east-1")
                self.setParam("s3_region", s3Region)
            else:
                # Prompt for Artifactory credentials
                self.printH2("Artifactory Configuration")

                # Check if artifactory credentials are already set from dev mode
                if not self.getParam("artifactory_username"):
                    artifactoryUsername = self.promptForString("Artifactory Username")
                    self.setParam("artifactory_username", artifactoryUsername)

                if not self.getParam("artifactory_token"):
                    artifactoryToken = self.promptForString("Artifactory Token", isPassword=True)
                    self.setParam("artifactory_token", artifactoryToken)

                artifactoryUrl = self.promptForString("Artifactory URL")
                self.setParam("artifactory_url", artifactoryUrl)

                artifactoryRepository = self.promptForString("Artifactory Repository")
                self.setParam("artifactory_repository", artifactoryRepository)

            cleanBackup = self.yesOrNo("Clean the downloaded backup files after completion")
            if cleanBackup:
                self.setParam("clean_backup", "true")
            else:
                self.setParam("clean_backup", "false")
        else:
            self.setParam("download_backup", "false")

    def promptForManageAppRestore(self) -> None:
        """Prompt user for Manage application restore configuration"""
        self.printH1("Manage Application Restore")
        self.printDescription([
            "In addition to restoring the MAS Suite, you can also restore the Manage application.",
            "This includes DB2, Manage namespace resources and persistent volume data."
        ])

        restoreManageApp = self.yesOrNo("Do you want to restore the Manage application")

        if restoreManageApp:
            self.setParam("restore_manage_app", "true")

            overrideAppSC = self.yesOrNo("Do you want to override the storage class for the Manage Application persistent volume")

            if overrideAppSC:
                self.setParam("manage_app_override_storageclass", "true")
                useCustomAppSC = self.yesOrNo("Do you want to use the custom storage class, if not default in cluster will be used")
                if useCustomAppSC:
                    manage_app_storage_class_rwx = self.promptForString("Manage Application - ReadWriteMany storage class name")
                    manage_app_storage_class_rwo = self.promptForString("Manage Application - ReadWriteOnce storage class name")
                    self.setParam("manage_app_storage_class_rwx", manage_app_storage_class_rwx)
                    self.setParam("manage_app_storage_class_rwo", manage_app_storage_class_rwo)
            else:
                self.setParam("manage_app_override_storageclass", "false")
            # Ask about DB2 restore
            self.printH2("Manage Database Restore")
            self.printDescription([
                "- The Manage application uses a Db2 database that should also be restored.",
                "- This will restore the incluster Db2 database associated with the Manage workspace."
                "- Note: This will be offline restore and the Manage application will be unavailable during the restore."
            ])

            restoreDb2 = self.yesOrNo("Do you want to restore the Manage database (Db2)")

            # Always set to disk for pipeline as s3 download is handled for the whole pipeline
            self.setParam("manage_db2_restore_vendor", "disk")
            if restoreDb2:
                self.setParam("restore_manage_db", "true")
                overrideStorageClass = self.yesOrNo("Do you want to override the storage class for the Manage database persistent volume")
                if overrideStorageClass:
                    self.setParam("manage_db_override_storageclass", "true")
                    useCustomSC = self.yesOrNo("Do you want to use the custom storage class, if not default in cluster will be used")
                    if useCustomSC:
                        manage_db_meta_storage_class = self.promptForString("DB2 Meta storage class name")
                        manage_db_data_storage_class = self.promptForString("DB2 Data storage class name")
                        manage_db_backup_storage_class = self.promptForString("DB2 Backup storage class name")
                        manage_db_logs_storage_class = self.promptForString("DB2 Logs storage class name")
                        manage_db_temp_storage_class = self.promptForString("Db2 temp storage class name")
                        self.setParam("manage_db_meta_storage_class", manage_db_meta_storage_class)
                        self.setParam("manage_db_data_storage_class", manage_db_data_storage_class)
                        self.setParam("manage_db_backup_storage_class", manage_db_backup_storage_class)
                        self.setParam("manage_db_logs_storage_class", manage_db_logs_storage_class)
                        self.setParam("manage_db_temp_storage_class", manage_db_temp_storage_class)
                else:
                    self.setParam("manage_db_override_storageclass", "false")
            else:
                self.setParam("restore_manage_db", "false")
        else:
            self.setParam("restore_manage_app", "false")
            self.setParam("restore_manage_db", "false")

    def addFilesToSecret(self, secretDict: dict, configPath: str, extension: str = '', keyPrefix: str = '') -> dict:
        """
        Add file (or files) to a secret
        """
        filesToProcess = []
        if path.isdir(configPath):
            logger.debug(f"Adding all config files in directory {configPath}")
            if extension:
                filesToProcess = glob(f"{configPath}/*.{extension}")
            else:
                filesToProcess = glob(f"{configPath}/*")
        else:
            logger.debug(f"Adding config file {configPath}")
            filesToProcess = [configPath]

        for fileToProcess in filesToProcess:
            logger.debug(f" * Processing config file {fileToProcess}")
            fileName = path.basename(fileToProcess)

            # Load the file
            with open(fileToProcess, 'r') as file:
                data = file.read()

            # Add/update an entry to the secret data
            if "data" not in secretDict:
                secretDict["data"] = {}
            secretDict["data"][keyPrefix + fileName] = b64encode(data.encode('ascii')).decode("ascii")

        return secretDict

    def createConfigSecrets(self) -> None:
        """
        Create a single secret for SLS and DRO configuration files if provided
        """
        self.configSecret = None

        slsCfgFile = self.getParam("sls_cfg_file")
        droCfgFile = self.getParam("dro_cfg_file")

        # Check if either config file is provided
        if slsCfgFile or droCfgFile:
            # Validate SLS config file exists if provided
            if slsCfgFile and not path.exists(slsCfgFile):
                self.fatalError(f"SLS configuration file not found: {slsCfgFile}")

            # Validate DRO config file exists if provided
            if droCfgFile and not path.exists(droCfgFile):
                self.fatalError(f"DRO configuration file not found: {droCfgFile}")

            # Create a single secret for both config files
            configSecret = {
                "apiVersion": "v1",
                "kind": "Secret",
                "type": "Opaque",
                "metadata": {
                    "name": "pipeline-restore-configs"
                }
            }

            # Add SLS config file to secret if provided
            if slsCfgFile:
                configSecret = self.addFilesToSecret(configSecret, slsCfgFile, '')
                # Update the param to point to the mounted file path
                self.setParam("sls_cfg_file", f"/workspace/restore/{path.basename(slsCfgFile)}")
                logger.debug(f"Added SLS config file to secret: {path.basename(slsCfgFile)}")

            # Add DRO config file to secret if provided
            if droCfgFile:
                configSecret = self.addFilesToSecret(configSecret, droCfgFile, '')
                # Update the param to point to the mounted file path
                self.setParam("dro_cfg_file", f"/workspace/restore/{path.basename(droCfgFile)}")
                logger.debug(f"Added DRO config file to secret: {path.basename(droCfgFile)}")

            self.configSecret = configSecret
