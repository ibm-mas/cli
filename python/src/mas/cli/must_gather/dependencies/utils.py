# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Utility functions for dependency collectors."""

import logging
from typing import Set, List, Optional
from kubernetes.dynamic import DynamicClient
from kubernetes.client.exceptions import ApiException

logger = logging.getLogger(__name__)


def checkNamespaceExists(dynClient: DynamicClient, namespace: str) -> bool:
    """Check if a namespace exists in the cluster.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client
        namespace (str): Namespace name to check

    Returns:
        bool: True if namespace exists, False otherwise
    """
    try:
        namespaceApi = dynClient.resources.get(kind="Namespace")
        namespaceApi.get(name=namespace)
        return True
    except ApiException as e:
        if e.status == 404:
            return False
        raise
    except Exception:
        return False


def discoverNamespacesFromCR(dynClient: DynamicClient, kind: str, apiVersion: Optional[str] = None) -> Set[str]:
    """Discover namespaces by finding all instances of a custom resource.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client
        kind (str): Kind of custom resource to search for
        apiVersion (str, optional): API version of the resource. Defaults to None.

    Returns:
        set: Set of namespace names where the CR exists
    """
    namespaces = set()
    try:
        if apiVersion:
            api = dynClient.resources.get(api_version=apiVersion, kind=kind)
        else:
            api = dynClient.resources.get(kind=kind)

        resources = api.get()
        for resource in resources.items:
            namespace = resource.metadata.namespace
            if namespace:
                namespaces.add(namespace)
    except Exception as e:
        logger.debug(f"Could not discover namespaces from {kind}: {e}")

    return namespaces


def collectFromNamespaces(
    namespaces: Set[str], outputDir: str, noDetail: bool, genericMustGather, additionalResources: Optional[List[tuple[str, str]]] = None
) -> bool:
    """Collect resources from multiple namespaces.

    Args:
        namespaces (set): Set of namespace names to collect from
        outputDir (str): Output directory
        noDetail (bool): Skip detailed collection
        genericMustGather (callable): Function to perform collection
        additionalResources (list, optional): Additional resource types as (apiVersion, kind) tuples. Defaults to None.

    Returns:
        bool: True if all collections succeeded
    """
    if not namespaces or not genericMustGather:
        return len(namespaces) > 0

    success = True
    for namespace in sorted(namespaces):
        logger.info(f"Collecting from namespace: {namespace}")
        kwargs = {"namespace": namespace, "outputDir": outputDir, "noDetail": noDetail}
        if additionalResources:
            kwargs["additionalResources"] = additionalResources

        if not genericMustGather(**kwargs):
            success = False

    return success
