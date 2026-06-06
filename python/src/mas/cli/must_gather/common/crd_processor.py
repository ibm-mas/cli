# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""CRD processing utilities for must-gather.

This module provides functionality to process CustomResourceDefinitions (CRDs)
from a Kubernetes cluster, extract printer columns for kubectl-like output,
and identify IBM-specific CRDs.
"""

import os
import yaml
import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from kubernetes.dynamic import DynamicClient
from jsonpath_ng.ext import parse

logger = logging.getLogger(__name__)

# Global cache for printer columns
_printerColumnsCache: Dict[Tuple[str, str], List["PrinterColumn"]] = {}


@dataclass
class PrinterColumn:
    """Represents a printer column from a CRD's additionalPrinterColumns.

    Attributes:
        name: Column name displayed in output
        type: Data type (string, integer, date, etc.)
        jsonPath: JSONPath expression to extract value from resource
        description: Human-readable description of the column
        priority: Display priority (0=always shown, higher=shown with -o wide)
    """

    name: str
    type: str
    jsonPath: str
    description: str = ""
    priority: int = 0


@dataclass
class CRDInfo:
    """Information about a CustomResourceDefinition.

    Attributes:
        kind: Resource kind (e.g., "Suite", "Kafka")
        apiVersion: Full API version (e.g., "core.mas.ibm.com/v1")
        group: API group (e.g., "core.mas.ibm.com")
        printerColumns: List of printer columns for this CRD
        isIBM: Whether this is an IBM CRD
    """

    kind: str
    apiVersion: str
    group: str
    printerColumns: List[PrinterColumn]
    isIBM: bool


def extractValueFromJsonPath(resource: dict, jsonPath: str) -> str:
    """Extract value from resource using JSONPath expression.

    Args:
        resource (dict): Kubernetes resource as dictionary
        jsonPath (str): JSONPath expression (e.g., ".metadata.name")

    Returns:
        str: Extracted value or empty string if not found
    """
    try:
        # Handle simple paths without filters
        if "[?" not in jsonPath:
            # Simple path like .metadata.name or .status.conditions[0].status
            parts = jsonPath.lstrip(".").split(".")
            value = resource
            for part in parts:
                if "[" in part and "]" in part:
                    # Handle array index like conditions[0]
                    field, index = part.split("[")
                    index = int(index.rstrip("]"))
                    value = value.get(field, [])[index]
                else:
                    value = value.get(part, "")
                    if value == "":
                        return ""
            return str(value) if value else ""
        else:
            # Complex path with filter like .status.conditions[?(@.type=="Ready")].status
            # Remove leading dot for jsonpath_ng
            cleanPath = jsonPath.lstrip(".")
            jsonpathExpr = parse(cleanPath)
            matches = jsonpathExpr.find(resource)
            if matches:
                return str(matches[0].value)
            return ""
    except (KeyError, IndexError, TypeError, Exception) as e:
        logger.debug(f"Failed to extract value from JSONPath {jsonPath}: {e}")
        return ""


def getPrinterColumns(kind: str, apiVersion: str) -> List[PrinterColumn]:
    """Get printer columns for a resource type.

    Looks up printer columns from the cache populated by processCRDs().
    If not found, returns fallback columns for built-in Kubernetes resources,
    or a default name-only column.

    Args:
        kind (str): Resource kind (e.g., "Pod", "Suite")
        apiVersion (str): API version (e.g., "v1", "core.mas.ibm.com/v1")

    Returns:
        list: List of PrinterColumn objects
    """
    key = (kind, apiVersion)

    # Check cache first
    if key in _printerColumnsCache:
        return _printerColumnsCache[key]

    # Check fallback mappings for built-in resources
    fallbackColumns = _getFallbackColumns(kind, apiVersion)
    if fallbackColumns:
        return fallbackColumns

    # Default: name only
    return [PrinterColumn(name="Name", type="string", jsonPath=".metadata.name")]


def _getFallbackColumns(kind: str, apiVersion: str) -> Optional[List[PrinterColumn]]:
    """Get fallback printer columns for built-in Kubernetes resources.

    Args:
        kind (str): Resource kind
        apiVersion (str): API version

    Returns:
        list: List of PrinterColumn objects, or None if no fallback defined
    """
    # Fallback mappings for common Kubernetes resources
    fallbacks = {
        # Core Kubernetes resources
        ("Pod", "v1"): [
            PrinterColumn("Name", "string", ".metadata.name"),
            PrinterColumn("Ready", "string", ".status.containerStatuses[0].ready"),
            PrinterColumn("Status", "string", ".status.phase"),
            PrinterColumn("Restarts", "integer", ".status.containerStatuses[0].restartCount"),
            PrinterColumn("Age", "date", ".metadata.creationTimestamp"),
        ],
        ("Service", "v1"): [
            PrinterColumn("Name", "string", ".metadata.name"),
            PrinterColumn("Type", "string", ".spec.type"),
            PrinterColumn("Cluster-IP", "string", ".spec.clusterIP"),
            PrinterColumn("External-IP", "string", ".status.loadBalancer.ingress[0].ip"),
            PrinterColumn("Port(s)", "string", ".spec.ports[0].port"),
            PrinterColumn("Age", "date", ".metadata.creationTimestamp"),
        ],
        ("Namespace", "v1"): [
            PrinterColumn("Name", "string", ".metadata.name"),
            PrinterColumn("Status", "string", ".status.phase"),
            PrinterColumn("Age", "date", ".metadata.creationTimestamp"),
        ],
        ("ConfigMap", "v1"): [
            PrinterColumn("Name", "string", ".metadata.name"),
            PrinterColumn("Data", "integer", ".data"),
            PrinterColumn("Age", "date", ".metadata.creationTimestamp"),
        ],
        ("Secret", "v1"): [
            PrinterColumn("Name", "string", ".metadata.name"),
            PrinterColumn("Type", "string", ".type"),
            PrinterColumn("Data", "integer", ".data"),
            PrinterColumn("Age", "date", ".metadata.creationTimestamp"),
        ],
        ("ServiceAccount", "v1"): [
            PrinterColumn("Name", "string", ".metadata.name"),
            PrinterColumn("Secrets", "integer", ".secrets"),
            PrinterColumn("Age", "date", ".metadata.creationTimestamp"),
        ],
        ("PersistentVolumeClaim", "v1"): [
            PrinterColumn("Name", "string", ".metadata.name"),
            PrinterColumn("Status", "string", ".status.phase"),
            PrinterColumn("Volume", "string", ".spec.volumeName"),
            PrinterColumn("Capacity", "string", ".status.capacity.storage"),
            PrinterColumn("Access Modes", "string", ".status.accessModes[0]"),
            PrinterColumn("StorageClass", "string", ".spec.storageClassName"),
            PrinterColumn("Age", "date", ".metadata.creationTimestamp"),
        ],
        # Apps resources
        ("Deployment", "apps/v1"): [
            PrinterColumn("Name", "string", ".metadata.name"),
            PrinterColumn("Ready", "string", ".status.readyReplicas"),
            PrinterColumn("Up-to-Date", "integer", ".status.updatedReplicas"),
            PrinterColumn("Available", "integer", ".status.availableReplicas"),
            PrinterColumn("Age", "date", ".metadata.creationTimestamp"),
        ],
        ("StatefulSet", "apps/v1"): [
            PrinterColumn("Name", "string", ".metadata.name"),
            PrinterColumn("Ready", "string", ".status.readyReplicas"),
            PrinterColumn("Age", "date", ".metadata.creationTimestamp"),
        ],
        ("DaemonSet", "apps/v1"): [
            PrinterColumn("Name", "string", ".metadata.name"),
            PrinterColumn("Desired", "integer", ".status.desiredNumberScheduled"),
            PrinterColumn("Current", "integer", ".status.currentNumberScheduled"),
            PrinterColumn("Ready", "integer", ".status.numberReady"),
            PrinterColumn("Up-to-Date", "integer", ".status.updatedNumberScheduled"),
            PrinterColumn("Available", "integer", ".status.numberAvailable"),
            PrinterColumn("Age", "date", ".metadata.creationTimestamp"),
        ],
        ("ReplicaSet", "apps/v1"): [
            PrinterColumn("Name", "string", ".metadata.name"),
            PrinterColumn("Desired", "integer", ".spec.replicas"),
            PrinterColumn("Current", "integer", ".status.replicas"),
            PrinterColumn("Ready", "integer", ".status.readyReplicas"),
            PrinterColumn("Age", "date", ".metadata.creationTimestamp"),
        ],
        # Batch resources
        ("Job", "batch/v1"): [
            PrinterColumn("Name", "string", ".metadata.name"),
            PrinterColumn("Completions", "string", ".status.succeeded"),
            PrinterColumn("Duration", "string", ".status.completionTime"),
            PrinterColumn("Age", "date", ".metadata.creationTimestamp"),
        ],
        ("CronJob", "batch/v1"): [
            PrinterColumn("Name", "string", ".metadata.name"),
            PrinterColumn("Schedule", "string", ".spec.schedule"),
            PrinterColumn("Suspend", "boolean", ".spec.suspend"),
            PrinterColumn("Active", "integer", ".status.active"),
            PrinterColumn("Last Schedule", "date", ".status.lastScheduleTime"),
            PrinterColumn("Age", "date", ".metadata.creationTimestamp"),
        ],
        # RBAC resources
        ("Role", "rbac.authorization.k8s.io/v1"): [
            PrinterColumn("Name", "string", ".metadata.name"),
            PrinterColumn("Age", "date", ".metadata.creationTimestamp"),
        ],
        ("RoleBinding", "rbac.authorization.k8s.io/v1"): [
            PrinterColumn("Name", "string", ".metadata.name"),
            PrinterColumn("Role", "string", ".roleRef.name"),
            PrinterColumn("Age", "date", ".metadata.creationTimestamp"),
        ],
        ("ClusterRole", "rbac.authorization.k8s.io/v1"): [
            PrinterColumn("Name", "string", ".metadata.name"),
            PrinterColumn("Age", "date", ".metadata.creationTimestamp"),
        ],
        ("ClusterRoleBinding", "rbac.authorization.k8s.io/v1"): [
            PrinterColumn("Name", "string", ".metadata.name"),
            PrinterColumn("Role", "string", ".roleRef.name"),
            PrinterColumn("Age", "date", ".metadata.creationTimestamp"),
        ],
        # Networking resources
        ("Ingress", "networking.k8s.io/v1"): [
            PrinterColumn("Name", "string", ".metadata.name"),
            PrinterColumn("Class", "string", ".spec.ingressClassName"),
            PrinterColumn("Hosts", "string", ".spec.rules[0].host"),
            PrinterColumn("Address", "string", ".status.loadBalancer.ingress[0].ip"),
            PrinterColumn("Ports", "string", ".spec.rules[0].http.paths[0].backend.service.port.number"),
            PrinterColumn("Age", "date", ".metadata.creationTimestamp"),
        ],
        # Storage resources
        ("StorageClass", "storage.k8s.io/v1"): [
            PrinterColumn("Name", "string", ".metadata.name"),
            PrinterColumn("Provisioner", "string", ".provisioner"),
            PrinterColumn("Reclaim Policy", "string", ".reclaimPolicy"),
            PrinterColumn("Volume Binding Mode", "string", ".volumeBindingMode"),
            PrinterColumn("Age", "date", ".metadata.creationTimestamp"),
        ],
        # OpenShift specific resources
        ("Node", "v1"): [
            PrinterColumn("Name", "string", ".metadata.name"),
            PrinterColumn("Status", "string", '.status.conditions[?(@.type=="Ready")].status'),
            PrinterColumn("Roles", "string", ".metadata.labels.node-role\\.kubernetes\\.io/worker"),
            PrinterColumn("Age", "date", ".metadata.creationTimestamp"),
            PrinterColumn("Version", "string", ".status.nodeInfo.kubeletVersion"),
        ],
        ("ClusterVersion", "config.openshift.io/v1"): [
            PrinterColumn("Name", "string", ".metadata.name"),
            PrinterColumn("Version", "string", ".status.desired.version"),
            PrinterColumn("Available", "string", '.status.conditions[?(@.type=="Available")].status'),
            PrinterColumn("Progressing", "string", '.status.conditions[?(@.type=="Progressing")].status'),
            PrinterColumn("Since", "date", '.status.conditions[?(@.type=="Available")].lastTransitionTime'),
            PrinterColumn("Status", "string", '.status.conditions[?(@.type=="Available")].message'),
        ],
        # Operator Lifecycle Manager resources
        ("CatalogSource", "operators.coreos.com/v1alpha1"): [
            PrinterColumn("Name", "string", ".metadata.name"),
            PrinterColumn("Display", "string", ".spec.displayName"),
            PrinterColumn("Type", "string", ".spec.sourceType"),
            PrinterColumn("Publisher", "string", ".spec.publisher"),
            PrinterColumn("Age", "date", ".metadata.creationTimestamp"),
        ],
        ("Subscription", "operators.coreos.com/v1alpha1"): [
            PrinterColumn("Name", "string", ".metadata.name"),
            PrinterColumn("Package", "string", ".spec.name"),
            PrinterColumn("Source", "string", ".spec.source"),
            PrinterColumn("Channel", "string", ".spec.channel"),
            PrinterColumn("Age", "date", ".metadata.creationTimestamp"),
        ],
        ("InstallPlan", "operators.coreos.com/v1alpha1"): [
            PrinterColumn("Name", "string", ".metadata.name"),
            PrinterColumn("CSV", "string", ".spec.clusterServiceVersionNames[0]"),
            PrinterColumn("Approval", "string", ".spec.approval"),
            PrinterColumn("Approved", "boolean", ".spec.approved"),
        ],
        ("ClusterServiceVersion", "operators.coreos.com/v1alpha1"): [
            PrinterColumn("Name", "string", ".metadata.name"),
            PrinterColumn("Display", "string", ".spec.displayName"),
            PrinterColumn("Version", "string", ".spec.version"),
            PrinterColumn("Replaces", "string", ".spec.replaces"),
            PrinterColumn("Phase", "string", ".status.phase"),
        ],
        ("PackageManifest", "packages.operators.coreos.com/v1"): [
            PrinterColumn("Name", "string", ".metadata.name"),
            PrinterColumn("Catalog", "string", ".status.catalogSource"),
            PrinterColumn("Age", "date", ".metadata.creationTimestamp"),
        ],
    }

    return fallbacks.get((kind, apiVersion))


def _writeCRDMarkdownIndex(crdDicts: list, outputFile: str) -> None:
    """Write CRD index as markdown table.

    Generates a markdown file with a table showing all CRDs with their name,
    group, and creation timestamp. The name column is converted to a markdown
    link pointing to the individual CRD YAML file.

    Args:
        crdDicts (list): List of CRD dictionaries
        outputFile (str): Path to output markdown file
    """
    with open(outputFile, "w") as f:
        # Write header
        f.write("# CustomResourceDefinition (apiextensions.k8s.io/v1)\n\n")

        if len(crdDicts) > 0:
            # Write table header
            f.write("| Name | Group | Age |\n")
            f.write("| --- | --- | --- |\n")

            # Write data rows
            for crdDict in crdDicts:
                crdName = crdDict.get("metadata", {}).get("name", "")
                group = crdDict.get("spec", {}).get("group", "")
                creationTimestamp = crdDict.get("metadata", {}).get("creationTimestamp", "")

                # Convert name to markdown link
                nameLink = f"[{crdName}](customresourcedefinitions/{crdName}.yaml)"

                # Escape pipe characters
                group = group.replace("|", "\\|") if group else ""
                creationTimestamp = creationTimestamp.replace("|", "\\|") if creationTimestamp else ""

                f.write(f"| {nameLink} | {group} | {creationTimestamp} |\n")
        else:
            f.write("No resources found.\n")


def processCRDs(dynClient: DynamicClient, outputDir: str) -> Tuple[Dict[Tuple[str, str], List[PrinterColumn]], List[Tuple[str, str]]]:
    """Process all CRDs in the cluster.

    Loads all CustomResourceDefinitions from the cluster, extracts printer columns,
    identifies IBM CRDs, and writes CRDs to a YAML file.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources

    Returns:
        tuple: (printerColumnsCache, ibmCRDsList)
            - printerColumnsCache: Dict mapping (kind, apiVersion) to printer columns
            - ibmCRDsList: List of (kind, apiVersion) tuples for IBM CRDs
    """
    printerColumnsCache = {}
    ibmCRDsList = []
    crdDicts = []

    try:
        logger.debug("Loading CRDs from cluster")
        crdApi = dynClient.resources.get(kind="CustomResourceDefinition")
        crds = crdApi.get()

        for crd in crds.items:
            crdDict = crd.to_dict()
            crdDicts.append(crdDict)

            # Extract CRD information
            crdName = crdDict.get("metadata", {}).get("name", "")
            spec = crdDict.get("spec", {})
            group = spec.get("group", "")
            names = spec.get("names", {})
            kind = names.get("kind", "")

            # Determine if IBM CRD
            isIBM = "ibm" in crdName.lower()

            # Process versions to extract printer columns
            versions = spec.get("versions", [])
            storageVersions = []
            for version in versions:
                if version.get("served", False):
                    versionName = version.get("name", "")
                    apiVersion = f"{group}/{versionName}"
                    isStorage = version.get("storage", False)

                    if isStorage:
                        storageVersions.append(versionName)

                    # Extract printer columns
                    printerColumns = []
                    additionalPrinterColumns = version.get("additionalPrinterColumns", [])
                    for col in additionalPrinterColumns:
                        printerColumn = PrinterColumn(
                            name=col.get("name", ""),
                            type=col.get("type", "string"),
                            jsonPath=col.get("jsonPath", ""),
                            description=col.get("description", ""),
                            priority=col.get("priority", 0),
                        )
                        printerColumns.append(printerColumn)

                    # Cache printer columns
                    if printerColumns:
                        printerColumnsCache[(kind, apiVersion)] = printerColumns

                    # Add to IBM CRD list if applicable
                    if isIBM and isStorage:
                        ibmCRDsList.append((kind, apiVersion))

            # Log one line per CRD with all key information
            storageInfo = f"storage={','.join(storageVersions)}" if storageVersions else "storage=none"
            logger.debug(f"CRD: {crdName} | kind={kind} | {storageInfo} | isIBM={isIBM}")

        # Write individual CRD files and generate markdown index
        clusterDir = os.path.join(outputDir, "_cluster")
        crdDir = os.path.join(clusterDir, "customresourcedefinitions")
        os.makedirs(crdDir, exist_ok=True)

        # Write each CRD to its own file
        for crdDict in crdDicts:
            crdName = crdDict.get("metadata", {}).get("name", "unknown")
            crdFile = os.path.join(crdDir, f"{crdName}.yaml")
            with open(crdFile, "w") as f:
                yaml.dump(crdDict, f, default_flow_style=False, sort_keys=False)

        # Generate markdown index
        indexFile = os.path.join(clusterDir, "customresourcedefinitions.md")
        _writeCRDMarkdownIndex(crdDicts, indexFile)

        logger.info(f"Processed {len(crdDicts)} CRDs, identified {len(ibmCRDsList)} IBM CRDs")
        if ibmCRDsList:
            logger.info(f"IBM CRDs found: {', '.join([f'{kind} ({apiVersion})' for kind, apiVersion in ibmCRDsList])}")

        # Update global cache
        _printerColumnsCache.update(printerColumnsCache)

        return printerColumnsCache, ibmCRDsList

    except Exception as e:
        logger.warning(f"Error processing CRDs: {e}")
        return {}, []
