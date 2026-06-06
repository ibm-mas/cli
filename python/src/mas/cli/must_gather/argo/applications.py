# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
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

import os
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


def collectArgo(dynClient: DynamicClient, outputDir: str, noDetail: bool = False, genericMustGather=None) -> bool:
    """Collect Argo CD resources from openshift-gitops namespace.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory
        noDetail (bool, optional): If True, skip detailed YAML collection. Defaults to False.
        genericMustGather (callable, optional): Function to perform generic must-gather collection. Defaults to None.

    Returns:
        bool: True if collection succeeded, False if errors occurred
    """
    try:
        # Create Argo output directory
        argoOutputDir = os.path.join(outputDir, "openshift-gitops")
        os.makedirs(argoOutputDir, exist_ok=True)

        # Perform generic resource collection using common utilities
        if genericMustGather:
            success = genericMustGather(
                namespace="openshift-gitops", outputDir=argoOutputDir, noDetail=noDetail, podsOnly=False, noLogs=False, additionalResources=[]
            )
            return success
        else:
            logger.warning("No genericMustGather function provided for openshift-gitops, skipping generic collection")
            return True

    except Exception as e:
        logger.error(f"Failed to collect Argo resources from openshift-gitops: {e}")
        return False
