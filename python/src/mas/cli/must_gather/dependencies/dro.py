# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""IBM Data Reporter Operator dependency collector."""

import logging
from kubernetes.dynamic import DynamicClient
from .utils import discoverNamespacesFromCR, collectFromNamespaces

logger = logging.getLogger(__name__)

# DRO-specific custom resources to collect (apiVersion, kind)
DRO_RESOURCES = [
    ("marketplace.redhat.com/v1alpha1", "DataReporterConfig"),
    ("marketplace.redhat.com/v1alpha1", "MarketplaceConfig"),
    ("marketplace.redhat.com/v1alpha1", "MeterReport"),
    ("marketplace.redhat.com/v1beta1", "MeterBase"),
    ("marketplace.redhat.com/v1alpha1", "RazeeDeployment"),
    ("marketplace.redhat.com/v1beta1", "MeterDefinition"),
]


def collectDRO(dynClient: DynamicClient, outputDir: str, noDetail: bool = False, genericMustGather=None) -> bool:
    """Collect IBM Data Reporter Operator resources.

    Discovers DRO namespace from DataReporterConfig CRs and collects DRO-specific resources.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.
        genericMustGather (callable, optional): Function to perform generic must-gather collection. Defaults to None.

    Returns:
        bool: True if collection succeeded, False if namespace not found or errors occurred
    """
    try:
        # Discover DRO namespaces from DataReporterConfig
        droNamespaces = discoverNamespacesFromCR(dynClient=dynClient, kind="DataReporterConfig")

        if not droNamespaces:
            logger.info("No DRO namespaces found, skipping collection")
            print("⏭️  IBM Data Reporter Operator skipped - no DataReporterConfig resources found")
            return False

        # Collect from discovered namespaces with DRO-specific resources
        result = collectFromNamespaces(
            namespaces=droNamespaces, outputDir=outputDir, noDetail=noDetail, genericMustGather=genericMustGather, additionalResources=DRO_RESOURCES
        )

        if result:
            print(f"✅ IBM Data Reporter Operator collected from {len(droNamespaces)} namespace(s)")
        else:
            print("❌ IBM Data Reporter Operator collection encountered errors (check logs)")

        return result

    except Exception as e:
        logger.warning(f"Error collecting IBM Data Reporter Operator: {e}")
        print(f"❌ IBM Data Reporter Operator - {e}")
        return False


# Made with Bob
