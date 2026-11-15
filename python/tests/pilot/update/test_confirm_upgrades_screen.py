# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Pilot tests for the ConfirmUpgradesScreen (tui/screens/confirm_upgrades.py).

Drives the real screen with a live Textual pilot against real UpdateApp
instances from the shared scenario registry, so the pending-confirmation
helpers compute exactly as production code does. Covers the full
confirm/abort/validation matrix per scenario, including the Db2 v11 to v12
case where entering the license path is itself the confirmation.
"""

import asyncio

import pytest
from textual.widgets import Checkbox, Input, Label

from mas.cli.tui.models import WorkflowStep
from mas.cli.tui.screens.confirm_upgrades import ConfirmUpgradesScreen
from pilot.harness import click_button, run_screen_pilot, wait_for, wait_for_widget
from scenarios.update import update_scenario

pytestmark = pytest.mark.pilot


def _make_screen(scenario: str, step_index: int = 3):
    """Return (screen, mas_app) for a scenario, as the shell would mount it.

    Args:
        scenario (str): Named UpdateApp state (see scenarios/update.py).
        step_index (int): Zero-based step index the screen reports on
            StepCompleted.

    Returns:
        tuple: (ConfirmUpgradesScreen, UpdateApp).
    """
    mas_app = update_scenario(scenario)
    step = WorkflowStep(id="confirm-upgrades", heading="Confirm Upgrade Requirements")
    return ConfirmUpgradesScreen(mas_app, step, step_index), mas_app


def _error_text(app) -> str:
    """Return the inline validation error text shown by the screen.

    Must be called while the pilot app is still running (inside drive) —
    the widget tree is torn down once the app shuts down.
    """
    return str(app.query_one("#validator-error-confirm-upgrades", Label).render())


def test_license_path_confirms_db2_upgrade(tmp_path):
    """Test that the license path alone confirms a Db2 v11 to v12 upgrade.

    GIVEN a real UpdateApp in the db2-v11-to-v12 scenario and a license
        file on disk
    WHEN the user enters the license path and clicks Confirm & Continue
    THEN the screen posts StepCompleted, writes db2_v12_upgrade=true and the
        license path, and the launch-time consumption of that path
        (db2LicenseFile) produces the pipeline param and secret.
    """
    license_file = tmp_path / "db2-v12-license.lic"
    license_file.write_text("test license content")

    screen, mas_app = _make_screen("db2-v11-to-v12")

    async def drive(pilot, app):
        app.query_one("#input-db2-license", Input).value = str(license_file)
        await pilot.pause()
        await click_button(pilot, "#btn-confirm-upgrades")
        await pilot.pause()

    app = run_screen_pilot(screen, drive)

    assert ("step_completed", 3) in app.posted
    assert mas_app.getParam("db2_v12_upgrade") == "true"
    assert mas_app.db2LicenseFileLocal == str(license_file)
    # Downstream: what launchUpdate consumes via db2LicenseFile()
    mas_app.db2LicenseFile()
    assert mas_app.getParam("db2_license_file") == f"/workspace/db2/{license_file.name}"
    assert license_file.name in (mas_app.db2LicenseFileSecret or {}).get("data", {})


def test_confirm_blocked_without_license_path():
    """Test that Confirm is blocked when the license path is empty.

    GIVEN a real UpdateApp in the db2-v11-to-v12 scenario
    WHEN the user clicks Confirm & Continue without entering a path
    THEN an inline error is shown and nothing is posted or written.
    """
    screen, mas_app = _make_screen("db2-v11-to-v12")

    async def drive(pilot, app):
        await click_button(pilot, "#btn-confirm-upgrades")
        await pilot.pause()
        assert app.posted == []
        assert "license file is required" in _error_text(app)

    run_screen_pilot(screen, drive)

    assert mas_app.db2LicenseFileLocal is None


def test_confirm_blocked_when_license_file_does_not_exist(tmp_path):
    """Test that Confirm is blocked when the license path points to no file.

    GIVEN a real UpdateApp in the db2-v11-to-v12 scenario
    WHEN the user enters a path to a file that does not exist and clicks
        Confirm & Continue
    THEN an inline error names the missing path and nothing is posted —
        the failure must surface at confirmation time, not at pipeline
        launch.
    """
    missing = tmp_path / "does-not-exist.lic"

    screen, mas_app = _make_screen("db2-v11-to-v12")

    async def drive(pilot, app):
        app.query_one("#input-db2-license", Input).value = str(missing)
        await pilot.pause()
        await click_button(pilot, "#btn-confirm-upgrades")
        await pilot.pause()
        assert app.posted == []
        assert str(missing) in _error_text(app)

    run_screen_pilot(screen, drive)

    assert mas_app.db2LicenseFileLocal is None


def test_license_path_user_directory_expanded(tmp_path, monkeypatch):
    """Test that a ~ license path is expanded before being stored.

    GIVEN a real UpdateApp in the db2-v11-to-v12 scenario and a license
        file in the user's home directory
    WHEN the user enters the path as ~/name.lic
    THEN the stored path is the absolute home-directory path, so the
        pipeline launch can open it.
    """
    license_file = tmp_path / "db2.lic"
    license_file.write_text("license")
    monkeypatch.setenv("HOME", str(tmp_path))

    screen, mas_app = _make_screen("db2-v11-to-v12")

    async def drive(pilot, app):
        app.query_one("#input-db2-license", Input).value = "~/db2.lic"
        await pilot.pause()
        await click_button(pilot, "#btn-confirm-upgrades")
        await pilot.pause()

    app = run_screen_pilot(screen, drive)

    assert ("step_completed", 3) in app.posted
    assert mas_app.db2LicenseFileLocal == str(license_file)


def test_license_input_rendered_when_only_license_pending():
    """Test that the license input renders when only the license is pending.

    GIVEN a real UpdateApp in the db2-license-only scenario (Db2 upgrade
        already confirmed via param)
    WHEN the screen mounts
    THEN the IBM Db2 section shows the license path input (no checkbox)
        and confirming with a valid path posts StepCompleted.
    """
    import tempfile
    import os

    handle = tempfile.NamedTemporaryFile(suffix=".lic", delete=False, mode="w")
    handle.write("license")
    handle.close()
    try:
        screen, mas_app = _make_screen("db2-license-only")

        async def drive(pilot, app):
            await wait_for(lambda: bool(app.query("#input-db2-license")))
            assert not app.query("#confirm-db2"), "no Db2 checkbox expected when the license is the confirmation"
            app.query_one("#input-db2-license", Input).value = handle.name
            await pilot.pause()
            await click_button(pilot, "#btn-confirm-upgrades")
            await pilot.pause()

        app = run_screen_pilot(screen, drive)

        assert ("step_completed", 3) in app.posted
        assert mas_app.db2LicenseFileLocal == handle.name
    finally:
        os.unlink(handle.name)


def test_db2_checkbox_required_when_no_license_needed():
    """Test that a Db2 checkbox is required for upgrades without a license file.

    GIVEN a real UpdateApp in the db2-major-no-license scenario
    WHEN the user clicks Confirm & Continue without checking the Db2 checkbox
    THEN an inline error is shown; after checking it, Confirm posts
        StepCompleted.
    """
    screen, mas_app = _make_screen("db2-major-no-license")

    async def drive(pilot, app):
        await click_button(pilot, "#btn-confirm-upgrades")
        await pilot.pause()
        assert app.posted == []
        assert "confirmations must be checked" in _error_text(app)

        app.query_one("#confirm-db2", Checkbox).value = True
        await pilot.pause()
        await click_button(pilot, "#btn-confirm-upgrades")
        await pilot.pause()

    app = run_screen_pilot(screen, drive)

    assert ("step_completed", 3) in app.posted
    assert mas_app.getParam("db2_v13_upgrade") == "true"


def test_mongo_checkbox_required():
    """Test that the MongoDB confirmation checkbox gates Confirm.

    GIVEN a real UpdateApp in the mongo-major scenario
    WHEN the user clicks Confirm without checking the MongoDB checkbox and
        then checks it and confirms
    THEN the first click is blocked with an inline error and the second
        posts StepCompleted with mongodb_v8_upgrade=true.
    """
    screen, mas_app = _make_screen("mongo-major")

    async def drive(pilot, app):
        await click_button(pilot, "#btn-confirm-upgrades")
        await pilot.pause()
        assert app.posted == []
        assert "confirmations must be checked" in _error_text(app)

        app.query_one("#confirm-mongodb", Checkbox).value = True
        await pilot.pause()
        await click_button(pilot, "#btn-confirm-upgrades")
        await pilot.pause()

    app = run_screen_pilot(screen, drive)

    assert ("step_completed", 3) in app.posted
    assert mas_app.getParam("mongodb_v8_upgrade") == "true"


def test_mongo_and_db2_license_combined(tmp_path):
    """Test combined MongoDB and Db2 license confirmations.

    GIVEN a real UpdateApp in the mongo-and-db2-v12 scenario
    WHEN the user checks the MongoDB checkbox, enters the license path, and
        confirms
    THEN both confirmation params and the license path are written.
    """
    license_file = tmp_path / "db2.lic"
    license_file.write_text("license")

    screen, mas_app = _make_screen("mongo-and-db2-v12")

    async def drive(pilot, app):
        app.query_one("#confirm-mongodb", Checkbox).value = True
        app.query_one("#input-db2-license", Input).value = str(license_file)
        await pilot.pause()
        await click_button(pilot, "#btn-confirm-upgrades")
        await pilot.pause()

    app = run_screen_pilot(screen, drive)

    assert ("step_completed", 3) in app.posted
    assert mas_app.getParam("mongodb_v8_upgrade") == "true"
    assert mas_app.getParam("db2_v12_upgrade") == "true"
    assert mas_app.db2LicenseFileLocal == str(license_file)


def test_abort_button_exits_app():
    """Test that the Abort button exits the application with a non-zero code.

    GIVEN a mounted ConfirmUpgradesScreen
    WHEN the user clicks Abort Update
    THEN the app exits with return code 1 and nothing is posted.
    """
    screen, _ = _make_screen("db2-v11-to-v12")

    async def drive(pilot, app):
        await click_button(pilot, "#btn-abort-upgrades")
        await pilot.pause()

    app = run_screen_pilot(screen, drive)

    assert app.posted == []
    assert app.return_value == 1


def test_workflow_reset_clears_license_state(tmp_path):
    """Test that a workflow reset clears the collected license path.

    GIVEN a real TextualShell over a real UpdateApp in the db2-v11-to-v12
        scenario, with confirm-upgrades as the first step and review second
    WHEN the user confirms with a license path, then resets from the
        review step
    THEN the license path (and params) are cleared so the workflow
        re-collects them — a stale path must not silently survive a reset,
        because db2LicenseFileNeeded() only checks for None and would skip
        the license input on the second pass.
    """
    from mas.cli.tui.screens.review import ReviewScreen
    from mas.cli.tui.shell import TextualShell

    license_file = tmp_path / "db2.lic"
    license_file.write_text("license")

    mas_app = update_scenario("db2-v11-to-v12")
    confirm_step = WorkflowStep(
        id="confirm-upgrades",
        heading="Confirm Upgrade Requirements",
        screen_class=ConfirmUpgradesScreen,
    )
    review_step = WorkflowStep(id="review", heading="Review Settings", screen_class=ReviewScreen)
    shell = TextualShell(mas_app, [confirm_step, review_step])

    async def run():
        async with shell.run_test(size=(100, 40)) as pilot:
            await pilot.pause()
            shell.query_one("#input-db2-license", Input).value = str(license_file)
            await pilot.pause()
            await click_button(pilot, "#btn-confirm-upgrades")
            # The review panel mounts lazily once the confirm step completes
            assert await wait_for_widget(pilot, "#btn-reset")
            # Now on the review step; the license has been collected
            assert mas_app.db2LicenseFileLocal == str(license_file)
            assert mas_app.getParam("db2_v12_upgrade") == "true"

            await click_button(pilot, "#btn-reset")
            await pilot.pause()
            # Back at the confirm step: everything re-collectable
            assert mas_app.db2LicenseFileLocal is None
            assert mas_app.db2LicenseFileSecret is None
            assert mas_app.getParam("db2_v12_upgrade") == ""
            assert mas_app.upgradeConfirmationsPending() is True
            assert shell.query_one("#input-db2-license", Input).value == ""

    asyncio.run(run())
