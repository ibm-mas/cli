# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Argument parser for must-gather command."""

import argparse


def createArgumentParser() -> argparse.ArgumentParser:
    """Create argument parser for must-gather command.

    Returns:
        argparse.ArgumentParser: Configured argument parser with all must-gather options
    """
    parser = argparse.ArgumentParser(
        description="Collect diagnostic information from MAS clusters or serve web viewer", formatter_class=argparse.RawTextHelpFormatter
    )

    # Add collect arguments directly to main parser for backward compatibility
    _addCollectArguments(parser)

    # Add serve subcommand
    _addServeSubparser(parser)

    return parser


def _addServeSubparser(parser: argparse.ArgumentParser) -> None:
    """Add serve subcommand to the parser.

    Args:
        parser (argparse.ArgumentParser): Main parser to add subcommand to
    """
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    serveParser = subparsers.add_parser("serve", help="Serve web viewer for existing must-gather output", formatter_class=argparse.RawTextHelpFormatter)
    serveParser.add_argument("-d", "--dir", type=str, required=True, help="Path to must-gather output directory")
    serveParser.add_argument("--port", type=int, default=8000, help="Port for HTTP server (default: 8000)")


def _addCollectArguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for the collect command.

    Args:
        parser (argparse.ArgumentParser): Parser to add arguments to
    """

    # Destination group
    destGroup = parser.add_argument_group("Destination")
    destGroup.add_argument(
        "-d", "--directory", type=str, default="/tmp/must-gather", help="Directory where the must-gather will be saved (default: /tmp/must-gather)"
    )
    destGroup.add_argument(
        "-k", "--keep-files", action="store_true", default=False, help="Do not delete individual files after creating the must-gather compressed tar archive"
    )

    # General Controls group
    controlsGroup = parser.add_argument_group("General Controls")
    controlsGroup.add_argument(
        "--summary-only", action="store_true", default=False, help="Perform a much faster must-gather that only gathers high level summary information"
    )
    controlsGroup.add_argument(
        "--no-logs", action="store_true", default=False, help="Skip collection of pod logs, greatly speeds up must-gather collection time"
    )
    controlsGroup.add_argument("--secret-data", action="store_true", default=False, help="Include secrets content in the must-gather")
    controlsGroup.add_argument("--pods-only", action="store_true", default=False, help="Limit must-gather to collection pods data (no other K8s resources)")

    # MAS Content Controls group
    masGroup = parser.add_argument_group("MAS Content Controls")
    masGroup.add_argument("--mas-instance-ids", type=str, default=None, help="Limit must-gather to a list of MAS instance IDs (comma-separated list)")
    masGroup.add_argument(
        "--mas-app-ids",
        type=str,
        default="core,add,assist,iot,monitor,manage,optimizer,predict,visualinspection,pipelines,facilities",
        help="Limit must-gather to a subset of MAS namespaces (comma-separated list)",
    )

    # AI Service Content Controls group
    aiserviceGroup = parser.add_argument_group("AI Service Content Controls")
    aiserviceGroup.add_argument(
        "--aiservice-instance-ids", type=str, default=None, help="Limit must-gather to a list of AI Service instance IDs (comma-separated list)"
    )
    aiserviceGroup.add_argument(
        "--aiservice-tenant-ids", type=str, default=None, help="Limit must-gather to a list of AI Service tenant IDs (comma-separated list)"
    )

    # Disable Collectors group
    disableGroup = parser.add_argument_group("Disable Collectors")
    disableGroup.add_argument("--no-ocp", action="store_true", default=False, help="Disable must-gather for the OCP cluster itself")
    disableGroup.add_argument("--no-dependencies", action="store_true", default=False, help="Disable must-gather for in-cluster dependencies")
    disableGroup.add_argument("--no-sls", action="store_true", default=False, help="Disable must-gather for IBM Suite License Service")

    # Additional Collectors group
    additionalGroup = parser.add_argument_group("Additional Collectors")
    additionalGroup.add_argument("--extra-namespaces", type=str, default=None, help="Enable must-gather in custom namespaces (comma-separated list)")

    # Artifactory Upload group
    artifactoryGroup = parser.add_argument_group("Artifactory Upload")
    artifactoryGroup.add_argument("--artifactory-token", type=str, default=None, help="Provide a token for Artifactory to automatically upload the file")
    artifactoryGroup.add_argument(
        "--artifactory-upload-dir",
        type=str,
        default=None,
        help="Working URL to the root directory in Artifactory where the must-gather file should be uploaded",
    )
