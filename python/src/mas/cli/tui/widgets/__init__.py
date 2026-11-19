# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Reusable widgets for the MAS CLI Textual TUI.

Each module in this package provides one focused widget shared by the
workflow screens:

- :mod:`action_bar` — the fixed-height bar pinned below a screen's
  scrollable content (reserved status row + button row).
- :mod:`step_checklist` — a ListView that transitions its items through the
  pending / active / done / error states.
"""

from mas.cli.tui.widgets.action_bar import ActionBar
from mas.cli.tui.widgets.step_checklist import StepChecklist

__all__ = [
    "ActionBar",
    "StepChecklist",
]
