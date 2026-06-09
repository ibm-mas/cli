"""AI Service pipelines collection."""

import logging
from typing import List, Optional

from kubernetes.dynamic import DynamicClient

logger = logging.getLogger(__name__)


def discoverAIServicePipelineNamespaces(dynClient: DynamicClient, instanceIds: Optional[List[str]] = None) -> List[str]:
    """Discover AI Service pipeline namespaces in the cluster.

    Discovers pipeline namespaces matching the pattern aiservice-{instance}-pipelines.
    Optionally filters by instance IDs.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client
        instanceIds (List[str], optional): List of instance IDs to filter. Defaults to None.

    Returns:
        List[str]: List of AI Service pipeline namespace names
    """
    namespaces = []

    try:
        nsApi = dynClient.resources.get(api_version="v1", kind="Namespace")
        allNamespaces = nsApi.get()

        for ns in allNamespaces.items:
            nsName = ns.metadata.name
            if nsName.startswith("aiservice-") and nsName.endswith("-pipelines"):
                # Extract instance ID from namespace name
                # Format: aiservice-{instance}-pipelines
                instanceId = nsName[len("aiservice-") : -len("-pipelines")]

                # Filter by instance IDs if provided
                if instanceIds is None or instanceId in instanceIds:
                    namespaces.append(nsName)

        logger.info(f"Discovered {len(namespaces)} AI Service pipeline namespaces")

    except Exception as e:
        logger.warning(f"Could not discover AI Service pipeline namespaces: {e}")

    return sorted(namespaces)
