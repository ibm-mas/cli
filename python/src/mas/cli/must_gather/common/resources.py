# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
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
from typing import Optional, List

from .crd_processor import PrinterColumn, getPrinterColumns, extractValueFromJsonPath
from .thread_safe_client import createThreadLocalDynamicClient

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
    namespace: Optional[str],
    apiVersion: str,
    kind: str,
    outputDir: str,
    allNamespaces: bool = False,
) -> bool:
    """Collect Kubernetes resources of a specific type.

    Collects resources and generates both summary (wide output) and detailed YAML files.
    Supports namespace-scoped and cluster-scoped resources.

    Args:
        namespace (str, optional): Target namespace for collection. Use None for cluster-scoped resources. Defaults to None.
        apiVersion (str): API version of the resource (e.g., "v1", "storage.k8s.io/v1")
        kind (str): Kind of resource to collect (e.g., "Pod", "StorageClass")
        outputDir (str): Base output directory for collected resources
        allNamespaces (bool, optional): If True, collect resources across all namespaces. Defaults to False.

    Returns:
        bool: True if collection succeeded, False if errors occurred
    """
    namespaceContext = namespace if namespace else "_cluster"

    try:
        # Convert kind to plural lowercase for file naming consistency
        resourceType = _pluralizeKind(kind)

        # Create resources directory and namespace directory
        resourcesDir = os.path.join(outputDir, "resources")
        if namespace:
            namespaceDir = os.path.join(resourcesDir, namespace)
        else:
            namespaceDir = os.path.join(resourcesDir, "_cluster")

        os.makedirs(namespaceDir, exist_ok=True)

        # Create thread-local DynamicClient for thread-safety
        dynClient = createThreadLocalDynamicClient()
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
            # We don't want to flood the logs with debug that doesn't help
            # logger.debug(f"{namespaceContext}: {kind} ({apiVersion}) - No resources to collect")
            return True

        logger.info(f"✅ {namespaceContext}: {kind} ({apiVersion}) - Successfully collected {resourceCount} resource{'s' if resourceCount != 1 else ''}")

        # Generate markdown index file
        summaryFile = os.path.join(namespaceDir, f"{resourceType}.md")
        printerColumns = getPrinterColumns(kind, apiVersion)
        _writeMarkdownIndex(resources, summaryFile, kind, apiVersion, printerColumns)

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

        return True

    except Exception as e:
        errorMsg = str(e)
        if "No matches found" in errorMsg or "not found" in errorMsg.lower():
            return True  # No resources of this type in the namespace
        else:
            logger.warning(f"{namespaceContext}: {kind} ({apiVersion}) - {errorMsg}")
            return False


def _writeMarkdownIndex(resources, outputFile: str, kind: str, apiVersion: str, printerColumns: List[PrinterColumn]) -> None:
    """Write resource index as markdown table.

    Generates a markdown file with a table showing resources using printer columns
    from CRD specifications or fallback columns for built-in resources.
    The first column (typically resource name) is converted to a markdown link
    pointing to the resource's YAML file.

    Args:
        resources: ResourceList or ResourceInstance from Kubernetes API
        outputFile (str): Path to output markdown file
        kind (str): Resource kind (e.g., "Pod", "Suite")
        apiVersion (str): API version (e.g., "v1", "core.mas.ibm.com/v1")
        printerColumns (list): List of PrinterColumn objects defining table columns
    """
    # Pluralize kind for directory name (simple pluralization)
    pluralKind = kind.lower() + "s"

    with open(outputFile, "w") as f:
        # Write header
        f.write(f"# {kind} ({apiVersion})\n\n")

        if hasattr(resources, "items") and len(resources.items) > 0:
            # Write table header
            columnNames = [col.name for col in printerColumns]
            f.write("| " + " | ".join(columnNames) + " |\n")

            # Write separator
            f.write("| " + " | ".join(["---"] * len(columnNames)) + " |\n")

            # Write data rows
            for resource in resources.items:
                resourceDict = resource.to_dict()
                resourceName = resource.metadata.name
                values = []
                for idx, col in enumerate(printerColumns):
                    value = extractValueFromJsonPath(resourceDict, col.jsonPath)
                    # Escape pipe characters in values to avoid breaking table
                    value = value.replace("|", "\\|") if value else ""

                    # Convert first column (name) to markdown link only if detail files exist
                    if idx == 0 and value:
                        value = f"[{value}]({pluralKind}/{resourceName}.yaml)"

                    values.append(value)

                f.write("| " + " | ".join(values) + " |\n")
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
