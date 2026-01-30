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
from halo import Halo
from prompt_toolkit import print_formatted_text, HTML

from ..cli import BaseApp
from ..validators import InstanceIDFormatValidator
from .argParser import restoreArgParser
from mas.devops.ocp import createNamespace, getConsoleURL
from mas.devops.mas import getDefaultStorageClasses
from mas.devops.tekton import preparePipelinesNamespace, installOpenShiftPipelines, updateTektonDefinitions, launchRestorePipeline

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

        if self.args.mas_instance_id:
            # Non-interactive mode
            self.interactive_mode = False
            logger.debug("MAS Instance ID is set, so we assume already connected to the desired OCP")
            requiredParams = ["mas_instance_id", "restore_version"]
            optionalParams = [
                "backup_storage_size",
                "include_sls",
                "include_grafana",
                "include_dro",
                "skip_pre_check",
                "dev_mode",
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
                "artifactory_repository"
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

            # Prompt for backup storage size if not provided
            if self.args.backup_storage_size is None:
                self.promptForBackupStorageSize()

            self.promptForDROConfiguration()

            self.promptForDownloadConfiguration()

        # Set default values for optional parameters if not provided
        self.setDefaultParams()

        print()

        self.printH1("Review Settings")
        self.printDescription([
            "Connected to:",
            f" - <u>{getConsoleURL(self.dynamicClient)}</u>"
        ])

        self.printH2("MAS Instance")
        self.printSummary("Instance ID", self.getParam("mas_instance_id"))

        self.printH2("Restore Configuration")
        self.printSummary("Backup Directory", "/workspace/backups (hardcoded)")
        self.printSummary("Config Directory", "/workspace/configs (hardcoded)")
        self.printSummary("Backup Storage Size", self.getParam("backup_storage_size"))
        self.printSummary("Backup Version to restore", self.getParam("restore_version"))

        self.printH2("Components")
        self.printSummary("Include Grafana", self.getParam("include_grafana") if self.getParam("include_grafana") else "true")
        self.printSummary("Include SLS", self.getParam("include_sls") if self.getParam("include_sls") else "true")
        self.printSummary("Include DRO", self.getParam("include_dro") if self.getParam("include_dro") else "true")

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

    def promptForBackupStorageSize(self) -> None:
        self.printH1("Backup Storage Configuration")
        storageSize = self.promptForString("Enter PVC storage size, must be bigger than backup archive size. (e.g. 20Gi))", default="20Gi")
        self.setParam("backup_storage_size", storageSize)

    def promptForBackupVersion(self) -> None:
        self.printH1("Backup Version Configuration")
        # Prompt user to enter custom backup version
        restore_version = self.promptForString("Set the backup version to use for this restore operation. (e.g. 20260117-191701)")
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
        if not self.getParam("backup_archive_name"):
            self.setParam("backup_archive_name", "")

    def promptForDROConfiguration(self) -> None:
        """Prompt user for IBM Data Reporting Operator configuration"""
        if self.args.include_dro:
            if self.args.dro_contact_email is None or self.args.dro_contact_firstname is None or self.args.dro_contact_lastname is None or self.args.ibm_entitlement_key is None:
                self.printH1("IBM Data Reporting Operator configuration Configuration")
                self.promptForString("IBM entitlement key", "ibm_entitlement_key", isPassword=True)
                self.promptForString("Contact e-mail address", "dro_contact_email")
                self.promptForString("Contact first name", "dro_contact_firstname")
                self.promptForString("Contact last name", "dro_contact_lastname")
                self.promptForString("IBM Data Reporter Operator (DRO) Namespace", "dro_namespace", default="redhat-marketplace")

    def promptForDownloadConfiguration(self) -> None:
        """Prompt user for backup download configuration"""
        self.printH1("Backup Download Configuration")

        # Ask if user wants to download the backup
        downloadBackup = self.yesOrNo("Do you want to download the backup archive before restore")

        if downloadBackup:
            self.setParam("download_backup", "true")

            # Confirm backup archive name.
            confirmBackupArchiveName = self.yesOrNo(f"Confirm backup archive name - 'mas-backup-{self.getParam('restore_version')}.tar.gz'")
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
        else:
            self.setParam("download_backup", "false")
