# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
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

from mas.cli.must_gather.common.reconcile_logs import collectReconcileLogs

logger = logging.getLogger(__name__)


def discoverMASCoreNamespaces(dynClient: DynamicClient, masInstanceIds: Optional[List[str]] = None) -> Set[str]:
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


def generateMASCoreCollectionTasks(
    dynClient: DynamicClient,
    namespace: str,
    outputDir: str,
    noDetail: bool = False,
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
        noDetail (bool, optional): If True, skip detailed YAML collection. Defaults to False.
        noLogs (bool, optional): If True, skip pod log collection. Defaults to False.
        ibmCRDs (list, optional): List of IBM CRD tuples (api_version, kind). Defaults to None.

    Returns:
        list: List of task tuples (task_name, function, *args)
    """
    from mas.cli.must_gather.common.task_generation import generateNamespaceCollectionTasks

    # Use the standard namespace collection tasks (IBM resources, standard resources, secrets, pods)
    tasks = generateNamespaceCollectionTasks(
        dynClient=dynClient,
        namespace=namespace,
        outputDir=outputDir,
        noDetail=noDetail,
        noLogs=noLogs,
        includeSecrets=True,  # MAS Core includes secrets
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


def addMASCoreToCollectionPlan(
    plan, dynClient: DynamicClient, outputDir: str, noDetail: bool, noLogs: bool, ibmCRDs: list, masInstanceIds: Optional[List[str]] = None
):
    """Add MAS Core collection tasks to the collection plan.

    Discovers MAS Core namespaces and adds collection groups for each instance
    to the provided collection plan. Returns the list of discovered core namespaces
    for use by MAS Apps discovery.

    Args:
        plan (CollectionPlan): Collection plan to add tasks to
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noDetail (bool): If True, skip detailed resource collection
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

        coreNamespaces = discoverMASCoreNamespaces(dynClient, masInstanceIds=masInstanceIds)
        if coreNamespaces:
            logger.info(f"Discovered {len(coreNamespaces)} MAS instance(s): {', '.join([ns[4:-5] for ns in sorted(coreNamespaces)])}")
            for coreNamespace in sorted(coreNamespaces):
                instanceId = coreNamespace[4:-5]  # Remove "mas-" prefix and "-core" suffix
                tasks = generateMASCoreCollectionTasks(
                    dynClient=dynClient,
                    namespace=coreNamespace,
                    outputDir=outputDir,
                    noDetail=noDetail,
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


def generateMASCoreSummary(dynClient: DynamicClient, namespaces: Set[str], outputFile: str) -> None:
    """Generate MAS Core summary report.

    Creates a summary report showing all Suite instances found with their
    status, version, and other key information.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        namespaces (set): Set of MAS Core namespaces
        outputFile (str): Path to output summary file
    """
    try:
        # Get Suite API
        suiteApi = dynClient.resources.get(api_version="core.mas.ibm.com/v1", kind="Suite")

        # Collect all Suite CRs from the namespaces
        suites = []
        for namespace in namespaces:
            try:
                suiteList = suiteApi.get(namespace=namespace)
                suites.extend(suiteList.items)
            except Exception as e:
                logger.debug(f"Could not get Suite CRs from {namespace}: {e}")

        # Write summary file
        with open(outputFile, "w") as f:
            f.write("MAS Core Summary\n")
            f.write("=" * 80 + "\n\n")

            if not suites:
                f.write("No MAS instances found\n")
            else:
                f.write(f"Found {len(suites)} MAS instance(s)\n\n")

                for suite in suites:
                    instanceId = suite.metadata.name
                    namespace = suite.metadata.namespace

                    # Get version from spec
                    version = "Unknown"
                    if hasattr(suite, "spec") and hasattr(suite.spec, "version"):
                        version = suite.spec.version

                    # Extract status
                    status = "Unknown"
                    if hasattr(suite, "status") and hasattr(suite.status, "conditions"):
                        conditions = suite.status.conditions
                    if conditions:
                        # Get the Ready condition
                        for condition in conditions:
                            if condition.get("type") == "Ready":
                                status = condition.get("status", "Unknown")
                                break

                    f.write(f"Instance: {instanceId}\n")
                    f.write(f"  Namespace: {namespace}\n")
                    f.write(f"  Version:   {version}\n")
                    f.write(f"  Status:    {status}\n")
                    f.write("\n")

        logger.info(f"MAS Core summary written to {outputFile}")

    except Exception as e:
        logger.error(f"Failed to generate MAS Core summary: {e}")
        # Create empty file to indicate attempt was made
        with open(outputFile, "w") as f:
            f.write(f"Error generating summary: {e}\n")
