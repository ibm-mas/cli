# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
# *****************************************************************************

"""Pilot tests for the upgrade command's instance-selection step screen.

Mounts the real instance-selection WorkflowStep (from buildUpgradeWorkflow)
in a StepScreen against a scenario app, verifying that the MAS instance
select is populated from the post_connect state and that a failing
prepareUpgrade validator surfaces its error in the reserved status row
without advancing the step.
"""

import pytest
from textual.widgets import Button, Label, Select

from mas.cli.tui.screens.step import StepScreen
from mas.cli.upgrade.workflow import buildUpgradeWorkflow
from pilot.harness import click_button, run_screen_pilot, wait_for
from scenarios.upgrade import upgrade_scenario

pytestmark = pytest.mark.pilot


def _make_screen(scenario, prepareUpgrade=None):
    """Return (screen, mas_app) for the instance-selection step.

    Args:
        scenario (str): Scenario name for the app state
            (_installedInstanceIds is set by the connect step's
            post_connect hook).
        prepareUpgrade (Callable, optional): Override for the step
            validator; defaults to the scenario app's real method.

    Returns:
        tuple: (StepScreen for the instance-selection step, the scenario app).
    """
    mas_app = upgrade_scenario(scenario)
    if prepareUpgrade is not None:
        mas_app.prepareUpgrade = prepareUpgrade
    definition = buildUpgradeWorkflow(mas_app)
    step = next(s for s in definition if s.id == "instance-selection")
    return StepScreen(mas_app, step, 1), mas_app


def test_instance_selection_populated_from_post_connect_state():
    """Test that the instance select lists the instances found at connect time.

    GIVEN an app whose post_connect found a single MAS instance
    WHEN the instance-selection step screen is shown
    THEN the mas_instance_id select offers that instance and is pre-selected
        (the only option), so a single-instance cluster needs no selection
        interaction.
    """
    screen, mas_app = _make_screen("single-instance")

    result = {}

    async def drive(pilot, app):
        select = app.query_one("#field-mas_instance_id", Select)
        result["value"] = select.value
        # _options is a list of (value, label) pairs; the blank placeholder
        # has an empty-string value, filtered out by truthiness.
        result["options"] = [value for value, _ in select._options if value]

    run_screen_pilot(screen, drive)

    assert result["value"] == "inst1"
    assert result["options"] == ["inst1"]


def test_instance_selection_offers_all_instances():
    """Test that every instance found at connect time is offered.

    GIVEN an app whose post_connect found two MAS instances
    WHEN the instance-selection step screen is shown
    THEN the select offers both instances (sorted, first pre-selected).
    """
    screen, _ = _make_screen("multiple-instances")

    result = {}

    async def drive(pilot, app):
        select = app.query_one("#field-mas_instance_id", Select)
        result["value"] = select.value
        result["options"] = [value for value, _ in select._options if value]

    run_screen_pilot(screen, drive)

    assert result["options"] == ["dev", "prod"]
    assert result["value"] == "dev"


def test_instance_selection_writes_param_on_next():
    """Test that Next writes the selected instance to the app params.

    GIVEN an app whose post_connect found one MAS instance (pre-selected)
    WHEN Next is clicked and the validator succeeds
    THEN mas_instance_id is written to params and the step completes.
    """
    screen, mas_app = _make_screen("single-instance", prepareUpgrade=lambda: None)

    async def drive(pilot, app):
        await click_button(pilot, "#btn-next-instance-selection")
        await wait_for(lambda: app.posted == [("step_completed", 1)])

    run_screen_pilot(screen, drive)

    assert mas_app.params["mas_instance_id"] == "inst1"


def test_validator_failure_shown_in_status_row():
    """Test that a failing prepareUpgrade blocks advancement and shows inline.

    GIVEN an app whose prepareUpgrade raises (e.g. no upgrade available for
        the selected instance)
    WHEN Next is clicked
    THEN the error message appears in the reserved status row, no
        StepCompleted is posted, and the Next button is re-enabled so the
        user can go back or change selection.
    """

    def _fail():
        raise RuntimeError("No upgrade available, inst1 is already on the latest release 9.3.x-feature")

    screen, mas_app = _make_screen("single-instance", prepareUpgrade=_fail)

    result = {}

    async def drive(pilot, app):
        await click_button(pilot, "#btn-next-instance-selection")
        await wait_for(lambda: "No upgrade available" in str(app.query_one("#validator-error-instance-selection", Label).render()))
        result["posted"] = list(app.posted)
        result["next_disabled"] = app.query_one("#btn-next-instance-selection", Button).disabled

    run_screen_pilot(screen, drive)

    # The selection is still written to params even when validation fails,
    # so going Back and returning keeps the user's choice.
    assert mas_app.params["mas_instance_id"] == "inst1"
    assert result["posted"] == []
    assert result["next_disabled"] is False
