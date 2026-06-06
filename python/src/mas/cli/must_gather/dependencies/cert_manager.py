# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Red Hat Certificate Manager dependency collector."""

import logging
from kubernetes.dynamic import DynamicClient
from .utils import checkNamespaceExists

logger = logging.getLogger(__name__)

# Cert-manager specific custom resources to collect (apiVersion, kind)
CERT_MANAGER_RESOURCES = [
    ("cert-manager.io/v1", "CertificateRequest"),
    ("cert-manager.io/v1", "Certificate"),
    ("acme.cert-manager.io/v1", "Challenge"),
    ("cert-manager.io/v1", "ClusterIssuer"),
    ("cert-manager.io/v1", "Issuer"),
    ("acme.cert-manager.io/v1", "Order"),
    ("operator.openshift.io/v1alpha1", "CertManager"),
]


def collectCertManager(dynClient: DynamicClient, outputDir: str, noDetail: bool = False, genericMustGather=None) -> bool:
    """Collect Red Hat Certificate Manager resources.

    Checks for cert-manager-operator and cert-manager namespaces and collects
    cert-manager specific resources.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.
        genericMustGather (callable, optional): Function to perform generic must-gather collection. Defaults to None.

    Returns:
        bool: True if collection succeeded, False if namespaces not found or errors occurred
    """
    try:
        success = False
        namespaceCount = 0

        # Check and collect from cert-manager-operator namespace
        if checkNamespaceExists(dynClient, "cert-manager-operator"):
            logger.info("Collecting from cert-manager-operator namespace")
            namespaceCount += 1
            if genericMustGather:
                if genericMustGather(namespace="cert-manager-operator", outputDir=outputDir, noDetail=noDetail, additionalResources=CERT_MANAGER_RESOURCES):
                    success = True
        else:
            logger.info("cert-manager-operator namespace not found")

        # Check and collect from cert-manager namespace
        if checkNamespaceExists(dynClient, "cert-manager"):
            logger.info("Collecting from cert-manager namespace")
            namespaceCount += 1
            if genericMustGather:
                if genericMustGather(namespace="cert-manager", outputDir=outputDir, noDetail=noDetail):
                    success = True
        else:
            logger.info("cert-manager namespace not found")

        if namespaceCount == 0:
            logger.info("No Certificate Manager namespaces found, skipping collection")
            print("⏭️  Red Hat Certificate Manager skipped - no cert-manager namespaces found")

        return success

    except Exception as e:
        logger.warning(f"Error collecting Certificate Manager: {e}")
        print(f"❌ Red Hat Certificate Manager - {e}")
        return False


# Made with Bob
