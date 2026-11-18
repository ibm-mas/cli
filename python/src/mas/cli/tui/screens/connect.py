# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""OCP cluster connection step screen."""

from typing import Any, Callable, Optional

try:
    from textual.app import ComposeResult
    from textual.containers import Vertical, VerticalScroll
    from textual.widgets import Button, ContentSwitcher, Input, Label, Switch
except ModuleNotFoundError as exc:
    raise ImportError("The Textual TUI requires textual to be installed. Install it with: pip install mas-cli[tui]") from exc

from mas.cli.tui.links import linkText
from mas.cli.tui.messages import StepCompleted
from mas.cli.tui.models import WorkflowStep
from mas.cli.tui.widgets.action_bar import ActionBar


class ConnectStepScreen(Vertical):
    """Content panel for the OCP cluster connection step.

    Implements a two-sub-screen flow inside a single ContentSwitcher, laid
    out with the shared screen shape: a ``.content-scroll`` area holding
    the heading and the switcher, and a fixed ``.action-bar`` below it
    with a reserved status row (busy spinner + message, or the error) and
    the action buttons:

    * **Sub-screen A** (``reuse``): Shown when an active kubeconfig connection
      is detected.  Displays the console URL; the action bar shows the
      Yes / No buttons.  Choosing Yes fires the action in a worker and
      advances the workflow.  Choosing No switches to sub-screen B.

    * **Sub-screen B** (``new``): Shown when no active connection exists, or
      when the user chose No on sub-screen A.  Collects Server URL, Login
      Token, and Skip TLS; the action bar shows the Connect button —
      disabled until both the server URL and login token are provided —
      plus a Cancel button that returns to the reuse sub-screen without
      changing the connection (only offered when there is a connection to
      go back to).  Connection failures are displayed in the status row —
      the screen does **not** advance until the connection succeeds.

    Attributes:
        _mas_app: MAS CLI app instance.
        _step: The WorkflowStep providing action / step_index.
        _step_index: Zero-based position in the definition.
        _post_connect: Optional callable run after a successful connection.
        _console_url: Detected console URL or None.
    """

    BINDINGS = [
        ("left", "focus_yes", "Yes"),
        ("right", "focus_no", "No"),
    ]

    def __init__(self, mas_app: Any, step: WorkflowStep, step_index: int, post_connect: Optional[Callable] = None) -> None:
        """Initialise the connect step screen.

        Args:
            mas_app: MAS CLI app instance.
            step (WorkflowStep): The connect-cluster WorkflowStep.
            step_index (int): Zero-based index in the workflow definition.
            post_connect (Callable, optional): Called in the worker thread
                immediately after a successful connection, before the workflow
                advances.  Use this for any blocking work that depends on the
                cluster being connected (e.g. reading the installed catalog).
                Defaults to None.
        """
        super().__init__(id=f"step-panel-{step.id}")
        self._mas_app = mas_app
        self._step = step
        self._step_index = step_index
        self._post_connect = post_connect
        self._console_url: str | None = None

    def compose(self) -> ComposeResult:
        """Build the two-sub-screen layout with the shared action bar.

        Yields:
            A scrollable area (``.content-scroll``) with the heading and the
            ContentSwitcher holding the reuse and new-credentials
            sub-screens, then a fixed action bar (``.action-bar``) with the
            reserved status row (busy spinner + message, or the error) and
            the Yes / No / Connect / Cancel buttons.  Which buttons are
            visible follows the active sub-screen; Connect stays disabled
            until both credentials are provided; the busy spinner is hidden
            until a connection worker runs.
        """
        with VerticalScroll(classes="content-scroll"):
            yield Label("Connect to OpenShift Cluster", classes="connect-heading")
            with ContentSwitcher(id="connect-switcher", initial="connect-reuse"):
                with Vertical(id="connect-reuse"):
                    yield Label("", id="reuse-url-label", classes="connect-url")
                with Vertical(id="connect-new"):
                    yield Label("Server URL", classes="connect-field-label")
                    yield Input(placeholder="https://api.cluster.example.com:6443", id="input-server-url")
                    yield Label("Login Token", classes="connect-field-label")
                    yield Input(placeholder="sha256~…", password=True, id="input-login-token")
                    yield Label("Skip TLS Verify", classes="connect-field-label")
                    yield Switch(value=False, id="switch-skip-tls")
        yield ActionBar(
            "",
            status_id="connect-status-label",
            busy=True,
            buttons=[
                Button("Yes — reuse this connection", id="btn-reuse-yes", variant="success"),
                Button("No — connect to a different cluster", id="btn-reuse-no", variant="default"),
                Button("Connect", id="btn-connect", variant="primary"),
                Button("Cancel", id="btn-connect-cancel", variant="default"),
            ],
        )

    def on_mount(self) -> None:
        """Detect active connection and configure initial sub-screen.

        The reuse sub-screen (and its Yes / No buttons) is the initial
        state; the detection worker switches to the credentials sub-screen
        when no active connection exists.
        """
        self._set_mode(reuse=True)
        self.run_worker(self._detect_connection, thread=True)

    def _set_mode(self, reuse: bool) -> None:
        """Show the action buttons belonging to the active sub-screen.

        The action bar always occupies its fixed rows; only the visibility
        of the individual buttons changes, so switching sub-screens never
        shifts the layout.  Cancel only appears on the credentials
        sub-screen when there is a reuse sub-screen to go back to (i.e. an
        active connection was detected).

        Args:
            reuse (bool): True for the reuse sub-screen (Yes / No buttons),
                False for the credentials sub-screen (Connect / Cancel
                buttons).
        """
        self.query_one("#btn-reuse-yes", Button).display = reuse
        self.query_one("#btn-reuse-no", Button).display = reuse
        self.query_one("#btn-connect", Button).display = not reuse
        self.query_one("#btn-connect-cancel", Button).display = not reuse and self._console_url is not None
        if not reuse:
            self._refresh_connect_enabled()

    def _refresh_connect_enabled(self) -> None:
        """Enable Connect only when both credentials are provided.

        The server URL and login token must both be non-empty
        (whitespace-trimmed) before the connection can be attempted, so
        the button reflects that live as the inputs change.
        """
        server = self.query_one("#input-server-url", Input).value.strip()
        token = self.query_one("#input-login-token", Input).value.strip()
        self.query_one("#btn-connect", Button).disabled = not (server and token)

    def _detect_connection(self) -> None:
        """Probe for an existing kubeconfig connection in a worker thread.

        Updates the reuse label and switches to the appropriate sub-screen
        on the event-loop thread via call_from_thread.
        """
        url = self._mas_app.getActiveConsoleURL()
        self.app.call_from_thread(self._apply_detection, url)

    def _apply_detection(self, url: str | None) -> None:
        """Apply connection-detection results on the event-loop thread.

        Args:
            url (str | None): Detected console URL, or None if not connected.
        """
        self._console_url = url
        switcher = self.query_one("#connect-switcher", ContentSwitcher)
        if url:
            label = self.query_one("#reuse-url-label", Label)
            # The URL is stylized as an OSC 8 hyperlink so ctrl+click opens
            # the full URL even though the text wraps in a narrow panel.
            label.update(linkText(url, prefix="Re-use active connection:\n  "))
            switcher.current = "connect-reuse"
            self._set_mode(reuse=True)
            self.query_one("#btn-reuse-yes", Button).focus()
        else:
            switcher.current = "connect-new"
            self._set_mode(reuse=False)
            self.query_one("#input-server-url", Input).focus()

    def action_focus_yes(self) -> None:
        """Move focus to the Yes button (bound to left arrow key)."""
        try:
            self.query_one("#btn-reuse-yes", Button).focus()
        except Exception:
            pass

    def action_focus_no(self) -> None:
        """Move focus to the No button (bound to right arrow key)."""
        try:
            self.query_one("#btn-reuse-no", Button).focus()
        except Exception:
            pass

    def start_dynamic_loaders(self) -> None:
        """No-op — satisfies the interface expected by TextualShell."""

    def _action_bar(self) -> ActionBar:
        """Return this screen's action bar.

        Returns:
            ActionBar: The pinned status + buttons bar (with busy spinner).
        """
        return self.query_one(ActionBar)

    def _set_busy(self, message: str) -> None:
        """Show the busy spinner and message in the status row, disabling all connect buttons.

        Called on the event-loop thread when a connection worker starts, so
        the screen visibly responds to the button press while the connection
        and post-connect checks run in the background.

        Args:
            message (str): Status text shown next to the spinner.
        """
        self._action_bar().show_busy(message)
        for btn_id in ("#btn-reuse-yes", "#btn-reuse-no", "#btn-connect", "#btn-connect-cancel"):
            try:
                self.query_one(btn_id, Button).disabled = True
            except Exception:
                pass

    def _update_busy_message(self, message: str) -> None:
        """Update the busy status text without toggling buttons.

        Args:
            message (str): New status text shown next to the spinner.
        """
        self._action_bar().set_status(message)

    def _clear_busy(self) -> None:
        """Hide the busy spinner and clear the status row, re-enabling the connect buttons.

        Called on the event-loop thread when a connection attempt fails, so
        the user can correct the inputs and retry.  Connect is re-enabled
        through ``_refresh_connect_enabled`` so it stays disabled when the
        credentials are still incomplete.
        """
        bar = self._action_bar()
        bar.hide_busy()
        bar.clear_status()
        for btn_id in ("#btn-reuse-yes", "#btn-reuse-no", "#btn-connect-cancel"):
            try:
                self.query_one(btn_id, Button).disabled = False
            except Exception:
                pass
        self._refresh_connect_enabled()

    def on_input_changed(self, event: Input.Changed) -> None:
        """React to credential edits on the new-credentials sub-screen.

        Keeps the Connect button's enabled state in step with the inputs
        (both server URL and login token must be provided) and clears a
        stale error from the status row once the user edits the inputs.
        The busy message is left alone — it is only shown while the
        buttons are disabled.

        Args:
            event (Input.Changed): The input change event.
        """
        if event.input.id not in ("input-server-url", "input-login-token"):
            return
        self._refresh_connect_enabled()
        bar = self._action_bar()
        if bar.has_error:
            bar.clear_status()

    def _do_reuse_connect(self) -> None:
        """Reuse the active kubeconfig connection in a worker thread.

        Raises:
            Exception: Propagated from _connectFromParams or post_connect on failure.
        """
        self._mas_app._connectFromParams()
        if self._post_connect is not None:
            self.app.call_from_thread(self._update_busy_message, "Checking cluster configuration…")
            self._post_connect()

    def _do_new_connect(self, serverUrl: str, loginToken: str, skipTls: bool) -> None:
        """Connect with explicit credentials in a worker thread.

        Args:
            serverUrl (str): OCP API server URL.
            loginToken (str): Login token.
            skipTls (bool): Whether to skip TLS verification.

        Raises:
            Exception: Propagated from _connectFromParams or post_connect on failure.
        """
        self._mas_app.params["server_url"] = serverUrl
        self._mas_app.params["login_token"] = loginToken
        self._mas_app.params["skip_tls_verify"] = "true" if skipTls else "false"
        self._mas_app._connectFromParams()
        if self._post_connect is not None:
            self.app.call_from_thread(self._update_busy_message, "Checking cluster configuration…")
            self._post_connect()

    def _on_connect_success(self) -> None:
        """Advance the workflow after a successful connection."""
        self.post_message(StepCompleted(self._step_index))

    def _on_connect_error(self, exc: Exception) -> None:
        """Display connection error in the status row without advancing.

        Shown on the reserved status row regardless of which sub-screen
        triggered the failure, including post_connect errors (e.g. no MAS
        instances found).

        Args:
            exc (Exception): The exception raised by the connection attempt.
        """
        self._clear_busy()
        self._action_bar().set_error(str(exc))

    def _run_reuse(self) -> None:
        """Worker: run reuse connection then report success or error."""
        try:
            self._do_reuse_connect()
            self.app.call_from_thread(self._on_connect_success)
        except Exception as exc:  # noqa: BLE001
            self.app.call_from_thread(self._on_connect_error, exc)

    def _run_new(self, serverUrl: str, loginToken: str, skipTls: bool) -> None:
        """Worker: run new-credentials connection then report success or error.

        Args:
            serverUrl (str): OCP API server URL.
            loginToken (str): Login token.
            skipTls (bool): Whether to skip TLS verification.
        """
        try:
            self._do_new_connect(serverUrl, loginToken, skipTls)
            self.app.call_from_thread(self._on_connect_success)
        except Exception as exc:  # noqa: BLE001
            self.app.call_from_thread(self._on_connect_error, exc)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses for both sub-screens.

        On sub-screen A, ``btn-reuse-yes`` starts the reuse connection worker
        and ``btn-reuse-no`` switches to the credentials sub-screen.
        On sub-screen B, ``btn-connect`` attempts a new connection (it is
        disabled until both credentials are provided) and
        ``btn-connect-cancel`` returns to the reuse sub-screen without
        touching the connection or the collected params.

        Args:
            event (Button.Pressed): The button press event.
        """
        btn_id = event.button.id

        if btn_id == "btn-reuse-yes":
            self._set_busy("Connecting to cluster…")
            self.run_worker(self._run_reuse, thread=True)

        elif btn_id == "btn-reuse-no":
            switcher = self.query_one("#connect-switcher", ContentSwitcher)
            switcher.current = "connect-new"
            self._set_mode(reuse=False)
            self.query_one("#input-server-url", Input).focus()

        elif btn_id == "btn-connect":
            serverUrl = self.query_one("#input-server-url", Input).value.strip()
            loginToken = self.query_one("#input-login-token", Input).value.strip()
            skipTls = self.query_one("#switch-skip-tls", Switch).value
            self._set_busy("Connecting to cluster…")
            self.run_worker(lambda: self._run_new(serverUrl, loginToken, skipTls), thread=True)

        elif btn_id == "btn-connect-cancel":
            switcher = self.query_one("#connect-switcher", ContentSwitcher)
            switcher.current = "connect-reuse"
            self._set_mode(reuse=True)
            self.query_one("#btn-reuse-yes", Button).focus()
