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

from .. import __version__ as packageVersion
from ..cli import getHelpFormatter

backupArgParser = argparse.ArgumentParser(
    prog='mas backup',
    description="\n".join([
        f"IBM Maximo Application Suite Admin CLI v{packageVersion}",
        "Backup a MAS instance by configuring and launching the MAS Backup Tekton Pipeline.\n",
        "Interactive Mode:",
        "Omitting the --instance-id option will trigger an interactive prompt"
    ]),
    epilog="Refer to the online documentation for more information: https://ibm-mas.github.io/cli/",
    formatter_class=getHelpFormatter(),
    add_help=False
)

masArgGroup = backupArgParser.add_argument_group(
    'MAS Instance',
    'Specify the MAS instance to backup.'
)
masArgGroup.add_argument(
    '-i', '--instance-id',
    dest='mas_instance_id',
    required=False,
    help="MAS Instance ID to backup"
)

backupArgGroup = backupArgParser.add_argument_group(
    'Backup Configuration',
    'Configure backup version and storage size.'
)
backupArgGroup.add_argument(
    '--backup-version',
    required=False,
    help="Version/timestamp for the backup (auto-generated if not provided)"
)
backupArgGroup.add_argument(
    '--backup-storage-size',
    required=False,
    help="Size of the backup PVC storage (default: 20Gi)"
)
backupArgGroup.add_argument(
    '--clean-backup',
    dest='clean_backup',
    required=False,
    action="store_const",
    const="true",
    default="true",
    help="Clean backup and config workspaces after completion (default: true)"
)
backupArgGroup.add_argument(
    '--no-clean-backup',
    dest='clean_backup',
    required=False,
    action="store_const",
    const="false",
    help="Do not clean backup and config workspaces after completion"
)

uploadArgGroup = backupArgParser.add_argument_group(
    'Upload Configuration',
    'Configure backup archive upload to S3 or Artifactory.'
)
uploadArgGroup.add_argument(
    '--upload-backup',
    required=False,
    action='store_true',
    default=False,
    help="Upload the backup archive after completion"
)
uploadArgGroup.add_argument(
    '--aws-access-key-id',
    required=False,
    help="AWS Access Key ID for S3 upload"
)
uploadArgGroup.add_argument(
    '--aws-secret-access-key',
    required=False,
    help="AWS Secret Access Key for S3 upload"
)
uploadArgGroup.add_argument(
    '--s3-bucket-name',
    required=False,
    help="S3 bucket name for backup upload"
)
uploadArgGroup.add_argument(
    '--s3-region',
    required=False,
    help="AWS region for S3 bucket"
)
uploadArgGroup.add_argument(
    '--artifactory-url',
    required=False,
    help="Artifactory URL for backup upload"
)
uploadArgGroup.add_argument(
    '--artifactory-repository',
    required=False,
    help="Artifactory repository for backup upload"
)

manageAppArgGroup = backupArgParser.add_argument_group(
    'Manage Application Backup',
    'Configure backup of the Manage application and its database.'
)
manageAppArgGroup.add_argument(
    '--backup-manage-app',
    dest='backup_manage_app',
    required=False,
    action="store_const",
    const="true",
    help="Backup the Manage application"
)
manageAppArgGroup.add_argument(
    '--manage-workspace-id',
    dest='manage_workspace_id',
    required=False,
    help="Manage workspace ID"
)
manageAppArgGroup.add_argument(
    '--backup-manage-db',
    dest='backup_manage_db',
    required=False,
    action="store_const",
    const="true",
    help="Backup the Manage application database (Db2)"
)
manageAppArgGroup.add_argument(
    '--manage-db2-namespace',
    dest='manage_db2_namespace',
    required=False,
    help="Manage Db2 namespace (default: db2u)"
)
manageAppArgGroup.add_argument(
    '--manage-db2-instance-name',
    dest='manage_db2_instance_name',
    required=False,
    help="Manage Db2 instance name"
)
manageAppArgGroup.add_argument(
    '--manage-db2-backup-type',
    dest='manage_db2_backup_type',
    required=False,
    choices=["offline", "online"],
    help="Manage Db2 backup type: offline (database unavailable) or online (database remains available)"
)

componentsArgGroup = backupArgParser.add_argument_group(
    'Components',
    'Configure which components to include in the backup.'
)
componentsArgGroup.add_argument(
    '--include-sls',
    required=False,
    action="store_const",
    const="true",
    default="true",
    help="Include SLS in backup (default: true)"
)
componentsArgGroup.add_argument(
    '--exclude-sls',
    dest='include_sls',
    required=False,
    action="store_const",
    const="false",
    help="Exclude SLS from backup (use if SLS is external)"
)

depsArgGroup = backupArgParser.add_argument_group(
    'Dependencies Configuration',
    'Configure MongoDB, SLS, and Certificate Manager settings.'
)
depsArgGroup.add_argument(
    '--mongodb-namespace',
    required=False,
    help="MongoDB namespace (default: mongoce)"
)
depsArgGroup.add_argument(
    '--mongodb-instance-name',
    required=False,
    help="MongoDB instance name (default: mas-mongo-ce)"
)
depsArgGroup.add_argument(
    '--mongodb-provider',
    required=False,
    choices=["community"],
    help="MongoDB provider (only community is supported for backup)"
)
depsArgGroup.add_argument(
    '--sls-namespace',
    required=False,
    help="SLS namespace (default: ibm-sls)"
)
depsArgGroup.add_argument(
    '--cert-manager-provider',
    required=False,
    choices=["redhat", "ibm"],
    help="Certificate manager provider (default: redhat)"
)

# More Options
# -----------------------------------------------------------------------------
otherArgGroup = backupArgParser.add_argument_group(
    'More',
    'Additional options including development mode, Artifactory credentials, and confirmation prompts.'
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
    "--dev-mode",
    required=False,
    action="store_true",
    default=False,
    help="Configure backup for development mode"
)
otherArgGroup.add_argument(
    '--no-confirm',
    required=False,
    action='store_true',
    default=False,
    help="Launch the backup without prompting for confirmation"
)
otherArgGroup.add_argument(
    '--skip-pre-check',
    required=False,
    action='store_true',
    default=False,
    help="Skips the 'pre-backup-check' task in the backup pipeline"
)
otherArgGroup.add_argument(
    '-h', "--help",
    action='help',
    default=False,
    help="Show this help message and exit"
)
