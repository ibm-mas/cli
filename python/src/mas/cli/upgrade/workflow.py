# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
# *****************************************************************************

"""Workflow definition for the MAS upgrade command.

Builds the ordered list of WorkflowStep objects that the Textual TUI
shell renders when the user runs ``mas-cli upgrade`` without arguments.
"""

from typing import Any

from mas.cli.tui.models import WorkflowDefinition, WorkflowField, WorkflowStep, WorkflowSummaryItem
from mas.cli.tui.screens import LaunchScreen, LicenseAcceptanceScreen, ReviewScreen
from mas.cli.common.workflow import connectClusterStep


def _nonInteractiveCommand(appInstance: Any) -> str:
    """Render the equivalent non-interactive ``mas upgrade`` command.

    Delegates to ``UpgradeApp.buildCommand()`` (the ``upgradeArgBuilderMixin``
    from PR #2713, round-trip tested in
    ``tests/unit/upgrade/test_upgrade_arg_builder.py``) so the TUI shows exactly
    what the classic interactive wizard would print.

    Args:
        appInstance (Any): An ``UpgradeApp`` instance with populated params.

    Returns:
        str: The rendered command, secrets masked as environment variables.
    """
    return appInstance.buildCommand()


def _scriptFilename(appInstance: Any) -> str:
    """Default filename for the review screen's Save Script button.

    Mirrors the filename offered by the classic interactive flow
    (the ``offerCommandScript`` call in ``UpgradeApp.upgrade()``).

    Args:
        appInstance (Any): An ``UpgradeApp`` instance.

    Returns:
        str: e.g. ``mas-upgrade-inst1.sh``.
    """
    return f"mas-upgrade-{appInstance.params.get('mas_instance_id', 'instance')}.sh"


def buildUpgradeReview(appInstance: Any) -> str:
    """Build the Markdown review text for the upgrade command.

    Mirrors the ``printH1``/``printSummary`` calls in the review settings
    section of ``UpgradeApp.upgrade()`` so the TUI review screen looks like
    its CLI counterpart.

    Args:
        appInstance (Any): An ``UpgradeApp`` instance with ``currentChannel``,
            ``nextChannel`` and the pipeline storage class attributes
            populated (by ``prepareUpgrade``).

    Returns:
        str: Markdown document string ready for the Textual Markdown widget.
    """

    def _row(label: str, value) -> str:
        rendered = "—" if value in (None, "") else str(value)
        return f"**{label}:** {rendered}  "

    lines = [
        "## Upgrade Summary",
        "",
        _row("Instance ID", appInstance.params.get("mas_instance_id")),
        _row("Current MAS Channel", getattr(appInstance, "currentChannel", None)),
        _row("Next MAS Channel", getattr(appInstance, "nextChannel", None)),
        _row("Skip Pre-Upgrade Checks", getattr(appInstance, "skipPreCheck", None)),
        "",
        "## Pipeline Storage",
        "",
        _row("Storage Class", getattr(appInstance, "pipelineStorageClass", None)),
        _row("Access Mode", getattr(appInstance, "pipelineStorageAccessMode", None)),
        "",
    ]
    return "\n".join(lines)


def buildUpgradeWorkflow(appInstance: Any) -> WorkflowDefinition:
    """Build the workflow definition for the upgrade command.

    Constructs the ordered list of steps shown in the TUI when the user
    invokes ``mas-cli upgrade`` without arguments.

    The five steps are:

    1. **connect-cluster** — Collect OCP credentials and connect, then fetch
       the list of installed MAS instance IDs via ``post_connect``.  If no
       instances are found the error is shown on the connect screen.
    2. **instance-selection** — Select which MAS instance to upgrade.  On
       Next, ``prepareUpgrade`` runs as the validator: it detects the current
       and next channels, validates app compatibility, evaluates RBAC and
       resolves the pipeline storage class — the same logic as the
       non-interactive path.  Errors are shown inline.
    3. **license-acceptance** — Conditional step shown only when the target
       channel resolved by ``prepareUpgrade`` carries a license that has not
       been accepted yet (``licenseAcceptancePending``): the TUI equivalent
       of the classic wizard's license prompt and of ``--accept-license``.
    4. **review** — Review all settings before proceeding, including the
       equivalent non-interactive ``mas upgrade`` command (with copy /
       save-as-script).  The Confirm button advances to the launch step.
    5. **launch** — Submits the Tekton upgrade pipeline, then re-displays
       the non-interactive command for reference.  The Done button exits
       the app.

    Args:
        appInstance (Any): An ``UpgradeApp`` instance whose methods are used
            as step actions and validators.

    Returns:
        WorkflowDefinition: Ordered list of WorkflowStep objects.
    """
    connectStep = connectClusterStep(appInstance, post_connect=appInstance.fetchInstalledInstanceIds)

    instanceSelectionStep = WorkflowStep(
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
    )

    # Only shown when prepareUpgrade resolved a target channel carrying a
    # license that has not been accepted yet.  The condition closes over the
    # app instance so it reads the validator's state (nextChannel /
    # licenseAccepted) rather than the params dict; the shell re-evaluates it
    # after the instance-selection step completes, so the panel composes (and
    # the license text resolves) with the selected instance's target channel.
    licenseAcceptanceStep = WorkflowStep(
        id="license-acceptance",
        heading="License Terms",
        heading_level="h1",
        description=[
            "To continue with the upgrade, you must accept the license terms for the target release.",
        ],
        screen_class=LicenseAcceptanceScreen,
        condition=lambda p: appInstance.licenseAcceptancePending(),
    )

    reviewStep = WorkflowStep(
        id="review",
        heading="Review Settings",
        heading_level="h1",
        description=["Please carefully review your choices below."],
        screen_class=ReviewScreen,
        screen_kwargs={
            "review_builder": buildUpgradeReview,
            "command_builder": _nonInteractiveCommand,
            "script_filename_builder": _scriptFilename,
        },
        summary=[
            WorkflowSummaryItem(label="MAS Instance ID", param="mas_instance_id"),
            WorkflowSummaryItem(label="Current MAS Channel", attr="currentChannel"),
            WorkflowSummaryItem(label="Next MAS Channel", attr="nextChannel"),
            WorkflowSummaryItem(label="Skip Pre-Upgrade Checks", attr="skipPreCheck"),
            WorkflowSummaryItem(label="Pipeline Storage Class", attr="pipelineStorageClass"),
            WorkflowSummaryItem(label="Pipeline Storage Access Mode", attr="pipelineStorageAccessMode"),
        ],
    )

    launchStep = WorkflowStep(
        id="launch",
        heading="Launch Upgrade",
        heading_level="h1",
        description=["Submitting the Tekton pipeline for MAS upgrade."],
        screen_class=LaunchScreen,
        screen_kwargs={
            "command_builder": _nonInteractiveCommand,
            "launch_method": "launchUpgrade",
        },
    )

    return [
        connectStep,
        instanceSelectionStep,
        licenseAcceptanceStep,
        reviewStep,
        launchStep,
    ]
