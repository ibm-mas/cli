# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""MAS Core collector for must-gather.

This module provides functionality to discover and collect MAS Core resources from
Kubernetes clusters. It discovers MAS Core namespaces (mas-{instance}-core), collects
Suite CRs and related resources, and generates summary reports.
"""

import logging
from typing import Set, Optional, List
from kubernetes.dynamic import DynamicClient

from mas.cli.must_gather.common.task_generation import generateNamespaceCollectionTasks
from mas.cli.must_gather.common.reconcile_logs import collectReconcileLogs

logger = logging.getLogger(__name__)


def _discoverMASCoreNamespaces(dynClient: DynamicClient, masInstanceIds: Optional[List[str]] = None) -> Set[str]:
    """Discover MAS Core namespaces.

    When MAS instance IDs are provided, returns namespaces for those specific instances.
    When no instance IDs are provided, discovers all MAS Core namespaces by finding
    namespaces matching the pattern mas-*-core.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        masInstanceIds (list, optional): List of MAS instance IDs to filter. Defaults to None.

    Returns:
        set: Set of MAS Core namespace names
    """
    namespaces = set()

    try:
        # Get namespace API
        namespaceApi = dynClient.resources.get(api_version="v1", kind="Namespace")

        # Get all namespaces
        allNamespaces = namespaceApi.get()

        # Filter for MAS Core namespaces
        for ns in allNamespaces.items:
            nsName = ns.metadata.name

            # Check if namespace matches mas-*-core pattern
            if nsName.startswith("mas-") and nsName.endswith("-core"):
                # If specific instance IDs provided, filter by them
                if masInstanceIds:
                    # Extract instance ID from namespace name (mas-{instance}-core)
                    instanceId = nsName[4:-5]  # Remove "mas-" prefix and "-core" suffix
                    if instanceId in masInstanceIds:
                        namespaces.add(nsName)
                else:
                    # No filter, add all MAS Core namespaces
                    namespaces.add(nsName)

    except Exception as e:
        logger.warning(f"Failed to discover MAS Core namespaces: {e}")

    return namespaces


def _generateMASCoreCollectionTasks(
    dynClient: DynamicClient,
    namespace: str,
    outputDir: str,
    noLogs: bool = False,
    ibmCRDs: Optional[List[tuple]] = None,
):
    """Generate collection tasks for MAS Core namespace.

    Creates a list of tasks for parallel execution that collect all MAS Core resources
    including IBM CRDs, standard Kubernetes resources, secrets, pods, and reconcile logs.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        namespace (str): MAS Core namespace to collect from
        outputDir (str): Base output directory
        noLogs (bool, optional): If True, skip pod log collection. Defaults to False.
        ibmCRDs (list, optional): List of IBM CRD tuples (api_version, kind). Defaults to None.

    Returns:
        list: List of task tuples (task_name, function, *args)
    """

    # Use the standard namespace collection tasks (IBM resources, standard resources, secrets, pods)
    tasks = generateNamespaceCollectionTasks(
        dynClient=dynClient,
        namespace=namespace,
        outputDir=outputDir,
        noLogs=noLogs,
        secretData=False,  # MAS Core does not include secret data
        customResources=None,  # No MAS-specific CRDs to add
        ibmCRDs=ibmCRDs,
    )

    # Add MAS Core-specific task: Collect reconcile logs from MAS operator
    def collectMASOperatorReconcileLogs():
        return collectReconcileLogs(
            namespace=namespace,
            labelSelector="app.kubernetes.io/name",
            labelValue="ibm-mas-operator",
            outputDir=outputDir,
        )

    tasks.append(("reconcile_logs", collectMASOperatorReconcileLogs))

    return tasks


def addMASCoreToCollectionPlan(plan, dynClient: DynamicClient, outputDir: str, noLogs: bool, ibmCRDs: list, masInstanceIds: Optional[List[str]] = None):
    """Add MAS Core collection tasks to the collection plan.

    Discovers MAS Core namespaces and adds collection groups for each instance
    to the provided collection plan. Returns the list of discovered core namespaces
    for use by MAS Apps discovery.

    Args:
        plan (CollectionPlan): Collection plan to add tasks to
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noLogs (bool): If True, skip pod log collection
        ibmCRDs (list): List of IBM CRD information for collection
        masInstanceIds (list, optional): List of MAS instance IDs to filter discovery. Defaults to None.

    Returns:
        set: Set of discovered MAS Core namespace names
    """
    logger.info("Discovering MAS instances")
    try:
        if masInstanceIds:
            logger.debug(f"Filtering MAS discovery by instance IDs: {', '.join(masInstanceIds)}")

        coreNamespaces = _discoverMASCoreNamespaces(dynClient, masInstanceIds=masInstanceIds)
        if coreNamespaces:
            logger.info(f"Discovered {len(coreNamespaces)} MAS instance(s): {', '.join([ns[4:-5] for ns in sorted(coreNamespaces)])}")
            for coreNamespace in sorted(coreNamespaces):
                instanceId = coreNamespace[4:-5]  # Remove "mas-" prefix and "-core" suffix
                tasks = _generateMASCoreCollectionTasks(
                    dynClient=dynClient,
                    namespace=coreNamespace,
                    outputDir=outputDir,
                    noLogs=noLogs,
                    ibmCRDs=ibmCRDs,
                )
                plan.addGroup(f"MAS Core ({instanceId})", tasks)
                logger.debug(f"Added {len(tasks)} MAS Core collection tasks for instance {instanceId}")
        else:
            logger.info("No MAS instances discovered")
        return coreNamespaces
    except Exception as e:
        logger.warning(f"MAS discovery failed: {e}")
        return set()
