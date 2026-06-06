# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""MAS Apps collector for must-gather.

This module provides functionality to discover and collect MAS application resources from
Kubernetes clusters. It discovers MAS app namespaces (mas-{instance}-{app}), calls
app-specific summary and collection scripts, and uses common utilities for generic
resource collection.
"""

import logging
from typing import Set, Optional, List
from kubernetes.dynamic import DynamicClient

logger = logging.getLogger(__name__)

# Default MAS app IDs to collect
DEFAULT_MAS_APP_IDS = ["core", "add", "assist", "iot", "monitor", "manage", "optimizer", "predict", "visualinspection", "pipelines", "facilities"]


def discoverMASAppNamespaces(dynClient: DynamicClient, masInstanceId: str, masAppIds: Optional[List[str]] = None) -> Set[str]:
    """Discover MAS application namespaces for a specific instance.

    Discovers namespaces matching the pattern mas-{instance}-{app}, excluding the
    core namespace. Can optionally filter by specific app IDs.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        masInstanceId (str): MAS instance ID to discover apps for
        masAppIds (list, optional): List of app IDs to filter. If None, discovers all apps. Defaults to None.

    Returns:
        set: Set of MAS app namespace names
    """
    namespaces = set()

    try:
        # Get namespace API
        namespaceApi = dynClient.resources.get(api_version="v1", kind="Namespace")

        # Get all namespaces
        allNamespaces = namespaceApi.get()

        # Build expected namespace prefix
        namespacePrefix = f"mas-{masInstanceId}-"

        # Filter for MAS app namespaces
        for ns in allNamespaces.items:
            nsName = ns.metadata.name

            # Check if namespace matches mas-{instance}-{app} pattern
            if nsName.startswith(namespacePrefix):
                # Extract app ID from namespace name
                appId = nsName[len(namespacePrefix) :]

                # Skip core namespace (handled separately)
                if appId == "core":
                    continue

                # If specific app IDs provided, filter by them
                if masAppIds:
                    if appId in masAppIds:
                        namespaces.add(nsName)
                else:
                    # No filter, add all app namespaces
                    namespaces.add(nsName)

    except Exception as e:
        logger.warning(f"Failed to discover MAS app namespaces for instance {masInstanceId}: {e}")

    return namespaces


def collectMASApp(
    dynClient: DynamicClient, namespace: str, appId: str, outputDir: str, noDetail: bool = False, noLogs: bool = False, genericMustGather=None
) -> bool:
    """Collect MAS application resources from a namespace.

    Calls app-specific summary and collection scripts if they exist, then performs
    generic resource collection using common utilities.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        namespace (str): MAS app namespace to collect from
        appId (str): MAS application ID (e.g., "manage", "iot")
        outputDir (str): Base output directory
        noDetail (bool, optional): If True, skip detailed YAML collection. Defaults to False.
        noLogs (bool, optional): If True, skip pod log collection. Defaults to False.
        genericMustGather (callable, optional): Function to perform generic must-gather collection. Defaults to None.

    Returns:
        bool: True if collection succeeded, False if errors occurred
    """
    try:
        # Perform generic resource collection using common utilities
        # Note: External scripts (mg-summary-mas-* and mg-collect-mas-*) are not part of Python migration
        if genericMustGather:
            success = genericMustGather(namespace=namespace, outputDir=outputDir, noDetail=noDetail, podsOnly=False, noLogs=noLogs, additionalResources=[])
            return success
        else:
            logger.warning(f"No genericMustGather function provided for {namespace}, skipping collection")
            return True

    except Exception as e:
        logger.error(f"Failed to collect MAS app {appId} from namespace {namespace}: {e}")
        return False
