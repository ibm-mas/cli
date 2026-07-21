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
    """Test that _run_launch() calls launchUpdate on the app with a callable.

    GIVEN a stub app with a launchUpdate method that records its progressCallback
    WHEN _run_launch() is invoked with app patched to a no-op call_from_thread
    THEN launchUpdate is called exactly once with a callable progressCallback.
    """
    from mas.cli.tui.screens.launch import LaunchScreen
    from unittest.mock import patch

    calls = []

    def fake_launch_update(progressCallback):
        calls.append(progressCallback)

    mas_app = MagicMock()
    mas_app.launchUpdate = fake_launch_update

    step = WorkflowStep(id="launch", heading="Launch Update")
    screen = LaunchScreen.__new__(LaunchScreen)
    screen._mas_app = mas_app
    screen._step = step
    screen._step_index = 4

    mock_app = MagicMock()
    # call_from_thread is a no-op — we only care that launchUpdate was called,
    # not that the UI callbacks (_enable_done etc.) execute on the widget.
    mock_app.call_from_thread = MagicMock()

    with patch.object(type(screen), "app", new_callable=lambda: property(lambda self: mock_app)):
        screen._run_launch()

    assert len(calls) == 1, "Expected launchUpdate to be called once"
    assert callable(calls[0]), "Expected a callable progressCallback"
