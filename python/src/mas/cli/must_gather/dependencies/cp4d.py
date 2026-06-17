# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""IBM CloudPak for Data dependency collector."""

import logging
from typing import List, Tuple, Optional
from kubernetes.dynamic import DynamicClient
from kubernetes.client.exceptions import ApiException

logger = logging.getLogger(__name__)


def _discoverCP4DNamespaces(dynClient: DynamicClient) -> List[str]:
    """Discover CloudPak for Data namespaces.

    Checks if ibm-cpd-operators namespace exists and returns both
    ibm-cpd and ibm-cpd-operators namespaces if found.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access

    Returns:
        list: List of CP4D namespaces (empty if not found)
    """
    try:
        # Check if ibm-cpd-operators namespace exists
        namespaceApi = dynClient.resources.get(kind="Namespace")
        namespaceApi.get(name="ibm-cpd-operators")

        # If we get here, namespace exists - return both CP4D namespaces
        return ["ibm-cpd", "ibm-cpd-operators"]

    except ApiException as e:
        if e.status == 404:
            logger.debug("ibm-cpd-operators namespace not found, skipping CP4D collection")
            return []
        logger.debug(f"Error checking for CP4D namespace: {e}")
        return []
    except Exception as e:
        logger.debug(f"Error discovering CP4D namespaces: {e}")
        return []


def _generateCP4DCollectionTasks(
    dynClient: DynamicClient,
    namespaces: List[str],
    outputDir: str,
    noLogs: bool = False,
    ibmCRDs: Optional[List[Tuple[str, str]]] = None,
) -> List[Tuple]:
    """Generate collection tasks for CP4D namespaces.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        namespaces (list): List of CP4D namespaces to collect from
        outputDir (str): Base output directory for collected resources
        noLogs (bool, optional): If True, skip pod log collection. Defaults to False.
        ibmCRDs (list, optional): Additional IBM CRD tuples (apiVersion, kind) to collect. Defaults to None.

    Returns:
        list: List of task tuples for namespace collection
    """
    from ..common.task_generation import generateNamespaceCollectionTasks

    allTasks = []
    for namespace in namespaces:
        tasks = generateNamespaceCollectionTasks(
            dynClient=dynClient,
            namespace=namespace,
            outputDir=outputDir,
            noLogs=noLogs,
            secretData=False,
            customResources=None,  # CP4D doesn't have specific CRDs to collect
            ibmCRDs=ibmCRDs,
        )
        allTasks.extend(tasks)
    return allTasks


def addCP4DToCollectionPlan(plan, dynClient: DynamicClient, outputDir: str, noLogs: bool, ibmCRDs: list):
    """Add CP4D collection tasks to the collection plan.

    Discovers CP4D namespaces and adds a collection group with all CP4D tasks
    to the provided collection plan.

    Args:
        plan (CollectionPlan): Collection plan to add tasks to
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noLogs (bool): If True, skip pod log collection
        ibmCRDs (list): List of IBM CRD information for collection
    """
    logger.debug("Discovering CP4D namespaces")
    cp4dNamespaces = _discoverCP4DNamespaces(dynClient)

    if cp4dNamespaces:
        logger.info(f"Discovered {len(cp4dNamespaces)} CP4D namespace(s): {', '.join(sorted(cp4dNamespaces))}")
        tasks = _generateCP4DCollectionTasks(
            dynClient=dynClient,
            namespaces=cp4dNamespaces,
            outputDir=outputDir,
            noLogs=noLogs,
            ibmCRDs=ibmCRDs,
        )
        plan.addGroup("IBM CloudPak for Data", tasks)
        logger.debug(f"Added {len(tasks)} CP4D collection tasks for {len(cp4dNamespaces)} namespace(s)")
    else:
        logger.info("No CP4D namespaces discovered")
