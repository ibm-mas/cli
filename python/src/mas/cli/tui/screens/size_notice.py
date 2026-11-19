# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Modal notice shown while the terminal is smaller than the TUI minimum."""

try:
    from textual.app import ComposeResult
    from textual.containers import Vertical
    from textual.screen import ModalScreen
    from textual.widgets import Label
except ModuleNotFoundError as exc:
    raise ImportError("The Textual TUI requires textual to be installed. Install it with: pip install mas-cli[tui]") from exc


class TerminalTooSmallScreen(ModalScreen[None]):
    """Blocking notice shown while the terminal is below the TUI minimum size.

    Pushed by ``TextualShell`` when a resize drops the terminal below
    ``TextualShell.MIN_WIDTH`` / ``MIN_HEIGHT`` and removed once the terminal
    is big enough again.  While shown it blocks interaction with the
    workflow underneath; the app-level ``q`` (quit) binding still works.

    If the terminal recovers while another modal (e.g. the ActionOverlay)
    sits above this notice, ``mark_stale()`` flags it for removal and it
    pops itself when it becomes the top screen again.
    """

    def __init__(self, min_width: int, min_height: int) -> None:
        """Initialise the notice.

        Args:
            min_width (int): Minimum terminal width in cells.
            min_height (int): Minimum terminal height in cells.
        """
        super().__init__()
        self._min_width = min_width
        self._min_height = min_height
        self._stale = False

    def compose(self) -> ComposeResult:
        """Build the notice dialog.

        Yields:
            A bordered dialog with a heading and guidance text.
        """
        with Vertical(id="size-notice-dialog"):
            yield Label("Terminal too small", classes="size-notice-heading")
            yield Label(
                f"Resize the terminal to at least {self._min_width}×{self._min_height} to continue. "
                "Your progress is kept and the workflow resumes where it left off.",
                classes="size-notice-para",
            )

    def mark_stale(self) -> None:
        """Flag the notice for removal once it is the top screen again.

        Called by ``TextualShell`` when the terminal recovers while another
        screen is stacked above this notice.
        """
        self._stale = True

    def _pop_if_stale(self) -> None:
        """Pop this screen when it is stale and on top of the stack."""
        if self._stale and self.app.screen is self:
            self.app.pop_screen()

    def on_screen_resume(self) -> None:
        """Remove the notice when it resurfaces after being marked stale."""
        self._pop_if_stale()
