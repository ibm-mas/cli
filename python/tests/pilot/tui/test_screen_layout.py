# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Pilot tests for the shared screen layout contract (phase 3.1 of the
visual polish plan).

Every workflow screen must lay out the same way regardless of its content:

* the scrollable content carries ``.content-scroll`` — one shared rule, so
  the gutter is identical between steps (it previously varied between 0, 1
  and 1 2 depending on the screen);
* screens with actions use the fixed-height ``.action-bar`` pinned below
  the scrollable content, so the content / action-bar boundary sits on the
  same row on every screen;
* the ``.action-status`` row is reserved — it keeps its height whether it
  holds guidance text, an error, or nothing, so revealing an error or a
  button never shifts the layout.
"""

from unittest.mock import MagicMock

import pytest
from textual.widgets import Label

from mas.cli.tui.models import WorkflowField, WorkflowStep, WorkflowSummaryItem
from mas.cli.tui.screens.auto_run import AutoRunScreen
from mas.cli.tui.screens.connect import ConnectStepScreen
from mas.cli.tui.screens.launch import LaunchScreen
from mas.cli.tui.screens.review import ReviewScreen
from mas.cli.tui.screens.step import StepScreen
from pilot.harness import click_button, run_screen_pilot, wait_for

pytestmark = pytest.mark.pilot


def _stub_app(**attrs):
    """Return a mock MAS app with a params dict and optional attributes.

    Args:
        **attrs: Attributes to set on the mock (e.g.
            ``getActiveConsoleURL=lambda: None``).

    Returns:
        MagicMock: App stand-in for screen construction.
    """
    m = MagicMock()
    m.params = {}
    m.getActiveConsoleURL.return_value = None
    for key, value in attrs.items():
        setattr(m, key, value)
    return m


def _screens():
    """Return one instance of every screen type that renders content.

    Returns:
        list[tuple[str, Widget]]: (name, screen) pairs, each constructed
        the way the shell would mount it.
    """
    return [
        ("step", StepScreen(_stub_app(), WorkflowStep(id="s1", heading="Step"), 0)),
        ("auto-run", AutoRunScreen(_stub_app(), WorkflowStep(id="dependency-checks", heading="Checks"), 0)),
        ("launch", LaunchScreen(_stub_app(), WorkflowStep(id="launch", heading="Launch"), 0)),
        (
            "review",
            ReviewScreen(
                _stub_app(),
                WorkflowStep(id="review", heading="Review", summary=[WorkflowSummaryItem(label="A", param="a")]),
                0,
            ),
        ),
        ("connect", ConnectStepScreen(_stub_app(), WorkflowStep(id="connect-cluster", heading="Connect"), 0)),
    ]


def test_action_bar_fixed_height_and_boundary():
    """Test that the action bar is pinned at a fixed height on every screen.

    GIVEN each screen that renders an action bar (step, auto-run, launch,
        review, connect)
    WHEN the screen is shown at the pilot default size
    THEN the bar is exactly 6 rows tall with a one-row status row, and its
        top edge sits at the same row on every screen (panel height minus
        the bar height) — the content / action-bar boundary does not move
        between steps.
    """
    boundaries = {}

    for name, screen in _screens():
        result = {}

        async def drive(pilot, app):
            await wait_for(lambda: app.query(".action-bar"))
            bar = app.query_one(".action-bar")
            panel = app.screen.children[0]
            result["bar_height"] = bar.region.height
            result["status_height"] = app.query_one(".action-status").region.height
            result["boundary"] = bar.region.y
            result["panel_height"] = panel.region.height

        run_screen_pilot(screen, drive)

        assert result["bar_height"] == 6, f"{name}: action bar height"
        assert result["status_height"] == 1, f"{name}: status row height"
        boundaries[name] = result["boundary"] - result["panel_height"]

    # The boundary sits at the same offset from the bottom of the panel on
    # every screen (a fixed 6-row bar), so switching steps never moves it.
    assert len(set(boundaries.values())) == 1
    assert boundaries["step"] == -6


def test_content_scroll_padding_is_uniform():
    """Test that every screen's scrollable content uses the shared gutter.

    GIVEN each screen type (including the connect screen, whose root is
        itself the scrollable content)
    WHEN the screen is shown
    THEN its .content-scroll area applies the shared 1 2 padding and the
        content starts at the same column on every screen.
    """
    for name, screen in _screens():
        result = {}

        async def drive(pilot, app):
            scroll = app.query_one(".content-scroll")
            result["padding"] = (scroll.styles.padding.top, scroll.styles.padding.right, scroll.styles.padding.bottom, scroll.styles.padding.left)
            result["content_x"] = scroll.content_region.x

        run_screen_pilot(screen, drive)

        assert result["padding"] == (1, 2, 1, 2), f"{name}: .content-scroll padding"
        assert result["content_x"] == 2, f"{name}: content gutter position"


def test_action_buttons_have_consistent_spacing():
    """Test that the action bar's buttons keep a consistent gap.

    GIVEN the review screen with all four action buttons visible (a
        command builder is supplied so Copy Command and Save Script show)
    WHEN the screen is shown
    THEN consecutive visible buttons are separated by the same 2-cell
        gap — Textual buttons carry no default margin, so without the
        shared rule they render flush against each other — and every
        button sits on the same row at the same height.
    """
    screen = ReviewScreen(
        _stub_app(),
        WorkflowStep(id="review", heading="Review", summary=[WorkflowSummaryItem(label="A", param="a")]),
        0,
        command_builder=lambda app: "mas update --example",
        script_filename_builder=lambda app: "mas-update.sh",
    )
    result = {}

    async def drive(pilot, app):
        buttons = sorted(
            (b for b in app.query(".action-buttons > Button") if b.display),
            key=lambda b: b.region.x,
        )
        result["count"] = len(buttons)
        result["gaps"] = [buttons[i + 1].region.x - (buttons[i].region.x + buttons[i].region.width) for i in range(len(buttons) - 1)]
        result["rows"] = {b.region.y for b in buttons}
        result["heights"] = {b.region.height for b in buttons}

    run_screen_pilot(screen, drive)

    assert result["count"] == 4, "all four review buttons visible"
    assert result["gaps"] == [2, 2, 2], "uniform 2-cell gap between buttons"
    assert len(result["rows"]) == 1, "buttons share one row"
    assert len(result["heights"]) == 1, "buttons share one height"


def test_step_validator_error_uses_reserved_status_row():
    """Test that a validator error fills the reserved status row without shifting the layout.

    GIVEN a step with a validator that raises
    WHEN the user clicks Next and the validator fails
    THEN the error text appears in the action bar's status row with the
        error styling, the bar keeps its height (the row was reserved), and
        the workflow does not advance.
    """

    def _bad_validator():
        raise RuntimeError("validation exploded")

    step = WorkflowStep(
        id="validated",
        heading="Validated Step",
        fields=[WorkflowField(id="name", label="Name", type="string", default="x")],
        validator=_bad_validator,
    )
    screen = StepScreen(_stub_app(), step, 0)

    async def drive(pilot, app):
        bar = app.query_one(".action-bar")
        height_before = bar.region.height
        status = app.query_one("#validator-error-validated", Label)
        assert not status.has_class("action-status--error")
        await click_button(pilot, "#btn-next-validated")
        await wait_for(lambda: status.has_class("action-status--error"))
        assert "validation exploded" in str(status.render())
        assert bar.region.height == height_before
        assert app.posted == []

    run_screen_pilot(screen, drive)
