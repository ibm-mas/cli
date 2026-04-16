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

            # Step 2.5: Execute gitops-license
            with Halo(text='Executing gitops-license', spinner=self.spinner) as h:
                if self._executeGitOpsCommand('gitops-license', self.params):
                    h.stop_and_persist(symbol=self.success_icon, text="gitops-license completed successfully")
                else:
                    h.stop_and_persist(symbol=self.failure_icon, text="gitops-license failed")
                    return False

            # Step 3: Execute gitops-suite (instance)
            with Halo(text='Executing gitops-suite', spinner=self.spinner) as h:
                if self._executeGitOpsCommand('gitops-suite', self.params):
                    h.stop_and_persist(symbol=self.success_icon, text="gitops-suite completed successfully")
                else:
                    h.stop_and_persist(symbol=self.failure_icon, text="gitops-suite failed")
                    return False

            # Step 3.1: Execute gitops-mas-config for bas
            with Halo(text='Executing gitops-mas-config (bas)', spinner=self.spinner) as h:
                mas_config_params = self.params.copy()
                mas_config_params['mas_config_type'] = 'bas'
                mas_config_params['config_action'] = 'upsert'
                if self._executeGitOpsCommand('gitops-mas-config', mas_config_params):
                    h.stop_and_persist(symbol=self.success_icon, text="gitops-mas-config (bas) completed successfully")
                else:
                    h.stop_and_persist(symbol=self.failure_icon, text="gitops-mas-config (bas) failed")
                    return False

            # Step 3.2: Execute gitops-mas-config for mongo
            with Halo(text='Executing gitops-mas-config (mongo)', spinner=self.spinner) as h:
                mas_config_params = self.params.copy()
                mas_config_params['mas_config_type'] = 'mongo'
                mas_config_params['config_action'] = 'upsert'
                if self._executeGitOpsCommand('gitops-mas-config', mas_config_params):
                    h.stop_and_persist(symbol=self.success_icon, text="gitops-mas-config (mongo) completed successfully")
                else:
                    h.stop_and_persist(symbol=self.failure_icon, text="gitops-mas-config (mongo) failed")
                    return False

            # Step 3.3: Execute gitops-mas-config for sls
            with Halo(text='Executing gitops-mas-config (sls)', spinner=self.spinner) as h:
                mas_config_params = self.params.copy()
                mas_config_params['mas_config_type'] = 'sls'
                mas_config_params['config_action'] = 'upsert'
                if self._executeGitOpsCommand('gitops-mas-config', mas_config_params):
                    h.stop_and_persist(symbol=self.success_icon, text="gitops-mas-config (sls) completed successfully")
                else:
                    h.stop_and_persist(symbol=self.failure_icon, text="gitops-mas-config (sls) failed")
                    return False

            # Step 3.4: Execute gitops-db2u
            with Halo(text='Executing gitops-db2u', spinner=self.spinner) as h:
                if self._executeGitOpsCommand('gitops-db2u', self.params):
                    h.stop_and_persist(symbol=self.success_icon, text="gitops-db2u completed successfully")
                else:
                    h.stop_and_persist(symbol=self.failure_icon, text="gitops-db2u failed")
                    return False

            # Step 3.5: Execute gitops-db2u-database for manage, facilities, and iot apps
            # followed by gitops-mas-config (jdbc) for each
            db2u_apps = []
            if self.params.get('mas_app_id_manage'):
                db2u_apps.append('manage')
            if self.params.get('mas_app_id_facilities'):
                db2u_apps.append('facilities')
            if self.params.get('mas_app_id_iot'):
                db2u_apps.append('iot')

            for app_id in db2u_apps:
                # Execute gitops-db2u-database for the app
                with Halo(text=f'Executing gitops-db2u-database for {app_id}', spinner=self.spinner) as h:
                    db2u_params = self._prepare_app_params(app_id, 'install')
                    if self._executeGitOpsCommand('gitops-db2u-database', db2u_params):
                        h.stop_and_persist(symbol=self.success_icon, text=f"gitops-db2u-database for {app_id} completed successfully")
                    else:
                        h.stop_and_persist(symbol=self.failure_icon, text=f"gitops-db2u-database for {app_id} failed")
                        return False

                # Execute gitops-mas-config (jdbc) after each db2u-database
                with Halo(text=f'Executing gitops-mas-config (jdbc) for {app_id}', spinner=self.spinner) as h:
                    jdbc_params = db2u_params.copy()
                    jdbc_params['mas_config_type'] = 'jdbc'
                    jdbc_params['mas_app_id'] = app_id
                    jdbc_params['config_action'] = 'upsert'
                    # Set mas_config_scope: 'system' for iot, 'wsapp' for manage and facilities
                    if app_id == 'iot':
                        jdbc_params['mas_config_scope'] = 'system'
                    else:  # manage or facilities
                        jdbc_params['mas_config_scope'] = 'wsapp'
                    if self._executeGitOpsCommand('gitops-mas-config', jdbc_params):
                        h.stop_and_persist(symbol=self.success_icon, text=f"gitops-mas-config (jdbc) for {app_id} completed successfully")
                    else:
                        h.stop_and_persist(symbol=self.failure_icon, text=f"gitops-mas-config (jdbc) for {app_id} failed")
                        return False

            # Step 4: Execute gitops-suite-workspace (only if mas_workspace_id is set)
            if self.params.get('mas_workspace_id'):
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

            # Step 6: Execute gitops-suite-app-config for each application that needs configuration (only if mas_workspace_id is set)
            if self.params.get('mas_workspace_id'):
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

            # Special mappings for parameters that need name transformations
            # These are exceptions where the param name doesn't directly map to the env var name
            special_mappings = {
                # Parameters that need prefix/suffix changes
                'secret_access_key': 'AWS_SECRET_ACCESS_KEY',
                'aws_vpc_id': 'VPC_ID',
                'ocp_domain': 'OCP_CLUSTER_DOMAIN',
                'gitops_repo_token_secret': 'GITHUB_PAT',

                # Parameters with aliases (multiple param names -> same env var)
                'catalog_version': 'MAS_CATALOG_VERSION',
                'mas_catalog_version': 'MAS_CATALOG_VERSION',
                'catalog_image': 'MAS_CATALOG_IMAGE',
                'mas_catalog_image': 'MAS_CATALOG_IMAGE',
                'catalog_action': 'MAS_CATALOG_ACTION',
                'mas_catalog_action': 'MAS_CATALOG_ACTION',

                'storage_provider': 'AISERVICE_STORAGE_PROVIDER',
                'aiservice_storage_provider': 'AISERVICE_STORAGE_PROVIDER',
                'storage_ssl': 'AISERVICE_STORAGE_SSL',
                'aiservice_storage_ssl': 'AISERVICE_STORAGE_SSL',
                'storage_region': 'AISERVICE_STORAGE_REGION',
                'aiservice_storage_region': 'AISERVICE_STORAGE_REGION',

                'cis_compliance_install_plan': 'CIS_INSTALL_PLAN',
                'cis_install_plan': 'CIS_INSTALL_PLAN',

                'db2_subscription_install_plan': 'DB2_INSTALL_PLAN',
                'db2_install_plan': 'DB2_INSTALL_PLAN',

                'mongo_provider': 'MONGODB_PROVIDER',
                'mongodb_action': 'MONGODB_ACTION',
                'yaml_file': 'MONGO_YAML_FILE',
            }

            # Conditional mappings - only set if target env var is not already set
            # These provide fallback values from alternative parameter names
            conditional_mappings = {
                'ibm_entitlement_key': 'ICR_PASSWORD',
                'sls_license_file': 'LICENSE_FILE',
            }

            # Track which env vars have been set to avoid duplicates
            env_vars_set = set()

            # First, apply special mappings
            for param_key, env_var in special_mappings.items():
                if param_key in params and params[param_key] is not None:
                    # Convert boolean values to lowercase strings ("true"/"false")
                    if isinstance(params[param_key], bool):
                        env[env_var] = str(params[param_key]).lower()
                    else:
                        env[env_var] = str(params[param_key])
                    env_vars_set.add(env_var)
                    logger.debug(f"Set environment variable {env_var}={env[env_var]} from param {param_key} (special mapping)")

            # Then, set all other params as env vars (uppercase param name)
            for param_key, param_value in params.items():
                if param_value is not None:
                    # Convert param name to uppercase for env var name
                    env_var = param_key.upper()

                    # Skip if already set by special mapping
                    if env_var in env_vars_set:
                        continue

                    # Convert boolean values to lowercase strings ("true"/"false")
                    if isinstance(param_value, bool):
                        env[env_var] = str(param_value).lower()
                    else:
                        env[env_var] = str(param_value)
                    env_vars_set.add(env_var)
                    logger.debug(f"Set environment variable {env_var}={env[env_var]} from param {param_key}")

            # Apply conditional mappings - only set if target env var is not already set
            for param_key, env_var in conditional_mappings.items():
                if param_key in params and params[param_key] is not None:
                    if env_var not in env:
                        # Convert boolean values to lowercase strings ("true"/"false")
                        if isinstance(params[param_key], bool):
                            env[env_var] = str(params[param_key]).lower()
                        else:
                            env[env_var] = str(params[param_key])
                        env_vars_set.add(env_var)
                        logger.debug(f"Set environment variable {env_var}={env[env_var]} from param {param_key} (conditional mapping)")

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
