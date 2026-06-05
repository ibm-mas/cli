# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Generic resource collection utilities for must-gather."""

import os
import yaml
import logging
from typing import Optional
from kubernetes.dynamic import DynamicClient

logger = logging.getLogger(__name__)


def _pluralizeKind(kind: str) -> str:
    """Convert Kind name to plural form for file naming.

    Args:
        kind (str): Kubernetes Kind name (e.g., "Pod", "StorageClass")

    Returns:
        str: Pluralized lowercase name (e.g., "pods", "storageclasses")
    """
    kind = kind.lower()

    # Special cases
    specialCases = {
        "storageclass": "storageclasses",
        "clusterversion": "clusterversions",
        "namespace": "namespaces",
        "packagemanifest": "packagemanifests",
        "clusterrole": "clusterroles",
        "clusterrolebinding": "clusterrolebindings",
        "imagecontentsourcepolicy": "imagecontentsourcepolicy",  # Already plural-like
        "imagedigestmirrorset": "imagedigestmirrorset",  # Already plural-like
        "imagetagmirrorset": "imagetagmirrorset",  # Already plural-like
        "machineconfig": "machineconfig",  # Already plural-like
        "machineconfigpool": "machineconfigpool",  # Already plural-like
        "catalogsource": "catalogsources",
        "subscription": "subscriptions",
        "installplan": "installplans",
        "operatorcondition": "operatorconditions",
        "objectbucket": "objectbucket",  # Already plural-like
        "objectbucketclaim": "objectbucketclaim",  # Already plural-like
        "objectstoragecfg": "objectstoragecfg",  # Already plural-like
        "job": "jobs",
        "node": "nodes",
    }

    if kind in specialCases:
        return specialCases[kind]

    # Default: add 's' to the end
    return kind + "s"


def collectResources(
    dynClient: DynamicClient,
    namespace: Optional[str],
    apiVersion: str,
    kind: str,
    outputDir: str,
    noDetail: bool = False,
    describe: bool = False,
    allNamespaces: bool = False,
) -> bool:
    """Collect Kubernetes resources of a specific type.

    Collects resources and generates both summary (wide output) and detailed YAML files.
    Supports namespace-scoped and cluster-scoped resources, with options for describe
    output and all-namespaces collection.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        namespace (str, optional): Target namespace for collection. Use None for cluster-scoped resources. Defaults to None.
        apiVersion (str): API version of the resource (e.g., "v1", "storage.k8s.io/v1")
        kind (str): Kind of resource to collect (e.g., "Pod", "StorageClass")
        outputDir (str): Base output directory for collected resources
        noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.
        describe (bool, optional): If True, generate describe output (.txt) for each resource. Defaults to False.
        allNamespaces (bool, optional): If True, collect resources across all namespaces. Defaults to False.

    Returns:
        bool: True if collection succeeded, False if errors occurred
    """
    namespaceContext = namespace if namespace else "_cluster"

    try:
        # Convert kind to plural lowercase for file naming consistency
        resourceType = _pluralizeKind(kind)

        # Determine namespace directory
        if namespace:
            namespaceDir = os.path.join(outputDir, namespace)
        else:
            namespaceDir = os.path.join(outputDir, "_cluster")

        os.makedirs(namespaceDir, exist_ok=True)

        # Get API resource
        api = dynClient.resources.get(api_version=apiVersion, kind=kind)

        # Collect resources
        if allNamespaces:
            resources = api.get()
        elif namespace:
            resources = api.get(namespace=namespace)
        else:
            resources = api.get()

        # Log result based on resource count
        resourceCount = len(resources.items) if resources.items else 0
        if resourceCount == 0:
            logger.info(f"{namespaceContext}: {kind} ({apiVersion}) - No resources to collect")
            return True

        logger.info(f"{namespaceContext}: {kind} ({apiVersion}) - Successfully collected {resourceCount} resource{'s' if resourceCount != 1 else ''}")

        # Generate summary file (wide output)
        summaryFile = os.path.join(namespaceDir, f"{resourceType}.txt")
        _writeSummary(resources, summaryFile)

        # Generate detailed reports if requested
        if not noDetail:
            resourceDir = os.path.join(namespaceDir, resourceType)
            os.makedirs(resourceDir, exist_ok=True)

            if allNamespaces:
                # For all-namespaces, write single YAML file
                allNamespacesFile = os.path.join(resourceDir, "all-namespaces.yaml")
                _writeYaml(resources.to_dict(), allNamespacesFile)
            else:
                # Write individual resource files
                for resource in resources.items:
                    resourceName = resource.metadata.name
                    # Sanitize resource name (replace colons with underscores)
                    sanitizedName = resourceName.replace(":", "_")

                    # Write YAML file
                    yamlFile = os.path.join(resourceDir, f"{sanitizedName}.yaml")
                    _writeYaml(resource.to_dict(), yamlFile)

                    # Write describe file if requested
                    if describe:
                        txtFile = os.path.join(resourceDir, f"{sanitizedName}.txt")
                        _writeDescribe(resource, txtFile)

        return True

    except Exception as e:
        errorMsg = str(e)
        # "No matches found" means the CRD doesn't exist, which is normal (INFO level)
        if "No matches found" in errorMsg or "not found" in errorMsg.lower():
            logger.info(f"{namespaceContext}: {kind} ({apiVersion}) - CRD does not exist")
        else:
            logger.warning(f"{namespaceContext}: {kind} ({apiVersion}) - {errorMsg}")
        return False


def _writeSummary(resources, outputFile: str) -> None:
    """Write resource summary in wide format.

    Generates a text summary similar to 'kubectl get -o wide' output.

    Args:
        resources: ResourceList or ResourceInstance from Kubernetes API
        outputFile (str): Path to output file
    """
    with open(outputFile, "w") as f:
        if hasattr(resources, "items") and len(resources.items) > 0:
            # Write header
            f.write(f"{'NAME':<50} {'NAMESPACE':<30} {'STATUS':<20}\n")

            # Write each resource
            for resource in resources.items:
                name = resource.metadata.name or ""
                namespace = getattr(resource.metadata, "namespace", "") or ""
                status = _extractStatus(resource) or ""
                f.write(f"{name:<50} {namespace:<30} {status:<20}\n")
        else:
            f.write("No resources found.\n")


def _writeYaml(resourceDict: dict, outputFile: str) -> None:
    """Write resource as YAML file.

    Args:
        resourceDict (dict): Resource dictionary to write
        outputFile (str): Path to output file
    """
    with open(outputFile, "w") as f:
        yaml.dump(resourceDict, f, default_flow_style=False, sort_keys=False)


def _writeDescribe(resource, outputFile: str) -> None:
    """Write resource describe output.

    Generates output similar to 'kubectl describe' command.

    Args:
        resource: ResourceInstance from Kubernetes API
        outputFile (str): Path to output file
    """
    with open(outputFile, "w") as f:
        resourceDict = resource.to_dict()

        # Write metadata section
        f.write("Name:         {}\n".format(resourceDict.get("metadata", {}).get("name", "")))
        f.write("Namespace:    {}\n".format(resourceDict.get("metadata", {}).get("namespace", "")))
        f.write("Labels:       {}\n".format(resourceDict.get("metadata", {}).get("labels", {})))
        f.write("Annotations:  {}\n".format(resourceDict.get("metadata", {}).get("annotations", {})))
        f.write("\n")

        # Write spec section if present
        if "spec" in resourceDict:
            f.write("Spec:\n")
            f.write(yaml.dump(resourceDict["spec"], default_flow_style=False, indent=2))
            f.write("\n")

        # Write status section if present
        if "status" in resourceDict:
            f.write("Status:\n")
            f.write(yaml.dump(resourceDict["status"], default_flow_style=False, indent=2))


def _extractStatus(resource) -> str:
    """Extract status information from resource.

    Attempts to extract meaningful status from various resource types.

    Args:
        resource: ResourceInstance from Kubernetes API

    Returns:
        str: Status string or empty string if not available
    """
    try:
        resourceDict = resource.to_dict()
        status = resourceDict.get("status", {})

        # Try common status fields
        if "phase" in status:
            return status["phase"]
        elif "conditions" in status and len(status["conditions"]) > 0:
            # Get last condition
            lastCondition = status["conditions"][-1]
            return f"{lastCondition.get('type', '')}: {lastCondition.get('status', '')}"
        else:
            return ""
    except Exception:
        return ""


# Made with Bob
