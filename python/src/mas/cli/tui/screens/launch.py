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

from typing import Any, List, Optional

try:
    import pyperclip
except ModuleNotFoundError:
    # pyperclip is only used for the Copy URL button — the TUI remains
    # fully functional without it (the button simply does nothing).
    pyperclip = None

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Button, Label

from mas.cli.tui.links import linkText
from mas.cli.tui.models import WorkflowStep
from mas.cli.tui.widgets.action_bar import ActionBar
from mas.cli.tui.widgets.step_checklist import GLYPH_DONE, StepChecklist

# Fixed pipeline stage labels shown upfront (unconditional stages only).
# RBAC stages are inserted dynamically when applyPreInstallMASRBAC is set.
_LAUNCH_STEPS: List[str] = [
    "Validate OpenShift Pipelines",
    "Prepare pipelines namespace",
    "Install Tekton definitions",
    "Submit PipelineRun",
]


class LaunchScreen(Vertical):
    """Content panel that submits the Tekton pipeline and shows a step-list.

    Auto-starts when start_dynamic_loaders() is called (i.e. when the step
    becomes active, after the user clicks Confirm on the review step).
    Calls launchUpdate(progressCallback, startCallback) on the app instance.

    All pipeline stages are shown upfront in a sidebar-style step-list.
    Before each stage starts, ``startCallback`` marks it active.  After it
    completes, ``progressCallback`` marks it completed (or error).

    Reveals a Done button on success, or a Dismiss button on failure.
    Done calls app.exit(0).  The scrollable content sits in a
    ``.content-scroll`` area with a fixed ``.action-bar`` pinned below
    (status row + Copy URL / Done / Dismiss buttons); the hidden buttons
    are revealed without shifting the layout.

    Attributes:
        _mas_app: MAS CLI app instance.
        _step: The WorkflowStep being rendered.
        _step_index: Zero-based position in the definition.
        _step_labels: Ordered list of stage labels pre-populated at construction.
        _pipeline_url: Pipeline run URL once the PipelineRun is submitted.
    """

    def __init__(self, mas_app: Any, step: WorkflowStep, step_index: int) -> None:
        """Initialise the launch screen.

        Args:
            mas_app: MAS CLI app instance with a launchUpdate(progressCallback, startCallback) method.
            step (WorkflowStep): The launch WorkflowStep.
            step_index (int): Zero-based index in the workflow definition.
        """
        super().__init__(id=f"step-panel-{step.id}")
        self._mas_app = mas_app
        self._step = step
        self._step_index = step_index
        self._step_labels: List[str] = list(_LAUNCH_STEPS)
        self._pipeline_url: Optional[str] = None

    def compose(self) -> ComposeResult:
        """Build the screen: heading, description, step-list, then footer with action buttons.

        Yields:
            A scrollable area (``.content-scroll``) with the heading,
            description, StepChecklist and pipeline URL label, then a fixed
            ActionBar (``.action-bar``) with the status row and the
            Copy URL / Done / Dismiss buttons.  All three buttons are
            hidden until work completes; revealing them never shifts the
            layout.
        """
        with VerticalScroll(id="launch-content", classes="content-scroll"):
            yield Label(self._step.heading, id=f"heading-{self._step.id}", classes="step-heading")
            for para in self._step.description:
                yield Label(para, classes="description-para")
            yield StepChecklist(
                self._step_labels,
                "launch-step-",
                id="launch-step-list",
                classes="step-checklist--boxed",
                on_done=self._on_checklist_done,
            )
            yield Label("", id="pipeline-url")
        yield ActionBar(
            "View the pipeline run:",
            status_id="launch-prompt",
            id="launch-footer",
            buttons=[
                Button("Copy URL", id="btn-copy-url", classes="btn-copy-url", variant="primary"),
                Button("Done", id="btn-done", classes="btn-launch-done", variant="success"),
                Button("Dismiss", id="btn-dismiss-error", classes="btn-launch-dismiss", variant="error"),
            ],
        )

    def on_mount(self) -> None:
        """Hide action buttons and pipeline URL label on mount."""
        self.query_one("#btn-copy-url", Button).display = False
        self.query_one("#btn-done", Button).display = False
        self.query_one("#btn-dismiss-error", Button).display = False
        self.query_one("#pipeline-url", Label).display = False

    def start_dynamic_loaders(self) -> None:
        """Start the pipeline submission worker when this step becomes active.

        Called by TextualShell._activate_step() so the pipeline is submitted
        only after the user confirms on the review step and this step is shown.
        """
        self.run_worker(self._run_launch, thread=True)

    def _checklist(self) -> StepChecklist:
        """Return this screen's step checklist widget.

        Returns:
            StepChecklist: The pipeline-stage list.
        """
        return self.query_one("#launch-step-list", StepChecklist)

    def _on_checklist_done(self, label: str, ok: bool, detail: str):
        """Completion hook for the step checklist (Submit PipelineRun special case).

        For the "Submit PipelineRun" stage the pipeline URL is rendered in a
        dedicated ``#pipeline-url`` Label outside the bordered list box, keeping
        the URL on a single unbroken line that Textual can make ctrl+clickable;
        the list item then shows only the step name.  All other stages return
        None so the checklist shows its default ``"<glyph> <label>: <detail>"``
        text.

        Args:
            label (str): Human-readable stage name.
            ok (bool): True for success, False for failure.
            detail (str): Short result text (pipeline URL for the last stage).

        Returns:
            Optional[str]: Override text for the list item, or None for the
            checklist default.
        """
        if label == "Submit PipelineRun" and ok and detail:
            url_label = self.query_one("#pipeline-url", Label)
            # The URL is stylized as an OSC 8 hyperlink so ctrl+click opens
            # the full URL even though the text wraps in a narrow panel.
            url_label.update(linkText(detail))
            url_label.display = True
            # Store URL and show Copy URL button
            self._pipeline_url = detail
            self.query_one("#btn-copy-url", Button).display = True
            return f"{GLYPH_DONE} {label}"
        return None

    def _run_launch(self) -> None:
        """Submit the pipeline in a worker thread.

        Calls launchUpdate(progressCallback, startCallback) on the app.
        ``startCallback`` marks each stage active before the work runs.
        ``progressCallback`` marks it completed (or error) after, updating its text.
        On success, reveals the Done button.  On exception, reveals Dismiss.
        """
        try:
            self._mas_app.launchUpdate(
                progressCallback=lambda label, ok, detail: self.app.call_from_thread(self._checklist().mark_done, label, ok, detail),
                startCallback=lambda label: self.app.call_from_thread(self._checklist().mark_active, label),
            )
            self.app.call_from_thread(self._enable_done)
        except Exception as exc:  # noqa: BLE001
            self.app.call_from_thread(self._mark_error, str(exc))
            self.app.call_from_thread(self._enable_dismiss)

    def _mark_error(self, message: str) -> None:
        """Mark all still-pending items as error on an unexpected exception.

        Args:
            message (str): Error message shown on the first still-active item.
        """
        self._checklist().mark_error_first_pending(message)

    def _enable_done(self) -> None:
        """Reveal the Done button after successful pipeline submission."""
        self.query_one("#btn-done", Button).display = True

    def _enable_dismiss(self) -> None:
        """Reveal the Dismiss button after a failed pipeline submission."""
        self.query_one("#btn-dismiss-error", Button).display = True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle Copy URL, Done and Dismiss buttons.

        Args:
            event (Button.Pressed): The button press event.
        """
        if event.button.id == "btn-copy-url":
            if self._pipeline_url:
                try:
                    pyperclip.copy(self._pipeline_url)
                    # Provide visual feedback by temporarily updating button text
                    button = event.button
                    original_label = button.label
                    button.label = "Copied!"
                    self.set_timer(2.0, lambda: setattr(button, "label", original_label))
                except Exception:
                    # If clipboard fails, silently ignore (pyperclip may not be available on all systems)
                    pass
        elif event.button.id == "btn-done":
            self.app.exit(0)
        elif event.button.id == "btn-dismiss-error":
            self.app.exit(1)
