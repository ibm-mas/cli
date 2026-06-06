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
from typing import Optional, List
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


def collectDb2(dynClient: DynamicClient, outputDir: str, noDetail: bool = False, masInstanceIds: Optional[List[str]] = None, genericMustGather=None) -> bool:
    """Collect IBM Db2 Universal Operator resources.

    Discovers Db2 namespaces either from JdbcCfg resources (when masInstanceIds provided)
    or from Db2uCluster resources (when masInstanceIds not provided), then collects
    resources from each discovered namespace.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.
        masInstanceIds (list, optional): List of MAS instance IDs to discover Db2 from JdbcCfg. Defaults to None.
        genericMustGather (callable, optional): Function to perform generic must-gather collection. Defaults to None.

    Returns:
        bool: True if collection succeeded, False if errors occurred
    """
    try:
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

        # Collect from each discovered namespace
        if db2Namespaces and genericMustGather:
            success = True
            for namespace in sorted(db2Namespaces):
                logger.info(f"Collecting Db2 resources from namespace: {namespace}")
                if not genericMustGather(namespace=namespace, outputDir=outputDir, noDetail=noDetail):
                    success = False

            if success:
                print(f"✅ IBM Db2 Universal Operator collected from {len(db2Namespaces)} namespace(s)")
            else:
                print("❌ IBM Db2 Universal Operator collection encountered errors (check logs)")
            return success

        if not db2Namespaces:
            logger.info("No Db2 namespaces found, skipping collection")
            print("⏭️  IBM Db2 Universal Operator skipped - no Db2 instances found")

        return len(db2Namespaces) > 0

    except Exception as e:
        logger.warning(f"Error collecting IBM Db2: {e}")
        print(f"❌ IBM Db2 Universal Operator - {e}")
        return False


# Made with Bob
