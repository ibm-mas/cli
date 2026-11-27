# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Shared named app states for MAS CLI tests.

Scenario modules in this package define the cluster/app states a command's
workflow can encounter, as plain data (params + instance attributes). They
are consumed by both the unit tests (``tests/unit/``) and the live pilot
tests (``tests/pilot/``), and are the intended foundation for the manual
testing harness (``dev.py --screen X --scenario Y``) so that automated and
manual testing exercise identical states.
"""
