# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""OpenShift Marketplace resource collection."""

import logging
from typing import List, Tuple

from kubernetes.dynamic import DynamicClient

logger = logging.getLogger(__name__)

# CatalogSource is the marketplace-specific custom resource
_MARKETPLACE_CUSTOM_RESOURCES = [
    ("operators.coreos.com/v1alpha1", "CatalogSource"),
]


def generateMarketplaceCollectionTasks(dynClient: DynamicClient, outputDir: str, noLogs: bool = False) -> List[Tuple]:
    """Generate collection tasks for the openshift-marketplace namespace.

    Uses generateNamespaceCollectionTasks to produce the standard set of tasks
    (pods, pod logs, secrets, configmaps, services, deployments, etc.) plus
    CatalogSource as a marketplace-specific custom resource.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noLogs (bool, optional): If True, skip pod log collection. Defaults to False.

    Returns:
        list: List of task tuples for namespace collection
    """
    from mas.cli.must_gather.common.task_generation import generateNamespaceCollectionTasks

    return generateNamespaceCollectionTasks(
        dynClient=dynClient,
        namespace="openshift-marketplace",
        outputDir=outputDir,
        noLogs=noLogs,
        customResources=_MARKETPLACE_CUSTOM_RESOURCES,
    )


def addMarketplaceToCollectionPlan(plan, dynClient: DynamicClient, outputDir: str, noLogs: bool = False) -> None:
    """Add OpenShift Marketplace collection tasks to the collection plan.

    Args:
        plan (CollectionPlan): Collection plan to add tasks to
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noLogs (bool, optional): If True, skip pod log collection. Defaults to False.
    """
    tasks = generateMarketplaceCollectionTasks(dynClient=dynClient, outputDir=outputDir, noLogs=noLogs)
    plan.addGroup("OpenShift Marketplace", tasks)
    logger.debug(f"Added {len(tasks)} marketplace collection tasks to plan")
