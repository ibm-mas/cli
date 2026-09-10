# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Red Hat Certificate Manager dependency collector."""

import logging
from typing import Set
from kubernetes.dynamic import DynamicClient
from .utils import checkNamespaceExists

logger = logging.getLogger(__name__)

# Resources collected scoped to the cert-manager operator namespaces only
CERT_MANAGER_NAMESPACE_RESOURCES = [
    ("operator.openshift.io/v1alpha1", "CertManager"),
    ("cert-manager.io/v1", "ClusterIssuer"),
]

# Namespace-scoped resources created by cert-manager in workload namespaces;
# collected across all namespaces so workload certificates are not missed
CERT_MANAGER_ALL_NAMESPACE_RESOURCES = [
    ("cert-manager.io/v1", "CertificateRequest"),
    ("cert-manager.io/v1", "Certificate"),
    ("cert-manager.io/v1", "Issuer"),
    ("acme.cert-manager.io/v1", "Order"),
    ("acme.cert-manager.io/v1", "Challenge"),
]


def _discoverCertManagerNamespaces(dynClient: DynamicClient) -> Set[str]:
    """Discover Certificate Manager namespaces.

    Checks for the existence of cert-manager-operator and cert-manager namespaces.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access

    Returns:
        set: Set of namespace names where cert-manager is installed
    """
    namespaces = set()

    try:
        # Check for cert-manager-operator namespace
        if checkNamespaceExists(dynClient, "cert-manager-operator"):
            namespaces.add("cert-manager-operator")

        # Check for cert-manager namespace
        if checkNamespaceExists(dynClient, "cert-manager"):
            namespaces.add("cert-manager")

    except Exception as e:
        logger.debug(f"Error discovering cert-manager namespaces: {e}")

    return namespaces


def addCertManagerToCollectionPlan(plan, dynClient: DynamicClient, outputDir: str, noLogs: bool, ibmCRDs: list):
    """Add Certificate Manager collection tasks to the collection plan.

    Discovers Certificate Manager namespaces and adds two kinds of collection groups:
    - One group per operator namespace (cert-manager, cert-manager-operator) collecting
      CertManager and ClusterIssuer resources scoped to those namespaces.
    - One all-namespaces group collecting CertificateRequest, Certificate, Issuer, Order,
      and Challenge across every namespace, since cert-manager creates these resources in
      workload namespaces (e.g. mas-inst1-core, ibm-sls) not in the operator namespace.

    Args:
        plan (CollectionPlan): Collection plan to add tasks to
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noLogs (bool): If True, skip pod log collection
        ibmCRDs (list): List of IBM CRD information for collection
    """
    from ..common.task_generation import generateNamespaceCollectionTasks
    from ..common.resources import collectResources

    logger.debug("Discovering Certificate Manager namespaces")
    certManagerNamespaces = _discoverCertManagerNamespaces(dynClient)

    if certManagerNamespaces:
        logger.info(f"Discovered {len(certManagerNamespaces)} Certificate Manager namespace(s): {', '.join(sorted(certManagerNamespaces))}")

        for ns in sorted(certManagerNamespaces):
            tasks = generateNamespaceCollectionTasks(
                dynClient=dynClient,
                namespace=ns,
                outputDir=outputDir,
                noLogs=noLogs,
                customResources=CERT_MANAGER_NAMESPACE_RESOURCES,
                ibmCRDs=ibmCRDs,
            )
            plan.addGroup(f"Certificate Manager ({ns})", tasks)
            logger.debug(f"Added {len(tasks)} Certificate Manager collection tasks for namespace {ns}")

        # Collect workload namespace resources across all namespaces in a single group.
        # namespace=None routes output to resources/_cluster/ which is correct since the
        # data spans all namespaces rather than a single one.
        allNsTasks = [
            (
                f"cert_{kind.lower()}",
                collectResources,
                None,
                apiVersion,
                kind,
                outputDir,
                True,  # allNamespaces
            )
            for apiVersion, kind in CERT_MANAGER_ALL_NAMESPACE_RESOURCES
        ]
        plan.addGroup("Certificate Manager (all namespaces)", allNsTasks)
        logger.debug(f"Added {len(allNsTasks)} all-namespace Certificate Manager collection tasks")
    else:
        logger.info("No Certificate Manager namespaces discovered")
