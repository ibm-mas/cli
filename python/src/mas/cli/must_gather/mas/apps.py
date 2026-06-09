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
from typing import Set, Optional, List, Tuple
from kubernetes.dynamic import DynamicClient

from mas.cli.must_gather.common import generateReconcileLogsCollectionTasks
from mas.cli.must_gather.common.task_generation import generateNamespaceCollectionTasks

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


def getReconcileLogsOperatorsForApp(namespace: str, appId: str) -> List[Tuple[str, str, str]]:
    """Get list of operators to collect reconcile logs from for a specific app.

    Returns a list of (namespace, labelSelector, labelValue) tuples for all operators
    that should have reconcile logs collected for the given app.

    Args:
        namespace (str): MAS app namespace
        appId (str): MAS application ID (e.g., "manage", "iot", "predict")

    Returns:
        List[Tuple[str, str, str]]: List of (namespace, labelSelector, labelValue) tuples
    """
    operators = []

    if appId == "manage":
        operators = [
            (namespace, "control-plane", "ibm-mas-manage"),
            (namespace, "mas.ibm.com/appType", "imagestitching-entitymgr-operator"),
            (namespace, "mas.ibm.com/appType", "entitymgr-ws-operator"),
            (namespace, "mas.ibm.com/appType", "healthext-entitymgr-ws-operator"),
            (namespace, "mas.ibm.com/appType", "maxinstudb"),
            (namespace, "operator", "ibm-truststore-mgr"),
            (namespace, "mas.ibm.com/appType", "serverBundle"),
        ]
    elif appId == "iot":
        operators = [
            (namespace, "control-plane", "ibm-iot-operator"),
            (namespace, "control-plane", "workspace-operator"),
            (namespace, "operator", "ibm-truststore-mgr"),
        ]
    elif appId == "optimizer":
        operators = [
            (namespace, "control-plane", "ibm-mas-optimizer"),
            (namespace, "mas.ibm.com/appType", "entitymgr-ws-operator"),
            (namespace, "mas.ibm.com/applicationId", "optimizer"),
            (namespace, "mas.ibm.com/appType", "optimizer-adminui"),
            (namespace, "mas.ibm.com/appType", "optimizer-api"),
            (namespace, "mas.ibm.com/appType", "optimizer-execution-service"),
        ]
    elif appId == "predict":
        operators = [
            (namespace, "control-plane", "ibm-mas-predict"),
            (namespace, "operator", "ibm-truststore-mgr"),
            (namespace, "app", "aiexpts-service"),
            (namespace, "io.kompose.service", "mat-service"),
            (namespace, "mas.ibm.com/appType", "predict-api"),
            (namespace, "mas.ibm.com/appType", "entitymgr-ws-operator"),
        ]
    elif appId == "visualinspection":
        operators = [
            (namespace, "control-plane", "ibm-mas-visualinspection"),
            (namespace, "app", "gpu-operator"),
            (namespace, "app", "visualinspection"),
        ]
    elif appId == "facilities":
        operators = [
            (namespace, "control-plane", "ibm-mas-facilities"),
        ]

    return operators


def generateMASAppCollectionTasks(
    dynClient: DynamicClient,
    namespace: str,
    appId: str,
    outputDir: str,
    noDetail: bool = False,
    noLogs: bool = False,
    ibmCRDs: Optional[List[Tuple[str, str]]] = None,
) -> List[Tuple]:
    """Generate collection tasks for a MAS application namespace.

    Creates a list of collection tasks that can be executed in parallel
    for collecting MAS app resources from a specific namespace.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        namespace (str): MAS app namespace to collect from
        appId (str): MAS application ID (e.g., "manage", "iot")
        outputDir (str): Base output directory
        noDetail (bool, optional): If True, skip detailed YAML collection. Defaults to False.
        noLogs (bool, optional): If True, skip pod log collection. Defaults to False.
        ibmCRDs (list, optional): List of IBM CRD tuples (apiVersion, kind) to collect. Defaults to None.

    Returns:
        list: List of task tuples in format (task_name, func, *args)
    """
    # Use common namespace collection task generation
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

    # Add app-specific reconcile logs tasks
    if not noDetail:
        operators = getReconcileLogsOperatorsForApp(namespace, appId)
        if operators:
            tasks.extend(generateReconcileLogsCollectionTasks(operators, outputDir))

    return tasks


def addMASAppsToCollectionPlan(
    plan, dynClient: DynamicClient, outputDir: str, noDetail: bool, noLogs: bool, ibmCRDs: list, coreNamespaces: Set[str], masAppIds: Optional[List[str]] = None
):
    """Add MAS Apps collection tasks to the collection plan.

    For each MAS Core namespace provided, discovers and adds MAS Apps collection groups
    to the provided collection plan.

    Args:
        plan (CollectionPlan): Collection plan to add tasks to
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noDetail (bool): If True, skip detailed resource collection
        noLogs (bool): If True, skip pod log collection
        ibmCRDs (list): List of IBM CRD information for collection
        coreNamespaces (set): Set of MAS Core namespace names to discover apps for
        masAppIds (list, optional): List of MAS app IDs to filter. Defaults to None.
    """
    if masAppIds:
        logger.debug(f"Filtering MAS app discovery by app IDs: {', '.join(masAppIds)}")

    for coreNamespace in sorted(coreNamespaces):
        instanceId = coreNamespace[4:-5]  # Remove "mas-" prefix and "-core" suffix

        # Discover MAS Apps for this instance
        logger.debug(f"Discovering MAS apps for instance {instanceId}")
        try:
            appNamespaces = discoverMASAppNamespaces(dynClient, masInstanceId=instanceId, masAppIds=masAppIds)
            if appNamespaces:
                logger.info(
                    f"Discovered {len(appNamespaces)} MAS app(s) for instance {instanceId}: {', '.join([ns.split('-')[-1] for ns in sorted(appNamespaces)])}"
                )
                for appNamespace in sorted(appNamespaces):
                    appId = appNamespace[len(f"mas-{instanceId}-") :]
                    tasks = generateMASAppCollectionTasks(
                        dynClient=dynClient,
                        namespace=appNamespace,
                        appId=appId,
                        outputDir=outputDir,
                        noDetail=noDetail,
                        noLogs=noLogs,
                        ibmCRDs=ibmCRDs,
                    )
                    plan.addGroup(f"MAS App ({instanceId}/{appId})", tasks)
                    logger.debug(f"Added {len(tasks)} MAS App collection tasks for {instanceId}/{appId}")
            else:
                logger.info(f"No MAS apps discovered for instance {instanceId}")
        except Exception as e:
            logger.warning(f"MAS Apps discovery failed for {instanceId}: {e}")
