# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Generic step screen rendering WorkflowField input widgets."""

from typing import Any, List

try:
    from textual.app import ComposeResult
    from textual.containers import VerticalScroll
    from textual.widgets import Button, Checkbox, Input, Label, Select, Switch
except ModuleNotFoundError as exc:
    raise ImportError("The Textual TUI requires textual to be installed. Install it with: pip install mas-cli[tui]") from exc

from mas.cli.tui.messages import StepCompleted
from mas.cli.tui.models import WorkflowField, WorkflowStep


class StepScreen(VerticalScroll):
    """Content panel for a single WorkflowStep.

    Renders the step heading, description paragraphs, and a field widget
    for each WorkflowField.  A "Next →" button at the bottom validates
    required fields, writes values to app.params, optionally runs the step
    validator, then posts StepCompleted.

    Attributes:
        _mas_app: MAS CLI app providing params dict.
        _step: The WorkflowStep being rendered.
        _step_index: Zero-based position in the definition.
    """

    def __init__(self, mas_app: Any, step: WorkflowStep, step_index: int) -> None:
        """Initialise the step screen.

        Args:
            mas_app: MAS CLI app instance.
            step (WorkflowStep): The step to render.
            step_index (int): Zero-based index in the workflow definition.
        """
        super().__init__(id=f"step-panel-{step.id}")
        self._mas_app = mas_app
        self._step = step
        self._step_index = step_index

    def compose(self) -> ComposeResult:
        """Build the step screen content.

        Yields:
            Heading, description paragraphs, field widgets, validator error
            label (hidden initially), and Next button.
        """
        yield Label(self._step.heading, id=f"heading-{self._step.id}")
        for para in self._step.description:
            yield Label(para, classes="description-para")
        for field in self._step.fields:
            yield Label(field.label, classes="field-label")
            yield self._build_field_widget(field)
        yield Label("", id=f"validator-error-{self._step.id}", classes="validator-error")
        yield Button("Next →", id=f"btn-next-{self._step.id}", classes="btn-next", variant="primary")

    def start_dynamic_loaders(self) -> None:
        """No-op — satisfies the interface expected by TextualShell."""

    def _build_field_widget(self, field: WorkflowField):
        """Return the appropriate Textual widget for a WorkflowField.

        Args:
            field (WorkflowField): Field definition.

        Returns:
            Widget: The constructed Textual widget.
        """
        fid = f"field-{field.id}"
        default = field.default or ""

        if field.type == "bool":
            initial = default.lower() in ("true", "1", "yes") if default else False
            return Switch(value=initial, id=fid)

        if field.type in ("select", "dynamic_select"):
            raw = field.options() if callable(field.options) else (field.options or [])
            options = [(opt, opt) for opt in raw]
            return Select(options, id=fid, value=options[0][0] if options else Select.BLANK, allow_blank=True)

        if field.type == "multi_select":
            raw = field.options() if callable(field.options) else (field.options or [])
            return self._make_checkbox_group(fid, raw)

        if field.type == "password":
            return Input(value=default, password=True, id=fid)

        if field.type == "int":
            return Input(value=default, restrict=r"[0-9]*", id=fid, type="integer")

        # string, file, dir — all render as plain Input
        placeholder = {"file": "Path to file…", "dir": "Path to directory…"}.get(field.type, "")
        return Input(value=default, placeholder=placeholder, id=fid)

    def _make_checkbox_group(self, group_id: str, options: List[str]) -> VerticalScroll:
        """Build a VerticalScroll containing one Checkbox per option.

        Args:
            group_id (str): Widget id for the container.
            options (list[str]): Option strings.

        Returns:
            VerticalScroll: Container with one Checkbox per option.
        """
        checkboxes = [Checkbox(opt, id=f"{group_id}-{opt}", classes="multi-select-option") for opt in options]
        return VerticalScroll(*checkboxes, id=group_id, can_focus=False)

    def _validate_required(self) -> bool:
        """Return True when all required fields have non-empty values.

        Returns:
            bool: True if validation passes.
        """
        for field in self._step.fields:
            if not field.required:
                continue
            fid = f"field-{field.id}"
            if field.type == "bool":
                continue  # Switch always has a value
            if field.type == "multi_select":
                checked = [cb for cb in self.query(".multi-select-option") if isinstance(cb, Checkbox) and cb.value]
                if not checked:
                    return False
            elif field.type in ("select", "dynamic_select"):
                try:
                    sel = self.query_one(f"#{fid}", Select)
                    if sel.value is Select.BLANK:
                        return False
                except Exception:
                    return False
            else:
                try:
                    inp = self.query_one(f"#{fid}", Input)
                    if not inp.value.strip():
                        return False
                except Exception:
                    return False
        return True

    def _write_params(self) -> None:
        """Write all field values to app.params.

        bool  → "true" / "false"
        multi_select → comma-joined selected option ids
        all others → str(value)
        """
        for field in self._step.fields:
            fid = f"field-{field.id}"
            if field.type == "bool":
                try:
                    sw = self.query_one(f"#{fid}", Switch)
                    self._mas_app.params[field.id] = "true" if sw.value else "false"
                except Exception:
                    pass

            elif field.type == "multi_select":
                checked_values = []
                opts = field.options() if callable(field.options) else (field.options or [])
                for opt in opts:
                    cb_id = f"#{fid}-{opt}"
                    try:
                        cb = self.query_one(cb_id, Checkbox)
                        if cb.value:
                            checked_values.append(opt)
                    except Exception:
                        pass
                self._mas_app.params[field.id] = ",".join(checked_values)

            elif field.type in ("select", "dynamic_select"):
                try:
                    sel = self.query_one(f"#{fid}", Select)
                    if sel.value is not Select.BLANK:
                        self._mas_app.params[field.id] = str(sel.value)
                except Exception:
                    pass

            else:
                try:
                    inp = self.query_one(f"#{fid}", Input)
                    self._mas_app.params[field.id] = inp.value
                except Exception:
                    pass

    def _run_validator(self) -> None:
        """Run the step validator in a worker thread.

        Called from ``on_button_pressed`` when ``step.validator`` is set.
        On success posts StepCompleted.  On failure shows the error inline
        and re-enables the Next button.  Widget queries are deferred to the
        main thread via ``call_from_thread``.
        """
        try:
            self._step.validator()  # type: ignore[misc]
            self.app.call_from_thread(self._on_validator_success)
        except Exception as exc:  # noqa: BLE001
            self.app.call_from_thread(self._on_validator_error, exc)

    def _on_validator_success(self) -> None:
        """Post StepCompleted after a successful validator run."""
        self.post_message(StepCompleted(self._step_index))

    def _on_validator_error(self, exc: Exception) -> None:
        """Display the validator error inline and re-enable the Next button.

        Args:
            exc (Exception): The exception raised by the validator.
        """
        error_label = self.query_one(f"#validator-error-{self._step.id}", Label)
        error_label.update(str(exc))
        error_label.add_class("validator-error--visible")
        btn = self.query_one(f"#btn-next-{self._step.id}", Button)
        btn.disabled = False

    def reset(self) -> None:
        """Clear any validator error and re-enable Next for a workflow reset.

        Called by TextualShell.on_workflow_reset() so the step is ready for
        a second pass without stale error state.
        """
        try:
            error_label = self.query_one(f"#validator-error-{self._step.id}", Label)
            error_label.update("")
            error_label.remove_class("validator-error--visible")
        except Exception:
            pass
        try:
            btn = self.query_one(f"#btn-next-{self._step.id}", Button)
            btn.disabled = False
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle Next button press.

        Validates required fields, writes params, then either runs the step
        validator (in a worker thread) or posts StepCompleted directly.
        If field validation fails, returns without advancing.

        Args:
            event (Button.Pressed): The button press event.
        """
        if "btn-next" not in (event.button.id or ""):
            return
        if not self._validate_required():
            return
        self._write_params()
        error_label = self.query_one(f"#validator-error-{self._step.id}", Label)
        error_label.update("")
        error_label.remove_class("validator-error--visible")
        if self._step.validator is not None:
            btn = self.query_one(f"#btn-next-{self._step.id}", Button)
            btn.disabled = True
            self.run_worker(self._run_validator, thread=True)
        else:
            self.post_message(StepCompleted(self._step_index))
