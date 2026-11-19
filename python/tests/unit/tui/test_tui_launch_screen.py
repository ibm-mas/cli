# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for the LaunchScreen TUI widget (tui/screens/launch.py).

Tests that do not require a running Textual app (importability, callback
wiring) are covered here. Progress-callback rendering requires a live
Textual pilot and is documented as a manual smoke test.
"""

import pytest
from unittest.mock import MagicMock

from mas.cli.tui.models import WorkflowStep

pytestmark = pytest.mark.tui


def test_launch_screen_is_importable():
    """Test that LaunchScreen can be imported from the screens package.

    GIVEN the mas.cli.tui.screens package
    WHEN LaunchScreen is imported
    THEN no ImportError is raised.
    """
    from mas.cli.tui.screens import LaunchScreen  # noqa: F401

    assert LaunchScreen is not None


def test_launch_screen_calls_launch_update_on_app():
    """Test that _run_launch() calls launchUpdate on the app with callable kwargs.

    GIVEN a stub app with a launchUpdate method that records its kwargs
    WHEN _run_launch() is invoked with app patched to a no-op call_from_thread
    THEN launchUpdate is called exactly once with progressCallback and startCallback kwargs.
    """
    from mas.cli.tui.screens.launch import LaunchScreen
    from unittest.mock import patch

    received = {}

    def fake_launch_update(**kwargs):
        received.update(kwargs)

    mas_app = MagicMock()
    mas_app.launchUpdate = fake_launch_update

    step = WorkflowStep(id="launch", heading="Launch Update")
    screen = LaunchScreen.__new__(LaunchScreen)
    screen._mas_app = mas_app
    screen._step = step
    screen._step_index = 4
    screen._step_labels = list([])
    screen._launch_method = "launchUpdate"

    mock_app = MagicMock()
    # call_from_thread is a no-op — we only care that launchUpdate was called,
    # not that the UI callbacks (_enable_done etc.) execute on the widget.
    mock_app.call_from_thread = MagicMock()

    with patch.object(type(screen), "app", new_callable=lambda: property(lambda self: mock_app)):
        screen._run_launch()

    assert "progressCallback" in received, "Expected progressCallback kwarg"
    assert "startCallback" in received, "Expected startCallback kwarg"
    assert callable(received["progressCallback"]), "Expected progressCallback to be callable"


def test_launch_screen_has_step_labels_attribute():
    """Test that LaunchScreen has a _step_labels list pre-populated with stage labels.

    GIVEN the LaunchScreen class
    WHEN an instance is created
    THEN it has a _step_labels attribute that is a non-empty list of strings.
    """
    from mas.cli.tui.screens.launch import LaunchScreen

    mas_app = MagicMock()
    step = WorkflowStep(id="launch", heading="Launch Update")
    screen = LaunchScreen.__new__(LaunchScreen)
    screen._mas_app = mas_app
    screen._step = step
    screen._step_index = 4
    # Trigger __init__-equivalent attribute setup (already done via __new__ + manual assignment)
    # Call the class-level initialiser to set _step_labels
    LaunchScreen.__init__(screen, mas_app, step, 4)

    assert hasattr(screen, "_step_labels"), "Expected _step_labels on LaunchScreen"
    assert isinstance(screen._step_labels, list), "Expected _step_labels to be a list"
    assert len(screen._step_labels) > 0, "Expected _step_labels to be non-empty"


def test_launch_screen_step_labels_include_expected_stages():
    """Test that LaunchScreen._step_labels contains all expected pipeline stage labels.

    GIVEN the LaunchScreen class
    WHEN an instance is constructed
    THEN _step_labels contains entries for the four unconditional pipeline stages.
    """
    from mas.cli.tui.screens.launch import LaunchScreen

    mas_app = MagicMock()
    step = WorkflowStep(id="launch", heading="Launch Update")
    screen = LaunchScreen.__new__(LaunchScreen)
    LaunchScreen.__init__(screen, mas_app, step, 4)

    expected_substrings = [
        "OpenShift Pipelines",
        "pipelines namespace",
        "Tekton definitions",
        "PipelineRun",
    ]
    labels_joined = " ".join(screen._step_labels)
    for substr in expected_substrings:
        assert substr.lower() in labels_joined.lower(), f"Expected stage containing '{substr}' in _step_labels, got: {screen._step_labels}"


def test_launch_screen_run_launch_passes_start_callback():
    """Test that _run_launch passes both startCallback and progressCallback to launchUpdate.

    GIVEN a stub app that records its kwargs
    WHEN _run_launch() is called
    THEN launchUpdate is called with both startCallback and progressCallback kwargs.
    """
    from mas.cli.tui.screens.launch import LaunchScreen
    from unittest.mock import patch

    received_kwargs = {}

    def fake_launch_update(**kwargs):
        received_kwargs.update(kwargs)

    mas_app = MagicMock()
    mas_app.launchUpdate = fake_launch_update

    step = WorkflowStep(id="launch", heading="Launch Update")
    screen = LaunchScreen.__new__(LaunchScreen)
    LaunchScreen.__init__(screen, mas_app, step, 4)

    mock_app = MagicMock()
    mock_app.call_from_thread = MagicMock()

    with patch.object(type(screen), "app", new_callable=lambda: property(lambda self: mock_app)):
        screen._run_launch()

    assert "startCallback" in received_kwargs, "Expected startCallback kwarg passed to launchUpdate"
    assert "progressCallback" in received_kwargs, "Expected progressCallback kwarg passed to launchUpdate"
    assert callable(received_kwargs["startCallback"]), "Expected startCallback to be callable"
    assert callable(received_kwargs["progressCallback"]), "Expected progressCallback to be callable"


def test_launch_screen_dispatches_to_overridden_launch_method():
    """Test that the launch_method constructor argument selects the app method called.

    GIVEN a stub app with launchUpdate and launchUpgrade methods, and a
        LaunchScreen constructed with launch_method="launchUpgrade" (as the
        upgrade workflow wires)
    WHEN _run_launch() is invoked
    THEN launchUpgrade is called (not launchUpdate) with the progress
         callbacks, so each command submits its own pipeline.
    """
    from mas.cli.tui.screens.launch import LaunchScreen
    from unittest.mock import patch

    received_kwargs = {}

    def fake_launch_upgrade(**kwargs):
        received_kwargs.update(kwargs)

    mas_app = MagicMock()
    mas_app.launchUpgrade = fake_launch_upgrade

    step = WorkflowStep(id="launch", heading="Launch Upgrade")
    screen = LaunchScreen(mas_app, step, 3, launch_method="launchUpgrade")

    mock_app = MagicMock()
    mock_app.call_from_thread = MagicMock()

    with patch.object(type(screen), "app", new_callable=lambda: property(lambda self: mock_app)):
        screen._run_launch()

    mas_app.launchUpdate.assert_not_called()
    assert "progressCallback" in received_kwargs, "Expected progressCallback kwarg passed to launchUpgrade"
    assert "startCallback" in received_kwargs, "Expected startCallback kwarg passed to launchUpgrade"


def test_mark_done_pipeline_run_does_not_put_url_in_list_item():
    """Test that mark_done for Submit PipelineRun stores URL separately, not in the list item.

    GIVEN a LaunchScreen's StepChecklist (wired to the screen's on_done hook)
        with a mocked widget tree
    WHEN mark_done("Submit PipelineRun", True, "https://example.com/run") is called
    THEN the ListItem Label does NOT contain the URL text, only the step name,
        and the #pipeline-url label receives the URL.
    """
    from mas.cli.tui.screens.launch import LaunchScreen
    from mas.cli.tui.widgets.step_checklist import StepChecklist
    from unittest.mock import patch, MagicMock

    mas_app = MagicMock()
    step = WorkflowStep(id="launch", heading="Launch Update")
    screen = LaunchScreen.__new__(LaunchScreen)
    LaunchScreen.__init__(screen, mas_app, step, 4)

    checklist = StepChecklist(screen._step_labels, "launch-step-", on_done=screen._on_checklist_done)

    list_label = MagicMock()
    mock_item = MagicMock()
    mock_item.query_one = MagicMock(return_value=list_label)

    screen_widgets = {}

    def fake_screen_query_one(selector, widget_type=None):
        mock = MagicMock()
        screen_widgets[selector] = mock
        return mock

    with (
        patch.object(screen, "query_one", side_effect=fake_screen_query_one),
        patch.object(checklist, "query_one", return_value=mock_item),
    ):
        checklist.mark_done("Submit PipelineRun", True, "https://example.com/run")

    # The list item label should show the step name only, not the URL
    updated = list_label.update.call_args[0][0]
    assert "https://" not in updated, f"URL should not be in list item label, got: {updated!r}"
    assert updated == "✓ Submit PipelineRun"

    # The pipeline-url label should have been updated with the URL
    assert "#pipeline-url" in screen_widgets, "Expected #pipeline-url label to be queried"
    url_widget = screen_widgets["#pipeline-url"]
    assert url_widget.update.called, "Expected #pipeline-url label to be updated"
    updated_url = url_widget.update.call_args[0][0]
    assert "https://example.com/run" in str(updated_url), f"Expected URL in #pipeline-url update, got: {updated_url!r}"
    assert screen._pipeline_url == "https://example.com/run"


def test_mark_done_non_pipeline_step_puts_detail_in_list_item():
    """Test that mark_done for non-PipelineRun steps puts detail in the list item as normal.

    GIVEN a LaunchScreen's StepChecklist (wired to the screen's on_done hook)
        with a mocked widget tree
    WHEN mark_done("Validate OpenShift Pipelines", True, "Operator is ready") is called
    THEN the ListItem Label contains both the step name and detail text.
    """
    from mas.cli.tui.screens.launch import LaunchScreen
    from mas.cli.tui.widgets.step_checklist import StepChecklist
    from unittest.mock import patch, MagicMock

    mas_app = MagicMock()
    step = WorkflowStep(id="launch", heading="Launch Update")
    screen = LaunchScreen.__new__(LaunchScreen)
    LaunchScreen.__init__(screen, mas_app, step, 4)

    checklist = StepChecklist(screen._step_labels, "launch-step-", on_done=screen._on_checklist_done)

    list_label = MagicMock()
    mock_item = MagicMock()
    mock_item.query_one = MagicMock(return_value=list_label)

    with patch.object(checklist, "query_one", return_value=mock_item):
        checklist.mark_done("Validate OpenShift Pipelines", True, "Operator is ready")

    updated = list_label.update.call_args[0][0]
    assert "Operator is ready" in updated, f"Expected detail in list item label, got: {updated!r}"
    assert "Validate OpenShift Pipelines" in updated, f"Expected step name in list item label, got: {updated!r}"
