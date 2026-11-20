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
         'confirm-upgrades', 'review', 'launch' in that order.
    """
    expected_ids = ["connect-cluster", "choose-catalog", "dependency-checks", "confirm-upgrades", "review", "launch"]
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


def test_connect_cluster_post_connect_is_post_connect_checks():
    """Test the connect-cluster step passes _postConnectChecks as post_connect.

    GIVEN an app instance with a _postConnectChecks method
    WHEN buildUpdateWorkflow(app) is called
    THEN the 'connect-cluster' step screen_kwargs['post_connect'] is
         app._postConnectChecks, so that installedCatalogId is set and the
         MAS/AI Service instance review runs inside the connection worker
         before validateCatalogSelection() runs on the next step.
    """
    app = _make_app()
    definition = buildUpdateWorkflow(app)
    step = next(s for s in definition if s.id == "connect-cluster")
    assert step.screen_kwargs.get("post_connect") is app._postConnectChecks


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


def test_choose_catalog_step_has_installed_catalog_context():
    """Test the choose-catalog step shows the installed catalog as context.

    GIVEN an app instance mock
    WHEN buildUpdateWorkflow(app) is called
    THEN the 'choose-catalog' step has a context item backed by the
         installedCatalogId attribute, so the step screen can display the
         catalog detected by the connect step's post-connect checks
         (installedCatalogId is populated by then because step panels
         compose lazily, after the connect step completes).
    """
    definition = buildUpdateWorkflow(_make_app())
    step = next(s for s in definition if s.id == "choose-catalog")
    attrs = [item.attr for item in step.context]
    assert "installedCatalogId" in attrs, f"Expected 'installedCatalogId' as attr in choose-catalog context: {attrs}"


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

    GIVEN an app instance mock with a validateCatalogSelection method
    WHEN buildUpdateWorkflow(app) is called
    THEN the 'choose-catalog' step validator is app.validateCatalogSelection
         (checkCatalog + routing-mode pre-flight check; raises on failure so
         the TUI can display the error inline without exiting).
    """
    app = _make_app()
    definition = buildUpdateWorkflow(app)
    step = next(s for s in definition if s.id == "choose-catalog")
    assert step.validator is not None
    assert callable(step.validator)
    assert step.validator is app.validateCatalogSelection


def test_confirm_upgrades_step_uses_confirm_screen_class():
    """Test the confirm-upgrades step uses ConfirmUpgradesScreen as its screen_class.

    GIVEN an app instance mock
    WHEN buildUpdateWorkflow(app) is called
    THEN the 'confirm-upgrades' step has screen_class named ConfirmUpgradesScreen.
    """
    definition = buildUpdateWorkflow(_make_app())
    step = next(s for s in definition if s.id == "confirm-upgrades")
    assert step.screen_class is not None
    assert step.screen_class.__name__ == "ConfirmUpgradesScreen"


def test_confirm_upgrades_step_condition_reads_app_state():
    """Test the confirm-upgrades step condition calls upgradeConfirmationsPending.

    GIVEN an app instance mock whose upgradeConfirmationsPending returns True
    WHEN the step condition is evaluated with a params dict
    THEN it returns True (the step is shown), and the app method was called.
    """
    app = _make_app()
    app.upgradeConfirmationsPending.return_value = True
    definition = buildUpdateWorkflow(app)
    step = next(s for s in definition if s.id == "confirm-upgrades")
    assert step.condition is not None
    assert step.condition({}) is True
    app.upgradeConfirmationsPending.assert_called()

    app.upgradeConfirmationsPending.reset_mock()
    app.upgradeConfirmationsPending.return_value = False
    assert step.condition({}) is False


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
         dependency-checks, confirm-upgrades, review, launch.
    """
    expected_ids = ["connect-cluster", "choose-catalog", "dependency-checks", "confirm-upgrades", "review", "launch"]
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


def test_review_step_command_builder_delegates_to_buildCommand():
    """Test the review step renders the non-interactive command via buildCommand.

    GIVEN an app instance mock whose buildCommand returns a sentinel
    WHEN buildUpdateWorkflow(app) is called and the review step's
        command_builder is invoked with the app
    THEN it returns the app's buildCommand() output, so the TUI review
        screen shows exactly what the classic interactive wizard prints
        (the round-trip-tested updateArgBuilderMixin from PR #2713).
    """
    app = _make_app()
    app.buildCommand.return_value = "mas update --no-confirm"
    definition = buildUpdateWorkflow(app)
    step = next(s for s in definition if s.id == "review")
    command_builder = step.screen_kwargs.get("command_builder")
    assert callable(command_builder), "Expected 'command_builder' in review step screen_kwargs"
    assert command_builder(app) == "mas update --no-confirm"
    app.buildCommand.assert_called_once()


def test_review_step_script_filename_mirrors_interactive_flow():
    """Test the review step's Save Script default filename.

    GIVEN an app instance mock with mas_catalog_version set
    WHEN the review step's script_filename_builder is invoked
    THEN it returns mas-update-<catalog-version>.sh, mirroring the filename
        the classic interactive flow offers (app.py offerCommandScript).
    """
    app = _make_app()
    app.getParam.return_value = "v9-261102-amd64"
    definition = buildUpdateWorkflow(app)
    step = next(s for s in definition if s.id == "review")
    filename_builder = step.screen_kwargs.get("script_filename_builder")
    assert callable(filename_builder), "Expected 'script_filename_builder' in review step screen_kwargs"
    assert filename_builder(app) == "mas-update-v9-261102-amd64.sh"


def test_launch_step_command_builder_delegates_to_buildCommand():
    """Test the launch step re-displays the non-interactive command.

    GIVEN an app instance mock whose buildCommand returns a sentinel
    WHEN the launch step's command_builder is invoked with the app
    THEN it returns the app's buildCommand() output, so the command is
        re-printed after pipeline submission (as the CLI does) rather than
        being lost when the review screen is gone.
    """
    app = _make_app()
    app.buildCommand.return_value = "mas update --no-confirm"
    definition = buildUpdateWorkflow(app)
    step = next(s for s in definition if s.id == "launch")
    command_builder = step.screen_kwargs.get("command_builder")
    assert callable(command_builder), "Expected 'command_builder' in launch step screen_kwargs"
    assert command_builder(app) == "mas update --no-confirm"


def test_command_builder_renders_real_update_command():
    """Test the wired builder renders a real command from a scenario app.

    GIVEN a real UpdateApp scenario (tests/scenarios/update.py) with a
        target catalog version chosen
    WHEN the review step's command_builder is invoked
    THEN the output is a mas update command referencing the chosen catalog
        and the always-required --no-confirm flag.
    """
    from scenarios.update import update_scenario

    mas_app = update_scenario("clean")
    mas_app.setParam("mas_catalog_version", "v9-261102-amd64")
    definition = buildUpdateWorkflow(mas_app)
    step = next(s for s in definition if s.id == "review")
    command = step.screen_kwargs["command_builder"](mas_app)

    assert command.startswith("mas update \\")
    assert "--catalog v9-261102-amd64" in command
    assert "--no-confirm" in command
