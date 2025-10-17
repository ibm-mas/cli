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

from ... import __version__ as packageVersion
from ...cli import getHelpFormatter

upgradeArgParser = argparse.ArgumentParser(
    prog='mas aiservice-upgrade',
    description="\n".join([
        f"IBM Maximo Application Suite Admin CLI v{packageVersion}",
        "Upgrade AI Service by configuring and launching the AI Service Upgrade Tekton Pipeline.\n",
        "Interactive Mode:",
        "Omitting the --aiservice-instance-id option will trigger an interactive prompt"
    ]),
    epilog="Refer to the online documentation for more information: https://ibm-mas.github.io/cli/",
    formatter_class=getHelpFormatter(),
    add_help=False
)

masArgGroup = upgradeArgParser.add_argument_group('MAS Instance Selection')
masArgGroup.add_argument(
    '--aiservice-instance-id',
    required=False,
    help="The AI Service Instance ID to be upgraded"
)

otherArgGroup = upgradeArgParser.add_argument_group('More')
otherArgGroup.add_argument(
    '--skip-pre-check',
    required=False,
    action='store_true',
    default=False,
    help="Disable the 'pre-upgrade-check' and 'post-upgrade-verify' tasks in the upgrade pipeline"
)
otherArgGroup.add_argument(
    '--no-confirm',
    required=False,
    action='store_true',
    default=False,
    help="Launch the upgrade without prompting for confirmation",
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
    help="Configure upgrade for development mode",
)
otherArgGroup.add_argument(
    '-h', "--help",
    action='help',
    default=False,
    help="Show this help message and exit",
)
