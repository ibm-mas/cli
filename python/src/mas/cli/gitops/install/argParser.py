# *****************************************************************************
# Copyright (c) 2024, 2026 IBM Corporation and other Contributors.
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
    """
    Validate that a file path exists.

    Args:
        parser: The argument parser instance
        arg: The file path to validate

    Returns:
        str: The validated file path

    Raises:
        argparse.ArgumentTypeError: If the file does not exist
    """
    if not path.exists(arg):
        parser.error(f"Error: The file {arg} does not exist")
        return ""  # This line will never be reached due to parser.error() raising SystemExit
    else:
        return arg


gitops_install_arg_parser = argparse.ArgumentParser(
    prog="mas gitops-install",
    description="\n".join([
        f"IBM Maximo Application Suite Admin CLI v{packageVersion}",
        "Install MAS using GitOps by configuring and deploying ArgoCD applications.\n",
        "Interactive Mode:",
        "Omitting the --account-id option will trigger an interactive prompt"
    ]),
    epilog="Refer to the online documentation for more information: https://ibm-mas.github.io/cli/",
    formatter_class=getHelpFormatter(),
    add_help=False
)

# Execution Mode
# -----------------------------------------------------------------------------
executionArgGroup = gitops_install_arg_parser.add_argument_group("Execution Mode")
# Create mutually exclusive group for execution mode
executionModeGroup = executionArgGroup.add_mutually_exclusive_group()
executionModeGroup.add_argument(
    "--use-tekton",
    action="store_true",
    default=False,
    help="Use Tekton pipelines for execution (this is the default behavior)"
)
executionModeGroup.add_argument(
    "--direct",
    action="store_true",
    default=False,
    help="Execute directly without Tekton pipelines"
)

# GitOps Configuration
# -----------------------------------------------------------------------------
gitopsArgGroup = gitops_install_arg_parser.add_argument_group("GitOps Configuration")
gitopsArgGroup.add_argument(
    "--account-id",
    required=False,
    help="Account ID for the GitOps configuration (e.g., 'mycompany')"
)
gitopsArgGroup.add_argument(
    "--region-id",
    required=False,
    help="Region ID for the GitOps configuration"
)
gitopsArgGroup.add_argument(
    "--cluster-id",
    required=False,
    help="Cluster ID for the GitOps configuration (e.g., 'cluster1')"
)
gitopsArgGroup.add_argument(
    "--cluster-url",
    required=False,
    help="Cluster API URL"
)
gitopsArgGroup.add_argument(
    "--github-host",
    required=False,
    help="GitHub host (e.g., github.com)"
)
gitopsArgGroup.add_argument(
    "--github-org",
    required=False,
    help="GitHub organization"
)
gitopsArgGroup.add_argument(
    "--github-repo",
    required=False,
    help="GitOps repository name"
)
gitopsArgGroup.add_argument(
    "--git-branch",
    required=False,
    default="main",
    help="Git branch (default: main)"
)
gitopsArgGroup.add_argument(
    "--gitops-repo-token-secret",
    required=False,
    help="GitHub repository token secret for GitOps repository access"
)
gitopsArgGroup.add_argument(
    "--secrets-path",
    required=False,
    help="Path to secrets in AWS Secrets Manager"
)
gitopsArgGroup.add_argument(
    "--avp-aws-secret-region",
    required=False,
    help="AWS region for secrets"
)
gitopsArgGroup.add_argument(
    "--sm-aws-access-key-id",
    required=False,
    help="AWS Access Key ID for Secrets Manager access"
)
gitopsArgGroup.add_argument(
    "--sm-aws-secret-access-key",
    required=False,
    help="AWS Secret Access Key for Secrets Manager access"
)

# Cluster Configuration
# -----------------------------------------------------------------------------
clusterArgGroup = gitops_install_arg_parser.add_argument_group("Cluster Configuration")
clusterArgGroup.add_argument(
    "-c", "--mas-catalog-version",
    required=False,
    help="IBM Maximo Operator Catalog version to install"
)
clusterArgGroup.add_argument(
    "--mas-catalog-image",
    required=False,
    help="IBM Maximo Operator Catalog image"
)
clusterArgGroup.add_argument(
    "--ibm-entitlement-key",
    required=False,
    help="IBM entitlement key"
)
clusterArgGroup.add_argument(
    "--install-dro",
    required=False,
    choices=['true', 'false'],
    help="Install DRO operator (true/false)"
)
clusterArgGroup.add_argument(
    "--dro-namespace",
    required=False,
    help="DRO namespace"
)
clusterArgGroup.add_argument(
    "--dro-install-plan",
    required=False,
    help="DRO install plan"
)
clusterArgGroup.add_argument(
    "--dro-contact-email",
    required=False,
    help="DRO contact email address"
)
clusterArgGroup.add_argument(
    "--dro-contact-firstname",
    required=False,
    help="DRO contact first name"
)
clusterArgGroup.add_argument(
    "--dro-contact-lastname",
    required=False,
    help="DRO contact last name"
)
clusterArgGroup.add_argument(
    "--install-gpu",
    required=False,
    choices=['true', 'false'],
    help="Install GPU operator (true/false)"
)
clusterArgGroup.add_argument(
    "--gpu-namespace",
    required=False,
    help="GPU operator namespace"
)
clusterArgGroup.add_argument(
    "--install-cert-manager",
    required=False,
    choices=['true', 'false'],
    help="Install cert-manager (true/false)"
)
clusterArgGroup.add_argument(
    "--install-nfd",
    required=False,
    choices=['true', 'false'],
    help="Install NFD operator (true/false)"
)
clusterArgGroup.add_argument(
    "--storage-class-rwo",
    required=False,
    help="ReadWriteOnce (RWO) storage class (e.g. ibmc-block-gold)"
)
clusterArgGroup.add_argument(
    "--storage-class-rwx",
    required=False,
    help="ReadWriteMany (RWX) storage class (e.g. ibmc-file-gold-gid)"
)
clusterArgGroup.add_argument(
    "--ocp-domain",
    required=False,
    help="OCP domain"
)
clusterArgGroup.add_argument(
    "--dns-provider",
    required=False,
    help="DNS provider (e.g., cloudflare, route53, cis)"
)

# MAS Instance Configuration
# -----------------------------------------------------------------------------
instanceArgGroup = gitops_install_arg_parser.add_argument_group("MAS Instance Configuration")
instanceArgGroup.add_argument(
    "-i", "--mas-instance-id",
    required=False,
    help="MAS Instance ID"
)
instanceArgGroup.add_argument(
    "--mas-channel",
    required=False,
    help="MAS channel"
)
instanceArgGroup.add_argument(
    "--mas-domain",
    required=False,
    help="MAS domain"
)
instanceArgGroup.add_argument(
    "--mas-workspace-id",
    required=False,
    help="MAS workspace ID"
)
instanceArgGroup.add_argument(
    "--mas-workspace-name",
    required=False,
    help="MAS workspace name"
)
instanceArgGroup.add_argument(
    "--operational-mode",
    required=False,
    choices=['production', 'nonproduction'],
    help="Operational mode (production/nonproduction)"
)
instanceArgGroup.add_argument(
    "--sls-channel",
    required=False,
    help="SLS channel"
)
instanceArgGroup.add_argument(
    "--sls-instance-name",
    required=False,
    help="SLS instance name"
)
instanceArgGroup.add_argument(
    "--mongo-provider",
    required=False,
    help="MongoDB provider (e.g., aws, ibm)"
)
instanceArgGroup.add_argument(
    "--mongo-namespace",
    required=False,
    help="MongoDB namespace"
)
instanceArgGroup.add_argument(
    "--mongodb-action",
    required=False,
    help="MongoDB action (e.g., provision, configure)"
)
instanceArgGroup.add_argument(
    "--mongo-yaml-file",
    required=False,
    help="MongoDB YAML configuration file (required when mongo-provider is yaml)"
)
instanceArgGroup.add_argument(
    "--mongo-username",
    required=False,
    help="MongoDB username (required when mongo-provider is yaml)"
)
instanceArgGroup.add_argument(
    "--mongo-password",
    required=False,
    help="MongoDB password (required when mongo-provider is yaml)"
)

# Dependencies Configuration (Optional)
# -----------------------------------------------------------------------------
depsArgGroup = gitops_install_arg_parser.add_argument_group("Dependencies Configuration (Optional)")
depsArgGroup.add_argument(
    "--vpc-ipv4-cidr",
    required=False,
    help="VPC IPv4 CIDR block"
)
depsArgGroup.add_argument(
    "--aws-docdb-instance-number",
    required=False,
    help="AWS DocumentDB instance number (default: 3)"
)
depsArgGroup.add_argument(
    "--aws-docdb-engine-version",
    required=False,
    help="AWS DocumentDB engine version (default: 4.0.0)"
)
depsArgGroup.add_argument(
    "--kafka-provider",
    required=False,
    help="Kafka provider (e.g., aws, ibm)"
)
depsArgGroup.add_argument(
    "--kafka-version",
    required=False,
    help="Kafka version (default: 3.3.1)"
)
depsArgGroup.add_argument(
    "--kafka-action",
    required=False,
    help="Kafka action (e.g., provision, configure)"
)
depsArgGroup.add_argument(
    "--kafkacfg-file-name",
    required=False,
    help="Kafka configuration file name"
)
depsArgGroup.add_argument(
    "--aws-msk-instance-type",
    required=False,
    help="AWS MSK instance type"
)
depsArgGroup.add_argument(
    "--efs-action",
    required=False,
    help="EFS action (e.g., provision, deprovision)"
)
depsArgGroup.add_argument(
    "--cloud-provider",
    required=False,
    help="Cloud provider (default: aws)"
)
depsArgGroup.add_argument(
    "--ibmcloud-resourcegroup",
    required=False,
    help="IBM Cloud resource group name"
)
depsArgGroup.add_argument(
    "--ibmcloud-apikey",
    required=False,
    help="IBM Cloud API key"
)
depsArgGroup.add_argument(
    "--cos-type",
    required=False,
    help="COS provider type (ibm or ocs)"
)
depsArgGroup.add_argument(
    "--cos-resourcegroup",
    required=False,
    help="COS resource group in IBM Cloud"
)
depsArgGroup.add_argument(
    "--cos-action",
    required=False,
    help="COS action (e.g., provision, deprovision)"
)
depsArgGroup.add_argument(
    "--cos-use-hmac",
    required=False,
    help="Whether HMAC is enabled for COS (true/false)"
)
depsArgGroup.add_argument(
    "--cos-apikey",
    required=False,
    help="COS API key"
)
depsArgGroup.add_argument(
    "--avp-aws-secret-key",
    required=False,
    help="AVP AWS secret key"
)
depsArgGroup.add_argument(
    "--avp-aws-access-key",
    required=False,
    help="AVP AWS access key"
)
depsArgGroup.add_argument(
    "--github-pat",
    required=False,
    help="GitHub Personal Access Token"
)

# SMTP Configuration (Optional)
# -----------------------------------------------------------------------------
smtpArgGroup = gitops_install_arg_parser.add_argument_group("SMTP Configuration (Optional)")
smtpArgGroup.add_argument(
    "--smtp-host",
    required=False,
    help="SMTP server host"
)
smtpArgGroup.add_argument(
    "--smtp-port",
    required=False,
    help="SMTP server port"
)
smtpArgGroup.add_argument(
    "--smtp-username",
    required=False,
    help="SMTP username"
)
smtpArgGroup.add_argument(
    "--smtp-password",
    required=False,
    help="SMTP password"
)
smtpArgGroup.add_argument(
    "--smtp-from",
    required=False,
    help="SMTP from address"
)

# LDAP Configuration (Optional)
# -----------------------------------------------------------------------------
ldapArgGroup = gitops_install_arg_parser.add_argument_group("LDAP Configuration (Optional)")
ldapArgGroup.add_argument(
    "--ldap-url",
    required=False,
    help="LDAP server URL"
)
ldapArgGroup.add_argument(
    "--ldap-bind-dn",
    required=False,
    help="LDAP bind DN"
)
ldapArgGroup.add_argument(
    "--ldap-bind-password",
    required=False,
    help="LDAP bind password"
)
ldapArgGroup.add_argument(
    "--ldap-user-base-dn",
    required=False,
    help="LDAP user base DN"
)
ldapArgGroup.add_argument(
    "--ldap-group-base-dn",
    required=False,
    help="LDAP group base DN"
)
ldapArgGroup.add_argument(
    "--ldap-certificate-file",
    required=False,
    help="LDAP certificate file path"
)

# Advanced GitOps Configuration Files (Optional)
# -----------------------------------------------------------------------------
advancedFilesArgGroup = gitops_install_arg_parser.add_argument_group("Advanced GitOps Configuration Files (Optional)")
advancedFilesArgGroup.add_argument(
    "--sls-entitlement-file",
    required=False,
    help="SLS entitlement license file path (entitlement.lic)"
)
advancedFilesArgGroup.add_argument(
    "--dro-ca-certificate-file",
    required=False,
    help="DRO CA certificate file path"
)
advancedFilesArgGroup.add_argument(
    "--mas-manual-certs-yaml",
    required=False,
    help="Manual certificates YAML file path"
)
advancedFilesArgGroup.add_argument(
    "--mas-pod-template-file",
    required=False,
    help="MAS pod template YAML file path"
)
advancedFilesArgGroup.add_argument(
    "--mas-bascfg-pod-template-file",
    required=False,
    help="MAS BAS config pod template YAML file path"
)
advancedFilesArgGroup.add_argument(
    "--mas-slscfg-pod-template-file",
    required=False,
    help="MAS SLS config pod template YAML file path"
)
advancedFilesArgGroup.add_argument(
    "--mas-smtpcfg-pod-template-file",
    required=False,
    help="MAS SMTP config pod template YAML file path"
)
advancedFilesArgGroup.add_argument(
    "--mas-appcfg-pod-template-file",
    required=False,
    help="MAS app config pod template YAML file path"
)
advancedFilesArgGroup.add_argument(
    "--suite-spec-additional-properties-yaml",
    required=False,
    help="Suite spec additional properties YAML file path"
)
advancedFilesArgGroup.add_argument(
    "--suite-spec-settings-additional-properties-yaml",
    required=False,
    help="Suite spec settings additional properties YAML file path"
)
advancedFilesArgGroup.add_argument(
    "--smtp-config-ca-certificate-file",
    required=False,
    help="SMTP CA certificate file path"
)

# Applications Configuration
# -----------------------------------------------------------------------------
appsArgGroup = gitops_install_arg_parser.add_argument_group("Applications Configuration")
appsArgGroup.add_argument(
    "--mas-app-ids",
    required=False,
    help="Comma-separated list of MAS application IDs (e.g., 'manage,iot,monitor')"
)

# Per-app arguments for each supported application
for app in ['manage', 'iot', 'monitor', 'predict', 'assist', 'visualinspection', 'health', 'optimizer']:
    app_group = gitops_install_arg_parser.add_argument_group(f"{app.upper()} Configuration")
    app_group.add_argument(
        f"--{app}-channel",
        required=False,
        help=f"{app.upper()} channel"
    )
    app_group.add_argument(
        f"--{app}-db-action",
        required=False,
        choices=['install', 'configure'],
        help=f"{app.upper()} database action (install/configure)"
    )
    app_group.add_argument(
        f"--{app}-db-type",
        required=False,
        help=f"{app.upper()} database type"
    )
    app_group.add_argument(
        f"--{app}-db-host",
        required=False,
        help=f"{app.upper()} database host"
    )
    app_group.add_argument(
        f"--{app}-db-port",
        required=False,
        help=f"{app.upper()} database port"
    )
    app_group.add_argument(
        f"--{app}-db-name",
        required=False,
        help=f"{app.upper()} database name"
    )
    app_group.add_argument(
        f"--{app}-db-username",
        required=False,
        help=f"{app.upper()} database username"
    )
    app_group.add_argument(
        f"--{app}-db-password",
        required=False,
        help=f"{app.upper()} database password"
    )

# App-Specific Advanced Configuration Files
# -----------------------------------------------------------------------------
appAdvancedFilesArgGroup = gitops_install_arg_parser.add_argument_group("App-Specific Advanced Configuration Files")

# DB2 configuration files for apps that need them
for app in ['manage', 'iot', 'facilities']:
    appAdvancedFilesArgGroup.add_argument(
        f"--db2-{app}-config-file",
        required=False,
        help=f"DB2 configuration YAML file for {app}"
    )

# MAS app workspace spec files
for app in ['manage', 'iot', 'monitor', 'predict', 'assist', 'visualinspection', 'health', 'optimizer']:
    appAdvancedFilesArgGroup.add_argument(
        f"--mas-appws-spec-{app}-file",
        required=False,
        help=f"MAS app workspace spec YAML file for {app}"
    )

# MAS app spec files
for app in ['manage', 'iot', 'monitor', 'predict', 'assist', 'visualinspection', 'health', 'optimizer']:
    appAdvancedFilesArgGroup.add_argument(
        f"--mas-app-spec-{app}-file",
        required=False,
        help=f"MAS app spec YAML file for {app}"
    )

# JDBC certificate files for apps
for app in ['manage', 'iot', 'monitor', 'predict', 'assist', 'visualinspection', 'health', 'optimizer']:
    appAdvancedFilesArgGroup.add_argument(
        f"--jdbc-cert-{app}-file",
        required=False,
        help=f"JDBC certificate file for {app}"
    )

# Manage-specific files
appAdvancedFilesArgGroup.add_argument(
    "--mas-app-global-secrets-manage-file",
    required=False,
    help="MAS app global secrets file for manage"
)

# More Options
# -----------------------------------------------------------------------------
otherArgGroup = gitops_install_arg_parser.add_argument_group("More")
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
    "--no-confirm",
    required=False,
    action="store_true",
    default=False,
    help="Launch the installation without prompting for confirmation",
)
otherArgGroup.add_argument(
    "-h", "--help",
    action="help",
    default=False,
    help="Show this help message and exit",
)
