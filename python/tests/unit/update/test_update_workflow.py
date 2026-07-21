# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for the update workflow builder (update/workflow.py).

All tests follow the RED-GREEN-REFACTOR TDD cycle.
"""

from unittest.mock import MagicMock

from mas.cli.update.workflow import buildUpdateWorkflow


def _make_app():
    """Return a minimal mock that satisfies buildUpdateWorkflow."""
    app = MagicMock()
    app._connectFromParams = MagicMock()
    return app


def test_build_update_workflow_returns_definition():
    """Test buildUpdateWorkflow returns a non-empty list.

    GIVEN an app instance mock
    WHEN buildUpdateWorkflow(app) is called
    THEN the return value is a non-empty list.
    """
    definition = buildUpdateWorkflow(_make_app())
    assert isinstance(definition, list)
    assert len(definition) > 0


def test_build_update_workflow_step_ids():
    """Test buildUpdateWorkflow returns steps with expected IDs in order.

    GIVEN an app instance mock
    WHEN buildUpdateWorkflow(app) is called
    THEN the step IDs are 'connect-cluster', 'choose-catalog', 'dependency-checks',
         'review', 'launch' in that order.
    """
    expected_ids = ["connect-cluster", "choose-catalog", "dependency-checks", "review", "launch"]
    app = _make_app()
    definition = buildUpdateWorkflow(app)
    step_ids = [step.id for step in definition]
    assert step_ids == expected_ids, f"Expected step ids {expected_ids}, got {step_ids}"


def test_connect_cluster_step_uses_screen_class():
    """Test the connect-cluster step uses ConnectStepScreen as its screen_class.

    GIVEN an app instance mock
    WHEN buildUpdateWorkflow(app) is called
    THEN the 'connect-cluster' step has screen_class named ConnectStepScreen.
    """
    definition = buildUpdateWorkflow(_make_app())
    step = next(s for s in definition if s.id == "connect-cluster")
    assert step.screen_class is not None
    assert step.screen_class.__name__ == "ConnectStepScreen"


def test_connect_cluster_post_connect_is_review_current_catalog():
    """Test the connect-cluster step passes reviewCurrentCatalog as post_connect.

    GIVEN an app instance with reviewCurrentCatalog method
    WHEN buildUpdateWorkflow(app) is called
    THEN the 'connect-cluster' step screen_kwargs['post_connect'] is
         app.reviewCurrentCatalog, so that installedCatalogId is set inside
         the connection worker before validateCatalog() runs on the next step.
    """
    app = _make_app()
    definition = buildUpdateWorkflow(app)
    step = next(s for s in definition if s.id == "connect-cluster")
    assert step.screen_kwargs.get("post_connect") is app.reviewCurrentCatalog


def test_dependency_checks_step_uses_screen_class():
    """Test the dependency-checks step uses AutoRunScreen as its screen_class.

    GIVEN an app instance mock
    WHEN buildUpdateWorkflow(app) is called
    THEN the 'dependency-checks' step has screen_class named AutoRunScreen
         and action is None (AutoRunScreen drives checks internally via runDependencyChecks).
    """
    definition = buildUpdateWorkflow(_make_app())
    step = next(s for s in definition if s.id == "dependency-checks")
    assert step.screen_class is not None
    assert step.screen_class.__name__ == "AutoRunScreen"
    assert step.action is None


def test_choose_catalog_field_is_select_type():
    """Test the choose-catalog step has a mas_catalog_version field of type 'select'.

    GIVEN an app instance mock whose getCatalogOptions returns 3 entries
    WHEN buildUpdateWorkflow(app) is called
    THEN the 'choose-catalog' step has a 'mas_catalog_version' field with
         type='select' and options matching getCatalogOptions() exactly.
    """
    app = _make_app()
    app.getCatalogOptions.return_value = ["v9-260625-amd64", "v9-260527-amd64", "v9-260430-amd64"]
    definition = buildUpdateWorkflow(app)
    step = next(s for s in definition if s.id == "choose-catalog")
    field = next((f for f in step.fields if f.id == "mas_catalog_version"), None)
    assert field is not None, "Expected field 'mas_catalog_version' in choose-catalog step"
    assert field.type == "select"
    assert field.options == ["v9-260625-amd64", "v9-260527-amd64", "v9-260430-amd64"]


def test_dependency_checks_step_has_summary_items():
    """Test the dependency-checks step carries all review summary items.

    GIVEN an app instance mock
    WHEN buildUpdateWorkflow(app) is called
    THEN the 'dependency-checks' step has Tekton params as summary items and
         installedCatalogId as an attr item (not a Tekton param).
    """
    definition = buildUpdateWorkflow(_make_app())
    step = next(s for s in definition if s.id == "dependency-checks")
    params = [item.param for item in step.summary]
    attrs = [item.attr for item in step.summary]
    for expected_param in [
        "mas_catalog_version",
        "db2_namespace",
        "mongodb_namespace",
        "kafka_namespace",
        "cp4d_update",
        "grafana_v5_upgrade",
        "odh_to_rhoai_migration",
    ]:
        assert expected_param in params, f"Expected '{expected_param}' in dependency-checks summary params: {params}"
    assert "installedCatalogId" in attrs, f"Expected 'installedCatalogId' as attr in dependency-checks summary: {attrs}"


def test_all_conditions_accept_params_dict():
    """Test that every step condition is None or callable with a dict argument without TypeError.

    GIVEN an app instance mock
    WHEN buildUpdateWorkflow(app) is called
    THEN every step.condition is either None or callable without raising TypeError
         when called with a plain dict.
    """
    definition = buildUpdateWorkflow(_make_app())
    for step in definition:
        if step.condition is not None:
            try:
                step.condition({})
            except TypeError as e:
                raise AssertionError(f"Step '{step.id}' condition raised TypeError with empty dict: {e}") from e


def test_choose_catalog_step_has_validator():
    """Test the choose-catalog step has a callable validator.

    GIVEN an app instance mock with a checkCatalog method
    WHEN buildUpdateWorkflow(app) is called
    THEN the 'choose-catalog' step validator is app.checkCatalog (raises on
         failure so the TUI can display the error inline without exiting).
    """
    app = _make_app()
    definition = buildUpdateWorkflow(app)
    step = next(s for s in definition if s.id == "choose-catalog")
    assert step.validator is not None
    assert callable(step.validator)
    assert step.validator is app.checkCatalog


def test_build_update_workflow_has_review_step():
    """Test that buildUpdateWorkflow includes a step with id='review'.

    GIVEN an app instance mock
    WHEN buildUpdateWorkflow(app) is called
    THEN a step with id 'review' is present in the definition.
    """
    definition = buildUpdateWorkflow(_make_app())
    step_ids = [step.id for step in definition]
    assert "review" in step_ids, f"Expected 'review' step in workflow, got: {step_ids}"


def test_build_update_workflow_has_launch_step():
    """Test that buildUpdateWorkflow includes a step with id='launch' as the last step.

    GIVEN an app instance mock
    WHEN buildUpdateWorkflow(app) is called
    THEN a step with id 'launch' is present and is the last step.
    """
    definition = buildUpdateWorkflow(_make_app())
    assert definition[-1].id == "launch", f"Expected last step to be 'launch', got: {definition[-1].id}"


def test_review_step_uses_review_screen_class():
    """Test that the 'review' step uses ReviewScreen as its screen_class.

    GIVEN an app instance mock
    WHEN buildUpdateWorkflow(app) is called
    THEN the 'review' step screen_class is ReviewScreen.
    """
    from mas.cli.tui.screens import ReviewScreen

    definition = buildUpdateWorkflow(_make_app())
    step = next(s for s in definition if s.id == "review")
    assert step.screen_class is ReviewScreen, f"Expected ReviewScreen, got: {step.screen_class}"


def test_launch_step_uses_launch_screen_class():
    """Test that the 'launch' step uses LaunchScreen as its screen_class.

    GIVEN an app instance mock
    WHEN buildUpdateWorkflow(app) is called
    THEN the 'launch' step screen_class is LaunchScreen.
    """
    from mas.cli.tui.screens import LaunchScreen

    definition = buildUpdateWorkflow(_make_app())
    step = next(s for s in definition if s.id == "launch")
    assert step.screen_class is LaunchScreen, f"Expected LaunchScreen, got: {step.screen_class}"


def test_build_update_workflow_step_order():
    """Test that buildUpdateWorkflow returns steps in the expected order.

    GIVEN an app instance mock
    WHEN buildUpdateWorkflow(app) is called
    THEN the step IDs are in order: connect-cluster, choose-catalog,
         dependency-checks, review, launch.
    """
    expected_ids = ["connect-cluster", "choose-catalog", "dependency-checks", "review", "launch"]
    definition = buildUpdateWorkflow(_make_app())
    step_ids = [step.id for step in definition]
    assert step_ids == expected_ids, f"Expected step ids {expected_ids}, got {step_ids}"


def test_review_step_has_summary_items():
    """Test that the 'review' step has summary items for the expected parameters.

    GIVEN an app instance mock
    WHEN buildUpdateWorkflow(app) is called
    THEN the 'review' step has a non-empty summary with entries for catalog,
         db2, mongodb, kafka, cp4d, grafana, and odh.
    """
    definition = buildUpdateWorkflow(_make_app())
    step = next(s for s in definition if s.id == "review")
    assert step.summary, "Expected non-empty summary on review step"
    params = [item.param for item in step.summary if item.param]
    attrs = [item.attr for item in step.summary if item.attr]
    for expected_param in [
        "mas_catalog_version",
        "db2_namespace",
        "mongodb_namespace",
        "kafka_namespace",
        "cp4d_update",
        "grafana_v5_upgrade",
        "odh_to_rhoai_migration",
    ]:
        assert expected_param in params, f"Expected '{expected_param}' in review step summary params"
    assert "installedCatalogId" in attrs, "Expected 'installedCatalogId' as attr in review step summary"
