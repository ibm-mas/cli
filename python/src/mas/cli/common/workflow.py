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
(e.g. the OCP cluster connection step and the storage class selection
step) so each command's workflow module does not duplicate field
definitions.
"""

from typing import Any, List, Optional

from mas.cli.tui.models import WorkflowField, WorkflowStep, WorkflowSummaryItem
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


def storageClassStep(
    appInstance: Any,
    id: str,
    heading: str,
    description: List[str],
    validator: Optional[Any] = None,
    validator_status: str = "",
    condition: Optional[Any] = None,
    required: bool = False,
    allowRwxNone: bool = False,
) -> WorkflowStep:
    """Return the standard RWO / RWX storage class selection WorkflowStep.

    The shared TUI counterpart of
    :meth:`mas.cli.common.storageClasses.StorageClassMixin.configStorageClasses`:
    both storage class fields are dropdowns whose options are looked up
    from the connected cluster in a worker thread
    (``appInstance.lookupStorageClasses``), with the auto-detected
    provider's classes pre-selected and the detected provider shown in a
    context row.  Used by the upgrade command's manage-foundation step
    today; the install command's future TUI workflow reuses it with
    ``required=True, allowRwxNone=True``.

    Args:
        appInstance (Any): A BaseApp subclass instance mixed with
            ``StorageClassMixin`` (provides ``lookupStorageClasses`` and
            the ``detectedStorageClasses`` / ``detectedStorageProviderName``
            attributes its loader populates).
        id (str): Machine-readable step id (e.g. "manage-foundation").
        heading (str): Step heading shown in the sidebar and panel.
        description (list[str]): Paragraphs shown below the heading.
        validator (Callable, optional): Step validator run on Next —
            typically the command's configuration method that consumes the
            selected classes (e.g. ``prepareManageFoundation``).  Defaults
            to None.
        validator_status (str, optional): Busy message shown while the
            validator runs.  Defaults to "" (a generic "Validating…").
        condition (Callable, optional): ``lambda params: bool`` controlling
            whether the step is shown at all.  Defaults to None.
        required (bool): When True both dropdowns must be set before Next
            is enabled; when False (default) blank means "auto-detect at
            validation time".
        allowRwxNone (bool): When True, ``"none"`` is offered as a
            ReadWriteMany option (clusters with no suitable RWX class —
            the install flavour).  Defaults to False.

    Returns:
        WorkflowStep: A fully configured storage class selection step.
    """

    def _detected(attr: str):
        """Return the auto-detected provider's class for an access mode, or None."""

        def _lookup():
            detected = getattr(appInstance, "detectedStorageClasses", None)
            if detected is None or getattr(detected, "provider", None) is None:
                return None
            return getattr(detected, attr, None)

        return _lookup

    def _rwxOptions(params: dict) -> List[str]:
        options = appInstance.lookupStorageClasses()
        return options + ["none"] if allowRwxNone else options

    return WorkflowStep(
        id=id,
        heading=heading,
        heading_level="h1",
        description=description,
        context=[
            WorkflowSummaryItem(label="Detected storage provider", attr="detectedStorageProviderName"),
        ],
        fields=[
            WorkflowField(
                id="storage_class_rwo",
                label="ReadWriteOnce (RWO) Storage Class",
                type="dynamic_select",
                required=required,
                options_loader=lambda params: appInstance.lookupStorageClasses(),
                default=_detected("rwo"),
            ),
            WorkflowField(
                id="storage_class_rwx",
                label="ReadWriteMany (RWX) Storage Class",
                type="dynamic_select",
                required=required,
                options_loader=_rwxOptions,
                default=_detected("rwx"),
            ),
        ],
        validator=validator,
        validator_status=validator_status,
        condition=condition,
    )
