# *****************************************************************************
# Copyright (c) 2024, 2025 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

import argparse
from os import path

from ... import __version__ as packageVersion
from ...cli import getHelpFormatter


def isValidFile(parser, arg) -> str:
    if not path.exists(arg):
        parser.error(f"Error: The file {arg} does not exist")
    else:
        return arg


aiServiceinstallArgParser = argparse.ArgumentParser(
    prog="mas install-aiservice",
    description="\n".join([
        f"IBM Maximo Application Suite Admin CLI v{packageVersion}",
        "Install Aiservice by configuring and launching the Tekton Pipeline.\n",
        "Interactive Mode:",
        "Omitting the --instance-id option will trigger an interactive prompt"
    ]),
    epilog="Refer to the online documentation for more information: https://ibm-mas.github.io/cli/",
    formatter_class=getHelpFormatter(),
    add_help=False
)

# MAS Catalog Selection & Entitlement
# -----------------------------------------------------------------------------
catArgGroup = aiServiceinstallArgParser.add_argument_group("MAS Catalog Selection & Entitlement")
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

# Aibroker Basic Configuration
# -----------------------------------------------------------------------------
masArgGroup = aiServiceinstallArgParser.add_argument_group("Aibroker Basic Configuration")
masArgGroup.add_argument(
    "-i", "--aibroker-instance-id",
    required=False,
    help="Aibroker Instance ID"
)

# MAS Advanced Configuration
# -----------------------------------------------------------------------------
masAdvancedArgGroup = aiServiceinstallArgParser.add_argument_group("MAS Advanced Configuration")
masAdvancedArgGroup.add_argument(
    "--additional-configs",
    required=False,
    help="Path to a directory containing additional configuration files to be applied"
)
masAdvancedArgGroup.add_argument(
    "--non-prod",
    required=False,
    help="Install MAS in non-production mode",
    action="store_true"
)

# Storage
# -----------------------------------------------------------------------------
storageArgGroup = aiServiceinstallArgParser.add_argument_group("Storage")
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
slsArgGroup = aiServiceinstallArgParser.add_argument_group("IBM Suite License Service")
slsArgGroup.add_argument(
    "--license-file",
    required=False,
    help="Path to MAS license file",
    type=lambda x: isValidFile(aiServiceinstallArgParser, x)
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
droArgGroup = aiServiceinstallArgParser.add_argument_group("IBM Data Reporting Operator (DRO)")
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
mongoArgGroup = aiServiceinstallArgParser.add_argument_group("MongoDb Community Operator")
mongoArgGroup.add_argument(
    "--mongodb-namespace",
    required=False,
    help=""
)

# MAS Applications
# -----------------------------------------------------------------------------
masAppsArgGroup = aiServiceinstallArgParser.add_argument_group("MAS Applications")

masAppsArgGroup.add_argument(
    "--aibroker-channel",
    required=False,
    help="Subscription channel for Maximo Ai Broker"
)

# AI Broker
# -----------------------------------------------------------------------------
aibrokerArgGroup = aiServiceinstallArgParser.add_argument_group("Maximo AI Broker")
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
aibrokerArgGroup.add_argument(
    "--minio-root-user",
    dest="minio_root_user",
    required=False,
    help="Root user for minio"
)
aibrokerArgGroup.add_argument(
    "--minio-root-password",
    dest="minio_root_password",
    required=False,
    help="Password for minio rootuser"
)
aibrokerArgGroup.add_argument(
    "--mariadb-user",
    dest="mariadb_user",
    required=False,
    help="Mariadb user name"
)
aibrokerArgGroup.add_argument(
    "--mariadb-password",
    dest="mariadb_password",
    required=False,
    help="Password for mariadb user"
)
aibrokerArgGroup.add_argument(
    "--tenant-entitlement-type",
    dest="tenant_entitlement_type",
    required=False,
    help="Type of aibroker tenant"
)
aibrokerArgGroup.add_argument(
    "--tenant-entitlement-start-date",
    dest="tenant_entitlement_start_date",
    required=False,
    help="Start date for Aibroker tenant"
)
aibrokerArgGroup.add_argument(
    "--tenant-entitlement-end-date",
    dest="tenant_entitlement_end_date",
    required=False,
    help="End date for Aibroker tenant"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-s3-bucket-prefix",
    dest="mas_aibroker_s3_bucket_prefix",
    required=False,
    help="s3 bucker prefix"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-s3-endpoint-url",
    dest="mas_aibroker_s3_endpoint_url",
    required=False,
    help="endpoint url for s3"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-s3-region",
    dest="mas_aibroker_s3_region",
    required=False,
    help="region for s3"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-tenant-s3-bucket-prefix",
    dest="mas_aibroker_tenant_s3_bucket_prefix",
    required=False,
    help="s3 bucker prefix ( tenant level )"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-tenant-s3-region",
    dest="mas_aibroker_tenant_s3_region",
    required=False,
    help="s3 region ( tenant level )"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-tenant-s3-endpoint-url",
    dest="mas_aibroker_tenant_s3_endpoint_url",
    required=False,
    help="endpoint url for s3 ( tenant level )"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-tenant-s3-access-key",
    dest="mas_aibroker_tenant_s3_access_key",
    required=False,
    help="access key for s3 ( tenant level )"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-tenant-s3-secret-key",
    dest="mas_aibroker_tenant_s3_secret_key",
    required=False,
    help="secret key for s3 ( tenant level )"
)
aibrokerArgGroup.add_argument(
    "--rsl-url",
    dest="rsl_url",
    required=False,
    help="rsl url"
)
aibrokerArgGroup.add_argument(
    "--rsl-org-id",
    dest="rsl_org_id",
    required=False,
    help="org id for rsl"
)
aibrokerArgGroup.add_argument(
    "--rsl-token",
    dest="rsl_token",
    required=False,
    help="token for rsl"
)
aibrokerArgGroup.add_argument(
    "--install-minio-aiservice",
    dest="install_minio_aiservice",
    required=False,
    help="flag for install minio"
)
aibrokerArgGroup.add_argument(
    "--install-sls-aiservice",
    dest="install_sls_aiservice",
    required=False,
    help="flag for install sls"
)
aibrokerArgGroup.add_argument(
    "--install-dro-aiservice",
    dest="install_dro_aiservice",
    required=False,
    help="flag for install dro"
)
aibrokerArgGroup.add_argument(
    "--install-db2-aiservice",
    dest="install_db2_aiservice",
    required=False,
    help="flag for install db2"
)

aibrokerArgGroup.add_argument(
    "--mas-aibroker-dro-secret-name",
    dest="mas_aibroker_dro_secret_name",
    required=False,
    help="DRO secret name"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-dro-api-key",
    dest="mas_aibroker_dro_api_key",
    required=False,
    help="DRO API key"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-dro-url",
    dest="mas_aibroker_dro_url",
    required=False,
    help="DRO URL"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-dro-ca-cert",
    dest="mas_aibroker_dro_ca_cert",
    required=False,
    help="DRO CA certificate"
)

aibrokerArgGroup.add_argument(
    "--mas-aibroker-db2-username",
    dest="mas_aibroker_db2_username",
    required=False,
    help="DB2 username"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-db2-password",
    dest="mas_aibroker_db2_password",
    required=False,
    help="DB2 password"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-db2-jdbc-url",
    dest="mas_aibroker_db2_jdbc_url",
    required=False,
    help="DB2 JDBC URL"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-db2-ssl-enabled",
    dest="mas_aibroker_db2_ssl_enabled",
    required=False,
    help="DB2 SSL enabled"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-db2-ca-cert",
    dest="mas_aibroker_db2_ca_cert",
    required=False,
    help="DB2 CA certificate"
)

aibrokerArgGroup.add_argument(
    "--mas-aibroker-sls-secret-name",
    dest="mas_aibroker_sls_secret_name",
    required=False,
    help="SLS secret name"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-sls-registration-key",
    dest="mas_aibroker_sls_registration_key",
    required=False,
    help="SLS registration key"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-sls-url",
    dest="mas_aibroker_sls_url",
    required=False,
    help="SLS URL"
)
aibrokerArgGroup.add_argument(
    "--mas-aibroker-sls-ca-cert",
    dest="mas_aibroker_sls_ca_cert",
    required=False,
    help="SLS CA certificate"
)

aibrokerArgGroup.add_argument(
    "--environment-type",
    dest="environment_type",
    required=False,
    default="non-production",
    help="Environment type (default: non-production)"
)
# IBM Db2 Universal Operator
# -----------------------------------------------------------------------------
db2ArgGroup = aiServiceinstallArgParser.add_argument_group("IBM Db2 Universal Operator")
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


# Development Mode
# -----------------------------------------------------------------------------
devArgGroup = aiServiceinstallArgParser.add_argument_group("Development Mode")
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
approvalsGroup = aiServiceinstallArgParser.add_argument_group("Integrated Approval Workflow (MAX_RETRIES:RETRY_DELAY:IGNORE_FAILURE)")
approvalsGroup.add_argument(
    "--approval-aibroker",
    default="",
    help="Require approval after the Aibroker has been configured"
)

# More Options
# -----------------------------------------------------------------------------
otherArgGroup = aiServiceinstallArgParser.add_argument_group("More")
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
