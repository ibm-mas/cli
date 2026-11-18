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

from typing import Any, List

try:
    from textual.app import ComposeResult
    from textual.containers import Vertical, VerticalScroll
    from textual.widgets import Button, Label
except ModuleNotFoundError as exc:
    raise ImportError("The Textual TUI requires textual to be installed. Install it with: pip install mas-cli[tui]") from exc

from mas.cli.tui.messages import StepCompleted
from mas.cli.tui.models import WorkflowStep
from mas.cli.tui.widgets.action_bar import ActionBar
from mas.cli.tui.widgets.step_checklist import StepChecklist, GLYPH_ERROR
from mas.cli.update.dependencies import dependencyCheckLabels


class AutoRunScreen(Vertical):
    """Content panel that runs dependency checks automatically, shows a step-list, then reveals Next.

    All steps are shown upfront in a sidebar-style list (using the same CSS
    classes as the workflow sidebar: ``step-skipped`` = pending, ``step-active``
    = in-progress, ``step-completed`` = done, ``step-error`` = failed).

    Before each check starts, the corresponding list item is highlighted as
    active via ``startCallback``.  After the check completes, it is marked
    completed (or error).  When all checks finish without failure, the Next
    button is revealed; a failed check blocks advancement (quit with ``q``),
    matching the CLI path where any failed check is fatal.

    The scrollable heading / description / step-list sit in a
    ``.content-scroll`` area with a fixed ``.action-bar`` pinned below:
    a reserved status row (guidance text, replaced by the error on
    failure) and the Next / Quit buttons.

    Attributes:
        _mas_app: MAS CLI app instance.
        _step: The WorkflowStep being rendered.
        _step_index: Zero-based position in the definition.
        _step_labels: Ordered list of check labels pre-populated at construction.
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
        self._step_labels: List[str] = list(dependencyCheckLabels())

    def compose(self) -> ComposeResult:
        """Build the screen: heading, description, step-list, then footer with Next button.

        Yields:
            A scrollable area (``.content-scroll``) with the heading,
            description paragraphs and the StepChecklist of dependency
            checks, then a fixed ActionBar (``.action-bar``) with a reserved
            status row (guidance text until a check fails, the error
            afterwards) and the Next and Quit buttons.  The Quit button is
            hidden until a check fails; revealing either button never shifts
            the layout.
        """
        with VerticalScroll(id="dep-content", classes="content-scroll"):
            yield Label(self._step.heading, id=f"heading-{self._step.id}", classes="step-heading")
            for para in self._step.description:
                yield Label(para, classes="description-para")
            yield StepChecklist(
                self._step_labels,
                "dep-step-",
                id="dep-step-list",
                classes="step-checklist--boxed",
            )
        yield ActionBar(
            "All checks must pass before you can continue.",
            status_id="dep-prompt",
            id="dep-footer",
            buttons=[
                Button("Next →", id="btn-next-dep", classes="btn-next", variant="primary"),
                Button("Quit", id="btn-quit-dep", classes="btn-quit-dep", variant="error"),
            ],
        )

    def on_mount(self) -> None:
        """No-op on mount — checks start only when the step becomes active."""

    def start_dynamic_loaders(self) -> None:
        """Start the dependency checks worker when this step becomes active.

        Called by TextualShell._activate_step() so checks run only after the
        user has completed the preceding steps and params are fully populated.
        """
        self.run_worker(self._run_checks, thread=True)

    def _checklist(self) -> StepChecklist:
        """Return this screen's step checklist widget.

        Returns:
            StepChecklist: The dependency-checks list.
        """
        return self.query_one("#dep-step-list", StepChecklist)

    def _action_bar(self) -> ActionBar:
        """Return this screen's action bar.

        Returns:
            ActionBar: The pinned status + buttons bar.
        """
        return self.query_one(ActionBar)

    def _run_checks(self) -> None:
        """Run all dependency checks in a worker thread.

        Calls ``runDependencyChecks(progressCallback, startCallback)`` on the app.
        ``startCallback`` marks each item active before the check runs.
        ``progressCallback`` marks it completed (or error) after, updating its text.
        The Next button is revealed only when every check passes — a failed
        check is blocking, matching the CLI path where failures are fatal.
        """
        try:
            self._mas_app.runDependencyChecks(
                progressCallback=lambda label, ok, detail: self.app.call_from_thread(self._checklist().mark_done, label, ok, detail),
                startCallback=lambda label: self.app.call_from_thread(self._checklist().mark_active, label),
            )
            self.app.call_from_thread(self._enable_next)
        except Exception as exc:  # noqa: BLE001
            self.app.call_from_thread(self._mark_error, str(exc))

    def _mark_error(self, message: str) -> None:
        """Show a blocking error in the action bar status row and reveal the Quit button.

        The reserved status row swaps its muted guidance text for the error
        message (red, bold) without changing height, so the layout does not
        shift (list items that already completed are left untouched — the
        failure is not attributable to any single pending check).  Because a
        failed check blocks advancement, the only available action is to
        quit (the ``q`` key binding or the revealed Quit button).

        Args:
            message (str): Error message describing why the checks failed.
        """
        self._action_bar().set_error(f"{GLYPH_ERROR} {message}")
        quit_btn = self.query_one("#btn-quit-dep", Button)
        quit_btn.add_class("dep-failed")

    def _enable_next(self) -> None:
        """Reveal and enable the Next button once all checks have passed."""
        self.query_one("#btn-next-dep", Button).add_class("dep-ready")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Advance the workflow on Next, or exit the app on Quit.

        Args:
            event (Button.Pressed): The button press event.
        """
        if event.button.id == "btn-next-dep":
            self.post_message(StepCompleted(self._step_index))
        elif event.button.id == "btn-quit-dep":
            self.app.exit(1)
