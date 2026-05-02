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

setupPreinstallRBACArgParser = argparse.ArgumentParser(
    prog="mas setup-preinstall-rbac",
    description="\n".join([
        f"IBM Maximo Application Suite Admin CLI v{packageVersion}",
        "Set up pre-install RBAC for MAS.",
    ]),
    epilog="",
    formatter_class=getHelpFormatter(),
    add_help=False
)

targetArgGroup = setupPreinstallRBACArgParser.add_argument_group(
    "Target Cluster Arguments",
    "Specify the target cluster and MAS instance for which pre-install RBAC should be set up."
)

targetArgGroup.add_argument(
    "-i", "--mas-instance-id",
    dest="mas_instance_id",
    required=False,
    help="The MAS instance ID for which pre-install RBAC will be set up"
)

targetArgGroup.add_argument(
    "--mas-version",
    dest="mas_version",
    required=False,
    help="The MAS major.minor version used to select pre-install RBAC manifests, for example 9.2"
)

targetArgGroup.add_argument(
    "--permission-mode",
    dest="permission_mode",
    required=False,
    choices=["cluster", "namespaced", "minimal"],
    help="The permission mode used to determine which pre-install RBAC manifests are set up"
)

targetArgGroup.add_argument(
    "--apps",
    dest="apps",
    required=False,
    help="Comma-separated list of apps used to filter which pre-install RBAC manifests are set up, for example core,manage,iot"
)

otherArgGroup = setupPreinstallRBACArgParser.add_argument_group(
    "More",
    "Additional options for setup-preinstall-rbac."
)

otherArgGroup.add_argument(
    "--no-confirm",
    required=False,
    action="store_true",
    default=False,
    help="Proceed without prompting for cluster confirmation"
)

setupPreinstallRBACArgParser.add_argument(
    "-h", "--help",
    action="help",
    default=False,
    help="Show this help message and exit"
)
