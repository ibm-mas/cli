# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.php
#
# *****************************************************************************

"""Pilot tests for the ReviewScreen non-interactive command panel (tui/screens/review.py).

Drives the review screen with a live pilot: the command panel renders the
command_builder output when supplied (and is hidden when not), Copy Command
places the command on the clipboard, Save Script writes the shared script
format to the builder-supplied filename, and Confirm still advances the
workflow.
"""

from unittest.mock import MagicMock

import pytest
from textual.widgets import Button, Static

from mas.cli.tui.models import WorkflowStep
from mas.cli.tui.screens.review import ReviewScreen
from pilot.harness import click_button, run_screen_pilot

pytestmark = pytest.mark.pilot

COMMAND = "mas update \\\n  --mas-catalog-version v9-261102-amd64 \\\n  --no-confirm\n"


def _make_step() -> WorkflowStep:
    """Return a review WorkflowStep for the screen under test."""
    return WorkflowStep(id="review", heading="Review Settings")


def _make_app():
    """Return a minimal mock MAS CLI app with a params dict."""
    app = MagicMock()
    app.params = {}
    return app


def test_command_panel_renders_builder_output(monkeypatch):
    """Test that the command builder's output is shown in the panel.

    GIVEN a review screen with a command_builder, with a usable clipboard
    WHEN the step becomes active (start_dynamic_loaders refreshes the panel)
    THEN the command text widget shows the rendered command and the Copy
        Command / Save Script buttons are visible.
    """
    import mas.cli.tui.screens.review as review_module

    monkeypatch.setattr(review_module, "clipboardAvailable", lambda: True)
    screen = ReviewScreen(
        _make_app(),
        _make_step(),
        4,
        command_builder=lambda app: COMMAND,
        script_filename_builder=lambda app: "mas-update-v9-261102-amd64.sh",
    )

    async def drive(pilot, app):
        rendered = str(app.query_one("#review-command-text", Static).render())
        assert "mas update" in rendered
        assert "--mas-catalog-version v9-261102-amd64" in rendered
        assert "--no-confirm" in rendered
        assert app.query_one("#review-command-panel").display
        assert app.query_one("#btn-copy-command", Button).display
        assert app.query_one("#btn-save-script", Button).display

    run_screen_pilot(screen, drive)


def test_copy_command_button_hidden_without_clipboard(monkeypatch):
    """Test that Copy Command is hidden when no clipboard is usable.

    GIVEN a review screen with a command_builder, but no clipboard
        mechanism in this environment (container / headless, no
        MAS_CLIPBOARD=osc52)
    WHEN the step becomes active
    THEN the command panel and Save Script are still shown, but Copy
        Command is hidden — the button must not offer an action that
        cannot succeed.
    """
    import mas.cli.tui.screens.review as review_module

    monkeypatch.setattr(review_module, "clipboardAvailable", lambda: False)
    screen = ReviewScreen(
        _make_app(),
        _make_step(),
        4,
        command_builder=lambda app: COMMAND,
        script_filename_builder=lambda app: "mas-update-v9-261102-amd64.sh",
    )

    async def drive(pilot, app):
        assert app.query_one("#review-command-panel").display
        assert not app.query_one("#btn-copy-command", Button).display
        assert app.query_one("#btn-save-script", Button).display

    run_screen_pilot(screen, drive)


def test_command_panel_hidden_without_builder():
    """Test that the panel and its buttons stay hidden without a builder.

    GIVEN a review screen with no command_builder
    WHEN the step becomes active
    THEN the command panel, Copy Command and Save Script are all hidden,
        so workflows without an argBuilder see the original review screen.
    """
    screen = ReviewScreen(_make_app(), _make_step(), 4)

    async def drive(pilot, app):
        assert not app.query_one("#review-command-panel").display
        assert not app.query_one("#btn-copy-command", Button).display
        assert not app.query_one("#btn-save-script", Button).display

    run_screen_pilot(screen, drive)


def test_save_script_hidden_without_filename_builder(monkeypatch):
    """Test that Save Script alone is hidden without a filename builder.

    GIVEN a review screen with a command_builder but no
        script_filename_builder, with a usable clipboard
    WHEN the step becomes active
    THEN the command panel and Copy Command are shown but Save Script is
        hidden.
    """
    import mas.cli.tui.screens.review as review_module

    monkeypatch.setattr(review_module, "clipboardAvailable", lambda: True)
    screen = ReviewScreen(_make_app(), _make_step(), 4, command_builder=lambda app: COMMAND)

    async def drive(pilot, app):
        assert app.query_one("#review-command-panel").display
        assert app.query_one("#btn-copy-command", Button).display
        assert not app.query_one("#btn-save-script", Button).display

    run_screen_pilot(screen, drive)


def test_copy_command_uses_clipboard(monkeypatch):
    """Test that Copy Command places the command on the clipboard.

    GIVEN a review screen with a command_builder, with the clipboard helper
        stubbed to record copies and a usable clipboard reported
    WHEN Copy Command is clicked
    THEN the clipboard receives the rendered command and the status row
        confirms the copy.
    """
    copied = []

    import mas.cli.tui.screens.review as review_module

    monkeypatch.setattr(review_module, "clipboardAvailable", lambda: True)
    monkeypatch.setattr(review_module, "copyToClipboard", lambda text: copied.append(text) or True)
    screen = ReviewScreen(
        _make_app(),
        _make_step(),
        4,
        command_builder=lambda app: COMMAND,
        script_filename_builder=lambda app: "unused.sh",
    )

    async def drive(pilot, app):
        await click_button(pilot, "#btn-copy-command")
        assert copied == [COMMAND]
        status = str(app.query_one("#review-prompt").render())
        assert "copied to clipboard" in status

    run_screen_pilot(screen, drive)


def test_save_script_writes_shared_script_format(tmp_path):
    """Test that Save Script writes the shared script format.

    GIVEN a review screen whose script_filename_builder targets a file in
        tmp_path
    WHEN Save Script is clicked
    THEN the file is written with the shebang + provenance header followed
        by the rendered command (the same format as the interactive
        wizard's save-as-script), and the status row names the file.
    """
    target = tmp_path / "mas-update-v9-261102-amd64.sh"
    screen = ReviewScreen(
        _make_app(),
        _make_step(),
        4,
        command_builder=lambda app: COMMAND,
        script_filename_builder=lambda app: str(target),
    )

    async def drive(pilot, app):
        await click_button(pilot, "#btn-save-script")
        status = str(app.query_one("#review-prompt").render())
        assert str(target) in status
        assert "saved" in status

    run_screen_pilot(screen, drive)

    content = target.read_text()
    assert content.startswith("#!/bin/bash\n# Generated by the MAS CLI interactive wizard\n\n")
    assert content.endswith(COMMAND)


def test_confirm_still_advances_with_command_panel():
    """Test that Confirm & Launch still posts StepCompleted with the panel shown.

    GIVEN a review screen with a command_builder
    WHEN Confirm & Launch is clicked
    THEN the screen posts step_completed for its step index — the command
        panel must not interfere with the workflow advance.
    """
    screen = ReviewScreen(
        _make_app(),
        _make_step(),
        4,
        command_builder=lambda app: COMMAND,
        script_filename_builder=lambda app: "unused.sh",
    )

    async def drive(pilot, app):
        await click_button(pilot, "#btn-confirm")

    app = run_screen_pilot(screen, drive)
    assert app.posted == [("step_completed", 4)]
