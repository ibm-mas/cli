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

setupRBACArgParser = argparse.ArgumentParser(
    prog="mas setup-rbac",
    description="\n".join([
        f"IBM Maximo Application Suite Admin CLI v{packageVersion}",
        "Create the minimal install RBAC resources for MAS installation.",
    ]),
    epilog="Refer to the online documentation for more details: https://ibm-mas.github.io/cli/examples/minimal-rbac/",
    formatter_class=getHelpFormatter(),
    add_help=False
)

targetArgGroup = setupRBACArgParser.add_argument_group(
    "Target Cluster Arguments",
    "Specify the target cluster for which to set up the RBAC resources."
)

targetArgGroup.add_argument(
    "-i", "--mas-instance-id",
    dest="mas_instance_id",
    required=True,
    help="The MAS Instance ID to prepare RBAC for"
)

otherArgGroup = setupRBACArgParser.add_argument_group(
    "More"
    "Additional options for setup-rbac."
)

otherArgGroup.add_argument(
    "--no-confirm",
    required=False,
    action="store_true",
    default=False,
    help="Proceed without prompting for cluster confirmation"
)

setupRBACArgParser.add_argument(
    "-h", "--help",
    action="help",
    default=False,
    help="Show this help message and exit"
)
