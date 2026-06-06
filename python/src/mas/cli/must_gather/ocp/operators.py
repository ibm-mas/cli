# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Kubernetes operator resource collection."""

import logging
from kubernetes.dynamic import DynamicClient

logger = logging.getLogger(__name__)


def collectOperatorResources(dynClient: DynamicClient, outputDir: str, noDetail: bool = False) -> bool:
    """Collect Kubernetes operator resources.

    NOTE: This function is deprecated. Operator resources (Subscription, InstallPlan,
    ClusterServiceVersion) are namespace-scoped and should be collected per-namespace
    as part of standard resource collection in genericMustGather().

    This function is kept for backward compatibility but does nothing.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.

    Returns:
        bool: Always returns True
    """
    logger.info("Operator resources (Subscription, InstallPlan, OperatorCondition) are now collected per-namespace")
    return True


# Made with Bob
