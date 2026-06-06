# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Pod collection utilities for must-gather."""

import os
import yaml
import logging
from typing import Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from kubernetes.dynamic import DynamicClient
from kubernetes.client import CoreV1Api

logger = logging.getLogger(__name__)


def collectPods(
    dynClient: DynamicClient,
    namespace: str,
    outputDir: str,
    podLogs: bool = False,
    noDetail: bool = False,
    max_workers: int = 10,
    progressCallback: Optional[Callable[[int, int], None]] = None,
) -> tuple[bool, int]:
    """Collect Kubernetes pods from a namespace with parallel processing.

    Collects pods with YAML and optionally container logs using parallel processing
    for improved performance. Organizes pods by app label into subdirectories.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        namespace (str): Target namespace for collection
        outputDir (str): Base output directory for collected pods
        podLogs (bool, optional): If True, collect container logs (current and previous). Defaults to False.
        noDetail (bool, optional): If True, skip YAML and logs collection. Defaults to False.
        max_workers (int, optional): Maximum number of parallel threads for pod processing. Defaults to 10.
        progressCallback (callable, optional): Callback function called with (completed, total) after each pod completion. Defaults to None.

    Returns:
        tuple[bool, int]: (success status, count of pods collected)
    """
    try:
        # Create resources directory
        resourcesDir = os.path.join(outputDir, "resources")
        os.makedirs(resourcesDir, exist_ok=True)

        # Create namespace directory
        namespaceDir = os.path.join(resourcesDir, namespace)
        os.makedirs(namespaceDir, exist_ok=True)

        # Create pods directory
        podsDir = os.path.join(namespaceDir, "pods")
        os.makedirs(podsDir, exist_ok=True)

        # Get API resource
        api = dynClient.resources.get(kind="Pod")

        # Collect pods
        pods = api.get(namespace=namespace)

        # Count pods
        podCount = len(pods.items) if hasattr(pods, "items") else 0

        # Generate summary file
        summaryFile = os.path.join(namespaceDir, "pods.md")
        _writeSummary(pods, summaryFile, namespace=namespace, podLogs=podLogs)

        # If no detail needed, we're done
        if noDetail:
            return (True, podCount)

        # Process pods in parallel
        totalPods = len(pods.items)
        completedPods = 0
        allSuccess = True

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all pod processing tasks
            futures = {}
            for pod in pods.items:
                future = executor.submit(
                    _processPod,
                    dynClient=dynClient,
                    namespace=namespace,
                    pod=pod,
                    podsDir=podsDir,
                    podLogs=podLogs,
                )
                futures[future] = pod.metadata.name

            # Process results as they complete
            for future in as_completed(futures):
                podName = futures[future]
                try:
                    success = future.result()
                    if not success:
                        allSuccess = False
                except Exception as e:
                    logger.error(f"Unexpected error processing pod {podName}: {e}")
                    allSuccess = False
                finally:
                    completedPods += 1
                    # Update progress callback if provided
                    if progressCallback is not None:
                        progressCallback(completedPods, totalPods)

        return (allSuccess, podCount)

    except Exception as e:
        logger.warning(f"Error collecting pods: {e}")
        return (False, 0)


def _processPod(dynClient: DynamicClient, namespace: str, pod, podsDir: str, podLogs: bool) -> bool:
    """Process a single pod: write YAML and collect logs.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client
        namespace (str): Pod namespace
        pod: ResourceInstance from Kubernetes API
        podsDir (str): Base pods directory
        podLogs (bool): Whether to collect logs

    Returns:
        bool: True if processing succeeded, False otherwise
    """
    try:
        podName = pod.metadata.name
        podDict = pod.to_dict()

        # Determine app label for organization
        appLabel = _extractAppLabel(pod, namespace)

        # Create app directory
        appDir = os.path.join(podsDir, appLabel)
        os.makedirs(appDir, exist_ok=True)

        # Write YAML
        yamlFile = os.path.join(appDir, f"{podName}.yaml")
        _writeYaml(podDict, yamlFile)

        # Collect logs if enabled
        if podLogs:
            _collectLogs(dynClient, namespace, podName, podDict, appDir)

        return True

    except Exception as e:
        logger.warning(f"Error processing pod {pod.metadata.name}: {e}")
        return False


def _writeSummary(pods, outputFile: str, namespace: str, podLogs: bool) -> None:
    """Write pod summary as a markdown table.

    Args:
        pods: ResourceList from Kubernetes API
        outputFile (str): Path to output file
        namespace (str): Namespace used to derive pod app grouping
        podLogs (bool): Whether pod logs are being collected
    """
    with open(outputFile, "w") as f:
        f.write("# Pods (v1)\n\n")

        if hasattr(pods, "items") and len(pods.items) > 0:
            f.write("| NAME | READY | STATUS | RESTARTS | LOGS |\n")
            f.write("| --- | --- | --- | --- | --- |\n")

            for pod in pods.items:
                name = pod.metadata.name
                podDict = pod.to_dict()
                status = podDict.get("status", {})
                appLabel = _extractAppLabel(pod, namespace)

                phase = status.get("phase", "Unknown")
                containerStatuses = status.get("containerStatuses", [])
                ready = f"{sum(1 for c in containerStatuses if c.get('ready', False))}/{len(containerStatuses)}" if containerStatuses else "0/0"
                restarts = str(sum(c.get("restartCount", 0) for c in containerStatuses))

                # First column: link to pod YAML
                nameLink = f"[{name}](pods/{appLabel}/{name}.yaml)"

                # Logs column: individual links for each container's log files
                logsLinks = []
                if podLogs and containerStatuses:
                    for containerStatus in containerStatuses:
                        containerName = containerStatus.get("name")
                        if containerName:
                            # Current log
                            logsLinks.append(f"[{containerName}](pods/{appLabel}/logs/{name}_{containerName}.log)")
                            # Previous log (if it exists, we'll create the link anyway)
                            # Note: We can't check if file exists here, but the link won't break if file is missing

                logsCell = "<br>".join(logsLinks) if logsLinks else ""

                f.write(f"| {nameLink} | {ready} | {phase} | {restarts} | {logsCell} |\n")
        else:
            f.write("No resources found.\n")


def _writeYaml(podDict: dict, outputFile: str) -> None:
    """Write pod as YAML file.

    Args:
        podDict (dict): Pod dictionary to write
        outputFile (str): Path to output file
    """
    with open(outputFile, "w") as f:
        yaml.dump(podDict, f, default_flow_style=False, sort_keys=False)


def _extractAppLabel(pod, namespace: str) -> str:
    """Extract app label from pod for organization.

    Prioritizes job-name label for job pods, then app label, then derives from pod name.

    Args:
        pod: ResourceInstance from Kubernetes API
        namespace (str): Pod namespace

    Returns:
        str: Job name, app label, or derived app name
    """
    podDict = pod.to_dict()
    labels = podDict.get("metadata", {}).get("labels", {})

    # First priority: job-name label (for job pods)
    if "job-name" in labels:
        return labels["job-name"]

    # Second priority: app label
    if "app" in labels:
        return labels["app"]

    # Fallback: derive from pod name
    podName = podDict.get("metadata", {}).get("name", "")

    # Extract instance ID from namespace (e.g., mas-inst1-core -> inst1)
    instanceId = namespace.split("-")[1] if len(namespace.split("-")) > 1 else ""

    # Remove hash suffixes from pod name
    parts = podName.split("-")
    if len(parts) > 2:
        # Remove last two parts (typically hash IDs)
        appName = "-".join(parts[:-2])
        # If app name equals instance ID, keep one more part
        if appName == instanceId and len(parts) > 3:
            appName = "-".join(parts[:-1])
        return appName
    else:
        return podName


def _collectLogs(dynClient: DynamicClient, namespace: str, podName: str, podDict: dict, appDir: str) -> None:
    """Collect container logs for a pod with parallel processing.

    Collects both current and previous logs for each container using parallel
    processing to improve performance when a pod has multiple containers.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client
        namespace (str): Pod namespace
        podName (str): Pod name
        podDict (dict): Pod dictionary
        appDir (str): App directory for log storage
    """
    try:
        # Create logs directory
        logsDir = os.path.join(appDir, "logs")
        os.makedirs(logsDir, exist_ok=True)

        # Get container names
        containerStatuses = podDict.get("status", {}).get("containerStatuses", [])

        # Collect logs for all containers in parallel
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for containerStatus in containerStatuses:
                containerName = containerStatus.get("name")
                if not containerName:
                    continue

                # Submit log collection tasks for this container
                future = executor.submit(
                    _collectContainerLogs,
                    dynClient=dynClient,
                    namespace=namespace,
                    podName=podName,
                    containerName=containerName,
                    logsDir=logsDir,
                )
                futures.append(future)

            # Wait for all log collections to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.debug(f"Error in container log collection: {e}")

    except Exception as e:
        logger.warning(f"Error collecting logs for pod {podName}: {e}")


def _collectContainerLogs(dynClient: DynamicClient, namespace: str, podName: str, containerName: str, logsDir: str) -> None:
    """Collect logs for a single container.

    Collects both current and previous logs for the specified container.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client
        namespace (str): Pod namespace
        podName (str): Pod name
        containerName (str): Container name
        logsDir (str): Directory for log storage
    """
    # Collect current logs
    try:
        coreV1 = CoreV1Api(dynClient.client)
        currentLogs = coreV1.read_namespaced_pod_log(name=podName, namespace=namespace, container=containerName)
        currentLogFile = os.path.join(logsDir, f"{podName}_{containerName}.log")
        with open(currentLogFile, "w") as f:
            f.write(currentLogs)
    except Exception as e:
        logger.debug(f"Could not collect current logs for {podName}/{containerName}: {e}")

    # Collect previous logs
    try:
        coreV1 = CoreV1Api(dynClient.client)
        previousLogs = coreV1.read_namespaced_pod_log(name=podName, namespace=namespace, container=containerName, previous=True)
        previousLogFile = os.path.join(logsDir, f"{podName}_{containerName}_prev.log")
        with open(previousLogFile, "w") as f:
            f.write(previousLogs)
    except Exception:
        # Previous logs may not exist, which is normal
        pass
