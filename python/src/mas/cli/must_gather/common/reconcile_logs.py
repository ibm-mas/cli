# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Reconcile logs collection utilities for must-gather.

This module provides functionality to collect Ansible operator reconciliation logs
from operator pods. These logs are stored in /tmp/ansible-operator/runner/ inside
operator pods and contain detailed information about operator reconciliation cycles.
"""

import io
import logging
import os
import re
import tarfile
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Optional, List, Callable, Tuple, Any

from kubernetes import client
from kubernetes.dynamic import DynamicClient
from kubernetes.stream import stream

logger = logging.getLogger(__name__)


def _stripAnsiCodes(text: str) -> str:
    """Remove ANSI escape codes from text.

    Args:
        text (str): Text potentially containing ANSI escape codes

    Returns:
        str: Text with ANSI codes removed
    """
    ansiEscape = re.compile(r"\x1B\[([0-9]{1,3}(;[0-9]{1,2})?)?[mGK]")
    return ansiEscape.sub("", text)


def _getTimestampFromFile(filePath: str) -> Optional[str]:
    """Convert file modification time to timestamp string.

    Args:
        filePath (str): Path to file

    Returns:
        str: Timestamp in format YYYYMMDD-HHMMSS, or None if file doesn't exist
    """
    try:
        mtime = os.path.getmtime(filePath)
        return datetime.fromtimestamp(mtime).strftime("%Y%m%d-%H%M%S")
    except (OSError, FileNotFoundError):
        return None


def _findPodByLabel(dynClient: DynamicClient, namespace: str, labelSelector: str, labelValue: str) -> Optional[Any]:
    """Find first pod matching label selector.

    Args:
        dynClient (DynamicClient): Kubernetes dynamic client
        namespace (str): Namespace to search in
        labelSelector (str): Label key to match
        labelValue (str): Label value to match

    Returns:
        Optional[Any]: Pod object or None if not found
    """
    try:
        api = dynClient.resources.get(api_version="v1", kind="Pod")
        pods = api.get(namespace=namespace, label_selector=f"{labelSelector}={labelValue}")
        if pods.items:
            return pods.items[0]
        return None
    except Exception as e:
        logger.warning(f"Error finding pod with label {labelSelector}={labelValue}: {e}")
        return None


def _findReconcileLogFiles(coreV1Api: client.CoreV1Api, namespace: str, podName: str) -> list[str]:
    """Find reconcile log files in operator pod.

    Args:
        coreV1Api (CoreV1Api): Kubernetes core API client
        namespace (str): Pod namespace
        podName (str): Pod name

    Returns:
        list[str]: List of log file paths in pod
    """
    try:
        execCommand = ["find", "/tmp/ansible-operator/runner/", "-name", "stdout"]
        resp = stream(
            coreV1Api.connect_get_namespaced_pod_exec,
            podName,
            namespace,
            command=execCommand,
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False,
        )
        if resp:
            return [line.strip() for line in resp.strip().split("\n") if line.strip()]
        return []
    except Exception as e:
        logger.warning(f"Error finding reconcile log files in pod {podName}: {e}")
        return []


def _createTarArchive(coreV1Api: client.CoreV1Api, namespace: str, podName: str, logFiles: list[str]) -> Optional[bytes]:
    """Create tar.gz archive of log files from pod.

    Args:
        coreV1Api (CoreV1Api): Kubernetes core API client
        namespace (str): Pod namespace
        podName (str): Pod name
        logFiles (list[str]): List of log file paths to archive

    Returns:
        bytes: Tar.gz archive data, or None on error
    """
    try:
        # Build tar command with all log files
        tarCommand = ["tar", "-czf", "-"] + logFiles
        resp = stream(
            coreV1Api.connect_get_namespaced_pod_exec,
            podName,
            namespace,
            command=tarCommand,
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False,
            _preload_content=False,
        )

        # Handle both real stream objects and mocked bytes (for testing)
        if isinstance(resp, bytes):
            return resp if resp else None

        # Read binary data from stream
        tarData = b""
        while resp.is_open():
            resp.update(timeout=1)
            if resp.peek_stdout():
                tarData += resp.read_stdout()
            if resp.peek_stderr():
                stderr = resp.read_stderr()
                if stderr:
                    logger.debug(f"Tar stderr: {stderr}")

        return tarData if tarData else None
    except Exception as e:
        logger.warning(f"Error creating tar archive in pod {podName}: {e}")
        return None


def _extractAndOrganizeLogs(tarData: bytes, namespace: str, outputDir: str) -> bool:
    """Extract tar archive and organize logs by kind/instance/timestamp.

    The tar archive contains logs in structure:
    /tmp/ansible-operator/runner/{api}/{version}/{kind}/{namespace}/{instance}/artifacts/{reconcile_id}/stdout

    Output structure:
    {outputDir}/reconcile-logs/{namespace}/{kind}/{instance}/{timestamp}.log

    Args:
        tarData (bytes): Tar.gz archive data
        namespace (str): Namespace being collected
        outputDir (str): Base output directory

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with tarfile.open(fileobj=io.BytesIO(tarData), mode="r:gz") as tar:
            # Extract to temporary directory
            with tempfile.TemporaryDirectory() as tmpDir:
                tar.extractall(path=tmpDir, filter="data")

                # Walk through extracted structure
                runnerPath = os.path.join(tmpDir, "tmp", "ansible-operator", "runner")
                if not os.path.exists(runnerPath):
                    logger.warning("No ansible-operator runner directory found in archive")
                    return False

                # Process each API directory
                for apiDir in os.listdir(runnerPath):
                    apiPath = os.path.join(runnerPath, apiDir)
                    if not os.path.isdir(apiPath):
                        continue

                    # Process each version directory
                    for versionDir in os.listdir(apiPath):
                        versionPath = os.path.join(apiPath, versionDir)
                        if not os.path.isdir(versionPath):
                            continue

                        # Process each kind directory
                        for kindDir in os.listdir(versionPath):
                            kindPath = os.path.join(versionPath, kindDir)
                            if not os.path.isdir(kindPath):
                                continue

                            # Use lowercase kind name for output directory
                            kindLower = kindDir.lower()

                            # Process each namespace directory
                            for nsDir in os.listdir(kindPath):
                                nsPath = os.path.join(kindPath, nsDir)
                                if not os.path.isdir(nsPath):
                                    continue

                                # Process each instance directory
                                for instanceDir in os.listdir(nsPath):
                                    instancePath = os.path.join(nsPath, instanceDir)
                                    if not os.path.isdir(instancePath):
                                        continue

                                    # Create output directory for this instance
                                    outputInstanceDir = os.path.join(outputDir, "reconcile-logs", namespace, kindLower, instanceDir)
                                    os.makedirs(outputInstanceDir, exist_ok=True)

                                    # Process artifacts directory
                                    artifactsPath = os.path.join(instancePath, "artifacts")
                                    if not os.path.exists(artifactsPath):
                                        continue

                                    # Process each reconcile run
                                    for reconcileId in os.listdir(artifactsPath):
                                        reconcilePath = os.path.join(artifactsPath, reconcileId)
                                        stdoutPath = os.path.join(reconcilePath, "stdout")

                                        if os.path.isfile(stdoutPath):
                                            # Get timestamp from file
                                            timestamp = _getTimestampFromFile(stdoutPath)
                                            if not timestamp:
                                                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

                                            # Read log content and strip ANSI codes
                                            with open(stdoutPath, "r", errors="replace") as f:
                                                content = f.read()
                                            cleanContent = _stripAnsiCodes(content)

                                            # Write to output file
                                            outputLogPath = os.path.join(outputInstanceDir, f"{timestamp}.log")
                                            with open(outputLogPath, "w") as f:
                                                f.write(cleanContent)

                return True
    except Exception as e:
        logger.warning(f"Error extracting and organizing logs: {e}")
        return False


def collectReconcileLogs(
    dynClient: DynamicClient,
    namespace: str,
    labelSelector: str,
    labelValue: str,
    outputDir: str,
) -> bool:
    """Collect reconcile logs from operator pod.

    Finds operator pod by label selector, extracts reconcile logs from
    /tmp/ansible-operator/runner/, and organizes them by kind/instance/timestamp.

    Args:
        dynClient (DynamicClient): Kubernetes dynamic client
        namespace (str): Namespace containing operator pod
        labelSelector (str): Label key to identify operator pod
        labelValue (str): Label value to identify operator pod
        outputDir (str): Base output directory for must-gather

    Returns:
        bool: True if collection succeeded or gracefully handled, False on critical error
    """
    logger.info(f"Collecting reconcile logs from {namespace} with label {labelSelector}={labelValue}")

    # Find pod by label
    pod = _findPodByLabel(dynClient, namespace, labelSelector, labelValue)
    if not pod:
        logger.warning(f"No pods found with label {labelSelector}={labelValue} in namespace {namespace}")
        return True  # Graceful handling

    podName = pod.metadata.name
    logger.debug(f"Found pod: {podName}")

    # Create CoreV1Api client
    coreV1Api = client.CoreV1Api()

    # Find reconcile log files
    logFiles = _findReconcileLogFiles(coreV1Api, namespace, podName)
    if not logFiles:
        logger.info(f"No reconcile logs available in pod {podName}")
        return True  # Graceful handling

    logger.debug(f"Found {len(logFiles)} reconcile log files")

    # Create tar archive
    tarData = _createTarArchive(coreV1Api, namespace, podName, logFiles)
    if not tarData:
        logger.warning(f"Error creating tar archive in pod {podName}")
        return True  # Graceful handling

    logger.debug(f"Created tar archive ({len(tarData)} bytes)")

    # Extract and organize logs
    success = _extractAndOrganizeLogs(tarData, namespace, outputDir)
    if not success:
        logger.warning(f"Error extracting logs from pod {podName}")
        return True  # Graceful handling

    logger.info(f"Successfully collected reconcile logs from {podName}")
    return True


def collectReconcileLogsParallel(
    dynClient: DynamicClient,
    operators: List[Tuple[str, str, str]],
    outputDir: str,
    max_workers: int = 10,
    progressCallback: Optional[Callable[[int, int], None]] = None,
) -> bool:
    """Collect reconcile logs from multiple operators in parallel.

    Uses ThreadPoolExecutor to collect reconcile logs from multiple operator pods
    simultaneously, significantly reducing collection time for I/O-bound operations.

    Args:
        dynClient (DynamicClient): Kubernetes dynamic client
        operators (list): List of (namespace, labelSelector, labelValue) tuples
        outputDir (str): Base output directory for must-gather
        max_workers (int, optional): Maximum number of parallel threads. Defaults to 10.
        progressCallback (callable, optional): Callback function called with (completed, total) after each completion. Defaults to None.

    Returns:
        bool: True if all collections succeeded or gracefully handled, False on critical error
    """
    if not operators:
        logger.debug("No operators to collect reconcile logs from")
        return True

    total = len(operators)
    logger.info(f"Collecting reconcile logs from {total} operators in parallel (max_workers={max_workers})")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all collection tasks
        futures = {}
        for namespace, labelSelector, labelValue in operators:
            future = executor.submit(collectReconcileLogs, dynClient, namespace, labelSelector, labelValue, outputDir)
            futures[future] = (namespace, labelSelector, labelValue)

        # Process completed tasks
        completed = 0
        success = True
        for future in as_completed(futures):
            namespace, labelSelector, labelValue = futures[future]
            try:
                result = future.result()
                if not result:
                    success = False
                    logger.warning(f"Failed to collect reconcile logs from {namespace} with label {labelSelector}={labelValue}")
            except Exception as e:
                success = False
                logger.warning(f"Exception collecting reconcile logs from {namespace} with label {labelSelector}={labelValue}: {e}")

            completed += 1
            if progressCallback:
                progressCallback(completed, total)

    logger.info(f"Completed parallel reconcile logs collection: {completed}/{total} operators processed")
    return success


# Made with Bob
