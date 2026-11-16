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
from textual.widgets import Button, Label

from mas.cli.tui.models import WorkflowStep
from mas.cli.tui.screens.launch import LaunchScreen
from pilot.harness import click_button, run_screen_pilot, wait_for

pytestmark = pytest.mark.pilot


def _make_screen(launch_update):
    """Return (screen, mas_app) with launchUpdate stubbed.

    Args:
        launch_update (Callable): Implementation for launchUpdate; it
            receives the progressCallback and startCallback keywords.

    Returns:
        tuple: (LaunchScreen, mas_app stub).
    """
    mas_app = MagicMock()
    mas_app.params = {}
    mas_app.launchUpdate.side_effect = launch_update
    step = WorkflowStep(id="launch", heading="Launch Update")
    return LaunchScreen(mas_app, step, 5), mas_app


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
        assert "✅" in rendered
        await click_button(pilot, "#btn-done")

    app = run_screen_pilot(screen, drive)

    assert app.return_value == 0


def test_successful_launch_shows_and_copies_pipeline_url(monkeypatch):
    """Test that the pipeline URL is shown and copied, not the completion message.

    GIVEN a stubbed app whose launchUpdate succeeds, with the Submit
        PipelineRun stage reporting the pipeline URL as its detail
    WHEN the launch step becomes active and Copy URL is clicked
    THEN the URL label shows the URL, the Copy URL button is revealed, and
        the clipboard receives the URL itself — not a message like
        "PipelineRun for MAS update submitted".
    """

    class FakePyperclip:
        """Stand-in for the optional pyperclip module, recording copies."""

        copied = None

        @classmethod
        def copy(cls, text):
            cls.copied = text

    monkeypatch.setattr("mas.cli.tui.screens.launch.pyperclip", FakePyperclip)
    screen, _ = _make_screen(_succeed)

    async def drive(pilot, app):
        await wait_for(lambda: app.query_one("#btn-copy-url", Button).display)
        assert "https://example.com/pipelinerun" in str(app.query_one("#pipeline-url", Label).render())
        await click_button(pilot, "#btn-copy-url")
        assert FakePyperclip.copied == "https://example.com/pipelinerun"

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
        assert "❌" in rendered
        assert app.posted == []

    run_screen_pilot(screen, drive)
