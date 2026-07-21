# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Workflow definition for the MAS upgrade command.

Builds the ordered list of WorkflowStep objects that the Textual TUI
shell renders when the user runs ``mas-cli upgrade`` without ``--mas-instance-id``.
"""

from typing import Any

from mas.cli.tui.models import WorkflowDefinition, WorkflowField, WorkflowStep, WorkflowSummaryItem
from mas.cli.common.workflow import connectClusterStep


def buildUpgradeWorkflow(appInstance: Any) -> WorkflowDefinition:
    """Build the workflow definition for the upgrade command.

    Constructs the ordered list of steps shown in the TUI when the user
    invokes ``mas-cli upgrade`` without ``--mas-instance-id``.

    The steps are:
    1. **connect-cluster** — Collect OCP credentials and connect, then fetch
       the list of installed MAS instance IDs via ``post_connect``.  If no
       instances are found the error is shown on the connect screen.
    2. **instance-selection** — Select which MAS instance to upgrade.  On
       Next, ``prepareUpgrade`` runs as the validator: it detects the current
       and next channels, validates app compatibility, checks license
       acceptance, and evaluates RBAC — the same logic as the non-interactive
       path.  Errors are shown inline; on success the workflow goes directly
       to the review screen.

    Args:
        appInstance (Any): An ``UpgradeApp`` instance whose methods are used
            as step actions.

    Returns:
        WorkflowDefinition: Ordered list of WorkflowStep objects.
    """
    connectStep = connectClusterStep(appInstance, post_connect=appInstance.fetchInstalledInstanceIds)

    return [
        connectStep,
        WorkflowStep(
            id="instance-selection",
            heading="Select MAS Instance",
            heading_level="h1",
            description=[
                "Select the MAS instance to upgrade to the next available release.",
            ],
            fields=[
                WorkflowField(
                    id="mas_instance_id",
                    label="MAS Instance ID",
                    type="select",
                    required=True,
                    options=lambda: appInstance._installedInstanceIds,
                ),
            ],
            validator=appInstance.prepareUpgrade,
            summary=[
                WorkflowSummaryItem(label="MAS Instance ID", param="mas_instance_id"),
                WorkflowSummaryItem(label="Current MAS Channel", attr="currentChannel"),
                WorkflowSummaryItem(label="Next MAS Channel", attr="nextChannel"),
                WorkflowSummaryItem(label="Skip Pre-Upgrade Checks", attr="skipPreCheck"),
            ],
        ),
    ]
