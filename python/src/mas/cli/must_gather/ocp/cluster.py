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
from typing import Tuple, Dict, List
from kubernetes.dynamic import DynamicClient
from mas.cli.must_gather.common.resources import collectResources
from mas.cli.must_gather.common.crd_processor import processCRDs, PrinterColumn

logger = logging.getLogger(__name__)

# Module-level variables to store CRD processing results
_printerColumnsCache: Dict[Tuple[str, str], List[PrinterColumn]] = {}
_ibmCRDsList: List[Tuple[str, str]] = []


def collectClusterResources(dynClient: DynamicClient, outputDir: str, noDetail: bool = False) -> Tuple[bool, Dict, List]:
    """Collect cluster-level OpenShift resources.

    Collects cluster-scoped resources including CRDs, storage classes, cluster versions,
    object storage resources, namespaces, package manifests, and RBAC resources.
    CRD processing is performed first to extract printer columns and identify IBM CRDs.
    Some resources (namespaces, packagemanifests, clusterroles, clusterrolebindings)
    are always collected in summary-only mode regardless of the noDetail flag.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.

    Returns:
        tuple: (success, printerColumnsCache, ibmCRDsList)
            - success: True if collection succeeded, False if errors occurred
            - printerColumnsCache: Dict mapping (kind, apiVersion) to printer columns
            - ibmCRDsList: List of (kind, apiVersion) tuples for IBM CRDs
    """
    global _printerColumnsCache, _ibmCRDsList

    successCount = 0
    totalCount = 0

    # Process CRDs first to extract printer columns and identify IBM CRDs
    logger.info("Processing CustomResourceDefinitions...")
    printerColumnsCache, ibmCRDsList = processCRDs(dynClient, outputDir)
    _printerColumnsCache = printerColumnsCache
    _ibmCRDsList = ibmCRDsList
    logger.info(f"Processed {len(printerColumnsCache)} CRDs with printer columns, identified {len(ibmCRDsList)} IBM CRDs")

    # Resources to collect with full detail (unless noDetail=True) - (apiVersion, kind)
    detailedResources = [
        ("storage.k8s.io/v1", "StorageClass"),
        ("config.openshift.io/v1", "ClusterVersion"),
        ("config.openshift.io/v1", "Infrastructure"),
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
            allNamespaces=False,
        ):
            successCount += 1

    # Return success status along with CRD processing results
    return successCount > 0, printerColumnsCache, ibmCRDsList


def getPrinterColumnsCache() -> Dict[Tuple[str, str], List[PrinterColumn]]:
    """Get the cached printer columns from CRD processing.

    Returns:
        dict: Printer columns cache mapping (kind, apiVersion) to printer columns
    """
    return _printerColumnsCache


def getIBMCRDsList() -> List[Tuple[str, str]]:
    """Get the list of IBM CRDs identified during processing.

    Returns:
        list: List of (kind, apiVersion) tuples for IBM CRDs
    """
    return _ibmCRDsList
