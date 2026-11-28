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
(9.2.x) carries a license, verifying that the license links render as
ctrl+clickable hyperlinks directly under the description (no subcontainer)
and that clicking Confirm & Continue records the acceptance on the app and
advances the step — the button press is itself the acceptance, with no
separate confirmation checkbox.
"""

import pytest
from textual.widgets import Label

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
    THEN the description names the target channel (its {channel}
        placeholder filled with nextChannel) and each license URL renders
        as a bulleted ctrl+clickable hyperlink — a Rich Text whose link
        style carries the URL, with the prompt_toolkit <u> tags stripped —
        directly under the description with no subcontainer, and no
        confirmation checkbox is rendered — the Confirm & Continue button
        is the acceptance.
    """
    screen, _ = _make_screen()

    result = {}

    async def drive(pilot, app):
        result["description"] = " ".join(widget.content for widget in app.query(".description-para"))
        result["links"] = [widget.content for widget in app.query(".license-link")]
        result["sections"] = len(app.query(".confirm-section"))
        result["checkboxes"] = len(app.query("Checkbox"))

    run_screen_pilot(screen, drive)

    assert "9.2.x" in result["description"]
    assert "<u>" not in result["description"]
    assert result["sections"] == 0
    assert result["checkboxes"] == 0

    expected = [
        "https://ibm.biz/MAS92-License",
        "https://ibm.biz/MAXIT92-License",
        "https://ibm.biz/MAXESRI92-License",
    ]
    assert [text.plain for text in result["links"]] == [f"- {url}" for url in expected]
    for text, url in zip(result["links"], expected):
        # Each URL is stylized as an OSC 8 hyperlink (the same linkText
        # helper the connect screen uses for the server URL), so ctrl+click
        # opens the full URL even where the text folds.  Rich stores the
        # span style as a string ("link <url>") or a parsed Style depending
        # on version — accept either.
        assert any(
            (isinstance(span.style, str) and f"link {url}" in span.style)
            or (not isinstance(span.style, str) and span.style is not None and span.style.link == url)
            for span in text.spans
        ), f"Expected {url} to be hyperlinked, got spans: {text.spans}"


def test_confirm_advances_and_records_acceptance():
    """Test that clicking Confirm & Continue records acceptance and advances.

    GIVEN a scenario app with a pending license
    WHEN Confirm & Continue is clicked
    THEN licenseAccepted is set on the app (as --accept-license would) and
        the step completes, advancing to the review step, with no inline
        error shown.
    """
    screen, mas_app = _make_screen()

    result = {}

    async def drive(pilot, app):
        await click_button(pilot, "#btn-confirm-license")
        await wait_for(lambda: app.posted == [("step_completed", 2)])
        result["error"] = str(app.query_one("#validator-error-license-acceptance", Label).render())

    run_screen_pilot(screen, drive)

    assert mas_app.licenseAccepted is True
    assert result["error"].strip() == ""
