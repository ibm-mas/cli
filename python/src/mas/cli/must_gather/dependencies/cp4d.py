# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""IBM CloudPak for Data dependency collector."""

import logging
from kubernetes.dynamic import DynamicClient
from kubernetes.client.exceptions import ApiException

logger = logging.getLogger(__name__)


def collectCP4D(dynClient: DynamicClient, outputDir: str, noDetail: bool = False, genericMustGather=None) -> bool:
    """Collect IBM CloudPak for Data resources.

    Checks if ibm-cpd-operators namespace exists and collects resources from
    ibm-cpd and ibm-cpd-operators namespaces.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.
        genericMustGather (callable, optional): Function to perform generic must-gather collection. Defaults to None.

    Returns:
        bool: True if collection succeeded, False if namespace not found or errors occurred
    """
    try:
        # Check if ibm-cpd-operators namespace exists
        namespaceApi = dynClient.resources.get(kind="Namespace")
        namespaceApi.get(name="ibm-cpd-operators")

        # Collect resources from both namespaces if genericMustGather is provided
        if genericMustGather:
            success = True
            # Collect from ibm-cpd namespace
            if not genericMustGather(namespace="ibm-cpd", outputDir=outputDir, noDetail=noDetail):
                success = False

            # Collect from ibm-cpd-operators namespace
            if not genericMustGather(namespace="ibm-cpd-operators", outputDir=outputDir, noDetail=noDetail):
                success = False

            if success:
                print("✅ IBM CloudPak for Data collected from 2 namespaces")
            else:
                print("❌ IBM CloudPak for Data collection encountered errors (check logs)")
            return success
        return True

    except ApiException as e:
        if e.status == 404:
            logger.info("ibm-cpd-operators namespace not found, skipping CP4D collection")
            print("⏭️  IBM CloudPak for Data skipped - namespace does not exist")
            return False
        logger.warning(f"Error collecting IBM CloudPak for Data: {e}")
        print(f"❌ IBM CloudPak for Data - {e}")
        return False
    except Exception as e:
        logger.warning(f"Error collecting IBM CloudPak for Data: {e}")
        print(f"❌ IBM CloudPak for Data - {e}")
        return False


# Made with Bob
