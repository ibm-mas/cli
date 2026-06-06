# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""IBM Suite License Service dependency collector."""

import logging
from kubernetes.dynamic import DynamicClient

from ..sls.license_service import collectSLSNamespace
from .utils import discoverNamespacesFromCR

logger = logging.getLogger(__name__)


def collectSLS(dynClient: DynamicClient, outputDir: str, noDetail: bool = False, genericMustGather=None) -> bool:
    """Collect IBM Suite License Service resources.

    Discovers SLS namespace from LicenseService CRs and collects SLS resources.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.
        genericMustGather (callable, optional): Function to perform generic must-gather collection. Defaults to None.

    Returns:
        bool: True if collection succeeded, False if no SLS found or errors occurred
    """
    try:
        # Discover SLS namespaces from LicenseService CRs
        slsNamespaces = discoverNamespacesFromCR(dynClient=dynClient, kind="LicenseService")

        if not slsNamespaces:
            logger.info("No SLS namespaces found, skipping collection")
            return False

        # Collect from discovered namespaces directly to avoid duplicating the resources path
        success = True
        for namespace in slsNamespaces:
            if not collectSLSNamespace(dynClient=dynClient, namespace=namespace, outputDir=outputDir, noDetail=noDetail):
                success = False

        return success

    except Exception as e:
        logger.warning(f"Error collecting IBM Suite License Service: {e}")
        return False
