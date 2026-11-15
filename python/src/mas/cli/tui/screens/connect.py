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
    from textual.containers import Horizontal, VerticalScroll
    from textual.widgets import Button, ContentSwitcher, Input, Label, Switch
except ModuleNotFoundError as exc:
    raise ImportError("The Textual TUI requires textual to be installed. Install it with: pip install mas-cli[tui]") from exc

from mas.cli.tui.messages import StepCompleted
from mas.cli.tui.models import WorkflowStep


class ConnectStepScreen(VerticalScroll):
    """Content panel for the OCP cluster connection step.

    Implements a two-sub-screen flow inside a single ContentSwitcher:

    * **Sub-screen A** (``reuse``): Shown when an active kubeconfig connection
      is detected.  Displays the console URL and offers Yes / No buttons.
      Choosing Yes fires the action in a worker and advances the workflow.
      Choosing No switches to sub-screen B.

    * **Sub-screen B** (``new``): Shown when no active connection exists, or
      when the user chose No on sub-screen A.  Collects Server URL, Login
      Token, and Skip TLS then runs ``_connectFromParams`` on Connect.
      Connection failures are displayed inline — the screen does **not**
      advance until the connection succeeds.

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
        """Build the two-sub-screen layout.

        Yields:
            ContentSwitcher containing the reuse and new-credentials sub-screens,
            followed by a shared error label visible on both.
        """
        yield Label("Connect to OpenShift Cluster", classes="connect-heading")
        with ContentSwitcher(id="connect-switcher", initial="connect-reuse"):
            with VerticalScroll(id="connect-reuse", can_focus=False):
                yield Label("", id="reuse-url-label", classes="connect-url")
                with Horizontal(id="reuse-buttons"):
                    yield Button("Yes — reuse this connection", id="btn-reuse-yes", variant="success")
                    yield Button("No — connect to a different cluster", id="btn-reuse-no", variant="default")
            with VerticalScroll(id="connect-new", can_focus=False):
                yield Label("Server URL", classes="connect-field-label")
                yield Input(placeholder="https://api.cluster.example.com:6443", id="input-server-url")
                yield Label("Login Token", classes="connect-field-label")
                yield Input(placeholder="sha256~…", password=True, id="input-login-token")
                yield Label("Skip TLS Verify", classes="connect-field-label")
                yield Switch(value=False, id="switch-skip-tls")
                yield Button("Connect", id="btn-connect", variant="primary")
        # Shared error label — rendered outside the switcher so it is always
        # visible regardless of which sub-screen is active.
        yield Label("", id="connect-error-label", classes="connect-error")

    def on_mount(self) -> None:
        """Detect active connection and configure initial sub-screen."""
        self.run_worker(self._detect_connection, thread=True)

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
            label.update(f"Re-use active connection:\n  {url}")
            switcher.current = "connect-reuse"
            self.query_one("#btn-reuse-yes", Button).focus()
        else:
            switcher.current = "connect-new"
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

    def _do_reuse_connect(self) -> None:
        """Reuse the active kubeconfig connection in a worker thread.

        Raises:
            Exception: Propagated from _connectFromParams or post_connect on failure.
        """
        self._mas_app._connectFromParams()
        if self._post_connect is not None:
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
            self._post_connect()

    def _on_connect_success(self) -> None:
        """Advance the workflow after a successful connection."""
        self.post_message(StepCompleted(self._step_index))

    def _on_connect_error(self, exc: Exception) -> None:
        """Display connection error inline without advancing.

        Shown on the shared error label regardless of which sub-screen triggered
        the failure, including post_connect errors (e.g. no MAS instances found).

        Args:
            exc (Exception): The exception raised by the connection attempt.
        """
        error_label = self.query_one("#connect-error-label", Label)
        error_label.update(str(exc))
        try:
            btn = self.query_one("#btn-connect", Button)
            btn.disabled = False
            btn.label = "Connect"
        except Exception:
            pass

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
        On sub-screen B, ``btn-connect`` validates and attempts a new connection.

        Args:
            event (Button.Pressed): The button press event.
        """
        btn_id = event.button.id

        if btn_id == "btn-reuse-yes":
            self.run_worker(self._run_reuse, thread=True)

        elif btn_id == "btn-reuse-no":
            switcher = self.query_one("#connect-switcher", ContentSwitcher)
            switcher.current = "connect-new"
            self.query_one("#input-server-url", Input).focus()

        elif btn_id == "btn-connect":
            serverUrl = self.query_one("#input-server-url", Input).value.strip()
            loginToken = self.query_one("#input-login-token", Input).value.strip()
            skipTls = self.query_one("#switch-skip-tls", Switch).value
            if not serverUrl:
                error_label = self.query_one("#connect-error-label", Label)
                error_label.update("Server URL is required.")
                return
            event.button.disabled = True
            event.button.label = "Connecting…"
            error_label = self.query_one("#connect-error-label", Label)
            error_label.update("")
            self.run_worker(lambda: self._run_new(serverUrl, loginToken, skipTls), thread=True)
