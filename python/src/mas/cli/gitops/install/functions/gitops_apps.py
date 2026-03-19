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
import os
from typing import Dict, Any, List

from .utils import run_mas_command

logger = logging.getLogger(__name__)


def _set_app_specific_env_vars(params: Dict[str, Any], app_id: str, var_names: List[str]) -> Dict[str, str]:
    """
    Set app-specific environment variables and return original values for restoration.

    Args:
        params: Dictionary containing all parameters
        app_id: Application ID (e.g., 'manage', 'health')
        var_names: List of environment variable names to check for app-specific versions

    Returns:
        Dictionary of original environment variable values for restoration
    """
    original_env = {}

    for var_name in var_names:
        app_specific_var = f"{var_name}_{app_id.upper()}"

        # Check if app-specific parameter exists
        app_specific_param = f"{var_name.lower()}_{app_id.lower()}"
        if app_specific_param in params and params[app_specific_param] is not None:
            logger.info(f"Using app-specific parameter {app_specific_param} for {var_name}")
            if var_name in os.environ:
                original_env[var_name] = os.environ[var_name]
            os.environ[var_name] = str(params[app_specific_param])
        # Also check environment for app-specific variable
        elif app_specific_var in os.environ:
            logger.info(f"Using app-specific environment variable {app_specific_var} for {var_name}")
            if var_name in os.environ:
                original_env[var_name] = os.environ[var_name]
            os.environ[var_name] = os.environ[app_specific_var]

    return original_env


def _restore_env_vars(original_env: Dict[str, str]) -> None:
    """
    Restore original environment variable values.

    Args:
        original_env: Dictionary of original environment variable values
    """
    for var_name, value in original_env.items():
        os.environ[var_name] = value


def gitops_apps(params: Dict[str, Any]) -> None:
    """
    Configure application-level GitOps resources.

    Creates/updates:
    - Application configurations
    - Database configurations

    Args:
        params: Dictionary containing applications configuration parameters
    """
    logger.info("Configuring application-level GitOps resources")

    # Validate required parameters
    required = ['account_id', 'cluster_id', 'mas_instance_id']
    missing = [k for k in required if not params.get(k)]
    if missing:
        raise ValueError(f"Missing required app parameters: {missing}")

    # Extract parameters
    account_id = params['account_id']
    cluster_id = params['cluster_id']
    gitops_working_dir = params.get('gitops_working_dir')

    # Extract app IDs
    mas_app_ids_str = params.get('mas_app_ids', '')
    if not mas_app_ids_str:
        logger.warning("No applications specified")
        return

    mas_app_ids = [app.strip() for app in mas_app_ids_str.split(',') if app.strip()]
    logger.info(f"Configuring applications: {', '.join(mas_app_ids)}")

    # Set base environment variables from params
    for key, value in params.items():
        if value is not None and not any(app_id in key.lower() for app_id in mas_app_ids):
            env_var = key.upper()
            os.environ[env_var] = str(value)
            logger.debug(f"Set environment variable: {env_var}={value}")

    # Configure each application
    for app_id in mas_app_ids:
        logger.info(f"Configuring application: {app_id}")

        # DB2 environment variables that might be app-specific
        db2_env_vars = [
            "DB2_INSTANCE_NAME", "DB2_VERSION", "DB2_DBNAME", "DB2_TLS_VERSION",
            "DB2_TABLE_ORG", "DB2_4K_DEVICE_SUPPORT", "DB2_WORKLOAD", "DB2_MLN_COUNT",
            "DB2_NUM_PODS", "DB2_META_STORAGE_CLASS", "DB2_META_STORAGE_SIZE",
            "DB2_META_STORAGE_ACCESSMODE", "DB2_DATA_STORAGE_CLASS", "DB2_DATA_STORAGE_SIZE",
            "DB2_DATA_STORAGE_ACCESSMODE", "DB2_BACKUP_STORAGE_CLASS", "DB2_BACKUP_STORAGE_SIZE",
            "DB2_BACKUP_STORAGE_ACCESSMODE", "DB2_LOGS_STORAGE_CLASS", "DB2_LOGS_STORAGE_SIZE",
            "DB2_LOGS_STORAGE_ACCESSMODE", "DB2_TEMP_STORAGE_CLASS", "DB2_TEMP_STORAGE_SIZE",
            "DB2_TEMP_STORAGE_ACCESSMODE", "DB2_CPU_REQUESTS", "DB2_CPU_LIMITS",
            "DB2_MEMORY_REQUESTS", "DB2_MEMORY_LIMITS", "JDBC_INSTANCE_NAME", "MAS_APP_ID"
        ]

        # Call gitops-db2u-database for the app (if DB2 is configured)
        if params.get(f'{app_id}_db_type', 'db2').lower() == 'db2' or params.get(f'db2_enabled_{app_id}'):
            logger.info(f"Calling gitops-db2u-database for {app_id}")
            original_env = _set_app_specific_env_vars(params, app_id, db2_env_vars)

            try:
                cmd = ["mas", "gitops-db2u-database", "-a", account_id, "-c", cluster_id]
                if gitops_working_dir:
                    cmd.extend(["--dir", gitops_working_dir])
                run_mas_command(cmd, f"gitops-db2u-database ({app_id})")
            finally:
                _restore_env_vars(original_env)

        # MAS config environment variables that might be app-specific
        mas_config_vars = [
            "MAS_APP_ID", "MAS_APP_KIND", "MAS_APP_CHANNEL", "MAS_APP_INSTALL_PLAN",
            "MAS_APP_CATALOG_SOURCE", "MAS_APP_API_VERSION", "MAS_APPWS_API_VERSION",
            "MAS_APPWS_KIND", "MAS_WORKSPACE_ID", "JDBC_INSTANCE_NAME", "JDBC_TYPE",
            "JDBC_ROUTE", "JDBC_CONNECTION_URL"
        ]

        # Call gitops-mas-config for JDBC configuration
        if params.get(f'{app_id}_jdbc_enabled') or params.get(f'jdbc_enabled_{app_id}'):
            logger.info(f"Calling gitops-mas-config for JDBC configuration ({app_id})")
            original_env = _set_app_specific_env_vars(params, app_id, mas_config_vars)

            try:
                cmd = [
                    "mas", "gitops-mas-config",
                    "-a", account_id,
                    "-c", cluster_id,
                    "-s", "wsapp",
                    "-t", "jdbc",
                    "-o", "upsert"
                ]
                if gitops_working_dir:
                    cmd.extend(["--dir", gitops_working_dir])
                run_mas_command(cmd, f"gitops-mas-config jdbc ({app_id})")
            finally:
                _restore_env_vars(original_env)

        # App installation environment variables
        app_install_vars = [
            "MAS_APP_ID", "MAS_APP_KIND", "MAS_APP_CHANNEL", "MAS_APP_INSTALL_PLAN",
            "MAS_APP_CATALOG_SOURCE", "MAS_APP_API_VERSION", "MAS_APP_SPEC_YAML"
        ]

        # Call gitops-suite-app-install
        logger.info(f"Calling gitops-suite-app-install for {app_id}")
        original_env = _set_app_specific_env_vars(params, app_id, app_install_vars)

        try:
            cmd = ["mas", "gitops-suite-app-install", "-a", account_id, "-c", cluster_id]
            if gitops_working_dir:
                cmd.extend(["--dir", gitops_working_dir])
            run_mas_command(cmd, f"gitops-suite-app-install ({app_id})")
        finally:
            _restore_env_vars(original_env)

        # App configuration environment variables
        app_config_vars = [
            "MAS_APP_ID", "MAS_APPWS_API_VERSION", "MAS_APPWS_KIND", "MAS_APPWS_SPEC_YAML",
            "MAS_WORKSPACE_ID"
        ]

        # Call gitops-suite-app-config
        logger.info(f"Calling gitops-suite-app-config for {app_id}")
        original_env = _set_app_specific_env_vars(params, app_id, app_config_vars)

        try:
            cmd = ["mas", "gitops-suite-app-config", "-a", account_id, "-c", cluster_id]
            if gitops_working_dir:
                cmd.extend(["--dir", gitops_working_dir])
            run_mas_command(cmd, f"gitops-suite-app-config ({app_id})")
        finally:
            _restore_env_vars(original_env)

    logger.info("Applications configuration complete")
