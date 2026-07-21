# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Dev-mode entry point for live CSS editing with textual run --dev.

Usage:
    Terminal 1:  .venv/bin/python -m textual console
    Terminal 2:  .venv/bin/python -m textual run --dev mas.cli.tui.dev

Textual's --dev flag hot-reloads DEFAULT_CSS in shell.py on every save.
Change COMMAND below to preview a different workflow (e.g. "upgrade").
"""

import importlib

from mas.cli.tui.shell import TextualShell

COMMAND = "update"

_wf_mod = importlib.import_module(f"mas.cli.{COMMAND}.workflow")
_build_fn = getattr(_wf_mod, f"build{COMMAND.capitalize()}Workflow")
_app_mod = importlib.import_module(f"mas.cli.{COMMAND}.app")
_mas_app = getattr(_app_mod, f"{COMMAND.capitalize()}App")()

app = TextualShell(_mas_app, _build_fn(_mas_app))
