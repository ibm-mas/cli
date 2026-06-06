"""AI Service pipelines collection."""

import logging
from typing import List, Optional, Callable

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


def collectAIServicePipelines(dynClient: DynamicClient, namespace: str, outputDir: str, genericMustGather: Optional[Callable] = None) -> bool:
    """Collect resources from an AI Service pipeline namespace.

    Uses genericMustGather to collect standard resources from the pipeline namespace.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client
        namespace (str): Pipeline namespace name (e.g., aiservice-inst1-pipelines)
        outputDir (str): Base output directory for must-gather
        genericMustGather (Callable, optional): Function to call for generic resource collection. Defaults to None.

    Returns:
        bool: True if collection succeeded, False otherwise
    """
    # Extract instance ID from namespace name
    # Format: aiservice-{instance}-pipelines
    if namespace.startswith("aiservice-") and namespace.endswith("-pipelines"):
        instanceId = namespace[len("aiservice-") : -len("-pipelines")]
        outputSubDir = f"aiservice/{instanceId}/pipelines"
    else:
        logger.warning(f"Unexpected pipeline namespace format: {namespace}")
        outputSubDir = f"aiservice/pipelines/{namespace}"

    logger.info(f"Collecting AI Service pipelines from namespace: {namespace}")

    # Use genericMustGather for resource collection
    if genericMustGather:
        try:
            genericMustGather(namespace=namespace, outputSubDir=outputSubDir)
            logger.debug(f"Collected pipeline resources from {namespace}")
        except Exception as e:
            logger.warning(f"Failed to collect pipeline resources from {namespace}: {e}")

    return True


# Made with Bob
