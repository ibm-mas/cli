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
defines no context items.  Also covers the dynamic_select machinery
(``options_loader`` fields populated in a worker thread when the step becomes
active, the field's possibly-callable default pre-selected once the options
arrive, the context rows refreshed after the load, a failing loader surfacing
its error inline) and the validator busy feedback (spinner + status message
while the blocking validator runs, mirroring the connect screen).
"""

import threading

import pytest
from textual.widgets import Button, Label, LoadingIndicator, Select

from mas.cli.tui.models import WorkflowField, WorkflowStep, WorkflowSummaryItem
from mas.cli.tui.screens.step import StepScreen
from pilot.harness import click_button, run_screen_pilot, wait_for

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


# ---------------------------------------------------------------------------
# dynamic_select fields (options_loader)
# ---------------------------------------------------------------------------


def _make_dynamic_step(loader, default=None, context=None, required=False):
    """Return a step with one dynamic_select field driven by a loader.

    Args:
        loader (Callable): options_loader for the field (receives params).
        default: Field default (plain value or zero-argument callable).
        context (list, optional): WorkflowSummaryItem list for the context
            panel.
        required (bool): Whether the field is required.

    Returns:
        WorkflowStep: Step definition for the screen under test.
    """
    return WorkflowStep(
        id="dyn-step",
        heading="Test Step",
        fields=[
            WorkflowField(
                id="storage_class",
                label="Storage Class",
                type="dynamic_select",
                required=required,
                options_loader=loader,
                default=default,
            ),
        ],
        context=context if context is not None else [],
    )


def test_dynamic_select_options_load_and_default_pre_selects():
    """Test that options_loader populates the Select and applies the default.

    GIVEN a step with a dynamic_select field whose options_loader returns
        two cluster storage class names, and a plain default present in them
    WHEN the step becomes active (start_dynamic_loaders runs the loader in
        a worker thread)
    THEN the options are applied to the Select, the default is
        pre-selected, the Next button is re-enabled, and the status row is
        cleared.
    """
    step = _make_dynamic_step(lambda params: ["sc-a", "sc-b"], default="sc-b")
    screen = StepScreen(_StubApp(), step, 1)

    result = {}

    async def drive(pilot, app):
        select = app.query_one("#field-storage_class", Select)
        await wait_for(lambda: select.value == "sc-b")
        result["value"] = select.value
        result["next_disabled"] = app.query_one("#btn-next-dyn-step", Button).disabled
        result["status"] = str(app.query_one("#validator-error-dyn-step", Label).render())

    run_screen_pilot(screen, drive)

    assert result["value"] == "sc-b"
    assert result["next_disabled"] is False
    assert result["status"].strip() == ""


def test_dynamic_select_callable_default_and_context_refresh():
    """Test that a callable default reads loader state and context refreshes.

    GIVEN a step whose options_loader caches the detected state on the app
        (as the storage class lookup does), a callable default reading that
        state, and an attr-backed context row for it
    WHEN the dynamic load completes
    THEN the Select is pre-selected with the detected value and the context
        row — "—" at compose time — is refreshed to show the detected value.
    """
    stub = _StubApp(attrs={"detectedStorageClasses": None, "detectedProviderName": None})

    def _loader(params):
        # Mirrors StorageClassMixin.lookupStorageClasses: cache the
        # detection on the app while loading the options
        stub.detectedProviderName = "OpenShift Container Storage"
        return ["sc-a", "sc-b"]

    step = _make_dynamic_step(
        _loader,
        default=lambda: "sc-a",
        context=[WorkflowSummaryItem(label="Detected storage provider", attr="detectedProviderName")],
    )
    screen = StepScreen(stub, step, 1)

    result = {}

    async def drive(pilot, app):
        select = app.query_one("#field-storage_class", Select)
        await wait_for(lambda: select.value == "sc-a")
        await wait_for(lambda: "OpenShift Container Storage" in str(app.query_one(".context-value", Label).render()))
        result["value"] = select.value
        result["context"] = str(app.query_one(".context-value", Label).render())

    run_screen_pilot(screen, drive)

    assert result["value"] == "sc-a"
    assert result["context"] == "OpenShift Container Storage"


def test_dynamic_select_loader_failure_shows_inline_error():
    """Test that a failing options_loader surfaces its error inline.

    GIVEN a step whose options_loader raises (e.g. the cluster lookup
        failed)
    WHEN the dynamic load fails
    THEN the error appears in the reserved status row (not a crash) and
        the Next button is re-enabled so the user can retry or abort.
    """

    def _loader(params):
        raise RuntimeError("Storage class lookup failed")

    step = _make_dynamic_step(_loader)
    screen = StepScreen(_StubApp(), step, 1)

    result = {}

    async def drive(pilot, app):
        await wait_for(lambda: "lookup failed" in str(app.query_one("#validator-error-dyn-step", Label).render()))
        result["next_disabled"] = app.query_one("#btn-next-dyn-step", Button).disabled

    run_screen_pilot(screen, drive)

    assert result["next_disabled"] is False


def test_dynamic_select_blank_writes_empty_param():
    """Test that a blank optional dynamic_select writes an empty param.

    GIVEN a step with an optional dynamic_select field left blank (the
        "auto-detect" convention)
    WHEN Next is clicked after the options have loaded
    THEN the field writes "" to the app params (rather than keeping any
        previously-written value) and the step completes.
    """
    step = _make_dynamic_step(lambda params: ["sc-a", "sc-b"])
    stub = _StubApp(params={"storage_class": "stale-value"})
    screen = StepScreen(stub, step, 1)

    async def drive(pilot, app):
        # Next re-enabling is the deterministic "load settled" signal
        await wait_for(lambda: not app.query_one("#btn-next-dyn-step", Button).disabled)
        await click_button(pilot, "#btn-next-dyn-step")
        await wait_for(lambda: app.posted == [("step_completed", 1)])

    run_screen_pilot(screen, drive)

    assert stub.params["storage_class"] == ""


# ---------------------------------------------------------------------------
# Validator busy feedback
# ---------------------------------------------------------------------------


def test_validator_shows_busy_spinner_and_status():
    """Test that a running validator shows the busy spinner and message.

    GIVEN a step whose validator blocks on an event (like the upgrade
        command's cluster-calling prepareUpgrade) with a validator_status
        message
    WHEN Next is clicked and the validator is running
    THEN the action bar shows the busy spinner and the step's status
        message (so the disabled Next button does not look like a hang),
        and both clear when the validator completes.
    """
    release = threading.Event()

    def _blocking_validator():
        release.wait(timeout=5)

    step = WorkflowStep(
        id="val-step",
        heading="Test Step",
        fields=[],
        validator=_blocking_validator,
        validator_status="Preparing upgrade…",
    )
    screen = StepScreen(_StubApp(), step, 1)

    result = {}

    async def drive(pilot, app):
        await click_button(pilot, "#btn-next-val-step")
        spinner = app.query_one("#action-busy-spinner", LoadingIndicator)
        await wait_for(lambda: spinner.display)
        result["status_during"] = str(app.query_one("#validator-error-val-step", Label).render())
        result["next_disabled_during"] = app.query_one("#btn-next-val-step", Button).disabled
        release.set()
        await wait_for(lambda: app.posted == [("step_completed", 1)])
        result["spinner_after"] = spinner.display

    run_screen_pilot(screen, drive)

    assert "Preparing upgrade" in result["status_during"]
    assert result["next_disabled_during"] is True
    assert result["spinner_after"] is False


def test_validator_default_status_and_error_path():
    """Test the generic status message and the error path hiding the spinner.

    GIVEN a step whose validator raises, with no validator_status set
    WHEN Next is clicked
    THEN the generic "Validating…" message is shown while the validator
        runs, and on failure the spinner is hidden, the error replaces the
        status text, and Next is re-enabled.
    """

    def _failing_validator():
        raise RuntimeError("Compatibility check failed")

    step = WorkflowStep(
        id="fail-step",
        heading="Test Step",
        fields=[],
        validator=_failing_validator,
    )
    screen = StepScreen(_StubApp(), step, 1)

    result = {}

    async def drive(pilot, app):
        await click_button(pilot, "#btn-next-fail-step")
        spinner = app.query_one("#action-busy-spinner", LoadingIndicator)
        await wait_for(lambda: "Compatibility check failed" in str(app.query_one("#validator-error-fail-step", Label).render()))
        result["spinner_after"] = spinner.display
        result["next_disabled"] = app.query_one("#btn-next-fail-step", Button).disabled
        result["posted"] = list(app.posted)

    run_screen_pilot(screen, drive)

    assert result["spinner_after"] is False
    assert result["next_disabled"] is False
    assert result["posted"] == []
