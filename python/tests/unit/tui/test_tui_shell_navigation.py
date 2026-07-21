# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for TextualShell params write-back and step navigation.

Covers: writing string/bool/multi_select values to app.params on Next,
default value pre-filling, required-field validation blocking Next,
step advancement, condition-based skipping, and condition re-evaluation
after params are updated.
"""

import asyncio
import pytest
from unittest.mock import MagicMock

from mas.cli.tui.models import WorkflowField, WorkflowStep

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


def _make_step_with_field(field: WorkflowField) -> WorkflowStep:
    """Return a single WorkflowStep containing one field.

    Args:
        field (WorkflowField): The field to include.

    Returns:
        WorkflowStep: Step containing the field.
    """
    return WorkflowStep(id="test-step", heading="Test", fields=[field])


# ---------------------------------------------------------------------------
# Params write-back
# ---------------------------------------------------------------------------


def test_next_writes_string_to_params():
    """Test that clicking Next stores the string field value in app.params.

    GIVEN a step with a string field pre-filled to "my-value"
    WHEN Next is clicked
    THEN app.params["server_url"] == "my-value".
    """
    from mas.cli.tui.shell import TextualShell

    mas_app = _make_app()
    field = WorkflowField(id="server_url", label="Server URL", type="string", required=False)
    definition = [_make_step_with_field(field)]

    async def run():
        shell = TextualShell(mas_app, definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            from textual.widgets import Input

            inp = shell.query_one("#field-server_url", Input)
            inp.value = "my-value"
            await pilot.click(".btn-next")
            await pilot.pause()

    asyncio.run(run())
    assert mas_app.params.get("server_url") == "my-value"


def test_next_writes_bool_as_true_string():
    """Test that a Switch in 'on' state writes 'true' (string) to params.

    GIVEN a step with a bool field, Switch toggled on
    WHEN Next is clicked
    THEN app.params[id] == "true".
    """
    from mas.cli.tui.shell import TextualShell

    mas_app = _make_app()
    field = WorkflowField(id="skip_tls", label="Skip TLS", type="bool", required=False)
    definition = [_make_step_with_field(field)]

    async def run():
        shell = TextualShell(mas_app, definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            await pilot.click("#field-skip_tls")
            await pilot.pause()
            from textual.widgets import Switch

            sw = shell.query_one("#field-skip_tls", Switch)
            assert sw.value is True
            await pilot.click(".btn-next")
            await pilot.pause()

    asyncio.run(run())
    assert mas_app.params.get("skip_tls") == "true"


def test_next_writes_bool_as_false_string():
    """Test that a Switch in 'off' state writes 'false' (string) to params.

    GIVEN a step with a bool field, Switch left off (default False)
    WHEN Next is clicked
    THEN app.params[id] == "false".
    """
    from mas.cli.tui.shell import TextualShell

    mas_app = _make_app()
    field = WorkflowField(id="skip_tls", label="Skip TLS", type="bool", required=False)
    definition = [_make_step_with_field(field)]

    async def run():
        shell = TextualShell(mas_app, definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            await pilot.click(".btn-next")
            await pilot.pause()

    asyncio.run(run())
    assert mas_app.params.get("skip_tls") == "false"


def test_next_writes_multi_select_as_comma_joined():
    """Test that multi_select checked options write as a comma-joined string.

    GIVEN a multi_select field with options [a, b, c], first two checked
    WHEN Next is clicked
    THEN app.params[id] == "base,health".
    """
    from mas.cli.tui.shell import TextualShell

    mas_app = _make_app()
    field = WorkflowField(
        id="components",
        label="Components",
        type="multi_select",
        options=["base", "health", "predict"],
        required=False,
    )
    definition = [_make_step_with_field(field)]

    async def run():
        shell = TextualShell(mas_app, definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            checkboxes = list(shell.query(".multi-select-option"))
            checkboxes[0].value = True
            checkboxes[1].value = True
            await pilot.pause()
            await pilot.click(".btn-next")
            await pilot.pause()

    asyncio.run(run())
    assert mas_app.params.get("components") == "base,health"


def test_default_value_pre_fills_input():
    """Test that a field with a default value pre-fills the Input widget.

    GIVEN a string field with default="https://api.example.com"
    WHEN the step is shown
    THEN the Input widget's value is "https://api.example.com".
    """
    from mas.cli.tui.shell import TextualShell
    from textual.widgets import Input

    field = WorkflowField(id="api_url", label="API URL", type="string", default="https://api.example.com")
    definition = [_make_step_with_field(field)]

    async def run():
        shell = TextualShell(_make_app(), definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            inp = shell.query_one("#field-api_url", Input)
            return inp.value

    assert asyncio.run(run()) == "https://api.example.com"


def test_required_field_empty_blocks_next():
    """Test that clicking Next with an empty required field does not advance.

    GIVEN a step with one required string field left empty
    WHEN Next is clicked
    THEN the step does not advance (still on same step).
    """
    from mas.cli.tui.shell import TextualShell

    mas_app = _make_app()
    field = WorkflowField(id="instance_id", label="Instance ID", type="string", required=True)
    definition = [
        _make_step_with_field(field),
        WorkflowStep(id="step-two", heading="Step Two"),
    ]

    async def run():
        shell = TextualShell(mas_app, definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            await pilot.click(".btn-next")
            await pilot.pause()
            return shell._active_index

    index = asyncio.run(run())
    assert index == 0  # still on first step


# ---------------------------------------------------------------------------
# Step navigation
# ---------------------------------------------------------------------------


def test_next_advances_sidebar_to_next_step():
    """Test that clicking Next marks current step complete and moves to next step.

    GIVEN a two-step workflow, first step has no required fields
    WHEN Next is clicked on step one
    THEN shell._active_index advances to 1 and sidebar shows step one as completed.
    """
    from mas.cli.tui.shell import TextualShell

    mas_app = _make_app()
    definition = [
        WorkflowStep(id="step-one", heading="Step One"),
        WorkflowStep(id="step-two", heading="Step Two"),
    ]

    async def run():
        shell = TextualShell(mas_app, definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            await pilot.click(".btn-next")
            await pilot.pause()
            active_idx = shell._active_index
            completed_items = list(shell.query(".step-completed"))
            return active_idx, len(completed_items)

    idx, completed_count = asyncio.run(run())
    assert idx == 1
    assert completed_count >= 1


def test_condition_false_step_auto_skipped():
    """Test that a step with False condition is automatically skipped when navigating.

    GIVEN a three-step workflow where step-two has condition=lambda p: False
    WHEN Next is clicked on step-one
    THEN the shell jumps to step-three (index 2), skipping step-two.
    """
    from mas.cli.tui.shell import TextualShell

    mas_app = _make_app()
    definition = [
        WorkflowStep(id="step-one", heading="Step One"),
        WorkflowStep(id="step-two", heading="Step Two (skip)", condition=lambda p: False),
        WorkflowStep(id="step-three", heading="Step Three"),
    ]

    async def run():
        shell = TextualShell(mas_app, definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            await pilot.click(".btn-next")
            await pilot.pause()
            return shell._active_index

    assert asyncio.run(run()) == 2


def test_condition_re_evaluated_after_param_set():
    """Test that step conditions are re-evaluated after a param is set.

    GIVEN a two-step workflow where step-two has condition=lambda p: p.get("x")=="yes"
    WHEN step-one sets params["x"]="yes" via Next
    THEN the shell advances to step-two proving the condition was re-evaluated.
    """
    from mas.cli.tui.shell import TextualShell

    mas_app = _make_app()
    field = WorkflowField(id="x", label="X", type="string", required=False)
    definition = [
        WorkflowStep(id="step-one", heading="Step One", fields=[field]),
        WorkflowStep(id="step-two", heading="Step Two", condition=lambda p: p.get("x") == "yes"),
    ]

    async def run():
        shell = TextualShell(mas_app, definition)
        # size=(200, 50) ensures the Next button is within the rendered viewport
        async with shell.run_test(size=(200, 50)) as pilot:
            await pilot.pause()
            assert shell._active_index == 0
            from textual.widgets import Input

            inp = shell.query_one("#field-x", Input)
            inp.value = "yes"
            await pilot.click(".btn-next")
            await pilot.pause()
            return shell._active_index

    index = asyncio.run(run())
    assert index == 1  # advanced to step-two since condition is now True
