# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Node resource collection with describe output."""

import os
import logging
from typing import List, Tuple, cast
from datetime import datetime
from kubernetes import client
from kubernetes.client.models import V1Lease
from mas.cli.must_gather.common.resources import collectResources
from mas.cli.must_gather.common.thread_safe_client import createThreadLocalDynamicClient

logger = logging.getLogger(__name__)


def collectNodes(outputDir: str) -> bool:
    """Collect node resources with describe output.

    Collects node information including both summary and detailed describe output
    for each node. The describe output provides comprehensive node information
    similar to 'kubectl describe node' command.

    Args:
        outputDir (str): Base output directory for collected resources

    Returns:
        bool: True if collection succeeded, False if errors occurred
    """
    # First collect standard YAML files
    success = collectResources(
        namespace=None,
        apiVersion="v1",
        kind="Node",
        outputDir=outputDir,
        allNamespaces=False,
    )

    if not success:
        return False

    # Now generate describe markdown files for each node
    try:
        dynClient = createThreadLocalDynamicClient()
        v1 = client.CoreV1Api(dynClient.client)
        coordinationV1 = client.CoordinationV1Api(dynClient.client)

        nodes = v1.list_node()
        nodesDir = os.path.join(outputDir, "resources", "_cluster", "nodes")

        for node in nodes.items:
            nodeName = node.metadata.name
            mdFile = os.path.join(nodesDir, f"{nodeName}.md")

            try:
                markdown = describeNode(node, v1, coordinationV1)
                with open(mdFile, "w") as f:
                    f.write(markdown)
                logger.debug(f"Generated describe output for node: {nodeName}")
            except Exception as e:
                logger.warning(f"Failed to generate describe output for node {nodeName}: {e}")

        return True

    except Exception as e:
        logger.warning(f"Failed to generate node describe outputs: {e}")
        return False


def describeNode(node, v1Api: client.CoreV1Api, coordinationV1Api: client.CoordinationV1Api) -> str:
    """Generate markdown description of a node similar to 'oc describe node'.

    Args:
        node: Node object from Kubernetes API
        v1Api: CoreV1Api client instance
        coordinationV1Api: CoordinationV1Api client instance

    Returns:
        str: Markdown formatted node description
    """
    lines = []
    nodeName = node.metadata.name

    # Header
    lines.append(f"# Node: {nodeName}\n")

    # Basic Information
    lines.append("## Basic Information\n")
    lines.append(f"**Name:** {nodeName}\n")

    # Roles
    roles = _extractRoles(node)
    lines.append(f"**Roles:** {roles}\n")

    # Labels
    lines.append("\n### Labels\n")
    if node.metadata.labels:
        for key, value in sorted(node.metadata.labels.items()):
            lines.append(f"- `{key}={value}`\n")
    else:
        lines.append("*No labels*\n")

    # Annotations
    lines.append("\n### Annotations\n")
    if node.metadata.annotations:
        for key, value in sorted(node.metadata.annotations.items()):
            lines.append(f"- `{key}: {value}`\n")
    else:
        lines.append("*No annotations*\n")

    # Creation Timestamp
    creationTime = node.metadata.creation_timestamp
    lines.append(f"\n**Creation Timestamp:** {_formatTimestamp(creationTime)}\n")

    # Taints
    lines.append("\n### Taints\n")
    if node.spec.taints:
        for taint in node.spec.taints:
            effect = taint.effect
            key = taint.key
            value = taint.value if taint.value else ""
            lines.append(f"- `{key}={value}:{effect}`\n")
    else:
        lines.append("*No taints*\n")

    # Unschedulable
    unschedulable = node.spec.unschedulable if node.spec.unschedulable else False
    lines.append(f"\n**Unschedulable:** {unschedulable}\n")

    # Lease Information
    lines.append("\n### Lease\n")
    try:
        lease = coordinationV1Api.read_namespaced_lease(name=nodeName, namespace="kube-node-lease")
        lease = cast(V1Lease, lease)  # Tell type checker this is V1Lease

        if lease.spec is None:
            lines.append("*Lease spec not available*\n")
        else:
            lines.append(f"**Holder Identity:** {lease.spec.holder_identity}\n")
            if lease.spec.acquire_time:
                lines.append(f"**Acquire Time:** {_formatTimestamp(lease.spec.acquire_time)}\n")
            else:
                lines.append("**Acquire Time:** *unset*\n")
            if lease.spec.renew_time:
                lines.append(f"**Renew Time:** {_formatTimestamp(lease.spec.renew_time)}\n")
    except Exception:
        lines.append("*Lease information not available*\n")

    # Conditions
    lines.append("\n## Conditions\n")
    lines.append("| Type | Status | Last Heartbeat | Last Transition | Reason | Message |\n")
    lines.append("| ---- | ------ | -------------- | --------------- | ------ | ------- |\n")
    if node.status.conditions:
        for condition in node.status.conditions:
            condType = condition.type
            status = condition.status
            lastHeartbeat = _formatTimestamp(condition.last_heartbeat_time) if condition.last_heartbeat_time else "N/A"
            lastTransition = _formatTimestamp(condition.last_transition_time) if condition.last_transition_time else "N/A"
            reason = condition.reason if condition.reason else ""
            message = condition.message.replace("|", "\\|") if condition.message else ""
            lines.append(f"| {condType} | {status} | {lastHeartbeat} | {lastTransition} | {reason} | {message} |\n")

    # Addresses
    lines.append("\n## Addresses\n")
    if node.status.addresses:
        for address in node.status.addresses:
            lines.append(f"- **{address.type}:** {address.address}\n")

    # Capacity and Allocatable
    lines.append("\n## Capacity\n")
    if node.status.capacity:
        for resource, quantity in sorted(node.status.capacity.items()):
            lines.append(f"- **{resource}:** {quantity}\n")

    lines.append("\n## Allocatable\n")
    if node.status.allocatable:
        for resource, quantity in sorted(node.status.allocatable.items()):
            lines.append(f"- **{resource}:** {quantity}\n")

    # System Info
    lines.append("\n## System Info\n")
    if node.status.node_info:
        info = node.status.node_info
        lines.append(f"- **Machine ID:** {info.machine_id}\n")
        lines.append(f"- **System UUID:** {info.system_uuid}\n")
        lines.append(f"- **Boot ID:** {info.boot_id}\n")
        lines.append(f"- **Kernel Version:** {info.kernel_version}\n")
        lines.append(f"- **OS Image:** {info.os_image}\n")
        lines.append(f"- **Operating System:** {info.operating_system}\n")
        lines.append(f"- **Architecture:** {info.architecture}\n")
        lines.append(f"- **Container Runtime Version:** {info.container_runtime_version}\n")
        lines.append(f"- **Kubelet Version:** {info.kubelet_version}\n")
        lines.append(f"- **Kube-Proxy Version:** {info.kube_proxy_version}\n")

    # Pod CIDR
    if hasattr(node.spec, "pod_cidr") and node.spec.pod_cidr:
        lines.append(f"\n**Pod CIDR:** {node.spec.pod_cidr}\n")
    if hasattr(node.spec, "pod_cidrs") and node.spec.pod_cidrs:
        lines.append(f"**Pod CIDRs:** {', '.join(node.spec.pod_cidrs)}\n")

    # Provider ID
    if node.spec.provider_id:
        lines.append(f"\n**Provider ID:** {node.spec.provider_id}\n")

    # Non-terminated Pods
    lines.append("\n## Non-terminated Pods\n")
    try:
        fieldSelector = f"spec.nodeName={nodeName},status.phase!=Succeeded,status.phase!=Failed"
        pods = v1Api.list_pod_for_all_namespaces(field_selector=fieldSelector)

        if pods.items:
            lines.append(f"\n**Total:** {len(pods.items)} pods\n\n")
            lines.append("| Namespace | Name | CPU Requests | CPU Limits | Memory Requests | Memory Limits | Age |\n")
            lines.append("| --------- | ---- | ------------ | ---------- | --------------- | ------------- | --- |\n")

            for pod in pods.items:
                namespace = pod.metadata.namespace
                name = pod.metadata.name
                cpuReq, cpuLim, memReq, memLim = _calculatePodResources(pod)
                age = _calculateAge(pod.metadata.creation_timestamp)

                # Calculate percentages
                cpuReqPct = _calculatePercentage(cpuReq, node.status.allocatable.get("cpu", "0"))
                cpuLimPct = _calculatePercentage(cpuLim, node.status.allocatable.get("cpu", "0"))
                memReqPct = _calculatePercentage(memReq, node.status.allocatable.get("memory", "0"))
                memLimPct = _calculatePercentage(memLim, node.status.allocatable.get("memory", "0"))

                cpuReqStr = f"{_formatResource(cpuReq, 'cpu')} ({cpuReqPct}%)"
                cpuLimStr = f"{_formatResource(cpuLim, 'cpu')} ({cpuLimPct}%)"
                memReqStr = f"{_formatResource(memReq, 'memory')} ({memReqPct}%)"
                memLimStr = f"{_formatResource(memLim, 'memory')} ({memLimPct}%)"

                lines.append(f"| {namespace} | {name} | {cpuReqStr} | {cpuLimStr} | {memReqStr} | {memLimStr} | {age} |\n")
        else:
            lines.append("\n*No non-terminated pods on this node*\n")

        # Allocated Resources Summary
        lines.append("\n## Allocated Resources\n")
        lines.append("\n*(Total limits may be over 100 percent, i.e., overcommitted.)*\n")

        totalCpuReq, totalCpuLim, totalMemReq, totalMemLim, totalEphemeralReq, totalEphemeralLim = _calculateTotalResources(pods.items)

        lines.append("\n| Resource | Requests | Limits |\n")
        lines.append("| -------- | -------- | ------ |\n")

        # CPU
        cpuAllocatable = _parseResource(node.status.allocatable.get("cpu", "0"), "cpu")
        cpuReqPct = (totalCpuReq / cpuAllocatable * 100) if cpuAllocatable > 0 else 0
        cpuLimPct = (totalCpuLim / cpuAllocatable * 100) if cpuAllocatable > 0 else 0
        lines.append(f"| cpu | {_formatResource(totalCpuReq, 'cpu')} ({cpuReqPct:.0f}%) | {_formatResource(totalCpuLim, 'cpu')} ({cpuLimPct:.0f}%) |\n")

        # Memory
        memAllocatable = _parseResource(node.status.allocatable.get("memory", "0"), "memory")
        memReqPct = (totalMemReq / memAllocatable * 100) if memAllocatable > 0 else 0
        memLimPct = (totalMemLim / memAllocatable * 100) if memAllocatable > 0 else 0
        lines.append(
            f"| memory | {_formatResource(totalMemReq, 'memory')} ({memReqPct:.0f}%) | {_formatResource(totalMemLim, 'memory')} ({memLimPct:.0f}%) |\n"
        )

        # Ephemeral Storage
        ephemeralAllocatable = _parseResource(node.status.allocatable.get("ephemeral-storage", "0"), "memory")
        ephemeralReqPct = (totalEphemeralReq / ephemeralAllocatable * 100) if ephemeralAllocatable > 0 else 0
        ephemeralLimPct = (totalEphemeralLim / ephemeralAllocatable * 100) if ephemeralAllocatable > 0 else 0
        lines.append(
            f"| ephemeral-storage | {_formatResource(totalEphemeralReq, 'memory')} ({ephemeralReqPct:.0f}%) | {_formatResource(totalEphemeralLim, 'memory')} ({ephemeralLimPct:.0f}%) |\n"
        )

        # Hugepages
        for resource in ["hugepages-1Gi", "hugepages-2Mi"]:
            if resource in node.status.allocatable:
                lines.append(f"| {resource} | 0 (0%) | 0 (0%) |\n")

    except Exception as e:
        lines.append(f"\n*Failed to retrieve pod information: {e}*\n")

    # Events
    lines.append("\n## Events\n")
    try:
        fieldSelector = f"involvedObject.name={nodeName},involvedObject.kind=Node"
        events = v1Api.list_event_for_all_namespaces(field_selector=fieldSelector)

        if events.items:
            # Sort by last timestamp
            sortedEvents = sorted(events.items, key=lambda e: e.last_timestamp or e.event_time or datetime.min, reverse=True)
            # Limit to most recent 10 events
            recentEvents = sortedEvents[:10]

            lines.append("\n| Type | Reason | Age | From | Message |\n")
            lines.append("| ---- | ------ | --- | ---- | -------- |\n")

            for event in recentEvents:
                eventType = event.type if event.type else "Normal"
                reason = event.reason if event.reason else ""
                age = _calculateAge(event.last_timestamp or event.event_time)
                source = event.source.component if event.source and event.source.component else ""
                message = event.message.replace("|", "\\|") if event.message else ""
                lines.append(f"| {eventType} | {reason} | {age} | {source} | {message} |\n")
        else:
            lines.append("\n*No events*\n")

    except Exception as e:
        lines.append(f"\n*Failed to retrieve events: {e}*\n")

    return "".join(lines)


def _extractRoles(node) -> str:
    """Extract node roles from labels.

    Args:
        node: Node object

    Returns:
        str: Comma-separated list of roles
    """
    roles = []
    if node.metadata.labels:
        for label in node.metadata.labels:
            if label.startswith("node-role.kubernetes.io/"):
                role = label.replace("node-role.kubernetes.io/", "")
                if role:
                    roles.append(role)
    return ",".join(roles) if roles else "<none>"


def _formatTimestamp(timestamp) -> str:
    """Format timestamp for display.

    Args:
        timestamp: Datetime object

    Returns:
        str: Formatted timestamp string
    """
    if not timestamp:
        return "N/A"
    return timestamp.strftime("%a, %d %b %Y %H:%M:%S %z")


def _calculateAge(creationTime) -> str:
    """Calculate age from creation timestamp.

    Args:
        creationTime: Creation timestamp

    Returns:
        str: Human-readable age string
    """
    if not creationTime:
        return "N/A"

    # Remove timezone info for calculation
    if creationTime.tzinfo:
        creationTime = creationTime.replace(tzinfo=None)

    now = datetime.utcnow()
    delta = now - creationTime

    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60

    if days > 0:
        return f"{days}d"
    elif hours > 0:
        return f"{hours}h"
    elif minutes > 0:
        return f"{minutes}m"
    else:
        return "<1m"


def _parseResource(resourceStr: str, resourceType: str) -> int:
    """Parse resource string to base units.

    Args:
        resourceStr: Resource string (e.g., "100m", "1Gi")
        resourceType: Type of resource ("cpu" or "memory")

    Returns:
        int: Resource in base units (millicores for CPU, bytes for memory)
    """
    if not resourceStr or resourceStr == "0":
        return 0

    if resourceType == "cpu":
        # Parse CPU (millicores)
        if resourceStr.endswith("m"):
            return int(resourceStr[:-1])
        else:
            return int(float(resourceStr) * 1000)
    else:
        # Parse memory/storage (bytes)
        units = {
            "Ki": 1024,
            "Mi": 1024**2,
            "Gi": 1024**3,
            "Ti": 1024**4,
            "Pi": 1024**5,
            "K": 1000,
            "M": 1000**2,
            "G": 1000**3,
            "T": 1000**4,
            "P": 1000**5,
        }

        for suffix, multiplier in units.items():
            if resourceStr.endswith(suffix):
                return int(resourceStr[: -len(suffix)]) * multiplier

        # No suffix, assume bytes
        return int(resourceStr)


def _formatResource(value: int, resourceType: str) -> str:
    """Format resource value for display.

    Args:
        value: Resource value in base units
        resourceType: Type of resource ("cpu" or "memory")

    Returns:
        str: Formatted resource string
    """
    if value == 0:
        return "0"

    if resourceType == "cpu":
        # Format CPU
        if value >= 1000:
            return f"{value // 1000}"
        else:
            return f"{value}m"
    else:
        # Format memory/storage
        if value >= 1024**3:
            return f"{value // (1024**3)}Gi"
        elif value >= 1024**2:
            return f"{value // (1024**2)}Mi"
        elif value >= 1024:
            return f"{value // 1024}Ki"
        else:
            return str(value)


def _calculatePercentage(value: int, allocatableStr: str) -> int:
    """Calculate percentage of allocatable resource.

    Args:
        value: Resource value in base units
        allocatableStr: Allocatable resource string

    Returns:
        int: Percentage (0-100+)
    """
    resourceType = "cpu" if "m" in allocatableStr or allocatableStr.isdigit() else "memory"
    allocatable = _parseResource(allocatableStr, resourceType)

    if allocatable == 0:
        return 0

    return int((value / allocatable) * 100)


def _calculatePodResources(pod) -> Tuple[int, int, int, int]:
    """Calculate total resource requests and limits for a pod.

    Args:
        pod: Pod object

    Returns:
        Tuple[int, int, int, int]: (cpu_requests, cpu_limits, memory_requests, memory_limits)
    """
    cpuReq = 0
    cpuLim = 0
    memReq = 0
    memLim = 0

    if pod.spec.containers:
        for container in pod.spec.containers:
            if container.resources:
                if container.resources.requests:
                    cpuReq += _parseResource(container.resources.requests.get("cpu", "0"), "cpu")
                    memReq += _parseResource(container.resources.requests.get("memory", "0"), "memory")

                if container.resources.limits:
                    cpuLim += _parseResource(container.resources.limits.get("cpu", "0"), "cpu")
                    memLim += _parseResource(container.resources.limits.get("memory", "0"), "memory")

    return cpuReq, cpuLim, memReq, memLim


def _calculateTotalResources(pods: List) -> Tuple[int, int, int, int, int, int]:
    """Calculate total resource requests and limits across all pods.

    Args:
        pods: List of pod objects

    Returns:
        Tuple: (cpu_req, cpu_lim, mem_req, mem_lim, ephemeral_req, ephemeral_lim)
    """
    totalCpuReq = 0
    totalCpuLim = 0
    totalMemReq = 0
    totalMemLim = 0
    totalEphemeralReq = 0
    totalEphemeralLim = 0

    for pod in pods:
        if pod.spec.containers:
            for container in pod.spec.containers:
                if container.resources:
                    if container.resources.requests:
                        totalCpuReq += _parseResource(container.resources.requests.get("cpu", "0"), "cpu")
                        totalMemReq += _parseResource(container.resources.requests.get("memory", "0"), "memory")
                        totalEphemeralReq += _parseResource(container.resources.requests.get("ephemeral-storage", "0"), "memory")

                    if container.resources.limits:
                        totalCpuLim += _parseResource(container.resources.limits.get("cpu", "0"), "cpu")
                        totalMemLim += _parseResource(container.resources.limits.get("memory", "0"), "memory")
                        totalEphemeralLim += _parseResource(container.resources.limits.get("ephemeral-storage", "0"), "memory")

    return totalCpuReq, totalCpuLim, totalMemReq, totalMemLim, totalEphemeralReq, totalEphemeralLim


# Made with Bob
