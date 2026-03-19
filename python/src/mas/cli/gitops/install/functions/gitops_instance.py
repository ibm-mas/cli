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
from typing import Dict, Any

from .utils import run_mas_command

logger = logging.getLogger(__name__)


def gitops_instance(params: Dict[str, Any]) -> None:
    """
    Configure instance-level GitOps resources.

    Creates/updates:
    - MAS instance configuration
    - Workspace configuration
    - SMTP/LDAP configuration (if provided)

    Args:
        params: Dictionary containing instance configuration parameters
    """
    logger.info("Configuring instance-level GitOps resources")

    # Validate required parameters
    required = ['account_id', 'cluster_id', 'mas_instance_id']
    missing = [k for k in required if not params.get(k)]
    if missing:
        raise ValueError(f"Missing required instance parameters: {missing}")

    # Extract parameters
    account_id = params['account_id']
    cluster_id = params['cluster_id']
    mas_instance_id = params['mas_instance_id']
    gitops_working_dir = params.get('gitops_working_dir')

    logger.info(f"Configuring MAS instance: {mas_instance_id}")
    logger.info(f"Account: {account_id}, Cluster: {cluster_id}")

    # Set environment variables from params
    # This ensures all configuration is available to the bash functions
    for key, value in params.items():
        if value is not None:
            env_var = key.upper()
            os.environ[env_var] = str(value)
            logger.debug(f"Set environment variable: {env_var}={value}")

    # Call gitops-suite function
    logger.info("Calling gitops-suite")
    cmd = ["mas", "gitops-suite", "-a", account_id, "-c", cluster_id]
    if gitops_working_dir:
        cmd.extend(["--dir", gitops_working_dir])
    run_mas_command(cmd, "gitops-suite")

    # Call gitops-license function (if license configuration is provided)
    if params.get('license_file') or params.get('sls_license_id'):
        logger.info("Calling gitops-license")
        cmd = ["mas", "gitops-license", "-a", account_id, "-c", cluster_id]
        if gitops_working_dir:
            cmd.extend(["--dir", gitops_working_dir])
        run_mas_command(cmd, "gitops-license")

    # Call gitops-suite-workspace function
    logger.info("Calling gitops-suite-workspace")
    cmd = ["mas", "gitops-suite-workspace", "-a", account_id, "-c", cluster_id]
    if gitops_working_dir:
        cmd.extend(["--dir", gitops_working_dir])
    run_mas_command(cmd, "gitops-suite-workspace")

    # Call gitops-mas-provisioner function (if configured)
    if params.get('configure_mas_provisioner') or params.get('mas_provisioner_enabled'):
        logger.info("Calling gitops-mas-provisioner")
        cmd = ["mas", "gitops-mas-provisioner", "-a", account_id, "-c", cluster_id]
        if gitops_working_dir:
            cmd.extend(["--dir", gitops_working_dir])
        run_mas_command(cmd, "gitops-mas-provisioner")

    # Call gitops-mas-config for system-level configurations

    # MongoDB configuration
    if params.get('mongodb_enabled') or params.get('mas_config_mongo'):
        logger.info("Calling gitops-mas-config for MongoDB")
        cmd = [
            "mas", "gitops-mas-config",
            "-a", account_id,
            "-c", cluster_id,
            "-s", "system",
            "-t", "mongo",
            "-o", "upsert"
        ]
        if gitops_working_dir:
            cmd.extend(["--dir", gitops_working_dir])
        run_mas_command(cmd, "gitops-mas-config (mongo)")

    # SLS configuration
    if params.get('sls_enabled') or params.get('mas_config_sls'):
        logger.info("Calling gitops-mas-config for SLS")
        cmd = [
            "mas", "gitops-mas-config",
            "-a", account_id,
            "-c", cluster_id,
            "-s", "system",
            "-t", "sls",
            "-o", "upsert"
        ]
        if gitops_working_dir:
            cmd.extend(["--dir", gitops_working_dir])
        run_mas_command(cmd, "gitops-mas-config (sls)")

    # BAS configuration
    if params.get('bas_enabled') or params.get('mas_config_bas'):
        logger.info("Calling gitops-mas-config for BAS")
        cmd = [
            "mas", "gitops-mas-config",
            "-a", account_id,
            "-c", cluster_id,
            "-s", "system",
            "-t", "bas",
            "-o", "upsert"
        ]
        if gitops_working_dir:
            cmd.extend(["--dir", gitops_working_dir])
        run_mas_command(cmd, "gitops-mas-config (bas)")

    logger.info("Instance configuration complete")
