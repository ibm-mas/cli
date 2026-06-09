"""AI Service instance discovery and collection."""

import logging
from typing import List, Optional

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


def addAIServiceToCollectionPlan(plan, dynClient: DynamicClient, outputDir: str, noLogs: bool, ibmCRDs: list):
    """Add AI Service collection tasks to the collection plan.

    Discovers AI Service instances and for each instance, adds collection groups for:
    - The instance namespace (mas-{instance}-aiservice)
    - Tenant namespaces (mas-{instance}-aiservice-{tenant})
    - Pipeline namespaces (aiservice-{instance}-pipelines)

    Args:
        plan (CollectionPlan): Collection plan to add tasks to
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noLogs (bool): If True, skip pod log collection
        ibmCRDs (list): List of IBM CRD information for collection
    """
    from mas.cli.must_gather.common.task_generation import generateNamespaceCollectionTasks
    from mas.cli.must_gather.aiservice import tenant as aiservice_tenant
    from mas.cli.must_gather.aiservice import pipelines as aiservice_pipelines

    logger.info("Discovering AI Service instances")
    try:
        instanceIds = discoverAIServiceInstances(dynClient)
        if instanceIds:
            logger.info(f"Discovered {len(instanceIds)} AI Service instance(s): {', '.join(sorted(instanceIds))}")
            for instanceId in sorted(instanceIds):
                # Generate tasks for AI Service instance namespace
                instanceNamespace = f"mas-{instanceId}-aiservice"
                tasks = generateNamespaceCollectionTasks(
                    dynClient=dynClient,
                    namespace=instanceNamespace,
                    outputDir=outputDir,
                    noLogs=noLogs,
                    secretData=False,
                    customResources=None,
                    ibmCRDs=ibmCRDs,
                )
                plan.addGroup(f"AI Service Instance ({instanceId})", tasks)
                logger.debug(f"Added {len(tasks)} AI Service instance collection tasks for {instanceId}")

                # Discover tenants for this instance
                logger.debug(f"Discovering AI Service tenants for instance {instanceId}")
                try:
                    tenantIds = aiservice_tenant.discoverAIServiceTenants(dynClient, instanceId=instanceId)
                    if tenantIds:
                        logger.info(f"Discovered {len(tenantIds)} AI Service tenant(s) for instance {instanceId}: {', '.join(sorted(tenantIds))}")
                        for tenantId in sorted(tenantIds):
                            tenantNamespace = f"mas-{instanceId}-aiservice-{tenantId}"
                            # Generate tasks for AI Service tenant namespace
                            tasks = generateNamespaceCollectionTasks(
                                dynClient=dynClient,
                                namespace=tenantNamespace,
                                outputDir=outputDir,
                                noLogs=noLogs,
                                secretData=False,
                                customResources=None,
                                ibmCRDs=ibmCRDs,
                            )
                            plan.addGroup(f"AI Service Tenant ({instanceId}/{tenantId})", tasks)
                            logger.debug(f"Added {len(tasks)} AI Service tenant collection tasks for {instanceId}/{tenantId}")
                    else:
                        logger.info(f"No AI Service tenants discovered for instance {instanceId}")
                except Exception as e:
                    logger.warning(f"AI Service Tenants discovery failed for {instanceId}: {e}")

                # Discover pipelines for this instance
                logger.debug(f"Discovering AI Service pipelines for instance {instanceId}")
                try:
                    pipelineNamespaces = aiservice_pipelines.discoverAIServicePipelineNamespaces(dynClient, instanceIds=[instanceId])
                    if pipelineNamespaces:
                        logger.info(
                            f"Discovered {len(pipelineNamespaces)} AI Service pipeline namespace(s) for instance {instanceId}: {', '.join(sorted(pipelineNamespaces))}"
                        )
                        for pipelineNamespace in sorted(pipelineNamespaces):
                            # Generate tasks for AI Service pipelines namespace
                            tasks = generateNamespaceCollectionTasks(
                                dynClient=dynClient,
                                namespace=pipelineNamespace,
                                outputDir=outputDir,
                                noLogs=noLogs,
                                secretData=False,
                                customResources=None,
                                ibmCRDs=ibmCRDs,
                            )
                            plan.addGroup(f"AI Service Pipelines ({pipelineNamespace})", tasks)
                            logger.debug(f"Added {len(tasks)} AI Service pipelines collection tasks for {pipelineNamespace}")
                    else:
                        logger.info(f"No AI Service pipeline namespaces discovered for instance {instanceId}")
                except Exception as e:
                    logger.warning(f"AI Service Pipelines discovery failed for {instanceId}: {e}")
        else:
            logger.info("No AI Service instances discovered")
    except Exception as e:
        logger.warning(f"AI Service discovery failed: {e}")
