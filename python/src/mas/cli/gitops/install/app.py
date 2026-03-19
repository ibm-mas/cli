#!/usr/bin/env python
# *****************************************************************************
# Copyright (c) 2024, 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

import logging

from sys import exit
from prompt_toolkit import print_formatted_text, HTML

from ...cli import BaseApp
from ...gencfg import ConfigGeneratorMixin
from .argBuilder import GitOpsInstallArgBuilderMixin
from .argParser import gitops_install_arg_parser
from .summarizer import GitOpsInstallSummarizerMixin
from .params import requiredParams, commonParams

from .settings.gitopsSettings import GitOpsInstallGitOpsSettingsMixin
from .settings.clusterSettings import GitOpsInstallClusterSettingsMixin
from .settings.instanceSettings import GitOpsInstallInstanceSettingsMixin
from .settings.appsSettings import GitOpsInstallAppsSettingsMixin

from .executor import GitOpsInstallExecutor


logger = logging.getLogger(__name__)


def logMethodCall(func):
    """Decorator to log method entry and exit for debugging purposes."""

    def wrapper(self, *args, **kwargs):
        logger.debug(f">>> GitOpsInstallApp.{func.__name__}")
        result = func(self, *args, **kwargs)
        logger.debug(f"<<< GitOpsInstallApp.{func.__name__}")
        return result
    return wrapper


class GitOpsInstallApp(
    BaseApp,
    GitOpsInstallArgBuilderMixin,
    GitOpsInstallSummarizerMixin,
    GitOpsInstallGitOpsSettingsMixin,
    GitOpsInstallClusterSettingsMixin,
    GitOpsInstallInstanceSettingsMixin,
    GitOpsInstallAppsSettingsMixin,
    ConfigGeneratorMixin
):
    """
    Main application class for the 'mas gitops-install' command.

    This class orchestrates the GitOps-based installation of MAS by:
    - Configuring cluster-level prerequisites
    - Setting up MAS instances
    - Deploying MAS applications
    - Managing the GitOps repository structure

    The installation follows a GitOps approach where all configuration is
    stored in a Git repository and applied via ArgoCD.
    """

    @logMethodCall
    def install(self, argv):
        """
        Main entry point for the GitOps-install command.

        This method will:
        1. Parse command-line arguments
        2. Determine interactive vs non-interactive mode
        3. Collect configuration for cluster, instance, and applications
        4. Generate GitOps configuration files
        5. Initialize or update the GitOps repository
        6. Deploy ArgoCD applications

        Args:
            argv: Command-line arguments passed to the install command
        """
        args = gitops_install_arg_parser.parse_args(args=argv)

        # Store arguments and control flags
        self.args = args
        self.noConfirm = args.no_confirm
        self.licenseAccepted = args.accept_license

        # Check if we're in interactive mode (account_id not provided)
        accountId = args.account_id

        # Set execution mode based on arguments or prompt in interactive mode
        if args.direct:
            self.useTekton = False
            self.executionMode = 'direct'
        elif args.use_tekton:
            self.useTekton = True
            self.executionMode = 'tekton'
        elif accountId is None:
            # Interactive mode - prompt for execution mode
            self.useTekton = None  # Will be set after prompt
            self.executionMode = None  # Will be set after prompt
        else:
            # Non-interactive mode without explicit flag - default to Tekton
            self.useTekton = True
            self.executionMode = 'tekton'

        if accountId is None:
            # Interactive mode
            self.printH1("Set Target OpenShift Cluster")
            self.connect()
        else:
            # Non-interactive mode - verify connection before proceeding
            logger.debug("Account ID is set, assuming already connected to the desired OCP")
            # Attempt to load the dynamic client to verify connection
            self.reloadDynamicClient()
            if self.dynamicClient is None:
                self.fatalError("Not connected to an OpenShift cluster. Please log in using 'oc login' before running in non-interactive mode.")
            self.lookupTargetArchitecture()

        if self.dynamicClient is None:
            print_formatted_text(HTML("<Red>Error: The Kubernetes dynamic Client is not available. See log file for details</Red>"))
            exit(1)

        # Collect configuration based on mode
        if accountId is None:
            self.interactiveMode(simplified=args.simplified, advanced=args.advanced)
        else:
            self.nonInteractiveMode()

        # Show non-interactive command only in interactive mode
        if accountId is None:
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
            if self.yesOrNo("Proceed with these settings"):
                self.executeInstallation()
        else:
            # In non-interactive mode, proceed automatically
            self.executeInstallation()

    @logMethodCall
    def interactiveMode(self, simplified: bool, advanced: bool) -> None:
        """
        Interactive installation flow with 8 steps.

        Steps:
        1. Choose install flavor (simplified vs advanced)
        2. Catalog selection
        3. GitOps configuration
        4. Cluster configuration
        5. Instance configuration
        6. Applications configuration
        7. Review configuration
        8. Launch installation

        Args:
            simplified: If True, show simplified installation options
            advanced: If True, show advanced installation options
        """
        self.isInteractiveMode = True

        # Prompt for execution mode if not already set
        if self.executionMode is None:
            self.chooseExecutionMode()

        # Step 1: Choose install flavor
        if simplified:
            self.showAdvancedOptions = False
            self.installFlavour = "simplified"
        elif advanced:
            self.showAdvancedOptions = True
            self.installFlavour = "advanced"
        else:
            self.chooseInstallFlavour()

        # Step 2: Catalog selection
        self.printH1("Step 2: Catalog Selection")
        self.configClusterCatalog()

        # Step 3: GitOps configuration
        self.printH1("Step 3: GitOps Configuration")
        self.configGitOpsRepository()
        self.configGitOpsCluster()
        self.configGitOpsSecrets()

        # Step 4: Cluster configuration
        self.printH1("Step 4: Cluster Configuration")

        # Configure storage classes (required for all modes)
        self.configStorageClasses()

        if self.installFlavour == "advanced":
            self.configClusterOperators()
        else:
            # In simplified mode, use defaults for cluster operators
            self.setParam("install_dro", "false")
            self.setParam("install_gpu", "false")
            self.setParam("install_cert_manager", "true")
            self.setParam("install_nfd", "false")

        # Step 5: Instance configuration
        self.printH1("Step 5: MAS Instance Configuration")
        self.configMASInstance()
        self.configMASWorkspace()

        # SLS Entitlement file (required for all modes)
        self.configSLSEntitlementFile()

        # Optional: SMTP and LDAP configuration (advanced mode only)
        if self.installFlavour == "advanced":
            if self.yesOrNo("Configure SMTP for email notifications"):
                self.configSMTP()
            if self.yesOrNo("Configure LDAP for user authentication"):
                self.configLDAP()
            if self.yesOrNo("Configure advanced GitOps configuration files"):
                self.configAdvancedGitOpsFiles()

        # Step 6: Applications configuration
        self.printH1("Step 6: MAS Applications Configuration")
        self.configApplications()

        # Note: Configuration review and confirmation happens in install() method
        # via displayInstallSummary() to avoid duplication

        # Step 7: Confirm before proceeding
        if not self.noConfirm:
            if not self.yesOrNo("Proceed with installation"):
                logger.info("Installation cancelled by user")
                exit(0)

        # Note: The install() method will call displayInstallSummary() and executeInstallation()

    @logMethodCall
    def nonInteractiveMode(self) -> None:
        """
        Handle non-interactive installation mode using command-line arguments.

        All required configuration must be provided via command-line arguments
        or environment variables. This method:
        1. Sets execution mode (Tekton vs direct)
        2. Maps all CLI arguments to internal parameters
        3. Validates required parameters
        4. Handles per-app configuration
        """
        self.isInteractiveMode = False
        self.showAdvancedOptions = False

        logger.info("Starting non-interactive GitOps installation")

        # Set execution mode
        if self.args.direct:
            self.useTekton = False
            logger.info("Execution mode: Direct")
        else:
            self.useTekton = True  # Default to Tekton
            logger.info("Execution mode: Tekton")

        # Map GitOps Configuration arguments
        if self.args.github_host:
            self.setParam('github_host', self.args.github_host)
        if self.args.github_org:
            self.setParam('github_org', self.args.github_org)
        if self.args.github_repo:
            self.setParam('github_repo', self.args.github_repo)
        if self.args.git_branch:
            self.setParam('git_branch', self.args.git_branch)
        if self.args.gitops_repo_token_secret:
            self.setParam('gitops_repo_token_secret', self.args.gitops_repo_token_secret)
        if self.args.account_id:
            self.setParam('account_id', self.args.account_id)
        if self.args.cluster_id:
            self.setParam('cluster_id', self.args.cluster_id)
        if self.args.cluster_url:
            self.setParam('cluster_url', self.args.cluster_url)
        if self.args.secrets_path:
            self.setParam('secrets_path', self.args.secrets_path)
        if self.args.avp_aws_secret_region:
            self.setParam('avp_aws_secret_region', self.args.avp_aws_secret_region)
        if self.args.sm_aws_access_key_id:
            self.setParam('sm_aws_access_key_id', self.args.sm_aws_access_key_id)
        if self.args.sm_aws_secret_access_key:
            self.setParam('sm_aws_secret_access_key', self.args.sm_aws_secret_access_key)

        # Map Cluster Configuration arguments
        if self.args.mas_catalog_version:
            self.setParam('mas_catalog_version', self.args.mas_catalog_version)
        if self.args.mas_catalog_image:
            self.setParam('mas_catalog_image', self.args.mas_catalog_image)
        if self.args.ibm_entitlement_key:
            self.setParam('ibm_entitlement_key', self.args.ibm_entitlement_key)
        if self.args.install_dro:
            self.setParam('install_dro', self.args.install_dro)
        if self.args.dro_namespace:
            self.setParam('dro_namespace', self.args.dro_namespace)
        if self.args.dro_install_plan:
            self.setParam('dro_install_plan', self.args.dro_install_plan)
        if self.args.install_gpu:
            self.setParam('install_gpu', self.args.install_gpu)
        if self.args.gpu_namespace:
            self.setParam('gpu_namespace', self.args.gpu_namespace)
        if self.args.install_cert_manager:
            self.setParam('install_cert_manager', self.args.install_cert_manager)
        if self.args.install_nfd:
            self.setParam('install_nfd', self.args.install_nfd)
        if self.args.storage_class_rwo:
            self.setParam('storage_class_rwo', self.args.storage_class_rwo)
        if self.args.storage_class_rwx:
            self.setParam('storage_class_rwx', self.args.storage_class_rwx)

        # Map Instance Configuration arguments
        if self.args.mas_instance_id:
            self.setParam('mas_instance_id', self.args.mas_instance_id)
        if self.args.mas_channel:
            self.setParam('mas_channel', self.args.mas_channel)
        if self.args.mas_domain:
            self.setParam('mas_domain', self.args.mas_domain)
        if self.args.ocp_domain:
            self.setParam('ocp_domain', self.args.ocp_domain)
        if self.args.dns_provider:
            self.setParam('dns_provider', self.args.dns_provider)

        # If mas_domain is blank/empty, set dns_provider to blank
        mas_domain = self.getParam('mas_domain')
        if not mas_domain or mas_domain.strip() == "":
            self.setParam('dns_provider', '')
            logger.debug("mas_domain is blank, setting dns_provider to blank")

        if self.args.mas_workspace_id:
            self.setParam('mas_workspace_id', self.args.mas_workspace_id)
        if self.args.mas_workspace_name:
            self.setParam('mas_workspace_name', self.args.mas_workspace_name)
        if self.args.operational_mode:
            self.setParam('operational_mode', self.args.operational_mode)
        if self.args.sls_channel:
            self.setParam('sls_channel', self.args.sls_channel)
        if self.args.sls_instance_name:
            self.setParam('sls_instance_name', self.args.sls_instance_name)
        if self.args.mongo_provider:
            self.setParam('mongo_provider', self.args.mongo_provider)
        if self.args.mongo_namespace:
            self.setParam('mongo_namespace', self.args.mongo_namespace)
        if self.args.mongodb_action:
            self.setParam('mongodb_action', self.args.mongodb_action)
        if self.args.mongo_yaml_file:
            self.setParam('mongo_yaml_file', self.args.mongo_yaml_file)
        if self.args.mongo_username:
            self.setParam('mongo_username', self.args.mongo_username)
        if self.args.mongo_password:
            self.setParam('mongo_password', self.args.mongo_password)

        # Map Dependencies Configuration (optional)
        if self.args.kafka_action:
            self.setParam('kafka_action', self.args.kafka_action)
        if self.args.efs_action:
            self.setParam('efs_action', self.args.efs_action)
        if self.args.cos_action:
            self.setParam('cos_action', self.args.cos_action)

        # Map SMTP Configuration (optional)
        if self.args.smtp_host:
            self.setParam('smtp_host', self.args.smtp_host)
        if self.args.smtp_port:
            self.setParam('smtp_port', self.args.smtp_port)
        if self.args.smtp_username:
            self.setParam('smtp_username', self.args.smtp_username)
        if self.args.smtp_password:
            self.setParam('smtp_password', self.args.smtp_password)
        if self.args.smtp_from:
            self.setParam('smtp_from', self.args.smtp_from)

        # Map LDAP Configuration (optional)
        if self.args.ldap_url:
            self.setParam('ldap_url', self.args.ldap_url)
        if self.args.ldap_bind_dn:
            self.setParam('ldap_bind_dn', self.args.ldap_bind_dn)
        if self.args.ldap_bind_password:
            self.setParam('ldap_bind_password', self.args.ldap_bind_password)
        if self.args.ldap_user_base_dn:
            self.setParam('ldap_user_base_dn', self.args.ldap_user_base_dn)
        if self.args.ldap_group_base_dn:
            self.setParam('ldap_group_base_dn', self.args.ldap_group_base_dn)
        if self.args.ldap_certificate_file:
            self.setParam('ldap_certificate_file', self.args.ldap_certificate_file)

        # Map Advanced GitOps Configuration Files (optional)
        if self.args.sls_entitlement_file:
            self.setParam('sls_entitlement_file', self.args.sls_entitlement_file)
        if self.args.dro_ca_certificate_file:
            self.setParam('dro_ca_certificate_file', self.args.dro_ca_certificate_file)
        if self.args.mas_manual_certs_yaml:
            self.setParam('mas_manual_certs_yaml', self.args.mas_manual_certs_yaml)
        if self.args.mas_pod_template_file:
            self.setParam('mas_pod_template_file', self.args.mas_pod_template_file)
        if self.args.mas_bascfg_pod_template_file:
            self.setParam('mas_bascfg_pod_template_file', self.args.mas_bascfg_pod_template_file)
        if self.args.mas_slscfg_pod_template_file:
            self.setParam('mas_slscfg_pod_template_file', self.args.mas_slscfg_pod_template_file)
        if self.args.mas_smtpcfg_pod_template_file:
            self.setParam('mas_smtpcfg_pod_template_file', self.args.mas_smtpcfg_pod_template_file)
        if self.args.mas_appcfg_pod_template_file:
            self.setParam('mas_appcfg_pod_template_file', self.args.mas_appcfg_pod_template_file)
        if self.args.suite_spec_additional_properties_yaml:
            self.setParam('suite_spec_additional_properties_yaml', self.args.suite_spec_additional_properties_yaml)
        if self.args.suite_spec_settings_additional_properties_yaml:
            self.setParam('suite_spec_settings_additional_properties_yaml', self.args.suite_spec_settings_additional_properties_yaml)
        if self.args.smtp_config_ca_certificate_file:
            self.setParam('smtp_config_ca_certificate_file', self.args.smtp_config_ca_certificate_file)

        # Map Applications Configuration
        if self.args.mas_app_ids:
            self.mas_app_ids = [app.strip() for app in self.args.mas_app_ids.split(',')]
            self.setParam('mas_app_ids', self.args.mas_app_ids)
            logger.info(f"Applications to install: {', '.join(self.mas_app_ids)}")

            # Per-app configuration
            for app_id in self.mas_app_ids:
                # Handle app IDs with hyphens (e.g., visual-inspection -> visualinspection)
                app_arg = app_id.replace('-', '')

                # Channel
                channel_attr = f'{app_arg}_channel'
                if hasattr(self.args, channel_attr):
                    channel_value = getattr(self.args, channel_attr)
                    if channel_value:
                        self.setParam(f'{app_id}_channel', channel_value)
                        logger.debug(f"Set {app_id}_channel = {channel_value}")

                # Database action
                db_action_attr = f'{app_arg}_db_action'
                if hasattr(self.args, db_action_attr):
                    db_action_value = getattr(self.args, db_action_attr)
                    if db_action_value:
                        self.setParam(f'{app_id}_db_action', db_action_value)
                        logger.debug(f"Set {app_id}_db_action = {db_action_value}")

                # Database type
                db_type_attr = f'{app_arg}_db_type'
                if hasattr(self.args, db_type_attr):
                    db_type_value = getattr(self.args, db_type_attr)
                    if db_type_value:
                        self.setParam(f'{app_id}_db_type', db_type_value)
                        logger.debug(f"Set {app_id}_db_type = {db_type_value}")

                # Database host
                db_host_attr = f'{app_arg}_db_host'
                if hasattr(self.args, db_host_attr):
                    db_host_value = getattr(self.args, db_host_attr)
                    if db_host_value:
                        self.setParam(f'{app_id}_db_host', db_host_value)
                        logger.debug(f"Set {app_id}_db_host = {db_host_value}")

                # Database port
                db_port_attr = f'{app_arg}_db_port'
                if hasattr(self.args, db_port_attr):
                    db_port_value = getattr(self.args, db_port_attr)
                    if db_port_value:
                        self.setParam(f'{app_id}_db_port', db_port_value)
                        logger.debug(f"Set {app_id}_db_port = {db_port_value}")

                # Database name
                db_name_attr = f'{app_arg}_db_name'
                if hasattr(self.args, db_name_attr):
                    db_name_value = getattr(self.args, db_name_attr)
                    if db_name_value:
                        self.setParam(f'{app_id}_db_name', db_name_value)
                        logger.debug(f"Set {app_id}_db_name = {db_name_value}")

                # Database username
                db_username_attr = f'{app_arg}_db_username'
                if hasattr(self.args, db_username_attr):
                    db_username_value = getattr(self.args, db_username_attr)
                    if db_username_value:
                        self.setParam(f'{app_id}_db_username', db_username_value)
                        logger.debug(f"Set {app_id}_db_username = {db_username_value}")

                # Database password
                db_password_attr = f'{app_arg}_db_password'
                if hasattr(self.args, db_password_attr):
                    db_password_value = getattr(self.args, db_password_attr)
                    if db_password_value:
                        self.setParam(f'{app_id}_db_password', db_password_value)
                        logger.debug(f"Set {app_id}_db_password = ********")

                # App-specific advanced configuration files
                # DB2 config files (for manage, iot, facilities)
                if app_id in ['manage', 'iot', 'facilities']:
                    db2_config_attr = f'db2_{app_arg}_config_file'
                    if hasattr(self.args, db2_config_attr):
                        db2_config_value = getattr(self.args, db2_config_attr)
                        if db2_config_value:
                            self.setParam(f'db2_{app_id}_config_file', db2_config_value)
                            logger.debug(f"Set db2_{app_id}_config_file = {db2_config_value}")

                # MAS app workspace spec files
                appws_spec_attr = f'mas_appws_spec_{app_arg}_file'
                if hasattr(self.args, appws_spec_attr):
                    appws_spec_value = getattr(self.args, appws_spec_attr)
                    if appws_spec_value:
                        self.setParam(f'mas_appws_spec_{app_id}_file', appws_spec_value)
                        logger.debug(f"Set mas_appws_spec_{app_id}_file = {appws_spec_value}")

                # MAS app spec files
                app_spec_attr = f'mas_app_spec_{app_arg}_file'
                if hasattr(self.args, app_spec_attr):
                    app_spec_value = getattr(self.args, app_spec_attr)
                    if app_spec_value:
                        self.setParam(f'mas_app_spec_{app_id}_file', app_spec_value)
                        logger.debug(f"Set mas_app_spec_{app_id}_file = {app_spec_value}")

                # JDBC certificate files
                jdbc_cert_attr = f'jdbc_cert_{app_arg}_file'
                if hasattr(self.args, jdbc_cert_attr):
                    jdbc_cert_value = getattr(self.args, jdbc_cert_attr)
                    if jdbc_cert_value:
                        self.setParam(f'jdbc_cert_{app_id}_file', jdbc_cert_value)
                        logger.debug(f"Set jdbc_cert_{app_id}_file = {jdbc_cert_value}")

                # Manage-specific files
                if app_id == 'manage':
                    if hasattr(self.args, 'mas_app_global_secrets_manage_file'):
                        manage_secrets_value = getattr(self.args, 'mas_app_global_secrets_manage_file')
                        if manage_secrets_value:
                            self.setParam('mas_app_global_secrets_manage_file', manage_secrets_value)
                            logger.debug(f"Set mas_app_global_secrets_manage_file = {manage_secrets_value}")

        # Validate required parameters
        logger.info("Validating required parameters...")
        missing_params = []
        for param in requiredParams:
            if not self.getParam(param):
                missing_params.append(param)

        if missing_params:
            error_msg = f"Missing required parameters: {', '.join(missing_params)}"
            logger.error(error_msg)
            self.fatalError(error_msg)

        logger.info("All required parameters validated successfully")

    @logMethodCall
    def chooseInstallFlavour(self) -> None:
        """
        Prompt user to choose between simplified and advanced installation modes.
        """
        self.printH1("Choose Install Mode")
        self.printDescription([
            "There are two flavours of the interactive install to choose from: <u>Simplified</u> and <u>Advanced</u>.",
            "The simplified option will present fewer dialogs, but you lose the ability to configure:",
            " - SMTP email configuration",
            " - LDAP authentication",
            " - Advanced cluster operator options",
            " - Custom storage configurations"
        ])
        self.showAdvancedOptions = self.yesOrNo("Show advanced installation options")
        self.installFlavour = 'advanced' if self.showAdvancedOptions else 'simplified'

    @logMethodCall
    def chooseExecutionMode(self) -> None:
        """
        Prompt user to choose between Tekton and Direct execution modes.
        """
        self.printH1("Choose Execution Mode")
        self.printDescription([
            "There are two execution modes available:",
            " - <u>Tekton Pipelines</u>: Uses OpenShift Pipelines (Tekton) to execute the installation",
            " - <u>Direct Execution</u>: Executes the installation directly from this CLI",
            "",
            "Tekton mode is recommended for production installations as it provides:",
            " - Better visibility and tracking of installation progress",
            " - Ability to resume failed installations",
            " - Centralized logging and monitoring"
        ])
        use_tekton = self.yesOrNo("Use Tekton Pipelines for execution")

        if use_tekton:
            self.useTekton = True
            self.executionMode = 'tekton'
            logger.info("Execution mode set to: Tekton")
        else:
            self.useTekton = False
            self.executionMode = 'direct'
            logger.info("Execution mode set to: Direct")

    @logMethodCall
    def executeInstallation(self) -> None:
        """
        Execute the installation based on the configured execution mode.

        Delegates to the GitOpsInstallExecutor class which handles both
        Tekton pipeline execution and direct mode execution.
        """
        self.printH1("Launch Install")

        logger.info(f"Executing GitOps installation in {self.executionMode} mode")

        try:
            # Create executor and delegate execution to it
            executor = GitOpsInstallExecutor(self)
            success = executor.execute()

            if not success:
                self.fatalError("Installation failed. Check logs for details.")
        except Exception as e:
            logger.error(f"Installation failed: {e}")
            self.fatalError(f"Installation failed: {e}")

    @logMethodCall
    def prepareClusterParams(self) -> dict:
        """
        Prepare parameters for cluster-level configuration.

        Combines common parameters with cluster-specific parameters.
        This method collects all parameters needed for the gitops-cluster
        stage, which configures cluster-level prerequisites like operators,
        catalogs, and cluster-wide resources.

        Returns:
            Dict containing all cluster parameters

        Raises:
            ValueError: If required parameters are missing
        """
        logger.debug("Preparing cluster parameters")

        params = {}

        # Common parameters (used by all stages)
        for param_name in commonParams:
            value = self.getParam(param_name)
            if value is not None:
                params[param_name] = value

        # Cluster-specific parameters
        cluster_param_names = [
            'mas_catalog_version', 'mas_catalog_image', 'ibm_entitlement_key',
            'install_dro', 'dro_namespace', 'dro_install_plan',
            'install_gpu', 'gpu_namespace',
            'install_cert_manager', 'install_nfd',
            'storage_class_rwo', 'storage_class_rwx'
        ]

        for param_name in cluster_param_names:
            value = self.getParam(param_name)
            if value is not None:
                params[param_name] = value

        # Set defaults for optional parameters if not provided
        if 'install_dro' not in params:
            params['install_dro'] = 'false'
        if 'dro_namespace' not in params:
            params['dro_namespace'] = 'ibm-software-central'
        if 'install_gpu' not in params:
            params['install_gpu'] = 'false'
        if 'install_cert_manager' not in params:
            params['install_cert_manager'] = 'true'
        if 'install_nfd' not in params:
            params['install_nfd'] = 'false'
        if 'git_branch' not in params:
            params['git_branch'] = 'main'
        if 'region_id' not in params:
            params['region_id'] = 'default'
        if 'avp_aws_secret_region' not in params:
            params['avp_aws_secret_region'] = 'us-east-1'
        if 'custom_labels' not in params:
            params['custom_labels'] = ''
        if 'github_user' not in params:
            params['github_user'] = ''
        if 'git_commit_msg' not in params:
            params['git_commit_msg'] = 'GitOps cluster configuration'
        if 'slack_channel_id' not in params:
            params['slack_channel_id'] = ''
        if 'custom_sa_namespace' not in params:
            params['custom_sa_namespace'] = ''
        if 'custom_sa_details' not in params:
            params['custom_sa_details'] = ''

        # DNS and domain parameters - must be explicitly set even when blank
        # to override pipeline defaults
        if 'ocp_domain' not in params:
            params['ocp_domain'] = self.getParam('ocp_domain') or ''
        if 'dns_provider' not in params:
            params['dns_provider'] = self.getParam('dns_provider') or ''

        # Validate required parameters
        required = ['account_id', 'cluster_id', 'github_host', 'github_org',
                    'github_repo', 'mas_catalog_version']
        missing = [k for k in required if not params.get(k)]
        if missing:
            raise ValueError(f"Missing required cluster parameters: {', '.join(missing)}")

        logger.debug(f"Prepared {len(params)} cluster parameters")
        return params

    @logMethodCall
    def prepareDepsParams(self) -> dict:
        """
        Prepare parameters for dependencies configuration.

        Combines common parameters with dependency-specific parameters.
        This method collects all parameters needed for the gitops-deps
        stage, which configures off-cluster dependencies like MongoDB,
        Kafka, COS, and EFS.

        Returns:
            Dict containing all dependency parameters

        Raises:
            ValueError: If required parameters are missing
        """
        logger.debug("Preparing dependencies parameters")

        params = {}

        # Common parameters (used by all stages)
        for param_name in commonParams:
            value = self.getParam(param_name)
            if value is not None:
                params[param_name] = value

        # Dependencies-specific parameters
        deps_param_names = [
            'mas_instance_id',
            'vpc_ipv4_cidr',
            'mongo_provider', 'mongodb_action',
            'mongo_yaml_file',
            'aws_docdb_instance_number', 'aws_docdb_engine_version',
            'kafka_provider', 'kafka_version', 'kafka_action',
            'kafkacfg_file_name', 'aws_msk_instance_type',
            'efs_action', 'cloud_provider',
            'ibmcloud_resourcegroup',
            'cos_type', 'cos_resourcegroup', 'cos_action',
            'cos_use_hmac'
        ]

        for param_name in deps_param_names:
            value = self.getParam(param_name)
            if value is not None:
                params[param_name] = value

        # Set defaults for optional parameters if not provided
        if 'mongo_provider' not in params:
            params['mongo_provider'] = 'aws'
        if 'mongodb_action' not in params:
            params['mongodb_action'] = ''
        if 'mongo_yaml_file' not in params:
            params['mongo_yaml_file'] = ''
        if 'aws_docdb_instance_number' not in params:
            params['aws_docdb_instance_number'] = '3'
        if 'aws_docdb_engine_version' not in params:
            params['aws_docdb_engine_version'] = '4.0.0'
        if 'kafka_provider' not in params:
            params['kafka_provider'] = 'aws'
        if 'kafka_version' not in params:
            params['kafka_version'] = '3.3.1'
        if 'kafka_action' not in params:
            params['kafka_action'] = ''
        if 'kafkacfg_file_name' not in params:
            params['kafkacfg_file_name'] = ''
        if 'aws_msk_instance_type' not in params:
            params['aws_msk_instance_type'] = ''
        if 'efs_action' not in params:
            params['efs_action'] = ''
        if 'cloud_provider' not in params:
            params['cloud_provider'] = 'aws'
        if 'ibmcloud_resourcegroup' not in params:
            params['ibmcloud_resourcegroup'] = ''
        if 'cos_type' not in params:
            params['cos_type'] = ''
        if 'cos_resourcegroup' not in params:
            params['cos_resourcegroup'] = ''
        if 'cos_action' not in params:
            params['cos_action'] = ''
        if 'cos_use_hmac' not in params:
            params['cos_use_hmac'] = ''
        if 'vpc_ipv4_cidr' not in params:
            params['vpc_ipv4_cidr'] = ''

        if 'git_branch' not in params:
            params['git_branch'] = 'main'
        if 'region_id' not in params:
            params['region_id'] = 'default'
        if 'avp_aws_secret_region' not in params:
            params['avp_aws_secret_region'] = 'us-east-1'

        # Validate required parameters
        required = ['account_id', 'cluster_id']
        missing = [k for k in required if not params.get(k)]
        if missing:
            raise ValueError(f"Missing required dependency parameters: {', '.join(missing)}")

        logger.debug(f"Prepared {len(params)} dependency parameters")
        return params

    @logMethodCall
    def prepareInstanceParams(self) -> dict:
        """
        Prepare parameters for instance-level configuration.

        Combines common parameters with instance-specific parameters.
        This method collects all parameters needed for the gitops-instance
        stage, which configures MAS instance resources like the Suite,
        workspaces, and instance-level dependencies.

        Returns:
            Dict containing all instance parameters

        Raises:
            ValueError: If required parameters are missing
        """
        logger.debug("Preparing instance parameters")

        params = {}

        # Common parameters (same as cluster)
        for param_name in commonParams:
            value = self.getParam(param_name)
            if value is not None:
                params[param_name] = value

        # Instance-specific parameters
        instance_param_names = [
            'mas_instance_id', 'mas_channel', 'mas_domain',
            'mas_workspace_id', 'mas_workspace_name',
            'operational_mode',
            'sls_channel', 'sls_instance_name',
            'mongo_provider', 'mongo_namespace',
            'smtp_host', 'smtp_port', 'smtp_username', 'smtp_password', 'smtp_from',
            'ldap_url', 'ldap_bind_dn', 'ldap_bind_password',
            'ldap_user_base_dn', 'ldap_group_base_dn',
            'mas_annotations', 'mas_image_tags', 'mas_labels', 'mas_config_dir', 'mas_app_id',
            'sls_license_expiry_date', 'sls_license_app_points', 'sls_license_customer_name', 'sls_license_country',
            'dro_contact_email', 'dro_contact_firstname', 'dro_contact_lastname',
            'smtp_security', 'smtp_authentication', 'smtp_default_sender_email', 'smtp_default_sender_name',
            'smtp_default_recipient_email', 'smtp_default_should_email_passwords', 'smtp_use_sendgrid',
            'smtp_disabled_templates', 'smtp_config_ca_certificate_file',
            'ldap_basedn', 'ldap_userid_map', 'ldap_certificate_file',
            'icr_cp', 'icr_cp_open', 'db2_action',
            'oidc', 'allow_list', 'enhanced_dr', 'extensions', 'additional_vpn', 'maf_enabled',
            'is_non_shared_cluster'
        ]

        for param_name in instance_param_names:
            value = self.getParam(param_name)
            if value is not None:
                params[param_name] = value

        # Set defaults for optional parameters if not provided
        if 'operational_mode' not in params:
            params['operational_mode'] = 'production'
        if 'mongo_provider' not in params:
            params['mongo_provider'] = 'aws'
        if 'git_branch' not in params:
            params['git_branch'] = 'main'
        if 'region_id' not in params:
            params['region_id'] = 'default'
        if 'avp_aws_secret_region' not in params:
            params['avp_aws_secret_region'] = 'us-east-1'
        if 'is_non_shared_cluster' not in params:
            params['is_non_shared_cluster'] = 'false'
        if 'cluster_name' not in params:
            params['cluster_name'] = ''
        if 'secrets_path' not in params:
            params['secrets_path'] = ''
        if 'mas_workspace_name' not in params:
            params['mas_workspace_name'] = ''
        if 'mas_annotations' not in params:
            params['mas_annotations'] = ''
        if 'mas_image_tags' not in params:
            params['mas_image_tags'] = ''
        if 'mas_labels' not in params:
            params['mas_labels'] = ''
        if 'mas_domain' not in params:
            params['mas_domain'] = ''
        if 'mas_config_dir' not in params:
            params['mas_config_dir'] = ''
        if 'mas_app_id' not in params:
            params['mas_app_id'] = ''
        if 'sls_channel' not in params:
            params['sls_channel'] = ''
        if 'sls_license_expiry_date' not in params:
            params['sls_license_expiry_date'] = ''
        if 'sls_license_app_points' not in params:
            params['sls_license_app_points'] = ''
        if 'sls_license_customer_name' not in params:
            params['sls_license_customer_name'] = ''
        if 'sls_license_country' not in params:
            params['sls_license_country'] = ''
        if 'dro_contact_email' not in params:
            params['dro_contact_email'] = ''
        if 'dro_contact_firstname' not in params:
            params['dro_contact_firstname'] = ''
        if 'dro_contact_lastname' not in params:
            params['dro_contact_lastname'] = ''
        if 'smtp_host' not in params:
            params['smtp_host'] = ''
        if 'smtp_port' not in params:
            params['smtp_port'] = ''
        if 'smtp_security' not in params:
            params['smtp_security'] = ''
        if 'smtp_authentication' not in params:
            params['smtp_authentication'] = ''
        if 'smtp_default_sender_email' not in params:
            params['smtp_default_sender_email'] = ''
        if 'smtp_default_sender_name' not in params:
            params['smtp_default_sender_name'] = ''
        if 'smtp_default_recipient_email' not in params:
            params['smtp_default_recipient_email'] = ''
        if 'smtp_default_should_email_passwords' not in params:
            params['smtp_default_should_email_passwords'] = ''
        if 'smtp_use_sendgrid' not in params:
            params['smtp_use_sendgrid'] = ''
        if 'smtp_disabled_templates' not in params:
            params['smtp_disabled_templates'] = ''
        if 'smtp_config_ca_certificate_file' not in params:
            params['smtp_config_ca_certificate_file'] = ''
        if 'ldap_url' not in params:
            params['ldap_url'] = ''
        if 'ldap_basedn' not in params:
            params['ldap_basedn'] = ''
        if 'ldap_userid_map' not in params:
            params['ldap_userid_map'] = ''
        if 'ldap_certificate_file' not in params:
            params['ldap_certificate_file'] = ''
        if 'icr_cp' not in params:
            params['icr_cp'] = ''
        if 'icr_cp_open' not in params:
            params['icr_cp_open'] = ''
        if 'db2_action' not in params:
            params['db2_action'] = ''
        if 'oidc' not in params:
            params['oidc'] = ''
        if 'allow_list' not in params:
            params['allow_list'] = ''
        if 'enhanced_dr' not in params:
            params['enhanced_dr'] = ''
        if 'extensions' not in params:
            params['extensions'] = ''
        if 'additional_vpn' not in params:
            params['additional_vpn'] = ''
        if 'maf_enabled' not in params:
            params['maf_enabled'] = ''
        if 'github_user' not in params:
            params['github_user'] = ''
        if 'git_commit_msg' not in params:
            params['git_commit_msg'] = 'GitOps instance configuration'

        # Validate required parameters
        required = ['account_id', 'cluster_id', 'mas_instance_id',
                    'mas_channel', 'mas_workspace_id']
        missing = [k for k in required if not params.get(k)]
        if missing:
            raise ValueError(f"Missing required instance parameters: {', '.join(missing)}")

        logger.debug(f"Prepared {len(params)} instance parameters")
        return params

    @logMethodCall
    def prepareAppsParams(self) -> dict:
        """
        Prepare parameters for applications configuration.

        Combines common parameters with app-specific parameters.
        This method collects all parameters needed for the gitops-apps
        stage, which configures MAS applications and their dependencies.

        Returns:
            Dict containing all apps parameters

        Raises:
            ValueError: If required parameters are missing
        """
        logger.debug("Preparing apps parameters")

        params = {}

        # Common parameters (same as cluster)
        for param_name in commonParams:
            value = self.getParam(param_name)
            if value is not None:
                params[param_name] = value

        # Apps-specific parameters
        mas_app_ids = self.getParam('mas_app_ids')
        if mas_app_ids:
            params['mas_app_ids'] = mas_app_ids

            # Parse app IDs and collect per-app parameters
            app_ids = [app.strip() for app in mas_app_ids.split(',') if app.strip()]

            # Validate app IDs
            valid_apps = ['manage', 'iot', 'monitor', 'predict', 'assist', 'visualinspection', 'health', 'optimizer', 'safety', 'facilities']
            for app_id in app_ids:
                if app_id not in valid_apps:
                    raise ValueError(f"Invalid application ID: {app_id}. Valid apps: {', '.join(valid_apps)}")

            for app_id in app_ids:
                # Per-app parameters
                app_param_names = [
                    f'{app_id}_channel',
                    f'{app_id}_db_action',
                    f'{app_id}_db_type',
                    f'{app_id}_db_host',
                    f'{app_id}_db_port',
                    f'{app_id}_db_name',
                    f'{app_id}_db_username',
                    f'{app_id}_db_password',
                ]

                for param_name in app_param_names:
                    value = self.getParam(param_name)
                    if value is not None:
                        params[param_name] = value

        # Set defaults for all required parameters
        if 'git_branch' not in params:
            params['git_branch'] = 'main'
        if 'region_id' not in params:
            params['region_id'] = 'default'
        if 'avp_aws_secret_region' not in params:
            params['avp_aws_secret_region'] = 'us-east-1'
        if 'cluster_name' not in params:
            params['cluster_name'] = ''
        if 'cluster_url' not in params:
            params['cluster_url'] = ''
        if 'image_pull_policy' not in params:
            params['image_pull_policy'] = 'IfNotPresent'
        if 'secrets_path' not in params:
            params['secrets_path'] = ''
        if 'mas_config_dir' not in params:
            params['mas_config_dir'] = ''
        if 'icr_cp' not in params:
            params['icr_cp'] = ''
        if 'icr_cp_open' not in params:
            params['icr_cp_open'] = ''
        if 'github_user' not in params:
            params['github_user'] = ''
        if 'git_commit_msg' not in params:
            params['git_commit_msg'] = 'GitOps apps configuration'

        # JDBC parameters for each app type
        for app_type in ['iot', 'manage', 'facilities']:
            if f'jdbc_type_{app_type}' not in params:
                params[f'jdbc_type_{app_type}'] = ''
            if f'jdbc_connection_url_additional_params_{app_type}' not in params:
                params[f'jdbc_connection_url_additional_params_{app_type}'] = ''
            if f'jdbc_instance_name_{app_type}' not in params:
                params[f'jdbc_instance_name_{app_type}'] = ''

        # DB2 parameters for each app type
        for app_type in ['iot', 'manage', 'facilities']:
            if f'db2_meta_storage_class_{app_type}' not in params:
                params[f'db2_meta_storage_class_{app_type}'] = ''
            if f'db2_temp_storage_class_{app_type}' not in params:
                params[f'db2_temp_storage_class_{app_type}'] = ''
            if f'db2_logs_storage_class_{app_type}' not in params:
                params[f'db2_logs_storage_class_{app_type}'] = ''
            if f'db2_audit_logs_storage_class_{app_type}' not in params:
                params[f'db2_audit_logs_storage_class_{app_type}'] = ''
            if f'db2_backup_storage_class_{app_type}' not in params:
                params[f'db2_backup_storage_class_{app_type}'] = ''
            if f'db2_archivelogs_storage_class_{app_type}' not in params:
                params[f'db2_archivelogs_storage_class_{app_type}'] = ''
            if f'db2_version_{app_type}' not in params:
                params[f'db2_version_{app_type}'] = ''
            if f'db2_action_{app_type}' not in params:
                params[f'db2_action_{app_type}'] = ''
            if f'db2_temp_storage_accessmode_{app_type}' not in params:
                params[f'db2_temp_storage_accessmode_{app_type}'] = ''

        # Storage classes
        if 'default_block_storage_class' not in params:
            params['default_block_storage_class'] = ''
        if 'default_file_storage_class' not in params:
            params['default_file_storage_class'] = ''

        # CP4D parameters
        if 'cpd_product_version' not in params:
            params['cpd_product_version'] = ''
        if 'cpd_primary_storage_class' not in params:
            params['cpd_primary_storage_class'] = ''
        if 'cpd_metadata_storage_class' not in params:
            params['cpd_metadata_storage_class'] = ''
        if 'cp4d_action' not in params:
            params['cp4d_action'] = ''
        if 'cpd_service_block_storage_class' not in params:
            params['cpd_service_block_storage_class'] = ''
        if 'cpd_service_storage_class' not in params:
            params['cpd_service_storage_class'] = ''
        if 'cp4d_wsl_action' not in params:
            params['cp4d_wsl_action'] = ''
        if 'cp4d_watson_machine_learning_action' not in params:
            params['cp4d_watson_machine_learning_action'] = ''
        if 'cp4d_analytics_engine_action' not in params:
            params['cp4d_analytics_engine_action'] = ''
        if 'cp4d_spss_modeler_action' not in params:
            params['cp4d_spss_modeler_action'] = ''

        # MAS App Spec YAML for each app
        for app_type in ['iot', 'manage', 'monitor', 'visualinspection', 'assist', 'optimizer', 'predict', 'facilities']:
            if f'mas_app_spec_yaml_{app_type}' not in params:
                params[f'mas_app_spec_yaml_{app_type}'] = ''
            if f'mas_appws_spec_yaml_{app_type}' not in params:
                params[f'mas_appws_spec_yaml_{app_type}'] = ''

        # Validate required parameters
        required = ['account_id', 'cluster_id']
        missing = [k for k in required if not params.get(k)]
        if missing:
            raise ValueError(f"Missing required apps parameters: {', '.join(missing)}")

        logger.debug(f"Prepared {len(params)} apps parameters")
        return params

    @logMethodCall
    def prepareSecureProperties(self) -> dict:
        """
        Prepare secure properties for GitOps installation.

        This method collects all sensitive parameters (passwords, tokens, access keys)
        that should be stored in the secure-properties secret for use by Tekton pipelines.

        Returns:
            Dict containing secure properties with their secret keys
        """
        logger.debug("Preparing secure properties")

        secure_props = {}

        # Artifactory credentials
        artifactory_token = self.getParam('artifactory_token')
        if artifactory_token:
            secure_props['ARTIFACTORY_TOKEN'] = artifactory_token
            logger.debug("Added ARTIFACTORY_TOKEN to secure properties")

        artifactory_username = self.getParam('artifactory_username')
        if artifactory_username:
            secure_props['ARTIFACTORY_USERNAME'] = artifactory_username
            logger.debug("Added ARTIFACTORY_USERNAME to secure properties")

        # CD Tekton Pipeline API Key
        cd_tekton_pipeline_apikey = self.getParam('cd_tekton_pipeline_apikey')
        if cd_tekton_pipeline_apikey:
            secure_props['CD_TEKTON_PIPELINE_APIKEY'] = cd_tekton_pipeline_apikey
            logger.debug("Added CD_TEKTON_PIPELINE_APIKEY to secure properties")

        # CIS API Key
        cis_apikey = self.getParam('cis_apikey')
        if cis_apikey:
            secure_props['CIS_APIKEY'] = cis_apikey
            logger.debug("Added CIS_APIKEY to secure properties")

        # CloudWatch AWS credentials
        cloudwatch_aws_access_key_id = self.getParam('cloudwatch_aws_access_key_id')
        if cloudwatch_aws_access_key_id:
            secure_props['CLOUDWATCH_AWS_ACCESS_KEY_ID'] = cloudwatch_aws_access_key_id
            logger.debug("Added CLOUDWATCH_AWS_ACCESS_KEY_ID to secure properties")

        cloudwatch_aws_secret_access_key = self.getParam('cloudwatch_aws_secret_access_key')
        if cloudwatch_aws_secret_access_key:
            secure_props['CLOUDWATCH_AWS_SECRET_ACCESS_KEY'] = cloudwatch_aws_secret_access_key
            logger.debug("Added CLOUDWATCH_AWS_SECRET_ACCESS_KEY to secure properties")

        # DevOps MongoDB URI
        devops_mongo_uri = self.getParam('devops_mongo_uri')
        if devops_mongo_uri:
            secure_props['DEVOPS_MONGO_URI'] = devops_mongo_uri
            logger.debug("Added DEVOPS_MONGO_URI to secure properties")

        # DRO CMM Auth API Key
        dro_cmm_auth_apikey = self.getParam('dro_cmm_auth_apikey')
        if dro_cmm_auth_apikey:
            secure_props['DRO_CMM_AUTH_APIKEY'] = dro_cmm_auth_apikey
            logger.debug("Added DRO_CMM_AUTH_APIKEY to secure properties")

        # Falcon credentials
        falcon_client_id = self.getParam('falcon_client_id')
        if falcon_client_id:
            secure_props['FALCON_CLIENT_ID'] = falcon_client_id
            logger.debug("Added FALCON_CLIENT_ID to secure properties")

        falcon_client_secret = self.getParam('falcon_client_secret')
        if falcon_client_secret:
            secure_props['FALCON_CLIENT_SECRET'] = falcon_client_secret
            logger.debug("Added FALCON_CLIENT_SECRET to secure properties")

        # GitHub PAT token for GitOps repository access
        gitops_repo_token = self.getParam('gitops_repo_token_secret')
        if gitops_repo_token:
            secure_props['GITHUB_PAT'] = gitops_repo_token
            logger.debug("Added GITHUB_PAT to secure properties")

        # IBM Cloud API Key
        ibmcloud_api_key = self.getParam('ibmcloud_api_key')
        if ibmcloud_api_key:
            secure_props['IBMCLOUD_API_KEY'] = ibmcloud_api_key
            logger.debug("Added IBMCLOUD_API_KEY to secure properties")

        # ICD Auth Key
        icd_auth_key = self.getParam('icd_auth_key')
        if icd_auth_key:
            secure_props['ICD_AUTH_KEY'] = icd_auth_key
            logger.debug("Added ICD_AUTH_KEY to secure properties")

        # IBM Container Registry credentials
        # ICR_PASSWORD is set from ibm_entitlement_key, ICR_USERNAME is hardcoded to 'cp'
        ibm_entitlement_key = self.getParam('ibm_entitlement_key')
        if ibm_entitlement_key:
            secure_props['ICR_PASSWORD'] = ibm_entitlement_key
            secure_props['ICR_USERNAME'] = 'cp'
            logger.debug("Added ICR_PASSWORD (from ibm_entitlement_key) to secure properties")
            logger.debug("Added ICR_USERNAME (hardcoded to 'cp') to secure properties")

        # Instana Key
        instana_key = self.getParam('instana_key')
        if instana_key:
            secure_props['INSTANA_KEY'] = instana_key
            logger.debug("Added INSTANA_KEY to secure properties")

        # ISV credentials
        isv_client_id = self.getParam('isv_client_id')
        if isv_client_id:
            secure_props['ISV_CLIENT_ID'] = isv_client_id
            logger.debug("Added ISV_CLIENT_ID to secure properties")

        isv_client_secret = self.getParam('isv_client_secret')
        if isv_client_secret:
            secure_props['ISV_CLIENT_SECRET'] = isv_client_secret
            logger.debug("Added ISV_CLIENT_SECRET to secure properties")

        # MAS Segment Key
        mas_segment_key = self.getParam('mas_segment_key')
        if mas_segment_key:
            secure_props['MAS_SEGMENT_KEY'] = mas_segment_key
            logger.debug("Added MAS_SEGMENT_KEY to secure properties")

        # MongoDB credentials
        mongo_username = self.getParam('mongo_username')
        if mongo_username:
            secure_props['MONGO_USERNAME'] = mongo_username
            logger.debug("Added MONGO_USERNAME to secure properties")

        mongo_password = self.getParam('mongo_password')
        if mongo_password:
            secure_props['MONGO_PASSWORD'] = mongo_password
            logger.debug("Added MONGO_PASSWORD to secure properties")

        # OCM API Key
        ocm_api_key = self.getParam('ocm_api_key')
        if ocm_api_key:
            secure_props['OCM_API_KEY'] = ocm_api_key
            logger.debug("Added OCM_API_KEY to secure properties")

        # SendGrid API Key
        sendgrid_api_key = self.getParam('sendgrid_api_key')
        if sendgrid_api_key:
            secure_props['SENDGRID_API_KEY'] = sendgrid_api_key
            logger.debug("Added SENDGRID_API_KEY to secure properties")

        # Secrets Manager AWS credentials
        sm_aws_access_key_id = self.getParam('sm_aws_access_key_id')
        if sm_aws_access_key_id:
            secure_props['SM_AWS_ACCESS_KEY_ID'] = sm_aws_access_key_id
            logger.debug("Added SM_AWS_ACCESS_KEY_ID to secure properties")

        sm_aws_secret_access_key = self.getParam('sm_aws_secret_access_key')
        if sm_aws_secret_access_key:
            secure_props['SM_AWS_SECRET_ACCESS_KEY'] = sm_aws_secret_access_key
            logger.debug("Added SM_AWS_SECRET_ACCESS_KEY to secure properties")

        # IBM Entitlement Key (kept for backward compatibility)
        # Note: ibm_entitlement_key is also used to set ICR_PASSWORD and ICR_USERNAME above
        ibm_entitlement_key_compat = self.getParam('ibm_entitlement_key')
        if ibm_entitlement_key_compat:
            secure_props['IBM_ENTITLEMENT_KEY'] = ibm_entitlement_key_compat
            logger.debug("Added IBM_ENTITLEMENT_KEY to secure properties")

        # SMTP password
        smtp_password = self.getParam('smtp_password')
        if smtp_password:
            secure_props['SMTP_PASSWORD'] = smtp_password
            logger.debug("Added SMTP_PASSWORD to secure properties")

        # LDAP bind password
        ldap_bind_password = self.getParam('ldap_bind_password')
        if ldap_bind_password:
            secure_props['LDAP_BIND_PASSWORD'] = ldap_bind_password
            logger.debug("Added LDAP_BIND_PASSWORD to secure properties")

        # Per-app database passwords
        mas_app_ids = self.getParam('mas_app_ids')
        if mas_app_ids:
            app_ids = [app.strip() for app in mas_app_ids.split(',') if app.strip()]
            for app_id in app_ids:
                db_password_param = f'{app_id}_db_password'
                db_password = self.getParam(db_password_param)
                if db_password:
                    # Use uppercase with underscores for secret key
                    secret_key = f'{app_id.upper().replace("-", "_")}_DB_PASSWORD'
                    secure_props[secret_key] = db_password
                    logger.debug(f"Added {secret_key} to secure properties")

        logger.debug(f"Prepared {len(secure_props)} secure properties")
        return secure_props

    @logMethodCall
    def prepareGitOpsConfigFiles(self) -> dict:
        """
        Prepare GitOps configuration files for pipeline-gitops-configs secret.

        Reads file contents from paths specified in parameters and encodes them
        in base64 for inclusion in Kubernetes secrets.

        Returns:
            Dict containing base64-encoded file contents with their secret keys
        """
        import base64
        import os

        logger.debug("Preparing GitOps configuration files")

        config_files = {}

        # Map of parameter names to secret data keys
        file_mappings = {
            'dro_ca_certificate_file': 'dro_ca.crt',
            'mas_manual_certs_yaml': 'manual_certs.yaml',
            'mas_pod_template_file': 'mas_pod_template.yaml',
            'mas_bascfg_pod_template_file': 'mas_bascfg_pod_template.yaml',
            'mas_appcfg_pod_template_file': 'mas_appcfg_pod_template.yaml',
            'mas_slscfg_pod_template_file': 'mas_slscfg_pod_template.yaml',
            'mas_smtpcfg_pod_template_file': 'mas_smtpcfg_pod_template.yaml',
            'suite_spec_additional_properties_yaml': 'suite_spec_additional_properties.yaml',
            'suite_spec_settings_additional_properties_yaml': 'suite_spec_settings_additional_properties.yaml',
            'smtp_config_ca_certificate_file': 'smtp_config_ca.crt',
            'mongo_yaml_file': 'mongo.yaml'
        }

        for param_name, secret_key in file_mappings.items():
            file_path = self.getParam(param_name)
            if file_path and os.path.exists(file_path):
                try:
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                        encoded_content = base64.b64encode(file_content).decode('utf-8')
                        config_files[secret_key] = encoded_content
                        logger.debug(f"Added {secret_key} to GitOps config files")
                except Exception as e:
                    logger.warning(f"Failed to read file {file_path}: {e}")

        logger.debug(f"Prepared {len(config_files)} GitOps configuration files")
        return config_files

    @logMethodCall
    def prepareAdditionalConfigFiles(self) -> dict:
        """
        Prepare additional configuration files for pipeline-additional-configs secret.

        Reads file contents from paths specified in parameters and encodes them
        in base64 for inclusion in Kubernetes secrets.

        Returns:
            Dict containing base64-encoded file contents with their secret keys
        """
        import base64
        import os

        logger.debug("Preparing additional configuration files")

        additional_files = {}

        # Map of parameter names to secret data keys
        file_mappings = {
            'ldap_certificate_file': 'ldap_masdeps1_cert.pem',
            'dro_ca_certificate_file': 'dro_ca.crt',
            'mas_pod_template_file': 'mas_pod_template.yaml',
            'mas_bascfg_pod_template_file': 'mas_bascfg_pod_template.yaml',
            'mas_slscfg_pod_template_file': 'mas_slscfg_pod_template.yaml',
            'mas_smtpcfg_pod_template_file': 'mas_smtpcfg_pod_template.yaml',
            'mas_appcfg_pod_template_file': 'mas_appcfg_pod_template.yaml'
        }

        for param_name, secret_key in file_mappings.items():
            file_path = self.getParam(param_name)
            if file_path and os.path.exists(file_path):
                try:
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                        encoded_content = base64.b64encode(file_content).decode('utf-8')
                        additional_files[secret_key] = encoded_content
                        logger.debug(f"Added {secret_key} to additional config files")
                except Exception as e:
                    logger.warning(f"Failed to read file {file_path}: {e}")

        logger.debug(f"Prepared {len(additional_files)} additional configuration files")
        return additional_files

    @logMethodCall
    def prepareSLSEntitlementFile(self) -> dict:
        """
        Prepare SLS entitlement file for pipeline-sls-entitlement secret.

        Reads the entitlement.lic file content and encodes it in base64
        for inclusion in Kubernetes secrets.

        Returns:
            Dict containing base64-encoded entitlement file content
        """
        import base64
        import os

        logger.debug("Preparing SLS entitlement file")

        entitlement_data = {}

        file_path = self.getParam('sls_entitlement_file')
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                    encoded_content = base64.b64encode(file_content).decode('utf-8')
                    entitlement_data['entitlement.lic'] = encoded_content
                    logger.debug("Added entitlement.lic to SLS entitlement data")
            except Exception as e:
                logger.error(f"Failed to read SLS entitlement file {file_path}: {e}")
                raise

        return entitlement_data

    @logMethodCall
    def prepareAppSpecificConfigFiles(self) -> dict:
        """
        Prepare app-specific configuration files for pipeline-gitops-configs secret (apps pipeline).

        Reads file contents from paths specified in parameters and encodes them
        in base64 for inclusion in Kubernetes secrets. This includes:
        - DB2 configuration files for manage, iot, facilities
        - MAS app workspace spec files
        - MAS app spec files
        - JDBC certificate files
        - Manage-specific global secrets file

        Returns:
            Dict containing base64-encoded file contents with their secret keys
        """
        import base64
        import os

        logger.debug("Preparing app-specific configuration files")

        app_config_files = {}

        # Get list of apps being installed
        mas_app_ids = self.getParam('mas_app_ids')
        if not mas_app_ids:
            logger.debug("No apps configured, skipping app-specific config files")
            return app_config_files

        app_ids = [app.strip() for app in mas_app_ids.split(',') if app.strip()]

        for app_id in app_ids:
            # DB2 configuration files (for manage, iot, facilities)
            if app_id in ['manage', 'iot', 'facilities']:
                file_path = self.getParam(f'db2_{app_id}_config_file')
                if file_path and os.path.exists(file_path):
                    try:
                        with open(file_path, 'rb') as f:
                            file_content = f.read()
                            encoded_content = base64.b64encode(file_content).decode('utf-8')
                            secret_key = f'db2_{app_id}.yaml'
                            app_config_files[secret_key] = encoded_content
                            logger.debug(f"Added {secret_key} to app-specific config files")
                    except Exception as e:
                        logger.warning(f"Failed to read DB2 config file {file_path}: {e}")

            # MAS app workspace spec files
            file_path = self.getParam(f'mas_appws_spec_{app_id}_file')
            if file_path and os.path.exists(file_path):
                try:
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                        encoded_content = base64.b64encode(file_content).decode('utf-8')
                        secret_key = f'mas_appws_spec_yaml_{app_id}.yaml'
                        app_config_files[secret_key] = encoded_content
                        logger.debug(f"Added {secret_key} to app-specific config files")
                except Exception as e:
                    logger.warning(f"Failed to read app workspace spec file {file_path}: {e}")

            # MAS app spec files
            file_path = self.getParam(f'mas_app_spec_{app_id}_file')
            if file_path and os.path.exists(file_path):
                try:
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                        encoded_content = base64.b64encode(file_content).decode('utf-8')
                        secret_key = f'mas_app_spec_yaml_{app_id}.yaml'
                        app_config_files[secret_key] = encoded_content
                        logger.debug(f"Added {secret_key} to app-specific config files")
                except Exception as e:
                    logger.warning(f"Failed to read app spec file {file_path}: {e}")

            # JDBC certificate files
            file_path = self.getParam(f'jdbc_cert_{app_id}_file')
            if file_path and os.path.exists(file_path):
                try:
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                        encoded_content = base64.b64encode(file_content).decode('utf-8')
                        secret_key = f'jdbc_cert_{app_id}.crt'
                        app_config_files[secret_key] = encoded_content
                        logger.debug(f"Added {secret_key} to app-specific config files")
                except Exception as e:
                    logger.warning(f"Failed to read JDBC certificate file {file_path}: {e}")

        # Manage-specific global secrets file
        if 'manage' in app_ids:
            file_path = self.getParam('mas_app_global_secrets_manage_file')
            if file_path and os.path.exists(file_path):
                try:
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                        encoded_content = base64.b64encode(file_content).decode('utf-8')
                        secret_key = 'mas_app_global_secrets_manage.yaml'
                        app_config_files[secret_key] = encoded_content
                        logger.debug(f"Added {secret_key} to app-specific config files")
                except Exception as e:
                    logger.warning(f"Failed to read manage global secrets file {file_path}: {e}")

        logger.debug(f"Prepared {len(app_config_files)} app-specific configuration files")
        return app_config_files
