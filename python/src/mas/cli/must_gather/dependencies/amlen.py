# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Amlen Message Gateway diagnostic log collector.

This module collects diagnostic logs from IBM Amlen Message Gateway (mbgx) pods
running in a MAS messaging namespace. Logs are extracted from
/var/messagesight/diag/logs/ inside each mbgx-messagesight pod and saved
to the must-gather output directory.
"""

import logging
import os
import shutil
import tarfile
import tempfile
from typing import List

from kubernetes import client
from kubernetes.stream import stream

from mas.cli.must_gather.common.thread_safe_client import createThreadLocalDynamicClient

logger = logging.getLogger(__name__)

_AMLEN_LOG_DIR = "/var/messagesight/diag/logs/"
_AMLEN_LABEL_SELECTOR = "app=mbgx-messagesight"


def _findAmlenLogFiles(coreV1Api: client.CoreV1Api, namespace: str, podName: str) -> List[str]:
    """Find Amlen diagnostic log files inside an mbgx pod.

    Executes ``find /var/messagesight/diag/logs/ -name '*.log'`` inside the pod
    and returns the list of matching paths.

    Args:
        coreV1Api (CoreV1Api): Kubernetes core API client
        namespace (str): Pod namespace
        podName (str): Pod name

    Returns:
        list[str]: List of absolute log file paths inside the pod, empty if none found
    """
    try:
        resp = stream(
            coreV1Api.connect_get_namespaced_pod_exec,
            podName,
            namespace,
            command=["find", _AMLEN_LOG_DIR, "-name", "*.log"],
            stderr=False,
            stdin=False,
            stdout=True,
            tty=False,
        )
        if resp:
            return [line.strip() for line in resp.strip().split("\n") if line.strip()]
        return []
    except Exception as e:
        logger.warning(f"Error listing Amlen log files in pod {podName}: {e}")
        return []


def _downloadAndExtractAmlenLogs(coreV1Api: client.CoreV1Api, namespace: str, podName: str, logFiles: List[str], outputDir: str) -> bool:
    """Stream a tar archive of Amlen log files out of the pod and extract it.

    Creates a ``tar -czf -`` of the discovered log files inside the pod, streams
    the archive to a temporary file, extracts it, and then moves the ``*.log``
    files to ``{outputDir}/amlen-logs/{namespace}/{podName}/``.

    Args:
        coreV1Api (CoreV1Api): Kubernetes core API client
        namespace (str): Pod namespace
        podName (str): Pod name
        logFiles (list[str]): Log file paths to archive
        outputDir (str): Base must-gather output directory

    Returns:
        bool: True if extraction succeeded (even partially), False on failure
    """
    destDir = os.path.join(outputDir, "amlen-logs", namespace, podName)
    os.makedirs(destDir, exist_ok=True)

    tarCommand = ["tar", "-czf", "-"] + logFiles

    try:
        with tempfile.TemporaryFile(mode="w+b") as tarBuffer:
            try:
                execStream = stream(
                    coreV1Api.connect_get_namespaced_pod_exec,
                    podName,
                    namespace,
                    command=tarCommand,
                    stderr=False,
                    stdin=False,
                    stdout=True,
                    tty=False,
                    _preload_content=False,
                    binary=True,
                )
            except Exception as e:
                logger.warning(f"Failed to execute tar command in pod {podName}: {e}")
                return False

            try:
                while execStream.is_open():
                    execStream.update(timeout=1)
                    if execStream.peek_stdout():
                        tarBuffer.write(execStream.read_stdout())
            except Exception as e:
                logger.warning(f"Error reading tar stream from pod {podName}: {e}")
                return False
            finally:
                execStream.close()

            tarBuffer.flush()
            tarBuffer.seek(0)

            # Extract archive and flatten log files into destDir
            try:
                with tarfile.open(fileobj=tarBuffer, mode="r:gz") as tar:
                    with tempfile.TemporaryDirectory() as tmpDir:
                        try:
                            tar.extractall(path=tmpDir, filter="data")
                        except Exception as e:
                            logger.warning(f"Incomplete Amlen log archive from {podName}: {e}")

                        # Walk extracted tree and move *.log files to destDir
                        for dirpath, _dirnames, filenames in os.walk(tmpDir):
                            for fname in filenames:
                                if fname.endswith(".log"):
                                    src = os.path.join(dirpath, fname)
                                    dst = os.path.join(destDir, fname)
                                    shutil.copy2(src, dst)
            except tarfile.TarError as e:
                logger.warning(f"Failed to open tar archive from pod {podName}: {e}")
                return False

        return True

    except OSError as e:
        logger.warning(f"Failed to create temporary file for Amlen tar archive: {e}")
        return False


def collectAmlenLogs(namespace: str, outputDir: str) -> bool:
    """Collect diagnostic logs from all Amlen (mbgx) pods in a namespace.

    Discovers pods labelled ``app=mbgx-messagesight``, finds ``*.log`` files
    inside each pod's ``/var/messagesight/diag/logs/`` directory, and streams
    them out into ``{outputDir}/amlen-logs/{namespace}/{podName}/``.

    Args:
        namespace (str): Kubernetes namespace to search for mbgx pods
        outputDir (str): Base must-gather output directory

    Returns:
        bool: Always True (failures are logged but never propagated)
    """
    logger.info(f"📥 Collecting Amlen (mbgx) logs from namespace {namespace}")

    dynClient = createThreadLocalDynamicClient()
    podApi = dynClient.resources.get(api_version="v1", kind="Pod")

    try:
        pods = podApi.get(namespace=namespace, label_selector=_AMLEN_LABEL_SELECTOR)
    except Exception as e:
        logger.warning(f"⚠️ Failed to list mbgx pods in {namespace}: {e}")
        return True

    if not pods.items:
        logger.debug(f"No mbgx-messagesight pods found in {namespace}")
        return True

    coreV1Api = client.CoreV1Api(api_client=dynClient.client)

    for pod in pods.items:
        podName = pod.metadata.name
        logger.debug(f"  - Collecting mbgx logs from '{podName}'")

        logFiles = _findAmlenLogFiles(coreV1Api, namespace, podName)
        if not logFiles:
            logger.debug(f"    - No log files found in {podName}")
            continue

        success = _downloadAndExtractAmlenLogs(coreV1Api, namespace, podName, logFiles, outputDir)
        if success:
            logger.info(f"    ✅ Collected Amlen logs from {podName}")
        else:
            logger.warning(f"    ⚠️ Unable to get mbgx logs from {podName}")

    return True


def addAmlenToCollectionPlan(plan, namespace: str, outputDir: str) -> None:
    """Add Amlen log collection task for a messaging namespace to the collection plan.

    Args:
        plan (CollectionPlan): Collection plan to add tasks to
        namespace (str): Messaging namespace containing mbgx pods
        outputDir (str): Base must-gather output directory
    """
    tasks = [
        (
            "amlen_logs",
            collectAmlenLogs,
            namespace,
            outputDir,
        )
    ]
    plan.addGroup(namespace, tasks)
    logger.debug(f"✅ {namespace}: Added Amlen log collection task")


# Made with Bob
