# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Grafana dependency collector."""

import logging
from typing import Set
from kubernetes.dynamic import DynamicClient
from .utils import discoverNamespacesFromCR

logger = logging.getLogger(__name__)

# Grafana-specific custom resources to collect (apiVersion, kind)
GRAFANA_RESOURCES = [
    ("grafana.integreatly.org/v1beta1", "Grafana"),
    ("grafana.integreatly.org/v1beta1", "GrafanaDatasource"),
]


def _discoverGrafanaNamespaces(dynClient: DynamicClient) -> Set[str]:
    """Discover namespaces containing Grafana resources.

    Discovers namespaces by finding all Grafana custom resources in the cluster.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access

    Returns:
        set: Set of namespace names where Grafana CRs exist
    """
    return discoverNamespacesFromCR(dynClient=dynClient, kind="Grafana")


def addGrafanaToCollectionPlan(plan, dynClient: DynamicClient, outputDir: str, noLogs: bool, ibmCRDs: list):
    """Add Grafana collection tasks to the collection plan.

    Discovers Grafana namespaces and adds collection groups for each namespace
    to the provided collection plan.

    Args:
        plan (CollectionPlan): Collection plan to add tasks to
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noLogs (bool): If True, skip pod log collection
        ibmCRDs (list): List of IBM CRD information for collection
    """
    from ..common.task_generation import generateNamespaceCollectionTasks

    logger.debug("Discovering Grafana namespaces")
    grafanaNamespaces = _discoverGrafanaNamespaces(dynClient)

    if grafanaNamespaces:
        logger.info(f"Discovered {len(grafanaNamespaces)} Grafana namespace(s): {', '.join(sorted(grafanaNamespaces))}")
        for ns in sorted(grafanaNamespaces):
            tasks = generateNamespaceCollectionTasks(
                dynClient=dynClient,
                namespace=ns,
                outputDir=outputDir,
                noLogs=noLogs,
                customResources=GRAFANA_RESOURCES,
                ibmCRDs=ibmCRDs,
            )
            plan.addGroup(f"Grafana ({ns})", tasks)
            logger.debug(f"Added {len(tasks)} Grafana collection tasks for namespace {ns}")
    else:
        logger.info("No Grafana namespaces discovered")
