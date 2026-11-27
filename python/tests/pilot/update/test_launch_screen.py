# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Pilot tests for the LaunchScreen pipeline submission (tui/screens/launch.py).

Drives the pipeline submission screen with a live pilot against a stubbed
app whose launchUpdate reports progress through the callbacks: a successful
run reveals the Done button, a failure reveals Dismiss with the error.
"""

from unittest.mock import MagicMock

import pytest
from textual.widgets import Button, Label, Static

from mas.cli.tui.models import WorkflowStep
from mas.cli.tui.screens.launch import LaunchScreen
from pilot.harness import click_button, run_screen_pilot, wait_for

pytestmark = pytest.mark.pilot


def _make_screen(launch_update, command_builder=None):
    """Return (screen, mas_app) with launchUpdate stubbed.

    Args:
        launch_update (Callable): Implementation for launchUpdate; it
            receives the progressCallback and startCallback keywords.
        command_builder (Callable, optional): Optional ``(mas_app) -> str``
            renderer for the non-interactive command reference.

    Returns:
        tuple: (LaunchScreen, mas_app stub).
    """
    mas_app = MagicMock()
    mas_app.params = {}
    mas_app.launchUpdate.side_effect = launch_update
    step = WorkflowStep(id="launch", heading="Launch Update")
    return LaunchScreen(mas_app, step, 5, command_builder=command_builder), mas_app


def _succeed(progressCallback=None, startCallback=None):
    """Report every launch stage as succeeding.

    Mirrors the real launchUpdate contract: the Submit PipelineRun stage
    reports the pipeline run URL as its detail (not a completion message),
    because the screen displays that detail as the URL and the Copy URL
    button copies it.
    """
    for label in ("Validate OpenShift Pipelines", "Prepare pipelines namespace", "Install Tekton definitions"):
        startCallback(label)
        progressCallback(label, True, "done")
    startCallback("Submit PipelineRun")
    progressCallback("Submit PipelineRun", True, "https://example.com/pipelinerun")


def test_successful_launch_reveals_done():
    """Test that a successful pipeline submission reveals the Done button.

    GIVEN a stubbed app whose launchUpdate succeeds
    WHEN the launch step becomes active (submission auto-starts)
    THEN every stage is marked completed in the step list and the Done
        button is revealed; clicking it exits with code 0.
    """
    screen, _ = _make_screen(_succeed)

    async def drive(pilot, app):
        await wait_for(lambda: app.query_one("#btn-done", Button).display)
        rendered = " ".join(str(item.query_one(Label).render()) for item in app.query("#launch-step-list ListItem"))
        assert "✓" in rendered
        await click_button(pilot, "#btn-done")

    app = run_screen_pilot(screen, drive)

    assert app.return_value == 0


def test_successful_launch_shows_and_copies_pipeline_url(monkeypatch):
    """Test that the pipeline URL is shown and copied, not the completion message.

    GIVEN a stubbed app whose launchUpdate succeeds, with the Submit
        PipelineRun stage reporting the pipeline URL as its detail, and a
        usable clipboard
    WHEN the launch step becomes active and Copy URL is clicked
    THEN the URL label shows the URL, the Copy URL button is revealed, the
        clipboard receives the URL itself — not a message like
        "PipelineRun for MAS update submitted" — and the button flashes
        "Copied!".
    """
    copied = []

    import mas.cli.tui.screens.launch as launch_module

    monkeypatch.setattr(launch_module, "clipboardAvailable", lambda: True)
    monkeypatch.setattr(launch_module, "copyToClipboard", lambda text: copied.append(text) or True)
    screen, _ = _make_screen(_succeed)

    async def drive(pilot, app):
        await wait_for(lambda: app.query_one("#btn-copy-url", Button).display)
        rendered = app.query_one("#pipeline-url", Label).render()
        assert "https://example.com/pipelinerun" in str(rendered)
        # The URL must carry a link style (rendered by Textual as an OSC 8
        # terminal hyperlink) so ctrl+click opens it even when wrapped.
        link_styles = [str(span.style) for span in getattr(rendered, "spans", [])]
        assert any("link" in style and "https://example.com/pipelinerun" in style for style in link_styles)
        await click_button(pilot, "#btn-copy-url")
        assert copied == ["https://example.com/pipelinerun"]
        assert str(app.query_one("#btn-copy-url", Button).label) == "Copied!"

    run_screen_pilot(screen, drive)


def test_copy_buttons_hidden_without_clipboard(monkeypatch):
    """Test that the copy buttons stay hidden without a usable clipboard.

    GIVEN a stubbed app whose launchUpdate succeeds, but no clipboard
        mechanism in this environment (container / headless, no
        MAS_CLIPBOARD=osc52)
    WHEN the launch step becomes active and the command reference is shown
    THEN the pipeline URL and command text are still revealed, but the Copy
        URL and Copy Command buttons stay hidden.
    """
    import mas.cli.tui.screens.launch as launch_module

    monkeypatch.setattr(launch_module, "clipboardAvailable", lambda: False)
    screen, _ = _make_screen(_succeed, command_builder=lambda app: "mas update --no-confirm")

    async def drive(pilot, app):
        await wait_for(lambda: app.query_one("#btn-done", Button).display)
        await wait_for(lambda: app.query_one("#launch-command-text", Static).display)
        assert app.query_one("#pipeline-url", Label).display
        assert not app.query_one("#btn-copy-url", Button).display
        assert not app.query_one("#btn-copy-command", Button).display

    run_screen_pilot(screen, drive)


def test_status_row_stays_empty_during_successful_launch():
    """Test that the action-bar status row is unused during a successful launch.

    GIVEN a stubbed app whose launchUpdate succeeds
    WHEN the launch step becomes active
    THEN the action-bar status row stays empty throughout the run — the
        pipeline URL is already shown in the content above and the buttons
        label themselves, so there is no guidance text to add.
    """
    screen, _ = _make_screen(_succeed)

    async def drive(pilot, app):
        status = app.query_one("#launch-prompt", Label)
        while not app.query_one("#btn-done", Button).display:
            assert str(status.render()).strip() == ""
            await pilot.pause()
        assert str(status.render()).strip() == ""

    run_screen_pilot(screen, drive)


def test_status_row_stays_empty_on_failed_launch():
    """Test that the action-bar status row is unused when submission fails.

    GIVEN a stubbed app whose launchUpdate raises
    WHEN the launch step becomes active and fails
    THEN the action-bar status row stays empty — there is no pipeline run
        to view and the failure is reported in the step list.
    """

    def _fail(progressCallback=None, startCallback=None):
        startCallback("Validate OpenShift Pipelines")
        progressCallback("Validate OpenShift Pipelines", False, "pipelines not installed")
        raise RuntimeError("Failed to validate OpenShift Pipelines")

    screen, _ = _make_screen(_fail)

    async def drive(pilot, app):
        await wait_for(lambda: app.query_one("#btn-dismiss-error", Button).display)
        assert str(app.query_one("#launch-prompt", Label).render()).strip() == ""

    run_screen_pilot(screen, drive)


def test_failed_copy_does_not_flash_copied(monkeypatch):
    """Test that a failed copy does not claim success.

    GIVEN a stubbed app whose launchUpdate succeeds, a usable clipboard
        reported, but the clipboard helper failing at copy time
    WHEN Copy URL is clicked
    THEN the button label stays "Copy URL" (no false "Copied!") and the
        action-bar status reports the clipboard as unavailable.
    """
    import mas.cli.tui.screens.launch as launch_module

    monkeypatch.setattr(launch_module, "clipboardAvailable", lambda: True)
    monkeypatch.setattr(launch_module, "copyToClipboard", lambda text: False)
    screen, _ = _make_screen(_succeed)

    async def drive(pilot, app):
        await wait_for(lambda: app.query_one("#btn-copy-url", Button).display)
        await click_button(pilot, "#btn-copy-url")
        assert str(app.query_one("#btn-copy-url", Button).label) == "Copy URL"
        status = str(app.query_one("#launch-prompt").render())
        assert "Clipboard is not available" in status

    run_screen_pilot(screen, drive)


def test_failed_launch_reveals_dismiss_with_error():
    """Test that a failed pipeline submission reveals Dismiss with the error.

    GIVEN a stubbed app whose launchUpdate raises
    WHEN the launch step becomes active
    THEN the failing stage is marked with an error, the Dismiss button is
        revealed, the Done button stays hidden, and nothing is posted.
    """

    def _fail(progressCallback=None, startCallback=None):
        startCallback("Validate OpenShift Pipelines")
        progressCallback("Validate OpenShift Pipelines", True, "installed")
        startCallback("Submit PipelineRun")
        progressCallback("Submit PipelineRun", False, "pipeline submission failed")
        raise RuntimeError("Failed to submit PipelineRun")

    screen, _ = _make_screen(_fail)

    async def drive(pilot, app):
        await wait_for(lambda: app.query_one("#btn-dismiss-error", Button).display)
        assert not app.query_one("#btn-done", Button).display
        rendered = " ".join(str(item.query_one(Label).render()) for item in app.query("#launch-step-list ListItem"))
        assert "✗" in rendered
        assert app.posted == []

    run_screen_pilot(screen, drive)


def test_successful_launch_shows_and_copies_noninteractive_command(monkeypatch):
    """Test that the non-interactive command is re-displayed after submission.

    GIVEN a stubbed app whose launchUpdate succeeds, with a command_builder
        wired (as the update workflow does), and the clipboard helper
        stubbed to record copies
    WHEN the launch step becomes active and Copy Command is clicked
    THEN the reference caption and command text are revealed below the
        pipeline URL, and the clipboard receives the rendered command —
        the TUI equivalent of the CLI re-printing the command at end of run.
    """
    command = "mas update \\n  --mas-catalog-version v9-261102-amd64 \\n  --no-confirm\n"
    copied = []

    import mas.cli.tui.screens.launch as launch_module

    monkeypatch.setattr(launch_module, "clipboardAvailable", lambda: True)
    monkeypatch.setattr(launch_module, "copyToClipboard", lambda text: copied.append(text) or True)
    screen, _ = _make_screen(_succeed, command_builder=lambda app: command)

    async def drive(pilot, app):
        await wait_for(lambda: app.query_one("#btn-done", Button).display)
        await wait_for(lambda: app.query_one("#btn-copy-command", Button).display)
        caption = str(app.query_one("#launch-command-caption", Label).render())
        assert "non-interactive command" in caption
        rendered = str(app.query_one("#launch-command-text", Static).render())
        assert "mas update" in rendered
        assert "--no-confirm" in rendered
        await click_button(pilot, "#btn-copy-command")
        assert copied == [command]

    run_screen_pilot(screen, drive)


def test_failed_launch_does_not_show_noninteractive_command():
    """Test that the command reference stays hidden on failure.

    GIVEN a stubbed app whose launchUpdate raises, with a command_builder wired
    WHEN the launch step becomes active and fails
    THEN the command reference caption, text and Copy Command button all
        stay hidden — there is nothing to re-run when nothing was launched.
    """

    def _fail(progressCallback=None, startCallback=None):
        raise RuntimeError("Failed to submit PipelineRun")

    screen, _ = _make_screen(_fail, command_builder=lambda app: "mas update --no-confirm")

    async def drive(pilot, app):
        await wait_for(lambda: app.query_one("#btn-dismiss-error", Button).display)
        assert not app.query_one("#launch-command-caption", Label).display
        assert not app.query_one("#launch-command-text", Static).display
        assert not app.query_one("#btn-copy-command", Button).display

    run_screen_pilot(screen, drive)
