# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Debug modal overlay showing the current pipeline params dict."""

try:
    from textual.app import ComposeResult
    from textual.containers import VerticalScroll
    from textual.screen import ModalScreen
    from textual.widgets import Button, DataTable, Label
except ModuleNotFoundError as exc:
    raise ImportError("The Textual TUI requires textual to be installed. Install it with: pip install mas-cli[tui]") from exc


class ParamsOverlay(ModalScreen):
    """Modal screen displaying all current app.params key/value pairs.

    Accessible at any point during a workflow via the ``p`` key binding on
    ``TextualShell``.  Dismisses with Escape or the Close button, leaving the
    underlying workflow completely unchanged.

    Attributes:
        _params: Snapshot of the params dict at the time the overlay is opened.
    """

    BINDINGS = [("escape", "dismiss", "Close")]

    def __init__(self, params: dict) -> None:
        """Initialise the params overlay.

        Args:
            params (dict): The current app.params dict to display.
        """
        super().__init__()
        self._params = dict(params)

    def compose(self) -> ComposeResult:
        """Build the overlay widget tree.

        Yields:
            A centred dialog with a heading, DataTable of params, and Close button.
        """
        with VerticalScroll(id="params-dialog"):
            yield Label("Pipeline Parameters", id="params-heading")
            yield DataTable(id="params-table")
            yield Button("Close", id="btn-params-close", variant="default")

    def on_mount(self) -> None:
        """Populate the DataTable with sorted param key/value pairs."""
        table = self.query_one("#params-table", DataTable)
        table.add_columns("Parameter", "Value")
        for key in sorted(self._params.keys()):
            value = str(self._params[key]) if self._params[key] is not None else ""
            table.add_row(key, value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Dismiss the overlay when Close is clicked.

        Args:
            event (Button.Pressed): The button press event.
        """
        if event.button.id == "btn-params-close":
            self.dismiss()
