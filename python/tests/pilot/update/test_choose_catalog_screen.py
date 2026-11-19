# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Pilot tests for the update command's choose-catalog step screen.

Mounts the real choose-catalog WorkflowStep (from buildUpdateWorkflow) in a
StepScreen against a scenario app, verifying that the currently installed
catalog detected by the connect step's post-connect checks is shown as
context alongside the target catalog options.
"""

import pytest
from textual.widgets import Label, Select

from mas.cli.tui.screens.step import StepScreen
from mas.cli.update.workflow import buildUpdateWorkflow
from pilot.harness import run_screen_pilot
from scenarios.update import update_scenario

pytestmark = pytest.mark.pilot


def _make_screen(scenario):
    """Return (screen, mas_app) for the choose-catalog step.

    Args:
        scenario (str): Scenario name for the app state (installedCatalogId
            is set by the connect step's post-connect checks).

    Returns:
        tuple: (StepScreen for the choose-catalog step, the scenario app).
    """
    mas_app = update_scenario(scenario)
    definition = buildUpdateWorkflow(mas_app)
    step = next(s for s in definition if s.id == "choose-catalog")
    return StepScreen(mas_app, step, 1), mas_app


def test_choose_catalog_shows_installed_catalog_as_context():
    """Test that the choose-catalog step shows the installed catalog.

    GIVEN an app whose post-connect checks detected the installed catalog
    WHEN the choose-catalog step screen is shown
    THEN a context panel shows "Installed Catalog" with the detected ID,
        alongside the target catalog select field.
    """
    screen, _ = _make_screen("installed-catalog")

    result = {}

    async def drive(pilot, app):
        result["rows"] = len(app.query(".step-context .context-row"))
        result["label"] = str(app.query_one(".context-label", Label).render())
        result["value"] = str(app.query_one(".context-value", Label).render())
        result["select"] = app.query_one("#field-mas_catalog_version", Select) is not None

    run_screen_pilot(screen, drive)

    assert result["rows"] == 1
    assert result["label"] == "Installed Catalog:"
    assert result["value"] == "v9-261022-amd64"
    assert result["select"]


def test_choose_catalog_unknown_catalog_shows_placeholder():
    """Test that an undetectable installed catalog shows a placeholder.

    GIVEN an app whose installed catalog could not be identified
        (installedCatalogId is None)
    WHEN the choose-catalog step screen is shown
    THEN the context panel shows "—" rather than raising, matching how the
        review screen renders missing values.
    """
    screen, _ = _make_screen("clean")

    result = {}

    async def drive(pilot, app):
        result["value"] = str(app.query_one(".context-value", Label).render())

    run_screen_pilot(screen, drive)

    assert result["value"] == "—"
