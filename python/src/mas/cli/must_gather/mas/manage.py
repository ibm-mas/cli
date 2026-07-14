# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""MAS Manage collector for must-gather.

This module provides functionality to collect Manage-specific resources and
perform network connectivity tests from Manage to MAS Core.
"""

import logging
from kubernetes.dynamic import DynamicClient

from .network_tests import testManageToCoreConnectivity

logger = logging.getLogger(__name__)


def collectManageNetworkTests(dynClient: DynamicClient, namespace: str, outputDir: str) -> bool:
    """Collect network connectivity tests for Manage namespace.

    Tests connectivity from Manage pods to MAS Core internalapi endpoint.
    Saves results to network-test.md in the manage namespace directory.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client
        namespace (str): Manage namespace (mas-{instance}-manage)
        outputDir (str): Base output directory

    Returns:
        bool: True if tests completed, False on error
    """
    # Extract instance ID from namespace
    if not namespace.startswith("mas-") or not namespace.endswith("-manage"):
        logger.warning(f"Invalid Manage namespace format: {namespace}")
        return False

    instanceId = namespace[4:-7]  # Remove "mas-" prefix and "-manage" suffix

    try:
        # Get ManageWorkspace CR to find workspace ID and bundle name
        manageWorkspaceApi = dynClient.resources.get(api_version="apps.mas.ibm.com/v1", kind="ManageWorkspace")
        workspaces = manageWorkspaceApi.get(namespace=namespace)

        if not workspaces.items:
            logger.debug(f"No ManageWorkspace found in {namespace}, skipping network tests")
            return True

        workspace = workspaces.items[0]
        workspaceId = workspace.metadata.labels.get("mas.ibm.com/workspaceId")

        if not workspaceId:
            logger.warning("Could not determine workspace ID for Manage, skipping network tests")
            return True

        # Determine bundle name
        baseComponent = workspace.spec.get("components", {}).get("base")
        if baseComponent:
            # Full Manage - find bundle name
            serverBundles = workspace.spec.get("settings", {}).get("deployment", {}).get("serverBundles", [])
            bundleName = None

            # Try to find "all" bundle first
            for bundle in serverBundles:
                if bundle.get("bundleType") == "all":
                    bundleName = bundle.get("name")
                    break

            # If not found, try "ui" bundle
            if not bundleName:
                for bundle in serverBundles:
                    if bundle.get("bundleType") == "ui":
                        bundleName = bundle.get("name")
                        break

            if not bundleName:
                logger.warning("Could not determine bundle name for Manage, skipping network tests")
                return True
        else:
            # Foundation only
            bundleName = "foundation"

        # Run connectivity tests
        return testManageToCoreConnectivity(dynClient=dynClient, instanceId=instanceId, workspaceId=workspaceId, bundleName=bundleName, outputDir=outputDir)

    except Exception as e:
        logger.debug(f"Error running Manage network tests: {e}")
        return True  # Don't fail collection if network tests can't run
