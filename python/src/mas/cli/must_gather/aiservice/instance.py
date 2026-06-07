"""AI Service instance discovery and collection."""

import logging
import os
from typing import List, Optional, Callable

from kubernetes.dynamic import DynamicClient

from mas.cli.must_gather.common import collectReconcileLogsParallel

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


def _generateAIServiceSummary(dynClient: DynamicClient, namespace: str, outputFile: str) -> None:
    """Generate AI Service summary for a namespace.

    Collects AIServiceApp and AIServiceTenant resources and writes them to a summary file.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client
        namespace (str): Namespace to collect from
        outputFile (str): Path to output summary file
    """
    try:
        with open(outputFile, "w") as f:
            # AIServiceApp resources
            f.write("IBM Maximo AI Service Application\n")
            f.write("-" * 80 + "\n")
            try:
                api = dynClient.resources.get(api_version="aiservice.ibm.com/v1", kind="AIServiceApp")
                apps = api.get(namespace=namespace)
                if apps.items:
                    for app in apps.items:
                        f.write(f"Name: {app.metadata.name}\n")
                        f.write(f"Namespace: {app.metadata.namespace}\n")
                        if hasattr(app, "status") and app.status:
                            f.write(f"Status: {app.status}\n")
                        f.write("\n")
                else:
                    f.write("No AIServiceApp resources found\n\n")
            except Exception as e:
                f.write(f"Error collecting AIServiceApp: {e}\n\n")

            # AIServiceTenant resources
            f.write("IBM Maximo AI Service - AI Service Tenant Configuration\n")
            f.write("-" * 80 + "\n")
            try:
                api = dynClient.resources.get(api_version="aiservice.ibm.com/v1", kind="AIServiceTenant")
                tenants = api.get(namespace=namespace)
                if tenants.items:
                    for tenant in tenants.items:
                        f.write(f"Name: {tenant.metadata.name}\n")
                        f.write(f"Namespace: {tenant.metadata.namespace}\n")
                        if hasattr(tenant, "status") and tenant.status:
                            f.write(f"Status: {tenant.status}\n")
                        f.write("\n")
                else:
                    f.write("No AIServiceTenant resources found\n\n")
            except Exception as e:
                f.write(f"Error collecting AIServiceTenant: {e}\n\n")

        logger.debug(f"Generated AI Service summary: {outputFile}")
    except Exception as e:
        logger.warning(f"Failed to generate AI Service summary: {e}")


def collectAIServiceInstance(dynClient: DynamicClient, instanceId: str, outputDir: str, genericMustGather: Optional[Callable] = None) -> bool:
    """Collect resources from an AI Service instance namespace.

    Collects AI Service summary, reconcile logs, and standard resources using Python Kubernetes client.

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

    # Generate AI Service summary
    summaryFile = os.path.join(instanceOutputDir, "aiservice-summary.txt")
    _generateAIServiceSummary(dynClient, namespace, summaryFile)

    # Collect reconcile logs from AI Service operators
    # Note: mg-collect-aiservice only collected reconcile logs, which is now handled here
    operators = [
        (namespace, "control-plane", "ibm-aiservice"),
        (namespace, "aiservice.ibm.com/appType", "entitymgr-tenant-operator"),
        (namespace, "operator", "ibm-truststore-mgr"),
    ]

    logger.info(f"Collecting reconcile logs from {len(operators)} operators")

    def progressCallback(completed: int, total: int) -> None:
        logger.info(f"Collecting reconcile logs: {completed}/{total} operators completed")

    collectReconcileLogsParallel(dynClient, operators, outputDir, progressCallback=progressCallback)

    # Use genericMustGather for standard resource collection
    if genericMustGather:
        try:
            genericMustGather(namespace=namespace, outputSubDir=outputSubDir)
            logger.debug(f"Collected generic resources for AI Service instance {instanceId}")
        except Exception as e:
            logger.warning(f"Failed to collect generic resources for AI Service instance {instanceId}: {e}")

    return True
