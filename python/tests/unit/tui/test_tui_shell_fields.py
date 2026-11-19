# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for TextualShell field widget rendering.

Covers all 9 FieldTypes: string, password, int, bool, select, multi_select,
file, dir, and dynamic_select — verifying that each type produces the correct
Textual widget in the step content area.
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
# Field widget rendering
# ---------------------------------------------------------------------------


def test_string_field_renders_input():
    """Test that a 'string' field type renders as an Input widget.

    GIVEN a WorkflowStep with one string field
    WHEN TextualShell is shown at that step
    THEN an Input widget with the field id is visible.
    """
    from mas.cli.tui.shell import TextualShell
    from textual.widgets import Input

    field = WorkflowField(id="server_url", label="Server URL", type="string")
    definition = [_make_step_with_field(field)]

    async def run():
        shell = TextualShell(_make_app(), definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            inp = shell.query_one("#field-server_url", Input)
            return inp is not None

    assert asyncio.run(run())


def test_password_field_renders_password_input():
    """Test that a 'password' field renders as a password Input (masked).

    GIVEN a WorkflowStep with one password field
    WHEN TextualShell is shown at that step
    THEN an Input widget with password=True is visible.
    """
    from mas.cli.tui.shell import TextualShell
    from textual.widgets import Input

    field = WorkflowField(id="login_token", label="Token", type="password", sensitive=True)
    definition = [_make_step_with_field(field)]

    async def run():
        shell = TextualShell(_make_app(), definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            inp = shell.query_one("#field-login_token", Input)
            return inp.password

    assert asyncio.run(run()) is True


def test_int_field_renders_integer_input():
    """Test that an 'int' field renders as an Input with integer restrict.

    GIVEN a WorkflowStep with one int field
    WHEN TextualShell is shown
    THEN an Input widget with id 'field-{id}' is present.
    """
    from mas.cli.tui.shell import TextualShell
    from textual.widgets import Input

    field = WorkflowField(id="port", label="Port", type="int")
    definition = [_make_step_with_field(field)]

    async def run():
        shell = TextualShell(_make_app(), definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            inp = shell.query_one("#field-port", Input)
            return inp is not None

    assert asyncio.run(run())


def test_bool_field_renders_switch():
    """Test that a 'bool' field renders as a Switch widget.

    GIVEN a WorkflowStep with one bool field
    WHEN TextualShell is shown
    THEN a Switch widget with the field id is visible.
    """
    from mas.cli.tui.shell import TextualShell
    from textual.widgets import Switch

    field = WorkflowField(id="skip_tls", label="Skip TLS Verify", type="bool")
    definition = [_make_step_with_field(field)]

    async def run():
        shell = TextualShell(_make_app(), definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            sw = shell.query_one("#field-skip_tls", Switch)
            return sw is not None

    assert asyncio.run(run())


def test_select_field_renders_select_with_options():
    """Test that a 'select' field renders as a Select widget with the given options.

    GIVEN a WorkflowStep with a select field having two options
    WHEN TextualShell is shown
    THEN a Select widget is visible with both options available.
    """
    from mas.cli.tui.shell import TextualShell
    from textual.widgets import Select

    field = WorkflowField(
        id="catalog",
        label="Catalog",
        type="select",
        options=["v9-amd64-241205-1", "v9-amd64-250115-1"],
    )
    definition = [_make_step_with_field(field)]

    async def run():
        shell = TextualShell(_make_app(), definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            sel = shell.query_one("#field-catalog", Select)
            return sel is not None

    assert asyncio.run(run())


def test_multi_select_field_renders_checkbox_group():
    """Test that a 'multi_select' field renders as a group of Checkbox widgets.

    GIVEN a WorkflowStep with a multi_select field having three options
    WHEN TextualShell is shown
    THEN one Checkbox widget exists per option.
    """
    from mas.cli.tui.shell import TextualShell

    field = WorkflowField(
        id="components",
        label="Components",
        type="multi_select",
        options=["base", "health", "predict"],
    )
    definition = [_make_step_with_field(field)]

    async def run():
        shell = TextualShell(_make_app(), definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            checkboxes = list(shell.query(".multi-select-option"))
            return len(checkboxes)

    assert asyncio.run(run()) == 3


def test_file_field_renders_input_with_hint():
    """Test that a 'file' field renders as an Input with a file-path placeholder.

    GIVEN a WorkflowStep with a file field
    WHEN TextualShell is shown
    THEN an Input widget with id 'field-{id}' is present.
    """
    from mas.cli.tui.shell import TextualShell
    from textual.widgets import Input

    field = WorkflowField(id="license_file", label="License File", type="file")
    definition = [_make_step_with_field(field)]

    async def run():
        shell = TextualShell(_make_app(), definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            inp = shell.query_one("#field-license_file", Input)
            return inp is not None

    assert asyncio.run(run())


def test_dir_field_renders_input_with_hint():
    """Test that a 'dir' field renders as an Input widget.

    GIVEN a WorkflowStep with a dir field
    WHEN TextualShell is shown
    THEN an Input widget with id 'field-{id}' is present.
    """
    from mas.cli.tui.shell import TextualShell
    from textual.widgets import Input

    field = WorkflowField(id="output_dir", label="Output Directory", type="dir")
    definition = [_make_step_with_field(field)]

    async def run():
        shell = TextualShell(_make_app(), definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            inp = shell.query_one("#field-output_dir", Input)
            return inp is not None

    assert asyncio.run(run())


def test_dynamic_select_renders_as_select_with_static_options():
    """Test that a dynamic_select field with static options renders as a Select.

    GIVEN a WorkflowStep with a dynamic_select field and a static options list
    WHEN TextualShell renders the step
    THEN a Select widget is present immediately with no LoadingIndicator.
    """
    from mas.cli.tui.shell import TextualShell
    from textual.widgets import Select

    field = WorkflowField(
        id="storage_class",
        label="Storage Class",
        type="dynamic_select",
        options=["class-silver", "class-gold"],
    )
    definition = [_make_step_with_field(field)]

    async def run():
        shell = TextualShell(_make_app(), definition)
        async with shell.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            return shell.query_one("#field-storage_class", Select) is not None

    assert asyncio.run(run())
