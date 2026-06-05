# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""IBM Suite License Service collector for must-gather.

This module provides functionality to discover and collect SLS resources from
Kubernetes clusters. It can discover SLS namespaces either from slscfg custom
resources (when MAS instance IDs are provided) or from LicenseService CRs directly.
"""

import logging
from typing import Set, Optional, List
from kubernetes.dynamic import DynamicClient
from kubernetes.client.exceptions import ApiException

logger = logging.getLogger(__name__)


def discoverSLSNamespaces(dynClient: DynamicClient, masInstanceIds: Optional[List[str]] = None) -> Set[str]:
    """Discover SLS namespaces from slscfg or LicenseService CRs.

    When MAS instance IDs are provided, discovers SLS namespaces by:
    1. Finding slscfg CRs in mas-{instance}-core namespaces
    2. Extracting SLS URLs from spec.config.url
    3. Finding routes matching those URLs to determine namespaces

    When no MAS instance IDs are provided, discovers namespaces by:
    1. Finding all LicenseService CRs across all namespaces
    2. Extracting their namespaces

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        masInstanceIds (list, optional): List of MAS instance IDs to search for slscfg. Defaults to None.

    Returns:
        set: Set of unique SLS namespace names
    """
    namespaces = set()

    if masInstanceIds:
        # Discover from slscfg CRs
        namespaces = _discoverFromSlsCfg(dynClient, masInstanceIds)
    else:
        # Discover from LicenseService CRs
        namespaces = _discoverFromLicenseService(dynClient)

    return namespaces


def _discoverFromSlsCfg(dynClient: DynamicClient, masInstanceIds: List[str]) -> Set[str]:
    """Discover SLS namespaces from slscfg CRs.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client
        masInstanceIds (list): List of MAS instance IDs

    Returns:
        set: Set of SLS namespace names
    """
    namespaces = set()

    try:
        slsCfgApi = dynClient.resources.get(api_version="config.mas.ibm.com/v1", kind="SlsCfg")
        routeApi = dynClient.resources.get(api_version="route.openshift.io/v1", kind="Route")

        for instanceId in masInstanceIds:
            coreNamespace = f"mas-{instanceId}-core"
            try:
                # Get slscfg CRs from the core namespace
                slsCfgs = slsCfgApi.get(namespace=coreNamespace)

                for slsCfg in slsCfgs.items:
                    # Extract URL from spec.config.url
                    url = slsCfg.get("spec", {}).get("config", {}).get("url", "")
                    if not url:
                        continue

                    # Extract route name from URL (format: https://route-name.namespace.svc:443)
                    # Split by '/' and get the host part, then split by '.' to get route name
                    try:
                        host = url.split("//")[1].split("/")[0].split(":")[0]
                        routeName = host.split(".")[0]

                        # Find the route across all namespaces
                        routes = routeApi.get()
                        for route in routes.items:
                            if route.metadata.name == routeName:
                                namespaces.add(route.metadata.namespace)
                                break
                    except (IndexError, AttributeError) as e:
                        logger.debug(f"Could not parse SLS URL '{url}': {e}")
                        continue

            except ApiException as e:
                if e.status == 404:
                    logger.debug(f"No slscfg found in namespace {coreNamespace}")
                else:
                    logger.warning(f"Error getting slscfg from {coreNamespace}: {e}")
            except Exception as e:
                logger.warning(f"Error processing slscfg in {coreNamespace}: {e}")

    except Exception as e:
        logger.debug(f"Could not discover SLS namespaces from slscfg: {e}")

    return namespaces


def _discoverFromLicenseService(dynClient: DynamicClient) -> Set[str]:
    """Discover SLS namespaces from LicenseService CRs.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client

    Returns:
        set: Set of SLS namespace names
    """
    namespaces = set()

    try:
        licenseServiceApi = dynClient.resources.get(api_version="sls.ibm.com/v1", kind="LicenseService")
        licenseServices = licenseServiceApi.get()

        for ls in licenseServices.items:
            namespace = ls.metadata.namespace
            if namespace:
                namespaces.add(namespace)

    except Exception as e:
        logger.debug(f"Could not discover SLS namespaces from LicenseService: {e}")

    return namespaces


def collectSLSNamespace(dynClient: DynamicClient, namespace: str, outputDir: str, noDetail: bool = False) -> bool:
    """Collect SLS resources from a namespace.

    Collects standard Kubernetes resources, IBM custom resources, pods, and secrets
    from the specified SLS namespace. Also generates a summary report.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        namespace (str): SLS namespace to collect from
        outputDir (str): Base output directory for collected resources
        noDetail (bool, optional): If True, skip detailed YAML collection. Defaults to False.

    Returns:
        bool: True if collection succeeded, False if errors occurred
    """
    try:
        # Import here to avoid circular dependency
        from ..common import collectResources, collectPods, collectSecrets, collectIBMCustomResources

        logger.info(f"Collecting SLS resources from namespace: {namespace}")

        # Generate summary first
        generateSLSSummary(dynClient, namespace, outputDir)

        if noDetail:
            return True

        success = True

        # Collect IBM custom resources
        try:
            if not collectIBMCustomResources(dynClient, namespace, f"{outputDir}/resources"):
                success = False
        except Exception as e:
            logger.warning(f"Error collecting IBM custom resources from {namespace}: {e}")
            success = False

        # Collect standard resources
        standardResources = [
            ("v1", "ConfigMap"),
            ("v1", "Service"),
            ("v1", "Secret"),
            ("apps/v1", "Deployment"),
            ("apps/v1", "StatefulSet"),
            ("apps/v1", "DaemonSet"),
            ("batch/v1", "Job"),
            ("batch/v1", "CronJob"),
        ]

        for apiVersion, kind in standardResources:
            try:
                collectResources(dynClient, namespace, apiVersion, kind, f"{outputDir}/resources")
            except Exception as e:
                logger.warning(f"Error collecting {kind} from {namespace}: {e}")
                success = False

        # Collect pods with logs
        try:
            collectPods(dynClient, namespace, f"{outputDir}/pods", podLogs=True)
        except Exception as e:
            logger.warning(f"Error collecting pods from {namespace}: {e}")
            success = False

        # Collect secrets (without data)
        try:
            collectSecrets(dynClient, namespace, f"{outputDir}/resources", secretData=False)
        except Exception as e:
            logger.warning(f"Error collecting secrets from {namespace}: {e}")
            success = False

        return success

    except Exception as e:
        logger.error(f"Error collecting SLS namespace {namespace}: {e}")
        return False


def generateSLSSummary(dynClient: DynamicClient, namespace: str, outputDir: str):
    """Generate SLS summary report for a namespace.

    Creates a text file summarizing the LicenseService instances found in the namespace,
    including their status and key configuration details.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        namespace (str): SLS namespace to generate summary for
        outputDir (str): Output directory for the summary file
    """
    import os

    summaryPath = os.path.join(outputDir, f"{namespace}.txt")

    try:
        licenseServiceApi = dynClient.resources.get(api_version="sls.ibm.com/v1", kind="LicenseService")
        licenseServices = licenseServiceApi.get(namespace=namespace)

        with open(summaryPath, "w") as f:
            f.write(f"SLS Summary for namespace: {namespace}\n")
            f.write("=" * 80 + "\n\n")

            if not licenseServices.items:
                f.write("No LicenseService instances found in this namespace.\n")
            else:
                for ls in licenseServices.items:
                    f.write(f"LicenseService: {ls.metadata.name}\n")
                    f.write("-" * 80 + "\n")
                    f.write(f"Namespace: {ls.metadata.namespace}\n")
                    f.write(f"Created: {ls.metadata.creationTimestamp}\n")

                    # Write status conditions if available
                    status = ls.get("status", {})
                    conditions = status.get("conditions", [])
                    if conditions:
                        f.write("\nConditions:\n")
                        for condition in conditions:
                            condType = condition.get("type", "Unknown")
                            condStatus = condition.get("status", "Unknown")
                            f.write(f"  - {condType}: {condStatus}\n")

                    f.write("\n")

        logger.info(f"Generated SLS summary: {summaryPath}")

    except Exception as e:
        logger.warning(f"Error generating SLS summary for {namespace}: {e}")
        # Create a minimal summary file even on error
        try:
            with open(summaryPath, "w") as f:
                f.write(f"SLS Summary for namespace: {namespace}\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"Error generating summary: {e}\n")
        except Exception:
            pass


# Made with Bob
