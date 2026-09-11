# *****************************************************************************
# Copyright (c) 2025, 2026 IBM Corporation and other Contributors.
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

# Constants for argument choices
DNS_PROVIDERS = ["cis", "route53"]


def isValidFile(parser, arg) -> str:
    if not path.exists(arg):
        parser.error(f"Error: The file {arg} does not exist")
    else:
        return arg


aiServiceinstallArgParser = argparse.ArgumentParser(
    prog="mas aiservice-install",
    description="\n".join(
        [
            f"IBM Maximo Application Suite Admin CLI v{packageVersion}",
            "Install Aiservice by configuring and launching the Tekton Pipeline.\n",
            "Interactive Mode:",
            "Omitting the --instance-id option will trigger an interactive prompt",
        ]
    ),
    epilog="Refer to the online documentation for more information: https://ibm-mas.github.io/cli/",
    formatter_class=getHelpFormatter(),
    add_help=False,
)

# MAS Catalog Selection & Entitlement
# -----------------------------------------------------------------------------
catArgGroup = aiServiceinstallArgParser.add_argument_group("MAS Catalog Selection & Entitlement")
catArgGroup.add_argument("-c", "--mas-catalog-version", required=False, help="IBM Maximo Operator Catalog to install")
catArgGroup.add_argument(
    "--mas-catalog-digest", required=False, help="IBM Maximo Operator Catalog Digest, only required when installing development catalog sources"
)
catArgGroup.add_argument("--ibm-entitlement-key", required=False, help="IBM entitlement key")

# AI Service Basic Configuration
# -----------------------------------------------------------------------------
masArgGroup = aiServiceinstallArgParser.add_argument_group("AI Service Basic Configuration")
masArgGroup.add_argument("-i", "--aiservice-instance-id", required=False, help="AI Service Instance ID")

# MAS Advanced Configuration
# -----------------------------------------------------------------------------
masAdvancedArgGroup = aiServiceinstallArgParser.add_argument_group("MAS Advanced Configuration")
masAdvancedArgGroup.add_argument("--additional-configs", required=False, help="Path to a directory containing additional configuration files to be applied")
masAdvancedArgGroup.add_argument("--non-prod", required=False, help="Install MAS in non-production mode", action="store_true")

# Storage
# -----------------------------------------------------------------------------
storageArgGroup = aiServiceinstallArgParser.add_argument_group("Storage")
storageArgGroup.add_argument("--storage-class-rwo", required=False, help="ReadWriteOnce (RWO) storage class (e.g. ibmc-block-gold)")
storageArgGroup.add_argument("--storage-class-rwx", required=False, help="ReadWriteMany (RWX) storage class (e.g. ibmc-file-gold-gid)")
storageArgGroup.add_argument("--storage-pipeline", required=False, help="Install pipeline storage class (e.g. ibmc-file-gold-gid)")
storageArgGroup.add_argument(
    "--storage-accessmode",
    required=False,
    help="Install pipeline storage class access mode (ReadWriteMany or ReadWriteOnce)",
    choices=["ReadWriteMany", "ReadWriteOnce"],
)

# IBM Suite License Service
# -----------------------------------------------------------------------------
slsArgGroup = aiServiceinstallArgParser.add_argument_group("IBM Suite License Service")
slsArgGroup.add_argument("--license-file", required=False, help="Path to MAS license file", type=lambda x: isValidFile(aiServiceinstallArgParser, x))
slsArgGroup.add_argument("--sls-namespace", required=False, help="Customize the SLS install namespace", default="ibm-sls")
slsArgGroup.add_argument("--dedicated-sls", action="store_true", default=False, help="Set the SLS namespace to mas-<instanceid>-sls")

# IBM Data Reporting Operator (DRO)
# -----------------------------------------------------------------------------
droArgGroup = aiServiceinstallArgParser.add_argument_group("IBM Data Reporting Operator (DRO)")
droArgGroup.add_argument("--contact-email", "--uds-email", dest="dro_contact_email", required=False, help="Contact e-mail address")
droArgGroup.add_argument("--contact-firstname", "--uds-firstname", dest="dro_contact_firstname", required=False, help="Contact first name")
droArgGroup.add_argument("--contact-lastname", "--uds-lastname", dest="dro_contact_lastname", required=False, help="Contact last name")
droArgGroup.add_argument("--dro-namespace", required=False, help="Namespace for the Data Reporting Operator")

# MongoDb Community Operator
# -----------------------------------------------------------------------------
mongoArgGroup = aiServiceinstallArgParser.add_argument_group("MongoDb Community Operator")
mongoArgGroup.add_argument("--mongodb-namespace", required=False, help="Namespace for the MongoDB Community Operator")

# MAS Applications
# -----------------------------------------------------------------------------
masAppsArgGroup = aiServiceinstallArgParser.add_argument_group("MAS Applications")

masAppsArgGroup.add_argument("--aiservice-channel", required=False, help="Subscription channel for Maximo AI Service")

# ODH
# -----------------------------------------------------------------------------
odhArgGroup = aiServiceinstallArgParser.add_argument_group("Opendatahub")

odhArgGroup.add_argument(
    "--odh-model-deployment-type", dest="aiservice_odh_model_deployment_type", required=False, default="raw", help="Model deployment type for ODH"
)

# Red Hat Openshift AI
# -----------------------------------------------------------------------------
rhoaiArgGroup = aiServiceinstallArgParser.add_argument_group("RedHat Openshift AI")

rhoaiArgGroup.add_argument(
    "--rhoai-model-deployment-type",
    dest="aiservice_rhoai_model_deployment_type",
    required=False,
    default="raw",
    help="Model deployment type for RedHat Openshift AI",
)

rhoaiArgGroup.add_argument(
    "--rhoai", dest="rhoai", required=False, help="temporary flag to install Redhat Openshift AI instead of Opendatahub", action="store_const", const="true"
)

# S3 - General
# -----------------------------------------------------------------------------
s3ArgGroup = aiServiceinstallArgParser.add_argument_group("S3 Storage")

# S3 - Minio
# -----------------------------------------------------------------------------
s3ArgGroup.add_argument(
    "--install-minio",
    dest="install_minio_aiservice",
    required=False,
    help="Install Minio and configure it as the S3 provider for AI Service",
    action="store_const",
    const="true",
)

s3ArgGroup.add_argument("--minio-root-user", dest="minio_root_user", required=False, help="Root user for minio")
s3ArgGroup.add_argument("--minio-root-password", dest="minio_root_password", required=False, help="Password for minio root user")

# S3 - External Connection
# -----------------------------------------------------------------------------
s3ArgGroup.add_argument("--s3-host", dest="aiservice_s3_host", required=False, help="Hostname or IP address of the S3 storage service")
s3ArgGroup.add_argument("--s3-port", dest="aiservice_s3_port", required=False, help="Port number for the S3 storage service")
s3ArgGroup.add_argument("--s3-ssl", dest="aiservice_s3_ssl", required=False, help="Enable or disable SSL for S3 connection (true/false)")
s3ArgGroup.add_argument("--s3-accesskey", dest="aiservice_s3_accesskey", required=False, help="Access key for authenticating with the S3 storage service")
s3ArgGroup.add_argument("--s3-secretkey", dest="aiservice_s3_secretkey", required=False, help="Secret key for authenticating with the S3 storage service")
s3ArgGroup.add_argument("--s3-region", dest="aiservice_s3_region", required=False, help="Region for the S3 storage service")
s3ArgGroup.add_argument("--s3-bucket-prefix", dest="aiservice_s3_bucket_prefix", required=False, help="Bucket prefix configured with S3 storage service")

# S3 - Bucket Naming
# -----------------------------------------------------------------------------
s3ArgGroup.add_argument(
    "--s3-tenants-bucket", dest="aiservice_s3_tenants_bucket", required=False, default="km-tenants", help="Name of the S3 bucket for tenants storage"
)
s3ArgGroup.add_argument(
    "--s3-templates-bucket", dest="aiservice_s3_templates_bucket", required=False, default="km-templates", help="Name of the S3 bucket for templates storage"
)

# Watsonx
# -----------------------------------------------------------------------------
watsonxArgGroup = aiServiceinstallArgParser.add_argument_group("Watsonx")

watsonxArgGroup.add_argument("--watsonxai-apikey", dest="aiservice_watsonxai_apikey", required=False, help="API key for WatsonX")
watsonxArgGroup.add_argument("--watsonxai-url", dest="aiservice_watsonxai_url", required=False, help="URL endpoint for WatsonX")
watsonxArgGroup.add_argument("--watsonxai-project-id", dest="aiservice_watsonxai_project_id", required=False, help="Project ID for WatsonX")
watsonxArgGroup.add_argument("--watsonx-action", dest="aiservice_watsonx_action", required=False, help="Action to perform with WatsonX (install/remove)")
watsonxArgGroup.add_argument(
    "--watsonxai-ca-crt",
    dest="aiservice_watsonxai_ca_crt",
    required=False,
    help="CA certificate for WatsonX AI (PEM format, optional, only if using self-signed certs)",
)
watsonxArgGroup.add_argument("--watsonxai-deployment-id", dest="aiservice_watsonxai_deployment_id", required=False, help="WatsonX deployment ID")
watsonxArgGroup.add_argument("--watsonxai-space-id", dest="aiservice_watsonxai_space_id", required=False, help="WatsonX space ID")
watsonxArgGroup.add_argument("--watsonxai-instance-id", dest="aiservice_watsonxai_instance_id", required=False, help="WatsonX instance ID")
watsonxArgGroup.add_argument("--watsonxai-username", dest="aiservice_watsonxai_username", required=False, help="WatsonX username")
watsonxArgGroup.add_argument("--watsonxai-version", dest="aiservice_watsonxai_version", required=False, help="WatsonX version")
watsonxArgGroup.add_argument("--watsonxai-onprem", dest="aiservice_watsonxai_on_prem", required=False, help="WatsonX deployed on prem")

# AI Service
# -----------------------------------------------------------------------------
aiServiceArgGroup = aiServiceinstallArgParser.add_argument_group("Maximo AI Service")

aiServiceArgGroup.add_argument(
    "--tenant-entitlement-type", dest="tenant_entitlement_type", required=False, default="standard", help="Entitlement type for AI Service tenant"
)
aiServiceArgGroup.add_argument("--tenant-entitlement-start-date", dest="tenant_entitlement_start_date", required=False, help="Start date for AI Service tenant")
aiServiceArgGroup.add_argument("--tenant-entitlement-end-date", dest="tenant_entitlement_end_date", required=False, help="End date for AI Service tenant")

aiServiceArgGroup.add_argument(
    "--rsl-ca-crt", dest="rsl_ca_crt", required=False, help="CA certificate for RSL API (PEM format, optional, only if using self-signed certs)"
)
aiServiceArgGroup.add_argument(
    "--environment-type", dest="environment_type", required=False, default="non-production", help="Environment type (default: non-production)"
)

# AI Service advanced configuration
# -----------------------------------------------------------------------------
aiserviceAdvancedArgGroup = aiServiceinstallArgParser.add_argument_group(
    "Advanced configuration for AI Service", "Advanced configuration options for AI Service including certificates issuer and IPv6 support"
)
aiserviceAdvancedArgGroup.add_argument(
    "--aiservice-certificate-issuer",
    dest="aiservice_certificate_issuer",
    required=False,
    help="Provide the name of the Issuer to configure AI Service to issue certificates",
)
aiserviceAdvancedArgGroup.add_argument(
    "--enable-ipv6",
    dest="enable_ipv6",
    required=False,
    default="false",
    help="Configure AI Service to run in IPv6. Before setting this option, be sure your cluster is configured in IPv6",
    action="store_const",
    const="true",
)
aiserviceAdvancedArgGroup.add_argument(
    "--tenant-scheduling-config-file",
    dest="tenant_scheduling_config_file",
    required=False,
    help="Path to the YAML file that contains the scheduling configuration for tenant",
    type=lambda x: isValidFile(aiServiceinstallArgParser, x),
)
aiserviceAdvancedArgGroup.add_argument(
    "--tenant-operator-config-file",
    dest="tenant_operator_config_file",
    required=False,
    help="Path to the YAML file that contains the tenant operator customization settings",
    type=lambda x: isValidFile(aiServiceinstallArgParser, x),
)
aiserviceAdvancedArgGroup.add_argument(
    "--domain",
    dest="aiservice_domain",
    required=False,
    help="Configure AI Service with a custom domain",
)
aiserviceAdvancedArgGroup.add_argument(
    "--dns-provider",
    dest="dns_provider",
    required=False,
    help="Enable automatic DNS management (see DNS Configuration options)",
    choices=DNS_PROVIDERS,
    metavar="{cis,route53}",
)
aiserviceAdvancedArgGroup.add_argument(
    "--ocp-ingress",
    dest="ocp_ingress",
    required=False,
    help="Overwrites Ingress Domain",
)
aiserviceAdvancedArgGroup.add_argument(
    "--ocp-ingress-tls-secret-name",
    dest="ocp_ingress_tls_secret_name",
    required=False,
    default="",
    help="Cluster ingress certificate secret name",
)

# DNS Integration - IBM CIS
# -----------------------------------------------------------------------------
cisArgGroup = aiServiceinstallArgParser.add_argument_group("DNS Integration - CIS")
cisArgGroup.add_argument(
    "--cis-email",
    dest="cis_email",
    required=False,
    help="Required when DNS provider is CIS and you want to use a Let's Encrypt Issuer",
)
cisArgGroup.add_argument(
    "--cis-apikey",
    dest="cis_apikey",
    required=False,
    help="Required when DNS provider is CIS",
)
cisArgGroup.add_argument(
    "--cis-crn",
    dest="cis_crn",
    required=False,
    help="Required when DNS provider is CIS",
)
cisArgGroup.add_argument(
    "--cis-subdomain",
    dest="cis_subdomain",
    required=False,
    help="Optionally setup AI Service instance as a subdomain under a multi-tenant CIS DNS record",
)
cisArgGroup.add_argument(
    "--cis-enhanced-security",
    dest="cis_enhanced_security",
    required=False,
    default="false",
    help="Configure enhanced security for CIS (enables WAF and proxy settings)",
    action="store_const",
    const="true",
)
cisArgGroup.add_argument(
    "--cis-service-name",
    dest="cis_service_name",
    required=False,
    help="CIS service instance name",
)
cisArgGroup.add_argument(
    "--update-dns-entries",
    dest="update_dns_entries",
    required=False,
    default="true",
    help="Update existing DNS entries in CIS if they already exist (default: true)",
    action="store_const",
    const="true",
)
cisArgGroup.add_argument(
    "--cis-waf",
    dest="cis_waf",
    required=False,
    default="true",
    help="Enable Web Application Firewall (WAF) for CIS DNS entries",
    action="store_const",
    const="true",
)
cisArgGroup.add_argument(
    "--cis-proxy",
    dest="cis_proxy",
    required=False,
    default="false",
    help="Enable CIS proxy for DNS entries",
    action="store_const",
    const="true",
)
cisArgGroup.add_argument(
    "--delete-wildcards",
    dest="delete_wildcards",
    required=False,
    default="false",
    help="Force deletion of wildcard DNS entries in CIS",
    action="store_const",
    const="true",
)
cisArgGroup.add_argument(
    "--override-edge-certs",
    dest="override_edge_certs",
    required=False,
    default="true",
    help="Override and delete existing edge certificates in CIS instance",
    action="store_const",
    const="true",
)

# DNS Integration - AWS Route53
# -----------------------------------------------------------------------------
route53ArgGroup = aiServiceinstallArgParser.add_argument_group("DNS Integration - AWS Route53")
route53ArgGroup.add_argument(
    "--aws-access-key-id",
    dest="aws_access_key_id",
    required=False,
    help="AWS access key ID for authenticating with the AWS account (required for Route53 DNS integration)",
)
route53ArgGroup.add_argument(
    "--aws-secret-access-key",
    dest="aws_secret_access_key",
    required=False,
    help="AWS secret access key for authenticating with the AWS account (required for Route53 DNS integration)",
)
route53ArgGroup.add_argument(
    "--route53-hosted-zone-name",
    dest="route53_hosted_zone_name",
    required=False,
    help="Required when DNS provider is Route53",
)
route53ArgGroup.add_argument(
    "--route53-hosted-zone-region",
    dest="route53_hosted_zone_region",
    required=False,
    help="Required when DNS provider is Route53",
)
route53ArgGroup.add_argument(
    "--route53-subdomain",
    dest="route53_subdomain",
    required=False,
    help="Required when DNS provider is Route53",
)
route53ArgGroup.add_argument(
    "--route53-email",
    dest="route53_email",
    required=False,
    help="Required when DNS provider is Route53",
)

# Database Configuration
# -----------------------------------------------------------------------------
databaseArgGroup = aiServiceinstallArgParser.add_argument_group(
    "Database Configuration",
    "Configure database for AI Service. By default, DB2 is installed in-cluster. Use --db-* parameters to connect to an external database (Oracle/SQL Server/DB2) instead.",
)

# Option 1: Install DB2 in-cluster (default)
databaseArgGroup.add_argument(
    "--db2-aiservice",
    dest="db2_action_aiservice",
    required=False,
    help="Install DB2 in-cluster for AI Service (default behavior, mutually exclusive with --db-*)",
    action="store_const",
    const="install",
)
databaseArgGroup.add_argument("--db2-namespace", required=False, help="Change namespace where Db2u instances will be created")
databaseArgGroup.add_argument("--db2-channel", required=False, help="Subscription channel for Db2u")
databaseArgGroup.add_argument("--db2-license-file", required=False, help="Db2 License File for Db2")

# Option 2: Use external database (Oracle/SQL Server/DB2)
databaseArgGroup.add_argument(
    "--aiservice-db-jdbc-url",
    dest="aiservice_db_jdbc_url",
    required=False,
    help="JDBC URL for external database (e.g., jdbc:oracle:thin:@host:1521/service, jdbc:sqlserver://host:1433;databaseName=db, jdbc:db2://host:50000/db)",
)
databaseArgGroup.add_argument("--aiservice-db-username", dest="aiservice_db_username", required=False, help="Database username for AI Service")
databaseArgGroup.add_argument("--aiservice-db-password", dest="aiservice_db_password", required=False, help="Database password for AI Service")
databaseArgGroup.add_argument(
    "--aiservice-db-ca-cert", dest="aiservice_db_ca_cert", required=False, help="Database CA certificate (PEM format, optional, only if using SSL/TLS)"
)

# Development Mode
# -----------------------------------------------------------------------------
devArgGroup = aiServiceinstallArgParser.add_argument_group("Development Mode")
devArgGroup.add_argument("--artifactory-username", required=False, help="Username for access to development builds on Artifactory")
devArgGroup.add_argument("--artifactory-token", required=False, help="API Token for access to development builds on Artifactory")

# Approvals
# -----------------------------------------------------------------------------
approvalsGroup = aiServiceinstallArgParser.add_argument_group("Integrated Approval Workflow (MAX_RETRIES:RETRY_DELAY:IGNORE_FAILURE)")
approvalsGroup.add_argument("--approval-aiservice", default="", help="Require approval after the AI Service has been configured")

# More Options
# -----------------------------------------------------------------------------
otherArgGroup = aiServiceinstallArgParser.add_argument_group("More")
otherArgGroup.add_argument("--advanced", action="store_true", default=False, help="Show advanced install options (in interactve mode)")
otherArgGroup.add_argument("--simplified", action="store_true", default=False, help="Don't show advanced install options (in interactve mode)")
otherArgGroup.add_argument("--accept-license", action="store_true", default=False, help="Accept all license terms without prompting")
otherArgGroup.add_argument(
    "--dev-mode",
    required=False,
    action="store_true",
    default=False,
    help="Configure installation for development mode",
)
otherArgGroup.add_argument("--skip-pre-check", required=False, action="store_true", help="Disable the 'pre-install-check' at the start of the install pipeline")
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
otherArgGroup.add_argument("--slack-token", dest="slack_token", required=False, help="Slack bot token for sending pipeline notifications")
otherArgGroup.add_argument(
    "--slack-channel", dest="slack_channel", required=False, help="Slack channel(s) for notifications (comma-separated for multiple channels)"
)

otherArgGroup.add_argument(
    "-h",
    "--help",
    action="help",
    default=False,
    help="Show this help message and exit",
)
