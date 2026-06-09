# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""MongoDB Community dependency collector."""

import logging
from typing import Set
from kubernetes.dynamic import DynamicClient
from .utils import discoverNamespacesFromCR

logger = logging.getLogger(__name__)

# MongoDB-specific custom resources to collect (apiVersion, kind)
MONGODB_RESOURCES = [
    ("mongodbcommunity.mongodb.com/v1", "MongoDBCommunity"),
]


def discoverMongoDBNamespaces(dynClient: DynamicClient) -> Set[str]:
    """Discover namespaces containing MongoDB Community resources.

    Discovers namespaces by finding all MongoDBCommunity custom resources in the cluster.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access

    Returns:
        set: Set of namespace names where MongoDBCommunity CRs exist
    """
    return discoverNamespacesFromCR(dynClient=dynClient, kind="MongoDBCommunity")


def addMongoDBToCollectionPlan(plan, dynClient: DynamicClient, outputDir: str, noDetail: bool, noLogs: bool, ibmCRDs: list):
    """Add MongoDB collection tasks to the collection plan.

    Discovers MongoDB namespaces and adds collection groups for each namespace
    to the provided collection plan.

    Args:
        plan (CollectionPlan): Collection plan to add tasks to
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noDetail (bool): If True, skip detailed resource collection
        noLogs (bool): If True, skip pod log collection
        ibmCRDs (list): List of IBM CRD information for collection
    """
    from ..common.task_generation import generateNamespaceCollectionTasks

    logger.debug("Discovering MongoDB namespaces")
    mongoNamespaces = discoverMongoDBNamespaces(dynClient)

    if mongoNamespaces:
        logger.info(f"Discovered {len(mongoNamespaces)} MongoDB namespace(s): {', '.join(sorted(mongoNamespaces))}")
        for ns in sorted(mongoNamespaces):
            tasks = generateNamespaceCollectionTasks(
                dynClient=dynClient,
                namespace=ns,
                outputDir=outputDir,
                noDetail=noDetail,
                noLogs=noLogs,
                includeSecrets=True,
                secretData=False,
                customResources=MONGODB_RESOURCES,
                ibmCRDs=ibmCRDs,
            )
            plan.addGroup(f"MongoDB ({ns})", tasks)
            logger.debug(f"Added {len(tasks)} MongoDB collection tasks for namespace {ns}")
    else:
        logger.info("No MongoDB namespaces discovered")
