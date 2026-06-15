# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Argument parser for must-gather command."""

import argparse
import os


class EnvDefault(argparse.Action):
    """Custom action to use environment variable as default if argument not provided."""

    def __init__(self, envvar, required=False, default=None, **kwargs):
        """Initialize action with environment variable name.
        
        Args:
            envvar (str): Name of environment variable to use as default
            required (bool, optional): Whether argument is required. Defaults to False.
            default: Default value if env var not set. Defaults to None.
            **kwargs: Additional arguments passed to Action
        """
        if envvar:
            if envvar in os.environ:
                default = os.environ[envvar]
        if required and default:
            required = False
        super(EnvDefault, self).__init__(default=default, required=required, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        """Set the attribute value.
        
        Args:
            parser: ArgumentParser instance
            namespace: Namespace object to populate
            values: Parsed values
            option_string: Option string used
        """
        setattr(namespace, self.dest, values)


# Define all available collectors
ALL_COLLECTORS = ["ocp", "db2", "kafka", "mongodb", "cp4d", "cert-manager", "grafana", "sls", "mas", "aiservice"]


def validateCollectors(collectorsStr: str) -> str:
    """Validate and parse collector names from comma-separated string.

    Args:
        collectorsStr (str): Comma-separated list of collector names (case-insensitive)

    Returns:
        str: Comma-separated string of validated collector names in lowercase, preserving original spacing

    Raises:
        argparse.ArgumentTypeError: If any collector name is invalid or empty
    """
    # Check for empty string
    if not collectorsStr or not collectorsStr.strip():
        raise argparse.ArgumentTypeError("Collectors list cannot be empty")

    # Parse comma-separated values, strip whitespace from each collector name
    collectorParts = collectorsStr.split(",")
    collectors = []
    for part in collectorParts:
        stripped = part.strip()
        if stripped:
            collectors.append(stripped.lower())

    # Validate each collector name
    invalidCollectors = [c for c in collectors if c not in ALL_COLLECTORS]
    if invalidCollectors:
        raise argparse.ArgumentTypeError(f"Invalid collector(s): {', '.join(invalidCollectors)}. Valid collectors: {', '.join(ALL_COLLECTORS)}")

    # Return preserving original spacing pattern (detect if spaces were used)
    if ", " in collectorsStr:
        return ", ".join(collectors)
    else:
        return ",".join(collectors)


# Module-level argument parser
mustGatherArgParser = argparse.ArgumentParser(
    prog="mas must-gather",
    description="Collect diagnostic information from MAS clusters or serve web viewer",
    formatter_class=argparse.RawTextHelpFormatter,
)

# Destination group
destGroup = mustGatherArgParser.add_argument_group("Destination")
destGroup.add_argument(
    "-d", "--directory", type=str, default="/tmp/must-gather", help="Directory where the must-gather will be saved (default: /tmp/must-gather)"
)
destGroup.add_argument(
    "-k", "--keep-files", action="store_true", default=False, help="Do not delete individual files after creating the must-gather compressed tar archive"
)

# General Controls group
controlsGroup = mustGatherArgParser.add_argument_group("General Controls")
controlsGroup.add_argument(
    "--collectors",
    type=validateCollectors,
    default=",".join(ALL_COLLECTORS),
    help=f"Comma-separated list of collectors to run (default: all)\nAvailable collectors: {', '.join(ALL_COLLECTORS)}",
)
controlsGroup.add_argument("--no-logs", action="store_true", default=False, help="Skip collection of pod logs, greatly speeds up must-gather collection time")
controlsGroup.add_argument("--secret-data", action="store_true", default=False, help="Include secrets content in the must-gather")

# MAS Content Controls group
masGroup = mustGatherArgParser.add_argument_group("MAS Content Controls")
masGroup.add_argument("--mas-instance-ids", type=str, default=None, help="Limit must-gather to a list of MAS instance IDs (comma-separated list)")
masGroup.add_argument(
    "--mas-app-ids",
    type=str,
    default="core,add,assist,iot,monitor,manage,optimizer,predict,visualinspection,pipelines,facilities",
    help="Limit must-gather to a subset of MAS namespaces (comma-separated list)",
)

# AI Service Content Controls group
aiserviceGroup = mustGatherArgParser.add_argument_group("AI Service Content Controls")
aiserviceGroup.add_argument(
    "--aiservice-instance-ids", type=str, default=None, help="Limit must-gather to a list of AI Service instance IDs (comma-separated list)"
)
aiserviceGroup.add_argument(
    "--aiservice-tenant-ids", type=str, default=None, help="Limit must-gather to a list of AI Service tenant IDs (comma-separated list)"
)

# Additional Collectors group
additionalGroup = mustGatherArgParser.add_argument_group("Additional Collectors")
additionalGroup.add_argument("--extra-namespaces", type=str, default=None, help="Enable must-gather in custom namespaces (comma-separated list)")

# Artifactory Upload group
artifactoryGroup = mustGatherArgParser.add_argument_group("Artifactory Upload")
artifactoryGroup.add_argument(
    "--artifactory-token",
    action=EnvDefault,
    envvar="ARTIFACTORY_TOKEN",
    type=str,
    help="Provide a token for Artifactory to automatically upload the file (can also be set via ARTIFACTORY_TOKEN environment variable)",
)
artifactoryGroup.add_argument(
    "--artifactory-upload-dir",
    action=EnvDefault,
    envvar="ARTIFACTORY_UPLOAD_DIR",
    type=str,
    help="Working URL to the root directory in Artifactory where the must-gather file should be uploaded (can also be set via ARTIFACTORY_UPLOAD_DIR environment variable)",
)

# Add serve subcommand
subparsers = mustGatherArgParser.add_subparsers(dest="command", help="Available commands")
serveParser = subparsers.add_parser("serve", help="Serve web viewer for existing must-gather output", formatter_class=argparse.RawTextHelpFormatter)
serveParser.add_argument("-d", "--dir", type=str, required=True, help="Path to must-gather output directory")
serveParser.add_argument("--port", type=int, default=8000, help="Port for HTTP server (default: 8000)")
