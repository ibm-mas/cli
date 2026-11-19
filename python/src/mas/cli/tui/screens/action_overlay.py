# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Modal overlay displayed while a step action runs in a worker thread."""

try:
    from textual.app import ComposeResult
    from textual.containers import VerticalScroll
    from textual.screen import ModalScreen
    from textual.widgets import Button, Label, ProgressBar, RichLog
except ModuleNotFoundError as exc:
    raise ImportError("The Textual TUI requires textual to be installed. Install it with: pip install mas-cli[tui]") from exc

from mas.cli.tui.messages import ActionComplete


class ActionOverlay(ModalScreen):
    """Modal screen displayed while a step's blocking action callable runs.

    Shows an indeterminate ProgressBar and a RichLog for status messages.
    On success the overlay is automatically dismissed.  On exception the
    error is shown in the log and a Dismiss button is revealed.

    Attributes:
        _action: The callable to run in a worker thread.
        _step_index: Index of the step whose action is running.
    """

    def __init__(self, action, step_index: int) -> None:
        """Initialise the overlay.

        Args:
            action: Blocking callable to run in a worker thread.
            step_index (int): Index of the owning step.
        """
        super().__init__()
        self._action = action
        self._step_index = step_index

    def compose(self) -> ComposeResult:
        """Build the overlay widget tree.

        Yields:
            A centred dialog with ProgressBar, RichLog, and hidden Dismiss button.
        """
        with VerticalScroll(id="action-dialog"):
            yield Label("Running…", id="action-heading")
            yield ProgressBar(total=None, id="action-progress")
            yield RichLog(id="action-log", markup=True)
            yield Button("Dismiss", id="btn-dismiss", variant="default")

    def on_mount(self) -> None:
        """Start the action worker when the overlay mounts."""
        self.run_worker(self._run_action, thread=True)

    def _run_action(self) -> None:
        """Execute the step action in a worker thread.

        On success, dismisses the overlay and posts ActionComplete.
        On exception, logs the error and reveals the Dismiss button.
        """
        try:
            self._action()
            self.app.call_from_thread(self._on_success)
        except Exception as exc:  # noqa: BLE001
            self.app.call_from_thread(self._on_error, exc)

    def _on_success(self) -> None:
        """Handle successful action completion on the event loop thread."""
        self.app.post_message(ActionComplete(self._step_index))
        self.dismiss()

    def _on_error(self, exc: Exception) -> None:
        """Show error in log and reveal Dismiss button.

        Args:
            exc (Exception): The exception raised by the action.
        """
        log = self.query_one("#action-log", RichLog)
        log.write(f"[bold red]Error:[/bold red] {exc}")
        dismiss_btn = self.query_one("#btn-dismiss", Button)
        dismiss_btn.display = True
        progress = self.query_one("#action-progress", ProgressBar)
        progress.display = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Dismiss the overlay when the Dismiss button is pressed.

        Args:
            event (Button.Pressed): The button press event.
        """
        if event.button.id == "btn-dismiss":
            self.dismiss()
