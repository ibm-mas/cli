# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Shared fixtures and helpers for the tui test package."""

from unittest.mock import MagicMock

from mas.cli.tui.models import WorkflowField, WorkflowStep


def make_app(params: dict = None):
    """Return a minimal mock MAS CLI app with a params dict.

    Args:
        params (dict, optional): Initial params. Defaults to empty dict.

    Returns:
        MagicMock: Mock app instance with .params attribute.
    """
    m = MagicMock()
    m.params = params if params is not None else {}
    return m


def make_step_with_field(field: WorkflowField) -> WorkflowStep:
    """Return a single-step WorkflowDefinition containing one field.

    Args:
        field (WorkflowField): The field to include in the step.

    Returns:
        WorkflowStep: Step containing the field, wrapped in a list.
    """
    return WorkflowStep(id="test-step", heading="Test", fields=[field])
