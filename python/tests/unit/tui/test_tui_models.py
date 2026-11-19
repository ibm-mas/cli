# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for the TUI workflow model types (tui/models.py).

All tests follow the RED-GREEN-REFACTOR TDD cycle.
"""

from mas.cli.tui.models import (
    WorkflowDefinition,
    WorkflowField,
    WorkflowStep,
    WorkflowSummaryItem,
)


def test_workflow_field_minimal_construction():
    """Test WorkflowField can be constructed with required fields only.

    GIVEN a field id, label, and type
    WHEN WorkflowField is constructed with only required args
    THEN no exception is raised and attributes are stored correctly.
    """
    field = WorkflowField(id="server_url", label="Server URL", type="string")

    assert field.id == "server_url"
    assert field.label == "Server URL"
    assert field.type == "string"
    assert field.options is None
    assert field.options_loader is None
    assert field.default is None
    assert field.validator is None
    assert field.sensitive is False
    assert field.required is True


def test_workflow_field_supports_multi_select_type():
    """Test WorkflowField accepts the multi_select FieldType.

    GIVEN a field with type="multi_select" and an options list
    WHEN WorkflowField is constructed
    THEN the type is stored correctly.
    """
    field = WorkflowField(
        id="components",
        label="Components",
        type="multi_select",
        options=["base", "health", "predict"],
    )

    assert field.type == "multi_select"
    assert field.options == ["base", "health", "predict"]


def test_workflow_field_supports_dynamic_select_type():
    """Test WorkflowField accepts the dynamic_select type and stores options_loader.

    GIVEN a field with type="dynamic_select" and an options_loader callable
    WHEN WorkflowField is constructed
    THEN the options_loader is stored and callable.
    """
    loader = lambda p: ["class-a", "class-b"]  # noqa: E731

    field = WorkflowField(
        id="storage_class",
        label="Storage Class",
        type="dynamic_select",
        options_loader=loader,
    )

    assert field.type == "dynamic_select"
    assert field.options is None
    assert callable(field.options_loader)
    assert field.options_loader({}) == ["class-a", "class-b"]


def test_workflow_step_condition_receives_params_dict():
    """Test that a WorkflowStep condition callable receives the params dict.

    GIVEN a step with condition=lambda p: p.get("x") == "y"
    WHEN condition is called with {"x": "y"}
    THEN it returns True; when called with {"x": "z"} returns False.
    """
    step = WorkflowStep(
        id="optional-step",
        heading="Optional Step",
        condition=lambda p: p.get("x") == "y",
    )

    assert step.condition({"x": "y"}) is True
    assert step.condition({"x": "z"}) is False
    assert step.condition({}) is False


def test_workflow_summary_item_construction():
    """Test WorkflowSummaryItem stores label, param, and sensitive flag.

    GIVEN label and param string values
    WHEN WorkflowSummaryItem is constructed
    THEN both attributes are stored and sensitive defaults to False.
    """
    item = WorkflowSummaryItem(label="Catalog Version", param="mas_catalog_version")

    assert item.label == "Catalog Version"
    assert item.param == "mas_catalog_version"
    assert item.sensitive is False


def test_workflow_summary_item_sensitive_flag():
    """Test WorkflowSummaryItem sensitive flag can be set to True.

    GIVEN a summary item for a password field
    WHEN constructed with sensitive=True
    THEN sensitive attribute is True.
    """
    item = WorkflowSummaryItem(label="Token", param="login_token", sensitive=True)

    assert item.sensitive is True


def test_workflow_definition_is_list():
    """Test WorkflowDefinition is accepted as a plain list of WorkflowStep objects.

    GIVEN a list of WorkflowStep instances
    WHEN assigned to a WorkflowDefinition variable
    THEN it behaves as a standard list.
    """
    steps = [
        WorkflowStep(id="step-one", heading="Step One"),
        WorkflowStep(id="step-two", heading="Step Two"),
    ]

    definition: WorkflowDefinition = steps

    assert len(definition) == 2
    assert definition[0].id == "step-one"
    assert definition[1].id == "step-two"


def test_workflow_step_defaults():
    """Test WorkflowStep has sensible defaults for optional fields.

    GIVEN only id and heading provided
    WHEN WorkflowStep is constructed
    THEN optional fields default to their specified defaults.
    """
    step = WorkflowStep(id="test", heading="Test Heading")

    assert step.heading_level == "h1"
    assert step.description == []
    assert step.fields == []
    assert step.summary == []
    assert step.action is None
    assert step.condition is None
