"""AI Service tenant discovery and collection."""

import logging
import os
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


def collectAIServiceTenant(dynClient: DynamicClient, instanceId: str, tenantId: str, namespace: str, outputDir: str) -> bool:
    """Collect resources for an AI Service tenant.

    Collects InferenceService resources associated with the tenant.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client
        instanceId (str): AI Service instance ID
        tenantId (str): AI Service tenant ID
        namespace (str): AI Service instance namespace
        outputDir (str): Base output directory for must-gather

    Returns:
        bool: True if collection succeeded, False otherwise
    """
    outputSubDir = f"aiservice/{instanceId}/tenants/{tenantId}"
    tenantOutputDir = os.path.join(outputDir, outputSubDir)

    logger.info(f"Collecting AI Service tenant: {tenantId} from namespace: {namespace}")

    # Create output directory
    os.makedirs(tenantOutputDir, exist_ok=True)

    # Collect InferenceService resources for this tenant
    try:
        api = dynClient.resources.get(api_version="serving.kserve.io/v1beta1", kind="InferenceService")
        inferenceServices = api.get(namespace=namespace, label_selector=f"aiservice.ibm.com/tenant={tenantId}")

        if inferenceServices.items:
            # Write InferenceService resources to file
            inferenceServiceFile = os.path.join(tenantOutputDir, "inferenceservices.yaml")
            with open(inferenceServiceFile, "w") as f:
                for svc in inferenceServices.items:
                    f.write("---\n")
                    f.write(str(svc.to_dict()))
                    f.write("\n")

            logger.debug(f"Collected {len(inferenceServices.items)} InferenceService resources for tenant {tenantId}")
        else:
            logger.debug(f"No InferenceService resources found for tenant {tenantId}")

    except Exception as e:
        logger.warning(f"Failed to collect InferenceService resources for tenant {tenantId}: {e}")

    return True


# Made with Bob
