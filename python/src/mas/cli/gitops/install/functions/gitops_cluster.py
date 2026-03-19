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


def gitops_cluster(params: Dict[str, Any]) -> None:
    """
    Configure cluster-level GitOps resources.

    Creates/updates:
    - Cluster configuration files in GitOps repo
    - Operator subscriptions
    - Catalog sources

    Args:
        params: Dictionary containing cluster configuration parameters
    """
    logger.info("Configuring cluster-level GitOps resources")

    # Validate required parameters
    required = ['account_id', 'cluster_id']
    missing = [k for k in required if not params.get(k)]
    if missing:
        raise ValueError(f"Missing required cluster parameters: {missing}")

    # Extract parameters
    account_id = params['account_id']
    cluster_id = params['cluster_id']
    gitops_working_dir = params.get('gitops_working_dir')

    logger.info(f"Configuring cluster: {cluster_id}")
    logger.info(f"Account: {account_id}")

    # Set environment variables from params
    # This ensures all configuration is available to the bash functions
    for key, value in params.items():
        if value is not None:
            env_var = key.upper()
            os.environ[env_var] = str(value)
            logger.debug(f"Set environment variable: {env_var}={value}")

    # Call gitops-cluster function
    logger.info("Calling gitops-cluster")
    cmd = ["mas", "gitops-cluster", "-a", account_id, "-c", cluster_id]
    if gitops_working_dir:
        cmd.extend(["--dir", gitops_working_dir])
    run_mas_command(cmd, "gitops-cluster")

    # Call optional cluster-level functions based on configuration

    # EFS CSI Driver (if configured)
    if params.get('configure_efs_csi_driver') or params.get('efs_enabled'):
        logger.info("Calling gitops-efs-csi-driver")
        cmd = ["mas", "gitops-efs-csi-driver", "-a", account_id, "-c", cluster_id]
        if gitops_working_dir:
            cmd.extend(["--dir", gitops_working_dir])
        run_mas_command(cmd, "gitops-efs-csi-driver")

    # CIS Compliance (if configured)
    if params.get('configure_cis_compliance') or params.get('cis_compliance_enabled'):
        logger.info("Calling gitops-cis-compliance")
        cmd = ["mas", "gitops-cis-compliance", "-a", account_id, "-c", cluster_id]
        if gitops_working_dir:
            cmd.extend(["--dir", gitops_working_dir])
        run_mas_command(cmd, "gitops-cis-compliance")

    # NVIDIA GPU (if configured)
    if params.get('configure_nvidia_gpu') or params.get('gpu_enabled'):
        logger.info("Calling gitops-nvidia-gpu")
        cmd = ["mas", "gitops-nvidia-gpu", "-a", account_id, "-c", cluster_id]
        if gitops_working_dir:
            cmd.extend(["--dir", gitops_working_dir])
        run_mas_command(cmd, "gitops-nvidia-gpu")

    # DRO (if configured)
    if params.get('configure_gitops_dro') or params.get('dro_enabled'):
        logger.info("Calling gitops-dro")
        cmd = ["mas", "gitops-dro", "-a", account_id, "-c", cluster_id]
        if gitops_working_dir:
            cmd.extend(["--dir", gitops_working_dir])
        run_mas_command(cmd, "gitops-dro")

    # DB2U (if configured)
    if params.get('configure_db2u') or params.get('db2u_enabled'):
        logger.info("Calling gitops-db2u")
        cmd = ["mas", "gitops-db2u", "-a", account_id, "-c", cluster_id]
        if gitops_working_dir:
            cmd.extend(["--dir", gitops_working_dir])
        run_mas_command(cmd, "gitops-db2u")

    logger.info("Cluster configuration complete")
