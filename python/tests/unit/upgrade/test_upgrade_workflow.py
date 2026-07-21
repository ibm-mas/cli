# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for the upgrade command workflow definition.

Covers: buildUpgradeWorkflow return type, step IDs, actions,
instance selection step, and condition callables.
"""

import pytest
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_app():
    """Create a minimal mock UpgradeApp instance.

    Returns:
        MagicMock: Mock with .params dict and _connectFromParams / other methods.
    """
    m = MagicMock()
    m.params = {}
    return m


# ---------------------------------------------------------------------------
# buildUpgradeWorkflow
# ---------------------------------------------------------------------------


def test_build_upgrade_workflow_returns_definition():
    """Test that buildUpgradeWorkflow returns a non-empty list.

    GIVEN a mock UpgradeApp instance
    WHEN buildUpgradeWorkflow is called
    THEN it returns a non-empty list (WorkflowDefinition).
    """
    from mas.cli.upgrade.workflow import buildUpgradeWorkflow

    result = buildUpgradeWorkflow(_make_app())
    assert isinstance(result, list)
    assert len(result) > 0


def test_build_upgrade_workflow_step_ids():
    """Test that the workflow contains the expected step IDs in order.

    GIVEN a mock UpgradeApp instance
    WHEN buildUpgradeWorkflow is called
    THEN the step IDs include 'connect-cluster' and 'instance-selection' in that order.
    """
    from mas.cli.upgrade.workflow import buildUpgradeWorkflow

    steps = buildUpgradeWorkflow(_make_app())
    ids = [s.id for s in steps]
    assert ids[0] == "connect-cluster"
    assert "instance-selection" in ids
    assert ids.index("connect-cluster") < ids.index("instance-selection")


def test_connect_cluster_step_has_post_connect():
    """Test that the connect-cluster step passes post_connect via screen_kwargs.

    GIVEN a mock UpgradeApp instance
    WHEN buildUpgradeWorkflow is called
    THEN the connect-cluster step has a callable post_connect in screen_kwargs
    and no step.action (so no ActionOverlay dialog is shown between screens).
    """
    from mas.cli.upgrade.workflow import buildUpgradeWorkflow

    steps = buildUpgradeWorkflow(_make_app())
    connect_step = next(s for s in steps if s.id == "connect-cluster")
    assert connect_step.action is None, "connect step must not use action (would show ActionOverlay popup)"
    assert callable(connect_step.screen_kwargs.get("post_connect"))


def test_instance_selection_step_has_validator_and_select_field():
    """Test that the instance-selection step has prepareUpgrade as validator and a lazy select field.

    GIVEN a mock UpgradeApp instance
    WHEN buildUpgradeWorkflow is called
    THEN the instance-selection step has a callable validator (prepareUpgrade),
    no custom screen_class, and a mas_instance_id select field with a callable options.
    """
    from mas.cli.upgrade.workflow import buildUpgradeWorkflow

    steps = buildUpgradeWorkflow(_make_app())
    instance_step = next((s for s in steps if s.id == "instance-selection"), None)
    assert instance_step is not None
    assert instance_step.screen_class is None
    assert callable(instance_step.validator), "instance-selection must have prepareUpgrade as validator"
    field = next(f for f in instance_step.fields if f.id == "mas_instance_id")
    assert field.type == "select"
    assert field.options_loader is None
    assert callable(field.options), "options must be a callable resolved at render time"


def test_workflow_has_no_dependency_checks_step():
    """Test that the upgrade workflow does not include a dependency-checks step.

    GIVEN a mock UpgradeApp instance
    WHEN buildUpgradeWorkflow is called
    THEN no step with id 'dependency-checks' is present.
    """
    from mas.cli.upgrade.workflow import buildUpgradeWorkflow

    steps = buildUpgradeWorkflow(_make_app())
    ids = [s.id for s in steps]
    assert "dependency-checks" not in ids


def test_all_conditions_accept_params_dict():
    """Test that all step condition callables accept a dict without raising TypeError.

    GIVEN a mock UpgradeApp instance
    WHEN each step's condition is invoked with an empty dict
    THEN no TypeError is raised.
    """
    from mas.cli.upgrade.workflow import buildUpgradeWorkflow

    steps = buildUpgradeWorkflow(_make_app())
    for step in steps:
        if step.condition is not None:
            try:
                step.condition({})
            except TypeError as exc:
                pytest.fail(f"Step '{step.id}' condition raised TypeError: {exc}")
