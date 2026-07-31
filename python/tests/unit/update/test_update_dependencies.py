# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for mas.cli.update.dependencies — DependencyDetectionMixin.

All tests follow the GIVEN-WHEN-THEN convention and verify that:
- DependencyDetectionMixin and CheckItem are importable from their own module
- UpdateApp inherits DependencyDetectionMixin
- _DEPENDENCY_CHECKS is present and structurally valid
- All detect methods are accessible on UpdateApp
"""

from mas.cli.update.dependencies import DependencyDetectionMixin, CheckItem
from mas.cli.update.app import UpdateApp


def test_dependency_detection_mixin_is_importable():
    """Test that DependencyDetectionMixin can be imported from mas.cli.update.dependencies.

    GIVEN the refactored package structure
    WHEN DependencyDetectionMixin is imported from mas.cli.update.dependencies
    THEN the import succeeds without error.
    """
    assert DependencyDetectionMixin is not None


def test_check_item_is_importable():
    """Test that CheckItem can be imported from mas.cli.update.dependencies.

    GIVEN the refactored package structure
    WHEN CheckItem is imported from mas.cli.update.dependencies
    THEN the import succeeds and it is a dataclass-like class with the expected fields.
    """
    assert CheckItem is not None
    item = CheckItem(label="test", method="doSomething", param="some_param")
    assert item.label == "test"
    assert item.method == "doSomething"
    assert item.param == "some_param"
    assert item.fatal_if_present is False
    assert item.absent_message == "No action required"


def test_update_app_inherits_dependency_detection_mixin():
    """Test that UpdateApp includes DependencyDetectionMixin in its MRO.

    GIVEN the refactored UpdateApp class
    WHEN its MRO is inspected
    THEN DependencyDetectionMixin appears in the inheritance chain.
    """
    assert DependencyDetectionMixin in UpdateApp.__mro__


def test_dependency_checks_class_variable_on_mixin():
    """Test that _DEPENDENCY_CHECKS is defined on DependencyDetectionMixin.

    GIVEN DependencyDetectionMixin
    WHEN _DEPENDENCY_CHECKS is accessed
    THEN it is a non-empty list of CheckItem instances.
    """
    checks = DependencyDetectionMixin._DEPENDENCY_CHECKS
    assert isinstance(checks, list)
    assert len(checks) > 0
    for item in checks:
        assert isinstance(item, CheckItem)
        assert item.label
        assert item.method


def test_dependency_checks_contains_expected_entries():
    """Test that _DEPENDENCY_CHECKS has all nine expected entries.

    GIVEN DependencyDetectionMixin._DEPENDENCY_CHECKS
    WHEN the method names are extracted
    THEN all nine detector methods are represented.
    """
    methods = {item.method for item in DependencyDetectionMixin._DEPENDENCY_CHECKS}
    expectedMethods = {
        "isWatsonDiscoveryInstalled",
        "isWatsonOpenscaleInstalled",
        "isIBMCertManagerInstalled",
        "detectGrafana4",
        "detectODH",
        "detectMongoDb",
        "detectDb2u",
        "detectKafka",
        "detectCP4D",
    }
    assert methods == expectedMethods


def test_fatal_checks_are_first():
    """Test that all fatal_if_present checks precede non-fatal checks in _DEPENDENCY_CHECKS.

    GIVEN DependencyDetectionMixin._DEPENDENCY_CHECKS
    WHEN the list is scanned
    THEN no non-fatal check appears before the last fatal check.
    """
    checks = DependencyDetectionMixin._DEPENDENCY_CHECKS
    seenNonFatal = False
    for item in checks:
        if not item.fatal_if_present:
            seenNonFatal = True
        elif seenNonFatal:
            raise AssertionError(f"Fatal check '{item.label}' appears after a non-fatal check")


def test_detect_methods_present_on_update_app():
    """Test that all detect methods are accessible on UpdateApp.

    GIVEN the refactored UpdateApp class
    WHEN each detect method name is looked up on the class
    THEN each method is present (inherited from DependencyDetectionMixin).
    """
    expectedMethods = [
        "isWatsonDiscoveryInstalled",
        "isWatsonOpenscaleInstalled",
        "isIBMCertManagerInstalled",
        "detectGrafana4",
        "detectODH",
        "detectMongoDb",
        "detectCP4D",
        "detectCpdService",
        "detectDb2u",
        "detectKafka",
        "runDependencyChecks",
        "reviewDependencyUpgrades",
        "showMongoDependencyUpdateNotice",
        "_runWithHalo",
    ]
    for methodName in expectedMethods:
        assert hasattr(UpdateApp, methodName), f"UpdateApp is missing method: {methodName}"


def test_run_dependency_checks_start_callback_called_before_progress():
    """Test that runDependencyChecks calls startCallback before progressCallback for each check.

    GIVEN a mock UpdateApp with all detect methods returning DetectResult(ok=True)
    WHEN runDependencyChecks(progressCallback=cb, startCallback=start_cb) is called
    THEN startCallback(label) is called before progressCallback(label, ...) for each check.
    """
    from unittest.mock import patch, MagicMock
    from mas.cli.update.dependencies import DetectResult

    app = UpdateApp.__new__(UpdateApp)
    app._dynClient = MagicMock()
    app.params = {}
    app.chosenCatalog = MagicMock()
    app.applyPreInstallMASRBAC = False
    app.instancesNeedingRBAC = []

    fake_result = DetectResult(ok=True, message="ok")
    events = []

    def start_cb(label):
        events.append(("start", label))

    def prog_cb(label, ok, detail):
        events.append(("done", label))

    # Patch all detector methods to return fake_result and RBAC evaluator to no-op
    with (
        patch.object(type(app), "isWatsonDiscoveryInstalled", return_value=fake_result),
        patch.object(type(app), "isWatsonOpenscaleInstalled", return_value=fake_result),
        patch.object(type(app), "isIBMCertManagerInstalled", return_value=fake_result),
        patch.object(type(app), "detectGrafana4", return_value=fake_result),
        patch.object(type(app), "detectODH", return_value=fake_result),
        patch.object(type(app), "detectMongoDb", return_value=fake_result),
        patch.object(type(app), "detectDb2u", return_value=fake_result),
        patch.object(type(app), "detectKafka", return_value=fake_result),
        patch.object(type(app), "detectCP4D", return_value=fake_result),
        patch.object(type(app), "evaluatePreinstallRBACAccessForUpdate", return_value=None),
    ):
        app.runDependencyChecks(progressCallback=prog_cb, startCallback=start_cb)

    # Interleaved events: for each label "start" must appear before "done"
    assert len(events) > 0, "Expected at least one event"
    labels_seen = {}
    for kind, label in events:
        if kind == "start":
            labels_seen[label] = "started"
        elif kind == "done":
            assert labels_seen.get(label) == "started", f"'done' for '{label}' arrived before 'start'"
            labels_seen[label] = "done"
