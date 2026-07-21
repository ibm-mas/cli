# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Shared workflow step builders reused across MAS CLI commands.

Provides factory functions that create standard WorkflowStep objects
(e.g. the OCP cluster connection step) so each command's workflow
module does not duplicate field definitions.
"""

from typing import Any

from mas.cli.tui.models import WorkflowStep
from mas.cli.tui.shell import ConnectStepScreen


def connectClusterStep(appInstance: Any, post_connect=None) -> WorkflowStep:
    """Return the standard OCP cluster connection WorkflowStep.

    The step uses :class:`~mas.cli.tui.shell.ConnectStepScreen` as its
    panel widget.  That widget detects an active kubeconfig connection and
    offers a Yes/No prompt to reuse it.  If the user declines, or if no
    connection exists, it collects Server URL, Login Token, and Skip TLS
    and runs ``app_instance._connectFromParams`` on Connect — showing
    connection errors inline rather than advancing.

    Args:
        appInstance (Any): A BaseApp subclass instance whose
            ``_connectFromParams`` and ``getActiveConsoleURL`` methods are used.
        post_connect (Callable, optional): Passed to ConnectStepScreen as
            ``post_connect`` — run in the worker thread after a successful
            connection.  Defaults to None.

    Returns:
        WorkflowStep: A fully configured connect-cluster step.
    """
    kwargs = {}
    if post_connect is not None:
        kwargs["post_connect"] = post_connect
    return WorkflowStep(
        id="connect-cluster",
        heading="Connect to OpenShift Cluster",
        heading_level="h1",
        screen_class=ConnectStepScreen,
        screen_kwargs=kwargs,
    )
