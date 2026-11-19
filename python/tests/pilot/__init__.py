# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Live Textual pilot tests: drive the UI sitting in front of the app.

Unlike the unit tests (which drive the business logic with the UI mocked
away), pilot tests mount a real screen in a bare Textual app and interact
with it through a live pilot — rendering, events, focus, and compose
structure are all exercised. See .bob/plans/2026-11-15-tui-pilot-test-plan.md.
"""
