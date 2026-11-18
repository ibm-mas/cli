# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Custom Textual theme for the MAS CLI TUI (phase 3.4 of the visual polish plan).

This module is the single place where the TUI's colour palette is chosen:
an IBM Carbon-derived dark theme, registered as ``mas`` and selected by
``TextualShell.__init__`` (a two-line hook — see the rollback note below).

The palette uses IBM Carbon's dark-theme colour tokens.  Every semantic
colour (success / warning / error) is specified explicitly: Textual
derives unspecified theme colours from ``primary``, which would turn
state colours blue and make them indistinguishable.

Rollback note: this module plus its registration in ``TextualShell`` is
the entire custom-theme change.  Reverting the phase 3.4 commit (new
files ``tui/theme.py`` / ``tests/unit/tui/test_tui_theme.py``, plus the
import and two registration lines in ``shell.py``) restores the default
Textual theme with no other behaviour change — the stylesheet only ever
references theme *variables* (``$surface``, ``$primary-darken-3``, …),
never literal colours.
"""

from textual.theme import Theme

MAS_THEME = Theme(
    name="mas",
    # IBM Blue 60 — brand primary (buttons, focus, selection).
    primary="#0F62FE",
    # IBM Blue 40 — secondary widgets and the accent used for links, the
    # active sidebar step, and the command panel text.  Staying in the
    # blue family keeps the accent readable on the dark greys below.
    secondary="#78A9FF",
    accent="#78A9FF",
    # Carbon dark greys: Gray 100 background, Gray 90 surface (also the
    # phase 3.3 header/footer chrome tint), Gray 80 panel.
    foreground="#F4F4F4",
    background="#161616",
    surface="#212121",
    panel="#262626",
    # Carbon dark-theme semantic colours — explicitly set so Textual does
    # not derive them from the blue primary.
    success="#42BE65",  # Green 40
    warning="#F1C21B",  # Yellow 30
    error="#FF8389",  # Red 40
    dark=True,
)
