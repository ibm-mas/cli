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
from itertools import groupby

from .config import PACKAGE_CONFIGS
from .. import __version__ as packageVersion
from ..cli import getHelpFormatter


mirrorArgParser = argparse.ArgumentParser(
    prog="mas mirror",
    description="\n".join([
        f"IBM Maximo Application Suite Admin CLI v{packageVersion}",
        "Mirror IBM Maximo content to a private container registry.",
    ]),
    epilog="Refer to the online documentation for more information: https://ibm-mas.github.io/cli/",
    formatter_class=getHelpFormatter(),
    add_help=False
)

mainGroup = mirrorArgParser.add_argument_group("Primary Configuration")
mainGroup.add_argument(
    "--catalog",
    required=True,
    help="Catalog version (e.g., v9-240625-amd64, v9-260129-amd64)"
)
mainGroup.add_argument(
    "--release",
    required=True,
    help="MAS release version",
    choices=["8.10.x", "8.11.x", "9.0.x", "9.1.x"]
)
mainGroup.add_argument(
    "--mode",
    required=True,
    help="Mirror mode",
    choices=["m2m", "m2d", "d2m"]
)
mainGroup.add_argument(
    "--target-registry",
    required=False,
    type=str,
    help="Target registry for m2m and d2m modes (e.g., registry.example.com/namespace)"
)

# Add package-specific arguments dynamically, organized by group
for groupName, groupItems in groupby(PACKAGE_CONFIGS, key=lambda x: x[0]):
    argGroup = mirrorArgParser.add_argument_group(groupName)
    for group, argName, packageName, _, description in groupItems:
        argGroup.add_argument(
            f"--{argName}",
            required=False,
            help=f"Mirror images for the {packageName} package",
            action="store_true"
        )

otherArgGroup = mirrorArgParser.add_argument_group(
    "More"
)
otherArgGroup.add_argument(
    "-h", "--help",
    action="help",
    default=False,
    help="Show this help message and exit"
)
