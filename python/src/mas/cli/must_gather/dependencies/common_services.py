# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""IBM Common Services dependency collector."""

import logging
from kubernetes.dynamic import DynamicClient
from kubernetes.client.exceptions import ApiException

logger = logging.getLogger(__name__)


def collectCommonServices(dynClient: DynamicClient, outputDir: str, noDetail: bool = False, genericMustGather=None) -> bool:
    """Collect IBM Common Services resources.

    Checks if ibm-common-services namespace exists and collects resources from it.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.
        genericMustGather (callable, optional): Function to perform generic must-gather collection. Defaults to None.

    Returns:
        bool: True if collection succeeded, False if namespace not found or errors occurred
    """
    try:
        # Check if ibm-common-services namespace exists
        namespaceApi = dynClient.resources.get(kind="Namespace")
        namespaceApi.get(name="ibm-common-services")

        # Collect resources from the namespace if genericMustGather is provided
        if genericMustGather:
            result = genericMustGather(namespace="ibm-common-services", outputDir=outputDir, noDetail=noDetail)
            if result:
                print("✅ IBM CloudPak Foundation Services collected")
            else:
                print("❌ IBM CloudPak Foundation Services collection encountered errors (check logs)")
            return result
        return True

    except ApiException as e:
        if e.status == 404:
            logger.info("ibm-common-services namespace not found, skipping collection")
            print("⏭️  IBM CloudPak Foundation Services skipped - namespace does not exist")
            return False
        logger.warning(f"Error collecting IBM Common Services: {e}")
        print(f"❌ IBM CloudPak Foundation Services - {e}")
        return False
    except Exception as e:
        logger.warning(f"Error collecting IBM Common Services: {e}")
        print(f"❌ IBM CloudPak Foundation Services - {e}")
        return False
