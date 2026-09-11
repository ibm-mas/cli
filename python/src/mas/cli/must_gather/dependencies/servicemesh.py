# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Service Mesh dependency collector."""

import logging
from typing import Set
from kubernetes.dynamic import DynamicClient
from .utils import discoverNamespacesFromCR

logger = logging.getLogger(__name__)

# ServiceMesh-specific custom resources to collect (apiVersion, kind)
SERVICEMESH_CLUSTER_RESOURCES = [
    ("sailoperator.io/v1", "Istio"),
    ("sailoperator.io/v1", "IstioCNI"),
]
SERVICEMESH_NS_RESOURCES = [
    ("networking.istio.io/v1", "Gateway"),
    ("networking.istio.io/v1", "VirtualService"),
]


def _discoverServiceMeshNamespaces(dynClient: DynamicClient) -> Set[str]:
    """Discover namespaces containing ServiceMesh resources.

    Discovers namespaces by finding all ServiceMesh custom resources in the cluster.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access

    Returns:
        set: Set of namespace names where ServiceMesh CRs exist
    """
    namespaces = set()
    for apiVersion, kind in SERVICEMESH_NS_RESOURCES:
        namespaces.update(discoverNamespacesFromCR(dynClient=dynClient, kind=kind, apiVersion=apiVersion))

    return namespaces


def addServiceMeshToCollectionPlan(plan, dynClient: DynamicClient, outputDir: str, noLogs: bool, ibmCRDs: list):
    """Add ServiceMesh collection tasks to the collection plan.

    Discovers ServiceMesh namespaces and adds collection groups for each namespace
    to the provided collection plan.

    Args:
        plan (CollectionPlan): Collection plan to add tasks to
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noLogs (bool): If True, skip pod log collection
        ibmCRDs (list): List of IBM CRD information for collection
    """
    from ..common.task_generation import generateNamespaceCollectionTasks
    from ..common.resources import collectResources

    # Collect cluster-scoped ServiceMesh resources first
    logger.debug("Collecting cluster-scoped ServiceMesh resources")
    clusterTasks = []

    # Add Istio and IstioCNI (cluster-scoped)
    for apiVersion, kind in SERVICEMESH_CLUSTER_RESOURCES:
        # clusterTasks.append((
        #     lambda: collectResources(namespace=None, apiVersion=apiVersion, kind=kind, outputDir=outputDir, allNamespaces=False)  # None = cluster-scoped
        # )
        clusterTasks.append(
            (
                kind,
                collectResources,
                None,  # namespace=None for cluster-scoped
                apiVersion,
                kind,
                outputDir,
                False,  # allNamespaces
            )
        )

    if clusterTasks:
        plan.addGroup("ServiceMesh (Cluster)", clusterTasks)
        logger.debug(f"Added {len(clusterTasks)} cluster-scoped ServiceMesh tasks")

    # Now collect namespace-scoped resources
    logger.debug("Discovering ServiceMesh namespaces")
    serviceMeshNamespaces = _discoverServiceMeshNamespaces(dynClient)

    if serviceMeshNamespaces:
        logger.info(f"Discovered {len(serviceMeshNamespaces)} ServiceMesh namespace(s): {', '.join(sorted(serviceMeshNamespaces))}")
        for ns in sorted(serviceMeshNamespaces):
            tasks = generateNamespaceCollectionTasks(
                dynClient=dynClient,
                namespace=ns,
                outputDir=outputDir,
                noLogs=noLogs,
                customResources=SERVICEMESH_NS_RESOURCES,
                ibmCRDs=ibmCRDs,
            )
            plan.addGroup(f"ServiceMesh ({ns})", tasks)
            logger.debug(f"Added {len(tasks)} ServiceMesh collection tasks for namespace {ns}")
    else:
        logger.info("No ServiceMesh namespaces discovered")
