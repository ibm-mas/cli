# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Thread-safe Kubernetes client utilities for must-gather."""

import os
import tempfile
import threading
from kubernetes import client, config
from kubernetes.dynamic import DynamicClient


def createThreadLocalDynamicClient() -> DynamicClient:
    """Create a thread-local DynamicClient with per-thread cache file.

    When using DynamicClient in a multi-threaded environment, the internal resource
    cache can cause race conditions if multiple threads share the same cache file.
    This function creates a new ApiClient and DynamicClient instance with a unique
    cache file per thread to ensure thread-safety.

    Each thread gets its own cache file in the system temp directory, named using
    the thread ID to prevent collisions.

    Returns:
        DynamicClient: A new thread-local DynamicClient instance with isolated cache
    """

    # Load kubernetes configuration
    kubeConfig = config.load_kube_config()

    # Create a new ApiClient for this thread
    apiClient = client.ApiClient(configuration=kubeConfig)

    # Create unique cache file path for this thread
    threadId = threading.get_ident()
    cacheFile = os.path.join(tempfile.gettempdir(), f"k8s-discovery-cache-{threadId}.json")

    # Create DynamicClient with thread-specific cache file
    dynClient = DynamicClient(apiClient, cache_file=cacheFile)

    return dynClient
