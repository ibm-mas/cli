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
from datetime import datetime
from halo import Halo
from prompt_toolkit import print_formatted_text, HTML
from prompt_toolkit.completion import WordCompleter

from openshift.dynamic.exceptions import ResourceNotFoundError

from ..cli import BaseApp
from ..validators import InstanceIDValidator
from .argParser import backupArgParser
from mas.devops.ocp import createNamespace, getConsoleURL
from mas.devops.mas import listMasInstances, getDefaultStorageClasses, getWorkspaceId
from mas.devops.tekton import preparePipelinesNamespace, installOpenShiftPipelines, updateTektonDefinitions, launchBackupPipeline


logger = logging.getLogger(__name__)


class BackupApp(BaseApp):

    def backup(self, argv):
        """
        Backup MAS instance
        """
        self.args = backupArgParser.parse_args(args=argv)
        self.noConfirm = self.args.no_confirm
        self.devMode = self.args.dev_mode
        self.interactive_mode = True

        if self.args.skip_pre_check:
            self.setParam("skip_pre_check", "true")

        if self.args.mas_instance_id:
            # Non-interactive mode
            self.interactive_mode = False
            logger.debug("MAS Instance ID is set, so we assume already connected to the desired OCP")
            requiredParams = ["mas_instance_id"]
            optionalParams = [
                "backup_version",
                "backup_storage_size",
                "clean_backup",
                "include_sls",
                "mongodb_namespace",
                "mongodb_instance_name",
                "mongodb_provider",
                "sls_namespace",
                "cert_manager_provider",
                "skip_pre_check",
                "dev_mode",
                # Dev Mode
                "artifactory_username",
                "artifactory_token",
                # Upload Configuration
                "upload_backup",
                "aws_access_key_id",
                "aws_secret_access_key",
                "s3_bucket_name",
                "s3_region",
                "artifactory_url",
                "artifactory_repository",
                # Manage App Backup
                "mas_app_id",
                "mas_workspace_id",
                "backup_manage_app",
                "backup_manage_db"
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
                elif key in ["no_confirm", "help", "upload_destination"]:
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

        # Review MAS instances
        isMasInstalled = self.reviewMASInstance()
        if not isMasInstalled:
            self.fatalError("No MAS instances were detected on the cluster => nothing to backup! See log file for details")

        # If instance ID not provided, prompt for it
        if self.interactive_mode:

            if self.args.mas_instance_id is None:
                self.promptForInstanceId()

            # Prompt for backup storage size if not provided
            if self.args.backup_storage_size is None:
                self.promptForBackupStorageSize()

            # Prompt for backup version if not provided
            if self.args.backup_version is None:
                self.promptForBackupVersion()

            # Prompt for clean backup option if not provided
            if self.args.clean_backup is None:
                self.promptForCleanBackup()

            # Prompt for Manage app backup
            self.promptForManageAppBackup()

            self.promptForUploadConfiguration()

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

        self.printH2("Backup Configuration")
        self.printSummary("Backup Directory", "/workspace/backups (hardcoded)")
        self.printSummary("Config Directory", "/workspace/configs (hardcoded)")
        self.printSummary("Backup Storage Size", self.getParam("backup_storage_size"))
        self.printSummary("Backup Version", self.getParam("backup_version"))
        self.printSummary("Clean Workspaces After Completion", self.getParam("clean_backup") if self.getParam("clean_backup") else "true")

        self.printH2("Components")
        self.printSummary("Include SLS", self.getParam("include_sls") if self.getParam("include_sls") else "true")
        self.printSummary("MongoDB Namespace", self.getParam("mongodb_namespace") if self.getParam("mongodb_namespace") else "mongoce")
        self.printSummary("SLS Namespace", self.getParam("sls_namespace") if self.getParam("sls_namespace") else "ibm-sls")

        if self.getParam("backup_manage_app") == "true":
            self.printH2("Manage Application Backup")
            self.printSummary("Backup Manage App", "Yes")
            self.printSummary("Workspace ID", self.getParam("mas_workspace_id"))
            self.printSummary("Backup Manage incluster Db2 Database", "Yes" if self.getParam("backup_manage_db") == "true" else "No")
            if self.getParam("backup_manage_db") == "true":
                self.printSummary("Db2 Namespace", self.getParam("db2_namespace"))
                self.printSummary("Db2 Instance Name", self.getParam("db2_instance_name"))
                self.printSummary("Db2 Backup Type", self.getParam("backup_type"))

        continueWithBackup = True
        if not self.noConfirm:
            print()
            self.printDescription([
                "Please carefully review your choices above, correcting mistakes now is much easier than after the backup has begun"
            ])
            continueWithBackup = self.yesOrNo("Proceed with these settings")

        # Prepare the namespace and launch the backup pipeline
        if self.noConfirm or continueWithBackup:
            self.createTektonFileWithDigest()

            self.printH1("Launch Backup")
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

            with Halo(text="Submitting PipelineRun for MAS backup", spinner=self.spinner) as h:
                pipelineURL = launchBackupPipeline(dynClient=self.dynamicClient, params=self.params)
                if pipelineURL is not None:
                    h.stop_and_persist(symbol=self.successIcon, text="PipelineRun for MAS backup submitted")
                    print_formatted_text(HTML(f"\nView progress:\n  <Cyan><u>{pipelineURL}</u></Cyan>\n"))
                else:
                    h.stop_and_persist(symbol=self.failureIcon, text="Failed to submit PipelineRun for MAS backup, see log file for details")
                    print()

    def reviewMASInstance(self) -> bool:
        self.printH1("Review MAS Instances")
        try:
            instances = listMasInstances(self.dynamicClient)
            self.printDescription(["The following MAS instances are installed on the target cluster:"])
            for instance in instances:
                self.printDescription([f"- <u>{instance['metadata']['name']}</u> v{instance['status']['versions']['reconciled']}"])
            return True
        except ResourceNotFoundError:
            self.printDescription(["No MAS instances were detected on the cluster (Suite.core.mas.ibm.com/v1 API is not available)"])
            return False

    def promptForInstanceId(self) -> None:
        self.printH1("Select MAS Instance")
        try:
            instances = listMasInstances(self.dynamicClient)
            if len(instances) == 0:
                self.fatalError("No MAS instances found on the cluster")
            elif len(instances) == 1:
                instanceId = instances[0]['metadata']['name']
                self.setParam("mas_instance_id", instanceId)
                self.printDescription([f"Using MAS instance: <u>{instanceId}</u>"])
            else:
                instanceOptions = []
                for instance in instances:
                    self.printDescription([f"- <u>{instance['metadata']['name']}</u> v{instance['status']['versions']['reconciled']}"])
                    instanceOptions.append(instance['metadata']['name'])

                instanceCompleter = WordCompleter(instanceOptions)
                print()
                instanceId = self.promptForString("MAS instance ID", completer=instanceCompleter, validator=InstanceIDValidator())
                self.setParam("mas_instance_id", instanceId)

        except ResourceNotFoundError:
            self.fatalError("Unable to list MAS instances")

    def promptForBackupStorageSize(self) -> None:
        self.printH1("Backup Storage Configuration")
        storageSize = self.promptForString("Enter backup PVC storage size", default="20Gi")
        self.setParam("backup_storage_size", storageSize)

    def promptForBackupVersion(self) -> None:
        self.printH1("Backup Version Configuration")
        useAutoGenerated = self.yesOrNo("Use autogenerated backup_version based on timestamp")

        if useAutoGenerated:
            # Auto-generate timestamp
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            self.setParam("backup_version", timestamp)
            self.printDescription([f"Using autogenerated backup version: <u>{timestamp}</u>"])
        else:
            # Prompt user to enter custom backup version
            backupVersion = self.promptForString("Set the backup version to use for this backup")
            self.setParam("backup_version", backupVersion)

    def promptForCleanBackup(self) -> None:
        self.printH1("Backup Cleanup Configuration")
        self.printDescription([
            "After the backup completes, the backup and config workspaces can be cleaned to free up space.",
            "This is recommended unless you need to inspect the workspace contents for troubleshooting."
        ])
        cleanBackup = self.yesOrNo("Clean backup and config workspaces after completion")

        if cleanBackup:
            self.setParam("clean_backup", "true")
        else:
            self.setParam("clean_backup", "false")

    def setDefaultParams(self) -> None:
        """Set default values for optional parameters if not already set"""
        if not self.getParam("mongodb_namespace"):
            self.setParam("mongodb_namespace", "mongoce")
        if not self.getParam("mongodb_instance_name"):
            self.setParam("mongodb_instance_name", "mas-mongo-ce")
        if not self.getParam("mongodb_provider"):
            self.setParam("mongodb_provider", "community")
        if not self.getParam("sls_namespace"):
            self.setParam("sls_namespace", "ibm-sls")
        if not self.getParam("cert_manager_provider"):
            self.setParam("cert_manager_provider", "redhat")
        if not self.getParam("include_sls"):
            self.setParam("include_sls", "true")
        if not self.getParam("backup_storage_size"):
            self.setParam("backup_storage_size", "20Gi")
        if not self.getParam("backup_version"):
            # Auto-generate timestamp
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            self.setParam("backup_version", timestamp)
        if not self.getParam("clean_backup"):
            self.setParam("clean_backup", "true")

    def promptForUploadConfiguration(self) -> None:
        """Prompt user for backup upload configuration"""
        self.printH1("Backup Upload Configuration")

        # Ask if user wants to upload the backup
        uploadBackup = self.yesOrNo("Do you want to upload the backup archive after completion")

        if uploadBackup:
            self.setParam("upload_backup", "true")

            # Determine upload destination based on dev_mode
            if self.devMode:
                self.printDescription([
                    "Development mode is enabled. Choose upload destination:"
                    " 1. S3",
                    " 2. Artifactory",
                ])
                uploadDestination = self.promptForListSelect(
                    "Select upload destination",
                    ["S3", "Artifactory"],
                    "upload_destination",
                    default=1
                )
            else:
                # Non-dev mode defaults to S3
                uploadDestination = "S3"
                self.printDescription(["Upload destination: S3"])

            if uploadDestination == "S3":
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
            self.setParam("upload_backup", "false")

    def promptForManageAppBackup(self) -> None:
        """Prompt user for Manage application backup configuration"""
        self.printH1("Manage Application Backup")
        self.printDescription([
            "In addition to backing up the MAS Suite, you can also backup the Manage application.",
            "This includes the Manage namespace resources and persistent volume data."
        ])

        backupManageApp = self.yesOrNo("Do you want to backup the Manage application")

        if backupManageApp:
            self.setParam("backup_manage_app", "true")
            self.setParam("mas_app_id", "manage")

            # Get workspace ID - try to auto-detect first
            try:
                instanceId = self.getParam("mas_instance_id")
                workspaceId = getWorkspaceId(self.dynamicClient, instanceId)
                if workspaceId:
                    self.printDescription([f"Detected Manage workspace: <u>{workspaceId}</u>"])
                    useDetected = self.yesOrNo("Use this workspace")
                    if useDetected:
                        self.setParam("mas_workspace_id", workspaceId)
                    else:
                        workspaceId = self.promptForString("Enter Manage workspace ID")
                        self.setParam("mas_workspace_id", workspaceId)
                else:
                    workspaceId = self.promptForString("Enter Manage workspace ID")
                    self.setParam("mas_workspace_id", workspaceId)
            except Exception:
                workspaceId = self.promptForString("Enter Manage workspace ID")
                self.setParam("mas_workspace_id", workspaceId)

            # Ask about DB2 backup
            self.printH2("Manage Database Backup")
            self.printDescription([
                "The Manage application uses a Db2 database that should also be backed up.",
                "This will backup the incluster Db2 database associated with the Manage workspace."
            ])
            backupDb2 = self.yesOrNo("Do you want to backup the Manage database (Db2)")

            if backupDb2:
                self.setParam("backup_manage_db", "true")
                self.promptForDb2BackupConfiguration()
            else:
                self.setParam("backup_manage_db", "false")
        else:
            self.setParam("backup_manage_app", "false")
            self.setParam("backup_manage_db", "false")

    def promptForDb2BackupConfiguration(self) -> None:
        """Prompt user for Db2 backup configuration - reusable for any app that uses Db2"""
        self.printH2("Db2 Configuration")

        # DB2 namespace
        db2Namespace = self.promptForString("Enter Db2 namespace", default="db2u")
        self.setParam("db2_namespace", db2Namespace)

        # DB2 instance name
        instanceId = self.getParam("mas_instance_id")
        workspaceID = self.getParam("mas_workspace_id")
        appId = self.getParam("mas_app_id")
        db2InstanceName = self.promptForString("Enter Db2 instance name", default=f"mas-{instanceId}-{workspaceID}-{appId}")
        self.setParam("db2_instance_name", db2InstanceName)

        # Backup type
        self.printDescription([
            "Db2 backup can be performed online (database remains available) or offline (database unavailable during backup).",
            "Note: If your Db2 instance uses circular logging (default), you must use offline backup."
            "Backup Types:"
            " 1. online",
            " 2. offline",
        ])
        backupType = self.promptForListSelect(
            message="Select backup type",
            options=["online", "offline"],
            param="backup_type",
            default=1
        )
        self.setParam("backup_type", backupType)

        # Set backup version to match main backup version
        if self.getParam("backup_version"):
            self.setParam("db2_backup_version", self.getParam("backup_version"))
