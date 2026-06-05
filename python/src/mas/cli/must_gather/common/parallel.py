# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Parallel resource collection utilities for must-gather.

This module provides utilities for collecting multiple Kubernetes resources
in parallel using ThreadPoolExecutor to improve collection performance.
"""

import logging
from typing import List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from kubernetes.dynamic import DynamicClient
from .resources import collectResources

logger = logging.getLogger(__name__)


def collectResourcesParallel(
    dynClient: DynamicClient,
    namespace: str,
    resources: List[tuple[str, str]],
    outputDir: str,
    noDetail: bool = False,
    max_workers: int = 10,
    progressCallback: Optional[Callable[[int, int], None]] = None,
) -> bool:
    """Collect multiple resource types in parallel using threads.

    Uses ThreadPoolExecutor to collect multiple Kubernetes resource types
    simultaneously, significantly reducing collection time for I/O-bound
    operations. Each resource type is collected independently in its own thread.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        namespace (str): Target namespace for collection
        resources (list): List of (apiVersion, kind) tuples to collect
        outputDir (str): Base output directory for collected resources
        noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.
        max_workers (int, optional): Maximum number of parallel threads. Defaults to 10.
        progressCallback (callable, optional): Callback function called with (completed, total) after each completion. Defaults to None.

    Returns:
        bool: True if all collections succeeded, False if any collection failed
    """
    # Handle empty resources list
    if not resources:
        return True

    allSuccess = True
    resourcesOutputDir = f"{outputDir}/resources"
    totalResources = len(resources)
    completedResources = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all collection tasks
        futures = {}
        for apiVersion, kind in resources:
            future = executor.submit(
                collectResources,
                dynClient=dynClient,
                namespace=namespace,
                apiVersion=apiVersion,
                kind=kind,
                outputDir=resourcesOutputDir,
                noDetail=noDetail,
                describe=False,
                allNamespaces=False,
            )
            futures[future] = (apiVersion, kind)

        # Process results as they complete
        for future in as_completed(futures):
            apiVersion, kind = futures[future]
            try:
                success = future.result()
                if not success:
                    allSuccess = False
            except Exception as e:
                logger.error(f"Unexpected error in parallel collection of {kind} ({apiVersion}): {e}")
                allSuccess = False
            finally:
                completedResources += 1
                # Update progress callback if provided
                if progressCallback is not None:
                    progressCallback(completedResources, totalResources)

    return allSuccess


# Made with Bob
