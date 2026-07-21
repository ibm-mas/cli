# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for TextualShell review screen and action overlay.

Covers: review DataTable rendering, sensitive value masking, Confirm button
exit, ActionOverlay push on step action, worker thread execution, overlay
dismissal on success, and error handling with Dismiss button.
"""

import asyncio
import threading
import pytest
from unittest.mock import MagicMock

from mas.cli.tui.models import WorkflowStep, WorkflowSummaryItem

pytestmark = pytest.mark.tui


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_app(params: dict = None):
    """Create a minimal mock MAS CLI app with a params dict.

    Args:
        params (dict, optional): Initial params. Defaults to empty dict.

    Returns:
        MagicMock: Mock app instance with .params attribute.
    """
    m = MagicMock()
    m.params = params if params is not None else {}
    return m


# ---------------------------------------------------------------------------
# Review screen
# ---------------------------------------------------------------------------


def test_review_screen_shows_summary_markdown():
    """Test that the review screen shows a Markdown widget with summary items.

    GIVEN a workflow with one step that has summary items
    WHEN all steps complete and the review screen is shown
    THEN a Markdown widget with id 'review-markdown' is present.
    """
    from mas.cli.tui.shell import TextualShell
    from textual.widgets import Markdown

    mas_app = _make_app({"catalog_version": "v9-amd64-241205-1"})
    definition = [
        WorkflowStep(
            id="step-one",
            heading="Step One",
            summary=[WorkflowSummaryItem(label="Catalog Version", param="catalog_version")],
        ),
    ]

    async def run():
        shell = TextualShell(mas_app, definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            await pilot.click(".btn-next")
            await pilot.pause()
            md = shell.query_one("#review-markdown", Markdown)
            return md is not None

    assert asyncio.run(run())


def test_review_screen_masks_sensitive_item():
    """Test that sensitive summary items are shown as '***' in the review markdown.

    GIVEN a workflow with a sensitive summary item
    WHEN the review screen is displayed
    THEN the rendered markdown source contains '***' and not the real value.
    """
    from mas.cli.tui.shell import TextualShell
    from mas.cli.tui.shell import ReviewScreen

    mas_app = _make_app({"login_token": "super-secret-token"})
    definition = [
        WorkflowStep(
            id="step-one",
            heading="Step One",
            summary=[WorkflowSummaryItem(label="Token", param="login_token", sensitive=True)],
        ),
    ]

    async def run():
        shell = TextualShell(mas_app, definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            await pilot.click(".btn-next")
            await pilot.pause()
            review = shell.query_one("#review-panel", ReviewScreen)
            return review._build_markdown()

    md_text = asyncio.run(run())
    assert "***" in md_text
    assert "super-secret-token" not in md_text


def test_confirm_button_triggers_workflow_confirmed():
    """Test that the Confirm button causes the shell to exit cleanly.

    GIVEN a single-step workflow navigated to the review screen
    WHEN the Confirm button is clicked
    THEN the shell's return_value is 0 (success).
    """
    from mas.cli.tui.shell import TextualShell

    mas_app = _make_app()
    definition = [WorkflowStep(id="step-one", heading="Step One")]

    async def run():
        shell = TextualShell(mas_app, definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            await pilot.click(".btn-next")
            await pilot.pause()
            await pilot.click("#btn-confirm")
            await pilot.pause()
        return shell.return_value

    result = asyncio.run(run())
    assert result == 0


# ---------------------------------------------------------------------------
# Action overlay
# ---------------------------------------------------------------------------


def test_step_with_action_pushes_action_overlay():
    """Test that a step with an action callable shows the ActionOverlay.

    GIVEN a step whose action blocks on an Event (controllable timing)
    WHEN Next is clicked
    THEN an ActionOverlay modal is in the screen stack while the action runs.
    """
    from mas.cli.tui.shell import TextualShell, ActionOverlay

    mas_app = _make_app()
    action_started = threading.Event()
    action_proceed = threading.Event()

    def blocking_action():
        action_started.set()
        action_proceed.wait(timeout=5)

    definition = [
        WorkflowStep(id="step-one", heading="Step One", action=blocking_action),
        WorkflowStep(id="step-two", heading="Step Two"),
    ]

    async def run():
        shell = TextualShell(mas_app, definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            await pilot.click(".btn-next")
            action_started.wait(timeout=3)
            await pilot.pause()
            result = any(isinstance(s, ActionOverlay) for s in shell.screen_stack)
            action_proceed.set()
            await pilot.pause()
            return result

    assert asyncio.run(run())


def test_action_runs_in_worker_thread():
    """Test that the step action callable is not called on the event loop thread.

    GIVEN a step action that records its thread identity
    WHEN Next is clicked
    THEN the recorded thread is not the main thread.
    """
    from mas.cli.tui.shell import TextualShell

    mas_app = _make_app()
    thread_record = []

    def record_thread():
        thread_record.append(threading.current_thread())

    definition = [
        WorkflowStep(id="step-one", heading="Step One", action=record_thread),
        WorkflowStep(id="step-two", heading="Step Two"),
    ]

    async def run():
        shell = TextualShell(mas_app, definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            await pilot.click(".btn-next")
            await pilot.pause(0.5)

    asyncio.run(run())
    assert len(thread_record) == 1
    assert thread_record[0] is not threading.main_thread()


def test_action_overlay_dismissed_on_success():
    """Test that the ActionOverlay is dismissed after a successful action.

    GIVEN a step with a fast no-op action
    WHEN the action completes
    THEN the ActionOverlay is no longer in the screen stack.
    """
    from mas.cli.tui.shell import TextualShell, ActionOverlay

    mas_app = _make_app()
    definition = [
        WorkflowStep(id="step-one", heading="Step One", action=lambda: None),
        WorkflowStep(id="step-two", heading="Step Two"),
    ]

    async def run():
        shell = TextualShell(mas_app, definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            await pilot.click(".btn-next")
            await pilot.pause(0.5)
            return any(isinstance(s, ActionOverlay) for s in shell.screen_stack)

    assert asyncio.run(run()) is False


def test_action_overlay_shows_error_on_exception():
    """Test that ActionOverlay stays visible and shows Dismiss button when action raises.

    GIVEN a step action that raises RuntimeError
    WHEN the action runs
    THEN the ActionOverlay remains in the screen stack (not auto-dismissed)
    AND the Dismiss button is visible (indicating an error occurred).
    """
    from mas.cli.tui.shell import TextualShell, ActionOverlay
    from textual.widgets import Button

    mas_app = _make_app()

    def bad_action():
        raise RuntimeError("cluster not reachable")

    definition = [
        WorkflowStep(id="step-one", heading="Step One", action=bad_action),
        WorkflowStep(id="step-two", heading="Step Two"),
    ]

    async def run():
        shell = TextualShell(mas_app, definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            await pilot.click(".btn-next")
            await pilot.pause(0.5)
            overlay = next((s for s in shell.screen_stack if isinstance(s, ActionOverlay)), None)
            if overlay is None:
                return False, False
            dismiss_btn = overlay.query_one("#btn-dismiss", Button)
            overlay_present = True
            dismiss_visible = dismiss_btn.display is not False
            return overlay_present, dismiss_visible

    overlay_present, dismiss_visible = asyncio.run(run())
    assert overlay_present
    assert dismiss_visible
