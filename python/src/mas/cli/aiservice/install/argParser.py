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
    "-i", "--aiservice-instance-id",
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
    "--aiservice-channel",
    required=False,
    help="Subscription channel for Maximo Ai Broker"
)

# AI Broker
# -----------------------------------------------------------------------------
aibrokerArgGroup = aiServiceinstallArgParser.add_argument_group("Maximo AI Broker")


# S3 - Minio
# -----------------------------------------------------------------------------
s3ArgGroup = aiServiceinstallArgParser.add_argument_group("S3 Storage")
s3ArgGroup.add_argument(
    "--install-minio",
    dest="install_minio_aiservice",
    required=False,
    help="Install Minio and configure it as the S3 provider for AI Service",
    action="store_const",
    const="true"
)

s3ArgGroup.add_argument(
    "--minio-root-user",
    dest="minio_root_user",
    required=False,
    help="Root user for minio"
)
s3ArgGroup.add_argument(
    "--minio-root-password",
    dest="minio_root_password",
    required=False,
    help="Password for minio root user"
)

# S3 - General
# -----------------------------------------------------------------------------
s3ArgGroup.add_argument(
    "--s3-provider",
    dest="aiservice_storage_provider",
    required=False,
    help="TODO: Write me"
)

# S3 - Bucket Naming
# -----------------------------------------------------------------------------
s3ArgGroup.add_argument(
    "--s3-pipelines-bucket",
    dest="aiservice_storage_pipelines_bucket",
    required=False,
    default="km-pipelines",
    help="TODO: Write me"
)
s3ArgGroup.add_argument(
    "--s3-tenants-bucket",
    dest="aiservice_storage_tenants_bucket",
    required=False,
    default="km-tenants",
    help="TODO: Write me"
)
s3ArgGroup.add_argument(
    "--s3-templates-bucket",
    dest="aiservice_storage_templates_bucket",
    required=False,
    default="km-templates",
    help="TODO: Write me"
)

# S3 - Bucket Prefixes
# -----------------------------------------------------------------------------
s3ArgGroup.add_argument(
    "--s3-bucket-prefix",
    dest="aiservice_s3_bucket_prefix",
    required=False,
    default="s3",
    help="s3 bucket prefix"
)
s3ArgGroup.add_argument(
    "--s3-bucket-prefix-tenant",
    dest="aiservice_tenant_s3_bucket_prefix",
    required=False,
    default="s3",
    help="s3 bucket prefix ( tenant level )"
)

# S3 - External Connection
# -----------------------------------------------------------------------------
s3ArgGroup.add_argument(
    "--s3-host",
    dest="aiservice_storage_host",
    required=False,
    help="TODO: Write me"
)
s3ArgGroup.add_argument(
    "--s3-port",
    dest="aiservice_storage_port",
    required=False,
    help="TODO: Write me"
)
s3ArgGroup.add_argument(
    "--s3-ssl",
    dest="aiservice_storage_ssl",
    required=False,
    help="TODO: Write me"
)
s3ArgGroup.add_argument(
    "--s3-accesskey",
    dest="aiservice_storage_accesskey",
    required=False,
    help="TODO: Write me"
)
s3ArgGroup.add_argument(
    "--s3-secretkey",
    dest="aiservice_storage_secretkey",
    required=False,
    help="TODO: Write me"
)
s3ArgGroup.add_argument(
    "--s3-region",
    dest="aiservice_storage_region",
    required=False,
    help="TODO: Write me"
)
s3ArgGroup.add_argument(
    "--s3-endpoint-url",
    dest="aiservice_s3_endpoint_url",
    required=False,
    help="endpoint url for s3"
)

# S3 - External Access Credentials (Tenant)
# -----------------------------------------------------------------------------
s3ArgGroup.add_argument(
    "--s3-tenant-access-key",
    dest="aiservice_tenant_s3_access_key",
    required=False,
    help="access key for s3 ( tenant level )"
)
s3ArgGroup.add_argument(
    "--s3-tenant-secret-key",
    dest="aiservice_tenant_s3_secret_key",
    required=False,
    help="secret key for s3 ( tenant level )"
)
s3ArgGroup.add_argument(
    "--s3-tenant-region",
    dest="aiservice_tenant_s3_region",
    required=False,
    help="s3 region ( tenant level )"
)
s3ArgGroup.add_argument(
    "--s3-tenant-endpoint-url",
    dest="aiservice_tenant_s3_endpoint_url",
    required=False,
    help="endpoint url for s3 ( tenant level )"
)

# Watsonx
# -----------------------------------------------------------------------------
watsonxArgGroup = aiServiceinstallArgParser.add_argument_group("Watsonx")

watsonxArgGroup.add_argument(
    "--watsonxai-apikey",
    dest="aiservice_watsonxai_apikey",
    required=False,
    help="TODO: Write me"
)
watsonxArgGroup.add_argument(
    "--watsonxai-url",
    dest="aiservice_watsonxai_url",
    required=False,
    help="TODO: Write me"
)
watsonxArgGroup.add_argument(
    "--watsonxai-project-id",
    dest="aiservice_watsonxai_project_id",
    required=False,
    help="TODO: Write me"
)
watsonxArgGroup.add_argument(
    "--watsonx-action",
    dest="aiservice_watsonx_action",
    required=False,
    help="TODO: Write me"
)


# AI Service
# -----------------------------------------------------------------------------
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
    "--approval-aiservice",
    default="",
    help="Require approval after the AI Service has been configured"
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
