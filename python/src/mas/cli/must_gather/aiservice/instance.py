"""AI Service instance discovery and collection."""

import logging
import os
import subprocess
from typing import List, Optional, Callable

from kubernetes.dynamic import DynamicClient

logger = logging.getLogger(__name__)


def discoverAIServiceInstances(dynClient: DynamicClient, instanceIds: Optional[str] = None) -> List[str]:
    """Discover AI Service instances in the cluster.

    Discovers AI Service instances by checking for AIServiceApp CRs across all namespaces.
    If no CRs are found, falls back to discovering from aiservice-* namespace names.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client
        instanceIds (str, optional): Comma-separated list of instance IDs to filter. Defaults to None.

    Returns:
        List[str]: List of AI Service instance IDs
    """
    instances = []

    # Try to discover from AIServiceApp CRs first
    try:
        api = dynClient.resources.get(api_version="aiservice.ibm.com/v1", kind="AIServiceApp")
        aiserviceApps = api.get()

        for app in aiserviceApps.items:
            namespace = app.metadata.namespace
            if namespace.startswith("aiservice-"):
                instanceId = namespace[len("aiservice-") :]
                if instanceId not in instances:
                    instances.append(instanceId)

        logger.info(f"Discovered {len(instances)} AI Service instances from AIServiceApp CRs")

    except Exception as e:
        logger.debug(f"Could not discover AI Service instances from CRs: {e}")

        # Fall back to discovering from namespace names
        try:
            nsApi = dynClient.resources.get(api_version="v1", kind="Namespace")
            namespaces = nsApi.get()

            for ns in namespaces.items:
                nsName = ns.metadata.name
                if nsName.startswith("aiservice-") and not nsName.endswith("-pipelines"):
                    instanceId = nsName[len("aiservice-") :]
                    if instanceId not in instances:
                        instances.append(instanceId)

            logger.info(f"Discovered {len(instances)} AI Service instances from namespaces")

        except Exception as e2:
            logger.warning(f"Could not discover AI Service instances from namespaces: {e2}")

    # Filter by instance IDs if provided
    if instanceIds:
        filterList = [id.strip() for id in instanceIds.split(",")]
        instances = [inst for inst in instances if inst in filterList]
        logger.info(f"Filtered to {len(instances)} AI Service instances based on --aiservice-instance-ids")

    return sorted(instances)


def collectAIServiceInstance(dynClient: DynamicClient, instanceId: str, outputDir: str, genericMustGather: Optional[Callable] = None) -> bool:
    """Collect resources from an AI Service instance namespace.

    Calls mg-summary-aiservice and mg-collect-aiservice scripts for the instance,
    then uses genericMustGather to collect standard resources.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client
        instanceId (str): AI Service instance ID
        outputDir (str): Base output directory for must-gather
        genericMustGather (Callable, optional): Function to call for generic resource collection. Defaults to None.

    Returns:
        bool: True if collection succeeded, False otherwise
    """
    namespace = f"aiservice-{instanceId}"
    outputSubDir = f"aiservice/{instanceId}"
    instanceOutputDir = os.path.join(outputDir, outputSubDir)

    logger.info(f"Collecting AI Service instance: {instanceId} from namespace: {namespace}")

    # Create output directory
    os.makedirs(instanceOutputDir, exist_ok=True)

    # Call mg-summary-aiservice script
    summaryFile = os.path.join(instanceOutputDir, "aiservice-summary.txt")
    try:
        with open(summaryFile, "w") as f:
            subprocess.run(["mg-summary-aiservice", namespace], stdout=f, stderr=subprocess.STDOUT, check=False, timeout=300)
        logger.debug(f"Generated AI Service summary for {instanceId}")
    except Exception as e:
        logger.warning(f"Failed to generate AI Service summary for {instanceId}: {e}")

    # Call mg-collect-aiservice script
    try:
        subprocess.run(["mg-collect-aiservice", namespace, instanceOutputDir], check=False, timeout=600)
        logger.debug(f"Collected AI Service resources for {instanceId}")
    except Exception as e:
        logger.warning(f"Failed to collect AI Service resources for {instanceId}: {e}")

    # Use genericMustGather for standard resource collection
    if genericMustGather:
        try:
            genericMustGather(namespace=namespace, outputSubDir=outputSubDir)
            logger.debug(f"Collected generic resources for AI Service instance {instanceId}")
        except Exception as e:
            logger.warning(f"Failed to collect generic resources for AI Service instance {instanceId}: {e}")

    return True
