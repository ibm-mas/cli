# *****************************************************************************
# Copyright (c) 2024, 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""
Utility functions for GitOps install operations.

This module contains shared utility functions used across different
GitOps installation modules.
"""

import logging
import subprocess

logger = logging.getLogger(__name__)


def run_mas_command(command: list, function_name: str) -> None:
    """
    Execute a MAS CLI command and handle errors.

    Args:
        command: List of command arguments
        function_name: Name of the function being called (for error messages)

    Raises:
        RuntimeError: If the command fails
    """
    logger.debug(f"Executing command: {' '.join(command)}")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            logger.info(f"Successfully executed {function_name}")
            if result.stdout:
                logger.debug(result.stdout)
        else:
            error_msg = f"Failed to execute {function_name}:\nError: {result.stderr}\nOutput: {result.stdout}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    except Exception as e:
        logger.error(f"Exception occurred while calling {function_name}: {str(e)}")
        raise RuntimeError(f"Exception calling {function_name}: {str(e)}") from e

# Made with Bob
