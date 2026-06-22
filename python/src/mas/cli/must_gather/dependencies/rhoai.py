# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Red Hat OpenShift AI dependency collector."""

import logging
from typing import Set, List, Tuple, Optional
from kubernetes.dynamic import DynamicClient

from mas.cli.must_gather.common.task_generation import generateNamespaceCollectionTasks
from .utils import checkNamespaceExists

logger = logging.getLogger(__name__)

# ODH Resources that are provided by RHOAI operator and used by AI Service
ODH_RESOURCES = [
    ("datasciencecluster.opendatahub.io/v1", "DataScienceCluster"),
    ("dscinitialization.opendatahub.io/v1", "DSCInitialization"),
    ("components.platform.opendatahub.io/v1alpha1", "Kserve"),
    ("components.platform.opendatahub.io/v1alpha1", "ModelController"),
    ("services.platform.opendatahub.io/v1alpha1", "Auth"),
]

def _discoverRHOAINamespaces(dynClient: DynamicClient) -> Set[str]:
    """Discover Red Hat OpenShift AI namespaces.

    Checks for standard RHOAI namespaces and returns those that exist.
    RHOAI typically uses these namespaces:
    - redhat-ods-operator: Operator namespace
    - redhat-ods-applications: Applications namespace

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access

    Returns:
        set: Set of RHOAI namespace names that exist in the cluster
    """
    # RHOAI namespaces to check
    candidateNamespaces = [
        "redhat-ods-operator",
        "redhat-ods-applications"
    ]

    discoveredNamespaces = set()
    for namespace in candidateNamespaces:
        if checkNamespaceExists(dynClient, namespace):
            discoveredNamespaces.add(namespace)
            logger.debug(f"Found RHOAI namespace: {namespace}")

    return discoveredNamespaces


def _generateRHOAICollectionTasks(
    dynClient: DynamicClient,
    namespace: str,
    outputDir: str,
    noLogs: bool = False,
    customResources: Optional[List[Tuple[str, str]]] = None,
    ibmCRDs: Optional[List[Tuple[str, str]]] = None,
) -> List[Tuple]:
    """Generate collection tasks for a RHOAI namespace.

    Creates a list of collection tasks that can be executed in parallel
    for collecting RHOAI resources from a specific namespace.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        namespace (str): Target namespace for collection
        outputDir (str): Base output directory for collected resources
        noLogs (bool, optional): If True, skip pod log collection. Defaults to False.
        customResources (list, optional): Custom CRD tuples (apiVersion, kind) specific to this namespace type. Defaults to None.
        ibmCRDs (list, optional): List of IBM CRD tuples (apiVersion, kind) to collect. Defaults to None.

    Returns:
        list: List of task tuples in format (task_name, func, *args)
    """

    # Use common namespace collection task generation
    tasks = generateNamespaceCollectionTasks(
        dynClient=dynClient,
        namespace=namespace,
        outputDir=outputDir,
        noLogs=noLogs,
        secretData=False,
        customResources=customResources,
        ibmCRDs=ibmCRDs,
    )

    return tasks


def addRHOAIToCollectionPlan(plan, dynClient: DynamicClient, outputDir: str, noLogs: bool, ibmCRDs: list):
    """Add RHOAI collection tasks to the collection plan.

    Discovers RHOAI namespaces and adds collection groups for each namespace
    to the provided collection plan.

    Args:
        plan (CollectionPlan): Collection plan to add tasks to
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noLogs (bool): If True, skip pod log collection
        ibmCRDs (list): List of IBM CRD information for collection
    """
    logger.info("💭 Discovering Red Hat OpenShift AI namespaces")
    try:
        rhoaiNamespaces = _discoverRHOAINamespaces(dynClient)
        if rhoaiNamespaces:
            logger.debug(f"Discovered {len(rhoaiNamespaces)} RHOAI namespace(s): {', '.join(sorted(rhoaiNamespaces))}")
            for ns in sorted(rhoaiNamespaces):
                tasks = _generateRHOAICollectionTasks(
                    dynClient=dynClient,
                    namespace=ns,
                    outputDir=outputDir,
                    noLogs=noLogs,
                    customResources=ODH_RESOURCES if ns == 'redhat-ods-applications' else None,
                    ibmCRDs=ibmCRDs,
                )
                plan.addGroup(f"Red Hat OpenShift AI ({ns})", tasks)
                logger.debug(f"✅ {ns}: Added {len(tasks)} collection tasks")
        else:
            logger.warning("⚠️ No Red Hat OpenShift AI namespaces discovered")
    except Exception as e:
        logger.error(f"❌ RHOAI discovery failed: {e}")
