# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Cluster-level OCP resource collection."""

import logging
from mas.cli.must_gather.common.resources import collectResources

logger = logging.getLogger(__name__)


def collectClusterResources(outputDir: str) -> bool:
    """Collect cluster-level OpenShift resources.

    Collects cluster-scoped resources including storage classes, cluster versions,
    object storage resources, namespaces, package manifests, and RBAC resources.

    Note: CRD processing is now handled upfront in app.py before the discovery phase,
    so this function no longer processes CRDs.

    Args:
        outputDir (str): Base output directory for collected resources

    Returns:
        bool: True if collection succeeded, False if errors occurred
    """
    successCount = 0
    totalCount = 0

    # Resources to collect with full detail - (apiVersion, kind)
    detailedResources = [
        ("storage.k8s.io/v1", "StorageClass"),
        ("config.openshift.io/v1", "ClusterVersion"),
        ("config.openshift.io/v1", "Infrastructure"),
        ("objectbucket.io/v1alpha1", "ObjectBucket"),
        ("objectbucket.io/v1alpha1", "ObjectBucketClaim"),
        ("ocs.ibm.io/v1", "ObjectStorageCfg"),
    ]

    # Resources to collect summary only - (apiVersion, kind)
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
            namespace=None,
            apiVersion=apiVersion,
            kind=kind,
            outputDir=outputDir,
            allNamespaces=False,
        ):
            successCount += 1

    # Collect summary-only resources
    for apiVersion, kind in summaryOnlyResources:
        totalCount += 1
        if collectResources(
            namespace=None,
            apiVersion=apiVersion,
            kind=kind,
            outputDir=outputDir,
            allNamespaces=False,
        ):
            successCount += 1

    # Return success status
    return successCount > 0
