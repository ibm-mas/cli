# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Textual TUI shell for the MAS CLI workflow layer.

This module requires textual to be installed as a dependency.  If textual is
not available, importing this module raises an ImportError with a clear hint.

Public API:
    TextualShell  — full-screen Textual App driving a WorkflowDefinition.
    AutoRunScreen — re-exported for use in workflow builders.
    ConnectStepScreen — re-exported for use in workflow builders.
    serveTuiMode  — entry point called from __main__.py.
"""

from pathlib import Path
from typing import Any, List

try:
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal, VerticalScroll
    from textual.widgets import ContentSwitcher, Footer, Header, Label, ListItem, ListView
except ModuleNotFoundError as exc:
    raise ImportError("The Textual TUI requires textual to be installed. Install it with: pip install mas-cli[tui]") from exc

from mas.cli.tui.messages import ActionComplete, StepCompleted, WorkflowReset
from mas.cli.tui.models import WorkflowDefinition, WorkflowStep
from mas.cli.tui.screens import ActionOverlay, AutoRunScreen, ConnectStepScreen, ParamsOverlay, ReviewScreen, StepScreen

# Re-export screen classes so existing workflow modules can import them from
# this module (e.g. ``from mas.cli.tui.shell import AutoRunScreen``).
__all__ = [
    "AutoRunScreen",
    "ConnectStepScreen",
    "ReviewScreen",
    "TextualShell",
    "serveTuiMode",
]


class TextualShell(App):
    """Full-screen Textual TUI shell for a MAS CLI workflow.

    Renders a two-pane layout: a step-progress sidebar on the left and a
    per-step content area on the right.  Step actions are dispatched to worker
    threads so the event loop remains responsive.

    After run() returns, ``mas_app.params`` is fully populated with all values
    collected during the workflow, identical to what ``CliRenderer`` would produce.

    Attributes:
        _mas_app: The MAS CLI application instance providing params and actions.
        _definition: Ordered list of WorkflowStep objects to present.
        _active_index: Index into _definition of the currently shown step.
        _completed: Set of step ids that have been confirmed.
    """

    ENABLE_COMMAND_PALETTE = False

    CSS_PATH = Path(__file__).parent / "styles" / "app.tcss"

    BINDINGS = [
        ("p", "show_params", "Debug params"),
        ("q", "quit_app", "Quit"),
    ]

    def __init__(
        self,
        mas_app: Any,
        definition: WorkflowDefinition,
        command: str = "",
    ) -> None:
        """Initialise the TUI shell.

        Args:
            mas_app: MAS CLI application instance exposing a params dict.
            definition (WorkflowDefinition): Ordered list of WorkflowStep objects.
            command (str, optional): CLI command name used in the header title.
        """
        super().__init__()
        self._mas_app = mas_app
        self._definition: WorkflowDefinition = definition
        self._active_index: int = 0
        self._completed: set = set()
        version = getattr(mas_app, "version", "")
        cmd = command.capitalize() if command else ""
        self.title = f"MAS {cmd} v{version}" if cmd else f"MAS CLI v{version}"
        self.sub_title = ""

    def compose(self) -> ComposeResult:
        """Build the initial widget tree.

        Yields:
            Header, main horizontal split (sidebar + ContentSwitcher), Footer.
        """
        yield Header()
        with Horizontal(id="main-horizontal"):
            with VerticalScroll(id="sidebar"):
                yield ListView(id="step-list")
            yield ContentSwitcher(id="step-content")
        yield Footer()

    async def on_mount(self) -> None:
        """Populate the sidebar and content area after the app mounts."""
        await self._populate_sidebar()
        await self._populate_content()
        self._activate_step(self._find_first_active_index())

    # ------------------------------------------------------------------
    # Sidebar helpers
    # ------------------------------------------------------------------

    def _is_skipped(self, step: WorkflowStep) -> bool:
        """Return True when the step's condition evaluates to False.

        Args:
            step (WorkflowStep): The step to evaluate.

        Returns:
            bool: True if the step should be skipped.
        """
        if step.condition is None:
            return False
        return not step.condition(self._mas_app.params)

    async def _populate_sidebar(self) -> None:
        """Build the sidebar ListView with one item per workflow step."""
        list_view = self.query_one("#step-list", ListView)
        list_view.can_focus = False
        list_view.can_focus_children = False
        for step in self._definition:
            item = ListItem(Label(f"⬜ {step.heading}"), id=f"sidebar-{step.id}")
            if self._is_skipped(step):
                item.add_class("step-skipped")
            await list_view.append(item)

    async def _populate_content(self) -> None:
        """Mount only the first step panel into ContentSwitcher.

        Remaining panels are mounted lazily by ``_activate_step`` the first
        time each step is shown.  This ensures ``compose()`` is not called on
        later panels before the data they depend on (e.g. connected cluster
        state) is available.
        """
        switcher = self.query_one("#step-content", ContentSwitcher)
        if self._definition:
            first = self._definition[0]
            i = 0
            if first.screen_class is not None:
                panel = first.screen_class(self._mas_app, first, i, **first.screen_kwargs)
            else:
                panel = StepScreen(self._mas_app, first, i)
            await switcher.mount(panel)

    def _make_panel(self, step: WorkflowStep, index: int):
        """Construct the panel widget for a step.

        Args:
            step (WorkflowStep): The step to build a panel for.
            index (int): Zero-based index in the definition.

        Returns:
            Widget: The constructed panel widget.
        """
        if step.screen_class is not None:
            return step.screen_class(self._mas_app, step, index, **step.screen_kwargs)
        return StepScreen(self._mas_app, step, index)

    def _find_first_active_index(self) -> int:
        """Return the index of the first non-skipped step.

        Returns:
            int: Zero-based index; 0 if all steps are skipped.
        """
        for i, step in enumerate(self._definition):
            if not self._is_skipped(step):
                return i
        return 0

    def _activate_step(self, index: int) -> None:
        """Mark step active in sidebar and switch content area to its panel.

        Args:
            index (int): Zero-based index of the step to activate.
        """
        if not self._definition:
            return

        self._active_index = index
        step = self._definition[index]

        for s in self._definition:
            try:
                item = self.query_one(f"#sidebar-{s.id}", ListItem)
                item.remove_class("step-active")
                if s.id in self._completed:
                    item.add_class("step-completed")
                    item.remove_class("step-skipped")
                    item.query_one(Label).update(f"✅ {s.heading}")
                elif self._is_skipped(s):
                    item.add_class("step-skipped")
            except Exception:
                pass

        try:
            active_item = self.query_one(f"#sidebar-{step.id}", ListItem)
            active_item.add_class("step-active")
            active_item.remove_class("step-skipped")
            active_item.query_one(Label).update(f"⏳ {step.heading}")
        except Exception:
            pass

        switcher = self.query_one("#step-content", ContentSwitcher)
        panel_id = f"step-panel-{step.id}"
        if not switcher.query(f"#{panel_id}"):
            self.call_after_refresh(self._mount_and_activate, step, index, panel_id)
            return
        switcher.current = panel_id
        try:
            self.query_one(f"#{panel_id}").start_dynamic_loaders()
        except Exception:
            pass

    async def _mount_and_activate(self, step: WorkflowStep, index: int, panel_id: str) -> None:
        """Mount a step panel lazily then activate it.

        Called as a non-threaded worker from ``_activate_step`` when a panel
        has not yet been mounted.  Mounting here (after ``post_connect`` has
        run) means ``compose()`` sees fully populated app state.

        Args:
            step (WorkflowStep): The step whose panel to mount.
            index (int): Zero-based index of the step.
            panel_id (str): Expected widget id for the panel.
        """
        switcher = self.query_one("#step-content", ContentSwitcher)
        panel = self._make_panel(step, index)
        await switcher.mount(panel)
        switcher.current = panel_id
        try:
            panel.start_dynamic_loaders()
        except Exception:
            pass

    def _find_next_active_index(self, from_index: int) -> int:
        """Return the next non-skipped step after from_index, or -1 if none.

        Args:
            from_index (int): Current step index.

        Returns:
            int: Index of next active step, or -1 if all remaining are skipped.
        """
        for i in range(from_index + 1, len(self._definition)):
            if not self._is_skipped(self._definition[i]):
                return i
        return -1

    def _refresh_sidebar_conditions(self) -> None:
        """Re-evaluate all step conditions and update sidebar CSS classes."""
        for s in self._definition:
            try:
                item = self.query_one(f"#sidebar-{s.id}", ListItem)
                if s.id in self._completed:
                    continue
                if self._is_skipped(s):
                    item.add_class("step-skipped")
                    item.remove_class("step-active")
                else:
                    item.remove_class("step-skipped")
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def on_step_completed(self, event: StepCompleted) -> None:
        """Handle step completion: fire action (if any) or advance.

        Args:
            event (StepCompleted): The completion event with step_index.
        """
        step = self._definition[event.step_index]
        if step.action is not None:
            self.push_screen(ActionOverlay(step.action, event.step_index))
        else:
            self._complete_step(event.step_index)

    def on_action_complete(self, event: ActionComplete) -> None:
        """Handle successful action completion.

        Args:
            event (ActionComplete): The completion event with step_index.
        """
        self._complete_step(event.step_index)

    def _complete_step(self, step_index: int) -> None:
        """Mark step done, refresh conditions, advance to next step.

        Args:
            step_index (int): Zero-based index of the completed step.
        """
        step = self._definition[step_index]
        self._completed.add(step.id)
        self._refresh_sidebar_conditions()
        next_index = self._find_next_active_index(step_index)
        if next_index != -1:
            self._activate_step(next_index)

    def action_show_params(self) -> None:
        """Push the ParamsOverlay to show current pipeline params.

        Bound to the ``p`` key.
        """
        self.push_screen(ParamsOverlay(self._mas_app.params))

    def action_quit_app(self) -> None:
        """Exit the shell without launching the pipeline.

        Bound to the ``q`` key.
        """
        self.exit(1)

    def on_workflow_reset(self, _event: WorkflowReset) -> None:
        """Reset the workflow: clear completed state and return to the first step.

        Args:
            _event (WorkflowReset): The reset event (unused payload).
        """
        self._completed.clear()
        self._mas_app.params.clear()
        self._refresh_sidebar_conditions()
        for s in self._definition:
            try:
                item = self.query_one(f"#sidebar-{s.id}", ListItem)
                item.remove_class("step-active", "step-completed")
                item.query_one(Label).update(f"⬜ {s.heading}")
                if self._is_skipped(s):
                    item.add_class("step-skipped")
            except Exception:
                pass
        switcher = self.query_one("#step-content", ContentSwitcher)
        # Remove all lazily-mounted panels (steps 1+) so they recompose fresh
        # with current app state on next activation.  Reset step 0 in place.
        first_id = f"step-panel-{self._definition[0].id}" if self._definition else None
        for widget in list(switcher.children):
            if first_id and widget.id == first_id:
                if hasattr(widget, "reset"):
                    widget.reset()
            else:
                widget.remove()
        self._activate_step(self._find_first_active_index())


def serveTuiMode(command: str, argv: List[str]) -> None:
    """Launch the Textual TUI for the given CLI command.

    Lazily imports the command's workflow builder and app class, constructs
    the workflow definition, and runs TextualShell to completion.

    Args:
        command (str): CLI command name, e.g. "update" or "upgrade".
        argv (list[str]): Remaining command-line arguments passed to the app.

    Raises:
        ImportError: If textual is not installed.
        ModuleNotFoundError: If no workflow module exists for command.
    """
    import importlib

    workflow_module = importlib.import_module(f"mas.cli.{command}.workflow")
    build_fn_name = f"build{command.capitalize()}Workflow"
    build_fn = getattr(workflow_module, build_fn_name)

    app_module = importlib.import_module(f"mas.cli.{command}.app")
    app_class_name = f"{command.capitalize()}App"
    app_class = getattr(app_module, app_class_name)

    mas_app = app_class()
    definition = build_fn(mas_app)

    shell = TextualShell(mas_app, definition, command=command)
    shell.run()
