# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
# *****************************************************************************

"""Pilot tests for the upgrade command's review screen.

Mounts the real review WorkflowStep (from buildUpgradeWorkflow) in a
ReviewScreen against a scenario app in the post-prepareUpgrade state,
verifying that the Markdown summary shows the upgrade channels and the
command panel renders the buildCommand() output.
"""

import pytest
from textual.widgets import Button, Markdown, Static

from mas.cli.upgrade.workflow import buildUpgradeWorkflow
from pilot.harness import run_screen_pilot
from scenarios.upgrade import upgrade_scenario

pytestmark = pytest.mark.pilot


def _markdown_text(markdown: Markdown) -> str:
    """Flatten a rendered Textual Markdown widget to plain text.

    Textual renders Markdown into a tree of Static sub-widgets (paragraphs,
    headings, tables), so the text is collected by walking the tree.

    Args:
        markdown (Markdown): The rendered Markdown widget.

    Returns:
        str: All rendered text joined with spaces.
    """
    parts = []

    def _walk(widget):
        if isinstance(widget, Static):
            parts.append(str(widget.render()))
        for child in widget.children:
            _walk(child)

    _walk(markdown)
    return " ".join(parts)


def _make_screen(scenario):
    """Return (screen, mas_app) for the review step.

    Args:
        scenario (str): Scenario name for the app state (channels and
            storage class are set by prepareUpgrade).

    Returns:
        tuple: (ReviewScreen for the review step, the scenario app).
    """
    mas_app = upgrade_scenario(scenario)
    definition = buildUpgradeWorkflow(mas_app)
    step = next(s for s in definition if s.id == "review")
    screen = step.screen_class(mas_app, step, 2, **step.screen_kwargs)
    return screen, mas_app


def test_review_shows_channels_and_storage_as_markdown():
    """Test that the review Markdown mirrors the classic review settings.

    GIVEN a scenario app in the post-prepareUpgrade state (9.1.x to 9.2.x
        with the pipeline storage class resolved)
    WHEN the review step becomes active (start_dynamic_loaders refreshes
        the Markdown)
    THEN the summary shows the instance ID, both channels, and the pipeline
        storage class and access mode.
    """
    screen, _ = _make_screen("upgrade-9-1-to-9-2")

    result = {}

    async def drive(pilot, app):
        result["text"] = _markdown_text(app.query_one("#review-markdown", Markdown))

    run_screen_pilot(screen, drive)

    for expected in ["inst1", "9.1.x", "9.2.x", "ocs-storagecluster-cephfs", "ReadWriteMany"]:
        assert expected in result["text"], f"Expected '{expected}' in review markdown: {result['text']}"


def test_review_command_panel_renders_buildCommand_output():
    """Test that the command panel renders the real buildCommand() output.

    GIVEN a real UpgradeApp scenario in the post-prepareUpgrade state
    WHEN the review step becomes active
    THEN the command panel shows the generated mas upgrade command — the
        same string the test_upgrade_arg_builder.py round-trip contract
        guarantees the parser accepts — including the selected instance and
        the always-required --no-confirm flag.
    """
    screen, mas_app = _make_screen("upgrade-9-1-to-9-2")

    result = {}

    async def drive(pilot, app):
        result["rendered"] = str(app.query_one("#review-command-text", Static).render())
        result["panel_visible"] = app.query_one("#review-command-panel").display
        result["save_script_visible"] = app.query_one("#btn-save-script", Button).display

    run_screen_pilot(screen, drive)

    assert result["panel_visible"]
    assert result["save_script_visible"]
    assert "mas upgrade" in result["rendered"]
    assert "--mas-instance-id inst1" in result["rendered"]
    assert "--no-confirm" in result["rendered"]


def test_review_renders_placeholders_for_unknown_channel():
    """Test that missing channel state renders placeholders, not crashes.

    GIVEN a scenario app whose channels could not be detected
    WHEN the review step becomes active
    THEN the Markdown renders with "Unknown" channels and em-dash
        placeholders for the unset storage class.
    """
    screen, _ = _make_screen("unknown-channel")

    result = {}

    async def drive(pilot, app):
        result["text"] = _markdown_text(app.query_one("#review-markdown", Markdown))

    run_screen_pilot(screen, drive)

    assert "Unknown" in result["text"]
    assert "—" in result["text"]
