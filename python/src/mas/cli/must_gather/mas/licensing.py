# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""MAS Licensing collector for must-gather.

This module collects licensing information from MAS Core API endpoints
including entitlement configuration, tokens, peaks, and usage reports.
"""

import json
import logging
import os
from typing import Optional

import requests
import urllib3
from kubernetes.dynamic import DynamicClient

from mas.cli.must_gather.common.coreapi import getAuthToken
from mas.cli.must_gather.common.thread_safe_client import createThreadLocalDynamicClient

# Disable SSL warnings for must-gather operations
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


def _getApiRoute(dynClient: DynamicClient, instanceId: str) -> Optional[str]:
    """Get the API route host for a MAS instance.

    Args:
        dynClient (DynamicClient): OpenShift Dynamic Client
        instanceId (str): MAS instance ID

    Returns:
        str: API route host, or None if not found
    """
    coreNamespace = f"mas-{instanceId}-core"

    try:
        routeResource = dynClient.resources.get(api_version="route.openshift.io/v1", kind="Route")
        apiRoute = routeResource.get(name=f"{instanceId}-api", namespace=coreNamespace)
        return apiRoute.spec.host
    except Exception as e:
        logger.error(f"Failed to get API route for instance {instanceId}: {e}")
        return None


def _fetchLicensingData(apiHost: str, authToken: str, endpoint: str) -> Optional[dict]:
    """Fetch data from a licensing API endpoint.

    Args:
        apiHost (str): API route host
        authToken (str): Authentication token
        endpoint (str): API endpoint path (e.g., "licensing/licenses")

    Returns:
        dict: JSON response data, or None if request fails
    """
    url = f"https://{apiHost}/{endpoint}"
    headers = {"x-access-token": authToken}

    try:
        logger.debug(f"Fetching licensing data from {url}")
        response = requests.get(url, headers=headers, verify=False, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.warning(f"Failed to fetch data from {endpoint}: {e}")
        return None


def collectLicensingInfo(dynClient: DynamicClient, namespace: str, outputDir: str) -> bool:
    """Collect licensing information from MAS Core API.

    Collects licensing data from multiple API endpoints and saves them
    to individual JSON files in the licensing directory.

    Args:
        dynClient (DynamicClient): OpenShift Dynamic Client (unused, thread-local client created internally)
        namespace (str): MAS Core namespace
        outputDir (str): Base output directory

    Returns:
        bool: True if collection succeeded, False otherwise
    """
    instanceId = namespace[4:-5]  # Remove "mas-" prefix and "-core" suffix
    logger.info(f"Starting licensing info collection for instance {instanceId}")

    try:
        # Create thread-local client for thread-safety
        threadLocalClient = createThreadLocalDynamicClient()

        # Get authentication token
        authToken = getAuthToken(threadLocalClient, instanceId)
        if not authToken:
            logger.warning(f"Failed to get auth token for instance {instanceId} - skipping licensing collection")
            return True

        # Get API route
        apiHost = _getApiRoute(threadLocalClient, instanceId)
        if not apiHost:
            logger.warning(f"Failed to get API route for instance {instanceId} - skipping licensing collection")
            return True

        # Create output directory
        licensingDir = os.path.join(outputDir, "licensing", instanceId)
        os.makedirs(licensingDir, exist_ok=True)
        logger.debug(f"Created licensing directory: {licensingDir}")

        # Define endpoints to collect
        endpoints = {
            "tokens.json": "licensing/tokens",
            "config.json": "licensing/config",
        }

        # Collect reports in subdirectory
        reportEndpoints = {
            "license-usage.json": "licensing/reports/licenseUsage",
            "token-usage.json": "licensing/reports/tokenUsage",
        }

        # Collect main endpoints
        successCount = 0
        for filename, endpoint in endpoints.items():
            data = _fetchLicensingData(apiHost, authToken, endpoint)
            if data is not None:
                outputPath = os.path.join(licensingDir, filename)
                with open(outputPath, "w") as f:
                    json.dump(data, f, indent=2)
                logger.debug(f"✅ Saved {filename}")
                successCount += 1
            else:
                logger.debug(f"⚠️  Failed to collect {filename}")

        # Collect report endpoints (save directly in licensing directory)
        for filename, endpoint in reportEndpoints.items():
            data = _fetchLicensingData(apiHost, authToken, endpoint)
            if data is not None:
                outputPath = os.path.join(licensingDir, filename)
                with open(outputPath, "w") as f:
                    json.dump(data, f, indent=2)
                logger.debug(f"✅ Saved {filename}")
                successCount += 1
            else:
                logger.debug(f"⚠️  Failed to collect {filename}")

        if successCount > 0:
            logger.info(f"✅ Licensing information collected ({successCount}/{len(endpoints) + len(reportEndpoints)} endpoints)")
        else:
            logger.warning(f"⚠️  No licensing data collected for instance {instanceId}")

        return True

    except Exception as e:
        logger.error(f"❌ Error collecting licensing information for {instanceId}: {e}", exc_info=True)
        return True  # Don't fail collection if licensing info can't be collected
