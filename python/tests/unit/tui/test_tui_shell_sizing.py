# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for TextualShell sizing constraints (phase 2 of the visual polish plan).

Covers: terminal-too-small notice, responsive sidebar hiding, and the
content / dialog max-width caps on wide terminals.
"""

import asyncio
import pytest
from unittest.mock import MagicMock

from mas.cli.tui.models import WorkflowStep

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
# Terminal-too-small notice
# ---------------------------------------------------------------------------


def test_too_small_terminal_shows_notice():
    """Test that a terminal below the minimum size shows the blocking notice.

    GIVEN a terminal smaller than TextualShell.MIN_WIDTH x MIN_HEIGHT
    WHEN TextualShell is run
    THEN a TerminalTooSmallScreen is pushed on top of the screen stack.
    """
    from mas.cli.tui.screens import TerminalTooSmallScreen
    from mas.cli.tui.shell import TextualShell

    definition = [WorkflowStep(id="test-step", heading="Test Step")]

    async def run():
        shell = TextualShell(_make_app(), definition)
        async with shell.run_test(size=(50, 15)) as pilot:
            await pilot.pause()
            return isinstance(shell.screen, TerminalTooSmallScreen)

    assert asyncio.run(run()) is True


def test_notice_removed_when_terminal_recovers():
    """Test that the too-small notice is removed once the terminal grows.

    GIVEN the shell running with the too-small notice showing
    WHEN the terminal is resized above the minimum size
    THEN the notice is popped and the workflow screen is on top again.
    """
    from mas.cli.tui.screens import TerminalTooSmallScreen
    from mas.cli.tui.shell import TextualShell

    definition = [WorkflowStep(id="test-step", heading="Test Step")]

    async def run():
        shell = TextualShell(_make_app(), definition)
        async with shell.run_test(size=(50, 15)) as pilot:
            await pilot.pause()
            was_shown = isinstance(shell.screen, TerminalTooSmallScreen)
            await pilot.resize_terminal(100, 30)
            await pilot.pause()
            still_shown = isinstance(shell.screen, TerminalTooSmallScreen)
            return was_shown, still_shown

    was_shown, still_shown = asyncio.run(run())
    assert was_shown is True
    assert still_shown is False


def test_notice_not_shown_at_normal_size():
    """Test that the too-small notice never appears at a normal terminal size.

    GIVEN a terminal at the pilot default size (80x24)
    WHEN TextualShell is run
    THEN no TerminalTooSmallScreen is pushed.
    """
    from mas.cli.tui.screens import TerminalTooSmallScreen
    from mas.cli.tui.shell import TextualShell

    definition = [WorkflowStep(id="test-step", heading="Test Step")]

    async def run():
        shell = TextualShell(_make_app(), definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            return isinstance(shell.screen, TerminalTooSmallScreen)

    assert asyncio.run(run()) is False


# ---------------------------------------------------------------------------
# Responsive sidebar
# ---------------------------------------------------------------------------


def test_sidebar_hidden_on_narrow_terminal():
    """Test that the sidebar is hidden below the 100-column breakpoint.

    GIVEN a 90-column terminal (below the -narrow breakpoint)
    WHEN TextualShell is run, then the terminal is widened to 120 columns
    THEN the sidebar is hidden when narrow and visible once widened.
    """
    from mas.cli.tui.shell import TextualShell

    definition = [WorkflowStep(id="test-step", heading="Test Step")]

    async def run():
        shell = TextualShell(_make_app(), definition)
        async with shell.run_test(size=(90, 24)) as pilot:
            await pilot.pause()
            hidden_when_narrow = not shell.query_one("#sidebar").display
            await pilot.resize_terminal(120, 24)
            await pilot.pause()
            visible_when_wide = shell.query_one("#sidebar").display
            return hidden_when_narrow, visible_when_wide

    hidden_when_narrow, visible_when_wide = asyncio.run(run())
    assert hidden_when_narrow is True
    assert visible_when_wide is True


# ---------------------------------------------------------------------------
# Wide-terminal max-width caps
# ---------------------------------------------------------------------------


def test_step_panel_fills_content_area():
    """Test that the step panel expands to fill all horizontal space.

    GIVEN a 160-column terminal
    WHEN TextualShell is run with a generic step
    THEN the step panel's rendered width equals the content area width —
        the RHS is not capped at a fixed readability measure.
    """
    from mas.cli.tui.shell import TextualShell

    definition = [WorkflowStep(id="test-step", heading="Test Step")]

    async def run():
        shell = TextualShell(_make_app(), definition)
        async with shell.run_test(size=(160, 40)) as pilot:
            await pilot.pause()
            panel_width = shell.query_one("#step-panel-test-step").region.width
            content_width = shell.query_one("#step-content").region.width
            return panel_width, content_width

    panel_width, content_width = asyncio.run(run())
    assert panel_width == content_width


def test_params_dialog_capped_on_wide_terminal():
    """Test that the params dialog is capped at the readability measure.

    GIVEN a 160-column terminal with the shell running
    WHEN the params overlay is opened via the ``p`` binding
    THEN the dialog's rendered width does not exceed 100 cells.
    """
    from mas.cli.tui.shell import TextualShell

    definition = [WorkflowStep(id="test-step", heading="Test Step")]

    async def run():
        shell = TextualShell(_make_app(), definition)
        async with shell.run_test(size=(160, 40)) as pilot:
            await pilot.pause()
            await pilot.press("p")
            await pilot.pause()
            return shell.screen.query_one("#params-dialog").region.width

    assert asyncio.run(run()) <= 100
