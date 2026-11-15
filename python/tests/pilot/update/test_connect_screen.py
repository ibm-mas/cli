# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Pilot tests for the ConnectStepScreen (tui/screens/connect.py).

Drives the two-sub-screen connection flow with a live pilot against a
stubbed MAS app: active-connection reuse, new-credentials entry, inline
error display on failure, and required-field validation.
"""

import pytest
from textual.widgets import ContentSwitcher
from textual.widgets import Button, Input, Label, Switch  # noqa: F401 (Button, Label used)

from mas.cli.tui.models import WorkflowStep
from mas.cli.tui.screens.connect import ConnectStepScreen
from pilot.harness import click_button, run_screen_pilot, wait_for

pytestmark = pytest.mark.pilot


def _make_screen(getActiveConsoleURL=None, connectRaises=None, post_connect=None):
    """Return (screen, mas_app, calls) for the connect step.

    Args:
        getActiveConsoleURL (str, optional): Console URL to report, or None
            for no active connection.
        connectRaises (Exception, optional): Exception for
            _connectFromParams to raise instead of connecting.
        post_connect (Callable, optional): Post-connect hook to record.

    Returns:
        tuple: (screen, mas_app, calls) — calls records hook invocations.
    """
    from unittest.mock import MagicMock

    mas_app = MagicMock()
    mas_app.params = {}
    mas_app.getActiveConsoleURL.return_value = getActiveConsoleURL
    if connectRaises is not None:
        mas_app._connectFromParams.side_effect = connectRaises
    calls = {"post_connect": 0}

    def _post_connect():
        calls["post_connect"] += 1

    step = WorkflowStep(id="connect-cluster", heading="Connect to OpenShift Cluster")
    screen = ConnectStepScreen(mas_app, step, 0, post_connect=post_connect if post_connect else _post_connect)
    return screen, mas_app, calls


def test_active_connection_reuse_advances():
    """Test that an active kubeconfig connection is offered for reuse.

    GIVEN a stubbed app reporting an active connection
    WHEN the reuse sub-screen is shown and the user clicks Yes
    THEN _connectFromParams and the post-connect hook run and the screen
        posts StepCompleted.
    """
    screen, mas_app, calls = _make_screen(getActiveConsoleURL="https://console.example.com")

    async def drive(pilot, app):
        await wait_for(lambda: app.query_one("#connect-switcher", ContentSwitcher).current == "connect-reuse")
        assert "https://console.example.com" in str(app.query_one("#reuse-url-label", Label).render())
        await click_button(pilot, "#btn-reuse-yes")
        await wait_for(lambda: app.posted)

    app = run_screen_pilot(screen, drive)

    assert ("step_completed", 0) in app.posted
    assert mas_app._connectFromParams.called
    assert calls["post_connect"] == 1


def test_new_credentials_flow_advances():
    """Test the new-credentials sub-screen collects params and connects.

    GIVEN a stubbed app with no active connection
    WHEN the user enters server URL and token, toggles skip TLS, and clicks
        Connect
    THEN the connection params are written, _connectFromParams is called,
        and the screen posts StepCompleted.
    """
    screen, mas_app, _ = _make_screen(getActiveConsoleURL=None)

    async def drive(pilot, app):
        await wait_for(lambda: app.query_one("#connect-switcher", ContentSwitcher).current == "connect-new")
        app.query_one("#input-server-url", Input).value = "https://api.cluster.example.com:6443"
        app.query_one("#input-login-token", Input).value = "sha256~token"
        app.query_one("#switch-skip-tls", Switch).value = True
        await pilot.pause()
        await click_button(pilot, "#btn-connect")
        await wait_for(lambda: app.posted)

    app = run_screen_pilot(screen, drive)

    assert ("step_completed", 0) in app.posted
    assert mas_app._connectFromParams.called
    assert mas_app.params["server_url"] == "https://api.cluster.example.com:6443"
    assert mas_app.params["login_token"] == "sha256~token"
    assert mas_app.params["skip_tls_verify"] == "true"


def test_connect_error_displayed_inline():
    """Test that a connection failure is displayed inline without advancing.

    GIVEN a stubbed app whose _connectFromParams raises
    WHEN the user submits credentials
    THEN the error is shown on the shared error label, the Connect button
        is re-enabled, and nothing is posted.
    """
    screen, mas_app, _ = _make_screen(getActiveConsoleURL=None, connectRaises=RuntimeError("connection refused"))

    async def drive(pilot, app):
        await wait_for(lambda: app.query_one("#connect-switcher", ContentSwitcher).current == "connect-new")
        app.query_one("#input-server-url", Input).value = "https://api.cluster.example.com:6443"
        await pilot.pause()
        await click_button(pilot, "#btn-connect")
        await wait_for(lambda: "connection refused" in str(app.query_one("#connect-error-label", Label).render()))
        assert app.posted == []
        btn = app.query_one("#btn-connect", Button)
        assert btn.disabled is False
        assert btn.label == "Connect"

    app = run_screen_pilot(screen, drive)
    assert app.posted == []


def test_server_url_required():
    """Test that clicking Connect without a server URL shows an inline error.

    GIVEN the new-credentials sub-screen with an empty server URL
    WHEN the user clicks Connect
    THEN "Server URL is required." is shown and no worker starts.
    """
    screen, mas_app, _ = _make_screen(getActiveConsoleURL=None)

    async def drive(pilot, app):
        await wait_for(lambda: app.query_one("#connect-switcher", ContentSwitcher).current == "connect-new")
        await click_button(pilot, "#btn-connect")
        await pilot.pause()
        assert "Server URL is required" in str(app.query_one("#connect-error-label", Label).render())

    run_screen_pilot(screen, drive)

    assert not mas_app._connectFromParams.called
