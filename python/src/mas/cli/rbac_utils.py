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
from typing import Callable

logger = logging.getLogger(__name__)


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
                f"{operation.capitalize()} will continue with the '{admin_mode}' admin mode.",
                "The current user does not have sufficient permissions to apply the pre-install RBAC automatically.",
                "With the --no-confirm flag, the operation assumes the required RBAC has already been applied by your OpenShift administrator.",
                "If it has not been applied, ensure your OpenShift administrator runs:",
            ]
        )
        for cmd in preinstall_commands:
            print_func([f"  {cmd}"])
        logger.warning(f"{operation.capitalize()} continuing with --no-confirm flag. Assuming pre-install RBAC already applied by administrator.")
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
