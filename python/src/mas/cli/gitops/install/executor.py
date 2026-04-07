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
import subprocess
import os
import requests
from typing import Dict, Any
from halo import Halo
from prompt_toolkit import print_formatted_text, HTML


logger = logging.getLogger(__name__)


class GitOpsInstallExecutor():
    """
    Executor class for performing GitOps installation operations.

    This class handles the execution of the GitOps installation process
    by calling bash CLI functions directly.
    """

    def __init__(self, params: Dict[str, Any], spinner: str = 'dots',
                 success_icon: str = '✔', failure_icon: str = '✖'):
        """
        Initialize the GitOps install executor.

        Args:
            params: Dictionary of all configuration parameters
            spinner: Spinner style for Halo (default: 'dots')
            success_icon: Icon to display on success (default: '✔')
            failure_icon: Icon to display on failure (default: '✖')
        """
        self.params = params
        self.spinner = spinner
        self.success_icon = success_icon
        self.failure_icon = failure_icon
        logger.debug("GitOpsInstallExecutor initialized")

    def execute(self) -> bool:
        """
        Execute GitOps installation by calling bash gitops functions directly.

        This method executes the GitOps installation by calling the bash CLI functions:
        1. gitops-deps (optional, for off-cluster dependencies)
        2. gitops-cluster (cluster-level configuration)
        3. gitops-suite (MAS instance installation)
        4. gitops-suite-app-install (for each application)

        Returns:
            bool: True if all functions completed successfully
        """
        logger.info("Executing GitOps installation")

        try:
            print_formatted_text(HTML("\n<b><u>Launch GitOps Install</u></b>\n"))

            instanceId = self.params.get('mas_instance_id')
            if not instanceId:
                logger.error("Instance ID is required for GitOps execution")
                return False

            # Step 1: Execute gitops-deps if needed (optional)
            # Execute individual dependency commands based on what's configured
            # Execute dependency commands if configured
            # These parameters contain action values like 'install', 'byo', etc.
            if self.params.get('mongodb_action') is not None:
                with Halo(text='Executing gitops-mongo', spinner=self.spinner) as h:
                    if self._executeGitOpsCommand('gitops-mongo', self.params):
                        h.stop_and_persist(symbol=self.success_icon, text="gitops-mongo completed successfully")
                    else:
                        h.stop_and_persist(symbol=self.failure_icon, text="gitops-mongo failed")
                        return False

            if self.params.get('kafka_action') is not None:
                with Halo(text='Executing gitops-kafka', spinner=self.spinner) as h:
                    if self._executeGitOpsCommand('gitops-kafka', self.params):
                        h.stop_and_persist(symbol=self.success_icon, text="gitops-kafka completed successfully")
                    else:
                        h.stop_and_persist(symbol=self.failure_icon, text="gitops-kafka failed")
                        return False

            if self.params.get('cos_action') is not None:
                with Halo(text='Executing gitops-cos', spinner=self.spinner) as h:
                    if self._executeGitOpsCommand('gitops-cos', self.params):
                        h.stop_and_persist(symbol=self.success_icon, text="gitops-cos completed successfully")
                    else:
                        h.stop_and_persist(symbol=self.failure_icon, text="gitops-cos failed")
                        return False

            if self.params.get('efs_action') is not None:
                with Halo(text='Executing gitops-efs', spinner=self.spinner) as h:
                    if self._executeGitOpsCommand('gitops-efs', self.params):
                        h.stop_and_persist(symbol=self.success_icon, text="gitops-efs completed successfully")
                    else:
                        h.stop_and_persist(symbol=self.failure_icon, text="gitops-efs failed")
                        return False

            # Step 2: Execute gitops-cluster
            with Halo(text='Executing gitops-cluster', spinner=self.spinner) as h:
                if self._executeGitOpsCommand('gitops-cluster', self.params):
                    h.stop_and_persist(symbol=self.success_icon, text="gitops-cluster completed successfully")
                else:
                    h.stop_and_persist(symbol=self.failure_icon, text="gitops-cluster failed")
                    return False

            # Step 3: Execute gitops-suite (instance)
            with Halo(text='Executing gitops-suite', spinner=self.spinner) as h:
                if self._executeGitOpsCommand('gitops-suite', self.params):
                    h.stop_and_persist(symbol=self.success_icon, text="gitops-suite completed successfully")
                else:
                    h.stop_and_persist(symbol=self.failure_icon, text="gitops-suite failed")
                    return False

            # Step 4: Execute gitops-suite-workspace
            with Halo(text='Executing gitops-suite-workspace', spinner=self.spinner) as h:
                if self._executeGitOpsCommand('gitops-suite-workspace', self.params):
                    h.stop_and_persist(symbol=self.success_icon, text="gitops-suite-workspace completed successfully")
                else:
                    h.stop_and_persist(symbol=self.failure_icon, text="gitops-suite-workspace failed")
                    return False

            # Step 5: Execute gitops-suite-app-install for each application
            apps_to_install = []
            if self.params.get('mas_app_id_iot'):
                apps_to_install.append('iot')
            if self.params.get('mas_app_id_monitor'):
                apps_to_install.append('monitor')
            if self.params.get('mas_app_id_manage'):
                apps_to_install.append('manage')
            if self.params.get('mas_app_id_predict'):
                apps_to_install.append('predict')
            if self.params.get('mas_app_id_assist'):
                apps_to_install.append('assist')
            if self.params.get('mas_app_id_optimizer'):
                apps_to_install.append('optimizer')
            if self.params.get('mas_app_id_visualinspection'):
                apps_to_install.append('visualinspection')
            if self.params.get('mas_app_id_facilities'):
                apps_to_install.append('facilities')

            for app_id in apps_to_install:
                with Halo(text=f'Executing gitops-suite-app-install for {app_id}', spinner=self.spinner) as h:
                    app_params = self._prepare_app_params(app_id, 'install')

                    if self._executeGitOpsCommand('gitops-suite-app-install', app_params):
                        h.stop_and_persist(symbol=self.success_icon, text=f"gitops-suite-app-install for {app_id} completed successfully")
                    else:
                        h.stop_and_persist(symbol=self.failure_icon, text=f"gitops-suite-app-install for {app_id} failed")
                        return False

            # Step 6: Execute gitops-suite-app-config for each application that needs configuration
            for app_id in apps_to_install:
                with Halo(text=f'Executing gitops-suite-app-config for {app_id}', spinner=self.spinner) as h:
                    app_params = self._prepare_app_params(app_id, 'config')

                    if self._executeGitOpsCommand('gitops-suite-app-config', app_params):
                        h.stop_and_persist(symbol=self.success_icon, text=f"gitops-suite-app-config for {app_id} completed successfully")
                    else:
                        h.stop_and_persist(symbol=self.failure_icon, text=f"gitops-suite-app-config for {app_id} failed")
                        return False

            print_formatted_text(HTML(f"\n<Green>GitOps installation completed successfully for {instanceId}</Green>\n"))
            logger.info("All GitOps commands executed successfully")
            return True

        except Exception as e:
            logger.error(f"Error executing GitOps installation: {e}", exc_info=True)
            return False

    def _prepare_app_params(self, app_id: str, operation: str) -> Dict[str, Any]:
        """
        Prepare app-specific parameters by transforming per-app params to generic ones.

        Transforms parameters like --mas-app-channel-manage to --mas-app-channel
        for the specific app being processed.

        Args:
            app_id: The application ID (e.g., 'manage', 'iot', 'visualinspection')
            operation: The operation type ('install' or 'config')

        Returns:
            Dictionary of parameters with app-specific values mapped to generic keys
        """
        app_params = self.params.copy()
        app_params['mas_app_id'] = app_id

        app_upper = app_id.upper().replace('-', '_')

        # Map per-app installation parameters to generic ones
        if operation == 'install':
            param_mappings = {
                f'mas_app_channel_{app_upper}': 'mas_app_channel',
                f'mas_app_catalog_source_{app_upper}': 'mas_app_catalog_source',
                f'mas_app_api_version_{app_upper}': 'mas_app_api_version',
                f'mas_app_kind_{app_upper}': 'mas_app_kind',
                f'mas_app_spec_yaml_{app_upper}': 'mas_app_spec_yaml',
            }

            # Add DB2/JDBC parameters for apps that need them
            if app_id in ['manage', 'iot', 'facilities']:
                db2_mappings = {
                    f'db2_channel_{app_upper}': 'db2_channel',
                    f'db2_version_{app_upper}': 'db2_version',
                    f'db2_meta_storage_class_{app_upper}': 'db2_meta_storage_class',
                    f'db2_data_storage_class_{app_upper}': 'db2_data_storage_class',
                    f'db2_logs_storage_class_{app_upper}': 'db2_logs_storage_class',
                    f'db2_backup_storage_class_{app_upper}': 'db2_backup_storage_class',
                    f'db2_instance_registry_yaml_{app_upper}': 'db2_instance_registry_yaml',
                    f'db2_instance_dbm_config_yaml_{app_upper}': 'db2_instance_dbm_config_yaml',
                    f'db2_database_db_config_yaml_{app_upper}': 'db2_database_db_config_yaml',
                    f'jdbc_instance_name_{app_upper}': 'jdbc_instance_name',
                }
                param_mappings.update(db2_mappings)

        # Map per-app workspace configuration parameters to generic ones
        elif operation == 'config':
            param_mappings = {
                f'mas_appws_api_version_{app_upper}': 'mas_appws_api_version',
                f'mas_appws_kind_{app_upper}': 'mas_appws_kind',
                f'mas_appws_spec_yaml_{app_upper}': 'mas_appws_spec_yaml',
            }

            # Add DB2/JDBC parameters for apps that need them (for config operation)
            if app_id in ['manage', 'iot', 'facilities']:
                db2_mappings = {
                    f'db2_channel_{app_upper}': 'db2_channel',
                    f'db2_version_{app_upper}': 'db2_version',
                    f'db2_meta_storage_class_{app_upper}': 'db2_meta_storage_class',
                    f'db2_data_storage_class_{app_upper}': 'db2_data_storage_class',
                    f'db2_logs_storage_class_{app_upper}': 'db2_logs_storage_class',
                    f'db2_backup_storage_class_{app_upper}': 'db2_backup_storage_class',
                    f'db2_instance_registry_yaml_{app_upper}': 'db2_instance_registry_yaml',
                    f'db2_instance_dbm_config_yaml_{app_upper}': 'db2_instance_dbm_config_yaml',
                    f'db2_database_db_config_yaml_{app_upper}': 'db2_database_db_config_yaml',
                    f'jdbc_instance_name_{app_upper}': 'jdbc_instance_name',
                }
                param_mappings.update(db2_mappings)
        else:
            param_mappings = {}

        # Apply the mappings
        for app_specific_key, generic_key in param_mappings.items():
            if app_specific_key in self.params and self.params[app_specific_key] is not None:
                app_params[generic_key] = self.params[app_specific_key]
                logger.debug(f"Mapped {app_specific_key} to {generic_key} for app {app_id}")

        return app_params

    def _executeGitOpsCommand(self, command: str, params: Dict[str, Any]) -> bool:
        """
        Execute a gitops bash command with the provided parameters.

        Args:
            command: The gitops command to execute (e.g., 'gitops-cluster', 'gitops-suite')
            params: Dictionary of parameters to pass as environment variables and command-line args

        Returns:
            bool: True if command executed successfully, False otherwise
        """
        try:
            # Build environment variables from params
            env = os.environ.copy()

            # Set git config for subprocess operations
            # Try to fetch user info from GitHub PAT if available, otherwise use defaults
            git_author_name = 'MAS Automation'
            git_author_email = 'mas.automation@ibm.com'

            github_pat = params.get('gitops_repo_token_secret') or env.get('GITHUB_PAT')
            github_host = params.get('github_host', 'github.com')

            if github_pat:
                try:
                    # Determine API URL based on GitHub host
                    if github_host and github_host != 'github.com':
                        # GitHub Enterprise
                        api_url = f"https://{github_host}/api/v3/user"
                    else:
                        # GitHub.com
                        api_url = "https://api.github.com/user"

                    headers = {
                        'Authorization': f'token {github_pat}',
                        'Accept': 'application/vnd.github.v3+json'
                    }

                    response = requests.get(api_url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        user_data = response.json()
                        git_author_name = user_data.get('name') or user_data.get('login', git_author_name)
                        git_author_email = user_data.get('email') or f"{user_data.get('login', 'mas.automation')}@users.noreply.github.com"
                        logger.info(f"Using GitHub user identity: {git_author_name} <{git_author_email}>")
                    else:
                        logger.warning(f"Failed to fetch GitHub user info (status {response.status_code}), using default identity")
                except Exception as e:
                    logger.warning(f"Error fetching GitHub user info: {e}, using default identity")

            # Set git identity environment variables
            env['GIT_AUTHOR_NAME'] = git_author_name
            env['GIT_AUTHOR_EMAIL'] = git_author_email
            env['GIT_COMMITTER_NAME'] = git_author_name
            env['GIT_COMMITTER_EMAIL'] = git_author_email

            # Extract required command-line parameters
            account_id = params.get('account_id')
            cluster_id = params.get('cluster_id')

            if not account_id:
                logger.error(f"account_id is required for command '{command}'")
                return False
            if not cluster_id:
                logger.error(f"cluster_id is required for command '{command}'")
                return False

            # gitops_working_dir is optional - commands will use their own defaults if not provided

            # Map common parameters to environment variables
            param_mapping = {
                # GitOps Configuration
                'gitops_working_dir': 'GITOPS_WORKING_DIR',
                'cluster_id': 'CLUSTER_ID',
                'cluster_url': 'CLUSTER_URL',
                'account_id': 'ACCOUNT_ID',
                'region_id': 'REGION_ID',
                'github_host': 'GITHUB_HOST',
                'github_org': 'GITHUB_ORG',
                'github_repo': 'GITHUB_REPO',
                'git_branch': 'GIT_BRANCH',
                'github_user': 'GITHUB_USER',
                'git_commit_msg': 'GIT_COMMIT_MSG',
                'github_push': 'GITHUB_PUSH',

                # Secrets Manager
                'secrets_path': 'SECRETS_PATH',
                'sm_aws_secret_region': 'SM_AWS_REGION',
                'sm_aws_access_key_id': 'SM_AWS_ACCESS_KEY_ID',
                'sm_aws_secret_access_key': 'SM_AWS_SECRET_ACCESS_KEY',

                # IBM Container Registry
                'icr_username': 'ICR_USERNAME',
                'icr_password': 'ICR_PASSWORD',
                'icr_cp': 'ICR_CP',
                'icr_cp_open': 'ICR_CP_OPEN',

                # Catalog Configuration
                'mas_catalog_version': 'MAS_CATALOG_VERSION',
                'mas_catalog_image': 'MAS_CATALOG_IMAGE',
                'mas_catalog_action': 'MAS_CATALOG_ACTION',

                # Certificate Manager
                'install_redhat_cert_manager': 'INSTALL_REDHAT_CERT_MANAGER',
                'redhat_cert_manager_install_plan': 'REDHAT_CERT_MANAGER_INSTALL_PLAN',

                # DNS Provider
                'dns_provider': 'DNS_PROVIDER',
                'ocp_domain': 'OCP_CLUSTER_DOMAIN',

                # MAS Instance Configuration
                'mas_instance_id': 'MAS_INSTANCE_ID',
                'mas_workspace_id': 'MAS_WORKSPACE_ID',
                'mas_workspace_name': 'MAS_WORKSPACE_NAME',
                'mas_channel': 'MAS_CHANNEL',
                'mas_domain': 'MAS_DOMAIN',
                'mas_annotations': 'MAS_ANNOTATIONS',
                'mas_image_tags': 'MAS_IMAGE_TAGS',
                'mas_labels': 'MAS_LABELS',
                'mas_config_dir': 'MAS_CONFIG_DIR',
                'mas_manual_cert_mgmt': 'MAS_MANUAL_CERT_MGMT',
                'mas_manual_certs_yaml': 'MAS_MANUAL_CERTS_YAML',
                'mas_pod_template_yaml': 'MAS_POD_TEMPLATE_YAML',
                'mas_install_plan': 'MAS_INSTALL_PLAN',

                # SLS Configuration
                'sls_channel': 'SLS_CHANNEL',
                'sls_install_plan': 'SLS_INSTALL_PLAN',
                'sls_license_id': 'SLS_LICENSE_ID',
                'sls_license_file': 'SLS_LICENSE_FILE',

                # MongoDB Configuration
                'mongo_provider': 'MONGODB_PROVIDER',
                'mongo_namespace': 'MONGO_NAMESPACE',
                'mongodb_action': 'MONGODB_ACTION',
                'mongo_yaml_file': 'MONGO_YAML_FILE',
                'mongo_username': 'MONGO_USERNAME',
                'mongo_password': 'MONGO_PASSWORD',
                'vpc_ipv4_cidr': 'VPC_IPV4_CIDR',
                'aws_docdb_instance_number': 'AWS_DOCDB_INSTANCE_NUMBER',
                'aws_docdb_engine_version': 'AWS_DOCDB_ENGINE_VERSION',

                # Kafka Configuration
                'kafka_action': 'KAFKA_ACTION',
                'kafka_provider': 'KAFKA_PROVIDER',
                'kafka_version': 'KAFKA_VERSION',
                'kafka_namespace': 'KAFKA_NAMESPACE',
                'kafkacfg_file_name': 'KAFKACFG_FILE_NAME',
                'aws_msk_instance_type': 'AWS_MSK_INSTANCE_TYPE',
                'aws_msk_instance_number': 'AWS_MSK_INSTANCE_NUMBER',
                'aws_msk_volume_size': 'AWS_MSK_VOLUME_SIZE',
                'aws_msk_cidr_az1': 'AWS_MSK_CIDR_AZ1',
                'aws_msk_cidr_az2': 'AWS_MSK_CIDR_AZ2',
                'aws_msk_cidr_az3': 'AWS_MSK_CIDR_AZ3',
                'aws_msk_egress_cidr': 'AWS_MSK_EGRESS_CIDR',
                'aws_msk_ingress_cidr': 'AWS_MSK_INGRESS_CIDR',
                'eventstreams_resourcegroup': 'EVENTSTREAMS_RESOURCEGROUP',
                'eventstreams_name': 'EVENTSTREAMS_NAME',
                'eventstreams_location': 'EVENTSTREAMS_LOCATION',

                # COS Configuration
                'cos_action': 'COS_ACTION',
                'cos_type': 'COS_TYPE',
                'cos_resourcegroup': 'COS_RESOURCEGROUP',
                'cos_apikey': 'COS_APIKEY',
                'cos_instance_name': 'COS_INSTANCE_NAME',
                'cos_bucket_name': 'COS_BUCKET_NAME',
                'cos_use_hmac': 'COS_USE_HMAC',

                # EFS Configuration
                'efs_action': 'EFS_ACTION',
                'cloud_provider': 'CLOUD_PROVIDER',

                # Cloud Provider Credentials
                'ibmcloud_apikey': 'IBMCLOUD_APIKEY',
                'ibmcloud_resourcegroup': 'IBMCLOUD_RESOURCEGROUP',
                'aws_region': 'AWS_REGION',
                'aws_access_key_id': 'AWS_ACCESS_KEY_ID',
                'secret_access_key': 'AWS_SECRET_ACCESS_KEY',
                'aws_vpc_id': 'VPC_ID',

                # GitOps Additional Configuration
                'nvidia_gpu_action': 'NVIDIA_GPU_ACTION',
                'sls_instance_name': 'SLS_INSTANCE_NAME',
                'avp_aws_secret_key': 'AVP_AWS_SECRET_KEY',
                'avp_aws_access_key': 'AVP_AWS_ACCESS_KEY',
                'gitops_repo_token_secret': 'GITHUB_PAT',

                # DB2 Configuration
                'db2_action': 'DB2_ACTION',
                'db2_version': 'DB2_VERSION',
                'db2_channel': 'DB2_CHANNEL',

                # Storage Classes
                'storage_class_rwx': 'STORAGE_CLASS_RWX',
                'storage_class_rwo': 'STORAGE_CLASS_RWO',
                'default_block_storage_class': 'DEFAULT_BLOCK_STORAGE_CLASS',
                'default_file_storage_class': 'DEFAULT_FILE_STORAGE_CLASS',

                # MAS Application Configuration
                'mas_app_id': 'MAS_APP_ID',
                'mas_app_channel': 'MAS_APP_CHANNEL',
                'mas_app_install_plan': 'MAS_APP_INSTALL_PLAN',
                'mas_app_catalog_source': 'MAS_APP_CATALOG_SOURCE',
                'mas_app_spec_yaml': 'MAS_APP_SPEC_YAML',

                # DRO Configuration
                'dro_contact_email': 'DRO_CONTACT_EMAIL',
                'dro_contact_firstname': 'DRO_CONTACT_FIRSTNAME',
                'dro_contact_lastname': 'DRO_CONTACT_LASTNAME',

                # SMTP Configuration
                'smtp_host': 'SMTP_HOST',
                'smtp_port': 'SMTP_PORT',
                'smtp_username': 'SMTP_USERNAME',
                'smtp_password': 'SMTP_PASSWORD',
                'smtp_from': 'SMTP_FROM',
                'smtp_security': 'SMTP_SECURITY',
                'smtp_authentication': 'SMTP_AUTHENTICATION',

                # LDAP Configuration
                'ldap_url': 'LDAP_URL',
                'ldap_bind_dn': 'LDAP_BIND_DN',
                'ldap_bind_password': 'LDAP_BIND_PASSWORD',
                'ldap_user_base_dn': 'LDAP_USER_BASE_DN',
                'ldap_group_base_dn': 'LDAP_GROUP_BASE_DN',
                'ldap_certificate_file': 'LDAP_CERTIFICATE_FILE',
                'ldap_basedn': 'LDAP_BASEDN',
                'ldap_userid_map': 'LDAP_USERID_MAP',

                # Advanced Configuration Files
                'dro_ca_certificate_file': 'DRO_CA_CERTIFICATE_FILE',

                # CP4D Configuration
                'cp4d_action': 'CP4D_ACTION',
                'cpd_product_version': 'CPD_PRODUCT_VERSION',
                'cpd_primary_storage_class': 'CPD_PRIMARY_STORAGE_CLASS',
                'cpd_metadata_storage_class': 'CPD_METADATA_STORAGE_CLASS',
            }

            # Set environment variables from params
            for param_key, env_var in param_mapping.items():
                if param_key in params and params[param_key] is not None:
                    # Convert boolean values to lowercase strings ("true"/"false")
                    if isinstance(params[param_key], bool):
                        env[env_var] = str(params[param_key]).lower()
                    else:
                        env[env_var] = str(params[param_key])
                    logger.debug(f"Set environment variable {env_var}={env[env_var]} from param {param_key}")

            # Special case: Set ICR_PASSWORD from ibm_entitlement_key if not already set
            if 'ibm_entitlement_key' in params and params['ibm_entitlement_key']:
                if 'ICR_PASSWORD' not in env:
                    env['ICR_PASSWORD'] = str(params['ibm_entitlement_key'])

            # Build the command with required CLI parameters
            # These parameters are always required and must be passed on the command line
            # to avoid interactive mode
            cmd = [
                'mas',
                command,
                '-a', account_id,
                '-c', cluster_id
            ]

            # Note: gitops_working_dir is set as GITOPS_WORKING_DIR environment variable
            # via the param_mapping above (line 329), so commands that need it will pick it up
            # from the environment rather than as a command-line argument

            # Execute the bash command
            logger.info(f"Executing command: {' '.join(cmd)}")

            # Log critical environment variables for debugging
            critical_vars = ['MAS_WORKSPACE_ID', 'MAS_INSTANCE_ID', 'REGION_ID', 'ACCOUNT_ID', 'CLUSTER_ID']
            logger.debug(f"Critical environment variables for command '{command}':")
            for var in critical_vars:
                logger.debug(f"  {var}={env.get(var, '<not set>')}")

            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=False
            )

            # Log output
            if result.stdout:
                logger.debug(f"Command output: {result.stdout}")
            if result.stderr:
                logger.warning(f"Command stderr: {result.stderr}")

            if result.returncode != 0:
                logger.error(f"Command 'mas {command}' failed with return code {result.returncode}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error executing command 'mas {command}': {e}", exc_info=True)
            return False
