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
GitOps Installation Package

This package provides a standalone command for GitOps-based MAS installations.
It includes dynamic argument parsing from bash functions and non-interactive
execution capabilities.
"""

from .app import GitOpsInstallApp
from .executor import GitOpsInstallExecutor
from .argParser import GitOpsArgumentParser
from .argBuilder import BashFunctionArgumentExtractor

__all__ = [
    'GitOpsInstallApp',
    'GitOpsInstallExecutor',
    'GitOpsArgumentParser',
    'BashFunctionArgumentExtractor'
]
