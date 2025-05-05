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


def isValidFile(parser, arg) -> str:
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
catArgGroup = installArgParser.add_argument_group("MAS Catalog Selection & Entitlement")
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

# MAS Basic Configuration
# -----------------------------------------------------------------------------
masArgGroup = installArgParser.add_argument_group("MAS Basic Configuration")
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
# MAS Special characters
# -----------------------------------------------------------------------------
masSpecialCharacters = installArgParser.add_argument_group("Mas Special Characters")
masSpecialCharacters.add_argument(
    "--allow-special-chars",
    dest="mas_special_characters",
    required=False,
    help="Allow special chars for users username/ID",
    action="store_true"
)
# ECK Integration
# -----------------------------------------------------------------------------
eckArgGroup = installArgParser.add_argument_group("ECK Integration")
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

# MAS Advanced Configuration
# -----------------------------------------------------------------------------
masAdvancedArgGroup = installArgParser.add_argument_group("MAS Advanced Configuration")
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
    help="Enable Automatic DNS management (see DNS Configuration options)",
    choices=["cloudflare", "cis", "route53"]
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

# DNS Configuration - IBM CIS
# -----------------------------------------------------------------------------
cisArgGroup = installArgParser.add_argument_group("DNS Configuration - CIS")
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

# Storage
# -----------------------------------------------------------------------------
storageArgGroup = installArgParser.add_argument_group("Storage")
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
    help="Install pipeline storage class access mode (ReadWriteMany or ReadWriteOnce)",
    choices=["ReadWriteMany", "ReadWriteOnce"]
)

# IBM Suite License Service
# -----------------------------------------------------------------------------
slsArgGroup = installArgParser.add_argument_group("IBM Suite License Service")
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

# IBM Data Reporting Operator (DRO)
# -----------------------------------------------------------------------------
droArgGroup = installArgParser.add_argument_group("IBM Data Reporting Operator (DRO)")
droArgGroup.add_argument(
    "--uds-email",
    dest="uds_contact_email",
    required=False,
    help="Contact e-mail address"
)
droArgGroup.add_argument(
    "--uds-firstname",
    dest="uds_contact_firstname",
    required=False,
    help="Contact first name"
)
droArgGroup.add_argument(
    "--uds-lastname",
    dest="uds_contact_lastname",
    required=False,
    help="Contact last name"
)
droArgGroup.add_argument(
    "--dro-namespace",
    required=False,
    help=""
)

# MongoDb Community Operator
# -----------------------------------------------------------------------------
mongoArgGroup = installArgParser.add_argument_group("MongoDb Community Operator")
mongoArgGroup.add_argument(
    "--mongodb-namespace",
    required=False,
    help=""
)

# OCP Configuration
# -----------------------------------------------------------------------------
ocpArgGroup = installArgParser.add_argument_group("OCP Configuration")
ocpArgGroup.add_argument(
    "--ocp-ingress-tls-secret-name",
    required=False,
    help="Name of the secret holding the cluster's ingress certificates"
)

# MAS Applications
# -----------------------------------------------------------------------------
masAppsArgGroup = installArgParser.add_argument_group("MAS Applications")
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
    "--is-full-manage",
    required=False,
    help="Full Manage instead of Manage Foundation"
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
    "--aibroker-channel",
    required=False,
    help="Subscription channel for Maximo Ai Broker"
)

# AI Broker
# -----------------------------------------------------------------------------
aibrokerArgGroup = installArgParser.add_argument_group("Maximo AI Broker")
aibrokerArgGroup.add_argument(
    "--mas-aibroker-storage-provider",
    dest="mas_aibroker_storage_provider",
    required=False,
    help="Customize Manage database encryption keys"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-storage-accesskey",
    dest="mas_aibroker_storage_accesskey",
    required=False,
    help="Customize Manage database encryption keys"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-storage-secretkey",
    dest="mas_aibroker_storage_secretkey",
    required=False,
    help="Customize Manage database encryption keys"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-storage-host",
    dest="mas_aibroker_storage_host",
    required=False,
    help="Customize Manage database encryption keys"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-storage-port",
    dest="mas_aibroker_storage_port",
    required=False,
    help="Customize Manage database encryption keys"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-storage-ssl",
    dest="mas_aibroker_storage_ssl",
    required=False,
    help="Customize Manage database encryption keys"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-storage-region",
    dest="mas_aibroker_storage_region",
    required=False,
    help="Customize Manage database encryption keys"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-storage-pipelines-bucket",
    dest="mas_aibroker_storage_pipelines_bucket",
    required=False,
    help="Customize Manage database encryption keys"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-storage-tenants-bucket",
    dest="mas_aibroker_storage_tenants_bucket",
    required=False,
    help="Customize Manage database encryption keys"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-storage-templates-bucket",
    dest="mas_aibroker_storage_templates_bucket",
    required=False,
    help="Customize Manage database encryption keys"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-tenant-name",
    dest="mas_aibroker_tenant_name",
    required=False,
    help="Customize Manage database encryption keys"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-watsonxai-apikey",
    dest="mas_aibroker_watsonxai_apikey",
    required=False,
    help="Customize Manage database encryption keys"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-watsonxai-url",
    dest="mas_aibroker_watsonxai_url",
    required=False,
    help="Customize Manage database encryption keys"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-watsonxai-project-id",
    dest="mas_aibroker_watsonxai_project_id",
    required=False,
    help="Customize Manage database encryption keys"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-watsonx-action",
    dest="mas_aibroker_watsonx_action",
    required=False,
    help="Customize Manage database encryption keys"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-db-host",
    dest="mas_aibroker_db_host",
    required=False,
    help="Customize Manage database encryption keys"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-db-port",
    dest="mas_aibroker_db_port",
    required=False,
    help="Customize Manage database encryption keys"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-db-user",
    dest="mas_aibroker_db_user",
    required=False,
    help="Customize Manage database encryption keys"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-db-database",
    dest="mas_aibroker_db_database",
    required=False,
    help="Customize Manage database encryption keys"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-db-secret-name",
    dest="mas_aibroker_db_secret_name",
    required=False,
    help="Customize Manage database encryption keys"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-db-secret-key",
    dest="mas_aibroker_db_secret_key",
    required=False,
    help="Customize Manage database encryption keys"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-db-secret-value",
    dest="mas_aibroker_db_secret_value",
    required=False,
    help="Customize Manage database encryption keys"
)

# Arcgis
# -----------------------------------------------------------------------------
arcgisArgGroup = installArgParser.add_argument_group("Maximo Location Services for Esri (arcgis)")
arcgisArgGroup.add_argument(
    "--install-arcgis",
    required=False,
    help="Enables IBM Maximo Location Services for Esri. Only applicable if installing Manage with Spatial",
    action="store_const",
    const="true"
)
arcgisArgGroup.add_argument(
    "--arcgis-channel",
    dest="mas_arcgis_channel",
    required=False,
    help=""
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
    default="base=latest,health=latest"
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
    dest="mas_app_settings_crypto_key",
    required=False,
    help="Customize Manage database encryption keys"
)
manageArgGroup.add_argument(
    "--manage-cryptox-key",
    dest="mas_app_settings_cryptox_key",
    required=False,
    help="Customize Manage database encryption keys"
)
manageArgGroup.add_argument(
    "--manage-old-crypto-key",
    dest="mas_app_settings_old_crypto_key",
    required=False,
    help="Customize Manage database encryption keys"
)
manageArgGroup.add_argument(
    "--manage-old-cryptox-key",
    dest="mas_app_settings_old_cryptox_key",
    required=False,
    help="Customize Manage database encryption keys"
)
manageArgGroup.add_argument(
    "--manage-override-encryption-secrets",
    dest="mas_app_settings_override_encryption_secrets_flag",
    required=False,
    help="Override any existing Manage database encryption keys. A backup of the original secret holding existing encryption keys is taken prior overriding it with the new defined keys",
    action="store_const",
    const="true"
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

# Manage Attachments
# -----------------------------------------------------------------------------
manageArgGroup.add_argument(
    "--manage-attachments-provider",
    dest="mas_manage_attachments_provider",
    required=False,
    help="Defines the storage provider type to be used to store attachments in Maximo Manage. Supported options are `filestorage`, `ibm` and `aws`.",
    choices=["filestorage", "ibm", "aws"]
)
manageArgGroup.add_argument(
    "--manage-attachments-mode",
    dest="mas_manage_attachment_configuration_mode",
    required=False,
    help="Defines how attachment properties will be configured in Manage. Possible values are: cr and db",
    choices=["cr", "db"]
)

# IBM Cloud Pak for Data
# -----------------------------------------------------------------------------
cpdAppsArgGroup = installArgParser.add_argument_group("IBM Cloud Pak for Data")
cpdAppsArgGroup.add_argument(
    "--cp4d-version",
    dest="cpd_product_version",
    required=False,
    help="Product version of CP4D to use"
)
cpdAppsArgGroup.add_argument(
    "--cp4d-install-spss",
    dest="cpd_install_spss",
    required=False,
    help="Add SPSS Modeler as part of Cloud Pak for Data",
    action="store_const",
    const="install"
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
db2ArgGroup = installArgParser.add_argument_group("IBM Db2 Universal Operator")
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
    "--db2-type",
    required=False,
    help="Choose the type of the Manage dedicated Db2u instance. Available options are `db2wh` (default) or `db2oltp`"
)
db2ArgGroup.add_argument(
    "--db2-timezone",
    required=False,
    help=""
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
    help="Set the effect that will be tolerated (NoSchedule, PreferNoSchedule, or NoExecute)"
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
    help="Customize Db2 storage capacity"
)
db2ArgGroup.add_argument(
    "--db2-data-storage",
    dest="db2_data_storage_size",
    required=False,
    help="Customize Db2 storage capacity"
)
db2ArgGroup.add_argument(
    "--db2-logs-storage",
    dest="db2_logs_storage_size",
    required=False,
    help="Customize Db2 storage capacity"
)
db2ArgGroup.add_argument(
    "--db2-meta-storage",
    dest="db2_meta_storage_size",
    required=False,
    help="Customize Db2 storage capacity"
)
db2ArgGroup.add_argument(
    "--db2-temp-storage",
    dest="db2_temp_storage_size",
    required=False,
    help="Customize Db2 storage capacity"
)

# Kafka - Common
# -----------------------------------------------------------------------------
kafkaCommonArgGroup = installArgParser.add_argument_group("Kafka - Common")
kafkaCommonArgGroup.add_argument(
    "--kafka-provider",
    required=False,
    help="Set Kafka provider.  Supported options are `redhat` (Red Hat AMQ Streams), `strimzi` and `ibm` (IBM Event Streams) and `aws` (AWS MSK)",
    choices=["strimzi", "redhat", "ibm", "aws"]
)
kafkaCommonArgGroup.add_argument(
    "--kafka-username",
    required=False,
    help="Set Kafka instance username. Only applicable if installing `redhat` (Red Hat AMQ Streams), `strimzi` or `aws` (AWS MSK)"
)
kafkaCommonArgGroup.add_argument(
    "--kafka-password",
    required=False,
    help="Set Kafka instance password. Only applicable if installing `redhat` (Red Hat AMQ Streams), `strimzi` or `aws` (AWS MSK)"
)

# Kafka - Strimzi & AMQ Streams
# -----------------------------------------------------------------------------
kafkaOCPArgGroup = installArgParser.add_argument_group("Kafka - Strimzi and AMQ Streams")
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

# Kafka - MSK
# -----------------------------------------------------------------------------
mskArgGroup = installArgParser.add_argument_group("Kafka - AWS MSK")
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
eventstreamsArgGroup = installArgParser.add_argument_group("Kafka - Event Streams")
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

# Turbonomic Integration
# -----------------------------------------------------------------------------
turboArgGroup = installArgParser.add_argument_group("Turbonomic Integration")
turboArgGroup.add_argument(
    "--turbonomic-name",
    dest="turbonomic_target_name",
    required=False,
    help=""
)
turboArgGroup.add_argument(
    "--turbonomic-url",
    dest="turbonomic_server_url",
    required=False,
    help=""
)
turboArgGroup.add_argument(
    "--turbonomic-version",
    dest="turbonomic_server_version",
    required=False,
    help=""
)
turboArgGroup.add_argument(
    "--turbonomic-username",
    dest="turbonomic_username",
    required=False,
    help=""
)
turboArgGroup.add_argument(
    "--turbonomic-password",
    dest="turbonomic_password",
    required=False,
    help=""
)

# Cloud Providers
# -----------------------------------------------------------------------------
cloudArgGroup = installArgParser.add_argument_group("Cloud Providers")
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

# Development Mode
# -----------------------------------------------------------------------------
devArgGroup = installArgParser.add_argument_group("Development Mode")
devArgGroup.add_argument(
    "--artifactory-username",
    required=False,
    help="Username for access to development builds on Artifactory"
)
devArgGroup.add_argument(
    "--artifactory-token",
    required=False,
    help="API Token for access to development builds on Artifactory"
)

# Approvals
# -----------------------------------------------------------------------------
approvalsGroup = installArgParser.add_argument_group("Integrated Approval Workflow (MAX_RETRIES:RETRY_DELAY:IGNORE_FAILURE)")
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


# More Options
# -----------------------------------------------------------------------------
otherArgGroup = installArgParser.add_argument_group("More")
otherArgGroup.add_argument(
    "--advanced",
    action="store_true",
    default=False,
    help="Show advanced install options (in interactve mode)"
)
otherArgGroup.add_argument(
    "--simplified",
    action="store_true",
    default=False,
    help="Don't show advanced install options (in interactve mode)"
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
    help="Configure installation for development mode",
)
otherArgGroup.add_argument(
    "--no-wait-for-pvc",
    required=False,
    action="store_true",
    help="Disable the wait for pipeline PVC to bind before starting the pipeline"
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
    help="Skips Grafana install action"
)
otherArgGroup.add_argument(
    "--no-confirm",
    required=False,
    action="store_true",
    default=False,
    help="Launch the upgrade without prompting for confirmation",
)
otherArgGroup.add_argument(
    "--image-pull-policy",
    dest="image_pull_policy",
    required=False,
    help="Manually set the image pull policy used in the Tekton Pipeline",
)
otherArgGroup.add_argument(
    "--service-account",
    dest="service_account_name",
    required=False,
    help="Run the install pipeline under a custom service account (also disables creation of the default 'pipeline' service account)",
)

otherArgGroup.add_argument(
    "-h", "--help",
    action="help",
    default=False,
    help="Show this help message and exit",
)
