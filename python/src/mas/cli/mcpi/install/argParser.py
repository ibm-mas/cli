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
from os import path

from ... import __version__ as packageVersion
from ...cli import getHelpFormatter


def isValidFile(parser, arg) -> str:
    """Validate that a file path exists.

    Args:
        parser (argparse.ArgumentParser): The argument parser instance
        arg (str): File path to validate

    Returns:
        str: The validated file path
    """
    if not path.exists(arg):
        parser.error(f"Error: The file {arg} does not exist")
    else:
        return arg


mcpiInstallArgParser = argparse.ArgumentParser(
    prog="mas mcpi-install",
    description="\n".join(
        [
            f"IBM Maximo Application Suite Admin CLI v{packageVersion}",
            "Install Maximo Cluster Performance Insights (MCPI) by configuring and launching the Tekton Pipeline.\n",
            "Interactive Mode:",
            "Omitting the --mas-instance-id option will trigger an interactive prompt",
        ]
    ),
    epilog="Refer to the online documentation for more information: https://ibm-mas.github.io/cli/",
    formatter_class=getHelpFormatter(),
    add_help=False,
)

# MAS Catalog Selection & Entitlement
# -----------------------------------------------------------------------------
catArgGroup = mcpiInstallArgParser.add_argument_group("MAS Catalog Selection & Entitlement")
catArgGroup.add_argument("-c", "--mas-catalog-version", required=False, help="IBM Maximo Operator Catalog to install")
catArgGroup.add_argument(
    "--mas-catalog-digest", required=False, help="IBM Maximo Operator Catalog Digest, only required when installing development catalog sources"
)
catArgGroup.add_argument("--ibm-entitlement-key", required=False, help="IBM entitlement key")

# MCPI Basic Configuration
# -----------------------------------------------------------------------------
mcpiArgGroup = mcpiInstallArgParser.add_argument_group("MCPI Basic Configuration")
mcpiArgGroup.add_argument("-i", "--mas-instance-id", required=False, dest="mas_instance_id", help="MAS Instance ID")

# MCPI Advanced Configuration
# -----------------------------------------------------------------------------
mcpiAdvancedArgGroup = mcpiInstallArgParser.add_argument_group("MCPI Advanced Configuration")
mcpiAdvancedArgGroup.add_argument("--mcpi-channel", required=False, dest="mcpi_channel", help="Subscription channel for Maximo Cluster Performance Insights")
mcpiAdvancedArgGroup.add_argument(
    "--routing-mode", required=False, dest="routing_mode", choices=["subdomain", "path"], help="Routing mode for MCPI (subdomain or path)"
)
mcpiAdvancedArgGroup.add_argument("--manual-route-mgmt", required=False, dest="manual_route_mgmt", help="Disable automatic route management for MCPI")

# MAS Advanced Configuration
# -----------------------------------------------------------------------------
masAdvancedArgGroup = mcpiInstallArgParser.add_argument_group("MAS Advanced Configuration")
masAdvancedArgGroup.add_argument("--additional-configs", required=False, help="Path to a directory containing additional configuration files to be applied")

# Storage
# -----------------------------------------------------------------------------
storageArgGroup = mcpiInstallArgParser.add_argument_group("Storage")
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
slsArgGroup = mcpiInstallArgParser.add_argument_group("IBM Suite License Service")
slsArgGroup.add_argument("--license-file", required=False, help="Path to MAS license file", type=lambda x: isValidFile(mcpiInstallArgParser, x))
slsArgGroup.add_argument("--sls-namespace", required=False, help="Customize the SLS install namespace", default="ibm-sls")
slsArgGroup.add_argument("--dedicated-sls", action="store_true", default=False, help="Set the SLS namespace to mas-<instanceid>-sls")

# IBM Data Reporting Operator (DRO)
# -----------------------------------------------------------------------------
droArgGroup = mcpiInstallArgParser.add_argument_group("IBM Data Reporting Operator (DRO)")
droArgGroup.add_argument("--contact-email", "--uds-email", dest="dro_contact_email", required=False, help="Contact e-mail address")
droArgGroup.add_argument("--contact-firstname", "--uds-firstname", dest="dro_contact_firstname", required=False, help="Contact first name")
droArgGroup.add_argument("--contact-lastname", "--uds-lastname", dest="dro_contact_lastname", required=False, help="Contact last name")
droArgGroup.add_argument("--dro-namespace", required=False, help="Namespace for the Data Reporting Operator")

# MongoDb Community Operator
# -----------------------------------------------------------------------------
mongoArgGroup = mcpiInstallArgParser.add_argument_group("MongoDb Community Operator")
mongoArgGroup.add_argument("--mongodb-namespace", required=False, help="Namespace for the MongoDB Community Operator")

# Development Mode
# -----------------------------------------------------------------------------
devArgGroup = mcpiInstallArgParser.add_argument_group("Development Mode")
devArgGroup.add_argument("--artifactory-username", required=False, help="Username for access to development builds on Artifactory")
devArgGroup.add_argument("--artifactory-token", required=False, help="API Token for access to development builds on Artifactory")

# More Options
# -----------------------------------------------------------------------------
otherArgGroup = mcpiInstallArgParser.add_argument_group("More")
otherArgGroup.add_argument("--advanced", action="store_true", default=False, help="Show advanced install options (in interactive mode)")
otherArgGroup.add_argument("--simplified", action="store_true", default=False, help="Don't show advanced install options (in interactive mode)")
otherArgGroup.add_argument("--accept-license", action="store_true", default=False, help="Accept all license terms without prompting")
otherArgGroup.add_argument("--dev-mode", required=False, action="store_true", default=False, help="Configure installation for development mode")
otherArgGroup.add_argument("--skip-pre-check", required=False, action="store_true", help="Disable the 'pre-install-check' at the start of the install pipeline")
otherArgGroup.add_argument("--no-confirm", required=False, action="store_true", default=False, help="Launch the install without prompting for confirmation")
otherArgGroup.add_argument(
    "--image-pull-policy", dest="image_pull_policy", required=False, help="Manually set the image pull policy used in the Tekton Pipeline"
)
otherArgGroup.add_argument(
    "--service-account",
    dest="service_account_name",
    required=False,
    help="Run the install pipeline under a custom service account",
)
otherArgGroup.add_argument("--slack-token", dest="slack_token", required=False, help="Slack bot token for sending pipeline notifications")
otherArgGroup.add_argument(
    "--slack-channel", dest="slack_channel", required=False, help="Slack channel(s) for notifications (comma-separated for multiple channels)"
)
otherArgGroup.add_argument("-h", "--help", action="help", default=False, help="Show this help message and exit")
