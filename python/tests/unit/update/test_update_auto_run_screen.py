# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for the AutoRunScreen step-list redesign (tui/screens/auto_run.py).

Covers structural contracts — labels pre-populated from _DEPENDENCY_CHECKS
and the startCallback/progressCallback wiring — without requiring a running
Textual app.
"""

import pytest
from unittest.mock import MagicMock, patch

from mas.cli.tui.models import WorkflowStep
from mas.cli.tui.screens.auto_run import _pending_label
from mas.cli.update.dependencies import _DEPENDENCY_CHECKS

pytestmark = pytest.mark.tui


def _make_screen():
    """Return an AutoRunScreen constructed without Textual by calling __init__ directly."""
    from mas.cli.tui.screens.auto_run import AutoRunScreen

    mas_app = MagicMock()
    step = WorkflowStep(id="dependency-checks", heading="Dependency Update Checks")
    screen = AutoRunScreen.__new__(AutoRunScreen)
    AutoRunScreen.__init__(screen, mas_app, step, 2)
    return screen


def test_auto_run_screen_has_step_labels_attribute():
    """Test that AutoRunScreen exposes a _step_labels list pre-populated from _DEPENDENCY_CHECKS.

    GIVEN the AutoRunScreen class
    WHEN an instance is created
    THEN it has a _step_labels attribute that is a non-empty list of strings.
    """
    screen = _make_screen()
    assert hasattr(screen, "_step_labels"), "Expected _step_labels attribute on AutoRunScreen"
    assert isinstance(screen._step_labels, list), "Expected _step_labels to be a list"
    assert len(screen._step_labels) > 0, "Expected _step_labels to be non-empty"


def test_auto_run_screen_step_labels_match_dependency_checks():
    """Test that AutoRunScreen._step_labels contains all _DEPENDENCY_CHECKS labels in order.

    GIVEN the DependencyDetectionMixin._DEPENDENCY_CHECKS registry
    WHEN an AutoRunScreen is constructed
    THEN _step_labels contains each CheckItem.label in the same order, plus the
         RBAC evaluation entry appended at the end.
    """
    screen = _make_screen()
    expected = [item.label for item in _DEPENDENCY_CHECKS]
    expected.append("Pre-install RBAC evaluation")
    assert screen._step_labels == expected, f"Expected {expected}, got {screen._step_labels}"


def test_auto_run_screen_run_checks_calls_start_and_progress():
    """Test that _run_checks passes both startCallback and progressCallback to runDependencyChecks.

    GIVEN a stub app that records the kwargs passed to runDependencyChecks
    WHEN _run_launch is invoked
    THEN runDependencyChecks is called with both startCallback and progressCallback callables.
    """
    from mas.cli.tui.screens.auto_run import AutoRunScreen

    received_kwargs = {}

    def fake_run_checks(**kwargs):
        received_kwargs.update(kwargs)

    mas_app = MagicMock()
    mas_app.runDependencyChecks = fake_run_checks
    step = WorkflowStep(id="dependency-checks", heading="Dependency Update Checks")
    screen = AutoRunScreen.__new__(AutoRunScreen)
    screen._mas_app = mas_app
    screen._step = step
    screen._step_index = 2
    screen._step_labels = ["Fake Check"]

    mock_app = MagicMock()
    mock_app.call_from_thread = MagicMock()

    with patch.object(type(screen), "app", new_callable=lambda: property(lambda self: mock_app)):
        screen._run_checks()

    assert "startCallback" in received_kwargs, "Expected startCallback kwarg passed to runDependencyChecks"
    assert "progressCallback" in received_kwargs, "Expected progressCallback kwarg passed to runDependencyChecks"
    assert callable(received_kwargs["startCallback"]), "Expected startCallback to be callable"
    assert callable(received_kwargs["progressCallback"]), "Expected progressCallback to be callable"


def test_auto_run_screen_mark_done_updates_label_text():
    """Test that _mark_done updates the Label text inside the ListItem with result detail.

    GIVEN an AutoRunScreen with a step-list
    WHEN _mark_done(label, ok=True, detail="Not installed") is called
    THEN the Label inside the matching ListItem shows "✓ <label>: <detail>".
    """
    screen = _make_screen()

    # Simulate the Textual query_one returning a mock ListItem with a child Label
    mock_label = MagicMock()
    mock_item = MagicMock()
    mock_item.query_one = MagicMock(return_value=mock_label)

    with patch.object(screen, "query_one", return_value=mock_item):
        screen._mark_done("IBM Db2", True, "All Db2uCluster instances in ibm-db2")

    mock_label.update.assert_called_once_with("✓ IBM Db2: All Db2uCluster instances in ibm-db2")


def test_auto_run_screen_mark_done_failure_uses_cross():
    """Test that _mark_done uses ✗ prefix when ok=False.

    GIVEN an AutoRunScreen with a step-list
    WHEN _mark_done(label, ok=False, detail="Installed — update cannot proceed") is called
    THEN the Label text starts with "✗".
    """
    screen = _make_screen()

    mock_label = MagicMock()
    mock_item = MagicMock()
    mock_item.query_one = MagicMock(return_value=mock_label)

    with patch.object(screen, "query_one", return_value=mock_item):
        screen._mark_done("IBM Watson Discovery", False, "Installed — update cannot proceed")

    call_text = mock_label.update.call_args[0][0]
    assert call_text.startswith("✗"), f"Expected text starting with '✗', got: {call_text!r}"


def test_auto_run_screen_pending_label_has_prefix():
    """Test that _step_labels items are prefixed with the pending glyph when composed.

    GIVEN an AutoRunScreen
    WHEN the initial label text for a step-list item is produced
    THEN it starts with the pending glyph (○).
    """
    screen = _make_screen()
    first_label = screen._step_labels[0]
    assert _pending_label(first_label).startswith("○"), f"Expected pending label to start with '○', got: {_pending_label(first_label)!r}"
