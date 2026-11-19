# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
# *****************************************************************************

"""Pilot tests for the upgrade command's license-acceptance step screen.

Mounts the real license-acceptance WorkflowStep (from buildUpgradeWorkflow)
in a LicenseAcceptanceScreen against a scenario app whose target channel
(9.2.x) carries a license, verifying that the license links are shown, that
Confirm is blocked with an inline error until the acceptance checkbox is
checked, and that Confirm records the acceptance on the app and advances
the step.
"""

import pytest
from textual.widgets import Checkbox, Label

from mas.cli.upgrade.workflow import buildUpgradeWorkflow
from pilot.harness import click_button, run_screen_pilot, wait_for
from scenarios.upgrade import upgrade_scenario

pytestmark = pytest.mark.pilot


def _make_screen(scenario="upgrade-9-1-to-9-2"):
    """Return (screen, mas_app) for the license-acceptance step.

    Args:
        scenario (str): Scenario name for the app state (nextChannel is
            resolved by prepareUpgrade; 9.2.x carries a license).

    Returns:
        tuple: (LicenseAcceptanceScreen for the license-acceptance step,
            the scenario app).
    """
    mas_app = upgrade_scenario(scenario)
    definition = buildUpgradeWorkflow(mas_app)
    step = next(s for s in definition if s.id == "license-acceptance")
    screen = step.screen_class(mas_app, step, 2)
    return screen, mas_app


def test_license_screen_shows_target_channel_terms():
    """Test that the license screen shows the target release's license links.

    GIVEN a scenario app whose target channel is 9.2.x (which carries
        license links)
    WHEN the license-acceptance step screen is shown
    THEN the terms section names the target channel and renders the license
        URLs as plain text (the prompt_toolkit <u> tags stripped), with the
        acceptance checkbox unchecked.
    """
    screen, _ = _make_screen()

    result = {}

    async def drive(pilot, app):
        result["text"] = " ".join(str(widget.render()) for widget in app.query("#license-terms-section Label"))
        result["checkbox"] = app.query_one("#accept-license", Checkbox).value
        result["label"] = str(app.query_one("#accept-license", Checkbox).label)

    run_screen_pilot(screen, drive)

    assert "9.2.x" in result["text"]
    assert "https://ibm.biz/MAS92-License" in result["text"]
    assert "<u>" not in result["text"]
    assert result["checkbox"] is False
    assert "9.2.x" in result["label"]


def test_confirm_blocked_until_checkbox_checked():
    """Test that Confirm is blocked with an inline error while unchecked.

    GIVEN a scenario app with a pending license
    WHEN Confirm & Continue is clicked without checking the acceptance box
    THEN the error appears in the reserved status row, no StepCompleted is
        posted, and the app's licenseAccepted stays False.
    """
    screen, mas_app = _make_screen()

    result = {}

    async def drive(pilot, app):
        await click_button(pilot, "#btn-confirm-license")
        await wait_for(lambda: "must accept" in str(app.query_one("#validator-error-license-acceptance", Label).render()))
        result["posted"] = list(app.posted)

    run_screen_pilot(screen, drive)

    assert result["posted"] == []
    assert mas_app.licenseAccepted is False


def test_confirm_with_checkbox_advances_and_records_acceptance():
    """Test that checking the box and confirming records acceptance and advances.

    GIVEN a scenario app with a pending license
    WHEN the acceptance checkbox is checked and Confirm & Continue clicked
    THEN licenseAccepted is set on the app (as --accept-license would) and
        the step completes, advancing to the review step.
    """
    screen, mas_app = _make_screen()

    async def drive(pilot, app):
        app.query_one("#accept-license", Checkbox).value = True
        await pilot.pause()
        await click_button(pilot, "#btn-confirm-license")
        await wait_for(lambda: app.posted == [("step_completed", 2)])

    run_screen_pilot(screen, drive)

    assert mas_app.licenseAccepted is True
