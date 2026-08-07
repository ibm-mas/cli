# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Kafka dependency collector."""

import logging
from typing import Set
from kubernetes.dynamic import DynamicClient
from .utils import discoverNamespacesFromCR

logger = logging.getLogger(__name__)

# Kafka-specific custom resources to collect (apiVersion, kind)
# API version will be auto-discovered by dynamic client
KAFKA_RESOURCES = [
    ("kafka.strimzi.io/v1beta2", "Kafka"),
    ("kafka.strimzi.io/v1beta2", "KafkaUser"),
]


def _discoverKafkaNamespaces(dynClient: DynamicClient) -> Set[str]:
    """Discover namespaces containing Kafka resources.

    Discovers namespaces by finding all Kafka custom resources in the cluster.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access

    Returns:
        set: Set of namespace names where Kafka CRs exist
    """
    return discoverNamespacesFromCR(dynClient=dynClient, kind="Kafka")


def addKafkaToCollectionPlan(plan, dynClient: DynamicClient, outputDir: str, noLogs: bool, ibmCRDs: list):
    """Add Kafka collection tasks to the collection plan.

    Discovers Kafka namespaces and adds collection groups for each namespace
    to the provided collection plan.

    Args:
        plan (CollectionPlan): Collection plan to add tasks to
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noLogs (bool): If True, skip pod log collection
        ibmCRDs (list): List of IBM CRD information for collection
    """
    from ..common.task_generation import generateNamespaceCollectionTasks

    logger.debug("Discovering Kafka namespaces")
    kafkaNamespaces = _discoverKafkaNamespaces(dynClient)

    if kafkaNamespaces:
        logger.info(f"Discovered {len(kafkaNamespaces)} Kafka namespace(s): {', '.join(sorted(kafkaNamespaces))}")
        for ns in sorted(kafkaNamespaces):
            tasks = generateNamespaceCollectionTasks(
                dynClient=dynClient,
                namespace=ns,
                outputDir=outputDir,
                noLogs=noLogs,
                customResources=KAFKA_RESOURCES,
                ibmCRDs=ibmCRDs,
            )
            plan.addGroup(f"Kafka ({ns})", tasks)
            logger.debug(f"Added {len(tasks)} Kafka collection tasks for namespace {ns}")
    else:
        logger.info("No Kafka namespaces discovered")
