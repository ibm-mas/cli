# *****************************************************************************
# Copyright (c) 2024, 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""
Parameter definitions for GitOps install command.

This module defines the required and optional parameters for the GitOps
installation process. These parameters are used to validate command-line
arguments in non-interactive mode and organize parameters by stage.

Note: CLI arguments use hyphenated names (e.g., --github-host) which are
automatically converted to snake_case parameter names (e.g., github_host)
by argparse. The parameter names below reflect this internal representation.
"""

# =============================================================================
# Common Parameters (used by all stages)
# =============================================================================
commonParams = [
    # Cluster identification
    "cluster_name",
    "cluster_url",
    "account_id",
    "region_id",
    "cluster_id",

    # GitOps repository
    "github_host",
    "github_org",
    "github_repo",
    "git_branch",
    "gitops_repo_token_secret",

    # Secrets management
    "secrets_path",
    "avp_aws_secret_region",
]

# =============================================================================
# Cluster Parameters (cluster-level configuration)
# =============================================================================
clusterParams = [
    # IBM Operator Catalog
    "mas_catalog_version",
    "mas_catalog_image",
    "ibm_entitlement_key",

    # Data Reporter Operator (DRO)
    "install_dro",
    "dro_namespace",
    "dro_install_plan",

    # GPU Operator
    "install_gpu",
    "gpu_namespace",

    # Certificate Manager
    "install_cert_manager",

    # Node Feature Discovery
    "install_nfd",

    # Storage classes
    "storage_class_rwo",
    "storage_class_rwx",
]

# =============================================================================
# Dependencies Parameters (off-cluster dependencies configuration)
# =============================================================================
depsParams = [
    # MAS Instance ID (needed for naming)
    "mas_instance_id",

    # MongoDB Configuration
    "vpc_ipv4_cidr",
    "mongo_provider",
    "mongodb_action",
    "mongo_yaml_file",
    "mongo_username",
    "mongo_password",
    "aws_docdb_instance_number",
    "aws_docdb_engine_version",

    # Kafka Configuration
    "kafka_provider",
    "kafka_version",
    "kafka_action",
    "kafkacfg_file_name",
    "aws_msk_instance_type",

    # EFS Configuration
    "efs_action",
    "cloud_provider",

    # IBM Cloud Configuration
    "ibmcloud_resourcegroup",

    # COS Configuration
    "cos_type",
    "cos_resourcegroup",
    "cos_action",
    "cos_use_hmac",
]

# =============================================================================
# Instance Parameters (MAS instance configuration)
# =============================================================================
instanceParams = [
    # MAS Suite
    "mas_instance_id",
    "mas_channel",
    "mas_domain",
    "operational_mode",

    # MAS Workspace
    "mas_workspace_id",
    "mas_workspace_name",

    # Suite License Service (SLS)
    "sls_channel",
    "sls_instance_name",

    # Data Reporter Operator (DRO)
    "dro_contact_email",
    "dro_contact_firstname",
    "dro_contact_lastname",

    # MongoDB
    "mongo_provider",
    "mongo_namespace",

    # SMTP Configuration (optional)
    "smtp_host",
    "smtp_port",
    "smtp_username",
    "smtp_password",
    "smtp_from",

    # LDAP Configuration (optional)
    "ldap_url",
    "ldap_bind_dn",
    "ldap_bind_password",
    "ldap_user_base_dn",
    "ldap_group_base_dn",
]

# =============================================================================
# Apps Parameters (MAS applications configuration)
# =============================================================================
appsParams = [
    # Application selection
    "mas_app_ids",  # Comma-separated list of app IDs

    # Per-app parameters (dynamically generated for each app)
    # Format: {app_id}_channel, {app_id}_db_action, etc.
    # Examples:
    # - manage_channel
    # - manage_db_action
    # - manage_db_type
    # - manage_db_host
    # - manage_db_port
    # - manage_db_name
    # - manage_db_username
    # - manage_db_password
    # - iot_channel
    # - monitor_channel
    # etc.
]

# =============================================================================
# Required Parameters (must be provided in non-interactive mode)
# =============================================================================
# These parameters are required for all deployments (cluster-only or full instance)
requiredParams = [
    "account_id",
    "cluster_id",
    "github_host",
    "github_org",
    "github_repo",
    "mas_catalog_version",
]

# Additional required parameters for instance deployment (not just cluster):
# These are validated in prepareInstanceParams() when deploying a MAS instance:
# - mas_instance_id
# - mas_channel
# - mas_workspace_id

# =============================================================================
# Optional Parameters (can be provided in non-interactive mode)
# =============================================================================
optionalParams = (
    # All common params except required ones
    [p for p in commonParams if p not in requiredParams] +
    # All cluster params
    clusterParams +
    # All dependencies params
    depsParams +
    # All instance params
    instanceParams +
    # All apps params
    appsParams
)

# =============================================================================
# Parameter Groups for Stage-Specific Preparation
# =============================================================================


def getDepsParamNames():
    """Get all parameter names needed for dependencies stage."""
    return commonParams + depsParams


def getClusterParamNames():
    """Get all parameter names needed for cluster stage."""
    return commonParams + clusterParams


def getInstanceParamNames():
    """Get all parameter names needed for instance stage."""
    return commonParams + instanceParams


def getAppsParamNames():
    """Get all parameter names needed for apps stage."""
    return commonParams + appsParams
