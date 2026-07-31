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

from typing import Any, List

try:
    from textual.app import ComposeResult
    from textual.containers import Horizontal, Vertical, VerticalScroll
    from textual.widgets import Button, Label, ListItem, ListView
except ModuleNotFoundError as exc:
    raise ImportError("The Textual TUI requires textual to be installed. Install it with: pip install mas-cli[tui]") from exc

from mas.cli.tui.models import WorkflowStep

# Fixed pipeline stage labels shown upfront (unconditional stages only).
# RBAC stages are inserted dynamically when applyPreInstallMASRBAC is set.
_LAUNCH_STEPS: List[str] = [
    "Validate OpenShift Pipelines",
    "Prepare pipelines namespace",
    "Install Tekton definitions",
    "Submit PipelineRun",
]


def _pending_label(label: str) -> str:
    """Return the pending-state display text for a step-list item.

    Args:
        label (str): Plain step label.

    Returns:
        str: Label prefixed with the pending icon.
    """
    return f"⬜ {label}"


class LaunchScreen(VerticalScroll):
    """Content panel that submits the Tekton pipeline and shows a step-list.

    Auto-starts when start_dynamic_loaders() is called (i.e. when the step
    becomes active, after the user clicks Confirm on the review step).
    Calls launchUpdate(progressCallback, startCallback) on the app instance.

    All pipeline stages are shown upfront in a sidebar-style step-list.
    Before each stage starts, ``startCallback`` marks it active.  After it
    completes, ``progressCallback`` marks it completed (or error).

    Reveals a Done button on success, or a Dismiss button on failure.
    Done calls app.exit(0).

    Attributes:
        _mas_app: MAS CLI app instance.
        _step: The WorkflowStep being rendered.
        _step_index: Zero-based position in the definition.
        _step_labels: Ordered list of stage labels pre-populated at construction.
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

    def compose(self) -> ComposeResult:
        """Build the screen: heading, description, step-list, then footer with action buttons.

        Yields:
            Scrollable content with heading, description and ListView, then a fixed
            footer section (border-top, guidance, Done/Dismiss buttons) matching
            ReviewScreen layout.  Both buttons are hidden until work completes.
        """
        with VerticalScroll(id="launch-content"):
            yield Label(self._step.heading, id=f"heading-{self._step.id}")
            for para in self._step.description:
                yield Label(para, classes="description-para")
            with ListView(id="launch-step-list"):
                for label in self._step_labels:
                    yield ListItem(Label(_pending_label(label)), id=f"launch-step-{_label_to_id(label)}", classes="step-skipped")
            yield Label("", id="pipeline-url")
        with Vertical(id="launch-footer"):
            yield Label("View the pipeline run:", id="launch-prompt")
            with Horizontal(id="launch-buttons"):
                yield Button("✓ Done", id="btn-done", classes="btn-launch-done", variant="success")
                yield Button("✕ Dismiss", id="btn-dismiss-error", classes="btn-launch-dismiss", variant="error")

    def on_mount(self) -> None:
        """Hide action buttons and pipeline URL label on mount."""
        self.query_one("#btn-done", Button).display = False
        self.query_one("#btn-dismiss-error", Button).display = False
        self.query_one("#pipeline-url", Label).display = False

    def start_dynamic_loaders(self) -> None:
        """Start the pipeline submission worker when this step becomes active.

        Called by TextualShell._activate_step() so the pipeline is submitted
        only after the user confirms on the review step and this step is shown.
        """
        self.run_worker(self._run_launch, thread=True)

    def _run_launch(self) -> None:
        """Submit the pipeline in a worker thread.

        Calls launchUpdate(progressCallback, startCallback) on the app.
        ``startCallback`` marks each stage active before the work runs.
        ``progressCallback`` marks it completed (or error) after, updating its text.
        On success, reveals the Done button.  On exception, reveals Dismiss.
        """
        try:
            self._mas_app.launchUpdate(
                progressCallback=lambda label, ok, detail: self.app.call_from_thread(self._mark_done, label, ok, detail),
                startCallback=lambda label: self.app.call_from_thread(self._mark_active, label),
            )
            self.app.call_from_thread(self._enable_done)
        except Exception as exc:  # noqa: BLE001
            self.app.call_from_thread(self._mark_error, str(exc))
            self.app.call_from_thread(self._enable_dismiss)

    def _mark_active(self, label: str) -> None:
        """Mark a stage list item as in-progress (active).

        If the label is not yet in the list (e.g. a dynamic RBAC stage), a new
        item is appended before being marked active.

        Args:
            label (str): Human-readable stage name.
        """
        item_id = f"#launch-step-{_label_to_id(label)}"
        try:
            item = self.query_one(item_id, ListItem)
        except Exception:
            # Dynamic RBAC stage — not in the pre-populated list; append it.
            list_view = self.query_one("#launch-step-list", ListView)
            new_item = ListItem(Label(_pending_label(label)), id=f"launch-step-{_label_to_id(label)}", classes="step-skipped")
            list_view.append(new_item)
            self._step_labels.append(label)
            item = new_item
        item.remove_class("step-skipped", "step-completed", "step-error")
        item.add_class("step-active")
        item.query_one(Label).update(f"⏳ {label}")

    def _mark_done(self, label: str, ok: bool, detail: str) -> None:
        """Mark a stage list item as completed or failed and update its text.

        For the "Submit PipelineRun" stage, the pipeline URL is rendered in a
        dedicated ``#pipeline-url`` Label outside the bordered list box, keeping
        the URL on a single unbroken line that Textual can make ctrl+clickable.
        All other stages show their detail inline in the list item as normal.

        Args:
            label (str): Human-readable stage name.
            ok (bool): True for success, False for failure.
            detail (str): Short result text (pipeline URL for the last stage).
        """
        icon = "✅" if ok else "❌"
        item_id = f"#launch-step-{_label_to_id(label)}"
        try:
            item = self.query_one(item_id, ListItem)
            item.remove_class("step-active", "step-skipped")
            if ok:
                item.add_class("step-completed")
            else:
                item.add_class("step-error")
            if label == "Submit PipelineRun" and ok and detail:
                # Show only the step name in the list; URL goes in the dedicated label.
                item.query_one(Label).update(f"{icon} {label}")
                url_label = self.query_one("#pipeline-url", Label)
                url_label.update(detail)
                url_label.display = True
            else:
                item.query_one(Label).update(f"{icon} {label}: {detail}")
        except Exception:
            pass

    def _mark_error(self, message: str) -> None:
        """Mark all still-pending items as error on an unexpected exception.

        Args:
            message (str): Error message shown on the first still-active item.
        """
        for label in self._step_labels:
            item_id = f"#launch-step-{_label_to_id(label)}"
            try:
                item = self.query_one(item_id, ListItem)
                if "step-active" in item.classes or "step-skipped" in item.classes:
                    item.remove_class("step-active", "step-skipped")
                    item.add_class("step-error")
                    item.query_one(Label).update(f"❌ {label}: {message}")
                    break
            except Exception:
                pass

    def _enable_done(self) -> None:
        """Reveal the Done button after successful pipeline submission."""
        self.query_one("#btn-done", Button).display = True

    def _enable_dismiss(self) -> None:
        """Reveal the Dismiss button after a failed pipeline submission."""
        self.query_one("#btn-dismiss-error", Button).display = True

    def reset(self) -> None:
        """Reset all stage items to pending, clear the URL label, and re-hide both buttons."""
        self._step_labels = list(_LAUNCH_STEPS)
        for label in self._step_labels:
            item_id = f"#launch-step-{_label_to_id(label)}"
            try:
                item = self.query_one(item_id, ListItem)
                item.remove_class("step-active", "step-completed", "step-error")
                item.add_class("step-skipped")
                item.query_one(Label).update(_pending_label(label))
            except Exception:
                pass
        try:
            url_label = self.query_one("#pipeline-url", Label)
            url_label.update("")
            url_label.display = False
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


def _label_to_id(label: str) -> str:
    """Convert a human-readable label to a CSS-safe identifier fragment.

    Replaces spaces and special characters with hyphens and lowercases the
    result so it is safe to use as a DOM id suffix.

    Args:
        label (str): Human-readable step label.

    Returns:
        str: CSS-safe id fragment.
    """
    return "".join(c if c.isalnum() else "-" for c in label.lower()).strip("-")
