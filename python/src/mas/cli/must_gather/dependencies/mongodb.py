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
from kubernetes.dynamic import DynamicClient
from .utils import discoverNamespacesFromCR, collectFromNamespaces

logger = logging.getLogger(__name__)

# MongoDB-specific custom resources to collect (apiVersion, kind)
MONGODB_RESOURCES = [
    ("mongodbcommunity.mongodb.com/v1", "MongoDBCommunity"),
]


def collectMongoDB(dynClient: DynamicClient, outputDir: str, noDetail: bool = False, genericMustGather=None) -> bool:
    """Collect MongoDB Community resources.

    Discovers MongoDB namespaces from MongoDBCommunity CRs and collects MongoDB-specific resources.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.
        genericMustGather (callable, optional): Function to perform generic must-gather collection. Defaults to None.

    Returns:
        bool: True if collection succeeded, False if no MongoDB found or errors occurred
    """
    try:
        # Discover MongoDB namespaces from MongoDBCommunity CRs
        mongoNamespaces = discoverNamespacesFromCR(dynClient=dynClient, kind="MongoDBCommunity")

        if not mongoNamespaces:
            logger.info("No MongoDB namespaces found, skipping collection")
            print("⏭️  MongoDB Community skipped - no MongoDB resources found")
            return False

        # Collect from discovered namespaces with MongoDB-specific resources
        result = collectFromNamespaces(
            namespaces=mongoNamespaces, outputDir=outputDir, noDetail=noDetail, genericMustGather=genericMustGather, additionalResources=MONGODB_RESOURCES
        )

        if result:
            print(f"✅ MongoDB Community collected from {len(mongoNamespaces)} namespace(s)")
        else:
            print("❌ MongoDB Community collection encountered errors (check logs)")

        return result

    except Exception as e:
        logger.warning(f"Error collecting MongoDB: {e}")
        print(f"❌ MongoDB Community - {e}")
        return False


# Made with Bob
