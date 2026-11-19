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

configureMcpiArgParser = argparse.ArgumentParser(
    prog="mas configure-mcpi",
    description="\n".join(
        [
            f"IBM Maximo Application Suite Admin CLI v{packageVersion}",
            "Configure Maximo Cluster Performance Insights (MCPI) on an existing MAS instance.",
        ]
    ),
    formatter_class=getHelpFormatter(),
    add_help=False,
)

targetArgGroup = configureMcpiArgParser.add_argument_group(
    "Target MAS Instance Arguments",
    "Specify the target MAS instance for which to configure MCPI.",
)

targetArgGroup.add_argument(
    "-i",
    "--mas-instance-id",
    dest="mas_instance_id",
    required=False,
    help="The MAS Instance ID to configure MCPI for (prompted if omitted)",
)

otherArgGroup = configureMcpiArgParser.add_argument_group(
    "More",
    "Additional options for configure-mcpi.",
)

otherArgGroup.add_argument(
    "--no-confirm",
    required=False,
    action="store_true",
    default=False,
    help="Proceed without prompting for confirmation",
)

configureMcpiArgParser.add_argument(
    "-h",
    "--help",
    action="help",
    default=False,
    help="Show this help message and exit",
)
