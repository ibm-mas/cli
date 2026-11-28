# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.php
#
# *****************************************************************************

"""Review screen shown as a workflow step before the launch step."""

from typing import Any, Callable, Optional

try:
    from textual.app import ComposeResult
    from textual.containers import Vertical, VerticalScroll
    from textual.widgets import Button, Label, Markdown, Static
except ModuleNotFoundError as exc:
    raise ImportError("The Textual TUI requires textual to be installed. Install it with: pip install mas-cli[tui]") from exc

from mas.cli.common.commandBuilder import clipboardAvailable, copyToClipboard, writeCommandScript
from mas.cli.tui.messages import StepCompleted
from mas.cli.tui.models import WorkflowStep
from mas.cli.tui.widgets.action_bar import ActionBar


class ReviewScreen(Vertical):
    """Content panel showing a Markdown summary with Confirm and Quit buttons.

    The screen is split into two fixed sections:

    - **Top** (scrollable): the Markdown content summary, optionally followed
      by a bordered panel showing the equivalent non-interactive command.
    - **Bottom** (fixed): a review prompt and the action buttons.

    The summary is produced (in priority order) by:

    1. ``review_builder(mas_app)`` — a custom callable supplied via the step's
       ``screen_kwargs``.  Produces the richest, command-specific Markdown.
    2. ``step.summary`` items — generic label/value table built from WorkflowSummaryItem.

    When ``command_builder`` is supplied (again via ``screen_kwargs``), the
    equivalent non-interactive command is rendered in a bordered panel below
    the summary, with Copy Command and Save Script buttons — so the run can be
    re-created without the prompts before anything is launched.

    The Confirm button posts ``StepCompleted(step_index)`` so the shell advances
    to the launch step.  Quit exits the application.

    Attributes:
        _mas_app: The MAS CLI app providing params and instance attributes.
        _step: The review WorkflowStep.
        _step_index: Zero-based index of this step in the workflow definition.
        _review_builder: Optional ``(mas_app) -> str`` callable for custom layout.
        _command_builder: Optional ``(mas_app) -> str`` callable rendering the
            equivalent non-interactive command.
        _script_filename_builder: Optional ``(mas_app) -> str`` callable for
            the Save Script default filename.
        _command: The most recently rendered command (empty when none).
    """

    def __init__(
        self,
        mas_app: Any,
        step: WorkflowStep,
        step_index: int,
        review_builder: Optional[Callable] = None,
        command_builder: Optional[Callable] = None,
        script_filename_builder: Optional[Callable] = None,
    ) -> None:
        """Initialise the review screen.

        Args:
            mas_app: MAS CLI app instance with params dict and attributes.
            step (WorkflowStep): The review WorkflowStep.
            step_index (int): Zero-based index of this step in the workflow definition.
            review_builder: Optional callable ``(mas_app) -> str`` that returns
                rich command-specific Markdown.  Takes priority over the generic
                summary-item rendering.  Defaults to None.
            command_builder: Optional callable ``(mas_app) -> str`` that renders
                the equivalent non-interactive command for the choices made.
                When None the command panel and its buttons are not shown.
                Defaults to None.
            script_filename_builder: Optional callable ``(mas_app) -> str``
                returning the default filename for the Save Script button.
                When None the Save Script button is not shown.  Defaults to None.
        """
        super().__init__(id=f"step-panel-{step.id}")
        self._mas_app = mas_app
        self._step = step
        self._step_index = step_index
        self._review_builder = review_builder
        self._command_builder = command_builder
        self._script_filename_builder = script_filename_builder
        self._command: str = ""

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
            A scrollable area (``.content-scroll``) with the Markdown
            summary and (when a command builder is supplied) the
            non-interactive command panel, then a fixed action bar
            (``.action-bar``) with the status row and the Copy Command /
            Save Script / Confirm / Quit buttons — the same layout contract
            as every other screen.
        """
        with VerticalScroll(id="review-content", classes="content-scroll"):
            yield Markdown("", id="review-markdown")
            with Vertical(id="review-command-panel", classes="command-panel"):
                yield Label(
                    "Save and re-use this command to repeat the run without the interactive prompts:",
                    classes="command-panel-caption",
                )
                yield Static("", id="review-command-text", classes="command-text")
        yield ActionBar(
            # Short enough to fit the single reserved status row at the
            # pilot-default 80 columns (the .action-status rule truncates
            # with an ellipsis rather than wrapping).
            "Review your choices carefully — mistakes are easier to fix now.",
            status_id="review-prompt",
            id="review-footer",
            buttons=[
                Button("Copy Command", id="btn-copy-command", variant="primary"),
                Button("Save Script", id="btn-save-script", variant="primary"),
                Button("Confirm & Launch", id="btn-confirm", variant="success"),
                Button("Quit", id="btn-quit", variant="error"),
            ],
        )

    def on_mount(self) -> None:
        """Hide the command panel and its buttons when no builder was supplied.

        Also hides Copy Command when no clipboard is usable in this
        environment (containers, headless machines) unless
        ``MAS_CLIPBOARD=osc52`` is set -- the button must not offer an
        action that cannot succeed.
        """
        if self._command_builder is None:
            self.query_one("#review-command-panel", Vertical).display = False
            self.query_one("#btn-copy-command", Button).display = False
            self.query_one("#btn-save-script", Button).display = False
        elif self._script_filename_builder is None:
            self.query_one("#btn-save-script", Button).display = False
        if self._command_builder is not None and not clipboardAvailable():
            self.query_one("#btn-copy-command", Button).display = False

    def start_dynamic_loaders(self) -> None:
        """Refresh the review Markdown and command when the step becomes active.

        Called by TextualShell._activate_step() each time this step is shown,
        so the summary and the generated command always reflect current
        params and app state (e.g. after going back and changing a choice).
        """
        md = self.query_one("#review-markdown", Markdown)
        md.update(self._build_markdown())
        if self._command_builder is not None:
            self._command = self._command_builder(self._mas_app)
            # Trailing newline stripped for display only (it would render as
            # a blank line inside the panel); copy and save-as-script keep
            # the full command text.
            self.query_one("#review-command-text", Static).update(self._command.rstrip("\n"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle Copy Command, Save Script, Confirm and Quit buttons.

        Args:
            event (Button.Pressed): The button press event.
        """
        if event.button.id == "btn-copy-command":
            if copyToClipboard(self._command):
                self.query_one("#review-footer", ActionBar).set_status("Command copied to clipboard")
            else:
                self.query_one("#review-footer", ActionBar).set_status("Clipboard is not available in this environment")
        elif event.button.id == "btn-save-script":
            self._save_script()
        elif event.button.id == "btn-confirm":
            self.post_message(StepCompleted(self._step_index))
        elif event.button.id == "btn-quit":
            self.app.exit(1)

    def _save_script(self) -> None:
        """Write the generated command to a shell script.

        The filename comes from ``script_filename_builder(mas_app)`` (e.g.
        ``mas-update-<catalog-version>.sh``); the file format is owned by
        :func:`mas.cli.common.commandBuilder.writeCommandScript`.  The result
        is reported in the action-bar status row.
        """
        footer = self.query_one("#review-footer", ActionBar)
        filename = self._script_filename_builder(self._mas_app)
        try:
            writeCommandScript(filename, self._command)
        except OSError as e:
            footer.set_error(f"Failed to save command to {filename}: {e}")
        else:
            footer.set_status(f"Command saved to {filename}")
