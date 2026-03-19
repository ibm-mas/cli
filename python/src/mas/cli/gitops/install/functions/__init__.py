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
Functions module for GitOps install operations.

This module contains utility functions for different aspects of the
GitOps installation process, organized by scope:
- gitops_cluster: Cluster-level configuration functions
- gitops_instance: Instance-level configuration functions
- gitops_apps: Application-level configuration functions
- utils: Shared utility functions
"""

from .utils import run_mas_command

__all__ = ['run_mas_command']
