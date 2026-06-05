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
from kubernetes.dynamic import DynamicClient
from kubernetes.client import CoreV1Api

logger = logging.getLogger(__name__)


def collectPods(dynClient: DynamicClient, namespace: str, outputDir: str, podLogs: bool = False, noDetail: bool = False) -> bool:
    """Collect Kubernetes pods from a namespace.

    Collects pods with describe output, YAML, and optionally container logs.
    Organizes pods by app label into subdirectories.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        namespace (str): Target namespace for collection
        outputDir (str): Base output directory for collected pods
        podLogs (bool, optional): If True, collect container logs (current and previous). Defaults to False.
        noDetail (bool, optional): If True, skip YAML and logs collection. Defaults to False.

    Returns:
        bool: True if collection succeeded, False if errors occurred
    """
    try:
        # Create namespace directory
        namespaceDir = os.path.join(outputDir, namespace)
        os.makedirs(namespaceDir, exist_ok=True)

        # Create pods directory
        podsDir = os.path.join(namespaceDir, "pods")
        os.makedirs(podsDir, exist_ok=True)

        # Get API resource
        api = dynClient.resources.get(kind="Pod")

        # Collect pods
        pods = api.get(namespace=namespace)

        # Generate summary file
        summaryFile = os.path.join(namespaceDir, "pods.txt")
        _writeSummary(pods, summaryFile)

        # Process each pod
        for pod in pods.items:
            podName = pod.metadata.name
            podDict = pod.to_dict()

            # Determine app label for organization
            appLabel = _extractAppLabel(pod, namespace)

            # Create app directory
            appDir = os.path.join(podsDir, appLabel)
            os.makedirs(appDir, exist_ok=True)

            # Write describe output
            describeFile = os.path.join(appDir, f"{podName}.txt")
            _writeDescribe(pod, describeFile)

            # Write YAML if detail enabled
            if not noDetail:
                yamlFile = os.path.join(appDir, f"{podName}.yaml")
                _writeYaml(podDict, yamlFile)

                # Collect logs if enabled
                if podLogs:
                    _collectLogs(dynClient, namespace, podName, podDict, appDir)

        return True

    except Exception as e:
        logger.warning(f"Error collecting pods: {e}")
        return False


def _writeSummary(pods, outputFile: str) -> None:
    """Write pod summary in wide format.

    Args:
        pods: ResourceList from Kubernetes API
        outputFile (str): Path to output file
    """
    with open(outputFile, "w") as f:
        if hasattr(pods, "items") and len(pods.items) > 0:
            # Write header
            f.write(f"{'NAME':<50} {'READY':<10} {'STATUS':<15} {'RESTARTS':<10} {'AGE':<10}\n")

            # Write each pod
            for pod in pods.items:
                name = pod.metadata.name
                podDict = pod.to_dict()
                status = podDict.get("status", {})

                # Extract status info
                phase = status.get("phase", "Unknown")
                containerStatuses = status.get("containerStatuses", [])
                ready = f"{sum(1 for c in containerStatuses if c.get('ready', False))}/{len(containerStatuses)}" if containerStatuses else "0/0"
                restarts = sum(c.get("restartCount", 0) for c in containerStatuses)

                f.write(f"{name:<50} {ready:<10} {phase:<15} {restarts:<10} {'':<10}\n")
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


def _writeDescribe(pod, outputFile: str) -> None:
    """Write pod describe output.

    Generates output similar to 'kubectl describe pod' command.

    Args:
        pod: ResourceInstance from Kubernetes API
        outputFile (str): Path to output file
    """
    with open(outputFile, "w") as f:
        podDict = pod.to_dict()

        # Write metadata section
        f.write("Name:         {}\n".format(podDict.get("metadata", {}).get("name", "")))
        f.write("Namespace:    {}\n".format(podDict.get("metadata", {}).get("namespace", "")))
        f.write("Labels:       {}\n".format(podDict.get("metadata", {}).get("labels", {})))
        f.write("Annotations:  {}\n".format(podDict.get("metadata", {}).get("annotations", {})))
        f.write("\n")

        # Write status section
        status = podDict.get("status", {})
        f.write("Status:       {}\n".format(status.get("phase", "Unknown")))
        f.write("IP:           {}\n".format(status.get("podIP", "")))
        f.write("\n")

        # Write containers section
        if "spec" in podDict and "containers" in podDict["spec"]:
            f.write("Containers:\n")
            for container in podDict["spec"]["containers"]:
                f.write(f"  {container.get('name', 'unknown')}:\n")
                f.write(f"    Image:  {container.get('image', '')}\n")

        # Write conditions
        if "conditions" in status:
            f.write("\nConditions:\n")
            for condition in status["conditions"]:
                f.write(f"  Type:    {condition.get('type', '')}\n")
                f.write(f"  Status:  {condition.get('status', '')}\n")


def _extractAppLabel(pod, namespace: str) -> str:
    """Extract app label from pod for organization.

    Falls back to deriving from pod name if no app label exists.

    Args:
        pod: ResourceInstance from Kubernetes API
        namespace (str): Pod namespace

    Returns:
        str: App label or derived app name
    """
    podDict = pod.to_dict()
    labels = podDict.get("metadata", {}).get("labels", {})

    # Try to get app label
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

    Collects both current and previous logs for each container.

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

        for containerStatus in containerStatuses:
            containerName = containerStatus.get("name")
            if not containerName:
                continue

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

    except Exception as e:
        logger.warning(f"Error collecting logs for pod {podName}: {e}")


# Made with Bob
