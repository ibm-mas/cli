# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Suite summarizer for must-gather."""

import os
import yaml
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from prettytable import PrettyTable, TableStyle


def _formatTimestamp(timestamp: str) -> str:
    """Format timestamp to consistent ISO 8601 format.

    Handles both Kubernetes creationTimestamp format (2026-01-15T10:30:00Z)
    and activation timestamp format which may vary.

    Args:
        timestamp (str): Timestamp string in various formats

    Returns:
        str: Formatted timestamp in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ) or original if parsing fails
    """
    if not timestamp or timestamp == "unknown":
        return ""

    try:
        # Try parsing ISO 8601 format with timezone offset
        if "+00:00" in timestamp or "-00:00" in timestamp:
            # Has timezone offset: 2026-04-22T20:26:06.490482+00:00
            dt = datetime.fromisoformat(timestamp.replace("+00:00", "+00:00"))
        elif "." in timestamp and timestamp.endswith("Z"):
            # Has microseconds with Z: 2026-01-15T10:30:00.123456Z
            dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
        elif timestamp.endswith("Z"):
            # No microseconds with Z: 2026-01-15T10:30:00Z
            dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
        else:
            # Try generic ISO format parsing
            dt = datetime.fromisoformat(timestamp)

        # Return in consistent format without microseconds
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, AttributeError):
        # Return original if parsing fails
        return timestamp


def _parseVersion(versionStr: str) -> Tuple[int, int, int]:
    """Parse version string into major, minor, patch tuple.

    Args:
        versionStr (str): Version string like "9.2.0-pre.dev" or "8.11.0"

    Returns:
        tuple: (major, minor, patch) as integers

    Raises:
        ValueError: If version string cannot be parsed
    """
    if not versionStr:
        raise ValueError("Version string is empty")

    # Remove any suffix like "-pre.dev"
    baseVersion = versionStr.split("-")[0]

    # Split into parts
    parts = baseVersion.split(".")
    if len(parts) < 2:
        raise ValueError(f"Invalid version format: {versionStr}")

    major = int(parts[0])
    minor = int(parts[1])
    patch = int(parts[2]) if len(parts) > 2 else 0

    return (major, minor, patch)


def _findMASInstances(resourcesDir: str) -> List[str]:
    """Find all MAS instance IDs from resource directories.

    Scans for directories matching pattern mas-{instance}-core and extracts
    the instance ID from the directory name.

    Args:
        resourcesDir (str): Path to resources directory

    Returns:
        list: List of MAS instance IDs found
    """
    instances = []

    if not os.path.exists(resourcesDir):
        return instances

    for entry in os.listdir(resourcesDir):
        if entry.startswith("mas-") and entry.endswith("-core"):
            # Extract instance ID from "mas-{instance}-core"
            instanceId = entry[4:-5]  # Remove "mas-" prefix and "-core" suffix
            instances.append(instanceId)

    return sorted(instances)


def _loadSuiteCR(outputDir: str, instanceId: str) -> Optional[Dict[str, Any]]:
    """Load Suite CR YAML for a MAS instance.

    Args:
        outputDir (str): Path to must-gather output directory
        instanceId (str): MAS instance ID

    Returns:
        dict: Suite CR data, or None if not found
    """
    suitePath = os.path.join(outputDir, "resources", f"mas-{instanceId}-core", "suites", f"{instanceId}.yaml")

    if not os.path.exists(suitePath):
        return None

    with open(suitePath, "r") as f:
        return yaml.safe_load(f)


def _getPodStatus(outputDir: str, namespace: str, podPrefixes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Get pod status information from collected pod YAML files.

    Reads pod YAML files matching specified prefixes and extracts
    pod name, container state, and path to pod YAML file.

    Args:
        outputDir (str): Path to must-gather output directory
        namespace (str): Namespace to scan for pods
        podPrefixes (list, optional): List of pod name prefixes to filter. If None, reads all pods.

    Returns:
        list: List of dicts with keys: name, state, filePath
    """
    podStatuses = []
    podsDir = os.path.join(outputDir, "resources", namespace, "pods")

    if not os.path.exists(podsDir):
        return podStatuses

    # Walk through all pod type directories
    for podType in os.listdir(podsDir):
        podTypeDir = os.path.join(podsDir, podType)
        if not os.path.isdir(podTypeDir):
            continue

        # Read pod YAML files
        for filename in os.listdir(podTypeDir):
            if not filename.endswith(".yaml"):
                continue

            # Filter by filename prefix if specified
            if podPrefixes:
                podNameWithoutExt = filename[:-5]  # Remove .yaml extension
                if not any(podNameWithoutExt.startswith(prefix) for prefix in podPrefixes):
                    continue

            podPath = os.path.join(podTypeDir, filename)
            relativePath = os.path.join("..", "resources", namespace, "pods", podType, filename)

            try:
                with open(podPath, "r") as f:
                    pod = yaml.safe_load(f)

                if not pod or "status" not in pod:
                    continue

                podName = pod["metadata"]["name"]

                # Extract container statuses
                if "containerStatuses" in pod["status"]:
                    for containerStatus in pod["status"]["containerStatuses"]:
                        state = containerStatus.get("state", {})
                        # State is a dict with one key: running, waiting, or terminated
                        stateType = list(state.keys())[0] if state else "unknown"

                        podStatuses.append({"name": podName, "state": stateType, "filePath": relativePath})
            except Exception:
                # Skip pods that can't be parsed
                continue

    return podStatuses


def _getActivatedApps(outputDir: str, instanceId: str) -> Dict[str, Dict[str, Any]]:
    """Get activated MAS applications with their status information.

    Checks for workspace CR directories and loads status from workspace CRs.

    Args:
        outputDir (str): Path to must-gather output directory
        instanceId (str): MAS instance ID

    Returns:
        dict: Dictionary mapping appId to status dict from workspace CR
    """
    apps = {}
    resourcesDir = os.path.join(outputDir, "resources")

    if not os.path.exists(resourcesDir):
        return apps

    # Known app IDs to check for
    knownApps = ["assist", "iot", "monitor", "manage", "optimizer", "predict", "visualinspection", "facilities"]

    for appId in knownApps:
        appNamespace = f"mas-{instanceId}-{appId}"
        appDir = os.path.join(resourcesDir, appNamespace)

        if os.path.exists(appDir) and os.path.isdir(appDir):
            # Check for workspace CR to confirm activation (plural form)
            workspaceCRKind = f"{appId}workspaces"
            if appId == "visualinspection":
                workspaceCRKind = "visualinspectionappworkspaces"

            workspaceDir = os.path.join(appDir, workspaceCRKind)
            if os.path.exists(workspaceDir):
                # Load workspace CR and extract status
                for filename in os.listdir(workspaceDir):
                    if filename.endswith(".yaml"):
                        workspacePath = os.path.join(workspaceDir, filename)
                        try:
                            with open(workspacePath, "r") as f:
                                workspaceCR = yaml.safe_load(f)
                                if workspaceCR and "status" in workspaceCR:
                                    apps[appId] = {
                                        "status": workspaceCR["status"],
                                        "workspaceFile": os.path.join("resources", appNamespace, workspaceCRKind, filename),
                                    }
                                    break
                        except Exception:
                            # Skip if can't load workspace CR
                            continue

    return apps


def _loadManageWorkspaceCR(outputDir: str, instanceId: str) -> Optional[Dict[str, Any]]:
    """Load ManageWorkspace CR if Manage is installed.

    Args:
        outputDir (str): Path to must-gather output directory
        instanceId (str): MAS instance ID

    Returns:
        dict: ManageWorkspace CR data, or None if not found
    """
    manageDir = os.path.join(outputDir, "resources", f"mas-{instanceId}-manage", "manageworkspaces")

    if not os.path.exists(manageDir):
        return None

    # Find the workspace CR file (should be only one)
    for filename in os.listdir(manageDir):
        if filename.endswith(".yaml"):
            workspacePath = os.path.join(manageDir, filename)
            with open(workspacePath, "r") as f:
                return yaml.safe_load(f)

    return None


def _getSCIMConfig(outputDir: str, instanceId: str) -> Optional[List[Dict[str, Any]]]:
    """Load SCIM configuration if configured.

    Args:
        outputDir (str): Path to must-gather output directory
        instanceId (str): MAS instance ID

    Returns:
        list: List of SCIM config CRs, or None if not configured
    """
    scimDir = os.path.join(outputDir, "resources", f"mas-{instanceId}-core", "scimcfg")

    if not os.path.exists(scimDir):
        return None

    scimConfigs = []
    for filename in os.listdir(scimDir):
        if filename.endswith(".yaml"):
            scimPath = os.path.join(scimDir, filename)
            with open(scimPath, "r") as f:
                config = yaml.safe_load(f)
                if config:
                    scimConfigs.append(config)

    return scimConfigs if scimConfigs else None


def _loadConfigMap(outputDir: str, namespace: str, configMapName: str) -> Optional[Dict[str, Any]]:
    """Load a ConfigMap from the must-gather.

    Args:
        outputDir (str): Path to must-gather output directory
        namespace (str): Namespace containing the ConfigMap
        configMapName (str): Name of the ConfigMap

    Returns:
        dict: ConfigMap data, or None if not found
    """
    configMapPath = os.path.join(outputDir, "resources", namespace, "configmaps", f"{configMapName}.yaml")

    if not os.path.exists(configMapPath):
        return None

    with open(configMapPath, "r") as f:
        return yaml.safe_load(f)


def _loadSystemInfo(outputDir: str, instanceId: str) -> Optional[Dict[str, Any]]:
    """Load system-info JSON file for MAS instance.

    Args:
        outputDir (str): Path to must-gather output directory
        instanceId (str): MAS instance ID

    Returns:
        dict: System info data, or None if not found
    """
    import json

    systemInfoPath = os.path.join(outputDir, "system-info", f"mas-{instanceId}-core.json")

    if not os.path.exists(systemInfoPath):
        return None

    with open(systemInfoPath, "r") as f:
        return json.load(f)


def _findNetworkTestFiles(outputDir: str, instanceId: str) -> List[str]:
    """Find network test markdown files for MAS instance.

    Args:
        outputDir (str): Path to must-gather output directory
        instanceId (str): MAS instance ID

    Returns:
        list: List of relative paths to network test files
    """
    networkTestsDir = os.path.join(outputDir, "network-tests")
    testFiles = []

    if not os.path.exists(networkTestsDir):
        return testFiles

    prefix = f"mas-{instanceId}-"
    for filename in os.listdir(networkTestsDir):
        if filename.startswith(prefix) and filename.endswith(".md"):
            testFiles.append(os.path.join("network-tests", filename))

    return sorted(testFiles)


def summarize(outputDir: str) -> None:
    """Generate MAS suite summaries for all instances.

    Discovers all MAS instances in the must-gather and generates a summary
    markdown file for each instance at resources/mas-{instance}-core/_summary.md.

    Args:
        outputDir (str): Path to must-gather output directory
    """
    resourcesDir = os.path.join(outputDir, "resources")

    # Find all MAS instances
    instances = _findMASInstances(resourcesDir)

    if not instances:
        return

    # Generate summary for each instance
    for instanceId in instances:
        _generateInstanceSummary(outputDir, instanceId)


def _generateInstanceSummary(outputDir: str, instanceId: str) -> None:
    """Generate summary for a single MAS instance.

    Args:
        outputDir (str): Path to must-gather output directory
        instanceId (str): MAS instance ID
    """
    # Load Suite CR
    suiteCR = _loadSuiteCR(outputDir, instanceId)
    if not suiteCR:
        return

    apps = _getActivatedApps(outputDir, instanceId)
    manageWorkspace = _loadManageWorkspaceCR(outputDir, instanceId)

    # Parse version
    versionStr = suiteCR.get("status", {}).get("versions", {}).get("reconciled", "")
    if not versionStr:
        return

    try:
        major, minor, patch = _parseVersion(versionStr)
    except ValueError:
        return

    # Determine version flags
    isAfterMAS811 = (major > 8) or (major == 8 and minor >= 11)
    isAfterMAS90 = major >= 9

    # Build summary content
    lines = []
    lines.append("# MAS Overview\n")

    # Version Information table
    lines.append("\n## Version Information\n")
    appsTable = PrettyTable()
    appsTable.field_names = ["Application", "Version", "Activation Date"]
    appsTable.align = "l"
    appsTable.set_style(TableStyle.MARKDOWN)

    # Add core version as first row with link to suite CR
    suiteCRPath = f"../resources/mas-{instanceId}-core/suites/{instanceId}.yaml"
    coreLink = f"[core]({suiteCRPath})"
    coreCreationTimestamp = suiteCR.get("metadata", {}).get("creationTimestamp", "")
    coreActivationDate = _formatTimestamp(coreCreationTimestamp)
    appsTable.add_row([coreLink, versionStr, coreActivationDate])

    # Add activated applications
    for appId, appData in sorted(apps.items()):
        status = appData.get("status", {})
        workspaceFile = appData.get("workspaceFile", "")

        # Extract version
        version = status.get("versions", {}).get("reconciled", "unknown")

        # Extract activation timestamp and format it
        activationTimestamp = status.get("milestones", {}).get("activated", {}).get("timestamp", "")
        activationDate = _formatTimestamp(activationTimestamp)

        # Create markdown link for application with ../ prefix
        appLink = f"[{appId}](../{workspaceFile})" if workspaceFile else appId

        appsTable.add_row([appLink, version, activationDate])

    lines.append(str(appsTable) + "\n")

    # Load system info for IDP and licensing data
    systemInfo = _loadSystemInfo(outputDir, instanceId)

    lines.append("\n----\n## Core\n")

    # SSO Configuration (8.11+)
    if isAfterMAS811:
        ssoDetails = suiteCR.get("status", {}).get("settings", {}).get("sso", {})
        if ssoDetails:
            lines.append("\n### SSO Configuration\n")
            ssoTable = PrettyTable()
            ssoTable.field_names = ["Setting", "Value"]
            ssoTable.align = "l"
            ssoTable.set_style(TableStyle.MARKDOWN)

            # Pretty names mapping for SSO settings
            ssoSettingNames = {
                "accessTokenTimeout": "Access Token Timeout",
                "allowCustomCacheKey": "Allow Custom Cache Key",
                "allowDefaultSsoCookieName": "Allow Default SSO Cookie Name",
                "customLoginPage": "Custom Login Page",
                "defaultIDP": "Default Identity Provider",
                "disableLtpaCookie": "Disable LTPA Cookie",
                "idleTimeout": "Idle Timeout",
                "idp": "Identity Provider Settings",
                "idpSessionTimeout": "IDP Session Timeout",
                "localLoginCacheEnabled": "Local Login Cache Enabled",
                "localLoginCacheTimeout": "Local Login Cache Timeout",
                "refreshTokenTimeout": "Refresh Token Timeout",
                "seamlessLogin": "Seamless Login",
                "ssoCookieName": "SSO Cookie Name",
                "useOnlyCustomCookieName": "Use Only Custom Cookie Name",
            }

            # Add all SSO settings to table
            for key, value in sorted(ssoDetails.items()):
                # Handle nested idp dict specially
                if key == "idp" and isinstance(value, dict):
                    # Extract idp.enabled and idp.visible as separate rows
                    idpEnabled = value.get("enabled", "unknown")
                    idpVisible = value.get("visible", "unknown")
                    if isinstance(idpEnabled, bool):
                        idpEnabled = "✅" if idpEnabled else "❌"
                    if isinstance(idpVisible, bool):
                        idpVisible = "✅" if idpVisible else "❌"
                    ssoTable.add_row(["IDP Enabled", idpEnabled])
                    ssoTable.add_row(["IDP Visible", idpVisible])
                    continue
                # Handle other nested dicts
                if isinstance(value, dict):
                    value = str(value)
                # Convert booleans to emojis
                elif isinstance(value, bool):
                    value = "✅" if value else "❌"
                prettyName = ssoSettingNames.get(key, key)
                ssoTable.add_row([prettyName, value])

            lines.append(str(ssoTable) + "\n")

    # Identity Provider Status
    if isAfterMAS811 and systemInfo and "availableIdps" in systemInfo:
        lines.append("\n### Identity Provider Status\n")
        idpTable = PrettyTable()
        idpTable.field_names = ["ID", "Name", "Type", "Default", "Enabled", "Ready", "Visible", "Status"]
        idpTable.align = "l"
        idpTable.set_style(TableStyle.MARKDOWN)

        for idp in systemInfo["availableIdps"]:
            idpTable.add_row(
                [
                    idp.get("id", ""),
                    idp.get("name", ""),
                    idp.get("type", ""),
                    "✅" if idp.get("isDefault") else "❌",
                    "✅" if idp.get("isEnabled") else "❌",
                    "✅" if idp.get("isReady") else "❌",
                    "✅" if idp.get("isVisible") else "❌",
                    idp.get("status", ""),
                ]
            )

        lines.append(str(idpTable) + "\n")

    # Licensing Information
    if isAfterMAS90 and systemInfo and "licensingProducts" in systemInfo:
        lines.append("\n### Licensing Information\n")
        licenseTable = PrettyTable()
        licenseTable.field_names = ["Product ID", "Version", "Token ID", "Token Cost"]
        licenseTable.align = "l"
        licenseTable.set_style(TableStyle.MARKDOWN)

        for product in systemInfo["licensingProducts"]:
            licenseTable.add_row([product.get("productId", ""), product.get("productVersion", ""), product.get("tokenId", ""), product.get("tokenCost", "")])

        lines.append(str(licenseTable) + "\n")

    # User self-registration (9.0+)
    if isAfterMAS90:
        lines.append("\n### User Self Registration Configuration\n")
        selfregConfigMap = _loadConfigMap(outputDir, f"mas-{instanceId}-core", f"{instanceId}-selfreg")
        if selfregConfigMap and "data" in selfregConfigMap:
            lines.append("**User self registration configuration:**\n")
            lines.append("```\n")
            for key, value in selfregConfigMap["data"].items():
                lines.append(f"{key}:\n{value}\n")
            lines.append("```\n")
        else:
            lines.append("**User self registration configuration:** (not configured)\n")

    # User Registry Synchronization
    lines.append("\n### User Registry\n")
    scimConfigs = _getSCIMConfig(outputDir, instanceId)
    if scimConfigs:
        lines.append("**User registry synchronization reports:**\n")
        for config in scimConfigs:
            name = config.get("metadata", {}).get("name", "unknown")
            report = config.get("status", {}).get("report", {})
            lines.append(f"- **{name}:** {report}\n")
    else:
        lines.append("**User registry synchronization:** (not configured)\n")

    # Pod Health and Status
    lines.append("\n### Critical Pods\n")

    namespace = f"mas-{instanceId}-core"
    # Only get the most important pods
    corePodPrefixes = [f"{instanceId}-coreapi", f"{instanceId}-internalapi", f"{instanceId}-usersync-coordinator", f"{instanceId}-scimsync"]
    podStatuses = _getPodStatus(outputDir, namespace, corePodPrefixes)

    # Create single pod status table
    if podStatuses:
        podTable = PrettyTable()
        podTable.field_names = ["Pod Name", "State"]
        podTable.align = "l"
        podTable.set_style(TableStyle.MARKDOWN)

        for pod in podStatuses:
            podLink = f"[{pod['name']}]({pod['filePath']})"
            podTable.add_row([podLink, pod["state"]])

        lines.append(str(podTable) + "\n\n")

    # Manage-specific details
    if "manage" in apps:
        # Load full manage workspace CR for status details
        manageWorkspace = _loadManageWorkspaceCR(outputDir, instanceId)
        if manageWorkspace:
            baseComponent = "base" in manageWorkspace.get("status", {}).get("components", {})
            if baseComponent:
                lines.append("\n----\n## Manage Application\n")
            else:
                lines.append("\n----\n## Manage Foundation\n")

            serverBundles = manageWorkspace.get("status", {}).get("settings", {}).get("deployment", {}).get("serverBundles", [])

            # Server Bundles table
            if len(serverBundles) > 0:
                lines.append("### Server Bundles\n")
                bundleTable = PrettyTable()
                bundleTable.field_names = ["Name", "Type", "Replicas", "Route Subdomain", "Pod Name", "State"]
                bundleTable.align = "l"
                bundleTable.set_style(TableStyle.MARKDOWN)

                workspaceId = manageWorkspace.get("metadata", {}).get("labels", {}).get("mas.ibm.com/workspaceId")

                defaultBundle = None
                mobileTarget = None
                userSyncTarget = None

                for bundle in serverBundles:
                    bundleName = bundle.get("name", "")

                    # Track special bundle roles
                    if bundle.get("isDefault", False):
                        defaultBundle = bundleName
                    if bundle.get("isMobileTarget", False):
                        mobileTarget = bundleName
                    if bundle.get("isUserSyncTarget", False):
                        userSyncTarget = bundleName

                    # Get pod status for this bundle
                    bundlePodPrefix = f"{instanceId}-{workspaceId}-{bundleName}"
                    bundlePods = _getPodStatus(outputDir, f"mas-{instanceId}-manage", [bundlePodPrefix])

                    podName = ""
                    podState = ""
                    if bundlePods:
                        pod = bundlePods[0]
                        podName = f"[{pod['name']}]({pod['filePath']})"
                        podState = pod["state"]

                    bundleTable.add_row(
                        [bundleName, bundle.get("bundleType", ""), bundle.get("replica", ""), bundle.get("routeSubDomain", ""), podName, podState]
                    )

                lines.append(str(bundleTable) + "\n\n")

                # Add bundle role information
                lines.append(f"- Default Bundle: **{defaultBundle}**\n")
                lines.append(f"- Mobile Target: **{mobileTarget}**\n")
                lines.append(f"- User Sync Target: **{userSyncTarget}**\n")
                lines.append("\n")

            # PodTemplates configuration
            podTemplates = manageWorkspace.get("status", {}).get("podTemplates", [])
            lines.append("### PodTemplates Configuration\n")
            lines.append(f"```\n{podTemplates}\n```\n")

    # Network Tests
    networkTestFiles = _findNetworkTestFiles(outputDir, instanceId)
    if networkTestFiles:
        lines.append("\n----\n## Network Tests\n")
        for testFile in networkTestFiles:
            testName = os.path.basename(testFile).replace(".md", "").replace(f"mas-{instanceId}-", "")
            lines.append(f"- [{testName}](../{testFile})\n")

    # Write summary file
    summariesDir = os.path.join(outputDir, "summaries")
    os.makedirs(summariesDir, exist_ok=True)
    summaryPath = os.path.join(summariesDir, f"mas-{instanceId}.md")

    with open(summaryPath, "w") as f:
        f.write("".join(lines))
