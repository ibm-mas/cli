# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""MAS Facilities collector for must-gather.

This module provides functionality to collect Facilities-specific logs from
pods running in the Facilities namespace. Logs are extracted from
/home/wiotp/log/ inside each Facilities pod and saved to the must-gather
output directory.
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

_FACILITIES_LOG_DIR = "/home/wiotp/log"
_FACILITIES_APP_TYPES = ["dwfagent", "appserver", "agent"]


def _findFacilitiesLogFiles(coreV1Api: client.CoreV1Api, namespace: str, podName: str) -> List[str]:
    """Find log files inside a Facilities pod at /home/wiotp/log.

    Executes ``find /home/wiotp/log -type f`` inside the pod and returns the
    list of matching paths.

    """
    try:
        resp = stream(
            coreV1Api.connect_get_namespaced_pod_exec,
            podName,
            namespace,
            command=["find", _FACILITIES_LOG_DIR, "-type", "f"],
            stderr=False,
            stdin=False,
            stdout=True,
            tty=False,
        )
        if resp:
            return [line.strip() for line in resp.strip().split("\n") if line.strip()]
        return []
    except Exception as e:
        logger.warning(f"Error listing Facilities log files in pod {podName}: {e}")
        return []


def _downloadAndExtractFacilitiesLogs(coreV1Api: client.CoreV1Api, namespace: str, podName: str, logFiles: List[str], outputDir: str) -> bool:
    """Stream a tar archive of Facilities log files out of the pod and extract it.

    Creates a ``tar -czf -`` of the discovered log files inside the pod, streams
    the archive to a temporary file, extracts it, and moves the files to
    ``{outputDir}/facilities-logs/{namespace}/{podName}/``.

    """
    destDir = os.path.join(outputDir, "facilities-logs", namespace, podName)
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

            try:
                with tarfile.open(fileobj=tarBuffer, mode="r:gz") as tar:
                    with tempfile.TemporaryDirectory() as tmpDir:
                        try:
                            tar.extractall(path=tmpDir, filter="data")
                        except Exception as e:
                            logger.warning(f"Incomplete Facilities log archive from {podName}: {e}")

                        # Walk extracted tree and copy all files flat into destDir
                        for dirpath, _dirnames, filenames in os.walk(tmpDir):
                            for fname in filenames:
                                src = os.path.join(dirpath, fname)
                                dst = os.path.join(destDir, fname)
                                shutil.copy2(src, dst)
            except tarfile.TarError as e:
                logger.warning(f"Failed to open tar archive from pod {podName}: {e}")
                return False

        return True

    except OSError as e:
        logger.warning(f"Failed to create temporary file for Facilities tar archive: {e}")
        return False


def collectFacilitiesLogs(namespace: str, outputDir: str) -> bool:
    """Collect logs from Facilities pods at /home/wiotp/log.

    Discovers pods with label ``mas.ibm.com/appType`` set to one of
    ``dwfagent``, ``appserver``, or ``agent``, finds all files inside each
    pod's ``/home/wiotp/log/`` directory, and streams them out into
    ``{outputDir}/facilities-logs/{namespace}/{podName}/``.

    """
    logger.info(f"📥 Collecting Facilities logs from namespace {namespace}")

    dynClient = createThreadLocalDynamicClient()
    podApi = dynClient.resources.get(api_version="v1", kind="Pod")
    coreV1Api = client.CoreV1Api(api_client=dynClient.client)

    # Collect pods across all target appTypes, deduplicate by pod name
    seenPods = set()
    podsToProcess = []

    for appType in _FACILITIES_APP_TYPES:
        labelSelector = f"mas.ibm.com/appType={appType}"
        try:
            pods = podApi.get(namespace=namespace, label_selector=labelSelector)
        except Exception as e:
            logger.warning(f"Failed to list Facilities pods in {namespace} with label {labelSelector}: {e}")
            continue

        for pod in pods.items:
            podName = pod.metadata.name
            if podName not in seenPods:
                seenPods.add(podName)
                podsToProcess.append((podName, appType))

    if not podsToProcess:
        logger.debug(f"No Facilities pods found in {namespace} with appTypes {_FACILITIES_APP_TYPES}")
        return True

    for podName, appType in podsToProcess:
        logger.debug(f"  - Collecting Facilities logs from '{podName}' (appType={appType})")

        logFiles = _findFacilitiesLogFiles(coreV1Api, namespace, podName)
        if not logFiles:
            logger.debug(f"    - No log files found in {podName} at {_FACILITIES_LOG_DIR}")
            continue

        success = _downloadAndExtractFacilitiesLogs(coreV1Api, namespace, podName, logFiles, outputDir)
        if success:
            logger.info(f"Collected Facilities logs from {podName}")
        else:
            logger.warning(f"Unable to get Facilities logs from {podName}")

    return True
