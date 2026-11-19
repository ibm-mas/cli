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


def test_long_console_url_wraps():
    """Test that a very long console URL wraps and stays fully clickable.

    GIVEN a stubbed app reporting an active connection whose console URL is
        longer than the content area width
    WHEN the reuse sub-screen is shown
    THEN the URL label folds onto multiple lines within the content area
        instead of overflowing it, and the URL carries an OSC 8 hyperlink
        style so ctrl+click opens the full URL despite the wrap.
    """
    long_url = "https://console-openshift-console.clidemo-6f1620198115433da1cac8216c06779b" "-0000.us-south.containers.appdomain.cloud"
    screen, _, _ = _make_screen(getActiveConsoleURL=long_url)

    async def drive(pilot, app):
        await wait_for(lambda: app.query_one("#connect-switcher", ContentSwitcher).current == "connect-reuse")
        label = app.query_one("#reuse-url-label", Label)
        rendered = label.render()
        assert long_url in str(rendered)
        # The URL portion must carry a link style (rendered by Textual as an
        # OSC 8 terminal hyperlink) covering the whole URL.
        link_styles = [str(span.style) for span in getattr(rendered, "spans", [])]
        assert any("link" in style and long_url in style for style in link_styles)
        # Harness runs at 100 columns; the content area is 96 wide
        # (.content-scroll padding 1 2).  The label must stay within it
        # and wrap (height grows) rather than overflow (width > 96).
        assert label.region.width <= 96
        assert label.region.height >= 3

    run_screen_pilot(screen, drive)


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


def test_action_buttons_follow_sub_screen():
    """Test that the action bar buttons swap with the active sub-screen.

    GIVEN a stubbed app reporting an active connection (reuse sub-screen)
    WHEN the screen is shown, then the user clicks No
    THEN the action bar shows Yes / No on the reuse sub-screen and swaps
        to Connect / Cancel on the credentials sub-screen, without the
        bar's fixed rows changing.
    """
    screen, _, _ = _make_screen(getActiveConsoleURL="https://console.example.com")

    async def drive(pilot, app):
        await wait_for(lambda: app.query_one("#connect-switcher", ContentSwitcher).current == "connect-reuse")
        assert app.query_one("#btn-reuse-yes", Button).display is True
        assert app.query_one("#btn-reuse-no", Button).display is True
        assert app.query_one("#btn-connect", Button).display is False
        bar = app.query_one(".action-bar")
        height_before = bar.region.height
        await click_button(pilot, "#btn-reuse-no")
        await wait_for(lambda: app.query_one("#connect-switcher", ContentSwitcher).current == "connect-new")
        assert app.query_one("#btn-reuse-yes", Button).display is False
        assert app.query_one("#btn-reuse-no", Button).display is False
        assert app.query_one("#btn-connect", Button).display is True
        assert app.query_one("#btn-connect-cancel", Button).display is True
        assert bar.region.height == height_before

    run_screen_pilot(screen, drive)


def test_busy_indicator_while_connecting():
    """Test that a busy indicator is shown while the connect worker runs.

    GIVEN a stubbed app whose _connectFromParams and post-connect hook each
        block until released
    WHEN the user clicks Yes on the reuse sub-screen
    THEN the busy indicator appears immediately with a status message, the
        connect buttons are disabled, the message advances once the
        connection succeeds, and the screen posts StepCompleted on release.
    """
    import threading
    from unittest.mock import MagicMock

    mas_app = MagicMock()
    mas_app.params = {}
    mas_app.getActiveConsoleURL.return_value = "https://console.example.com"

    connect_release = threading.Event()
    post_release = threading.Event()
    mas_app._connectFromParams.side_effect = lambda: connect_release.wait(timeout=5)

    def _blocking_post_connect():
        post_release.wait(timeout=5)

    step = WorkflowStep(id="connect-cluster", heading="Connect to OpenShift Cluster")
    screen = ConnectStepScreen(mas_app, step, 0, post_connect=_blocking_post_connect)

    async def drive(pilot, app):
        await wait_for(lambda: app.query_one("#connect-switcher", ContentSwitcher).current == "connect-reuse")
        await click_button(pilot, "#btn-reuse-yes")
        # The indicator must appear with the button press so the screen does
        # not feel unresponsive during the background work.  The connect
        # worker is still blocked here, so the first message is stable.
        # (The ActionBar's show_busy helper reveals the spinner.)
        busy = app.query_one("#action-busy-spinner")
        assert busy.display is True
        assert "Connecting to cluster" in str(app.query_one("#connect-status-label", Label).render())
        assert app.query_one("#btn-reuse-yes", Button).disabled is True
        # Once the connection itself succeeds the message advances to the
        # post-connect phase (catalog detection etc.) while still blocked.
        connect_release.set()
        await wait_for(lambda: "Checking cluster configuration" in str(app.query_one("#connect-status-label", Label).render()))
        assert app.query_one("#btn-reuse-yes", Button).disabled is True
        post_release.set()
        await wait_for(lambda: app.posted)

    app = run_screen_pilot(screen, drive)

    assert ("step_completed", 0) in app.posted
    assert mas_app._connectFromParams.called


def test_connect_error_displayed_inline():
    """Test that a connection failure is displayed inline without advancing.

    GIVEN a stubbed app whose _connectFromParams raises
    WHEN the user submits credentials
    THEN the error is shown on the status row, the busy indicator is
        hidden, the Connect button is re-enabled, and nothing is posted.
    """
    screen, mas_app, _ = _make_screen(getActiveConsoleURL=None, connectRaises=RuntimeError("connection refused"))

    async def drive(pilot, app):
        await wait_for(lambda: app.query_one("#connect-switcher", ContentSwitcher).current == "connect-new")
        app.query_one("#input-server-url", Input).value = "https://api.cluster.example.com:6443"
        app.query_one("#input-login-token", Input).value = "sha256~token"
        await pilot.pause()
        await click_button(pilot, "#btn-connect")
        await wait_for(lambda: "connection refused" in str(app.query_one("#connect-status-label", Label).render()))
        assert app.posted == []
        # hide_busy concealed the spinner again after the failure.
        assert app.query_one("#action-busy-spinner").display is False
        btn = app.query_one("#btn-connect", Button)
        assert btn.disabled is False
        assert btn.label == "Connect"

    app = run_screen_pilot(screen, drive)
    assert app.posted == []


def test_connect_disabled_until_credentials_provided():
    """Test that Connect stays disabled until both credentials are entered.

    GIVEN the new-credentials sub-screen with empty inputs
    WHEN the user enters only the server URL, then the login token
    THEN the Connect button is disabled until both are provided, and no
        connection is attempted while it is disabled.
    """
    screen, mas_app, _ = _make_screen(getActiveConsoleURL=None)

    async def drive(pilot, app):
        await wait_for(lambda: app.query_one("#connect-switcher", ContentSwitcher).current == "connect-new")
        btn = app.query_one("#btn-connect", Button)
        assert btn.disabled is True
        app.query_one("#input-server-url", Input).value = "https://api.cluster.example.com:6443"
        await pilot.pause()
        assert btn.disabled is True
        app.query_one("#input-login-token", Input).value = "sha256~token"
        await pilot.pause()
        assert btn.disabled is False

    run_screen_pilot(screen, drive)

    assert not mas_app._connectFromParams.called


def test_cancel_returns_to_reuse_screen():
    """Test that Cancel returns to the reuse sub-screen without connecting.

    GIVEN an active connection was detected and the user chose No
        (credentials sub-screen)
    WHEN the user clicks Cancel
    THEN the reuse sub-screen and its Yes / No buttons are shown again,
        no connection is attempted, and nothing is posted.
    """
    screen, mas_app, _ = _make_screen(getActiveConsoleURL="https://console.example.com")

    async def drive(pilot, app):
        await wait_for(lambda: app.query_one("#connect-switcher", ContentSwitcher).current == "connect-reuse")
        await click_button(pilot, "#btn-reuse-no")
        await wait_for(lambda: app.query_one("#connect-switcher", ContentSwitcher).current == "connect-new")
        # Partially entered credentials must survive a cancel round-trip
        # but never reach the app.
        app.query_one("#input-server-url", Input).value = "https://api.cluster.example.com:6443"
        await pilot.pause()
        await click_button(pilot, "#btn-connect-cancel")
        await wait_for(lambda: app.query_one("#connect-switcher", ContentSwitcher).current == "connect-reuse")
        assert app.query_one("#btn-reuse-yes", Button).display is True
        assert app.query_one("#btn-reuse-no", Button).display is True
        assert app.query_one("#btn-connect", Button).display is False

    app = run_screen_pilot(screen, drive)

    assert not mas_app._connectFromParams.called
    assert app.posted == []


def test_cancel_hidden_without_active_connection():
    """Test that Cancel is not offered when there is nothing to return to.

    GIVEN a stubbed app with no active connection
    WHEN the credentials sub-screen is shown
    THEN only the Connect button is visible — Cancel is hidden because the
        reuse sub-screen has no connection to go back to.
    """
    screen, _, _ = _make_screen(getActiveConsoleURL=None)

    async def drive(pilot, app):
        await wait_for(lambda: app.query_one("#connect-switcher", ContentSwitcher).current == "connect-new")
        assert app.query_one("#btn-connect", Button).display is True
        assert app.query_one("#btn-connect-cancel", Button).display is False
        assert app.query_one("#btn-reuse-yes", Button).display is False

    run_screen_pilot(screen, drive)
