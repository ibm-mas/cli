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


def collectAirgapResources(dynClient: DynamicClient, outputDir: str) -> bool:
    """Collect airgap environment resources.

    Detects airgap environment and collects related resources including:
    - Image mirror configurations (imagecontentsourcepolicy, imagedigestmirrorset, imagetagmirrorset)
    - Machine configurations (machineconfig, machineconfigpool)

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources

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
            namespace=None,
            apiVersion=apiVersion,
            kind=kind,
            outputDir=outputDir,
            allNamespaces=False,
        ):
            successCount += 1

    # Collect machine resources
    for apiVersion, kind in machineResources:
        totalCount += 1
        if collectResources(
            namespace=None,
            apiVersion=apiVersion,
            kind=kind,
            outputDir=outputDir,
            allNamespaces=False,
        ):
            successCount += 1

    return successCount > 0
