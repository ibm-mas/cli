# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Cluster-level OCP resource collection."""

import logging
from kubernetes.dynamic import DynamicClient
from mas.cli.must_gather.common.resources import collectResources

logger = logging.getLogger(__name__)


def collectClusterResources(dynClient: DynamicClient, outputDir: str, noDetail: bool = False) -> bool:
    """Collect cluster-level OpenShift resources.

    Collects cluster-scoped resources including storage classes, cluster versions,
    object storage resources, namespaces, package manifests, and RBAC resources.
    Some resources (namespaces, packagemanifests, clusterroles, clusterrolebindings)
    are always collected in summary-only mode regardless of the noDetail flag.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.

    Returns:
        bool: True if collection succeeded, False if errors occurred
    """
    successCount = 0
    totalCount = 0

    # Resources to collect with full detail (unless noDetail=True) - (apiVersion, kind)
    detailedResources = [
        ("storage.k8s.io/v1", "StorageClass"),
        ("config.openshift.io/v1", "ClusterVersion"),
        ("objectbucket.io/v1alpha1", "ObjectBucket"),
        ("objectbucket.io/v1alpha1", "ObjectBucketClaim"),
        ("ocs.ibm.io/v1", "ObjectStorageCfg"),
    ]

    # Resources to collect summary only (always noDetail=True) - (apiVersion, kind)
    summaryOnlyResources = [
        ("v1", "Namespace"),
        ("packages.operators.coreos.com/v1", "PackageManifest"),
        ("rbac.authorization.k8s.io/v1", "ClusterRole"),
        ("rbac.authorization.k8s.io/v1", "ClusterRoleBinding"),
    ]

    # Collect detailed resources
    for apiVersion, kind in detailedResources:
        totalCount += 1
        if collectResources(
            dynClient=dynClient,
            namespace=None,
            apiVersion=apiVersion,
            kind=kind,
            outputDir=outputDir,
            noDetail=noDetail,
            describe=False,
            allNamespaces=False,
        ):
            successCount += 1

    # Collect summary-only resources
    for apiVersion, kind in summaryOnlyResources:
        totalCount += 1
        if collectResources(
            dynClient=dynClient,
            namespace=None,
            apiVersion=apiVersion,
            kind=kind,
            outputDir=outputDir,
            noDetail=True,  # Always summary only
            describe=False,
            allNamespaces=False,
        ):
            successCount += 1

    # Return True if at least one resource was collected successfully
    return successCount > 0


# Made with Bob
