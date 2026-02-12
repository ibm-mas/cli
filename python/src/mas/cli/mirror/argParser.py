# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

from collections import defaultdict
import argparse
import re
from itertools import groupby

from .config import PACKAGE_CONFIGS
from .. import __version__ as packageVersion
from ..cli import getHelpFormatter


def validate_timeout(value):
    """
    Validate that the timeout string is in a valid format.

    Valid formats: "1h20m10s", "1h", "20m", "10s", "1h20m", etc.

    Args:
        value: The timeout string to validate

    Returns:
        The validated timeout string

    Raises:
        argparse.ArgumentTypeError: If the format is invalid
    """
    # Pattern matches combinations of hours (h), minutes (m), and seconds (s)
    # Must have at least one unit and units must be in order (h, m, s)
    pattern = r'^(\d+h)?(\d+m)?(\d+s)?$'

    if not re.match(pattern, value):
        raise argparse.ArgumentTypeError(
            f"Invalid timeout format: '{value}'. "
            "Expected format: combinations of hours (h), minutes (m), and seconds (s), "
            "e.g., '1h20m10s', '1h', '20m', '10s'"
        )

    # Ensure at least one unit is present
    if not any(unit in value for unit in ['h', 'm', 's']):
        raise argparse.ArgumentTypeError(
            f"Invalid timeout format: '{value}'. "
            "Must include at least one time unit (h, m, or s)"
        )

    return value


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
mainGroup.add_argument(
    "--dir",
    required=True,
    type=str,
    help="Root directory for mirror operations (workspace for m2m, disk storage for m2d/d2m)"
)
mainGroup.add_argument(
    "--authfile",
    required=False,
    type=str,
    help="Path to authentication file (must exist). If not provided, will be generated from environment variables (REGISTRY_USERNAME, REGISTRY_PASSWORD, and IBM_ENTITLEMENT_KEY)."
)

# Add package-specific arguments dynamically, organized by group
# First, deduplicate by argName and aggregate package names

# Group configs by (groupName, argName) to deduplicate and aggregate packages
arg_map = defaultdict(list)
for group, argName, packageName, versionKey in PACKAGE_CONFIGS:
    arg_map[(group, argName)].append(packageName)

# Now create arguments with deduplicated argNames and aggregated package lists
for groupName, groupItems in groupby(PACKAGE_CONFIGS, key=lambda x: x[0]):
    argGroup = mirrorArgParser.add_argument_group(groupName)
    # Track which argNames we've already added to this group
    added_args = set()

    for group, argName, packageName, _ in groupItems:
        if argName not in added_args:
            added_args.add(argName)
            # Get all package names for this argName
            packages = arg_map[(group, argName)]

            # Create help text based on number of packages
            if len(packages) == 1:
                help_text = f"Mirror images for the {packages[0]} package"
            else:
                package_list = ", ".join(packages)
                help_text = f"Mirror images for packages: {package_list}"

            argGroup.add_argument(
                f"--{argName}",
                required=False,
                help=help_text,
                action="store_true"
            )

advancedGroup = mirrorArgParser.add_argument_group("Advanced Configuration")
advancedGroup.add_argument(
    "--dest-tls-verify",
    required=False,
    type=lambda x: x.lower() == 'true',
    default=True,
    help="Verify TLS certificates for destination registry (default: true)"
)
advancedGroup.add_argument(
    "--image-timeout",
    required=False,
    type=validate_timeout,
    default="20m",
    help="Timeout for image operations (e.g., '1h20m10s', '1h', '20m', default: '20m')"
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
