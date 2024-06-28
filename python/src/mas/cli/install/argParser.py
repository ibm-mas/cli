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
    prog="mas uninstall",
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
    help=""
)
catArgGroup.add_argument(
    "--ibm-entitlement-key",
    required=False,
    help=""
)

# MAS Basic Configuration
# -----------------------------------------------------------------------------
masArgGroup = installArgParser.add_argument_group("MAS Basic Configuration")
masArgGroup.add_argument(
    "-i", "--mas-instance-id",
    required=False,
    help=""
)
masArgGroup.add_argument(
    "-w", "--mas-workspace-id",
    required=False,
    help=""
)
masArgGroup.add_argument(
    "-W", "--mas-workspace-name",
    required=False,
    help=""
)
masArgGroup.add_argument(
    "--mas-channel",
    required=False,
    help=""
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
    help=""
)
masAdvancedArgGroup.add_argument(
    "--pod-templates",
    required=False,
    help=""
)
masAdvancedArgGroup.add_argument(
    "--non-prod",
    required=False,
    help="",
    action="store_true"
)
masAdvancedArgGroup.add_argument(
    "--disable-ca-trust",
    dest="mas_trust_default_cas",
    required=False,
    help="",
    action="store_const",
    const="false"
)

# Storage
# -----------------------------------------------------------------------------
storageArgGroup = installArgParser.add_argument_group("Storage")
storageArgGroup.add_argument(
    "--storage-class-rwo",
    required=False,
    help=""
)
storageArgGroup.add_argument(
    "--storage-class-rwx",
    required=False,
    help=""
)
storageArgGroup.add_argument(
    "--storage-pipeline",
    required=False,
    help=""
)
storageArgGroup.add_argument(
    "--storage-accessmode",
    required=False,
    help="",
    choices=["ReadOnlyMany", "ReadWriteMany", "ReadWriteOnce", "ReadWriteOncePod"]
)

# IBM Suite License Service
# -----------------------------------------------------------------------------
slsArgGroup = installArgParser.add_argument_group("IBM Suite License Service")
slsArgGroup.add_argument(
    "--license-file",
    required=False,
    help="",
    type=lambda x: isValidFile(installArgParser, x)
)

# IBM Data Reporting Operator (DRO)
# -----------------------------------------------------------------------------
droArgGroup = installArgParser.add_argument_group("IBM Data Reporting Operator (DRO)")
droArgGroup.add_argument(
    "--uds-email",
    dest="uds_contact_email",
    required=False,
    help=""
)
droArgGroup.add_argument(
    "--uds-firstname",
    dest="uds_contact_firstname",
    required=False,
    help=""
)
droArgGroup.add_argument(
    "--uds-lastname",
    dest="uds_contact_lastname",
    required=False,
    help=""
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
    help=""
)

# MAS Applications
# -----------------------------------------------------------------------------
masAppsArgGroup = installArgParser.add_argument_group("MAS Applications")
masAppsArgGroup.add_argument(
    "--assist-channel",
    required=False,
    help=""
)
masAppsArgGroup.add_argument(
    "--iot-channel",
    required=False,
    help=""
)
masAppsArgGroup.add_argument(
    "--monitor-channel",
    required=False,
    help=""
)
masAppsArgGroup.add_argument(
    "--manage-channel",
    required=False,
    help=""
)
masAppsArgGroup.add_argument(
    "--predict-channel",
    required=False,
    help=""
)
masAppsArgGroup.add_argument(
    "--visualinspection-channel",
    required=False,
    help=""
)
masAppsArgGroup.add_argument(
    "--optimizer-channel",
    required=False,
    help=""
)
masAppsArgGroup.add_argument(
    "--optimizer-plan",
    required=False,
    help=""
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
    help="",
    choices=["dev", "snojms", "small", "jms"]
)
manageArgGroup.add_argument(
    "--manage-jms",
    dest="mas_app_settings_default_jms",
    required=False,
    help="",
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
    help="",
    default="base=latest;health=latest"
)

manageArgGroup.add_argument(
    "--manage-customization-archive-name",
    dest="mas_app_settings_customization_archive_name",
    required=False,
    help=""
)
manageArgGroup.add_argument(
    "--manage-customization-archive-url",
    dest="mas_app_settings_customization_archive_url",
    required=False,
    help=""
)
manageArgGroup.add_argument(
    "--manage-customization-archive-username",
    dest="mas_app_settings_customization_archive_username",
    required=False,
    help=""
)
manageArgGroup.add_argument(
    "--manage-customization-archive-password",
    dest="mas_app_settings_customization_archive_password",
    required=False,
    help=""
)

manageArgGroup.add_argument(
    "--manage-db-tablespace",
    dest="mas_app_settings_tablespace",
    required=False,
    help=""
)
manageArgGroup.add_argument(
    "--manage-db-indexspace",
    dest="mas_app_settings_indexspace",
    required=False,
    help=""
)
manageArgGroup.add_argument(
    "--manage-db-schema",
    dest="mas_app_settings_db2_schema",
    required=False,
    help=""
)

manageArgGroup.add_argument(
    "--manage-crypto-key",
    dest="mas_app_settings_crypto_key",
    required=False,
    help=""
)
manageArgGroup.add_argument(
    "--manage-cryptox-key",
    dest="mas_app_settings_cryptox_key",
    required=False,
    help=""
)
manageArgGroup.add_argument(
    "--manage-old-crypto-key",
    dest="mas_app_settings_old_crypto_key",
    required=False,
    help=""
)
manageArgGroup.add_argument(
    "--manage-old-cryptox-key",
    dest="mas_app_settings_old_cryptox_key",
    required=False,
    help=""
)
manageArgGroup.add_argument(
    "--manage-override-encryption-secrets",
    dest="mas_app_settings_override_encryption_secrets_flag",
    required=False,
    help="",
    action="store_const",
    const="true"
)

manageArgGroup.add_argument(
    "--manage-base-language",
    dest="mas_app_settings_base_lang",
    required=False,
    help=""
)
manageArgGroup.add_argument(
    "--manage-secondary-languages",
    dest="mas_app_settings_secondary_langs",
    required=False,
    help=""
)
manageArgGroup.add_argument(
    "--manage-server-timezone",
    dest="mas_app_settings_server_timezone",
    required=False,
    help=""
)

# IBM Cloud Pak for Data
# -----------------------------------------------------------------------------
cpdAppsArgGroup = installArgParser.add_argument_group("IBM Cloud Pak for Data")
cpdAppsArgGroup.add_argument(
    "--cp4d-version",
    dest="cpd_product_version",
    required=False,
    help=""
)
cpdAppsArgGroup.add_argument(
    "--cp4d-install-spss",
    dest="cpd_install_spss",
    required=False,
    help="",
    action="store_const",
    const="install"
)
cpdAppsArgGroup.add_argument(
    "--cp4d-installopenscale",
    dest="cpd_install_openscale",
    required=False,
    help="",
    action="store_const",
    const="install"
)
cpdAppsArgGroup.add_argument(
    "--cp4d-install-cognos",
    dest="cpd_install_cognos",
    required=False,
    help="",
    action="store_const",
    const="install"
)

# IBM Db2 Universal Operator
# -----------------------------------------------------------------------------
db2ArgGroup = installArgParser.add_argument_group("IBM Db2 Universal Operator")
db2ArgGroup.add_argument(
    "--db2-namespace",
    required=False,
    help=""
)
db2ArgGroup.add_argument(
    "--db2-channel",
    required=False,
    help=""
)
db2ArgGroup.add_argument(
    "--db2-system",
    dest="db2_action_system",
    required=False,
    help="",
    action="store_const",
    const="install"
)
db2ArgGroup.add_argument(
    "--db2-manage",
    dest="db2_action_manage",
    required=False,
    help="",
    action="store_const",
    const="install"
)
db2ArgGroup.add_argument(
    "--db2-type",
    required=False,
    help=""
)
db2ArgGroup.add_argument(
    "--db2-timezone",
    required=False,
    help=""
)
db2ArgGroup.add_argument(
    "--db2-affinity-key",
    required=False,
    help=""
)
db2ArgGroup.add_argument(
    "--db2-affinity-value",
    required=False,
    help=""
)
db2ArgGroup.add_argument(
    "--db2-tolerate-key",
    required=False,
    help=""
)
db2ArgGroup.add_argument(
    "--db2-tolerate-value",
    required=False,
    help=""
)
db2ArgGroup.add_argument(
    "--db2-tolerate-effect",
    required=False,
    help=""
)
db2ArgGroup.add_argument(
    "--db2-cpu-requests",
    required=False,
    help=""
)
db2ArgGroup.add_argument(
    "--db2-cpu-limits",
    required=False,
    help=""
)
db2ArgGroup.add_argument(
    "--db2-memory-requests",
    required=False,
    help=""
)
db2ArgGroup.add_argument(
    "--db2-memory-limits",
    required=False,
    help=""
)
db2ArgGroup.add_argument(
    "--db2-backup-storage",
    dest="db2_backup_storage_size",
    required=False,
    help=""
)
db2ArgGroup.add_argument(
    "--db2-data-storage",
    dest="db2_data_storage_size",
    required=False,
    help=""
)
db2ArgGroup.add_argument(
    "--db2-logs-storage",
    dest="db2_logs_storage_size",
    required=False,
    help=""
)
db2ArgGroup.add_argument(
    "--db2-meta-storage",
    dest="db2_meta_storage_size",
    required=False,
    help=""
)
db2ArgGroup.add_argument(
    "--db2-temp-storage",
    dest="db2_temp_storage_size",
    required=False,
    help=""
)


# Kafka - Common
# -----------------------------------------------------------------------------
kafkaCommonArgGroup = installArgParser.add_argument_group("Kafka - Common")
kafkaCommonArgGroup.add_argument(
    "--kafka-provider",
    required=False,
    help="",
    choices=["strimzi", "redhat", "ibm", "aws"]
)
kafkaCommonArgGroup.add_argument(
    "--kafka-username",
    required=False,
    help=""
)
kafkaCommonArgGroup.add_argument(
    "--kafka-password",
    required=False,
    help=""
)

# Kafka - Strimzi & AMQ Streams
# -----------------------------------------------------------------------------
kafkaOCPArgGroup = installArgParser.add_argument_group("Kafka - Strimzi and AMQ Streams")
kafkaCommonArgGroup.add_argument(
    "--kafka-namespace",
    required=False,
    help=""
)
kafkaOCPArgGroup.add_argument(
    "--kafka-version",
    required=False,
    help=""
)

# Kafka - MSK
# -----------------------------------------------------------------------------
mskArgGroup = installArgParser.add_argument_group("Kafka - AWS MSK")
mskArgGroup.add_argument(
    "--msk-instance-type",
    dest="aws_msk_instance_type",
    required=False,
    help=""
)
mskArgGroup.add_argument(
    "--msk-instance-nodes",
    dest="aws_msk_instance_number",
    required=False,
    help=""
)
mskArgGroup.add_argument(
    "--msk-instance-volume-size",
    dest="aws_msk_volume_size",
    required=False,
    help=""
)
mskArgGroup.add_argument(
    "--msk-cidr-az1",
    dest="aws_msk_cidr_az1",
    required=False,
    help=""
)
mskArgGroup.add_argument(
    "--msk-cidr-az2",
    dest="aws_msk_cidr_az2",
    required=False,
    help=""
)
mskArgGroup.add_argument(
    "--msk-cidr-az3",
    dest="aws_msk_cidr_az3",
    required=False,
    help=""
)
mskArgGroup.add_argument(
    "--msk-cidr-egress",
    dest="aws_msk_egress_cidr",
    required=False,
    help=""
)
mskArgGroup.add_argument(
    "--msk-cidr-ingress",
    dest="aws_msk_ingress_cidr",
    required=False,
    help=""
)

# Kafka - Event Streams
# -----------------------------------------------------------------------------
mskArgGroup = installArgParser.add_argument_group("Kafka - Event Streams")
mskArgGroup.add_argument(
    "--eventstreams-resource-group",
    required=False,
    help=""
)
mskArgGroup.add_argument(
    "--eventstreams-instance-name",
    required=False,
    help=""
)
mskArgGroup.add_argument(
    "--eventstreams-instance-location",
    required=False,
    help=""
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
    help=""
)
cloudArgGroup.add_argument(
    "--aws-region",
    required=False,
    help=""
)
cloudArgGroup.add_argument(
    "--aws-access-key-id",
    required=False,
    help=""
)
cloudArgGroup.add_argument(
    "--secret-access-key",
    required=False,
    help=""
)
cloudArgGroup.add_argument(
    "--aws-vpc-id",
    required=False,
    help=""
)

otherArgGroup = installArgParser.add_argument_group("More")
otherArgGroup.add_argument(
    "--accept-license",
    action="store_true",
    default=False,
    help=""
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
    "--no-confirm",
    required=False,
    action="store_true",
    default=False,
    help="Launch the upgrade without prompting for confirmation",
)

otherArgGroup.add_argument(
    "-h", "--help",
    action="help",
    default=False,
    help="Show this help message and exit",
)
