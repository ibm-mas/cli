#!/usr/bin/env python
# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
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

import logging
from typing import Callable, Optional

from openshift.dynamic import DynamicClient
from halo import Halo

logger = logging.getLogger(__name__)


def check_rbac_permissions(dynamic_client: DynamicClient, version: str, admin_mode: str) -> bool:
    """
    Check if user has permissions to apply pre-install RBAC.

    This function performs three checks:
    1. Version must be >= 9.2.0 (when RBAC was introduced)
    2. Admin mode must not be "minimal" (minimal mode doesn't need pre-install RBAC)
    3. User must have cluster-admin level permissions

    Args:
        dynamic_client: Kubernetes dynamic client
        version: Target MAS version (e.g., "9.2.0", "9.2.1")
        admin_mode: Admin mode (cluster, namespaced, minimal)

    Returns:
        bool: True if user has permissions and RBAC should be applied, False otherwise
    """
    from mas.devops.utils import isVersionEqualOrAfter
    from mas.devops.pre_install import permissionCheckForRBAC

    # Early returns for cases where RBAC not needed
    if not isVersionEqualOrAfter("9.2.0", version):
        logger.debug(f"Version {version} is < 9.2.0, RBAC not required")
        return False

    if admin_mode == "minimal":
        logger.debug("Admin mode is 'minimal', RBAC not required")
        return False

    # Check permissions
    logger.debug(f"Checking RBAC permissions for version {version}, admin mode {admin_mode}")
    permission_results = permissionCheckForRBAC(dynamic_client)
    has_permissions = all(result["allowed"] for result in permission_results)

    if has_permissions:
        logger.info("User has sufficient permissions to apply pre-install RBAC")
    else:
        logger.warning("User does not have sufficient permissions to apply pre-install RBAC")

    return has_permissions


def generate_preinstall_command(instance_id: str, channel: str, admin_mode: str, selected_apps: Optional[list] = None) -> str:
    """
    Generate the mas pre-install command string.

    Args:
        instance_id: MAS instance ID
        channel: MAS channel/version (e.g., "9.2", "9.2.0")
        admin_mode: Admin mode (cluster, namespaced, minimal)
        selected_apps: Optional list of selected apps (e.g., ["manage", "monitor"])

    Returns:
        str: Complete mas pre-install command

    Example:
        >>> generate_preinstall_command("inst1", "9.2", "cluster")
        'mas pre-install --mas-instance-id inst1 --mas-channel 9.2 --admin-mode cluster'

        >>> generate_preinstall_command("inst1", "9.2", "namespaced", ["manage", "monitor"])
        'mas pre-install --mas-instance-id inst1 --mas-channel 9.2 --admin-mode namespaced --selected-apps manage,monitor'
    """
    apps_arg = f" --selected-apps {','.join(selected_apps)}" if selected_apps else ""
    return f"mas pre-install --mas-instance-id {instance_id} --mas-channel {channel} --admin-mode {admin_mode}{apps_arg}"


def handle_rbac_permission_denied(
    print_func: Callable,
    yes_or_no_func: Callable,
    fatal_error_func: Callable,
    no_confirm: bool,
    admin_mode: str,
    preinstall_commands: list,
    operation: str = "installation",
) -> None:
    """
    Handle user messaging when RBAC permissions are denied.

    This function provides consistent messaging across all commands when the user
    doesn't have permissions to apply pre-install RBAC. It handles both interactive
    and non-interactive modes.

    Args:
        print_func: Function to print messages (e.g., self.printDescription)
        yes_or_no_func: Function to prompt yes/no (e.g., self.yesOrNo)
        fatal_error_func: Function to exit with error (e.g., self.fatalError)
        no_confirm: Whether running in no-confirm mode
        admin_mode: Admin mode being used
        preinstall_commands: List of pre-install commands to show user
        operation: Type of operation (installation, upgrade, update)

    Behavior:
        - In no-confirm mode: Logs warning and continues (assumes RBAC already applied)
        - In interactive mode: Prompts user to confirm RBAC was applied, exits if not
    """
    if no_confirm:
        # Non-interactive mode: assume RBAC already applied
        print_func(
            [
                f"{operation.capitalize()} will continue with the selected '{admin_mode}' admin mode.",
                "The current user does not have sufficient permissions to apply the pre-install RBAC automatically.",
                "With the --no-confirm flag, the operation assumes the required RBAC has already been applied by your OpenShift administrator.",
                "If it has not been applied, ensure your OpenShift administrator runs:",
            ]
        )
        for cmd in preinstall_commands:
            print_func([f"  {cmd}"])
        logger.warning(f"{operation.capitalize()} continuing with --no-confirm flag. " f"Assuming pre-install RBAC already applied by administrator.")
    else:
        # Interactive mode: prompt user to confirm
        print_func(
            [
                "",
                f"You are performing a {operation} with '{admin_mode}' admin mode.",
                "The pre-install RBAC required for this admin mode has not been applied by your current cluster login.",
                "This step must be completed by an OpenShift cluster administrator before the operation can continue.",
                "Ask your OpenShift administrator to run:",
            ]
        )
        for cmd in preinstall_commands:
            print_func([f"  {cmd}"])
        print_func(["", "If that has already been done, you can continue."])

        if not yes_or_no_func(f"Has your OpenShift administrator already run 'mas pre-install' for this {operation}"):
            error_msg = f"{operation.capitalize()} aborted. Ask your OpenShift administrator to run the commands listed above."
            fatal_error_func(error_msg)

        # User confirmed RBAC was already applied
        logger.info(f"User confirmed pre-install RBAC was already applied by administrator, continuing with {operation}")


def apply_rbac_with_spinner(
    dynamic_client: DynamicClient, instance_id: str, channel: str, admin_mode: str, selected_apps: Optional[list], spinner, success_icon: str
) -> None:
    """
    Apply pre-install RBAC with spinner feedback.

    This function wraps the applyPreInstallMASRBAC call with a Halo spinner
    to provide visual feedback during the operation.

    Args:
        dynamic_client: Kubernetes dynamic client
        instance_id: MAS instance ID
        channel: MAS channel (e.g., "9.2.0", "9.2.1")
        admin_mode: Admin mode (cluster, namespaced, minimal)
        selected_apps: List of selected apps (e.g., ["manage", "monitor"])
        spinner: Halo spinner configuration
        success_icon: Success icon for spinner (e.g., "✔")

    Raises:
        Any exceptions from applyPreInstallMASRBAC are propagated
    """
    from mas.devops.utils import extractBaseVersion
    from mas.devops.pre_install import applyPreInstallMASRBAC

    with Halo(text=f"Applying pre-install MAS RBAC for {instance_id}", spinner=spinner) as h:
        target_version = extractBaseVersion(channel)
        logger.info(f"Applying pre-install RBAC: instance={instance_id}, " f"version={target_version}, mode={admin_mode}, apps={selected_apps}")

        applyPreInstallMASRBAC(
            dynClient=dynamic_client,
            masVersion=target_version,
            masInstanceId=instance_id,
            adminMode=admin_mode,
            selectedApps=selected_apps,
        )

        h.stop_and_persist(symbol=success_icon, text=f"Pre-install MAS RBAC applied for {instance_id} (version: {target_version}, mode: {admin_mode})")
        logger.info(f"Pre-install RBAC successfully applied for instance {instance_id}")


# Made with Bob
