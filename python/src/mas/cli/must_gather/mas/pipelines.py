# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
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

from mas.cli.must_gather.common.task_generation import generateNamespaceCollectionTasks

logger = logging.getLogger(__name__)


# Tekton resources to collect (both v1 and v1beta1 for compatibility)
TEKTON_RESOURCES = [
    ("tekton.dev/v1", "Pipeline"),
    ("tekton.dev/v1", "PipelineRun"),
    ("tekton.dev/v1", "Task"),
    ("tekton.dev/v1", "TaskRun"),
    ("tekton.dev/v1beta1", "Pipeline"),
    ("tekton.dev/v1beta1", "PipelineRun"),
    ("tekton.dev/v1beta1", "Task"),
    ("tekton.dev/v1beta1", "TaskRun"),
]


def _discoverMASPipelineNamespaces(dynClient: DynamicClient, masInstanceIds: Optional[List[str]] = None) -> Set[str]:
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
            if nsName == "mas-pipelines":
                namespaces.add(nsName)

            # Check if namespace matches mas-{instance}-pipelines pattern
            elif nsName.startswith("mas-") and nsName.endswith("-pipelines"):
                # Extract instance ID from namespace name (mas-{instance}-pipelines)
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


def addMASPipelinesToCollectionPlan(plan, dynClient: DynamicClient, outputDir: str, noLogs: bool, masInstanceIds: Optional[List[str]] = None):
    """Add MAS Pipelines collection tasks to the collection plan.

    Discovers MAS pipelines namespace and adds collection group
    to the provided collection plan.

    Args:
        plan (CollectionPlan): Collection plan to add tasks to
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noLogs (bool): If True, skip pod log collection
    """
    logger.debug("Discovering MAS pipelines namespaces")
    try:
        masPipelineNamespaces = _discoverMASPipelineNamespaces(dynClient, masInstanceIds)
        for pipelinesNamespace in masPipelineNamespaces:
            tasks = generateNamespaceCollectionTasks(
                dynClient=dynClient, namespace=pipelinesNamespace, outputDir=outputDir, noLogs=noLogs, customResources=TEKTON_RESOURCES
            )
            plan.addGroup(f"MAS Pipelines ({pipelinesNamespace})", tasks)
            logger.debug(f"Added {len(tasks)} MAS Pipelines collection tasks for {pipelinesNamespace}")
    except Exception as e:
        logger.warning(f"MAS Pipelines discovery failed: {e}")
