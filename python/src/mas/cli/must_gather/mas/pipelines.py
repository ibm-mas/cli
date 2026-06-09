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
from typing import Set, Optional, List, Tuple
from kubernetes.dynamic import DynamicClient

from mas.cli.must_gather.common.task_generation import generateNamespaceCollectionTasks

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


def generateMASPipelinesCollectionTasks(
    dynClient: DynamicClient,
    namespace: str,
    outputDir: str,
    noDetail: bool = False,
    noLogs: bool = False,
    ibmCRDs: Optional[List[Tuple[str, str]]] = None,
) -> List[Tuple]:
    """Generate collection tasks for a MAS pipelines namespace.

    Creates a list of collection tasks that can be executed in parallel
    for collecting MAS pipeline resources from a specific namespace.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        namespace (str): MAS pipeline namespace to collect from
        outputDir (str): Base output directory
        noDetail (bool, optional): If True, skip detailed YAML collection. Defaults to False.
        noLogs (bool, optional): If True, skip pod log collection. Defaults to False.
        ibmCRDs (list, optional): List of IBM CRD tuples (apiVersion, kind) to collect. Defaults to None.

    Returns:
        list: List of task tuples in format (task_name, func, *args)
    """
    # Use common namespace collection task generation
    # Pipelines collect standard resources and pods
    tasks = generateNamespaceCollectionTasks(
        dynClient=dynClient,
        namespace=namespace,
        outputDir=outputDir,
        noDetail=noDetail,
        noLogs=noLogs,
        includeSecrets=True,
        secretData=False,
        customResources=None,
        ibmCRDs=ibmCRDs,
    )

    return tasks


def addMASPipelinesToCollectionPlan(plan, dynClient: DynamicClient, outputDir: str, noDetail: bool, noLogs: bool, ibmCRDs: list):
    """Add MAS Pipelines collection tasks to the collection plan.

    Discovers cluster-level MAS pipelines namespace and adds collection group
    to the provided collection plan.

    Args:
        plan (CollectionPlan): Collection plan to add tasks to
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noDetail (bool): If True, skip detailed resource collection
        noLogs (bool): If True, skip pod log collection
        ibmCRDs (list): List of IBM CRD information for collection
    """
    logger.debug("Discovering cluster-level MAS pipelines")
    try:
        clusterPipelineNamespaces = discoverMASPipelineNamespaces(dynClient, masInstanceIds=[], includeClusterLevel=True)
        if "mas-pipelines" in clusterPipelineNamespaces:
            logger.info("Discovered cluster-level MAS pipelines namespace")
            tasks = generateMASPipelinesCollectionTasks(
                dynClient=dynClient,
                namespace="mas-pipelines",
                outputDir=outputDir,
                noDetail=noDetail,
                noLogs=noLogs,
                ibmCRDs=ibmCRDs,
            )
            plan.addGroup("MAS Pipelines (cluster)", tasks)
            logger.debug(f"Added {len(tasks)} MAS Pipelines collection tasks for cluster-level pipelines")
        else:
            logger.info("No cluster-level MAS pipelines namespace found")
    except Exception as e:
        logger.warning(f"MAS Pipelines discovery failed: {e}")
