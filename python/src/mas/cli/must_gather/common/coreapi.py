# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""MAS Core API authentication utilities for must-gather."""

import base64
import logging
from typing import Optional

import requests
import urllib3
from kubernetes.dynamic import DynamicClient

# Disable SSL warnings for must-gather operations
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


def getAuthToken(dynClient: DynamicClient, instanceId: str) -> Optional[str]:
    """Get authentication token for MAS Core API.

    Retrieves superuser credentials from the secret and authenticates
    with the MAS admin dashboard to obtain an auth token.

    Args:
        dynClient (DynamicClient): OpenShift Dynamic Client
        instanceId (str): MAS instance ID

    Returns:
        str: Authentication token for API requests, or None if authentication fails

    Raises:
        Exception: If credentials cannot be retrieved or authentication fails
    """
    coreNamespace = f"mas-{instanceId}-core"

    try:
        # Get superuser credentials from secret
        secretResource = dynClient.resources.get(api_version="v1", kind="Secret")
        secretName = f"{instanceId}-credentials-superuser"

        logger.debug(f"Retrieving secret {secretName} from namespace {coreNamespace}")
        superuserSecret = secretResource.get(name=secretName, namespace=coreNamespace)

        # Extract and decode credentials
        username = base64.b64decode(superuserSecret.data.get("username")).decode("utf-8")
        password = base64.b64decode(superuserSecret.data.get("password")).decode("utf-8")

        if not username or not password:
            logger.error(f"Username or password not found in secret {secretName}")
            return None

        # Get admin route URL
        routeResource = dynClient.resources.get(api_version="route.openshift.io/v1", kind="Route")
        adminRoute = routeResource.get(name=f"{instanceId}-admin", namespace=coreNamespace)
        adminHost = adminRoute.spec.host

        # Login to MAS admin dashboard
        loginUrl = f"https://{adminHost}/logininitial"
        loginPayload = {"username": username, "password": password}

        logger.debug(f"Authenticating to {loginUrl}")
        response = requests.post(loginUrl, json=loginPayload, verify=False, timeout=30)
        response.raise_for_status()

        authToken = response.json().get("token")
        if not authToken:
            logger.error("No token returned from authentication endpoint")
            return None

        logger.debug("Successfully obtained auth token")
        return authToken

    except Exception as e:
        logger.error(f"Failed to get auth token for instance {instanceId}: {e}")
        return None
