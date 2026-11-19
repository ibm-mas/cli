#!/usr/bin/env python
# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""
Common utilities for handling RBAC permission checks and pre-install operations
across install, upgrade, and update commands.
"""

import json
import logging
from os import environ, path
from typing import Any, Callable
from mas.devops.utils import isVersionEqualOrAfter
from mas.devops.pre_install import permissionCheckForRBAC
from mas.devops.mas import getInstalledApps

logger = logging.getLogger(__name__)

# Environment variable that overrides the location of the pre-install RBAC manifests
PREINSTALL_RBAC_DIR_ENV = "MAS_PREINSTALL_RBAC_DIR"

# Location populated during the container image build (see the RBAC copy step in image/cli/Dockerfile)
LEGACY_PREINSTALL_RBAC_DIR = "/opt/app-root/rbac"

# Location populated during the python package build (see build/bin/bundle-preinstall-rbac.sh), used by uvx and uv tool installs
PACKAGED_PREINSTALL_RBAC_DIR = path.join(path.abspath(path.dirname(__file__)), "rbac", "preinstall")

# Written next to the bundled manifests by the package build, records which pre-install commit they came from
PREINSTALL_RBAC_SOURCE_FILE = "SOURCE.json"


def getPreinstallRBACSource(rootDir: str) -> dict[str, Any] | None:
    """Read the provenance recorded alongside the bundled pre-install RBAC manifests.

    Provenance is informational only, so a missing or unreadable file results in None rather than an error.
    The container image and user overrides do not have this file.

    Args:
        rootDir (str): RBAC root directory returned by getPreinstallRBACRootDir

    Returns:
        dict[str, Any] | None: The recorded repository, branch and commit, or None if unavailable
    """
    try:
        with open(path.join(rootDir, PREINSTALL_RBAC_SOURCE_FILE), "r", encoding="utf-8") as sourceFile:
            source = json.load(sourceFile)
    except (OSError, ValueError):
        return None
    return source if isinstance(source, dict) else None


def _describeRBACRoot(rootDir: str) -> str:
    """Build the log description of a resolved RBAC root, including provenance when known."""
    source = getPreinstallRBACSource(rootDir)
    if source is None:
        return rootDir
    return f"{rootDir} (pre-install branch={source.get('branch', 'unknown')}, commit={source.get('commit', 'unknown')})"


def getPreinstallRBACRootDir() -> str:
    """Locate the directory holding the pre-install RBAC manifests.

    Candidates are tried in order and the first one that exists wins. Which manifests inside the directory
    are applied is decided by mas.devops.pre_install, not here:

    1. The directory named by the MAS_PREINSTALL_RBAC_DIR environment variable. If it is set but is not a
       directory this is an error, rather than silently using a different set of manifests.
    2. /opt/app-root/rbac, which is populated in the container image.
    3. The rbac/preinstall directory bundled inside the mas.cli package, used by uvx and uv tool installs.

    Returns:
        str: The RBAC root directory to pass as rbacRootDir

    Raises:
        FileNotFoundError: If no candidate directory exists
    """
    override = environ.get(PREINSTALL_RBAC_DIR_ENV, "").strip()
    if override:
        if path.isdir(override):
            logger.info(f"Using pre-install RBAC manifests from {PREINSTALL_RBAC_DIR_ENV}={_describeRBACRoot(override)}")
            return override
        raise FileNotFoundError(f"{PREINSTALL_RBAC_DIR_ENV} is set to '{override}' but it is not a directory")

    for candidate in (LEGACY_PREINSTALL_RBAC_DIR, PACKAGED_PREINSTALL_RBAC_DIR):
        if path.isdir(candidate):
            logger.info(f"Using pre-install RBAC manifests from {_describeRBACRoot(candidate)}")
            return candidate

    raise FileNotFoundError(
        "Could not find the pre-install RBAC manifests. "
        f"Looked in {LEGACY_PREINSTALL_RBAC_DIR} and {PACKAGED_PREINSTALL_RBAC_DIR}. "
        f"Set {PREINSTALL_RBAC_DIR_ENV} to a directory containing a checkout of the ibm-mas/pre-install RBAC folders."
    )


def handleRBACPermissionDenied(
    printFunc: Callable,
    yesOrNoFunc: Callable,
    fatalErrorFunc: Callable,
    noConfirm: bool,
    adminMode: str,
    preinstallCommand: str,
    operation: str = "installation",
) -> None:
    """
    Handle user messaging when RBAC permissions are denied.

    This function provides consistent messaging across all commands when the user
    doesn't have permissions to apply pre-install RBAC. It handles both interactive
    and non-interactive modes.

    Args:
        printFunc: Function to print messages (e.g., self.printDescription)
        yesOrNoFunc: Function to prompt yes/no (e.g., self.yesOrNo)
        fatalErrorFunc: Function to exit with error (e.g., self.fatalError)
        noConfirm: Whether running with --no-confirm flag
        adminMode: Admin mode being used
        preinstallCommand: Pre-install command to show user
        operation: Type of operation (installation, upgrade, update)

    Behavior:
        - In noConfirm mode: Logs warning and continues (assumes RBAC already applied)
        - In interactive mode: Prompts user to confirm RBAC was applied, exits if not
    """
    if noConfirm:
        # Non-interactive mode: assume RBAC already applied
        printFunc(
            [
                f"{operation.capitalize()} will continue with the '{adminMode}' admin mode.",
                "The current user does not have sufficient permissions to apply the pre-install RBAC automatically.",
                "With the --no-confirm flag, the operation assumes the required RBAC has already been applied by your OpenShift administrator.",
                "If it has not been applied, ensure your OpenShift administrator runs:",
                f"  {preinstallCommand}",
            ]
        )
        logger.warning(f"{operation.capitalize()} continuing with --no-confirm flag. Assuming pre-install RBAC already applied by administrator.")
    else:
        # Interactive mode: prompt user to confirm
        printFunc(
            [
                "",
                f"You are performing an {operation} with '{adminMode}' admin mode.",
                "The pre-install RBAC required for this admin mode has not been applied by your current cluster login.",
                "This step must be completed by an OpenShift cluster administrator before the operation can continue.",
                "Ask your OpenShift administrator to run:",
                f"  {preinstallCommand}",
                "",
                "If that has already been done, you can continue.",
            ]
        )

        if not yesOrNoFunc(f"Has your OpenShift administrator already run 'mas pre-install' for this {operation}"):
            errorMsg = f"{operation.capitalize()} aborted. Ask your OpenShift administrator to run the command listed above."
            fatalErrorFunc(errorMsg)

        # User confirmed RBAC was already applied
        logger.info(msg=f"User confirmed pre-install RBAC was already applied by administrator, continuing with {operation}")


def evaluatePreinstallRBACAccess(
    dynamicClient,
    masChannel: str,
    adminMode: str,
    instanceId: str = None,
    noConfirm: bool = False,
    printH1Func: Callable = None,
    printDescriptionFunc: Callable = None,
    yesOrNoFunc: Callable = None,
    fatalErrorFunc: Callable = None,
    operation: str = "installation",
) -> bool:
    """
    Evaluate if pre-install RBAC should be applied for a single MAS instance.
    This is a common function used by install, upgrade, and update commands.

    This function:
    1. Checks if version >= 9.2.0 (RBAC requirement)
    2. Checks if admin mode is "minimal" (no RBAC needed)
    3. Checks if user has RBAC permissions
    4. If no permissions: prompts user or shows error message

    Args:
        dynamicClient: OpenShift dynamic client
        masChannel: MAS channel/version (e.g., "9.2.x" or "9.2.0")
        adminMode: Admin mode (cluster, namespaced, minimal)
        instanceId: MAS instance ID (optional, for upgrade/update)
        noConfirm: Whether running in noConfirm mode
        printH1Func: Function to print H1 headers (optional)
        printDescriptionFunc: Function to print descriptions (optional)
        yesOrNoFunc: Function to prompt yes/no (optional)
        fatalErrorFunc: Function to exit with error (optional)
        operation: Type of operation (installation, upgrade, update)

    Returns:
        bool: True if user has permissions and RBAC should be applied, False otherwise

    Usage:
        # Install command
        if evaluatePreinstallRBACAccess(client, "9.2.x", "cluster", ...):
            # Apply RBAC

        # Upgrade command
        if evaluatePreinstallRBACAccess(client, "9.2.0", "cluster", instance_id="prod", ...):
            apps = getInstalledApps(client, "prod")
            # Apply RBAC with apps

        # Update command (loop through instances)
        for instance in instances:
            if evaluatePreinstallRBACAccess(client, version, mode, instance_id=id, ...):
                apps = getInstalledApps(client, "prod")
                # Apply RBAC with apps
    """

    # Check if version requires RBAC (>= 9.2.0)
    if not isVersionEqualOrAfter("9.2.0", masChannel):
        logger.info(f"MAS channel {masChannel} is < 9.2.0, no pre-install RBAC needed")
        return False

    # Check if minimal mode (doesn't need RBAC)
    if adminMode == "minimal":
        logger.info("Admin mode is 'minimal', no pre-install RBAC needed")
        return False

    # Check if user has permissions to apply RBAC
    permissionResults = permissionCheckForRBAC(dynamicClient)
    hasPermissions = all(result["allowed"] for result in permissionResults)

    if hasPermissions:
        logger.info("User has permissions to apply pre-install RBAC")
        return True

    # User does not have permissions - handle accordingly
    logger.warning("User does not have permissions to apply pre-install RBAC")

    # Print header if function provided
    if printH1Func:
        printH1Func("Pre-Install RBAC Configuration")

    # Print description if function provided
    if printDescriptionFunc:
        printDescriptionFunc(
            [
                f"Admin mode: '{adminMode}'",
                "Pre-install RBAC could not be applied automatically (insufficient permissions).",
            ]
        )

    # Generate pre-install command
    # Get apps for the command if instanceId provided
    selectedApps = []
    if instanceId:
        selectedApps = getInstalledApps(dynamicClient, instanceId)

    appsArg = f" --apps {','.join(selectedApps)}" if selectedApps else ""
    instanceArg = f" --mas-instance-id {instanceId}" if instanceId else ""
    preinstallCmd = f"mas pre-install{instanceArg} --mas-channel {masChannel} --admin-mode {adminMode}{appsArg}"

    # Handle permission denied if functions provided
    if yesOrNoFunc and fatalErrorFunc and printDescriptionFunc:
        handleRBACPermissionDenied(
            printFunc=printDescriptionFunc,
            yesOrNoFunc=yesOrNoFunc,
            fatalErrorFunc=fatalErrorFunc,
            noConfirm=noConfirm,
            adminMode=adminMode,
            preinstallCommand=preinstallCmd,
            operation=operation,
        )

    # If we reach here, user confirmed RBAC was already applied (or no UI functions provided)
    # Return False because we don't need to apply it ourselves
    return False
