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

rollbackArgParser = argparse.ArgumentParser(
    prog='mas rollback',
    description="\n".join([
        f"IBM Maximo Application Suite Admin CLI v{packageVersion}",
        "Rollback the IBM Maximo Operator Catalog, and related MAS dependencies by configuring and launching the MAS Rollback Tekton Pipeline.\n",
        "Interactive Mode:",
        "Omitting the --catalog option will trigger an interactive prompt"
    ]),
    epilog="Refer to the online documentation for more information: https://ibm-mas.github.io/cli/",
    formatter_class=getHelpFormatter(),
    add_help=False
)

masArgGroup = rollbackArgParser.add_argument_group('MAS Basic Configuration')
masArgGroup.add_argument(
    "-i", "--mas-instance-id",
    dest='mas_instance_id',
    required=False,
    help="MAS Instance ID"
)

masArgGroup = rollbackArgParser.add_argument_group('Catalog Selection')
masArgGroup.add_argument(
    '-c', '--catalog',
    dest='mas_catalog_version',
    required=False,
    help="Maximo Operator Catalog Version (e.g. v9-240625-amd64)"
)

masArgGroup.add_argument(
    "--mas-channel",
    dest='mas_channel',
    required=False,
    help="Subscription channel for the Core Platform"
)


masArgGroup.add_argument(
    "--manage-channel",
    dest='mas_app_channel_manage',
    required=False,
    help="Subscription channel for Maximo Manage"
)

masArgGroup.add_argument(
    "--iot-channel",
    required=False,
    dest='mas_app_channel_iot',
    help="Subscription channel for Maximo IoT"
)


# Development Mode
# -----------------------------------------------------------------------------
devArgGroup = rollbackArgParser.add_argument_group("Development Mode")
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

# More Options
# -----------------------------------------------------------------------------
otherArgGroup = rollbackArgParser.add_argument_group('More')
otherArgGroup.add_argument(
    "--dev-mode",
    required=False,
    action="store_true",
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
    '--skip-pre-check',
    required=False,
    action='skip_pre_check',
    default=False,
    help="Skips the 'pre-update-check' and 'post-update-verify' tasks in the update pipeline",
)
otherArgGroup.add_argument(
    '-h', "--help",
    action='help',
    default=False,
    help="Show this help message and exit",
)
