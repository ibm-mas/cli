# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""IBM Db2 Universal Operator dependency collector."""

import logging
from typing import Optional, List, Tuple
from kubernetes.dynamic import DynamicClient

logger = logging.getLogger(__name__)


def _extractNamespaceFromJdbcUrl(jdbcUrl: str) -> Optional[str]:
    """Extract namespace from JDBC URL.

    Parses JDBC URL format: jdbc:db2://service.namespace.svc:port/database
    to extract the namespace component.

    Args:
        jdbcUrl (str): JDBC connection URL

    Returns:
        str: Extracted namespace or None if parsing fails
    """
    try:
        # Split by '/' to get the host part
        parts = jdbcUrl.split("/")
        if len(parts) >= 3:
            # Get host part (e.g., "c-db2u-db2u.db2u-namespace.svc")
            host = parts[2]
            # Split by '.' and get second part (namespace)
            hostParts = host.split(".")
            if len(hostParts) >= 2:
                return hostParts[1]
    except Exception as e:
        logger.debug(f"Failed to extract namespace from JDBC URL {jdbcUrl}: {e}")
    return None


def discoverDb2Namespaces(dynClient: DynamicClient, masInstanceIds: Optional[List[str]] = None) -> List[str]:
    """Discover Db2 namespaces from cluster resources.

    Discovers Db2 namespaces either from JdbcCfg resources (when masInstanceIds provided)
    or from Db2uCluster resources (when masInstanceIds not provided).

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        masInstanceIds (list, optional): List of MAS instance IDs to discover Db2 from JdbcCfg. Defaults to None.

    Returns:
        list: Sorted list of discovered Db2 namespaces
    """
    db2Namespaces = set()

    if masInstanceIds:
        # Discover Db2 namespaces from JdbcCfg resources
        try:
            jdbcApi = dynClient.resources.get(kind="JdbcCfg")
            for instanceId in masInstanceIds:
                namespace = f"mas-{instanceId}-core"
                try:
                    jdbcConfigs = jdbcApi.get(namespace=namespace)
                    for jdbcConfig in jdbcConfigs.items:
                        jdbcDict = jdbcConfig.to_dict()
                        jdbcUrl = jdbcDict.get("spec", {}).get("config", {}).get("url", "")
                        if jdbcUrl:
                            extractedNs = _extractNamespaceFromJdbcUrl(jdbcUrl)
                            if extractedNs:
                                db2Namespaces.add(extractedNs)
                except Exception as e:
                    logger.debug(f"Could not get JdbcCfg from namespace {namespace}: {e}")
        except Exception as e:
            logger.debug(f"Could not discover Db2 from JdbcCfg: {e}")
    else:
        # Discover Db2 namespaces from Db2uCluster resources
        try:
            db2Api = dynClient.resources.get(kind="Db2uCluster")
            db2Clusters = db2Api.get()
            for cluster in db2Clusters.items:
                namespace = cluster.metadata.namespace
                if namespace:
                    db2Namespaces.add(namespace)
        except Exception as e:
            logger.debug(f"Could not discover Db2 from Db2uCluster: {e}")

    return sorted(db2Namespaces)


def generateDb2CollectionTasks(
    dynClient: DynamicClient,
    namespaces: List[str],
    outputDir: str,
    noDetail: bool = False,
    noLogs: bool = False,
    ibmCRDs: Optional[List[Tuple[str, str]]] = None,
) -> List[Tuple]:
    """Generate collection tasks for Db2 namespaces.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        namespaces (list): List of Db2 namespaces to collect from
        outputDir (str): Base output directory for collected resources
        noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.
        noLogs (bool, optional): If True, skip pod log collection. Defaults to False.
        ibmCRDs (list, optional): Additional IBM CRD tuples (apiVersion, kind) to collect. Defaults to None.

    Returns:
        list: List of task tuples for namespace collection
    """
    from ..common.task_generation import generateNamespaceCollectionTasks

    allTasks = []
    for namespace in namespaces:
        # Db2-specific custom resources
        db2Resources = [
            ("db2u.databases.ibm.com/v1", "Db2uCluster"),
        ]
        tasks = generateNamespaceCollectionTasks(
            dynClient=dynClient,
            namespace=namespace,
            outputDir=outputDir,
            noDetail=noDetail,
            noLogs=noLogs,
            includeSecrets=True,
            secretData=False,
            customResources=db2Resources,
            ibmCRDs=ibmCRDs,
        )
        allTasks.extend(tasks)
    return allTasks


def addDb2ToCollectionPlan(
    plan, dynClient: DynamicClient, outputDir: str, noDetail: bool, noLogs: bool, ibmCRDs: list, masInstanceIds: Optional[List[str]] = None
):
    """Add DB2 collection tasks to the collection plan.

    Discovers DB2 namespaces and adds a collection group with all DB2 tasks
    to the provided collection plan.

    Args:
        plan (CollectionPlan): Collection plan to add tasks to
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noDetail (bool): If True, skip detailed resource collection
        noLogs (bool): If True, skip pod log collection
        ibmCRDs (list): List of IBM CRD information for collection
        masInstanceIds (list, optional): List of MAS instance IDs to filter discovery. Defaults to None.
    """
    logger.debug("Discovering DB2 namespaces")
    db2Namespaces = discoverDb2Namespaces(dynClient, masInstanceIds=masInstanceIds)

    if db2Namespaces:
        logger.info(f"Discovered {len(db2Namespaces)} DB2 namespace(s): {', '.join(sorted(db2Namespaces))}")
        tasks = generateDb2CollectionTasks(
            dynClient=dynClient,
            namespaces=db2Namespaces,
            outputDir=outputDir,
            noDetail=noDetail,
            noLogs=noLogs,
            ibmCRDs=ibmCRDs,
        )
        plan.addGroup("IBM Db2", tasks)
        logger.debug(f"Added {len(tasks)} DB2 collection tasks for {len(db2Namespaces)} namespace(s)")
    else:
        logger.info("No DB2 namespaces discovered")
