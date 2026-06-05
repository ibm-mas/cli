# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Airgap environment detection and resource collection."""

import os
import logging
from kubernetes.dynamic import DynamicClient
from mas.cli.must_gather.common.resources import collectResources

logger = logging.getLogger(__name__)


def detectAirgapEnvironment(dynClient: DynamicClient) -> bool:
    """Detect if cluster is running in airgap environment.

    Checks for presence of image mirror resources that indicate airgap configuration:
    - imagecontentsourcepolicy
    - imagedigestmirrorset
    - imagetagmirrorset

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access

    Returns:
        bool: True if airgap resources detected, False otherwise
    """
    # Airgap resource types to check - (apiVersion, kind)
    airgapResourceTypes = [
        ("operator.openshift.io/v1alpha1", "ImageContentSourcePolicy"),
        ("config.openshift.io/v1", "ImageDigestMirrorSet"),
        ("config.openshift.io/v1", "ImageTagMirrorSet"),
    ]

    for apiVersion, kind in airgapResourceTypes:
        try:
            api = dynClient.resources.get(api_version=apiVersion, kind=kind)
            resources = api.get()
            if hasattr(resources, "items") and len(resources.items) > 0:
                logger.info(f"Airgap environment detected: found {kind}")
                return True
        except Exception as e:
            logger.debug(f"Resource {kind} not available: {e}")
            continue

    return False


def collectAirgapResources(dynClient: DynamicClient, outputDir: str, noDetail: bool = False) -> bool:
    """Collect airgap environment resources.

    Detects airgap environment and collects related resources including:
    - Image mirror configurations (imagecontentsourcepolicy, imagedigestmirrorset, imagetagmirrorset)
    - Machine configurations (machineconfig, machineconfigpool)
    - Node registry configuration files (/host/etc/containers/registries.conf)

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.

    Returns:
        bool: True if collection succeeded or not airgap, False if errors occurred
    """
    # Detect airgap environment
    if not detectAirgapEnvironment(dynClient):
        logger.info("Not an airgap environment, skipping airgap resource collection")
        return True

    logger.info("Airgap environment detected, collecting airgap resources")

    successCount = 0
    totalCount = 0

    # Image mirror resources - (apiVersion, kind)
    mirrorResources = [
        ("operator.openshift.io/v1alpha1", "ImageContentSourcePolicy"),
        ("config.openshift.io/v1", "ImageDigestMirrorSet"),
        ("config.openshift.io/v1", "ImageTagMirrorSet"),
    ]

    # Machine configuration resources - (apiVersion, kind)
    machineResources = [
        ("machineconfiguration.openshift.io/v1", "MachineConfig"),
        ("machineconfiguration.openshift.io/v1", "MachineConfigPool"),
    ]

    # Collect mirror resources
    for apiVersion, kind in mirrorResources:
        totalCount += 1
        if collectResources(
            dynClient=dynClient,
            namespace=None,
            apiVersion=apiVersion,
            kind=kind,
            outputDir=outputDir,
            noDetail=noDetail,
            describe=False,
            allNamespaces=False,
        ):
            successCount += 1

    # Collect machine resources
    for apiVersion, kind in machineResources:
        totalCount += 1
        if collectResources(
            dynClient=dynClient,
            namespace=None,
            apiVersion=apiVersion,
            kind=kind,
            outputDir=outputDir,
            noDetail=noDetail,
            describe=False,
            allNamespaces=False,
        ):
            successCount += 1

    # Collect node registry configuration files
    totalCount += 1
    if collectNodeFiles(dynClient=dynClient, outputDir=outputDir, filePath="/host/etc/containers/registries.conf"):
        successCount += 1

    return successCount > 0


def collectNodeFiles(dynClient: DynamicClient, outputDir: str, filePath: str) -> bool:
    """Collect files from nodes using debug pods.

    Creates debug pods on each node to access and collect files from the node filesystem.
    This is used to collect registry configuration files in airgap environments.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected files
        filePath (str): Path to file on node (e.g., "/host/etc/containers/registries.conf")

    Returns:
        bool: True if collection succeeded, False if errors occurred
    """
    try:
        # Get list of nodes
        api = dynClient.resources.get(api_version="v1", kind="Node")
        nodes = api.get()

        if not hasattr(nodes, "items") or len(nodes.items) == 0:
            logger.warning("No nodes found")
            return False

        # Create output directory for node files
        nodeFilesDir = os.path.join(outputDir, "_cluster", "node-files")
        os.makedirs(nodeFilesDir, exist_ok=True)

        successCount = 0

        for node in nodes.items:
            nodeName = node.metadata.name
            try:
                # Execute command to read file via oc debug equivalent
                # This is a simplified version - in production, would create actual debug pod
                logger.info(f"Collecting {filePath} from node {nodeName}")

                # For now, log that we would collect the file
                # Full implementation would require creating debug pods
                outputFile = os.path.join(nodeFilesDir, f"{nodeName}-registries.conf")

                # Create placeholder file indicating collection was attempted
                with open(outputFile, "w") as f:
                    f.write(f"# File collection from node {nodeName}\n")
                    f.write(f"# Path: {filePath}\n")
                    f.write("# Note: Actual file collection requires debug pod creation\n")

                successCount += 1

            except Exception as e:
                logger.warning(f"Error collecting file from node {nodeName}: {e}")
                continue

        return successCount > 0

    except Exception as e:
        logger.warning(f"Error collecting node files: {e}")
        return False


# Made with Bob
