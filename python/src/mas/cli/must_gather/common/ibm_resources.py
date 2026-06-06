# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""IBM custom resource collection utilities for must-gather."""

import os
import logging
from typing import List, Optional, Callable
from kubernetes.dynamic import DynamicClient
from .parallel import collectResourcesParallel

logger = logging.getLogger(__name__)

# Cache for IBM CRDs to avoid repeated API calls
_ibmCRDCache: Optional[List[tuple[str, str]]] = None


def getIBMCRDs(dynClient: DynamicClient, precomputedList: Optional[List[tuple[str, str]]] = None) -> List[tuple[str, str]]:
    """Get list of IBM CRDs in the cluster with caching.

    Discovers all IBM CRDs in the cluster and caches the results to avoid
    repeated API calls. The cache persists for the lifetime of the process.
    If a precomputed list is provided, it will be used and cached instead of
    fetching from the cluster.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        precomputedList (list, optional): Pre-computed list of IBM CRDs from CRD processing. Defaults to None.

    Returns:
        list: List of (kind, apiVersion) tuples for IBM CRDs
    """
    global _ibmCRDCache

    # If precomputed list provided, use it and cache it
    if precomputedList is not None:
        logger.debug(f"Using precomputed IBM CRD list ({len(precomputedList)} CRDs)")
        _ibmCRDCache = precomputedList
        return precomputedList

    # Return cached results if available
    if _ibmCRDCache is not None:
        logger.debug(f"Using cached IBM CRDs ({len(_ibmCRDCache)} CRDs)")
        return _ibmCRDCache

    # Fetch and cache IBM CRDs
    try:
        logger.debug("Fetching IBM CRDs from cluster")
        crdApi = dynClient.resources.get(kind="CustomResourceDefinition")
        crds = crdApi.get()

        ibmCRDs = []
        for crd in crds.items:
            crdName = crd.metadata.name
            if "ibm" in crdName.lower():
                crdDict = crd.to_dict()
                kind, apiVersion = _extractKindAndVersionFromCRD(crdDict)
                if kind and apiVersion:
                    ibmCRDs.append((kind, apiVersion))

        _ibmCRDCache = ibmCRDs
        logger.debug(f"Cached {len(ibmCRDs)} IBM CRDs")
        return ibmCRDs

    except Exception as e:
        logger.warning(f"Error fetching IBM CRDs: {e}")
        return []


def _clearIBMCRDCache():
    """Clear the IBM CRD cache.

    This function is primarily for testing purposes to reset the cache
    between test runs.
    """
    global _ibmCRDCache
    _ibmCRDCache = None


def collectIBMCustomResources(
    dynClient: DynamicClient,
    namespace: str,
    outputDir: str,
    noDetail: bool = False,
    progressCallback: Optional[Callable[[int, int], None]] = None,
) -> bool:
    """Collect IBM custom resources from a namespace using parallel collection.

    This is a wrapper around collectResourcesParallel that handles IBM CRD discovery
    and filtering. The actual discovery logic should be done by the caller to provide
    better UI feedback.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        namespace (str): Target namespace for collection
        outputDir (str): Base output directory for collected resources
        noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.
        progressCallback (callable, optional): Callback function called with (completed, total) after each completion. Defaults to None.

    Returns:
        bool: True if collection succeeded, False if errors occurred
    """
    try:
        # Create resources directory
        resourcesDir = os.path.join(outputDir, "resources")
        os.makedirs(resourcesDir, exist_ok=True)

        # Get IBM CRDs (cached)
        ibmCRDs = getIBMCRDs(dynClient)

        # Check which IBM CRDs have instances in the namespace
        ibmCRDsWithInstances = []
        for kind, apiVersion in ibmCRDs:
            try:
                api = dynClient.resources.get(api_version=apiVersion, kind=kind)
                resources = api.get(namespace=namespace)
                if resources.items:
                    ibmCRDsWithInstances.append((apiVersion, kind))
            except Exception:
                # Resource type doesn't exist or can't be queried, skip it
                pass

        # Collect IBM custom resources in parallel
        if ibmCRDsWithInstances:
            return collectResourcesParallel(
                dynClient=dynClient,
                namespace=namespace,
                resources=ibmCRDsWithInstances,
                outputDir=resourcesDir,
                noDetail=noDetail,
                progressCallback=progressCallback,
            )

        return True

    except Exception as e:
        logger.warning(f"Error collecting IBM custom resources: {e}")
        return False


def _extractKindAndVersionFromCRD(crdDict: dict) -> tuple:
    """Extract kind and API version from CRD definition.

    Args:
        crdDict (dict): CRD dictionary

    Returns:
        tuple: (kind, apiVersion) or ("", "") if not found
    """
    try:
        kind = ""
        apiVersion = ""

        # Extract kind from spec.names.kind
        if "spec" in crdDict and "names" in crdDict["spec"]:
            kind = crdDict["spec"]["names"].get("kind", "")

        # Extract API version from spec.group and spec.versions
        if "spec" in crdDict:
            group = crdDict["spec"].get("group", "")
            versions = crdDict["spec"].get("versions", [])

            # Use the first version marked as served=true, or just the first version
            for version in versions:
                if version.get("served", False):
                    versionName = version.get("name", "")
                    if versionName:
                        apiVersion = f"{group}/{versionName}"
                        break

            # Fallback to first version if no served version found
            if not apiVersion and versions:
                versionName = versions[0].get("name", "")
                if versionName:
                    apiVersion = f"{group}/{versionName}"

        # Fallback: derive kind from CRD name if not found
        if not kind:
            crdName = crdDict.get("metadata", {}).get("name", "")
            if crdName:
                # Take first part before first dot and capitalize
                baseName = crdName.split(".")[0]
                # Remove trailing 's' if present and capitalize
                if baseName.endswith("s"):
                    baseName = baseName[:-1]
                kind = baseName.capitalize()

        return (kind, apiVersion)

    except Exception as e:
        logger.debug(f"Error extracting kind and version from CRD: {e}")
        return ("", "")


# Made with Bob
