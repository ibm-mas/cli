# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Auto-running dependency-detection checklist screen."""

from typing import Any

try:
    from textual.app import ComposeResult
    from textual.containers import VerticalScroll
    from textual.widgets import Button, Label, RichLog
except ModuleNotFoundError as exc:
    raise ImportError("The Textual TUI requires textual to be installed. Install it with: pip install mas-cli[tui]") from exc

from mas.cli.tui.messages import StepCompleted
from mas.cli.tui.models import WorkflowStep


class AutoRunScreen(VerticalScroll):
    """Content panel that runs a task automatically, streams results, then reveals Next.

    A generic "auto-run with progress" screen suitable for any step that follows
    the pattern: start work immediately when the step becomes active, report
    each result to a scrolling log, and reveal a Next button once done.

    The work is driven by calling ``runDependencyChecksWithProgress`` on the
    app instance — a convention expected on any app that uses this screen.
    Each progress callback invocation appends one ✓ or ✗ row to the log.

    Attributes:
        _mas_app: MAS CLI app instance.
        _step: The WorkflowStep being rendered.
        _step_index: Zero-based position in the definition.
    """

    def __init__(self, mas_app: Any, step: WorkflowStep, step_index: int) -> None:
        """Initialise the dependency checks screen.

        Args:
            mas_app: MAS CLI app instance.
            step (WorkflowStep): The dependency-checks WorkflowStep.
            step_index (int): Zero-based index in the workflow definition.
        """
        super().__init__(id=f"step-panel-{step.id}")
        self._mas_app = mas_app
        self._step = step
        self._step_index = step_index

    def compose(self) -> ComposeResult:
        """Build the screen: heading, description, log widget, and Next button.

        Yields:
            Label heading, description paragraphs, RichLog, and Next button.
        """
        yield Label(self._step.heading, id=f"heading-{self._step.id}")
        for para in self._step.description:
            yield Label(para, classes="description-para")
        yield RichLog(id="dep-log", markup=True, highlight=False)
        yield Button("Next →", id="btn-next-dep", classes="btn-next", variant="primary")

    def on_mount(self) -> None:
        """No-op on mount — checks start only when the step becomes active."""

    def start_dynamic_loaders(self) -> None:
        """Start the dependency checks worker when this step becomes active.

        Called by TextualShell._activate_step() so checks run only after the
        user has completed the preceding steps and params are fully populated.
        Focuses the log so the user can scroll immediately with arrow keys.
        """
        self.run_worker(self._run_checks, thread=True)
        self.query_one("#dep-log", RichLog).focus()

    def _run_checks(self) -> None:
        """Run all dependency checks in a worker thread.

        Calls ``runDependencyChecks(progressCallback)`` on the app, passing a
        callback that posts each result to the event loop for display.
        After all checks complete, enables the Next button.
        """
        try:
            self._mas_app.runDependencyChecks(lambda label, ok, detail: self.app.call_from_thread(self._append_result, label, ok, detail))
        except Exception as exc:  # noqa: BLE001
            self.app.call_from_thread(self._append_error, exc)
        self.app.call_from_thread(self._enable_next)

    def _append_result(self, label: str, ok: bool, detail: str) -> None:
        """Append one check result row to the RichLog.

        Args:
            label (str): Human-readable check name.
            ok (bool): True for success / informational, False for failure.
            detail (str): Short result text.
        """
        log = self.query_one("#dep-log", RichLog)
        icon = "[green]✓[/green]" if ok else "[red]✗[/red]"
        log.write(f"{icon} {label}: {detail}")

    def _append_error(self, exc: Exception) -> None:
        """Append an unexpected exception row to the RichLog.

        Args:
            exc (Exception): The exception raised during checks.
        """
        log = self.query_one("#dep-log", RichLog)
        log.write(f"[bold red]Error:[/bold red] {exc}")

    def _enable_next(self) -> None:
        """Reveal and enable the Next button once all checks have finished."""
        btn = self.query_one("#btn-next-dep", Button)
        btn.add_class("dep-ready")

    def reset(self) -> None:
        """Clear the log and re-hide the Next button for a workflow reset.

        Called by TextualShell.on_workflow_reset() so the screen is ready for
        a second pass through the dependency checks.
        """
        try:
            log = self.query_one("#dep-log", RichLog)
            log.clear()
        except Exception:
            pass
        try:
            btn = self.query_one("#btn-next-dep", Button)
            btn.remove_class("dep-ready")
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Advance the workflow when Next is clicked.

        Args:
            event (Button.Pressed): The button press event.
        """
        if event.button.id == "btn-next-dep":
            self.post_message(StepCompleted(self._step_index))
