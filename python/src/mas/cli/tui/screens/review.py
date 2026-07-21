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

from typing import Any

try:
    from textual.app import ComposeResult
    from textual.containers import Horizontal, Vertical, VerticalScroll
    from textual.widgets import Button, Label, Markdown
except ModuleNotFoundError as exc:
    raise ImportError("The Textual TUI requires textual to be installed. Install it with: pip install mas-cli[tui]") from exc

from mas.cli.tui.messages import StepCompleted, WorkflowConfirmed, WorkflowReset
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
    3. Full definition fallback (legacy upgrade path via ``_activate_review``).

    When ``step_index`` is >= 0, the Confirm button posts
    ``StepCompleted(step_index)`` so the shell advances to the launch step.
    When ``step_index`` is -1 (legacy path used by upgrade), the Confirm button
    posts ``WorkflowConfirmed`` for backward compatibility.

    Attributes:
        _mas_app: The MAS CLI app providing params and instance attributes.
        _step: The review WorkflowStep (or None for the legacy path).
        _definition: Full workflow definition used by the legacy fallback.
        _step_index: Zero-based index of the review step, or -1 for legacy mode.
        _review_builder: Optional ``(mas_app) -> str`` callable for custom layout.
    """

    def __init__(
        self,
        mas_app: Any,
        step_or_definition: Any = None,
        step_index: int = -1,
        review_builder: Any = None,
    ) -> None:
        """Initialise the review screen.

        Supports two calling conventions:

        - **Step mode** (new): ``ReviewScreen(mas_app, step, step_index)`` —
          used when the review screen is a proper WorkflowStep. ``step_or_definition``
          is a ``WorkflowStep``; the custom ``review_builder`` is used when present,
          otherwise the generic ``step.summary`` table is rendered.
        - **Legacy mode** (upgrade): ``ReviewScreen(mas_app, definition)`` —
          ``step_or_definition`` is a ``WorkflowDefinition`` list.  The generic
          fallback iterates the definition to build the summary table.

        Args:
            mas_app: MAS CLI app instance with params dict and attributes.
            step_or_definition: Either a ``WorkflowStep`` (step mode) or a
                ``WorkflowDefinition`` list (legacy mode).
            step_index (int, optional): Zero-based index of this step. When >= 0
                Confirm posts StepCompleted; when -1 posts WorkflowConfirmed.
                Defaults to -1.
            review_builder: Optional callable ``(mas_app) -> str`` that returns
                rich command-specific Markdown.  Takes priority over the generic
                summary-item rendering.  Defaults to None.
        """
        # Step mode: id follows the standard step-panel-{id} convention so
        # ContentSwitcher can find it. Legacy mode keeps "review-panel" because
        # _show_review() and _activate_review() in shell.py query for that id.
        if isinstance(step_or_definition, WorkflowStep):
            super().__init__(id=f"step-panel-{step_or_definition.id}")
            self._step = step_or_definition
            self._definition = None
        else:
            # Legacy path: step_or_definition is a WorkflowDefinition list (or None).
            super().__init__(id="review-panel")
            self._step = None
            self._definition = step_or_definition
        self._mas_app = mas_app
        self._step_index = step_index
        self._review_builder = review_builder

    def _build_markdown(self) -> str:
        """Build the Markdown review text.

        Priority:
        1. ``_review_builder(mas_app)`` — custom callable, richest output.
        2. ``step.summary`` items — generic label/value table.
        3. Full definition fallback (legacy upgrade path).

        Returns:
            str: Markdown document string.
        """
        if self._review_builder is not None:
            return self._review_builder(self._mas_app)

        if self._step is not None and self._step.summary:
            # Step mode generic fallback: render label/value rows.
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

        # Legacy fallback: iterate the full definition.
        lines = []
        for step in self._definition or []:
            if not step.summary:
                continue
            lines.append(f"## {step.heading}\n")
            for item in step.summary:
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

    def refresh_table(self) -> None:
        """Refresh the Markdown summary with current params / app attribute values.

        Called by TextualShell._activate_review() each time the review screen
        is shown (legacy upgrade path).
        """
        md = self.query_one("#review-markdown", Markdown)
        md.update(self._build_markdown())

    def start_dynamic_loaders(self) -> None:
        """Refresh the review table when the step becomes active.

        Called by TextualShell._activate_step() when this step is shown, so the
        Markdown is always current when the user reaches the review screen.
        """
        self.refresh_table()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle Confirm, Reset, and Quit buttons.

        When step_index >= 0 the Confirm button posts StepCompleted so the
        shell advances normally to the launch step.  When step_index is -1
        (legacy upgrade path) it posts WorkflowConfirmed instead.

        Args:
            event (Button.Pressed): The button press event.
        """
        if event.button.id == "btn-confirm":
            if self._step_index >= 0:
                self.post_message(StepCompleted(self._step_index))
            else:
                self.post_message(WorkflowConfirmed())
        elif event.button.id == "btn-reset":
            self.post_message(WorkflowReset())
        elif event.button.id == "btn-quit":
            self.app.exit(1)
