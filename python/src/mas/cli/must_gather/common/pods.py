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
import json
import yaml
import logging
from typing import List, Tuple
from kubernetes.dynamic import DynamicClient
from kubernetes.client import CoreV1Api

logger = logging.getLogger(__name__)


def generatePodCollectionTasks(
    dynClient: DynamicClient,
    namespace: str,
    outputDir: str,
    podLogs: bool = False,
) -> List[Tuple]:
    """Generate individual collection tasks for each pod in a namespace.

    Discovers all pods in the namespace and creates a task for each pod
    that can be executed in parallel by the shared threadpool.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        namespace (str): Target namespace for collection
        outputDir (str): Base output directory for collected pods
        podLogs (bool, optional): If True, collect container logs. Defaults to False.

    Returns:
        list: List of task tuples in format (task_name, func, *args), one per pod
    """
    try:
        # Create directories
        resourcesDir = os.path.join(outputDir, "resources")
        os.makedirs(resourcesDir, exist_ok=True)
        namespaceDir = os.path.join(resourcesDir, namespace)
        os.makedirs(namespaceDir, exist_ok=True)
        podsDir = os.path.join(namespaceDir, "pods")
        os.makedirs(podsDir, exist_ok=True)

        # Use CoreV1Api to list pods with raw JSON response (preserves Kubernetes field names)
        coreV1 = CoreV1Api(dynClient.client)
        rawResponse = coreV1.list_namespaced_pod(namespace=namespace, _preload_content=False)
        rawJson = rawResponse.data
        podListDict = json.loads(rawJson)

        # Generate summary file
        _writeSummary(podListDict, os.path.join(namespaceDir, "pods.md"), namespace=namespace, podLogs=podLogs)

        # Generate one task per pod
        tasks = []
        podItems = podListDict.get("items", [])
        for podDict in podItems:
            podName = podDict.get("metadata", {}).get("name", "unknown")
            # Add apiVersion and kind (omitted from list items by Kubernetes API)
            if "apiVersion" not in podDict:
                podDict["apiVersion"] = "v1"
            if "kind" not in podDict:
                podDict["kind"] = "Pod"
            tasks.append(
                (
                    f"pod_{podName}",
                    _processPod,
                    dynClient,
                    namespace,
                    podName,
                    podDict,
                    podsDir,
                    podLogs,
                )
            )

        logger.debug(f"Generated {len(tasks)} pod collection tasks for namespace {namespace} ({'with' if podLogs else 'without'} logs)")
        return tasks

    except Exception as e:
        logger.error(f"❌ Error generating pod collection tasks for {namespace}: {e}")
        return []


def _processPod(dynClient: DynamicClient, namespace: str, podName: str, podDict: dict, podsDir: str, podLogs: bool) -> bool:
    """Process a single pod: write YAML and collect logs.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client
        namespace (str): Pod namespace
        podName (str): Pod name
        podDict (dict): Pod dictionary with full status information
        podsDir (str): Base pods directory
        podLogs (bool): Whether to collect logs

    Returns:
        bool: True if processing succeeded, False otherwise
    """
    try:
        logger.debug(f"{namespace}: Processing pod {podName} (podLogs={podLogs})")

        # Determine app label for organization
        appLabel = _extractAppLabel(podDict, namespace)
        logger.debug(f"{namespace}: Pod {podName} app label: {appLabel}")

        # Create app directory
        appDir = os.path.join(podsDir, appLabel)
        os.makedirs(appDir, exist_ok=True)

        # Write YAML
        yamlFile = os.path.join(appDir, f"{podName}.yaml")
        _writeYaml(podDict, yamlFile)
        logger.debug(f"{namespace}: Wrote YAML for pod {podName}")

        # Collect logs if enabled
        if podLogs:
            logger.debug(f"{namespace}: Collecting logs for pod {podName}")
            _collectLogs(dynClient, namespace, podName, podDict, appDir)
        else:
            logger.debug(f"{namespace}: Skipping log collection for pod {podName} (podLogs=False)")

        return True

    except Exception as e:
        logger.error(f"{namespace}: Error processing pod {podName}: {e}", exc_info=True)
        return False


def _writeSummary(podListDict: dict, outputFile: str, namespace: str, podLogs: bool) -> None:
    """Write pod summary as a markdown table.

    Args:
        podListDict (dict): Pod list dictionary from Kubernetes API (raw JSON)
        outputFile (str): Path to output file
        namespace (str): Namespace used to derive pod app grouping
        podLogs (bool): Whether pod logs are being collected
    """
    with open(outputFile, "w") as f:
        f.write("# Pods (v1)\n\n")

        items = podListDict.get("items", [])
        if len(items) > 0:
            f.write("| NAME | READY | STATUS | RESTARTS | LOGS |\n")
            f.write("| --- | --- | --- | --- | --- |\n")

            for podDict in items:
                metadata = podDict.get("metadata", {})
                name = metadata.get("name", "")
                status = podDict.get("status", {})
                appLabel = _extractAppLabel(podDict, namespace)

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


def _extractAppLabel(podDict: dict, namespace: str) -> str:
    """Extract app label from pod for organization.

    Prioritizes job-name label for job pods, then app label, then derives from pod name.

    Args:
        podDict (dict): Pod dictionary
        namespace (str): Pod namespace

    Returns:
        str: Job name, app label, or derived app name
    """
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
    """Collect container logs for a pod.

    Collects both current and previous logs for each container sequentially.
    Since pods are already processed in parallel by the main threadpool,
    we don't need nested parallelism for containers.

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
        if not containerStatuses:
            logger.warning(f"⚠️ {namespace}: Pod {podName} has no containerStatuses - cannot collect logs")
            return

        # Collect logs for all containers sequentially
        for containerStatus in containerStatuses:
            containerName = containerStatus.get("name")
            if not containerName:
                logger.warning(f"⚠️ {namespace}: Container status missing name in pod {podName}")
                continue

            # Collect logs for this container
            _collectContainerLogs(
                dynClient=dynClient,
                namespace=namespace,
                podName=podName,
                containerName=containerName,
                logsDir=logsDir,
            )

    except Exception as e:
        logger.error(f"❌ {namespace}: Error collecting logs for pod {podName}: {e}", exc_info=True)


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
    coreV1 = CoreV1Api(dynClient.client)
    try:
        currentLogs = coreV1.read_namespaced_pod_log(name=podName, namespace=namespace, container=containerName)
        currentLogFile = os.path.join(logsDir, f"{podName}_{containerName}.log")
        with open(currentLogFile, "w") as f:
            f.write(currentLogs)
        logger.info(f"✅ {namespace}: Collected current logs for {podName}/{containerName} ({len(currentLogs)} bytes)")
    except Exception as e:
        logger.warning(f"⚠️ {namespace}: Could not collect current logs for {podName}/{containerName}: {e}")

    # Collect previous logs
    try:
        previousLogs = coreV1.read_namespaced_pod_log(name=podName, namespace=namespace, container=containerName, previous=True)
        previousLogFile = os.path.join(logsDir, f"{podName}_{containerName}_prev.log")
        with open(previousLogFile, "w") as f:
            f.write(previousLogs)
        logger.info(f"✅ {namespace}: Collected previous logs for {podName}/{containerName} ({len(previousLogs)} bytes)")
    except Exception:
        # Previous logs may not exist, which is normal
        pass
