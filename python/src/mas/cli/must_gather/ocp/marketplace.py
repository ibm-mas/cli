# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""OpenShift Marketplace resource collection."""

import logging
from kubernetes.dynamic import DynamicClient
from mas.cli.must_gather.common.resources import collectResources

logger = logging.getLogger(__name__)


def collectMarketplaceResources(dynClient: DynamicClient, outputDir: str) -> bool:
    """Collect OpenShift Marketplace resources.

    Collects resources from the openshift-marketplace namespace including:
    - catalogsources: Operator catalog sources
    - jobs: Catalog import and refresh jobs

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources

    Returns:
        bool: True if collection succeeded, False if errors occurred
    """
    successCount = 0
    totalCount = 0

    # Resources to collect from openshift-marketplace - (apiVersion, kind)
    marketplaceResources = [
        ("operators.coreos.com/v1alpha1", "CatalogSource"),
        ("batch/v1", "Job"),
    ]

    for apiVersion, kind in marketplaceResources:
        totalCount += 1
        if collectResources(
            namespace="openshift-marketplace",
            apiVersion=apiVersion,
            kind=kind,
            outputDir=outputDir,
            allNamespaces=False,
        ):
            successCount += 1

    return successCount > 0
