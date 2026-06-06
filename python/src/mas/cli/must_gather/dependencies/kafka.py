# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Kafka dependency collector."""

import logging
from kubernetes.dynamic import DynamicClient
from .utils import discoverNamespacesFromCR, collectFromNamespaces

logger = logging.getLogger(__name__)

# Kafka-specific custom resources to collect (apiVersion, kind)
# API version will be auto-discovered by dynamic client
KAFKA_RESOURCES = [
    ("kafka.strimzi.io/v1beta2", "Kafka"),
    ("kafka.strimzi.io/v1beta2", "KafkaUser"),
]


def collectKafka(dynClient: DynamicClient, outputDir: str, noDetail: bool = False, genericMustGather=None) -> bool:
    """Collect Kafka resources.

    Discovers Kafka namespaces from Kafka CRs and collects Kafka-specific resources.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.
        genericMustGather (callable, optional): Function to perform generic must-gather collection. Defaults to None.

    Returns:
        bool: True if collection succeeded, False if no Kafka found or errors occurred
    """
    try:
        # Discover Kafka namespaces from Kafka CRs
        kafkaNamespaces = discoverNamespacesFromCR(dynClient=dynClient, kind="Kafka")

        if not kafkaNamespaces:
            logger.info("No Kafka namespaces found, skipping collection")
            print("⏭️  Kafka skipped - no Kafka resources found")
            return False

        # Collect from discovered namespaces with Kafka-specific resources
        result = collectFromNamespaces(
            namespaces=kafkaNamespaces, outputDir=outputDir, noDetail=noDetail, genericMustGather=genericMustGather, additionalResources=KAFKA_RESOURCES
        )

        return result

    except Exception as e:
        logger.warning(f"Error collecting Kafka: {e}")
        print(f"❌ Kafka - {e}")
        return False
