# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""MAS Pipelines collector for must-gather.

This module provides functionality to discover and collect MAS pipeline resources from
Kubernetes clusters. It discovers MAS pipeline namespaces (mas-{instance}-pipelines and
mas-pipelines), and collects pipeline resources including PipelineRuns with logs.
"""

import logging
from typing import Set, Optional, List
from kubernetes.dynamic import DynamicClient

logger = logging.getLogger(__name__)


def discoverMASPipelineNamespaces(dynClient: DynamicClient, masInstanceIds: Optional[List[str]] = None, includeClusterLevel: bool = False) -> Set[str]:
    """Discover MAS pipeline namespaces.

    Discovers namespaces matching the pattern mas-{instance}-pipelines for instance-specific
    pipelines, and optionally includes the cluster-level mas-pipelines namespace.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        masInstanceIds (list, optional): List of MAS instance IDs to filter. If None, discovers all instances. Defaults to None.
        includeClusterLevel (bool, optional): If True, include cluster-level mas-pipelines namespace. Defaults to False.

    Returns:
        set: Set of MAS pipeline namespace names
    """
    namespaces = set()

    try:
        # Get namespace API
        namespaceApi = dynClient.resources.get(api_version="v1", kind="Namespace")

        # Get all namespaces
        allNamespaces = namespaceApi.get()

        # Filter for MAS pipeline namespaces
        for ns in allNamespaces.items:
            nsName = ns.metadata.name

            # Check for cluster-level mas-pipelines namespace
            if includeClusterLevel and nsName == "mas-pipelines":
                namespaces.add(nsName)
                continue

            # Check if namespace matches mas-{instance}-pipelines pattern
            if nsName.startswith("mas-") and nsName.endswith("-pipelines"):
                # Extract instance ID from namespace name (mas-{instance}-pipelines)
                # Skip if it's the cluster-level namespace
                if nsName == "mas-pipelines":
                    continue

                instanceId = nsName[4:-10]  # Remove "mas-" prefix and "-pipelines" suffix

                # If specific instance IDs provided, filter by them
                if masInstanceIds:
                    if instanceId in masInstanceIds:
                        namespaces.add(nsName)
                else:
                    # No filter, add all instance pipeline namespaces
                    namespaces.add(nsName)

    except Exception as e:
        logger.warning(f"Failed to discover MAS pipeline namespaces: {e}")

    return namespaces


def collectMASPipelines(dynClient: DynamicClient, namespace: str, outputDir: str, noDetail: bool = False, noLogs: bool = False, genericMustGather=None) -> bool:
    """Collect MAS pipeline resources from a namespace.

    Collects pipeline resources including PipelineRuns with logs using the generic
    must-gather collection function.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        namespace (str): MAS pipeline namespace to collect from
        outputDir (str): Base output directory
        noDetail (bool, optional): If True, skip detailed YAML collection. Defaults to False.
        noLogs (bool, optional): If True, skip pod log collection. Defaults to False.
        genericMustGather (callable, optional): Function to perform generic must-gather collection. Defaults to None.

    Returns:
        bool: True if collection succeeded, False if errors occurred
    """
    try:
        # Perform generic resource collection using common utilities
        # Note: genericMustGather will create the proper directory structure under outputDir/resources/{namespace}
        if genericMustGather:
            success = genericMustGather(namespace=namespace, outputDir=outputDir, noDetail=noDetail, podsOnly=False, noLogs=noLogs, additionalResources=[])
            return success
        else:
            logger.warning(f"No genericMustGather function provided for {namespace}, skipping generic collection")
            return True

    except Exception as e:
        logger.error(f"Failed to collect MAS pipelines from namespace {namespace}: {e}")
        return False
