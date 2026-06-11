# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Argo applications collector for must-gather.

This module provides functionality to collect Argo CD resources from the
openshift-gitops namespace if it exists.
"""

import logging
from kubernetes.dynamic import DynamicClient

logger = logging.getLogger(__name__)


def checkArgoNamespace(dynClient: DynamicClient) -> bool:
    """Check if openshift-gitops namespace exists.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access

    Returns:
        bool: True if openshift-gitops namespace exists, False otherwise
    """
    try:
        # Get namespace API
        namespaceApi = dynClient.resources.get(api_version="v1", kind="Namespace")

        # Get all namespaces
        allNamespaces = namespaceApi.get()

        # Check if openshift-gitops exists
        for ns in allNamespaces.items:
            if ns.metadata.name == "openshift-gitops":
                return True

        return False

    except Exception as e:
        logger.warning(f"Failed to check for openshift-gitops namespace: {e}")
        return False


def addArgoToCollectionPlan(plan, dynClient: DynamicClient, outputDir: str, noLogs: bool, ibmCRDs: list):
    """Add Argo CD collection tasks to the collection plan.

    Checks for openshift-gitops namespace and adds collection group if it exists.

    Args:
        plan (CollectionPlan): Collection plan to add tasks to
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noLogs (bool): If True, skip pod log collection
        ibmCRDs (list): List of IBM CRD information for collection
    """
    from mas.cli.must_gather.common.task_generation import generateNamespaceCollectionTasks

    logger.info("Checking for Argo CD")
    try:
        if checkArgoNamespace(dynClient):
            logger.info("Discovered Argo CD (openshift-gitops namespace exists)")
            # Generate tasks for Argo CD namespace
            tasks = generateNamespaceCollectionTasks(
                dynClient=dynClient,
                namespace="openshift-gitops",
                outputDir=outputDir,
                noLogs=noLogs,
                secretData=False,
                customResources=None,
                ibmCRDs=ibmCRDs,
            )
            plan.addGroup("Argo CD (openshift-gitops)", tasks)
            logger.debug(f"Added {len(tasks)} Argo CD collection tasks")
        else:
            logger.info("Argo CD not found (openshift-gitops namespace does not exist)")
    except Exception as e:
        logger.warning(f"Argo discovery failed: {e}")
