import argparse
from os import path

from . import __version__ as packageVersion
from .cli import getHelpFormatter

def isValidFile(parser, arg) -> str:
    if not path.exists(arg):
        parser.error(f"Error: The file {arg} does not exist")
    else:
        return arg

installArgParser = argparse.ArgumentParser(
    prog='mas uninstall',
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
catArgGroup = installArgParser.add_argument_group('MAS Catalog Selection & Entitlement')
catArgGroup.add_argument(
    '-c', '--mas-catalog-version',
    required=False,
    help=""
)
catArgGroup.add_argument(
    '--ibm-entitlement-key',
    required=False,
    help=""
)

# MAS Basic Configuration
# -----------------------------------------------------------------------------
masArgGroup = installArgParser.add_argument_group('MAS Basic Configuration')
masArgGroup.add_argument(
    '-i', '--mas-instance-id',
    required=False,
    help=""
)
masArgGroup.add_argument(
    '-w', '--mas-workspace-id',
    required=False,
    help=""
)
masArgGroup.add_argument(
    '-W', '--mas-workspace-name',
    required=False,
    help=""
)
masArgGroup.add_argument(
    '--mas-channel',
    required=False,
    help=""
)

# MAS Advanced Configuration
# -----------------------------------------------------------------------------
masAdvancedArgGroup = installArgParser.add_argument_group('MAS Advanced Configuration')
masAdvancedArgGroup.add_argument(
    '--additional-configs',
    required=False,
    help=""
)
masAdvancedArgGroup.add_argument(
    '--non-prod',
    required=False,
    help="",
    action="store_true"
)
masAdvancedArgGroup.add_argument(
    '--mas-trust-default-cas',
    required=False,
    help=""
)
masAdvancedArgGroup.add_argument(
    '--workload-scale-profile',
    required=False,
    help=""
)
masAdvancedArgGroup.add_argument(
    '--mas-pod-templates-dir',
    required=False,
    help=""
)

# Storage
# -----------------------------------------------------------------------------
storageArgGroup = installArgParser.add_argument_group('Storage')
storageArgGroup.add_argument(
    '--storage-class-rwo',
    required=False,
    help=""
)
storageArgGroup.add_argument(
    '--storage-class-rwx',
    required=False,
    help=""
)
storageArgGroup.add_argument(
    '--storage-pipeline',
    required=False,
    help=""
)
storageArgGroup.add_argument(
    '--storage-accessmode',
    required=False,
    help="",
    choices=["ReadOnlyMany", "ReadWriteMany", "ReadWriteOnce", "ReadWriteOncePod"]
)

# IBM Suite License Service
# -----------------------------------------------------------------------------
slsArgGroup = installArgParser.add_argument_group('IBM Suite License Service')
slsArgGroup.add_argument(
    '--license-file',
    required=False,
    help="",
    type=lambda x: isValidFile(installArgParser, x)
)

# IBM Data Reporting Operator (DRO)
# -----------------------------------------------------------------------------
droArgGroup = installArgParser.add_argument_group('IBM Data Reporting Operator (DRO)')
droArgGroup.add_argument(
    '--uds-email',
    dest='uds_contact_email',
    required=False,
    help=""
)
droArgGroup.add_argument(
    '--uds-firstname',
    dest='uds_contact_firstname',
    required=False,
    help=""
)
droArgGroup.add_argument(
    '--uds-lastname',
    dest='uds_contact_lastname',
    required=False,
    help=""
)
droArgGroup.add_argument(
    '--dro-namespace',
    required=False,
    help=""
)

# MongoDb Community Operator
# -----------------------------------------------------------------------------
mongoArgGroup = installArgParser.add_argument_group('MongoDb Community Operator')
mongoArgGroup.add_argument(
    '--mongodb-namespace',
    required=False,
    help=""
)

# OCP Configuration
# -----------------------------------------------------------------------------
ocpArgGroup = installArgParser.add_argument_group('OCP Configuration')
ocpArgGroup.add_argument(
    '--ocp-ingress-tls-secret-name',
    required=False,
    help=""
)

# MAS Applications
# -----------------------------------------------------------------------------
masAppsArgGroup = installArgParser.add_argument_group('MAS Applications')
masAppsArgGroup.add_argument(
    '--assist-channel',
    required=False,
    help=""
)
masAppsArgGroup.add_argument(
    '--iot-channel',
    required=False,
    help=""
)
masAppsArgGroup.add_argument(
    '--monitor-channel',
    required=False,
    help=""
)
masAppsArgGroup.add_argument(
    '--manage-channel',
    required=False,
    help=""
)
masAppsArgGroup.add_argument(
    '--predict-channel',
    required=False,
    help=""
)
masAppsArgGroup.add_argument(
    '--visualinspection-channel',
    required=False,
    help=""
)
masAppsArgGroup.add_argument(
    '--optimizer-channel',
    required=False,
    help=""
)
masAppsArgGroup.add_argument(
    '--optimizer-plan',
    required=False,
    help=""
)

# IBM Cloud Pak for Data
# -----------------------------------------------------------------------------
cpdAppsArgGroup = installArgParser.add_argument_group('IBM Cloud Pak for Data')
cpdAppsArgGroup.add_argument(
    '--cp4d-version',
    dest='cpd_product_version',
    required=False,
    help=""
)
cpdAppsArgGroup.add_argument(
    '--cp4d-install-spss',
    dest='cpd_install_spss',
    required=False,
    help="",
    action="store_const",
    const="install"
)
cpdAppsArgGroup.add_argument(
    '--cp4d-installopenscale',
    dest='cpd_install_openscale',
    required=False,
    help="",
    action="store_const",
    const="install"
)
cpdAppsArgGroup.add_argument(
    '--cp4d-install-cognos',
    dest='cpd_install_cognos',
    required=False,
    help="",
    action="store_const",
    const="install"
)

# IBM Db2 Universal Operator
# -----------------------------------------------------------------------------
db2AppsArgGroup = installArgParser.add_argument_group('IBM Db2 Universal Operator')
db2AppsArgGroup.add_argument(
    '--db2-namespace',
    required=False,
    help=""
)
db2AppsArgGroup.add_argument(
    '--db2-channel',
    required=False,
    help=""
)
db2AppsArgGroup.add_argument(
    '--db2-system',
    dest='db2_action_system',
    required=False,
    help="",
    action="store_const",
    const="install"
)
db2AppsArgGroup.add_argument(
    '--db2-manage',
    dest='db2_action_manage',
    required=False,
    help="",
    action="store_const",
    const="install"
)
db2AppsArgGroup.add_argument(
    '--db2-type',
    required=False,
    help=""
)

db2AppsArgGroup.add_argument(
    '--db2-affinity-key',
    required=False,
    help=""
)
db2AppsArgGroup.add_argument(
    '--db2-affinity-value',
    required=False,
    help=""
)
db2AppsArgGroup.add_argument(
    '--db2-tolerate-key',
    required=False,
    help=""
)
db2AppsArgGroup.add_argument(
    '--db2-tolerate-value',
    required=False,
    help=""
)
db2AppsArgGroup.add_argument(
    '--db2-tolerate-effect',
    required=False,
    help=""
)
db2AppsArgGroup.add_argument(
    '--db2-cpu-requests',
    required=False,
    help=""
)
db2AppsArgGroup.add_argument(
    '--db2-cpu-limits',
    required=False,
    help=""
)
db2AppsArgGroup.add_argument(
    '--db2-memory-requests',
    required=False,
    help=""
)
db2AppsArgGroup.add_argument(
    '--db2-memory-limits',
    required=False,
    help=""
)
db2AppsArgGroup.add_argument(
    '--db2-backup-storage',
    dest='db2_backup_storage_size',
    required=False,
    help=""
)
db2AppsArgGroup.add_argument(
    '--db2-data-storage',
    dest='db2_data_storage_size',
    required=False,
    help=""
)
db2AppsArgGroup.add_argument(
    '--db2-logs-storage',
    dest='db2_logs_storage_size',
    required=False,
    help=""
)
db2AppsArgGroup.add_argument(
    '--db2-meta-storage',
    dest='db2_meta_storage_size',
    required=False,
    help=""
)
db2AppsArgGroup.add_argument(
    '--db2-temp-storage',
    dest='db2_temp_storage_size',
    required=False,
    help=""
)







#   # Dependencies - Kafka common arguments
#   --kafka-provider)
#     export KAFKA_ACTION_SYSTEM=install
#     export KAFKA_PROVIDER=$1 && shift
#     ;;
#   --kafka-username)
#     export AWS_KAFKA_USER_NAME=$1
#     export KAFKA_USER_NAME=$1 && shift
#     ;;
#   --kafka-password)
#     export AWS_KAFKA_USER_PASSWORD=$1
#     export KAFKA_USER_PASSWORD=$1 && shift
#     ;;

#   # Dependencies - Kafka (AMQ & Strimzi)
#   --kafka-namespace)
#     export KAFKA_NAMESPACE=$1 && shift
#     ;;
#   --kafka-version)
#     export KAFKA_VERSION=$1 && shift
#     ;;

#   # Dependencies - Kafka (AWS MSK)
#   --msk-instance-type)
#     export AWS_MSK_INSTANCE_TYPE=$1 && shift
#     ;;
#   --msk-instance-nodes)
#     export AWS_MSK_INSTANCE_NUMBER=$1 && shift
#     ;;
#   --msk-instance-volume-size)
#     export AWS_MSK_VOLUME_SIZE=$1 && shift
#     ;;
#   --msk-cidr-az1)
#     export AWS_MSK_CIDR_AZ1=$1 && shift
#     ;;
#   --msk-cidr-az2)
#     export AWS_MSK_CIDR_AZ2=$1 && shift
#     ;;
#   --msk-cidr-az3)
#     export AWS_MSK_CIDR_AZ3=$1 && shift
#     ;;
#   --msk-cidr-ingress)
#     export AWS_MSK_INGRESS_CIDR=$1 && shift
#     ;;
#   --msk-cidr-egress)
#     export AWS_MSK_EGRESS_CIDR=$1 && shift
#     ;;

#   # Dependencies - Kafka (IBM Cloud Event Streams)
#   --eventstreams-resource-group)
#     export EVENTSTREAMS_RESOURCEGROUP=$1 && shift
#     ;;
#   --eventstreams-instance-name)
#     export EVENTSTREAMS_NAME=$1 && shift
#     ;;
#   --eventstreams-instance-location)
#     export EVENTSTREAMS_LOCATION=$1 && shift
#     ;;



#   # Manage commands - Server bundle configuration
#   --manage-server-bundle-size)
#     export MAS_APP_SETTINGS_SERVER_BUNDLES_SIZE=$1 && shift
#     if [[ "$MAS_APP_SETTINGS_SERVER_BUNDLES_SIZE" == "jms" || "$MAS_APP_SETTINGS_SERVER_BUNDLES_SIZE" == "snojms" ]]; then
#       export MAS_APP_SETTINGS_PERSISTENT_VOLUMES_FLAG=true
#     fi
#     ;;
#   --manage-jms)
#     if [[ "$MAS_APP_SETTINGS_SERVER_BUNDLES_SIZE" == "jms" || "$MAS_APP_SETTINGS_SERVER_BUNDLES_SIZE" == "snojms" ]]; then
#       export MAS_APP_SETTINGS_DEFAULT_JMS=true
#       export MAS_APP_SETTINGS_PERSISTENT_VOLUMES_FLAG=true
#     fi
#     ;;
#   --manage-demodata)
#     export MAS_APP_SETTINGS_DEMODATA=true
#     ;;
#   --manage-jdbc)
#     export MAS_APPWS_BINDINGS_JDBC_MANAGE=$1 && shift
#     ;;

#   # Manage commands - Components
#   --manage-components)
#     export MAS_APPWS_COMPONENTS=$1 && shift
#    ;;

#   # Manage commands - Customization archive
#   --manage-customization-archive-name)
#     export MAS_APP_SETTINGS_CUSTOMIZATION_ARCHIVE_NAME=$1 && shift
#     ;;
#   --manage-customization-archive-url)
#     export MAS_APP_SETTINGS_CUSTOMIZATION_ARCHIVE_URL=$1 && shift
#     ;;
#   --manage-customization-archive-username)
#     export MAS_APP_SETTINGS_CUSTOMIZATION_ARCHIVE_USERNAME=$1 && shift
#     ;;
#   --manage-customization-archive-password)
#     export MAS_APP_SETTINGS_CUSTOMIZATION_ARCHIVE_PASSWORD=$1 && shift
#     ;;

#   # Manage commands - Dabatase tablespaces
#   --manage-db-tablespace)
#     export MAS_APP_SETTINGS_TABLESPACE=$1 && shift
#     ;;

#   --manage-db-indexspace)
#     export MAS_APP_SETTINGS_INDEXSPACE=$1 && shift
#     ;;

#   --manage-db-schema)
#     export MAS_APP_SETTINGS_DB2_SCHEMA=$1 && shift
#     ;;

#   # Manage commands - Database encryption keys
#   --manage-crypto-key)
#     export MAS_APP_SETTINGS_CRYPTO_KEY=$1 && shift
#     ;;
#   --manage-cryptox-key)
#     export MAS_APP_SETTINGS_CRYPTOX_KEY=$1 && shift
#     ;;
#   --manage-old-crypto-key)
#     export MAS_APP_SETTINGS_OLD_CRYPTO_KEY=$1 && shift
#     ;;
#   --manage-old-cryptox-key)
#     export MAS_APP_SETTINGS_OLD_CRYPTOX_KEY=$1 && shift
#     ;;
#   --manage-override-encryption-secrets)
#     export MAS_APP_SETTINGS_OVERRIDE_ENCRYPTION_SECRETS_FLAG=true
#     ;;

#   # Manage commands - Base & secondary languages
#   --manage-base-language)
#     export MAS_APP_SETTINGS_BASE_LANG=$1 && shift
#     ;;

#   --manage-secondary-languages)
#     export MAS_APP_SETTINGS_SECONDARY_LANGS=$1 && shift
#     ;;

#   # Manage commands - Server timezone
#   --manage-server-timezone)
#     export MAS_APP_SETTINGS_SERVER_TIMEZONE=$1 && shift
#     export DB2_TIMEZONE=$MAS_APP_SETTINGS_SERVER_TIMEZONE # If used, set Manage dedicated Db2 timezone to be same as Manage server timezone
#     ;;

#   # Cloud Provider Commands - IBM Cloud
#   --ibmcloud-apikey)
#     export IBMCLOUD_APIKEY=$1 && shift
#     ;;

#   # Cloud Provider Commands - AWS
#   --aws-region)
#     export AWS_REGION=$1 && shift
#     ;;
#   --aws-access-key-id)
#     export AWS_ACCESS_KEY_ID=$1 && shift
#     ;;
#   --aws-secret-access-key)
#     export AWS_SECRET_ACCESS_KEY=$1 && shift
#     ;;
#   --aws-vpc-id)
#     export VPC_ID=$1 && shift
#     ;;

#   # Other Commands
#   --skip-pre-check)
#     SKIP_PRE_CHECK=true
#     ;;
#   --dev-mode)
#     DEV_MODE=true
#     ;;
#   --no-wait-for-pvcs)
#     WAIT_FOR_PVCS=false
#     ;;
#   --no-confirm)
#     NO_CONFIRM=true
#     ;;
#   --accept-license)
#     LICENSE_ACCEPTED=true
#     ;;
#   -h|--help)
#     install_help
#     ;;
#   *)
#     # unknown option
#     echo -e "${COLOR_RED}Usage Error: Unsupported option \"${key}\"${TEXT_RESET}\n"
#     install_help
#     exit 1
#     ;;


otherArgGroup = installArgParser.add_argument_group('More')
otherArgGroup.add_argument(
    '--dev-mode',
    required=False,
    action='store_true',
    default=False,
    help="Configure installation for development mode",
)
otherArgGroup.add_argument(
    '--no-confirm',
    required=False,
    action='store_true',
    default=False,
    help="Launch the upgrade without prompting for confirmation",
)
otherArgGroup.add_argument(
    '-h', "--help",
    action='help',
    default=False,
    help="Show this help message and exit",
)
