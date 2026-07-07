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

import json
import logging
import os
from typing import Set, Optional, List
from kubernetes.dynamic import DynamicClient
from kubernetes import client

from mas.cli.must_gather.common import generateReconcileLogsCollectionTasks
from mas.cli.must_gather.common.task_generation import generateNamespaceCollectionTasks
from mas.cli.must_gather.common.pod_exec import execCurlInPod
from .network_tests import testCoreToManageConnectivity
from .version import isMAS91OrLater
from .licensing import collectLicensingInfo

logger = logging.getLogger(__name__)


def _collectSystemInfo(dynClient: DynamicClient, namespace: str, outputDir: str) -> bool:
    """Collect system information from MAS internalapi.

    Queries the MAS internalapi /v1/authservice/systeminfo endpoint to retrieve
    system information including licensing data. Only runs for MAS 9.1+.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client
        namespace (str): MAS Core namespace
        outputDir (str): Base output directory

    Returns:
        bool: True if collection succeeded, False otherwise
    """
    instanceId = namespace[4:-5]  # Remove "mas-" prefix and "-core" suffix
    logger.info(f"Starting system info collection for instance {instanceId}")

    # Check MAS version - only collect for 9.1+
    is91OrLater, versionString = isMAS91OrLater(dynClient, namespace)
    if not is91OrLater:
        logger.info(f"Skipping system info collection for {instanceId} - MAS version {versionString} is below 9.1")
        return True

    try:
        # Find internalapi pod
        logger.debug(f"Searching for internalapi pod in namespace {namespace}")
        coreV1 = client.CoreV1Api(dynClient.client)
        pods = coreV1.list_namespaced_pod(namespace=namespace, label_selector=f"app={instanceId}-internalapi")

        internalapiPod = None
        logger.debug(f"Found {len(pods.items)} internalapi pods")
        for pod in pods.items:
            podName = pod.metadata.name
            phase = pod.status.phase
            logger.debug(f"  Pod: {podName}, Phase: {phase}")

            if podName.startswith(f"{instanceId}-internalapi-") and phase == "Running":
                internalapiPod = podName
                logger.debug(f"  ✓ Selected pod: {podName}")
                break

        if not internalapiPod:
            logger.warning(f"No running internalapi pod found for instance {instanceId} - skipping licensing info collection")
            return True

        logger.info(f"Found internalapi pod: {internalapiPod}")

        # Query systeminfo endpoint using shared curl utility
        logger.debug(f"Querying systeminfo endpoint for instance {instanceId}")
        result = execCurlInPod(
            dynClient=dynClient,
            namespace=namespace,
            podName=internalapiPod,
            url=f"https://internalapi.{namespace}.svc/v1/authservice/systeminfo",
            certPath="/etc/pki/tls/certs/mascore-cert/tls.crt",
            keyPath="/etc/pki/tls/certs/mascore-cert/tls.key",
            caPath="/etc/pki/tls/certs/mascore-cert/ca.crt",
            containerName=None,
            timeout=30,
        )

        if result["success"] and result["json_data"]:
            logger.debug(f"Successfully retrieved system info with {len(result['json_data'])} top-level keys")

            # Save system info
            outputPath = os.path.join(outputDir, "system-info", f"{namespace}.json")
            logger.debug(f"Creating output directory: {os.path.dirname(outputPath)}")
            os.makedirs(os.path.dirname(outputPath), exist_ok=True)

            logger.debug(f"Writing system info to: {outputPath}")
            with open(outputPath, "w") as f:
                json.dump(result["json_data"], f, indent=2)

            logger.info(f"✅ System information saved to {outputPath}")
            return True
        else:
            logger.warning(f"Failed to retrieve system info for instance {instanceId}: {result.get('error', 'Unknown error')}")
            return True

    except Exception as e:
        logger.error(f"❌ Error collecting licensing information for {instanceId}: {e}", exc_info=True)
        return True  # Don't fail collection if licensing info can't be collected


def _runNetworkTests(dynClient: DynamicClient, namespace: str, outputDir: str) -> bool:
    """Run network connectivity tests for MAS Core.

    Tests connectivity from MAS Core pods to Manage endpoints if Manage is installed.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client
        namespace (str): MAS Core namespace
        outputDir (str): Base output directory

    Returns:
        bool: True if tests completed, False on error
    """
    # Extract instance ID from namespace
    instanceId = namespace[4:-5]  # Remove "mas-" prefix and "-core" suffix

    # Check if Manage is installed by looking for ManageWorkspace CR
    try:
        manageNamespace = f"mas-{instanceId}-manage"
        manageWorkspaceApi = dynClient.resources.get(api_version="apps.mas.ibm.com/v1", kind="ManageWorkspace")
        workspaces = manageWorkspaceApi.get(namespace=manageNamespace)

        if not workspaces.items:
            logger.debug(f"Manage not installed for instance {instanceId}, skipping network tests")
            return True

        # Get workspace ID from first workspace
        workspace = workspaces.items[0]
        workspaceId = workspace.metadata.labels.get("mas.ibm.com/workspaceId")

        if not workspaceId:
            logger.warning("Could not determine workspace ID for Manage, skipping network tests")
            return True

        # Run connectivity tests
        return testCoreToManageConnectivity(dynClient=dynClient, instanceId=instanceId, workspaceId=workspaceId, outputDir=outputDir)

    except Exception as e:
        logger.debug(f"Error checking for Manage installation: {e}")
        return True  # Don't fail collection if network tests can't run


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
    enabledCollectors: Optional[set] = None,
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
        enabledCollectors (set, optional): Set of enabled collector names. Defaults to None.

    Returns:
        list: List of task tuples (task_name, function, *args)
    """

    tasks = []

    # Determine if we should collect standard MAS resources
    collectMASResources = enabledCollectors is None or "mas" in enabledCollectors
    collectLicensing = enabledCollectors is None or "lic" in enabledCollectors

    # Only collect standard MAS Core resources if 'mas' collector is enabled
    if collectMASResources:
        # Use the standard namespace collection tasks (IBM resources, standard resources, secrets, pods)
        tasks.extend(
            generateNamespaceCollectionTasks(
                dynClient=dynClient,
                namespace=namespace,
                outputDir=outputDir,
                noLogs=noLogs,
                customResources=None,  # No MAS-specific CRDs to add
                ibmCRDs=ibmCRDs,
            )
        )

        # Add MAS Core-specific task: Collect reconcile logs from MAS operator
        operators = [
            (namespace, "control-plane", "ibm-mas"),
            (namespace, "control-plane", "ibm-mas-ws"),
            (namespace, "control-plane", "ibm-mas-coreidp"),
            (namespace, "control-plane", "ibm-mas-addons"),
            (namespace, "control-plane", "ibm-mas-cfg-ai"),
            (namespace, "control-plane", "ibm-mas-cfg-app"),
            (namespace, "control-plane", "ibm-mas-cfg-bas"),
            (namespace, "control-plane", "ibm-mas-cfg-idp"),
            (namespace, "control-plane", "ibm-mas-cfg-scim"),
            (namespace, "control-plane", "ibm-mas-cfg-jdbc"),
            (namespace, "control-plane", "ibm-mas-cfg-mongo"),
            (namespace, "control-plane", "ibm-mas-cfg-kafka"),
            (namespace, "control-plane", "ibm-mas-cfg-objectstorage"),
            (namespace, "control-plane", "ibm-mas-cfg-smtp"),
            (namespace, "operator", "ibm-truststore-mgr"),
        ]
        tasks.extend(generateReconcileLogsCollectionTasks(operators, outputDir))

        # Add network connectivity test (Core to Manage)
        tasks.append(
            (
                "network_tests",
                _runNetworkTests,
                dynClient,
                namespace,
                outputDir,
            )
        )

        # Add system information collection
        tasks.append(
            (
                "system_info",
                _collectSystemInfo,
                dynClient,
                namespace,
                outputDir,
            )
        )

    # Add licensing information collection (only if lic collector is enabled)
    if collectLicensing:
        tasks.append(
            (
                "licensing_info",
                collectLicensingInfo,
                dynClient,
                namespace,
                outputDir,
            )
        )

    return tasks


def addMASCoreToCollectionPlan(
    plan,
    dynClient: DynamicClient,
    outputDir: str,
    noLogs: bool,
    ibmCRDs: list,
    masInstanceIds: Optional[List[str]] = None,
    enabledCollectors: Optional[set] = None,
):
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
        enabledCollectors (set, optional): Set of enabled collector names. Defaults to None.

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
                    enabledCollectors=enabledCollectors,
                )
                plan.addGroup(f"MAS Core ({instanceId})", tasks)
                logger.debug(f"Added {len(tasks)} MAS Core collection tasks for instance {instanceId}")
        else:
            logger.info("No MAS instances discovered")
        return coreNamespaces
    except Exception as e:
        logger.warning(f"MAS discovery failed: {e}")
        return set()
