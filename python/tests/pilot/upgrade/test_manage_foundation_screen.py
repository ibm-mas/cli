# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
# *****************************************************************************

"""Pilot tests for the upgrade command's manage-foundation step screen.

Mounts the real manage-foundation WorkflowStep (from buildUpgradeWorkflow)
in a StepScreen against a scenario app whose upgrade needs to install
Manage Foundation, verifying that the entitlement key and storage class
fields render, that the optional fields do not block advancement, and that
a failing prepareManageFoundation validator surfaces its error in the
reserved status row without advancing the step.
"""

import pytest
from textual.widgets import Button, Input, Label

from mas.cli.tui.screens.step import StepScreen
from mas.cli.upgrade.workflow import buildUpgradeWorkflow
from pilot.harness import click_button, run_screen_pilot, wait_for
from scenarios.upgrade import upgrade_scenario

pytestmark = pytest.mark.pilot


def _make_screen(scenario="manage-foundation", prepareManageFoundation=None):
    """Return (screen, mas_app) for the manage-foundation step.

    Args:
        scenario (str): Scenario name for the app state (isManageFoundation
            is set by prepareUpgrade).
        prepareManageFoundation (Callable, optional): Override for the step
            validator; defaults to the scenario app's real method.

    Returns:
        tuple: (StepScreen for the manage-foundation step, the scenario app).
    """
    mas_app = upgrade_scenario(scenario)
    if prepareManageFoundation is not None:
        mas_app.prepareManageFoundation = prepareManageFoundation
    definition = buildUpgradeWorkflow(mas_app)
    step = next(s for s in definition if s.id == "manage-foundation")
    return StepScreen(mas_app, step, 3), mas_app


def test_manage_foundation_renders_entitlement_and_storage_fields():
    """Test that the step collects the entitlement key and storage classes.

    GIVEN a scenario app whose upgrade needs Manage Foundation
    WHEN the manage-foundation step screen is shown
    THEN a password input for the entitlement key and plain inputs for the
        (optional) RWO / RWX storage classes are rendered.
    """
    screen, _ = _make_screen()

    result = {}

    async def drive(pilot, app):
        result["entitlement"] = app.query_one("#field-ibm_entitlement_key", Input)
        result["rwo"] = app.query_one("#field-storage_class_rwo", Input)
        result["rwx"] = app.query_one("#field-storage_class_rwx", Input)

    run_screen_pilot(screen, drive)

    assert result["entitlement"].password is True
    assert result["rwo"] is not None
    assert result["rwx"] is not None


def test_blank_fields_do_not_block_required_validation():
    """Test that every manage-foundation field is optional at field level.

    GIVEN a scenario app whose upgrade needs Manage Foundation
    WHEN Next is clicked with all fields left blank (the entitlement key is
        read from the cluster and the storage classes auto-detected by the
        validator, not by field validation)
    THEN the validator runs and the step completes — required-field
        validation does not block on the empty inputs.
    """
    screen, mas_app = _make_screen(prepareManageFoundation=lambda: None)

    async def drive(pilot, app):
        await click_button(pilot, "#btn-next-manage-foundation")
        await wait_for(lambda: app.posted == [("step_completed", 3)])

    run_screen_pilot(screen, drive)

    # Blank inputs are written as empty strings; the validator resolves them
    assert mas_app.params.get("ibm_entitlement_key") == ""


def test_validator_failure_shown_in_status_row():
    """Test that a failing prepareManageFoundation blocks and shows inline.

    GIVEN a scenario app whose prepareManageFoundation raises (e.g. a
        storage class that is not on the cluster)
    WHEN the entitlement key is entered and Next is clicked
    THEN the error appears in the reserved status row and no StepCompleted
        is posted, so the user can correct the inputs and retry.
    """

    def _fail():
        raise RuntimeError("Storage class 'missing-sc' specified via --storage-class-rwo is not available on this cluster.")

    screen, mas_app = _make_screen(prepareManageFoundation=_fail)

    result = {}

    async def drive(pilot, app):
        app.query_one("#field-ibm_entitlement_key", Input).value = "ent-key"
        await pilot.pause()
        await click_button(pilot, "#btn-next-manage-foundation")
        await wait_for(lambda: "missing-sc" in str(app.query_one("#validator-error-manage-foundation", Label).render()))
        result["posted"] = list(app.posted)
        result["next_disabled"] = app.query_one("#btn-next-manage-foundation", Button).disabled

    run_screen_pilot(screen, drive)

    # The field values are still written to params even when validation
    # fails, so the user's entries survive going back and returning.
    assert mas_app.params["ibm_entitlement_key"] == "ent-key"
    assert result["posted"] == []
    assert result["next_disabled"] is False


def test_successful_validation_advances_and_writes_params():
    """Test that a successful validator run writes the inputs and advances.

    GIVEN a scenario app whose prepareManageFoundation succeeds
    WHEN the entitlement key and storage classes are entered and Next clicked
    THEN the field values are written to the app params (ready for the
        validator's configuration and the pipeline launch) and the step
        completes.
    """
    screen, mas_app = _make_screen(prepareManageFoundation=lambda: None)

    async def drive(pilot, app):
        app.query_one("#field-ibm_entitlement_key", Input).value = "ent-key"
        app.query_one("#field-storage_class_rwo", Input).value = "rwo-sc"
        app.query_one("#field-storage_class_rwx", Input).value = "rwx-sc"
        await pilot.pause()
        await click_button(pilot, "#btn-next-manage-foundation")
        await wait_for(lambda: app.posted == [("step_completed", 3)])

    run_screen_pilot(screen, drive)

    assert mas_app.params["ibm_entitlement_key"] == "ent-key"
    assert mas_app.params["storage_class_rwo"] == "rwo-sc"
    assert mas_app.params["storage_class_rwx"] == "rwx-sc"
