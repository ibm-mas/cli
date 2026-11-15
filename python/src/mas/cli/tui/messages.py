# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Textual message types used for inter-widget communication in the TUI.

These are deliberately separated from the widget code so any module can
import them without pulling in the full widget tree.
"""

try:
    from textual.message import Message as _TxtMessage
except ModuleNotFoundError as exc:
    raise ImportError("The Textual TUI requires textual to be installed. Install it with: pip install mas-cli[tui]") from exc


class StepCompleted(_TxtMessage):
    """Posted when a step's fields have been confirmed and written to params."""

    def __init__(self, step_index: int) -> None:
        """Initialise StepCompleted message.

        Args:
            step_index (int): Zero-based index of the completed step.
        """
        super().__init__()
        self.step_index = step_index


class WorkflowReset(_TxtMessage):
    """Posted by ReviewScreen when the user clicks Reset — restarts the workflow."""


class ActionComplete(_TxtMessage):
    """Posted by ActionOverlay when the step action completes successfully."""

    def __init__(self, step_index: int) -> None:
        """Initialise ActionComplete message.

        Args:
            step_index (int): Zero-based index of the step whose action completed.
        """
        super().__init__()
        self.step_index = step_index
