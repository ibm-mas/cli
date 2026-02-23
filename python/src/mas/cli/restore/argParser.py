# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
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

restoreArgParser = argparse.ArgumentParser(
    prog='mas restore',
    description="\n".join([
        f"IBM Maximo Application Suite Admin CLI v{packageVersion}",
        "Restore a MAS instance from backup by configuring and launching the MAS Restore Tekton Pipeline.\n",
        "Interactive Mode:",
        "Omitting the --instance-id option will trigger an interactive prompt"
    ]),
    epilog="Refer to the online documentation for more information: https://ibm-mas.github.io/cli/",
    formatter_class=getHelpFormatter(),
    add_help=False
)

masArgGroup = restoreArgParser.add_argument_group(
    'MAS Instance',
    'Specify the MAS instance to restore.'
)
masArgGroup.add_argument(
    '-i', '--instance-id',
    dest='mas_instance_id',
    required=False,
    help="MAS Instance ID to restore, must match the instance ID of the backup."
)

masArgGroup.add_argument(
    '--mas-domain-restore',
    dest='mas_domain_on_restore',
    required=False,
    help="MAS Domain to restore. If not specified, the domain will be taken from the backup."
)

masArgGroup.add_argument(
    '--sls-url-restore',
    dest='sls_url_on_restore',
    required=False,
    help="SLS URL to restore in Suite configuration. If not specified, the url will be taken from the backup."
)

masArgGroup.add_argument(
    '--dro-url-restore',
    dest='dro_url_on_restore',
    required=False,
    help="DRO URL to restore in Suite configuration. If not specified, the url will be taken from the backup."
)

masArgGroup.add_argument(
    '--include-slscfg-from-backup',
    dest='include_slscfg_from_backup',
    required=False,
    action="store_const",
    const="true",
    default="true",
    help="Use SLS config from backup during Suite restore."
)

masArgGroup.add_argument(
    '--exclude-slscfg-from-backup',
    dest='include_slscfg_from_backup',
    required=False,
    action="store_const",
    const="false",
    help="Exclude SLS config from backup during Suite restore."
)

masArgGroup.add_argument(
    '--sls-cfg-file',
    dest='sls_cfg_file',
    required=False,
    help="SLS config file path to restore, must be provided if own SLS is used."
)

masArgGroup.add_argument(
    '--dro-cfg-file',
    dest='dro_cfg_file',
    required=False,
    help="DRO config file path to restore, must be provided if own DRO is used."
)

masArgGroup.add_argument(
    '--include-drocfg-from-backup',
    dest='include_drocfg_from_backup',
    required=False,
    action="store_const",
    const="true",
    default="true",
    help="Include DRO config from backup during Suite restore."
)

masArgGroup.add_argument(
    '--exclude-drocfg-from-backup',
    dest='include_drocfg_from_backup',
    required=False,
    action="store_const",
    const="false",
    help="Exclude DRO config from backup during Suite restore."
)

restoreArgGroup = restoreArgParser.add_argument_group(
    'Restore Configuration',
    'Configure backup version to be restored and storage size.'
)
restoreArgGroup.add_argument(
    '--restore-version',
    required=False,
    help="Version/timestamp used in backup. Example: YYYYMMDD-HHMMSS"
)
restoreArgGroup.add_argument(
    '--backup-storage-size',
    required=False,
    help="Size of the PVC storage, must be bigger than backup archive size. (default: 20Gi)"
)
restoreArgGroup.add_argument(
    '--clean-backup',
    dest='clean_backup',
    required=False,
    action="store_const",
    const="true",
    default="true",
    help="Clean backup and config workspaces after completion (default: true)"
)
restoreArgGroup.add_argument(
    '--no-clean-backup',
    dest='clean_backup',
    required=False,
    action="store_const",
    const="false",
    help="Do not clean backup and config workspaces after completion"
)

mongoArgGroup = restoreArgParser.add_argument_group(
    'MongoDB Restore Configuration',
    'Configure MongoDB for restore.'
)

mongoArgGroup.add_argument(
    '--override-mongodb-storageclass',
    dest='override_mongodb_storageclass',
    required=False,
    action="store_const",
    const="true",
    help="Override MongoDb PVC storageclass"
)

mongoArgGroup.add_argument(
    '--mongodb-storage-class-name',
    required=False,
    dest="mongodb_storageclass_name",
    help="ReadWriteOnce Storage class for MongoDb PVC"
)

downloadArgGroup = restoreArgParser.add_argument_group(
    'Download Configuration',
    'Configure backup archive download from S3 or Artifactory.'
)
downloadArgGroup.add_argument(
    '--download-backup',
    required=False,
    action='store_true',
    default=False,
    help="Download the backup archive from S3 or Artifactory"
)
downloadArgGroup.add_argument(
    '--aws-access-key-id',
    required=False,
    help="AWS Access Key ID for S3 download"
)
downloadArgGroup.add_argument(
    '--aws-secret-access-key',
    required=False,
    help="AWS Secret Access Key for S3 download"
)
downloadArgGroup.add_argument(
    '--s3-bucket-name',
    required=False,
    help="S3 bucket name for backup download"
)
downloadArgGroup.add_argument(
    '--s3-region',
    required=False,
    help="AWS region for S3 bucket"
)
downloadArgGroup.add_argument(
    '--s3-endpoint-url',
    required=False,
    help="Endpoint url for S3 bucket"
)
downloadArgGroup.add_argument(
    '--artifactory-url',
    required=False,
    help="Artifactory URL for backup download"
)
downloadArgGroup.add_argument(
    '--artifactory-repository',
    required=False,
    help="Artifactory repository for backup download"
)
downloadArgGroup.add_argument(
    '--custom-backup-archive-name',
    required=False,
    dest="backup_archive_name",
    help="Custom backup archive name to download from S3 or Artifactory"
)

manageAppArgGroup = restoreArgParser.add_argument_group(
    'Manage Application Restore',
    'Configure restore of the Manage application and its database.'
)
manageAppArgGroup.add_argument(
    '--restore-manage-app',
    dest='restore_manage_app',
    required=False,
    action="store_const",
    const="true",
    help="Restore the Manage application"
)
manageAppArgGroup.add_argument(
    '--restore-manage-db',
    dest='restore_manage_db',
    required=False,
    action="store_const",
    const="true",
    help="Restore the Manage application database (Db2)"
)

manageAppArgGroup.add_argument(
    '--override-manage-app-storageclass',
    dest='manage_app_override_storageclass',
    required=False,
    action="store_const",
    const="true",
    help="Override Manage Application PVC storageclass"
)

manageAppArgGroup.add_argument(
    '--manage-app-storage-class-rwx',
    required=False,
    dest="manage_app_storage_class_rwx",
    help="ReadWriteMany Storage class for Manage App PVC"
)

manageAppArgGroup.add_argument(
    '--manage-app-storage-class-rwo',
    required=False,
    dest="manage_app_storage_class_rwo",
    help="ReadWriteOnce Storage class for Manage App PVC"
)

manageAppArgGroup.add_argument(
    '--override-manage-db-storageclass',
    dest='manage_db_override_storageclass',
    required=False,
    action="store_const",
    const="true",
    help="Override database (Db2) PVC storageclass"
)

manageAppArgGroup.add_argument(
    '--manage-db-meta-storage-class',
    required=False,
    dest="manage_db_meta_storage_class",
    help="Storage class for DB2 Meta storage"
)

manageAppArgGroup.add_argument(
    '--manage-db-data-storage-class',
    required=False,
    dest="manage_db_data_storage_class",
    help="Storage class for DB2 Data storage"
)
manageAppArgGroup.add_argument(
    '--manage-db-backup-storage-class',
    required=False,
    dest="manage_db_backup_storage_class",
    help="Storage class for DB2 Backup storage"
)
manageAppArgGroup.add_argument(
    '--manage-db-logs-storage-class',
    required=False,
    dest="manage_db_logs_storage_class",
    help="Storage class for DB2 Logs storage"
)
manageAppArgGroup.add_argument(
    '--manage-db-temp-storage-class',
    required=False,
    dest="manage_db_temp_storage_class",
    help="Storage class for DB2 Temp storage"
)


componentsArgGroup = restoreArgParser.add_argument_group(
    'Components',
    'Configure which components to include in the restore.'
)

componentsArgGroup.add_argument(
    '--include-grafana',
    required=False,
    action="store_const",
    const="true",
    default="true",
    help="Include Grafana in restore (default: true)"
)
componentsArgGroup.add_argument(
    '--exclude-grafana',
    dest='include_grafana',
    required=False,
    action="store_const",
    const="false",
    help="Skip installing Grafana."
)

componentsArgGroup.add_argument(
    '--include-dro',
    required=False,
    action="store_const",
    const="true",
    default="true",
    help="Include DRO in restore (default: true)"
)
componentsArgGroup.add_argument(
    '--exclude-dro',
    dest='include_dro',
    required=False,
    action="store_const",
    const="false",
    help="Skip installing DRO."
)

componentsArgGroup.add_argument(
    '--include-sls',
    required=False,
    action="store_const",
    const="true",
    default="true",
    help="Include SLS in restore (default: true)"
)
componentsArgGroup.add_argument(
    '--exclude-sls',
    dest='include_sls',
    required=False,
    action="store_const",
    const="false",
    help="Exclude SLS from restore (use if SLS is external)"
)

slsArgGroup = restoreArgParser.add_argument_group(
    "IBM Suite License Service Operator",
    "Configure IBM Suite License Service Operator (SLS) domain during restore."
)
slsArgGroup.add_argument(
    "--sls-domain",
    dest='sls_domain',
    required=False,
    help="SLS domain to use during SLS instance restore (optional)."
)

droArgGroup = restoreArgParser.add_argument_group(
    "IBM Data Reporting Operator",
    "Configure IBM Data Reporting Operator (DRO) with contact information and namespace settings for usage data collection."
)
droArgGroup.add_argument(
    "--ibm-entitlement-key",
    required=False,
    help="IBM entitlement key"
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

# More Options
# -----------------------------------------------------------------------------
otherArgGroup = restoreArgParser.add_argument_group(
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
    help="Configure restore in development mode"
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
    help="Skips the 'pre-restore-check' task in the restore pipeline"
)
otherArgGroup.add_argument(
    '-h', "--help",
    action='help',
    default=False,
    help="Show this help message and exit"
)
