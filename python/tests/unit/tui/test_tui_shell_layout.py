# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for TextualShell import guard, instantiation, and two-pane layout.

Covers: import guard, shell construction, sidebar item count,
skipped-step CSS class, and active-step heading visibility.
"""

import asyncio
import sys
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
# Import guard
# ---------------------------------------------------------------------------


def test_import_error_without_textual(monkeypatch):
    """Test that importing shell without textual raises ImportError with install hint.

    GIVEN textual is not installed (simulated via monkeypatch)
    WHEN mas.cli.tui.shell is imported
    THEN an ImportError is raised containing the install hint string.
    """
    real_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

    def mock_import(name, *args, **kwargs):
        if name == "textual" or name.startswith("textual."):
            raise ModuleNotFoundError(f"No module named '{name}'")
        return real_import(name, *args, **kwargs)

    cached = [k for k in sys.modules if k == "mas.cli.tui.shell" or k.startswith("mas.cli.tui.shell.")]
    for k in cached:
        del sys.modules[k]

    monkeypatch.setattr("builtins.__import__", mock_import)

    with pytest.raises(ImportError, match="pip install mas-cli\\[tui\\]"):
        import mas.cli.tui.shell  # noqa: F401


# ---------------------------------------------------------------------------
# Instantiation
# ---------------------------------------------------------------------------


def test_shell_instantiates():
    """Test that TextualShell can be constructed without raising.

    GIVEN a mock app instance and a single-step WorkflowDefinition
    WHEN TextualShell is instantiated
    THEN no exception is raised.
    """
    from mas.cli.tui.shell import TextualShell

    shell = TextualShell(_make_app(), [WorkflowStep(id="test-step", heading="Test Step")])
    assert shell is not None


# ---------------------------------------------------------------------------
# Sidebar and content layout
# ---------------------------------------------------------------------------


def test_sidebar_has_one_item_per_step():
    """Test that the sidebar contains exactly one list item per workflow step.

    GIVEN a WorkflowDefinition with two unconditional steps
    WHEN TextualShell is run
    THEN the sidebar ListView has exactly 2 ListItem children.
    """
    from mas.cli.tui.shell import TextualShell
    from textual.widgets import ListItem

    definition = [
        WorkflowStep(id="step-one", heading="Step One"),
        WorkflowStep(id="step-two", heading="Step Two"),
    ]

    async def run():
        shell = TextualShell(_make_app(), definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            return len(list(shell.query(ListItem)))

    assert asyncio.run(run()) == 2


def test_condition_false_step_renders_greyed():
    """Test that a step with a False condition has the skipped CSS class in the sidebar.

    GIVEN a two-step definition where the second step has condition=lambda p: False
    WHEN TextualShell is run
    THEN the skipped step has 'step-skipped' CSS class; Review Settings is not greyed.
    """
    from mas.cli.tui.shell import TextualShell

    definition = [
        WorkflowStep(id="step-one", heading="Step One"),
        WorkflowStep(id="step-two", heading="Step Two (Skipped)", condition=lambda p: False),
    ]

    async def run():
        shell = TextualShell(_make_app(), definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            return len(list(shell.query(".step-skipped")))

    assert asyncio.run(run()) == 1


def test_active_step_heading_visible_in_content_area():
    """Test that the first active step's heading appears in the content area.

    GIVEN a single-step WorkflowDefinition with heading="Choose Catalog"
    WHEN TextualShell is run
    THEN the content area contains a Label whose text matches the heading.
    """
    from mas.cli.tui.shell import TextualShell
    from textual.widgets import Label

    definition = [WorkflowStep(id="choose-catalog", heading="Choose Catalog")]

    async def run():
        shell = TextualShell(_make_app(), definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            return [str(lbl.render()) for lbl in shell.query(Label)]

    texts = asyncio.run(run())
    assert any("Choose Catalog" in t for t in texts)
