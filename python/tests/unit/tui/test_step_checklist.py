# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for the StepChecklist widget (tui/widgets/step_checklist.py).

Covers the item-marking primitives extracted from the AutoRunScreen and
LaunchScreen (phase 3.2 of the visual polish plan) without requiring a
running Textual app — the DOM queries are mocked at the widget boundary.
The launch screen's on_done hook contract (Submit PipelineRun special
case) is covered by tests/unit/tui/test_tui_launch_screen.py and the
pilot tests.
"""

import pytest
from unittest.mock import MagicMock, patch

from mas.cli.tui.widgets.step_checklist import StepChecklist, pending_label

pytestmark = pytest.mark.tui


def _mock_item(classes=None):
    """Return (mock ListItem, mock Label) wired as query_one would return them.

    Args:
        classes (set, optional): Classes the mock item reports having.

    Returns:
        tuple: (MagicMock ListItem, MagicMock Label).
    """
    mock_label = MagicMock()
    mock_item = MagicMock()
    mock_item.classes = classes if classes is not None else set()
    mock_item.query_one = MagicMock(return_value=mock_label)
    return mock_item, mock_label


def test_pending_label_has_prefix():
    """Test that pending items are prefixed with the pending glyph.

    GIVEN a plain step label
    WHEN the pending-state display text is produced
    THEN it starts with the pending glyph (○).
    """
    assert pending_label("IBM Db2").startswith("○"), f"Expected '○' prefix, got: {pending_label('IBM Db2')!r}"


def test_mark_done_updates_label_text():
    """Test that mark_done updates the Label text inside the ListItem with result detail.

    GIVEN a StepChecklist with a step-list
    WHEN mark_done(label, ok=True, detail="Not installed") is called
    THEN the Label inside the matching ListItem shows "✓ <label>: <detail>".
    """
    checklist = StepChecklist(["IBM Db2"], "dep-step-")
    mock_item, mock_label = _mock_item()

    with patch.object(checklist, "query_one", return_value=mock_item):
        checklist.mark_done("IBM Db2", True, "All Db2uCluster instances in ibm-db2")

    mock_label.update.assert_called_once_with("✓ IBM Db2: All Db2uCluster instances in ibm-db2")


def test_mark_done_failure_uses_cross():
    """Test that mark_done uses ✗ prefix when ok=False.

    GIVEN a StepChecklist with a step-list
    WHEN mark_done(label, ok=False, detail="Installed — update cannot proceed") is called
    THEN the Label text starts with "✗".
    """
    checklist = StepChecklist(["IBM Watson Discovery"], "dep-step-")
    mock_item, mock_label = _mock_item()

    with patch.object(checklist, "query_one", return_value=mock_item):
        checklist.mark_done("IBM Watson Discovery", False, "Installed — update cannot proceed")

    call_text = mock_label.update.call_args[0][0]
    assert call_text.startswith("✗"), f"Expected text starting with '✗', got: {call_text!r}"


def test_mark_done_uses_on_done_hook_text():
    """Test that the on_done hook can override the item text.

    GIVEN a StepChecklist constructed with an on_done hook returning custom text
    WHEN mark_done is called
    THEN the Label shows the hook's text instead of the default.
    """
    hook_calls = {}

    def hook(label, ok, detail):
        hook_calls["args"] = (label, ok, detail)
        return "custom text"

    checklist = StepChecklist(["Submit PipelineRun"], "launch-step-", on_done=hook)
    mock_item, mock_label = _mock_item()

    with patch.object(checklist, "query_one", return_value=mock_item):
        checklist.mark_done("Submit PipelineRun", True, "https://example.com/run")

    mock_label.update.assert_called_once_with("custom text")
    assert hook_calls["args"] == ("Submit PipelineRun", True, "https://example.com/run")


def test_mark_done_hook_returning_none_uses_default_text():
    """Test that a None return from the on_done hook keeps the default text.

    GIVEN a StepChecklist constructed with an on_done hook returning None
    WHEN mark_done is called
    THEN the Label shows the default "<glyph> <label>: <detail>" text.
    """
    checklist = StepChecklist(["Validate OpenShift Pipelines"], "launch-step-", on_done=lambda label, ok, detail: None)
    mock_item, mock_label = _mock_item()

    with patch.object(checklist, "query_one", return_value=mock_item):
        checklist.mark_done("Validate OpenShift Pipelines", True, "Operator is ready")

    mock_label.update.assert_called_once_with("✓ Validate OpenShift Pipelines: Operator is ready")


def test_mark_active_marks_existing_item():
    """Test that mark_active swaps the item to the active class and glyph.

    GIVEN a StepChecklist with a pre-populated item
    WHEN mark_active is called for a known label
    THEN the item gains step-active (losing the other state classes) and its
        Label shows "◐ <label>".
    """
    checklist = StepChecklist(["Prepare pipelines namespace"], "launch-step-")
    mock_item, mock_label = _mock_item()

    with patch.object(checklist, "query_one", return_value=mock_item):
        checklist.mark_active("Prepare pipelines namespace")

    mock_item.remove_class.assert_called_once_with("step-skipped", "step-completed", "step-error")
    mock_item.add_class.assert_called_once_with("step-active")
    mock_label.update.assert_called_once_with("◐ Prepare pipelines namespace")


def test_mark_active_appends_unknown_label():
    """Test that mark_active appends a dynamic (runtime-evaluated) stage.

    GIVEN a StepChecklist pre-populated with only the fixed stages
    WHEN mark_active is called for a label not in that list (e.g. an RBAC
        stage evaluated at runtime)
    THEN a new item is appended for it and the label becomes known to the
        checklist.
    """
    checklist = StepChecklist(["Known stage"], "launch-step-")
    appended = []

    known_item, _ = _mock_item()

    def fake_query_one(selector, widget_type=None):
        if "known-stage" in selector:
            return known_item
        raise ValueError(f"no match for {selector}")

    with (
        patch("mas.cli.tui.widgets.step_checklist.ListItem") as list_item_cls,
        patch.object(checklist, "query_one", side_effect=fake_query_one),
        patch.object(checklist, "append", side_effect=lambda item: appended.append(item)),
    ):
        checklist.mark_active("Dynamic RBAC stage")

    list_item_cls.assert_called_once()
    assert len(appended) == 1, "Expected the dynamic stage to be appended"
    assert "Dynamic RBAC stage" in checklist.labels


def test_mark_error_first_pending_marks_first_unfinished_item():
    """Test that mark_error_first_pending marks the first not-yet-completed item.

    GIVEN a StepChecklist whose first item has completed and whose second is
        still pending
    WHEN mark_error_first_pending("boom") is called
    THEN only the second item is marked as an error carrying the message.
    """
    checklist = StepChecklist(["A", "B"], "launch-step-")
    item_a, label_a = _mock_item(classes={"step-completed"})
    item_b, label_b = _mock_item(classes={"step-skipped"})

    def fake_query_one(selector, widget_type=None):
        return item_a if selector.endswith("-a") else item_b

    with patch.object(checklist, "query_one", side_effect=fake_query_one):
        checklist.mark_error_first_pending("boom")

    label_a.update.assert_not_called()
    item_b.add_class.assert_called_once_with("step-error")
    label_b.update.assert_called_once_with("✗ B: boom")
