# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Launch screen that submits the Tekton pipeline and streams progress."""

from typing import Any

try:
    from textual.app import ComposeResult
    from textual.containers import VerticalScroll
    from textual.widgets import Button, Label, RichLog
except ModuleNotFoundError as exc:
    raise ImportError("The Textual TUI requires textual to be installed. Install it with: pip install mas-cli[tui]") from exc

from mas.cli.tui.models import WorkflowStep


class LaunchScreen(VerticalScroll):
    """Content panel that submits the Tekton pipeline and streams progress.

    Auto-starts when start_dynamic_loaders() is called (i.e. when the step
    becomes active, after the user clicks Confirm on the review step).
    Calls launchUpdate(progressCallback) on the app instance. Appends one
    log row per stage. Reveals a Done button on success, or an error row
    and Dismiss button on failure. Done calls app.exit(0).

    Attributes:
        _mas_app: MAS CLI app instance.
        _step: The WorkflowStep being rendered.
        _step_index: Zero-based position in the definition.
    """

    def __init__(self, mas_app: Any, step: WorkflowStep, step_index: int) -> None:
        """Initialise the launch screen.

        Args:
            mas_app: MAS CLI app instance with a launchUpdate(progressCallback) method.
            step (WorkflowStep): The launch WorkflowStep.
            step_index (int): Zero-based index in the workflow definition.
        """
        super().__init__(id=f"step-panel-{step.id}")
        self._mas_app = mas_app
        self._step = step
        self._step_index = step_index

    def compose(self) -> ComposeResult:
        """Build the screen: heading, description, log widget, and action buttons.

        Yields:
            Label heading, description paragraphs, RichLog, Done button, and
            Dismiss button (both hidden initially).
        """
        yield Label(self._step.heading, id=f"heading-{self._step.id}")
        for para in self._step.description:
            yield Label(para, classes="description-para")
        yield RichLog(id="launch-log", markup=True, highlight=False)
        yield Button("✓ Done", id="btn-done", classes="btn-launch-done", variant="success")
        yield Button("✕ Dismiss", id="btn-dismiss-error", classes="btn-launch-dismiss", variant="error")

    def on_mount(self) -> None:
        """Hide both action buttons on mount — revealed only when work completes."""
        self.query_one("#btn-done", Button).display = False
        self.query_one("#btn-dismiss-error", Button).display = False

    def start_dynamic_loaders(self) -> None:
        """Start the pipeline submission worker when this step becomes active.

        Called by TextualShell._activate_step() so the pipeline is submitted
        only after the user confirms on the review step and this step is shown.
        """
        self.run_worker(self._run_launch, thread=True)

    def _run_launch(self) -> None:
        """Submit the pipeline in a worker thread.

        Calls launchUpdate(progressCallback) on the app, passing a callback
        that posts each result to the event loop for display. On success,
        reveals the Done button. On exception, appends the error and reveals
        the Dismiss button.
        """
        try:
            self._mas_app.launchUpdate(lambda label, ok, detail: self.app.call_from_thread(self._append_result, label, ok, detail))
            self.app.call_from_thread(self._enable_done)
        except Exception as exc:  # noqa: BLE001
            self.app.call_from_thread(self._append_error, exc)
            self.app.call_from_thread(self._enable_dismiss)

    def _append_result(self, label: str, ok: bool, detail: str) -> None:
        """Append one stage result row to the RichLog.

        Args:
            label (str): Human-readable stage name.
            ok (bool): True for success, False for failure.
            detail (str): Short result text.
        """
        log = self.query_one("#launch-log", RichLog)
        icon = "[green]✓[/green]" if ok else "[red]✗[/red]"
        log.write(f"{icon} {label}: {detail}")

    def _append_error(self, exc: Exception) -> None:
        """Append an unexpected exception row to the RichLog.

        Args:
            exc (Exception): The exception raised during pipeline submission.
        """
        log = self.query_one("#launch-log", RichLog)
        log.write(f"[bold red]Error:[/bold red] {exc}")

    def _enable_done(self) -> None:
        """Reveal the Done button after successful pipeline submission."""
        self.query_one("#btn-done", Button).display = True

    def _enable_dismiss(self) -> None:
        """Reveal the Dismiss button after a failed pipeline submission."""
        self.query_one("#btn-dismiss-error", Button).display = True

    def reset(self) -> None:
        """Clear the log and re-hide both buttons for a workflow reset.

        Called by TextualShell.on_workflow_reset() so the screen is ready for
        a second pass if the user resets the workflow.
        """
        try:
            log = self.query_one("#launch-log", RichLog)
            log.clear()
        except Exception:
            pass
        try:
            self.query_one("#btn-done", Button).display = False
        except Exception:
            pass
        try:
            self.query_one("#btn-dismiss-error", Button).display = False
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle Done and Dismiss buttons.

        Args:
            event (Button.Pressed): The button press event.
        """
        if event.button.id == "btn-done":
            self.app.exit(0)
        elif event.button.id == "btn-dismiss-error":
            self.app.exit(1)
