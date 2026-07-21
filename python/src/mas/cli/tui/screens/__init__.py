# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Screen widgets for the MAS CLI Textual TUI.

Each module in this package provides one focused screen class:

- :mod:`action_overlay` — modal shown while a step action runs in a worker.
- :mod:`connect` — OCP cluster connection step (reuse or new credentials).
- :mod:`auto_run` — auto-run with progress: runs work, streams results, reveals Next.
- :mod:`launch` — launch screen: submits the pipeline, streams progress, reveals Done.
- :mod:`params_overlay` — debug modal showing current pipeline params.
- :mod:`review` — review screen with Confirm / Reset / Quit.
- :mod:`step` — generic step screen rendering WorkflowField widgets.
"""

from mas.cli.tui.screens.action_overlay import ActionOverlay
from mas.cli.tui.screens.auto_run import AutoRunScreen
from mas.cli.tui.screens.connect import ConnectStepScreen
from mas.cli.tui.screens.launch import LaunchScreen
from mas.cli.tui.screens.params_overlay import ParamsOverlay
from mas.cli.tui.screens.review import ReviewScreen
from mas.cli.tui.screens.step import StepScreen

__all__ = [
    "ActionOverlay",
    "AutoRunScreen",
    "ConnectStepScreen",
    "LaunchScreen",
    "ParamsOverlay",
    "ReviewScreen",
    "StepScreen",
]
