# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Pilot tests for the AutoRunScreen dependency checks (tui/screens/auto_run.py).

Drives the auto-running checklist with a live pilot against a stubbed app
whose runDependencyChecks reports progress through the callbacks: all-pass
reveals Next and advances, a failed check shows a blocking error with Quit.
"""

from unittest.mock import MagicMock

import pytest
from textual.widgets import Button, Label

from mas.cli.tui.models import WorkflowStep
from mas.cli.tui.screens.auto_run import AutoRunScreen
from mas.cli.update.dependencies import dependencyCheckLabels
from pilot.harness import click_button, run_screen_pilot, wait_for

pytestmark = pytest.mark.pilot


def _make_screen(run_checks):
    """Return (screen, mas_app) with runDependencyChecks stubbed.

    Args:
        run_checks (Callable): Implementation for runDependencyChecks; it
            receives the progressCallback and startCallback keywords.

    Returns:
        tuple: (AutoRunScreen, mas_app stub).
    """
    mas_app = MagicMock()
    mas_app.params = {}
    mas_app.runDependencyChecks.side_effect = run_checks
    step = WorkflowStep(id="dependency-checks", heading="Dependency Update Checks")
    return AutoRunScreen(mas_app, step, 2), mas_app


def _all_pass(progressCallback=None, startCallback=None):
    """Report every dependency check as passing."""
    for label in dependencyCheckLabels():
        startCallback(label)
        progressCallback(label, True, "detected")


def test_all_checks_pass_reveals_next_and_advances():
    """Test that a clean dependency-check run reveals Next and advances.

    GIVEN a stubbed app whose dependency checks all pass
    WHEN the screen becomes active (checks auto-run)
    THEN every list item is marked completed, the Next button is revealed,
        and clicking it posts StepCompleted.
    """
    screen, _ = _make_screen(_all_pass)

    async def drive(pilot, app):
        await wait_for(lambda: app.query_one("#btn-next-dep", Button).has_class("dep-ready"))
        items = app.query("#dep-step-list ListItem")
        assert len(items) == len(dependencyCheckLabels())
        await click_button(pilot, "#btn-next-dep")

    app = run_screen_pilot(screen, drive)

    assert ("step_completed", 2) in app.posted


def test_failed_check_blocks_and_shows_quit():
    """Test that a failed dependency check blocks advancement with a visible error.

    GIVEN a stubbed app whose dependency checks raise after one failure
    WHEN the screen becomes active
    THEN the blocking error is shown, the prompt changes, the Quit button
        is revealed, the Next button stays hidden, and nothing is posted.
    """

    def _fail(progressCallback=None, startCallback=None):
        labels = dependencyCheckLabels()
        startCallback(labels[0])
        progressCallback(labels[0], True, "detected")
        startCallback(labels[1])
        progressCallback(labels[1], False, "multiple namespaces detected")
        raise RuntimeError("Dependency checks failed")

    screen, _ = _make_screen(_fail)

    async def drive(pilot, app):
        await wait_for(lambda: "Dependency checks failed" in str(app.query_one("#dep-error-label", Label).render()))
        assert app.query_one("#btn-quit-dep", Button).has_class("dep-failed")
        assert not app.query_one("#btn-next-dep", Button).has_class("dep-ready")
        assert "cannot proceed" in str(app.query_one("#dep-prompt", Label).render())
        assert app.posted == []

    run_screen_pilot(screen, drive)


def test_quit_button_exits_app():
    """Test that the revealed Quit button exits the application with a non-zero code.

    GIVEN a stubbed app whose dependency checks fail (revealing Quit)
    WHEN the user clicks Quit
    THEN the app exits with return code 1.
    """

    def _fail(progressCallback=None, startCallback=None):
        raise RuntimeError("Dependency checks failed")

    screen, _ = _make_screen(_fail)

    async def drive(pilot, app):
        await wait_for(lambda: app.query_one("#btn-quit-dep", Button).has_class("dep-failed"))
        await click_button(pilot, "#btn-quit-dep")

    app = run_screen_pilot(screen, drive)

    assert app.return_value == 1
