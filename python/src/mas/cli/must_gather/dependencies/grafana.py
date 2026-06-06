# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Grafana dependency collector."""

import logging
from kubernetes.dynamic import DynamicClient
from .utils import discoverNamespacesFromCR, collectFromNamespaces

logger = logging.getLogger(__name__)

# Grafana-specific custom resources to collect (apiVersion, kind)
GRAFANA_RESOURCES = [
    ("grafana.integreatly.org/v1beta1", "Grafana"),
    ("grafana.integreatly.org/v1beta1", "GrafanaDatasource"),
]


def collectGrafana(dynClient: DynamicClient, outputDir: str, noDetail: bool = False, genericMustGather=None) -> bool:
    """Collect Grafana resources.

    Discovers Grafana namespaces from Grafana CRs and collects Grafana-specific resources.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.
        genericMustGather (callable, optional): Function to perform generic must-gather collection. Defaults to None.

    Returns:
        bool: True if collection succeeded, False if no Grafana found or errors occurred
    """
    try:
        # Discover Grafana namespaces from Grafana CRs
        grafanaNamespaces = discoverNamespacesFromCR(dynClient=dynClient, kind="Grafana")

        if not grafanaNamespaces:
            logger.info("No Grafana namespaces found, skipping collection")
            print("⏭️  Grafana skipped - no Grafana resources found")
            return False

        # Collect from discovered namespaces with Grafana-specific resources
        result = collectFromNamespaces(
            namespaces=grafanaNamespaces, outputDir=outputDir, noDetail=noDetail, genericMustGather=genericMustGather, additionalResources=GRAFANA_RESOURCES
        )

        return result

    except Exception as e:
        logger.warning(f"Error collecting Grafana: {e}")
        print(f"❌ Grafana - {e}")
        return False
