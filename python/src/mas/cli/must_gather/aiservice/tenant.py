# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""AI Service tenant discovery and collection."""

import logging
from typing import List, Optional

from kubernetes.dynamic import DynamicClient

logger = logging.getLogger(__name__)


def discoverAIServiceTenants(dynClient: DynamicClient, instanceId: str, tenantIds: Optional[str] = None) -> List[str]:
    """Discover AI Service tenants for a specific instance.

    Discovers tenants by checking for AIServiceTenant CRs in the instance namespace.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client
        instanceId (str): AI Service instance ID
        tenantIds (str, optional): Comma-separated list of tenant IDs to filter. Defaults to None.

    Returns:
        List[str]: List of AI Service tenant IDs
    """
    tenants = []
    namespace = f"aiservice-{instanceId}"

    try:
        api = dynClient.resources.get(api_version="aiservice.ibm.com/v1", kind="AIServiceTenant")
        aiserviceTenants = api.get(namespace=namespace)

        for tenantCr in aiserviceTenants.items:
            tenantId = tenantCr.metadata.name
            if tenantId not in tenants:
                tenants.append(tenantId)

        logger.info(f"Discovered {len(tenants)} AI Service tenants in namespace {namespace}")

    except Exception as e:
        logger.debug(f"Could not discover AI Service tenants in {namespace}: {e}")

    # Filter by tenant IDs if provided
    if tenantIds:
        filterList = [id.strip() for id in tenantIds.split(",")]
        tenants = [t for t in tenants if t in filterList]
        logger.info(f"Filtered to {len(tenants)} AI Service tenants based on --aiservice-tenant-ids")

    return sorted(tenants)
