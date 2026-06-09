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

import logging
import os
import re
import tarfile
import tempfile
from datetime import datetime
from typing import Optional, List, Tuple, Any

from kubernetes import client
from kubernetes.stream import stream

from .thread_safe_client import createThreadLocalDynamicClient

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


def _findPodByLabel(namespace: str, labelSelector: str, labelValue: str) -> Optional[Any]:
    """Find first pod matching label selector.

    Args:
        namespace (str): Namespace to search in
        labelSelector (str): Label key to match
        labelValue (str): Label value to match

    Returns:
        Optional[Any]: Pod object or None if not found
    """
    try:
        # Create thread-local DynamicClient for thread-safety
        dynClient = createThreadLocalDynamicClient()
        api = dynClient.resources.get(api_version="v1", kind="Pod")
        pods = api.get(namespace=namespace, label_selector=f"{labelSelector}={labelValue}")
        if pods.items:
            return pods.items[0]
        return None
    except Exception as e:
        logger.warning(f"Error finding pod with label {labelSelector}={labelValue} in namespace {namespace}: {type(e).__name__}: {e}", exc_info=True)
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


def _extractAndOrganizeTarBuffer(tarBuffer: Any, namespace: str, podName: str, outputDir: str) -> bool:
    """Extract tar buffer and organize logs by kind/instance/timestamp.

    The tar archive contains logs in structure:
    /tmp/ansible-operator/runner/{api}/{version}/{kind}/{namespace}/{instance}/artifacts/{reconcile_id}/stdout

    Output structure:
    {outputDir}/reconcile-logs/{namespace}/{kind}/{instance}/{timestamp}.log

    Args:
        tarBuffer: File-like object containing tar.gz data
        namespace (str): Namespace being collected
        podName (str): Pod name (for logging)
        outputDir (str): Base output directory

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with tarfile.open(fileobj=tarBuffer, mode="r:gz") as tar:
            # Extract to temporary directory first
            with tempfile.TemporaryDirectory() as tmpDir:
                try:
                    tar.extractall(path=tmpDir, filter="data")
                except Exception as e:
                    logger.warning(f"Failed to extract tar archive from pod {podName}: {e}")
                    return False

                # Walk through extracted structure
                runnerPath = os.path.join(tmpDir, "tmp", "ansible-operator", "runner")
                if not os.path.exists(runnerPath):
                    logger.debug(f"No ansible-operator runner directory found in archive from pod {podName}")
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
                                            try:
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
                                            except Exception as e:
                                                logger.warning(f"Failed to process log file {stdoutPath}: {e}")
                                                continue

                return True
    except tarfile.TarError as e:
        logger.warning(f"Failed to open tar archive from pod {podName}: {e}")
        return False


def _downloadAndExtractReconcileLogs(coreV1Api: client.CoreV1Api, namespace: str, podName: str, logFiles: list[str], outputDir: str) -> bool:
    """Download reconcile logs from pod and extract them to output directory.

    Creates a tar archive of log files in the pod, streams it to a temporary file,
    then extracts and organizes the logs by kind/instance/timestamp.

    Args:
        coreV1Api (CoreV1Api): Kubernetes core API client
        namespace (str): Pod namespace
        podName (str): Pod name
        logFiles (list[str]): List of log file paths to archive
        outputDir (str): Base output directory

    Returns:
        bool: True if successful, False otherwise
    """
    # Build tar command with all log files
    tarCommand = ["tar", "-czf", "-"] + logFiles

    try:
        # Use TemporaryFile in binary mode ('w+b')
        with tempfile.TemporaryFile(mode="w+b") as tarBuffer:
            # Execute the command
            try:
                execStream = stream(
                    coreV1Api.connect_get_namespaced_pod_exec,
                    podName,
                    namespace,
                    command=tarCommand,
                    stderr=True,
                    stdin=False,
                    stdout=True,
                    tty=False,
                    _preload_content=False,
                    binary=True,
                )
            except Exception as e:
                logger.warning(f"Failed to execute tar command in pod {podName}: {e}")
                return False

            # Read the output into the buffer
            try:
                while execStream.is_open():
                    execStream.update(timeout=1)
                    if execStream.peek_stdout():
                        out = execStream.read_stdout()
                        tarBuffer.write(out)
                    # The stderr from tar is not meaningfully useful, it mostly contains
                    # messages about "stripping leading / from member names"
                    # if execStream.peek_stderr():
                    #     stderr = execStream.read_stderr()
                    #     if stderr:
                    #         logger.debug(f"Tar stderr: {stderr}")
            except Exception as e:
                logger.warning(f"Error reading tar stream from pod {podName}: {e}")
                return False
            finally:
                execStream.close()

            tarBuffer.flush()
            tarBuffer.seek(0)

            # Extract and organize the logs
            return _extractAndOrganizeTarBuffer(tarBuffer, namespace, podName, outputDir)

    except OSError as e:
        logger.warning(f"Failed to create temporary file for tar archive: {e}")
        return False


def collectReconcileLogs(
    namespace: str,
    labelSelector: str,
    labelValue: str,
    outputDir: str,
) -> bool:
    """Collect reconcile logs from operator pod.

    Finds operator pod by label selector, extracts reconcile logs from
    /tmp/ansible-operator/runner/, and organizes them by kind/instance/timestamp.

    Args:
        namespace (str): Namespace containing operator pod
        labelSelector (str): Label key to identify operator pod
        labelValue (str): Label value to identify operator pod
        outputDir (str): Base output directory for must-gather

    Returns:
        bool: True if collection succeeded or gracefully handled, False on critical error
    """
    logger.info(f"📥 Collecting reconcile logs from {namespace} with label {labelSelector}={labelValue}")

    # Find pod by label
    pod = _findPodByLabel(namespace, labelSelector, labelValue)
    if not pod:
        logger.warning(f"⚠️ No pods found with label {labelSelector}={labelValue} in namespace {namespace}")
        return True  # Graceful handling

    podName = pod.metadata.name
    logger.debug(f"Found pod: {podName}")

    # Create thread-local CoreV1Api client for thread-safety
    dynClient = createThreadLocalDynamicClient()
    coreV1Api = client.CoreV1Api(api_client=dynClient.client)

    # Find reconcile log files
    logFiles = _findReconcileLogFiles(coreV1Api, namespace, podName)
    if not logFiles:
        logger.debug(f"No reconcile logs available in pod {podName}")
        return True  # Graceful handling

    logger.debug(f"Found {len(logFiles)} reconcile log files")

    # Download and extract logs directly to output directory
    success = _downloadAndExtractReconcileLogs(coreV1Api, namespace, podName, logFiles, outputDir)
    if not success:
        logger.error(f"❌ Error downloading and extracting logs from pod {podName}")
        return True  # Graceful handling

    logger.info(f"✅ Successfully collected reconcile logs from {podName}")
    return True


def generateReconcileLogsCollectionTasks(operators: List[Tuple[str, str, str]], outputDir: str) -> List[Tuple]:
    """Generate collection tasks for reconcile logs from multiple operators.

    Creates individual tasks for each operator that will be executed by the
    shared threadpool, eliminating nested parallelism.

    Args:
        operators (list): List of (namespace, labelSelector, labelValue) tuples
        outputDir (str): Base output directory for must-gather

    Returns:
        list: List of task tuples (task_name, func, namespace, labelSelector, labelValue, outputDir)
    """
    tasks = []
    for namespace, labelSelector, labelValue in operators:
        taskName = f"reconcile_logs_{namespace}_{labelSelector}_{labelValue}"
        tasks.append((taskName, collectReconcileLogs, namespace, labelSelector, labelValue, outputDir))
    return tasks


# Made with Bob
