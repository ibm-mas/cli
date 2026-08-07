# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""MAS version utilities for must-gather.

This module provides shared utilities for retrieving and checking MAS versions
across different collectors.
"""

import logging
from typing import Tuple
from kubernetes.dynamic import DynamicClient

logger = logging.getLogger(__name__)


def getMASVersion(dynClient: DynamicClient, namespace: str) -> str:
    """Get the reconciled MAS version from Suite CR.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client
        namespace (str): MAS Core namespace

    Returns:
        str: MAS version string (e.g., "9.1.0") or "unknown" if not found
    """
    try:
        logger.debug(f"Retrieving MAS version from Suite CR in {namespace}")
        suiteApi = dynClient.resources.get(api_version="core.mas.ibm.com/v1", kind="Suite")
        suites = suiteApi.get(namespace=namespace)

        if not suites.items:
            logger.warning(f"No Suite CR found in {namespace}")
            return "unknown"

        suite = suites.items[0]
        logger.debug(f"Found Suite CR: {suite.metadata.name}")

        versions = suite.status.get("versions", {})
        logger.debug(f"Suite status.versions: {versions}")

        reconciledVersion = versions.get("reconciled", "unknown")
        logger.info(f"MAS version in {namespace}: {reconciledVersion}")
        return reconciledVersion
    except Exception as e:
        logger.error(f"Failed to get MAS version from {namespace}: {e}", exc_info=True)
        return "unknown"


def parseVersion(versionString: str) -> Tuple[int, int, int]:
    """Parse a version string into major, minor, patch components.

    Handles pre-release versions (e.g., "9.2.0-pre.stable+29369") by extracting
    only the numeric version components.

    Args:
        versionString (str): Version string (e.g., "9.1.0" or "9.2.0-pre.stable+29369")

    Returns:
        tuple: (major, minor, patch) as integers, or (0, 0, 0) if parsing fails
    """
    if versionString == "unknown":
        return (0, 0, 0)

    try:
        # Strip pre-release suffix (everything after first '-' or '+')
        baseVersion = versionString.split("-")[0].split("+")[0]
        parts = baseVersion.split(".")
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        return (major, minor, patch)
    except (ValueError, IndexError):
        logger.warning(f"Failed to parse version string: {versionString}")
        return (0, 0, 0)


def isMAS91OrLater(dynClient: DynamicClient, namespace: str) -> Tuple[bool, str]:
    """Check if MAS version is 9.1 or later.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client
        namespace (str): MAS Core namespace

    Returns:
        tuple: (is_91_or_later, version_string)
            - is_91_or_later (bool): True if MAS >= 9.1, False otherwise
            - version_string (str): The MAS version string
    """
    versionString = getMASVersion(dynClient, namespace)
    logger.debug(f"Retrieved version string: {versionString}")

    major, minor, _ = parseVersion(versionString)
    logger.debug(f"Parsed version: major={major}, minor={minor}")

    is91OrLater = major > 9 or (major == 9 and minor >= 1)
    logger.info(f"Version check for {namespace}: {versionString} is {'>=9.1' if is91OrLater else '<9.1'}")
    return (is91OrLater, versionString)
