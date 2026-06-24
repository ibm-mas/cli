# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Pod command execution utilities for must-gather."""

import json
import logging
from typing import Optional, Tuple, Dict, Any
from kubernetes import client
from kubernetes.stream import stream
from kubernetes.dynamic import DynamicClient

logger = logging.getLogger(__name__)


def execCommandInPod(
    dynClient: DynamicClient, namespace: str, podName: str, containerName: Optional[str], command: list, timeout: int = 30
) -> Tuple[bool, str, str]:
    """Execute a command in a pod container.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client
        namespace (str): Pod namespace
        podName (str): Pod name
        containerName (str, optional): Container name. If None, uses first container.
        command (list): Command to execute as list of strings
        timeout (int, optional): Command timeout in seconds. Defaults to 30.

    Returns:
        tuple: (success: bool, stdout: str, stderr: str)
    """
    try:
        coreV1 = client.CoreV1Api(dynClient.client)

        # Execute command
        execStream = stream(
            coreV1.connect_get_namespaced_pod_exec,
            podName,
            namespace,
            command=command,
            container=containerName,
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False,
            _preload_content=False,
        )

        stdout = ""
        stderr = ""

        # Read output with timeout
        try:
            while execStream.is_open():
                execStream.update(timeout=1)
                if execStream.peek_stdout():
                    stdout += execStream.read_stdout()
                if execStream.peek_stderr():
                    stderr += execStream.read_stderr()
        except Exception as e:
            logger.debug(f"Error reading stream from pod {podName}: {e}")
            return False, stdout, stderr
        finally:
            execStream.close()

        return True, stdout, stderr

    except Exception as e:
        logger.warning(f"Failed to execute command in pod {podName}: {e}")
        return False, "", str(e)


def execCurlInPod(
    dynClient: DynamicClient,
    namespace: str,
    podName: str,
    url: str,
    certPath: str,
    keyPath: str,
    caPath: str,
    containerName: Optional[str] = None,
    timeout: int = 30,
) -> Dict[str, Any]:
    """Execute a curl command in a pod and return parsed JSON response.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client
        namespace (str): Pod namespace
        podName (str): Pod name
        url (str): URL to curl
        certPath (str): Path to client certificate in pod
        keyPath (str): Path to client key in pod
        caPath (str): Path to CA certificate in pod
        containerName (str, optional): Container name. Defaults to None.
        timeout (int, optional): Command timeout in seconds. Defaults to 30.

    Returns:
        dict: Result with keys:
            - success (bool): Whether curl succeeded
            - json_data (dict): Parsed JSON response if successful
            - raw_response (str): Raw response text
            - error (str): Error message if failed
    """
    command = ["curl", "-s", "-X", "GET", url, "--cert", certPath, "--key", keyPath, "--cacert", caPath]

    success, stdout, stderr = execCommandInPod(
        dynClient=dynClient, namespace=namespace, podName=podName, containerName=containerName, command=command, timeout=timeout
    )

    result = {"success": success, "json_data": None, "raw_response": stdout, "error": stderr if not success else ""}

    if success and stdout:
        try:
            result["json_data"] = json.loads(stdout)
        except json.JSONDecodeError:
            result["success"] = False
            result["error"] = "Invalid JSON response"

    return result
