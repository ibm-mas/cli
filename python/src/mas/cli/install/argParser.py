# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

import argparse
from os import path

from .. import __version__ as packageVersion
from ..cli import getHelpFormatter

# Constants for argument choices
DNS_PROVIDERS = ["cloudflare", "cis", "route53"]
STORAGE_ACCESS_MODES = ["ReadWriteMany", "ReadWriteOnce"]
KAFKA_PROVIDERS = ["strimzi", "redhat", "ibm", "aws"]
DB2_TYPES = ["db2wh", "db2oltp"]
TAINT_EFFECTS = ["NoSchedule", "PreferNoSchedule", "NoExecute"]
UPGRADE_TYPES = ["regularUpgrade", "onlineUpgrade"]
ATTACHMENT_PROVIDERS = ["filestorage", "ibm", "aws"]
ATTACHMENT_MODES = ["cr", "db"]
FACILITIES_SIZES = ["small", "medium", "large"]
IMAGE_PULL_POLICIES = ["IfNotPresent", "Always"]


def isValidFile(parser: argparse.ArgumentParser, arg: str) -> str:
    """
    Validate that a file exists at the given path.

    Args:
        parser: The ArgumentParser instance for error reporting
        arg: The file path to validate

    Returns:
        The validated file path

    Raises:
        ArgumentParser.error: If the file does not exist
    """
    if not path.exists(arg):
        parser.error(f"Error: The file {arg} does not exist")
    else:
        return arg


installArgParser = argparse.ArgumentParser(
    prog="mas install",
    description="\n".join([
        f"IBM Maximo Application Suite Admin CLI v{packageVersion}",
        "Install MAS by configuring and launching the MAS Uninstall Tekton Pipeline.\n",
        "Interactive Mode:",
        "Omitting the --instance-id option will trigger an interactive prompt"
    ]),
    epilog="Refer to the online documentation for more information: https://ibm-mas.github.io/cli/",
    formatter_class=getHelpFormatter(),
    add_help=False
)

# MAS Catalog Selection & Entitlement
# -----------------------------------------------------------------------------
catArgGroup = installArgParser.add_argument_group(
    "MAS Catalog Selection & Entitlement",
    "Configure which IBM Maximo Operator Catalog to install and provide your IBM entitlement key for access to container images."
)
catArgGroup.add_argument(
    "-c", "--mas-catalog-version",
    required=False,
    help="IBM Maximo Operator Catalog to install"
)
catArgGroup.add_argument(
    "--mas-catalog-digest",
    required=False,
    help="IBM Maximo Operator Catalog Digest, only required when installing development catalog sources"
)
catArgGroup.add_argument(
    "--ibm-entitlement-key",
    required=False,
    help="IBM entitlement key"
)

# Basic Configuration
# -----------------------------------------------------------------------------
masArgGroup = installArgParser.add_argument_group(
    "Basic Configuration",
    "Core configuration options for your MAS instance including instance ID, workspace settings, subscription channels, and user settings."
)
masArgGroup.add_argument(
    "-i", "--mas-instance-id",
    required=False,
    help="MAS Instance ID"
)
masArgGroup.add_argument(
    "-w", "--mas-workspace-id",
    required=False,
    help="MAS Workspace ID"
)
masArgGroup.add_argument(
    "-W", "--mas-workspace-name",
    required=False,
    help="MAS Workspace Name"
)
masArgGroup.add_argument(
    "--mas-channel",
    required=False,
    help="Subscription channel for the Core Platform"
)
masArgGroup.add_argument(
    "--aiservice-instance-id",
    required=False,
    help="AI Service Instance ID"
)
masArgGroup.add_argument(
    "--allow-special-chars",
    dest="mas_special_characters",
    required=False,
    help="Allow special characters for user username/ID",
    action="store_true"
)

# Advanced Configuration
# -----------------------------------------------------------------------------
masAdvancedArgGroup = installArgParser.add_argument_group(
    "Advanced Configuration",
    "Advanced configuration options for MAS including DNS providers, certificates, domain settings, and IPv6 support."
)
masAdvancedArgGroup.add_argument(
    "--superuser-username",
    dest="mas_superuser_username",
    required=False,
    help=""
)
masAdvancedArgGroup.add_argument(
    "--superuser-password",
    dest="mas_superuser_password",
    required=False,
    help=""
)
masAdvancedArgGroup.add_argument(
    "--additional-configs",
    required=False,
    help="Path to a directory containing additional configuration files to be applied"
)
masAdvancedArgGroup.add_argument(
    "--pod-templates",
    required=False,
    help="Path to directory containing custom podTemplates configuration files to be applied"
)
masAdvancedArgGroup.add_argument(
    "--non-prod",
    required=False,
    help="Install MAS in non-production mode",
    action="store_true"
)
masAdvancedArgGroup.add_argument(
    "--disable-ca-trust",
    dest="mas_trust_default_cas",
    required=False,
    help="Disable built-in trust of well-known CAs",
    action="store_const",
    const="false"
)
masAdvancedArgGroup.add_argument(
    "--routing",
    dest="mas_routing_mode",
    required=False,
    help="Configure MAS with path or subdomain routing",
    choices=["path", "subdomain"]
)
masAdvancedArgGroup.add_argument(
    "--configure-ingress",
    dest="mas_configure_ingress",
    required=False,
    action="store_true",
    help="Automatically configure IngressController to allow InterNamespaceAllowed for path-based routing"
)
masAdvancedArgGroup.add_argument(
    "--ingress-controller-name",
    dest="mas_ingress_controller_name",
    required=False,
    help="Name of the IngressController to use for path-based routing (default: 'default')"
)
masAdvancedArgGroup.add_argument(
    "--manual-certificates",
    required=False,
    help="Path to directory containing the certificates to be applied"
)
masAdvancedArgGroup.add_argument(
    "--domain",
    dest="mas_domain",
    required=False,
    help="Configure MAS with a custom domain"
)
masAdvancedArgGroup.add_argument(
    "--disable-walkme",
    dest="mas_enable_walkme",
    required=False,
    help="Disable MAS guided tour",
    action="store_const",
    const="false"
)

masAdvancedArgGroup.add_argument(
    "--dns-provider",
    dest="dns_provider",
    required=False,
    help="Enable automatic DNS management (see DNS Configuration options)",
    choices=DNS_PROVIDERS,
    metavar="{cloudflare,cis,route53}"
)

masAdvancedArgGroup.add_argument(
    "--ocp-ingress",
    dest="ocp_ingress",
    required=False,
    help="Overwrites Ingress Domain"
)

masAdvancedArgGroup.add_argument(
    "--mas-cluster-issuer",
    dest="mas_cluster_issuer",
    required=False,
    help="Provide the name of the ClusterIssuer to configure MAS to issue certificates",
)

masAdvancedArgGroup.add_argument(
    "--enable-ipv6",
    dest="enable_ipv6",
    required=False,
    help="Configure MAS to run in IP version 6. Before setting this option, be sure your cluster is configured in IP version 6",
    action="store_const",
    const="true"
)

# DNS Integration - IBM CIS
# -----------------------------------------------------------------------------
cisArgGroup = installArgParser.add_argument_group("DNS Integration - CIS")
cisArgGroup.add_argument(
    "--cis-email",
    dest="cis_email",
    required=False,
    help="Required when DNS provider is CIS and you want to use a Let's Encrypt ClusterIssuer"
)
cisArgGroup.add_argument(
    "--cis-apikey",
    dest="cis_apikey",
    required=False,
    help="Required when DNS provider is CIS"
)
cisArgGroup.add_argument(
    "--cis-crn",
    dest="cis_crn",
    required=False,
    help="Required when DNS provider is CIS"
)
cisArgGroup.add_argument(
    "--cis-subdomain",
    dest="cis_subdomain",
    required=False,
    help="Optionally setup MAS instance as a subdomain under a multi-tenant CIS DNS record"
)

# DNS Integration - CloudFlare
# -----------------------------------------------------------------------------
cloudFlareArgGroup = installArgParser.add_argument_group(
    "DNS Integration - CloudFlare",
    "Configuration options for Cloudflare DNS provider, including API credentials, zone, and subdomain settings."
)
cloudFlareArgGroup.add_argument(
    "--cloudflare-email",
    dest="cloudflare_email",
    required=False,
    help="Required when DNS provider is Cloudflare"
)
cloudFlareArgGroup.add_argument(
    "--cloudflare-apitoken",
    dest="cloudflare_apitoken",
    required=False,
    help="Required when DNS provider is Cloudflare"
)
cloudFlareArgGroup.add_argument(
    "--cloudflare-zone",
    dest="cloudflare_zone",
    required=False,
    help="Required when DNS provider is Cloudflare"
)
cloudFlareArgGroup.add_argument(
    "--cloudflare-subdomain",
    dest="cloudflare_subdomain",
    required=False,
    help="Required when DNS provider is Cloudflare"
)

# Storage
# -----------------------------------------------------------------------------
storageArgGroup = installArgParser.add_argument_group(
    "Storage",
    "Configure storage classes for ReadWriteOnce (RWO) and ReadWriteMany (RWX) volumes, and pipeline storage settings."
)
storageArgGroup.add_argument(
    "--storage-class-rwo",
    required=False,
    help="ReadWriteOnce (RWO) storage class (e.g. ibmc-block-gold)"
)
storageArgGroup.add_argument(
    "--storage-class-rwx",
    required=False,
    help="ReadWriteMany (RWX) storage class (e.g. ibmc-file-gold-gid)"
)
storageArgGroup.add_argument(
    "--storage-pipeline",
    required=False,
    help="Install pipeline storage class (e.g. ibmc-file-gold-gid)"
)
storageArgGroup.add_argument(
    "--storage-accessmode",
    required=False,
    help="Install pipeline storage class access mode",
    choices=STORAGE_ACCESS_MODES,
    metavar="{ReadWriteMany,ReadWriteOnce}"
)

# IBM Suite License Service
# -----------------------------------------------------------------------------
slsArgGroup = installArgParser.add_argument_group(
    "IBM Suite License Service",
    "Configure IBM Suite License Service (SLS) including license file location, namespace, and subscription channel."
)
slsArgGroup.add_argument(
    "--license-file",
    required=False,
    help="Path to MAS license file",
    type=lambda x: isValidFile(installArgParser, x)
)
slsArgGroup.add_argument(
    "--sls-namespace",
    required=False,
    help="Customize the SLS install namespace",
    default="ibm-sls"
)
slsArgGroup.add_argument(
    "--dedicated-sls",
    action="store_true",
    default=False,
    help="Set the SLS namespace to mas-<instanceid>-sls"
)
slsArgGroup.add_argument(
    "--sls-channel",
    required=False,
    help="Customize the SLS channel when in development mode",
)

# IBM Data Reporting Operator
# -----------------------------------------------------------------------------
droArgGroup = installArgParser.add_argument_group(
    "IBM Data Reporting Operator",
    "Configure IBM Data Reporting Operator (DRO) with contact information and namespace settings for usage data collection."
)
droArgGroup.add_argument(
    "--contact-email",
    "--uds-email",
    dest="dro_contact_email",
    required=False,
    help="Contact e-mail address"
)
droArgGroup.add_argument(
    "--contact-firstname",
    "--uds-firstname",
    dest="dro_contact_firstname",
    required=False,
    help="Contact first name"
)
droArgGroup.add_argument(
    "--contact-lastname",
    "--uds-lastname",
    dest="dro_contact_lastname",
    required=False,
    help="Contact last name"
)
droArgGroup.add_argument(
    "--dro-namespace",
    required=False,
    help="Namespace for DRO"
)

# MongoDB Community Operator
# -----------------------------------------------------------------------------
mongoArgGroup = installArgParser.add_argument_group(
    "MongoDB Community Operator",
    "Configure the namespace for MongoDB Community Operator deployment."
)
mongoArgGroup.add_argument(
    "--mongodb-namespace",
    required=False,
    help="Namespace for MongoDB Community Operator"
)

# OCP Configuration
# -----------------------------------------------------------------------------
ocpArgGroup = installArgParser.add_argument_group(
    "OCP Configuration",
    "OpenShift Container Platform specific configuration including ingress certificate settings."
)
ocpArgGroup.add_argument(
    "--ocp-ingress-tls-secret-name",
    required=False,
    help="Name of the secret holding the cluster's ingress certificates"
)

# MAS Applications
# -----------------------------------------------------------------------------
masAppsArgGroup = installArgParser.add_argument_group(
    "MAS Applications",
    "Configure subscription channels for MAS applications including Assist, IoT, Monitor, Optimizer, Predict, and Visual Inspection."
)
masAppsArgGroup.add_argument(
    "--assist-channel",
    required=False,
    help="Subscription channel for Maximo Assist"
)
masAppsArgGroup.add_argument(
    "--iot-channel",
    required=False,
    help="Subscription channel for Maximo IoT"
)
masAppsArgGroup.add_argument(
    "--monitor-channel",
    required=False,
    help="Subscription channel for Maximo Monitor"
)
masAppsArgGroup.add_argument(
    "--manage-channel",
    required=False,
    help="Subscription channel for Maximo Manage"
)
masAppsArgGroup.add_argument(
    "--predict-channel",
    required=False,
    help="Subscription channel for Maximo Predict"
)
masAppsArgGroup.add_argument(
    "--visualinspection-channel",
    required=False,
    help="Subscription channel for Maximo Visual Inspection"
)
masAppsArgGroup.add_argument(
    "--optimizer-channel",
    required=False,
    help="Subscription channel for Maximo optimizer"
)
masAppsArgGroup.add_argument(
    "--optimizer-plan",
    required=False,
    choices=["full", "limited"],
    help="Install plan for Maximo Optimizer"
)
masAppsArgGroup.add_argument(
    "--facilities-channel",
    required=False,
    help="Subscription channel for Maximo Real Estate and Facilities"
)
masAppsArgGroup.add_argument(
    "--aiservice-channel",
    required=False,
    help="Subscription channel for Maximo AI Service"
)

# Arcgis
# -----------------------------------------------------------------------------
arcgisArgGroup = installArgParser.add_argument_group("Maximo Location Services for Esri (arcgis)")
arcgisArgGroup.add_argument(
    "--arcgis-channel",
    dest="mas_arcgis_channel",
    required=False,
    help="Subscription channel for IBM Maximo Location Services for Esri. Only applicable if installing Manage with Spatial or Facilities"
)

# Manage Advanced Settings
# -----------------------------------------------------------------------------
manageArgGroup = installArgParser.add_argument_group("Advanced Settings - Manage")
manageArgGroup.add_argument(
    "--manage-server-bundle-size",
    dest="mas_app_settings_server_bundles_size",
    required=False,
    help="Set Manage server bundle size configuration",
    choices=["dev", "snojms", "small", "jms"]
)
manageArgGroup.add_argument(
    "--manage-jms",
    dest="mas_app_settings_default_jms",
    required=False,
    help="Set JMS configuration",
    action="store_const",
    const="true"
)
manageArgGroup.add_argument(
    "--manage-persistent-volumes",
    dest="mas_app_settings_persistent_volumes_flag",
    required=False,
    help="",
    action="store_const",
    const="true"
)

manageArgGroup.add_argument(
    "--manage-jdbc",
    dest="mas_appws_bindings_jdbc_manage",
    required=False,
    help="",
    choices=["system", "workspace-application"]
)
manageArgGroup.add_argument(
    "--manage-demodata",
    dest="mas_app_settings_demodata",
    required=False,
    help="",
    action="store_const",
    const="true"
)
manageArgGroup.add_argument(
    "--manage-components",
    dest="mas_appws_components",
    required=False,
    help="Set Manage Components to be installed (e.g 'base=latest,health=latest,civil=latest')",
    default=""
)

manageArgGroup.add_argument(
    "--manage-health-wsl",
    dest="mas_appws_bindings_health_wsl_flag",
    required=False,
    help="Set boolean value indicating if Watson Studio must be bound to Manage. It is expected a system level WatsonStudioCfg applied in the cluster.",
    action="store_const",
    const="true"
)

manageArgGroup.add_argument(
    "--manage-customization-archive-name",
    dest="mas_app_settings_customization_archive_name",
    required=False,
    help="Manage Archive name"
)
manageArgGroup.add_argument(
    "--manage-customization-archive-url",
    dest="mas_app_settings_customization_archive_url",
    required=False,
    help="Manage Archive url"
)
manageArgGroup.add_argument(
    "--manage-customization-archive-username",
    dest="mas_app_settings_customization_archive_username",
    required=False,
    help="Manage Archive username (HTTP basic auth)"
)
manageArgGroup.add_argument(
    "--manage-customization-archive-password",
    dest="mas_app_settings_customization_archive_password",
    required=False,
    help="Manage Archive password (HTTP basic auth)"
)

manageArgGroup.add_argument(
    "--manage-db-tablespace",
    dest="mas_app_settings_tablespace",
    required=False,
    help="Database tablespace name that Manage will use to be installed. Default is 'MAXDATA'"
)
manageArgGroup.add_argument(
    "--manage-db-indexspace",
    dest="mas_app_settings_indexspace",
    required=False,
    help="Database indexspace name that Manage will use to be installed. Default is 'MAXINDEX'"
)
manageArgGroup.add_argument(
    "--manage-db-schema",
    dest="mas_app_settings_db2_schema",
    required=False,
    help="Database schema name that Manage will use to be installed. Default is 'maximo'"
)

manageArgGroup.add_argument(
    "--manage-crypto-key",
    dest="mas_manage_encryptionsecret_crypto_key",
    required=False,
    help="Customize Manage database encryption keys"
)
manageArgGroup.add_argument(
    "--manage-cryptox-key",
    dest="mas_manage_encryptionsecret_cryptox_key",
    required=False,
    help="Customize Manage database encryption keys"
)
manageArgGroup.add_argument(
    "--manage-old-crypto-key",
    dest="mas_manage_encryptionsecret_old_crypto_key",
    required=False,
    help="Customize Manage database encryption keys"
)
manageArgGroup.add_argument(
    "--manage-old-cryptox-key",
    dest="mas_manage_encryptionsecret_old_cryptox_key",
    required=False,
    help="Customize Manage database encryption keys"
)
manageArgGroup.add_argument(
    "--manage-encryption-secret-name",
    dest="mas_manage_ws_db_encryptionsecret",
    required=False,
    help="Name of the Manage database encryption secret"
)

manageArgGroup.add_argument(
    "--manage-base-language",
    dest="mas_app_settings_base_lang",
    required=False,
    help="Manage base language to be installed. Default is `EN` (English)"
)
manageArgGroup.add_argument(
    "--manage-secondary-languages",
    dest="mas_app_settings_secondary_langs",
    required=False,
    help="Comma-separated list of Manage secondary languages to be installed (e.g. 'JA,DE,AR')"
)
manageArgGroup.add_argument(
    "--manage-server-timezone",
    dest="mas_app_settings_server_timezone",
    required=False,
    help="Manage server timezone. Default is `GMT`"
)

manageArgGroup.add_argument(
    "--manage-upgrade-type",
    dest="mas_appws_upgrade_type",
    required=False,
    help="Set Manage upgrade type (default: regularUpgrade)",
    default="regularUpgrade",
    choices=UPGRADE_TYPES,
    metavar="{regularUpgrade,onlineUpgrade}"
)

# Manage Attachments
# -----------------------------------------------------------------------------
manageArgGroup.add_argument(
    "--manage-attachments-provider",
    dest="mas_manage_attachments_provider",
    required=False,
    help="Storage provider type for Maximo Manage attachments",
    choices=ATTACHMENT_PROVIDERS,
    metavar="{filestorage,ibm,aws}"
)
manageArgGroup.add_argument(
    "--manage-attachments-mode",
    dest="mas_manage_attachment_configuration_mode",
    required=False,
    help="How attachment properties will be configured in Manage",
    choices=ATTACHMENT_MODES,
    metavar="{cr,db}"
)

manageArgGroup.add_argument(
    "--manage-aiservice-instance-id",
    dest="manage_bind_aiservice_instance_id",
    required=False,
    help="AI Service Instance ID to bind with Manage"
)
manageArgGroup.add_argument(
    "--manage-aiservice-tenant-id",
    dest="manage_bind_aiservice_tenant_id",
    required=False,
    help="AI Service Tenant ID to bind with Manage"
)

# Facilities Advanced Settings
# -----------------------------------------------------------------------------
facilitiesArgGroup = installArgParser.add_argument_group(
    "Advanced Settings - Facilities",
    "Advanced configuration for Maximo Real Estate and Facilities including deployment size, image pull policy, routes timeout, Liberty extensions, vault secrets, workflow agents, connection pool size, and storage settings."
)
facilitiesArgGroup.add_argument(
    "--facilities-size",
    dest="mas_ws_facilities_size",
    required=False,
    help="Size of Facilities deployment",
    choices=FACILITIES_SIZES,
    metavar="{small,medium,large}"
)
facilitiesArgGroup.add_argument(
    "--facilities-pull-policy",
    dest="mas_ws_facilities_pull_policy",
    required=False,
    help="Image pull policy for Facilities",
    choices=IMAGE_PULL_POLICIES,
    metavar="{IfNotPresent,Always}"
)
facilitiesArgGroup.add_argument(
    "--facilities-routes-timeout",
    dest="mas_ws_facilities_routes_timeout",
    required=False,
    help="Timeout for Facilities routes (default: 600s)",
    default="600s"
)
facilitiesArgGroup.add_argument(
    "--facilities-xml-extension",
    dest="mas_ws_facilities_liberty_extension_XML",
    required=False,
    help="Secret name containing Liberty server extensions"
)
facilitiesArgGroup.add_argument(
    "--facilities-vault-secret",
    dest="mas_ws_facilities_vault_secret",
    required=False,
    help="Secret name containing AES encryption password"
)
facilitiesArgGroup.add_argument(
    "--facilities-dwfagent",
    dest="mas_ws_facilities_dwfagents",
    required=False,
    help="List of dedicated workflow agents",
    type=str
)
facilitiesArgGroup.add_argument(
    "--facilities-maxconnpoolsize",
    dest="mas_ws_facilities_db_maxconnpoolsize",
    required=False,
    help="Maximum database connection pool size (default: 200)",
    type=int,
    default=200
)
facilitiesArgGroup.add_argument(
    "--facilities-log-storage-class",
    dest="mas_ws_facilities_storage_log_class",
    required=False,
    help="Storage class for Facilities logs"
)
facilitiesArgGroup.add_argument(
    "--facilities-log-storage-mode",
    dest="mas_ws_facilities_storage_log_mode",
    required=False,
    help="Storage mode for Facilities logs"
)
facilitiesArgGroup.add_argument(
    "--facilities-log-storage-size",
    dest="mas_ws_facilities_storage_log_size",
    required=False,
    help="Storage size for Facilities logs"
)
facilitiesArgGroup.add_argument(
    "--facilities-userfiles-storage-class",
    dest="mas_ws_facilities_storage_userfiles_class",
    required=False,
    help="Storage class for Facilities user files"
)
facilitiesArgGroup.add_argument(
    "--facilities-userfiles-storage-mode",
    dest="mas_ws_facilities_storage_userfiles_mode",
    required=False,
    help="Storage mode for Facilities user files"
)
facilitiesArgGroup.add_argument(
    "--facilities-userfiles-storage-size",
    dest="mas_ws_facilities_storage_userfiles_size",
    required=False,
    help="Storage size for Facilities user files"
)

# Open Data Hub
# -----------------------------------------------------------------------------
odhArgGroup = installArgParser.add_argument_group("Open Data Hub")

odhArgGroup.add_argument(
    "--odh-model-deployment-type",
    dest="aiservice_odh_model_deployment_type",
    required=False,
    default="raw",
    help="Model deployment type for ODH"
)

# S3 Storage
# -----------------------------------------------------------------------------
aiServiceS3ArgGroup = installArgParser.add_argument_group(
    "S3 Storage",
    "Configure S3-compatible object storage for AI Service including Minio installation or external S3 connection details (host, port, SSL, credentials, bucket, and region)."
)
aiServiceS3ArgGroup.add_argument(
    "--install-minio",
    dest="install_minio_aiservice",
    required=False,
    help="Install Minio and configure it as the S3 provider for AI Service",
    action="store_const",
    const="true"
)

# S3 - Minio
# -----------------------------------------------------------------------------
aiServiceS3ArgGroup.add_argument(
    "--minio-root-user",
    dest="minio_root_user",
    required=False,
    help="Root user for minio"
)
aiServiceS3ArgGroup.add_argument(
    "--minio-root-password",
    dest="minio_root_password",
    required=False,
    help="Password for minio root user"
)

# S3 - External Connection
# -----------------------------------------------------------------------------
aiServiceS3ArgGroup.add_argument(
    "--s3-host",
    dest="aiservice_s3_host",
    required=False,
    help="Hostname or IP address of the S3 storage service"
)
aiServiceS3ArgGroup.add_argument(
    "--s3-port",
    dest="aiservice_s3_port",
    required=False,
    help="Port number for the S3 storage service"
)
aiServiceS3ArgGroup.add_argument(
    "--s3-ssl",
    dest="aiservice_s3_ssl",
    required=False,
    help="Enable or disable SSL for S3 connection (true/false)"
)
aiServiceS3ArgGroup.add_argument(
    "--s3-accesskey",
    dest="aiservice_s3_accesskey",
    required=False,
    help="Access key for authenticating with the S3 storage service"
)
aiServiceS3ArgGroup.add_argument(
    "--s3-secretkey",
    dest="aiservice_s3_secretkey",
    required=False,
    help="Secret key for authenticating with the S3 storage service"
)
aiServiceS3ArgGroup.add_argument(
    "--s3-region",
    dest="aiservice_s3_region",
    required=False,
    help="Region for the S3 storage service"
)
aiServiceS3ArgGroup.add_argument(
    "--s3-bucket-prefix",
    dest="aiservice_s3_bucket_prefix",
    required=False,
    help="Bucket prefix configured with S3 storage service"
)

# S3 - Bucket Naming
# -----------------------------------------------------------------------------
aiServiceS3ArgGroup.add_argument(
    "--s3-tenants-bucket",
    dest="aiservice_s3_tenants_bucket",
    required=False,
    default="km-tenants",
    help="Name of the S3 bucket for tenants storage"
)
aiServiceS3ArgGroup.add_argument(
    "--s3-templates-bucket",
    dest="aiservice_s3_templates_bucket",
    required=False,
    default="km-templates",
    help="Name of the S3 bucket for templates storage"
)

# Watsonx
# -----------------------------------------------------------------------------
aiServiceWatsonxArgGroup = installArgParser.add_argument_group(
    "Watsonx",
    "Configure IBM Watsonx integration for AI Service including API key, instance ID, project ID, and service URL."
)

aiServiceWatsonxArgGroup.add_argument(
    "--watsonxai-apikey",
    dest="aiservice_watsonxai_apikey",
    required=False,
    help="API key for WatsonX"
)
aiServiceWatsonxArgGroup.add_argument(
    "--watsonxai-url",
    dest="aiservice_watsonxai_url",
    required=False,
    help="URL endpoint for WatsonX"
)
aiServiceWatsonxArgGroup.add_argument(
    "--watsonxai-project-id",
    dest="aiservice_watsonxai_project_id",
    required=False,
    help="Project ID for WatsonX"
)
aiServiceWatsonxArgGroup.add_argument(
    "--watsonx-action",
    dest="aiservice_watsonx_action",
    required=False,
    help="Action to perform with WatsonX (install/remove)"
)
aiServiceWatsonxArgGroup.add_argument(
    "--watsonxai-ca-crt",
    dest="aiservice_watsonxai_ca_crt",
    required=False,
    help="CA certificate for WatsonX AI (PEM format, optional, only if using self-signed certs)"
)
aiServiceWatsonxArgGroup.add_argument(
    "--watsonxai-deployment-id",
    dest="aiservice_watsonxai_deployment_id",
    required=False,
    help="WatsonX deployment ID"
)
aiServiceWatsonxArgGroup.add_argument(
    "--watsonxai-space-id",
    dest="aiservice_watsonxai_space_id",
    required=False,
    help="WatsonX space ID"
)
aiServiceWatsonxArgGroup.add_argument(
    "--watsonxai-instance-id",
    dest="aiservice_watsonxai_instance_id",
    required=False,
    help="WatsonX instance ID"
)
aiServiceWatsonxArgGroup.add_argument(
    "--watsonxai-username",
    dest="aiservice_watsonxai_username",
    required=False,
    help="WatsonX username"
)
aiServiceWatsonxArgGroup.add_argument(
    "--watsonxai-version",
    dest="aiservice_watsonxai_version",
    required=False,
    help="WatsonX version"
)
aiServiceWatsonxArgGroup.add_argument(
    "--watsonxai-onprem",
    dest="aiservice_watsonxai_on_prem",
    required=False,
    help="WatsonX deployed on prem"
)

# AI Service Tenant
# -----------------------------------------------------------------------------
aiServiceTenantArgGroup = installArgParser.add_argument_group("Maximo AI Service Tenant")

aiServiceTenantArgGroup.add_argument(
    "--tenant-entitlement-type",
    dest="tenant_entitlement_type",
    required=False,
    default="standard",
    help="Entitlement type for AI Service tenant"
)
aiServiceTenantArgGroup.add_argument(
    "--tenant-entitlement-start-date",
    dest="tenant_entitlement_start_date",
    required=False,
    help="Start date for AI Service tenant"
)
aiServiceTenantArgGroup.add_argument(
    "--tenant-entitlement-end-date",
    dest="tenant_entitlement_end_date",
    required=False,
    help="End date for AI Service tenant"
)
aiServiceTenantArgGroup.add_argument(
    "--rsl-url",
    dest="rsl_url",
    required=False,
    help="rsl url"
)
aiServiceTenantArgGroup.add_argument(
    "--rsl-org-id",
    dest="rsl_org_id",
    required=False,
    help="org id for rsl"
)
aiServiceTenantArgGroup.add_argument(
    "--rsl-token",
    dest="rsl_token",
    required=False,
    help="token for rsl"
)
aiServiceTenantArgGroup.add_argument(
    "--rsl-ca-crt",
    dest="rsl_ca_crt",
    required=False,
    help="CA certificate for RSL API (PEM format, optional, only if using self-signed certs)"
)

# AI Service Configuration
# -----------------------------------------------------------------------------
aiServiceArgGroup = installArgParser.add_argument_group(
    "Maximo AI Service",
    "Maximo AI Service configuration such as certificate Issuer, environment type"
)
aiServiceArgGroup.add_argument(
    "--environment-type",
    dest="environment_type",
    required=False,
    default="non-production",
    help="Environment type (default: non-production)"
)
aiServiceArgGroup.add_argument(
    "--aiservice-certificate-issuer",
    dest="aiservice_certificate_issuer",
    required=False,
    help="Provide the name of the Issuer to configure AI Service to issue certificates",
)

# IBM Cloud Pak for Data
# -----------------------------------------------------------------------------
cpdAppsArgGroup = installArgParser.add_argument_group(
    "IBM Cloud Pak for Data",
    "Configure IBM Cloud Pak for Data applications including Watson Studio, Watson Machine Learning, Watson Discovery, Analytics Engine (Spark), Cognos Analytics, SPSS Modeler, and Canvas Base."
)
cpdAppsArgGroup.add_argument(
    "--cp4d-version",
    dest="cpd_product_version",
    required=False,
    help="Product version of CP4D to use"
)
cpdAppsArgGroup.add_argument(
    "--cp4d-install-cognos",
    dest="cpd_install_cognos",
    required=False,
    help="Add Cognos as part of Cloud Pak for Data",
    action="store_const",
    const="install"
)
cpdAppsArgGroup.add_argument(
    "--cp4d-install-ws",
    dest="cpd_install_ws",
    required=False,
    help="Add Watson Studio as part of Cloud Pak for Data",
    action="store_const",
    const="install"
)
cpdAppsArgGroup.add_argument(
    "--cp4d-install-wml",
    dest="cpd_install_wml",
    required=False,
    help="Add Watson Machine Learning as part of Cloud Pak for Data",
    action="store_const",
    const="install"
)
cpdAppsArgGroup.add_argument(
    "--cp4d-install-ae",
    dest="cpd_install_ae",
    required=False,
    help="Add Spark Analytics Engine as part of Cloud Pak for Data",
    action="store_const",
    const="install"
)

# IBM Db2 Universal Operator
# -----------------------------------------------------------------------------
db2ArgGroup = installArgParser.add_argument_group(
    "IBM Db2 Universal Operator",
    "Configure IBM Db2 instances including namespace, channel, installation options for system/manage/facilities databases, database type, timezone, affinity, tolerations, resource limits, and storage capacity."
)
db2ArgGroup.add_argument(
    "--db2-namespace",
    required=False,
    help="Change namespace where Db2u instances will be created"
)
db2ArgGroup.add_argument(
    "--db2-channel",
    required=False,
    help="Subscription channel for Db2u"
)
db2ArgGroup.add_argument(
    "--db2-system",
    dest="db2_action_system",
    required=False,
    help="Install a shared Db2u instance for MAS (required by IoT & Monitor, supported by Manage)",
    action="store_const",
    const="install"
)
db2ArgGroup.add_argument(
    "--db2-manage",
    dest="db2_action_manage",
    required=False,
    help="Install a dedicated Db2u instance for Maximo Manage (supported by Manage)",
    action="store_const",
    const="install"
)
db2ArgGroup.add_argument(
    "--db2-facilities",
    dest="db2_action_facilities",
    required=False,
    help="Install a dedicated Db2u instance for Maximo Real Estate and Facilities (supported by Facilities)",
    action="store_const",
    const="install"
)
db2ArgGroup.add_argument(
    "--db2-type",
    required=False,
    help="Type of Manage dedicated Db2u instance (default: db2wh)",
    choices=DB2_TYPES,
    metavar="{db2wh,db2oltp}"
)
db2ArgGroup.add_argument(
    "--db2-timezone",
    required=False,
    help="Timezone for Db2 instance"
)
db2ArgGroup.add_argument(
    "--db2-affinity-key",
    required=False,
    help="Set a node label to declare affinity to"
)
db2ArgGroup.add_argument(
    "--db2-affinity-value",
    required=False,
    help="Set the value of the node label to affine with"
)
db2ArgGroup.add_argument(
    "--db2-tolerate-key",
    required=False,
    help="Set a node taint to tolerate"
)
db2ArgGroup.add_argument(
    "--db2-tolerate-value",
    required=False,
    help="Set the value of the taint to tolerate"
)
db2ArgGroup.add_argument(
    "--db2-tolerate-effect",
    required=False,
    help="Taint effect to tolerate",
    choices=TAINT_EFFECTS,
    metavar="{NoSchedule,PreferNoSchedule,NoExecute}"
)
db2ArgGroup.add_argument(
    "--db2-cpu-requests",
    required=False,
    help="Customize Db2 CPU request"
)
db2ArgGroup.add_argument(
    "--db2-cpu-limits",
    required=False,
    help="Customize Db2 CPU limit"
)
db2ArgGroup.add_argument(
    "--db2-memory-requests",
    required=False,
    help="Customize Db2 memory request"
)
db2ArgGroup.add_argument(
    "--db2-memory-limits",
    required=False,
    help="Customize Db2 memory limit"
)
db2ArgGroup.add_argument(
    "--db2-backup-storage",
    dest="db2_backup_storage_size",
    required=False,
    help="Db2 backup storage capacity"
)
db2ArgGroup.add_argument(
    "--db2-data-storage",
    dest="db2_data_storage_size",
    required=False,
    help="Db2 data storage capacity"
)
db2ArgGroup.add_argument(
    "--db2-logs-storage",
    dest="db2_logs_storage_size",
    required=False,
    help="Db2 logs storage capacity"
)
db2ArgGroup.add_argument(
    "--db2-meta-storage",
    dest="db2_meta_storage_size",
    required=False,
    help="Db2 metadata storage capacity"
)
db2ArgGroup.add_argument(
    "--db2-temp-storage",
    dest="db2_temp_storage_size",
    required=False,
    help="Db2 temporary storage capacity"
)

# ECK Integration
# -----------------------------------------------------------------------------
eckArgGroup = installArgParser.add_argument_group(
    "ECK Integration",
    "Configure Elastic Cloud on Kubernetes (ECK) integration for logging and monitoring capabilities."
)
eckArgGroup.add_argument(
    "--eck",
    dest="eck_action",
    required=False,
    help="",
    action="store_const",
    const="install"
)
eckArgGroup.add_argument(
    "--eck-enable-logstash",
    required=False,
    help="",
    action="store_true"
)
eckArgGroup.add_argument(
    "--eck-remote-es-hosts",
    required=False,
    help=""
)
eckArgGroup.add_argument(
    "--eck-remote-es-username",
    required=False,
    help=""
)
eckArgGroup.add_argument(
    "--eck-remote-es-password",
    required=False,
    help=""
)

# Kafka - Common
# -----------------------------------------------------------------------------
kafkaCommonArgGroup = installArgParser.add_argument_group(
    "Kafka - Common",
    "Common Kafka configuration options including provider selection (Strimzi, Red Hat AMQ Streams, IBM Event Streams, or AWS MSK) and authentication credentials."
)
kafkaCommonArgGroup.add_argument(
    "--kafka-provider",
    required=False,
    help="Kafka provider: redhat (Red Hat AMQ Streams), strimzi, ibm (IBM Event Streams), or aws (AWS MSK)",
    choices=KAFKA_PROVIDERS,
    metavar="{strimzi,redhat,ibm,aws}"
)
kafkaCommonArgGroup.add_argument(
    "--kafka-username",
    required=False,
    help="Kafka instance username (applicable for redhat, strimzi, or aws providers)"
)
kafkaCommonArgGroup.add_argument(
    "--kafka-password",
    required=False,
    help="Kafka instance password (applicable for redhat, strimzi, or aws providers)"
)

# Kafka - Strimzi & AMQ Streams
# -----------------------------------------------------------------------------
kafkaOCPArgGroup = installArgParser.add_argument_group(
    "Kafka - Strimzi and AMQ Streams",
    "Configuration options specific to Strimzi and Red Hat AMQ Streams Kafka deployments including namespace and cluster version."
)
kafkaCommonArgGroup.add_argument(
    "--kafka-namespace",
    required=False,
    help="Set Kafka namespace. Only applicable if installing `redhat` (Red Hat AMQ Streams) or `strimzi`"
)
kafkaOCPArgGroup.add_argument(
    "--kafka-version",
    required=False,
    help="Set version of the Kafka cluster that the Strimzi or AMQ Streams operator will create"
)

# Kafka - AWS MSK
# -----------------------------------------------------------------------------
mskArgGroup = installArgParser.add_argument_group(
    "Kafka - AWS MSK",
    "Configuration options for Amazon Managed Streaming for Apache Kafka (MSK) including instance type, node count, volume size, CIDR subnets for availability zones, and egress settings."
)
mskArgGroup.add_argument(
    "--msk-instance-type",
    dest="aws_msk_instance_type",
    required=False,
    help="Set the MSK instance type"
)
mskArgGroup.add_argument(
    "--msk-instance-nodes",
    dest="aws_msk_instance_number",
    required=False,
    help="Set total number of MSK instance nodes"
)
mskArgGroup.add_argument(
    "--msk-instance-volume-size",
    dest="aws_msk_volume_size",
    required=False,
    help="Set storage/volume size for the MSK instance"
)
mskArgGroup.add_argument(
    "--msk-cidr-az1",
    dest="aws_msk_cidr_az1",
    required=False,
    help="Set the CIDR subnet for availability zone 1 for the MSK instance"
)
mskArgGroup.add_argument(
    "--msk-cidr-az2",
    dest="aws_msk_cidr_az2",
    required=False,
    help="Set the CIDR subnet for availability zone 2 for the MSK instance"
)
mskArgGroup.add_argument(
    "--msk-cidr-az3",
    dest="aws_msk_cidr_az3",
    required=False,
    help="Set the CIDR subnet for availability zone 3 for the MSK instance"
)
mskArgGroup.add_argument(
    "--msk-cidr-egress",
    dest="aws_msk_egress_cidr",
    required=False,
    help="Set the CIDR for egress connectivity"
)
mskArgGroup.add_argument(
    "--msk-cidr-ingress",
    dest="aws_msk_ingress_cidr",
    required=False,
    help="Set the CIDR for ingress connectivity"
)

# Kafka - Event Streams
# -----------------------------------------------------------------------------
eventstreamsArgGroup = installArgParser.add_argument_group(
    "Kafka - Event Streams",
    "Configuration options for IBM Event Streams including resource group, instance name, and location."
)
eventstreamsArgGroup.add_argument(
    "--eventstreams-resource-group",
    dest="eventstreams_resourcegroup",
    required=False,
    help="Set IBM Cloud resource group to target the Event Streams instance provisioning"
)
eventstreamsArgGroup.add_argument(
    "--eventstreams-instance-name",
    dest="eventstreams_name",
    required=False,
    help="Set IBM Event Streams instance name"
)
eventstreamsArgGroup.add_argument(
    "--eventstreams-instance-location",
    dest="eventstreams_location",
    required=False,
    help="Set IBM Event Streams instance location"
)

# COS
# -----------------------------------------------------------------------------
cosArgGroup = installArgParser.add_argument_group("Cloud Object Storage")
cosArgGroup.add_argument(
    "--cos",
    dest="cos_type",
    required=False,
    help="Set cloud object storage provider.  Supported options are `ibm` and `ocs`",
    choices=["ibm", "ocs"]
)
cosArgGroup.add_argument(
    "--cos-resourcegroup",
    dest="cos_resourcegroup",
    required=False,
    help="When using IBM COS, set the resource group where the instance will run"
)
cosArgGroup.add_argument(
    "--cos-apikey",
    dest="cos_apikey",
    required=False,
    help="When using IBM COS, set COS priviledged apikey for IBM Cloud"
)
cosArgGroup.add_argument(
    "--cos-instance-name",
    dest="cos_instance_name",
    required=False,
    help="When using IBM COS, set COS instance name to be used/created"
)
cosArgGroup.add_argument(
    "--cos-bucket-name",
    dest="cos_bucket_name",
    required=False,
    help="When using IBM COS, set COS bucket name to be used/created"
)


# Cloud Providers
# -----------------------------------------------------------------------------
cloudArgGroup = installArgParser.add_argument_group(
    "Cloud Providers",
    "Configure cloud provider settings including AWS region, availability zones, and IBM Cloud API key."
)
cloudArgGroup.add_argument(
    "--ibmcloud-apikey",
    required=False,
    help="Set IBM Cloud API Key"
)
cloudArgGroup.add_argument(
    "--aws-region",
    required=False,
    help="Set target AWS region for the MSK instance"
)
cloudArgGroup.add_argument(
    "--aws-access-key-id",
    required=False,
    help="Set AWS access key ID for the target AWS account"
)
cloudArgGroup.add_argument(
    "--secret-access-key",
    required=False,
    help="Set AWS secret access key for the target AWS account"
)
cloudArgGroup.add_argument(
    "--aws-vpc-id",
    required=False,
    help="Set target Virtual Private Cloud ID for the MSK instance"
)

# Approvals
# -----------------------------------------------------------------------------
approvalsGroup = installArgParser.add_argument_group(
    "Integrated Approval Workflow",
    "Configure approval checkpoints during installation for Core Platform and each MAS application workspace (Assist, IoT, Manage, Monitor, Optimizer, Predict, Visual Inspection, Facilities, and AI Service). Format: MAX_RETRIES:RETRY_DELAY:IGNORE_FAILURE"
)
approvalsGroup.add_argument(
    "--approval-core",
    default="",
    help="Require approval after the Core Platform has been configured"
)
approvalsGroup.add_argument(
    "--approval-assist",
    default="",
    help="Require approval after the Maximo Assist workspace has been configured"
)
approvalsGroup.add_argument(
    "--approval-iot",
    default="",
    help="Require approval after the Maximo IoT workspace has been configured"
)
approvalsGroup.add_argument(
    "--approval-manage",
    default="",
    help="Require approval after the Maximo Manage workspace has been configured"
)
approvalsGroup.add_argument(
    "--approval-monitor",
    default="",
    help="Require approval after the Maximo Monitor workspace has been configured"
)
approvalsGroup.add_argument(
    "--approval-optimizer",
    default="",
    help="Require approval after the Maximo Optimizer workspace has been configured"
)
approvalsGroup.add_argument(
    "--approval-predict",
    default="",
    help="Require approval after the Maximo Predict workspace has been configured"
)
approvalsGroup.add_argument(
    "--approval-visualinspection",
    default="",
    help="Require approval after the Maximo Visual Inspection workspace has been configured"
)
approvalsGroup.add_argument(
    "--approval-facilities",
    default="",
    help="Require approval after the Maximo Real Estate and Facilities workspace has been configured"
)
approvalsGroup.add_argument(
    "--approval-aiservice",
    default="",
    help="Require approval after the AI Service has been configured"
)

# More Options
# -----------------------------------------------------------------------------
otherArgGroup = installArgParser.add_argument_group(
    "More",
    "Additional options including advanced/simplified mode toggles, license acceptance, development mode, Artifactory credentials, PVC wait control, pre-check skip, Grafana installation, confirmation prompts, image pull policy, and custom service account."
)
otherArgGroup.add_argument(
    "--artifactory-username",
    required=False,
    help="Username for access to development builds on Artifactory"
)
otherArgGroup.add_argument(
    "--artifactory-token",
    required=False,
    help="API Token for access to development builds on Artifactory"
)
otherArgGroup.add_argument(
    "--advanced",
    action="store_true",
    default=False,
    help="Show advanced install options (in interactive mode)"
)
otherArgGroup.add_argument(
    "--simplified",
    action="store_true",
    default=False,
    help="Don't show advanced install options (in interactive mode)"
)

otherArgGroup.add_argument(
    "--accept-license",
    action="store_true",
    default=False,
    help="Accept all license terms without prompting"
)
otherArgGroup.add_argument(
    "--dev-mode",
    required=False,
    action="store_true",
    default=False,
    help="Configure installation for development mode"
)
otherArgGroup.add_argument(
    "--skip-pre-check",
    required=False,
    action="store_true",
    help="Disable the 'pre-install-check' at the start of the install pipeline"
)
otherArgGroup.add_argument(
    "--skip-grafana-install",
    required=False,
    action="store_true",
    help="Skip Grafana installation"
)
otherArgGroup.add_argument(
    "--no-confirm",
    required=False,
    action="store_true",
    default=False,
    help="Launch the installation without prompting for confirmation"
)
otherArgGroup.add_argument(
    "--image-pull-policy",
    dest="image_pull_policy",
    required=False,
    help="Image pull policy for Tekton Pipeline",
    choices=IMAGE_PULL_POLICIES,
    metavar="{IfNotPresent,Always}"
)
otherArgGroup.add_argument(
    "--service-account",
    dest="service_account_name",
    required=False,
    help="Custom service account for install pipeline (disables default 'pipeline' service account creation)"
)

otherArgGroup.add_argument(
    "-h", "--help",
    action="help",
    default=False,
    help="Show this help message and exit"
)
