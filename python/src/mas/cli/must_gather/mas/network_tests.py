# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Network connectivity tests for MAS must-gather."""

import json
import logging
import os
from typing import Optional, List, Dict, Any
from kubernetes.dynamic import DynamicClient
from kubernetes import client

from mas.cli.must_gather.common.pod_exec import execCurlInPod
from .version import isMAS91OrLater

logger = logging.getLogger(__name__)


def _findPodByPrefix(dynClient: DynamicClient, namespace: str, podPrefix: str) -> Optional[str]:
    """Find first pod matching a name prefix.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client
        namespace (str): Namespace to search
        podPrefix (str): Pod name prefix to match

    Returns:
        str: Pod name if found, None otherwise
    """
    try:
        coreV1 = client.CoreV1Api(dynClient.client)
        pods = coreV1.list_namespaced_pod(namespace=namespace)

        for pod in pods.items:
            if pod.metadata.name.startswith(podPrefix) and pod.status.phase == "Running":
                return pod.metadata.name

        return None
    except Exception as e:
        logger.debug(f"Error finding pod with prefix {podPrefix}: {e}")
        return None


def _generateTestSummary(testName: str, targetUrl: str, podName: Optional[str], result: Dict[str, Any]) -> List[str]:
    """Generate markdown summary for a connectivity test.

    Args:
        testName (str): Name of the test
        targetUrl (str): Target URL being tested
        podName (str, optional): Pod name used for test, None if pod not found
        result (dict): Test result from execCurlInPod

    Returns:
        list: List of markdown lines
    """
    lines = []
    lines.append(f"## {testName}\n")
    lines.append(f"**Target URL:** {targetUrl}\n")

    if not podName:
        lines.append("**Result:** ⚠️ Pod not found\n")
        return lines

    lines.append(f"**Pod:** {podName}\n")

    if result["success"] and result["json_data"]:
        lines.append("**Result:** ✅ Successful\n")
        lines.append(f"**Response:**\n```json\n{json.dumps(result['json_data'], indent=2)}\n```\n")
    else:
        lines.append("**Result:** ❌ Failed\n")
        lines.append(f"**Error:** {result['error']}\n")
        if result["raw_response"]:
            lines.append(f"**Response:**\n```\n{result['raw_response']}\n```\n")

    return lines


def testCoreToManageConnectivity(dynClient: DynamicClient, instanceId: str, workspaceId: str, outputDir: str) -> bool:
    """Test network connectivity from MAS Core to Manage.

    Tests connectivity from internalapi and coreapi pods to Manage /ping endpoint.
    Saves results to network-test.md in the core namespace directory.

    Note: This test requires MAS >= 9.1 as the /maximo/api/ping endpoint is not
    available in earlier versions.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client
        instanceId (str): MAS instance ID
        workspaceId (str): Manage workspace ID
        outputDir (str): Base output directory

    Returns:
        bool: True if tests completed (even if some failed), False on error
    """
    coreNamespace = f"mas-{instanceId}-core"
    manageNamespace = f"mas-{instanceId}-manage"

    # Check MAS version using shared utility
    is91OrLater, masVersion = isMAS91OrLater(dynClient, coreNamespace)

    results = []
    results.append("# Core Network Connectivity Tests\n")
    results.append(f"**Instance ID:** {instanceId}\n")
    results.append(f"**Workspace ID:** {workspaceId}\n")
    results.append(f"**MAS Version:** {masVersion}\n\n")

    # Skip tests if MAS < 9.1
    if not is91OrLater:
        results.append("**Note:** Skipping Core→Manage connectivity tests. ")
        results.append("MAS version is below 9.1, so /maximo/api/ping endpoint is not available in Manage.\n\n")

        # Write results
        networkTestsDir = os.path.join(outputDir, "network-tests")
        os.makedirs(networkTestsDir, exist_ok=True)
        outputPath = os.path.join(networkTestsDir, f"{coreNamespace}.md")

        try:
            with open(outputPath, "w") as f:
                f.write("".join(results))
            logger.info(f"Network connectivity test results saved to {outputPath}")
            return True
        except Exception as e:
            logger.error(f"Failed to write network test results: {e}")
            return False

    manageUrl = f"https://{instanceId}-{workspaceId}-foundation.{manageNamespace}.svc/maximo/api/ping"

    # Test from internalapi pod
    internalapiPod = _findPodByPrefix(dynClient, coreNamespace, f"{instanceId}-internalapi-")
    if internalapiPod:
        result = execCurlInPod(
            dynClient=dynClient,
            namespace=coreNamespace,
            podName=internalapiPod,
            url=manageUrl,
            certPath="/etc/ssl/certs/mascore-cert/tls.crt",
            keyPath="/etc/ssl/certs/mascore-cert/tls.key",
            caPath="/etc/ssl/certs/mascore-cert/ca.crt",
        )
        results.extend(_generateTestSummary("Test from internalapi pod", manageUrl, internalapiPod, result))
    else:
        results.extend(_generateTestSummary("Test from internalapi pod", manageUrl, None, {}))

    # Test from coreapi pod
    coreApiPod = _findPodByPrefix(dynClient, coreNamespace, f"{instanceId}-coreapi-")
    if coreApiPod:
        result = execCurlInPod(
            dynClient=dynClient,
            namespace=coreNamespace,
            podName=coreApiPod,
            url=manageUrl,
            certPath="/etc/mas/certs/manage-cert-internal/tls.crt",
            keyPath="/etc/mas/certs/manage-cert-internal/tls.key",
            caPath="/etc/mas/certs/manage-cert-internal/ca.crt",
        )
        results.extend(_generateTestSummary("Test from coreapi pod", manageUrl, coreApiPod, result))
    else:
        results.extend(_generateTestSummary("Test from coreapi pod", manageUrl, None, {}))

    # Write results
    networkTestsDir = os.path.join(outputDir, "network-tests")
    os.makedirs(networkTestsDir, exist_ok=True)
    outputPath = os.path.join(networkTestsDir, f"{coreNamespace}.md")

    try:
        with open(outputPath, "w") as f:
            f.write("".join(results))
        logger.info(f"Network connectivity test results saved to {outputPath}")
        return True
    except Exception as e:
        logger.error(f"Failed to write network test results: {e}")
        return False


def testManageToCoreConnectivity(dynClient: DynamicClient, instanceId: str, workspaceId: str, bundleName: str, outputDir: str) -> bool:
    """Test network connectivity from Manage to MAS Core.

    Tests connectivity from Manage pod to MAS internalapi endpoint.
    - MAS >= 9.1: Uses /v1/authservice/systeminfo endpoint
    - MAS < 9.1: Uses /v1/idps endpoint

    Saves results to network-test.md in the manage namespace directory.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client
        instanceId (str): MAS instance ID
        workspaceId (str): Manage workspace ID
        bundleName (str): Manage bundle name to find pod
        outputDir (str): Base output directory

    Returns:
        bool: True if tests completed (even if some failed), False on error
    """
    coreNamespace = f"mas-{instanceId}-core"
    manageNamespace = f"mas-{instanceId}-manage"

    # Check MAS version using shared utility
    is91OrLater, masVersion = isMAS91OrLater(dynClient, coreNamespace)

    # Select appropriate endpoint based on version
    if is91OrLater:
        coreUrl = f"https://internalapi.{coreNamespace}.svc/v1/authservice/systeminfo"
    else:
        coreUrl = f"https://internalapi.{coreNamespace}.svc/v1/idps"

    results = []
    results.append("# Manage Network Connectivity Tests\n")
    results.append(f"**Instance ID:** {instanceId}\n")
    results.append(f"**Workspace ID:** {workspaceId}\n")
    results.append(f"**Bundle Name:** {bundleName}\n")
    results.append(f"**MAS Version:** {masVersion}\n\n")

    # Find Manage pod by bundle name label
    try:
        coreV1 = client.CoreV1Api(dynClient.client)
        pods = coreV1.list_namespaced_pod(namespace=manageNamespace, label_selector=f"mas.ibm.com/appTypeName={bundleName}")

        managePod = None
        containerName = None
        for pod in pods.items:
            if pod.status.phase == "Running":
                managePod = pod.metadata.name
                # Get first container name from pod spec
                if pod.spec.containers:
                    containerName = pod.spec.containers[0].name
                break

        if managePod and containerName:
            result = execCurlInPod(
                dynClient=dynClient,
                namespace=manageNamespace,
                podName=managePod,
                url=coreUrl,
                certPath="/etc/pki/tls/certs/internal-manage-tls/tls.crt",
                keyPath="/etc/pki/tls/certs/internal-manage-tls/tls.key",
                caPath="/etc/pki/tls/certs/internal-manage-tls/ca.crt",
                containerName=containerName,
            )
            results.extend(_generateTestSummary("Test from Manage pod", coreUrl, managePod, result))
        else:
            results.extend(_generateTestSummary("Test from Manage pod", coreUrl, None, {}))

    except Exception as e:
        results.append("**Result:** ❌ Error\n")
        results.append(f"**Error:** {str(e)}\n")
        logger.error(f"Error testing Manage to Core connectivity: {e}")

    # Write results
    networkTestsDir = os.path.join(outputDir, "network-tests")
    os.makedirs(networkTestsDir, exist_ok=True)
    outputPath = os.path.join(networkTestsDir, f"{manageNamespace}.md")

    try:
        with open(outputPath, "w") as f:
            f.write("".join(results))
        logger.info(f"Network connectivity test results saved to {outputPath}")
        return True
    except Exception as e:
        logger.error(f"Failed to write network test results: {e}")
        return False
