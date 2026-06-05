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
from mas.cli.must_gather.common.resources import collectResources

logger = logging.getLogger(__name__)


def collectOperatorResources(dynClient: DynamicClient, outputDir: str, noDetail: bool = False) -> bool:
    """Collect Kubernetes operator resources across all namespaces.

    Collects operator-related resources from all namespaces including:
    - subscriptions: Operator subscriptions
    - installplans: Operator installation plans
    - operatorconditions: Operator health conditions

    All resources are collected with allNamespaces=True flag.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.

    Returns:
        bool: True if collection succeeded, False if errors occurred
    """
    successCount = 0
    totalCount = 0

    # Operator resources to collect across all namespaces - (apiVersion, kind)
    operatorResources = [
        ("operators.coreos.com/v1alpha1", "Subscription"),
        ("operators.coreos.com/v1alpha1", "InstallPlan"),
        ("operators.coreos.com/v2", "OperatorCondition"),
    ]

    for apiVersion, kind in operatorResources:
        totalCount += 1
        if collectResources(
            dynClient=dynClient,
            namespace=None,
            apiVersion=apiVersion,
            kind=kind,
            outputDir=outputDir,
            noDetail=noDetail,
            describe=False,
            allNamespaces=True,  # Collect from all namespaces
        ):
            successCount += 1

    return successCount > 0


# Made with Bob
