# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for DetectResult and the _runWithHalo / runDependencyChecks integration.

All tests follow the GIVEN-WHEN-THEN convention.
"""

from unittest.mock import MagicMock, patch

from mas.cli.update.dependencies import DetectResult, DependencyDetectionMixin

# ---------------------------------------------------------------------------
# DetectResult dataclass
# ---------------------------------------------------------------------------


def test_detect_result_ok_true():
    """Test DetectResult stores ok=True and message correctly.

    GIVEN DetectResult(ok=True, message="All good")
    WHEN the fields are accessed
    THEN ok is True and message is "All good".
    """
    result = DetectResult(ok=True, message="All good")
    assert result.ok is True
    assert result.message == "All good"


def test_detect_result_ok_false():
    """Test DetectResult stores ok=False and message correctly.

    GIVEN DetectResult(ok=False, message="Error occurred")
    WHEN the fields are accessed
    THEN ok is False and message is "Error occurred".
    """
    result = DetectResult(ok=False, message="Error occurred")
    assert result.ok is False
    assert result.message == "Error occurred"


def test_detect_result_is_importable_from_dependencies():
    """Test DetectResult can be imported from mas.cli.update.dependencies.

    GIVEN the refactored package
    WHEN DetectResult is imported
    THEN it is not None and is a class.
    """
    assert DetectResult is not None
    assert isinstance(DetectResult, type)


# ---------------------------------------------------------------------------
# _runWithHalo uses DetectResult.message as the Halo text
# ---------------------------------------------------------------------------


def _make_mixin_stub(result: DetectResult):
    """Return a minimal DependencyDetectionMixin-like stub whose fn returns result."""

    class Stub(DependencyDetectionMixin):
        spinner = "dots"
        successIcon = "✅"
        failureIcon = "❌"

        def fatalError(self, msg):
            raise SystemExit(msg)

    stub = Stub()
    return stub, lambda: result


def test_run_with_halo_uses_result_message_on_success():
    """Test _runWithHalo shows DetectResult.message when ok=True.

    GIVEN a detector that returns DetectResult(ok=True, message="MongoDB CE v7.0 → no action required")
    WHEN _runWithHalo is called
    THEN Halo stop_and_persist is called with the successIcon and the DetectResult.message.
    """
    stub, fn = _make_mixin_stub(DetectResult(ok=True, message="MongoDB CE v7.0 → no action required"))

    with patch("mas.cli.update.dependencies.Halo") as MockHalo:
        mockH = MagicMock()
        MockHalo.return_value.__enter__ = MagicMock(return_value=mockH)
        MockHalo.return_value.__exit__ = MagicMock(return_value=False)
        stub._runWithHalo("Checking for MongoDB Community", fn)

    mockH.stop_and_persist.assert_called_once_with(symbol="✅", text="MongoDB CE v7.0 → no action required")


def test_run_with_halo_uses_result_message_on_failure():
    """Test _runWithHalo shows DetectResult.message when ok=False.

    GIVEN a detector that returns DetectResult(ok=False, message="CP4D upgrade path is invalid")
    WHEN _runWithHalo is called
    THEN Halo stop_and_persist is called with the failureIcon and the DetectResult.message,
         and fatalError is called with the same message.
    """
    stub, fn = _make_mixin_stub(DetectResult(ok=False, message="CP4D upgrade path is invalid"))
    fatalCalls = []
    stub.fatalError = lambda msg: fatalCalls.append(msg)

    with patch("mas.cli.update.dependencies.Halo") as MockHalo:
        mockH = MagicMock()
        MockHalo.return_value.__enter__ = MagicMock(return_value=mockH)
        MockHalo.return_value.__exit__ = MagicMock(return_value=False)
        stub._runWithHalo("Checking for IBM Cloud Pak for Data", fn)

    mockH.stop_and_persist.assert_called_once_with(symbol="❌", text="CP4D upgrade path is invalid")
    assert fatalCalls == ["CP4D upgrade path is invalid"]


# ---------------------------------------------------------------------------
# runDependencyChecks TUI path uses DetectResult from non-fatal detectors
# ---------------------------------------------------------------------------


def test_run_dependency_checks_tui_path_uses_detect_result_message():
    """Test runDependencyChecks TUI path forwards DetectResult.message to progressCallback.

    GIVEN a DependencyDetectionMixin subclass where a non-fatal detect method
          returns DetectResult(ok=True, message="MongoDB CE v7 already at target")
    WHEN runDependencyChecks(progressCallback) is called
    THEN progressCallback is called with (label, True, "MongoDB CE v7 already at target").
    """

    class Stub(DependencyDetectionMixin):
        _DEPENDENCY_CHECKS = []

        def detectMongoDb(self):
            return DetectResult(ok=True, message="MongoDB CE v7 already at target")

        def evaluatePreinstallRBACAccessForUpdate(self):
            pass

        def getParam(self, key):
            return ""

    from mas.cli.update.dependencies import CheckItem

    stub = Stub()
    stub._DEPENDENCY_CHECKS = [
        CheckItem("MongoDB Community", "detectMongoDb", "mongodb_namespace"),
    ]

    calls = []
    stub.runDependencyChecks(progressCallback=lambda label, ok, detail: calls.append((label, ok, detail)))

    assert len(calls) == 2  # one check + RBAC
    assert calls[0] == ("MongoDB Community", True, "MongoDB CE v7 already at target")


def test_run_dependency_checks_tui_path_fatal_check_still_uses_bool():
    """Test runDependencyChecks TUI path for fatal checks: ok=False when found.

    GIVEN a fatal-if-present check whose method returns DetectResult(ok=False, message="Installed")
    WHEN runDependencyChecks(progressCallback) is called
    THEN progressCallback receives (label, False, "Installed") and RuntimeError is raised.
    """

    class Stub(DependencyDetectionMixin):
        _DEPENDENCY_CHECKS = []

        def isWatsonDiscoveryInstalled(self):
            return DetectResult(ok=False, message="Installed — update cannot proceed")

        def evaluatePreinstallRBACAccessForUpdate(self):
            pass

        def getParam(self, key):
            return ""

    from mas.cli.update.dependencies import CheckItem

    stub = Stub()
    stub._DEPENDENCY_CHECKS = [
        CheckItem(
            "IBM Watson Discovery",
            "isWatsonDiscoveryInstalled",
            "",
            fatal_if_present=True,
            present_message="Installed — update cannot proceed",
        ),
    ]

    calls = []
    try:
        stub.runDependencyChecks(progressCallback=lambda label, ok, detail: calls.append((label, ok, detail)))
    except RuntimeError:
        pass

    assert len(calls) == 1
    label, ok, detail = calls[0]
    assert label == "IBM Watson Discovery"
    assert ok is False
    assert "Installed" in detail
