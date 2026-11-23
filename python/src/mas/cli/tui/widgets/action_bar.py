# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Fixed-height action bar pinned below a screen's scrollable content.

Extracted (phase 3.2 of the visual polish plan) from six hand-composed
copies of the same structure (``Vertical(.action-bar)`` → reserved status
row + ``Horizontal(.action-buttons)``).  The widget owns the status row's
text / error / busy handling; screens pass their Buttons in and keep owning
the button-press logic.  The bar stays inside each screen's panel (not
hoisted to the shell): the fixed height makes per-screen copies
pixel-identical anyway.
"""

from typing import Iterable, Optional

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Label, LoadingIndicator


class ActionBar(Vertical):
    """Action bar with a reserved status row and a row of action buttons.

    The bar carries the shared ``.action-bar`` class (fixed height 6:
    border-top 1 + status row 1 + gap 1 + buttons 3) so the content /
    action-bar boundary sits on the same row on every screen.  The status
    row keeps its height whether it holds guidance text, an error, or
    nothing — ``set_status`` / ``set_error`` / ``clear_status`` only change
    the text and the ``action-status--error`` class, never the geometry.

    Attributes:
        _status_text: Initial text for the reserved status row.
        _status_id: DOM id for the status label (screens and tests query it,
            e.g. ``dep-prompt``, ``connect-status-label``).
        _buttons: The action buttons, in display order.
        _busy: Whether the status row is prefixed by a busy spinner.
    """

    def __init__(
        self,
        status_text: str = "",
        *,
        status_id: Optional[str] = None,
        buttons: Iterable[Button] = (),
        busy: bool = False,
        **kwargs,
    ) -> None:
        """Initialise the action bar.

        Args:
            status_text (str): Initial (muted guidance) text for the
                reserved status row; may be empty.  Defaults to "".
            status_id (str, optional): DOM id for the status label — screens
                and tests query it (e.g. ``dep-prompt``,
                ``validator-error-<step id>``, ``connect-status-label``).
            buttons (Iterable[Button]): The action buttons, in display
                order.  The bar only lays them out; the owning screen keeps
                handling Button.Pressed.  Defaults to ().
            busy (bool): When True the status row is prefixed by a busy
                spinner, hidden until ``show_busy`` is called — used by the
                connect screen while a connection worker runs.  Defaults to
                False.
            **kwargs: Forwarded to Vertical (id, classes, ...).  The shared
                ``.action-bar`` class is always applied.
        """
        # The shared .action-bar class is part of the widget contract (fixed
        # height, border-top) — merged with any caller-provided classes.
        merged = " ".join(c for c in ("action-bar", kwargs.pop("classes", "")) if c)
        super().__init__(classes=merged, **kwargs)
        self._status_text = status_text
        self._status_id = status_id
        self._buttons = list(buttons)
        self._busy = busy

    def compose(self) -> ComposeResult:
        """Build the reserved status row (with spinner on busy bars) and the button row.

        Yields:
            A one-row status label (muted guidance text, or the error via
            ``.action-status--error``), then a Horizontal with the screen's
            buttons.
        """
        if self._busy:
            # The geometry sits on the row (.action-status); the text
            # treatment applies to its inner Label (.action-status > Label).
            with Horizontal(classes="action-status"):
                yield LoadingIndicator(id="action-busy-spinner")
                yield Label(self._status_text, id=self._status_id)
        else:
            yield Label(self._status_text, id=self._status_id, classes="action-status")
        with Horizontal(classes="action-buttons"):
            yield from self._buttons

    def on_mount(self) -> None:
        """Hide the busy spinner until a worker runs (busy bars only)."""
        if self._busy:
            self.query_one("#action-busy-spinner", LoadingIndicator).display = False

    def _status_label(self) -> Label:
        """Return the status row's Label (nested inside the row on busy bars).

        Returns:
            Label: The label carrying the status text.
        """
        if self._busy:
            return self.query_one(".action-status Label", Label)
        return self.query_one(".action-status", Label)

    def set_status(self, text: str) -> None:
        """Show muted guidance text in the reserved status row.

        Any error styling from a previous set_error call is cleared.

        Args:
            text (str): Status text (single line — it is truncated with an
                ellipsis, never wrapped).
        """
        label = self._status_label()
        label.update(text)
        label.remove_class("action-status--error")

    def set_error(self, text: str) -> None:
        """Show an error message in the reserved status row (red, bold).

        Args:
            text (str): Error text (single line — it is truncated with an
                ellipsis, never wrapped).
        """
        label = self._status_label()
        label.update(text)
        label.add_class("action-status--error")

    def clear_status(self) -> None:
        """Clear the status row back to empty, non-error text."""
        label = self._status_label()
        label.update("")
        label.remove_class("action-status--error")

    @property
    def has_error(self) -> bool:
        """Whether the status row currently shows an error."""
        return self._status_label().has_class("action-status--error")

    def show_busy(self, message: Optional[str] = None) -> None:
        """Reveal the busy spinner, optionally showing a status message.

        Args:
            message (str, optional): Status text to show next to the
                spinner; when None the current text is left untouched.
        """
        if self._busy:
            self.query_one("#action-busy-spinner", LoadingIndicator).display = True
        if message is not None:
            self.set_status(message)

    def hide_busy(self) -> None:
        """Hide the busy spinner (busy bars only)."""
        if self._busy:
            self.query_one("#action-busy-spinner", LoadingIndicator).display = False
