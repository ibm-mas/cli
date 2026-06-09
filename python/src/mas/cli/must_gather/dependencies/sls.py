# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""IBM Suite License Service dependency collector."""

import logging
from typing import Set, Optional, List, Tuple
from kubernetes.dynamic import DynamicClient

from mas.cli.must_gather.common import generateReconcileLogsCollectionTasks
from mas.cli.must_gather.common.task_generation import generateNamespaceCollectionTasks
from .utils import discoverNamespacesFromCR

logger = logging.getLogger(__name__)


def discoverSLSNamespaces(dynClient: DynamicClient, masInstanceIds: Optional[List[str]] = None) -> Set[str]:
    """Discover SLS namespaces from LicenseService CRs.

    Note: The masInstanceIds parameter is kept for backward compatibility but is not used.
    Discovery is always done via LicenseService CRs, which is simpler and more reliable
    than parsing SlsCfg URLs and searching for routes.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        masInstanceIds (list, optional): Unused - kept for backward compatibility. Defaults to None.

    Returns:
        set: Set of unique SLS namespace names
    """
    return discoverNamespacesFromCR(dynClient=dynClient, kind="LicenseService")


def generateSLSCollectionTasks(
    dynClient: DynamicClient,
    namespace: str,
    outputDir: str,
    noDetail: bool = False,
    noLogs: bool = False,
    ibmCRDs: Optional[List[Tuple[str, str]]] = None,
) -> List[Tuple]:
    """Generate collection tasks for an SLS namespace.

    Creates a list of collection tasks that can be executed in parallel
    for collecting SLS resources from a specific namespace.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        namespace (str): Target namespace for collection
        outputDir (str): Base output directory for collected resources
        noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.
        noLogs (bool, optional): If True, skip pod log collection. Defaults to False.
        ibmCRDs (list, optional): List of IBM CRD tuples (apiVersion, kind) to collect. Defaults to None.

    Returns:
        list: List of task tuples in format (task_name, func, *args)
    """
    # Use common namespace collection task generation
    # SLS always collects pod logs (podLogs=True)
    tasks = generateNamespaceCollectionTasks(
        dynClient=dynClient,
        namespace=namespace,
        outputDir=outputDir,
        noDetail=noDetail,
        noLogs=noLogs,
        includeSecrets=True,
        secretData=False,
        customResources=None,  # SLS uses IBM CRDs
        ibmCRDs=ibmCRDs,
    )

    # Add SLS-specific reconcile logs tasks
    if not noDetail:
        operators = [
            (namespace, "control-plane", "controller-manager"),
            (namespace, "operator", "ibm-truststore-mgr"),
        ]
        tasks.extend(generateReconcileLogsCollectionTasks(operators, outputDir))

    return tasks


def addSLSToCollectionPlan(
    plan, dynClient: DynamicClient, outputDir: str, noDetail: bool, noLogs: bool, ibmCRDs: list, masInstanceIds: Optional[List[str]] = None
):
    """Add SLS collection tasks to the collection plan.

    Discovers SLS namespaces and adds collection groups for each namespace
    to the provided collection plan.

    Args:
        plan (CollectionPlan): Collection plan to add tasks to
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noDetail (bool): If True, skip detailed resource collection
        noLogs (bool): If True, skip pod log collection
        ibmCRDs (list): List of IBM CRD information for collection
        masInstanceIds (list, optional): List of MAS instance IDs (kept for compatibility, not used). Defaults to None.
    """
    logger.info("💭 Discovering SLS namespaces")
    try:
        slsNamespaces = discoverSLSNamespaces(dynClient, masInstanceIds=masInstanceIds)
        if slsNamespaces:
            logger.debug(f"Discovered {len(slsNamespaces)} SLS namespace(s): {', '.join(sorted(slsNamespaces))}")
            for ns in sorted(slsNamespaces):
                tasks = generateSLSCollectionTasks(
                    dynClient=dynClient,
                    namespace=ns,
                    outputDir=outputDir,
                    noDetail=noDetail,
                    noLogs=noLogs,
                    ibmCRDs=ibmCRDs,
                )
                plan.addGroup(ns, tasks)
                logger.debug(f"✅ {ns}: Added {len(tasks)} collection tasks")
        else:
            logger.warning("⚠️ No SLS namespaces discovered")
    except Exception as e:
        logger.error(f"❌ SLS discovery failed: {e}")
