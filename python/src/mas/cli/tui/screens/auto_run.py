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
    from textual.containers import Horizontal, Vertical, VerticalScroll
    from textual.widgets import Button, Label, ListItem, ListView
except ModuleNotFoundError as exc:
    raise ImportError("The Textual TUI requires textual to be installed. Install it with: pip install mas-cli[tui]") from exc

from mas.cli.tui.messages import StepCompleted
from mas.cli.tui.models import WorkflowStep
from mas.cli.update.dependencies import DependencyDetectionMixin

# All labels shown upfront in order — derived from the dependency-checks registry
# plus the final RBAC-evaluation step that runDependencyChecks always fires last.
_DEP_CHECK_LABELS: List[str] = [item.label for item in DependencyDetectionMixin._DEPENDENCY_CHECKS] + ["Pre-install RBAC evaluation"]


def _pending_label(label: str) -> str:
    """Return the pending-state display text for a step-list item.

    Args:
        label (str): Plain step label.

    Returns:
        str: Label prefixed with the pending icon.
    """
    return f"⬜ {label}"


class AutoRunScreen(VerticalScroll):
    """Content panel that runs dependency checks automatically, shows a step-list, then reveals Next.

    All steps are shown upfront in a sidebar-style list (using the same CSS
    classes as the workflow sidebar: ``step-skipped`` = pending, ``step-active``
    = in-progress, ``step-completed`` = done, ``step-error`` = failed).

    Before each check starts, the corresponding list item is highlighted as
    active via ``startCallback``.  After the check completes, it is marked
    completed (or error).  When all checks finish, the Next button is revealed.

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
        self._step_labels: List[str] = list(_DEP_CHECK_LABELS)

    def compose(self) -> ComposeResult:
        """Build the screen: heading, description, step-list, then footer with Next button.

        Yields:
            Label heading, description paragraphs, ListView of steps, then a
            footer section (border-top, guidance, Next button) matching ReviewScreen.
        """
        with VerticalScroll(id="dep-content"):
            yield Label(self._step.heading, id=f"heading-{self._step.id}")
            for para in self._step.description:
                yield Label(para, classes="description-para")
            with ListView(id="dep-step-list"):
                for label in self._step_labels:
                    yield ListItem(Label(_pending_label(label)), id=f"dep-step-{_label_to_id(label)}", classes="step-skipped")
        with Vertical(id="dep-footer"):
            yield Label("All checks must pass before you can continue.", id="dep-prompt")
            with Horizontal(id="dep-buttons"):
                yield Button("Next →", id="btn-next-dep", classes="btn-next", variant="primary")

    def on_mount(self) -> None:
        """No-op on mount — checks start only when the step becomes active."""

    def start_dynamic_loaders(self) -> None:
        """Start the dependency checks worker when this step becomes active.

        Called by TextualShell._activate_step() so checks run only after the
        user has completed the preceding steps and params are fully populated.
        """
        self.run_worker(self._run_checks, thread=True)

    def _run_checks(self) -> None:
        """Run all dependency checks in a worker thread.

        Calls ``runDependencyChecks(progressCallback, startCallback)`` on the app.
        ``startCallback`` marks each item active before the check runs.
        ``progressCallback`` marks it completed (or error) after, updating its text.
        After all checks complete, enables the Next button.
        """
        try:
            self._mas_app.runDependencyChecks(
                progressCallback=lambda label, ok, detail: self.app.call_from_thread(self._mark_done, label, ok, detail),
                startCallback=lambda label: self.app.call_from_thread(self._mark_active, label),
            )
        except Exception as exc:  # noqa: BLE001
            self.app.call_from_thread(self._mark_error, str(exc))
        self.app.call_from_thread(self._enable_next)

    def _mark_active(self, label: str) -> None:
        """Mark a step list item as in-progress (active).

        Args:
            label (str): Human-readable check name matching a list item.
        """
        item_id = f"#dep-step-{_label_to_id(label)}"
        try:
            item = self.query_one(item_id, ListItem)
            item.remove_class("step-skipped", "step-completed", "step-error")
            item.add_class("step-active")
            item.query_one(Label).update(f"⏳ {label}")
        except Exception:
            pass

    def _mark_done(self, label: str, ok: bool, detail: str) -> None:
        """Mark a step list item as completed or failed and update its text.

        Updates the Label inside the ListItem to show the result detail,
        matching the previous Markdown-log format but in the step-list widget.

        Args:
            label (str): Human-readable check name.
            ok (bool): True for success, False for failure.
            detail (str): Short result text from the detector.
        """
        icon = "✅" if ok else "❌"
        item_id = f"#dep-step-{_label_to_id(label)}"
        try:
            item = self.query_one(item_id, ListItem)
            item.remove_class("step-active", "step-skipped")
            if ok:
                item.add_class("step-completed")
            else:
                item.add_class("step-error")
            item.query_one(Label).update(f"{icon} {label}: {detail}")
        except Exception:
            pass

    def _mark_error(self, message: str) -> None:
        """Mark all still-pending items as error on an unexpected exception.

        Args:
            message (str): Error message shown on the first still-active item.
        """
        for label in self._step_labels:
            item_id = f"#dep-step-{_label_to_id(label)}"
            try:
                item = self.query_one(item_id, ListItem)
                if "step-active" in item.classes or "step-skipped" in item.classes:
                    item.remove_class("step-active", "step-skipped")
                    item.add_class("step-error")
                    item.query_one(Label).update(f"❌ {label}: {message}")
                    break
            except Exception:
                pass

    def _enable_next(self) -> None:
        """Reveal and enable the Next button once all checks have finished."""
        self.query_one("#btn-next-dep", Button).add_class("dep-ready")

    def reset(self) -> None:
        """Reset all step items to pending and restore their plain label text."""
        for label in self._step_labels:
            item_id = f"#dep-step-{_label_to_id(label)}"
            try:
                item = self.query_one(item_id, ListItem)
                item.remove_class("step-active", "step-completed", "step-error")
                item.add_class("step-skipped")
                item.query_one(Label).update(_pending_label(label))
            except Exception:
                pass
        try:
            self.query_one("#btn-next-dep", Button).remove_class("dep-ready")
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Advance the workflow when Next is clicked.

        Args:
            event (Button.Pressed): The button press event.
        """
        if event.button.id == "btn-next-dep":
            self.post_message(StepCompleted(self._step_index))


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
