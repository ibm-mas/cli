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

from functools import partial
from typing import Any, List

try:
    from textual.app import ComposeResult
    from textual.containers import Horizontal, Vertical, VerticalScroll
    from textual.widgets import Button, Checkbox, Input, Label, Select, Switch
except ModuleNotFoundError as exc:
    raise ImportError("The Textual TUI requires textual to be installed. Install it with: pip install mas-cli[tui]") from exc

from mas.cli.tui.messages import StepCompleted
from mas.cli.tui.models import WorkflowField, WorkflowStep, WorkflowSummaryItem
from mas.cli.tui.widgets.action_bar import ActionBar


class StepScreen(Vertical):
    """Content panel for a single WorkflowStep.

    Splits the panel into a scrollable content area (``.content-scroll``)
    holding the step heading, description paragraphs, an optional read-only
    context panel (from ``step.context``, e.g. the installed catalog on the
    update command's choose-catalog step), and a field widget for each
    WorkflowField, plus a fixed-height action bar (``.action-bar``) pinned
    below it with a reserved status row and the "Next →" button.

    The Next button validates required fields, writes values to app.params,
    optionally runs the step validator, then posts StepCompleted.  While the
    validator runs the action bar shows a busy spinner with the step's
    ``validator_status`` message (cluster calls can take a while — without
    the spinner the disabled button makes the app look hung); a validator
    error replaces it in the reserved status row, so revealing it never
    shifts the layout.

    Fields with an ``options_loader`` (``dynamic_select``) are populated
    asynchronously: ``start_dynamic_loaders`` — called by the shell when
    the step becomes active — runs each loader in a worker thread (the
    loader typically queries the cluster, which cannot run on the UI
    thread), applies the returned options to the Select, and then applies
    the field's ``default`` (which may be a callable, so it can read state
    the loader cached on the app) and refreshes the context rows (which
    may likewise have been populated by the load).  While a load is in
    flight the Next button is disabled and the status row shows progress;
    a failing loader surfaces its error inline like a validator failure.

    Attributes:
        _mas_app: MAS CLI app providing params dict.
        _step: The WorkflowStep being rendered.
        _step_index: Zero-based position in the definition.
        _pending_loads: Number of dynamic option loads still in flight.
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
        self._pending_loads = 0

    def compose(self) -> ComposeResult:
        """Build the step screen content.

        Yields:
            A scrollable area with the heading, description paragraphs,
            optional context panel rows and field widgets, then a fixed
            action bar with the validator error status row (empty until a
            validation fails) and the Next button.
        """
        with VerticalScroll(classes="content-scroll"):
            yield Label(self._step.heading, id=f"heading-{self._step.id}", classes="step-heading")
            for para in self._step.description:
                yield Label(para, classes="description-para")
            if self._step.context:
                with Vertical(classes="step-context"):
                    for item in self._step.context:
                        with Horizontal(classes="context-row"):
                            yield Label(f"{item.label}:", classes="context-label")
                            yield Label(self._context_value(item), classes="context-value")
            for field in self._step.fields:
                yield Label(field.label, classes="field-label")
                yield self._build_field_widget(field)
        yield ActionBar(
            "",
            status_id=f"validator-error-{self._step.id}",
            busy=True,
            buttons=[
                Button("Next →", id=f"btn-next-{self._step.id}", classes="btn-next", variant="primary"),
            ],
        )

    def _action_bar(self) -> ActionBar:
        """Return this screen's action bar.

        Returns:
            ActionBar: The pinned status + buttons bar.
        """
        return self.query_one(ActionBar)

    def _context_value(self, item: WorkflowSummaryItem) -> str:
        """Resolve a context row's display value from the app instance.

        Args:
            item (WorkflowSummaryItem): Context row with ``attr`` or ``param``
                identifying where the value lives.

        Returns:
            str: Display string — the resolved value, "***" for sensitive
            items, or "—" when the value is missing or empty.
        """
        if item.attr:
            raw = getattr(self._mas_app, item.attr, None)
        else:
            raw = self._mas_app.params.get(item.param, None)
        if item.sensitive:
            return "***"
        if raw is None or str(raw).strip() == "":
            return "—"
        return str(raw)

    def start_dynamic_loaders(self) -> None:
        """Populate dynamic_select fields via their ``options_loader``.

        Called by the shell when the step becomes active (and by the pilot
        harness after mount).  Each loader runs in a worker thread — the
        loaders query the cluster, which cannot run on the UI thread — and
        its result is applied to the field's Select on the event loop via
        ``call_from_thread``, followed by the field's ``default`` (which
        may be a callable reading state the loader cached on the app) and
        a refresh of the context rows.  While any load is in flight the
        Next button is disabled and the status row shows progress.
        """
        dynamic_fields = [f for f in self._step.fields if f.options_loader is not None]
        if not dynamic_fields:
            return
        self._pending_loads = len(dynamic_fields)
        try:
            self.query_one(f"#btn-next-{self._step.id}", Button).disabled = True
        except Exception:
            pass
        self._action_bar().show_busy("Looking up available options…")
        for field in dynamic_fields:
            self.run_worker(partial(self._run_dynamic_loader, field), name=f"load-{field.id}", thread=True)

    def _run_dynamic_loader(self, field: WorkflowField) -> None:
        """Run one field's options_loader in a worker thread.

        The whole body is wrapped so a loader failure routes to the inline
        status row rather than crashing the worker (Textual's default
        worker error handling exits the app).

        Args:
            field (WorkflowField): The dynamic_select field to load.
        """
        try:
            options = field.options_loader(self._mas_app.params)
            self.app.call_from_thread(self._on_dynamic_load_success, field, options)
        except Exception as exc:  # noqa: BLE001
            self.app.call_from_thread(self._on_dynamic_load_error, exc)

    def _on_dynamic_load_success(self, field: WorkflowField, options: List[str]) -> None:
        """Apply loaded options (and the field's default) to the Select.

        Args:
            field (WorkflowField): The dynamic_select field that loaded.
            options (list[str]): The option strings returned by the loader.
        """
        fid = f"field-{field.id}"
        try:
            select = self.query_one(f"#{fid}", Select)
            select.set_options([(opt, opt) for opt in options])
            # The default may be a callable so it can read state the loader
            # cached on the app (e.g. the auto-detected storage provider's
            # classes); it is only applied when present in the options.
            default = field.default() if callable(field.default) else field.default
            if default and default in options:
                select.value = default
        except Exception:
            pass
        self._dynamic_load_finished(error=None)

    def _on_dynamic_load_error(self, exc: Exception) -> None:
        """Surface a failed options load like a validator failure.

        Args:
            exc (Exception): The exception raised by the loader.
        """
        self._dynamic_load_finished(error=str(exc))

    def _dynamic_load_finished(self, error: Any = None) -> None:
        """Re-enable Next when the last dynamic load settles.

        Args:
            error (Any, optional): Error text from the failed load, if any.
        """
        self._pending_loads -= 1
        if self._pending_loads > 0:
            return
        try:
            self.query_one(f"#btn-next-{self._step.id}", Button).disabled = False
        except Exception:
            pass
        self._action_bar().hide_busy()
        if error is not None:
            self._action_bar().set_error(error)
        else:
            self._action_bar().clear_status()
        self._refresh_context()

    def _refresh_context(self) -> None:
        """Re-resolve the step's context rows against the app.

        Context values are resolved at compose time, but a dynamic load
        may populate the attributes they read (e.g. the storage provider
        detected while loading options); this updates each context value
        label in place so those rows fill in after the load completes.
        """
        labels = self.query(".step-context .context-value")
        for item, label in zip(self._step.context or [], labels):
            label.update(self._context_value(item))

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
            # The default may be a callable so it can read state populated
            # by an earlier step's validator (e.g. the auto-derived upgrade
            # target); it is applied when present in the options, otherwise
            # the first option is pre-selected
            defaultValue = default() if callable(default) else default
            initial = defaultValue if defaultValue in raw else (options[0][0] if options else Select.NULL)
            # Select.NULL (not the deprecated Select.BLANK alias, which is
            # literally False in this Textual release and fails validation
            # at mount) is the no-selection sentinel.
            return Select(options, id=fid, value=initial, allow_blank=True)

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
                    if sel.value is Select.NULL:
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
                    # A blank optional select writes "" (e.g. "auto-detect")
                    # rather than silently keeping a previously-written
                    # value; required selects cannot be blank (validated).
                    self._mas_app.params[field.id] = "" if sel.value is Select.NULL else str(sel.value)
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

    def _validator_status(self) -> str:
        """Return the busy message shown while the step validator runs.

        Validators are blocking cluster calls (e.g. the upgrade command's
        ``prepareUpgrade``) that can take a while — without the spinner the
        disabled Next button makes the app look hung, the same problem the
        connect screen's "Connecting to cluster…" feedback solves.

        Returns:
            str: The step's ``validator_status`` when set, else a generic
            "Validating…" message.
        """
        return self._step.validator_status or "Validating…"

    def _on_validator_success(self) -> None:
        """Hide the busy spinner and post StepCompleted after a successful validator run."""
        self._action_bar().hide_busy()
        self.post_message(StepCompleted(self._step_index))

    def _on_validator_error(self, exc: Exception) -> None:
        """Display the validator error in the action bar status row and re-enable the Next button.

        Args:
            exc (Exception): The exception raised by the validator.
        """
        self._action_bar().hide_busy()
        self._action_bar().set_error(str(exc))
        btn = self.query_one(f"#btn-next-{self._step.id}", Button)
        btn.disabled = False

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
        self._action_bar().clear_status()
        if self._step.validator is not None:
            btn = self.query_one(f"#btn-next-{self._step.id}", Button)
            btn.disabled = True
            # Busy spinner + message while the (blocking, cluster-calling)
            # validator runs, mirroring the connect screen's feedback
            self._action_bar().show_busy(self._validator_status())
            self.run_worker(self._run_validator, thread=True)
        else:
            self.post_message(StepCompleted(self._step_index))
