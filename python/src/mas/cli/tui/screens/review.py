# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Review screen shown as a workflow step before the launch step."""

from typing import Any, Callable, Optional

try:
    from textual.app import ComposeResult
    from textual.containers import Horizontal, Vertical, VerticalScroll
    from textual.widgets import Button, Label, Markdown
except ModuleNotFoundError as exc:
    raise ImportError("The Textual TUI requires textual to be installed. Install it with: pip install mas-cli[tui]") from exc

from mas.cli.tui.messages import StepCompleted, WorkflowReset
from mas.cli.tui.models import WorkflowStep


class ReviewScreen(Vertical):
    """Content panel showing a Markdown summary with Confirm, Reset, and Quit buttons.

    The screen is split into two fixed sections:

    - **Top** (scrollable): the Markdown content summary.
    - **Bottom** (fixed): a review prompt and the action buttons.

    The summary is produced (in priority order) by:

    1. ``review_builder(mas_app)`` — a custom callable supplied via the step's
       ``screen_kwargs``.  Produces the richest, command-specific Markdown.
    2. ``step.summary`` items — generic label/value table built from WorkflowSummaryItem.

    The Confirm button posts ``StepCompleted(step_index)`` so the shell advances
    to the launch step.  Reset posts ``WorkflowReset`` to restart from step 0.

    Attributes:
        _mas_app: The MAS CLI app providing params and instance attributes.
        _step: The review WorkflowStep.
        _step_index: Zero-based index of this step in the workflow definition.
        _review_builder: Optional ``(mas_app) -> str`` callable for custom layout.
    """

    def __init__(
        self,
        mas_app: Any,
        step: WorkflowStep,
        step_index: int,
        review_builder: Optional[Callable] = None,
    ) -> None:
        """Initialise the review screen.

        Args:
            mas_app: MAS CLI app instance with params dict and attributes.
            step (WorkflowStep): The review WorkflowStep.
            step_index (int): Zero-based index of this step in the workflow definition.
            review_builder: Optional callable ``(mas_app) -> str`` that returns
                rich command-specific Markdown.  Takes priority over the generic
                summary-item rendering.  Defaults to None.
        """
        super().__init__(id=f"step-panel-{step.id}")
        self._mas_app = mas_app
        self._step = step
        self._step_index = step_index
        self._review_builder = review_builder

    def _build_markdown(self) -> str:
        """Build the Markdown review text.

        Priority:
        1. ``_review_builder(mas_app)`` — custom callable, richest output.
        2. ``step.summary`` items — generic label/value table.

        Returns:
            str: Markdown document string.
        """
        if self._review_builder is not None:
            return self._review_builder(self._mas_app)

        lines = [f"## {self._step.heading}\n"]
        for item in self._step.summary:
            if item.attr:
                raw = getattr(self._mas_app, item.attr, "")
            else:
                raw = self._mas_app.params.get(item.param, "")
            value = "***" if item.sensitive else str(raw) if raw is not None else "—"
            if not value:
                value = "—"
            lines.append(f"**{item.label}:** {value}  ")
        lines.append("")
        return "\n".join(lines)

    def compose(self) -> ComposeResult:
        """Build the review screen layout.

        Yields:
            A scrollable top section with the Markdown summary, then a fixed
            bottom section with the review prompt and action buttons.
        """
        with VerticalScroll(id="review-content"):
            yield Markdown("", id="review-markdown")
        with Vertical(id="review-footer"):
            yield Label(
                "Please carefully review your choices above. " "Correcting mistakes now is much easier than after the update has begun.",
                id="review-prompt",
            )
            with Horizontal(id="review-buttons"):
                yield Button("✓ Confirm & Launch", id="btn-confirm", variant="success")
                yield Button("↺ Reset", id="btn-reset", variant="warning")
                yield Button("✕ Quit", id="btn-quit", variant="error")

    def start_dynamic_loaders(self) -> None:
        """Refresh the review Markdown when the step becomes active.

        Called by TextualShell._activate_step() each time this step is shown,
        so the summary always reflects current params and app state.
        """
        md = self.query_one("#review-markdown", Markdown)
        md.update(self._build_markdown())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle Confirm, Reset, and Quit buttons.

        Args:
            event (Button.Pressed): The button press event.
        """
        if event.button.id == "btn-confirm":
            self.post_message(StepCompleted(self._step_index))
        elif event.button.id == "btn-reset":
            self.post_message(WorkflowReset())
        elif event.button.id == "btn-quit":
            self.app.exit(1)
