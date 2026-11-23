# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Pilot tests for the generic StepScreen context panel (tui/screens/step.py).

Covers the read-only context rows rendered from ``step.context`` between the
description and the fields: attr-backed and param-backed values, sensitive
masking, the missing-value fallback, and the panel being absent when a step
defines no context items.
"""

import pytest
from textual.widgets import Label

from mas.cli.tui.models import WorkflowField, WorkflowStep, WorkflowSummaryItem
from mas.cli.tui.screens.step import StepScreen
from pilot.harness import run_screen_pilot

pytestmark = pytest.mark.pilot


class _StubApp:
    """Minimal app stand-in with a params dict and settable attributes."""

    def __init__(self, params=None, attrs=None):
        """Initialise the stub with params and instance attributes.

        Args:
            params (dict, optional): Contents of the app params dict.
            attrs (dict, optional): Instance attributes to set (context rows
                resolved via ``attr`` read these).
        """
        self.params = params if params is not None else {}
        for key, value in (attrs or {}).items():
            setattr(self, key, value)


def _make_step(context):
    """Return a step with one string field and the given context items.

    Args:
        context (list): WorkflowSummaryItem list for the step's context panel.

    Returns:
        WorkflowStep: Step definition for the screen under test.
    """
    return WorkflowStep(
        id="ctx-step",
        heading="Test Step",
        fields=[WorkflowField(id="target", label="Target", type="string")],
        context=context,
    )


def test_context_attr_row_renders_value():
    """Test that an attr-backed context row shows the attribute value.

    GIVEN a step with a context item resolved via attr, and an app holding
        that attribute
    WHEN the StepScreen is shown
    THEN the context panel has one row showing the label and the value.
    """
    step = _make_step([WorkflowSummaryItem(label="Installed Catalog", attr="installedCatalogId")])
    screen = StepScreen(_StubApp(attrs={"installedCatalogId": "v9-261022-amd64"}), step, 1)

    result = {}

    async def drive(pilot, app):
        result["rows"] = len(app.query(".step-context .context-row"))
        result["label"] = str(app.query_one(".context-label", Label).render())
        result["value"] = str(app.query_one(".context-value", Label).render())

    run_screen_pilot(screen, drive)

    assert result["rows"] == 1
    assert result["label"] == "Installed Catalog:"
    assert result["value"] == "v9-261022-amd64"


def test_context_param_row_renders_value():
    """Test that a param-backed context row shows the param value.

    GIVEN a step with a context item resolved via param, and an app whose
        params dict holds that key
    WHEN the StepScreen is shown
    THEN the context row shows the param value.
    """
    step = _make_step([WorkflowSummaryItem(label="Target Catalog", param="mas_catalog_version")])
    screen = StepScreen(_StubApp(params={"mas_catalog_version": "v9-261105-amd64"}), step, 1)

    result = {}

    async def drive(pilot, app):
        result["value"] = str(app.query_one(".context-value", Label).render())

    run_screen_pilot(screen, drive)

    assert result["value"] == "v9-261105-amd64"


def test_context_missing_value_renders_placeholder():
    """Test that a missing context value falls back to an em dash.

    GIVEN a step with an attr-backed context item the app does not define
    WHEN the StepScreen is shown
    THEN the context row shows "—" rather than raising or showing blank.
    """
    step = _make_step([WorkflowSummaryItem(label="Installed Catalog", attr="installedCatalogId")])
    screen = StepScreen(_StubApp(attrs={"installedCatalogId": None}), step, 1)

    result = {}

    async def drive(pilot, app):
        result["value"] = str(app.query_one(".context-value", Label).render())

    run_screen_pilot(screen, drive)

    assert result["value"] == "—"


def test_context_sensitive_item_is_masked():
    """Test that a sensitive context item is masked.

    GIVEN a step with a sensitive context item backed by a param
    WHEN the StepScreen is shown
    THEN the context row shows "***" instead of the value.
    """
    step = _make_step([WorkflowSummaryItem(label="Token", param="login_token", sensitive=True)])
    screen = StepScreen(_StubApp(params={"login_token": "sha256~secret"}), step, 1)

    result = {}

    async def drive(pilot, app):
        result["value"] = str(app.query_one(".context-value", Label).render())

    run_screen_pilot(screen, drive)

    assert result["value"] == "***"


def test_no_context_items_renders_no_panel():
    """Test that a step without context items renders no context panel.

    GIVEN a step whose context list is empty
    WHEN the StepScreen is shown
    THEN no .step-context widget exists and the fields still render.
    """
    step = _make_step([])
    screen = StepScreen(_StubApp(), step, 1)

    result = {}

    async def drive(pilot, app):
        result["panels"] = len(app.query(".step-context"))
        result["fields"] = app.query_one("#field-target") is not None

    run_screen_pilot(screen, drive)

    assert result["panels"] == 0
    assert result["fields"]
