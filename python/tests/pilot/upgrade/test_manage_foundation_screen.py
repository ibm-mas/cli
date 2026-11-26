# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Pilot tests for the upgrade command's manage-foundation step screen.

Mounts the real manage-foundation WorkflowStep (built by the shared
``storageClassStep`` from buildUpgradeWorkflow) in a StepScreen against a
scenario app whose upgrade needs to install Manage Foundation, with the
cluster storage class lookup patched at the shared mixin module.  Verifies
that the storage class fields render as dropdowns populated from the
cluster (with the detected provider's classes pre-selected and the
provider shown in the context row, and no entitlement key input — the key
is read from the cluster by the validator), that blank selections do not
block advancement (blank = auto-detect), and that a failing
prepareManageFoundation validator surfaces its error in the reserved
status row without advancing the step.
"""

from types import SimpleNamespace

import pytest
from textual.widgets import Button, Label, Select
from unittest.mock import patch

from mas.cli.tui.screens.step import StepScreen
from mas.cli.upgrade.workflow import buildUpgradeWorkflow
from pilot.harness import click_button, run_screen_pilot, wait_for
from scenarios.upgrade import upgrade_scenario

pytestmark = pytest.mark.pilot

# Fake OCS-style cluster: three storage classes, one of which is not part
# of the detected provider's pair (so option population and pre-selection
# can be asserted independently).
CLUSTER_STORAGE_CLASSES = ["ocs-storagecluster-ceph-rbd", "ocs-storagecluster-cephfs", "custom-nfs"]
DETECTED_DEFAULTS = SimpleNamespace(
    provider="ocs",
    providerName="OpenShift Container Storage",
    rwo="ocs-storagecluster-ceph-rbd",
    rwx="ocs-storagecluster-cephfs",
)


def _storageClassesPatch():
    """Return a patch pair for the shared mixin's cluster lookups.

    Returns:
        tuple: (getStorageClasses patch, getDefaultStorageClasses patch)
        targeting mas.cli.common.storageClasses, where the shared
        StorageClassMixin resolves them.
    """
    classes = [SimpleNamespace(metadata=SimpleNamespace(name=name)) for name in CLUSTER_STORAGE_CLASSES]
    return (
        patch("mas.cli.common.storageClasses.getStorageClasses", return_value=classes),
        patch("mas.cli.common.storageClasses.getDefaultStorageClasses", return_value=DETECTED_DEFAULTS),
    )


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


def test_manage_foundation_renders_storage_dropdowns_with_detected_defaults():
    """Test that the step collects the storage classes via dropdowns.

    GIVEN a scenario app whose upgrade needs Manage Foundation, on a
        cluster with a detectable storage provider
    WHEN the manage-foundation step screen becomes active
    THEN the RWO / RWX fields are Selects populated with the cluster's
        storage classes (looked up in the worker thread), the detected
        provider's classes are pre-selected, the detected provider is
        shown in the context row, and there is no entitlement key input —
        the key is read from the cluster's ibm-entitlement secret by the
        validator.
    """
    screen, _ = _make_screen()
    getScPatch, defaultsPatch = _storageClassesPatch()

    result = {}

    async def drive(pilot, app):
        rwo = app.query_one("#field-storage_class_rwo", Select)
        await wait_for(lambda: rwo.value == DETECTED_DEFAULTS.rwo)
        result["rwo_value"] = rwo.value
        result["rwx_value"] = app.query_one("#field-storage_class_rwx", Select).value
        result["options"] = sorted(str(value) for _, value in rwo._options if value is not Select.NULL)
        result["provider"] = str(app.query_one(".context-value", Label).render())
        result["entitlement_fields"] = len(app.query("#field-ibm_entitlement_key"))

    with getScPatch, defaultsPatch:
        run_screen_pilot(screen, drive)

    assert result["rwo_value"] == "ocs-storagecluster-ceph-rbd"
    assert result["rwx_value"] == "ocs-storagecluster-cephfs"
    assert result["options"] == sorted(CLUSTER_STORAGE_CLASSES)
    assert result["provider"] == "OpenShift Container Storage"
    assert result["entitlement_fields"] == 0


def test_blank_selections_do_not_block_required_validation():
    """Test that every manage-foundation field is optional at field level.

    GIVEN a scenario app whose upgrade needs Manage Foundation, with the
        detected provider's classes pre-selected
    WHEN the pre-selections are cleared and Next is clicked with both
        dropdowns blank (the storage classes are auto-detected by the
        validator, not by field validation)
    THEN the validator runs and the step completes — required-field
        validation does not block on the blank dropdowns.
    """
    screen, mas_app = _make_screen(prepareManageFoundation=lambda: None)
    getScPatch, defaultsPatch = _storageClassesPatch()

    async def drive(pilot, app):
        rwo = app.query_one("#field-storage_class_rwo", Select)
        rwx = app.query_one("#field-storage_class_rwx", Select)
        await wait_for(lambda: rwo.value == DETECTED_DEFAULTS.rwo)
        # Clear back to blank: "auto-detect at validation time"
        rwo.clear()
        rwx.clear()
        await pilot.pause()
        await click_button(pilot, "#btn-next-manage-foundation")
        await wait_for(lambda: app.posted == [("step_completed", 3)])

    with getScPatch, defaultsPatch:
        run_screen_pilot(screen, drive)

    # Blank selections are written as empty strings; the validator resolves them
    assert mas_app.params.get("storage_class_rwo") == ""
    assert mas_app.params.get("storage_class_rwx") == ""


def test_validator_failure_shown_in_status_row():
    """Test that a failing prepareManageFoundation blocks and shows inline.

    GIVEN a scenario app whose prepareManageFoundation raises (e.g. the
        entitlement key cannot be read from the cluster, or a storage class
        is not on the cluster)
    WHEN the storage classes are selected and Next is clicked
    THEN the error appears in the reserved status row and no StepCompleted
        is posted, so the user can correct the inputs and retry.
    """

    def _fail():
        raise RuntimeError("Storage class 'missing-sc' specified via --storage-class-rwo is not available on this cluster.")

    screen, mas_app = _make_screen(prepareManageFoundation=_fail)
    getScPatch, defaultsPatch = _storageClassesPatch()

    result = {}

    async def drive(pilot, app):
        rwo = app.query_one("#field-storage_class_rwo", Select)
        await wait_for(lambda: rwo.value == DETECTED_DEFAULTS.rwo)
        await click_button(pilot, "#btn-next-manage-foundation")
        await wait_for(lambda: "missing-sc" in str(app.query_one("#validator-error-manage-foundation", Label).render()))
        result["posted"] = list(app.posted)
        result["next_disabled"] = app.query_one("#btn-next-manage-foundation", Button).disabled

    with getScPatch, defaultsPatch:
        run_screen_pilot(screen, drive)

    # The selected values are still written to params even when validation
    # fails, so the user's entries survive going back and returning.
    assert mas_app.params["storage_class_rwo"] == "ocs-storagecluster-ceph-rbd"
    assert result["posted"] == []
    assert result["next_disabled"] is False


def test_successful_validation_advances_and_writes_params():
    """Test that a successful validator run writes the inputs and advances.

    GIVEN a scenario app whose prepareManageFoundation succeeds
    WHEN different storage classes are picked from the dropdowns and Next
        clicked
    THEN the field values are written to the app params (ready for the
        validator's configuration and the pipeline launch) and the step
        completes.
    """
    screen, mas_app = _make_screen(prepareManageFoundation=lambda: None)
    getScPatch, defaultsPatch = _storageClassesPatch()

    async def drive(pilot, app):
        rwo = app.query_one("#field-storage_class_rwo", Select)
        rwx = app.query_one("#field-storage_class_rwx", Select)
        await wait_for(lambda: rwo.value == DETECTED_DEFAULTS.rwo)
        # Pick different classes than the pre-selected provider defaults
        rwo.value = "custom-nfs"
        rwx.value = "ocs-storagecluster-cephfs"
        await pilot.pause()
        await click_button(pilot, "#btn-next-manage-foundation")
        await wait_for(lambda: app.posted == [("step_completed", 3)])

    with getScPatch, defaultsPatch:
        run_screen_pilot(screen, drive)

    assert mas_app.params["storage_class_rwo"] == "custom-nfs"
    assert mas_app.params["storage_class_rwx"] == "ocs-storagecluster-cephfs"
