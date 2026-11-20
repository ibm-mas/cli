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
- :mod:`confirm_upgrades` — conditional step collecting upgrade confirmations.
- :mod:`connect` — OCP cluster connection step (reuse or new credentials).
- :mod:`auto_run` — auto-run with progress: runs work, streams results, reveals Next.
- :mod:`launch` — launch screen: submits the pipeline, streams progress, reveals Done.
- :mod:`license_acceptance` — conditional step collecting license acceptance.
- :mod:`params_overlay` — debug modal showing current pipeline params.
- :mod:`review` — review screen with Confirm / Quit.
- :mod:`size_notice` — blocking notice shown when the terminal is too small.
- :mod:`step` — generic step screen rendering WorkflowField widgets.
"""

from mas.cli.tui.screens.action_overlay import ActionOverlay
from mas.cli.tui.screens.auto_run import AutoRunScreen
from mas.cli.tui.screens.confirm_upgrades import ConfirmUpgradesScreen
from mas.cli.tui.screens.connect import ConnectStepScreen
from mas.cli.tui.screens.launch import LaunchScreen
from mas.cli.tui.screens.license_acceptance import LicenseAcceptanceScreen
from mas.cli.tui.screens.params_overlay import ParamsOverlay
from mas.cli.tui.screens.review import ReviewScreen
from mas.cli.tui.screens.size_notice import TerminalTooSmallScreen
from mas.cli.tui.screens.step import StepScreen

__all__ = [
    "ActionOverlay",
    "AutoRunScreen",
    "ConfirmUpgradesScreen",
    "ConnectStepScreen",
    "LaunchScreen",
    "LicenseAcceptanceScreen",
    "ParamsOverlay",
    "ReviewScreen",
    "StepScreen",
    "TerminalTooSmallScreen",
]
