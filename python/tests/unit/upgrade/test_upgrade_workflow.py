# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
# *****************************************************************************

"""Tests for the upgrade workflow builder (upgrade/workflow.py).

Covers the step list, the instance-selection field and validator wiring,
the review screen builders, and the launch step's launchUpgrade dispatch.
"""

from unittest.mock import MagicMock

from mas.cli.upgrade.workflow import buildUpgradeReview, buildUpgradeWorkflow


def _make_app():
    """Return a minimal mock that satisfies buildUpgradeWorkflow."""
    app = MagicMock()
    app._connectFromParams = MagicMock()
    return app


def test_build_upgrade_workflow_returns_definition():
    """Test buildUpgradeWorkflow returns a non-empty list.

    GIVEN an app instance mock
    WHEN buildUpgradeWorkflow(app) is called
    THEN the return value is a non-empty list.
    """
    definition = buildUpgradeWorkflow(_make_app())
    assert isinstance(definition, list)
    assert len(definition) > 0


def test_build_upgrade_workflow_step_ids():
    """Test buildUpgradeWorkflow returns steps with expected IDs in order.

    GIVEN an app instance mock
    WHEN buildUpgradeWorkflow(app) is called
    THEN the step IDs are 'connect-cluster', 'instance-selection', 'review',
         'launch' in that order.
    """
    expected_ids = ["connect-cluster", "instance-selection", "review", "launch"]
    definition = buildUpgradeWorkflow(_make_app())
    step_ids = [step.id for step in definition]
    assert step_ids == expected_ids, f"Expected step ids {expected_ids}, got {step_ids}"


def test_connect_cluster_step_uses_screen_class():
    """Test the connect-cluster step uses ConnectStepScreen as its screen_class.

    GIVEN an app instance mock
    WHEN buildUpgradeWorkflow(app) is called
    THEN the 'connect-cluster' step has screen_class named ConnectStepScreen.
    """
    definition = buildUpgradeWorkflow(_make_app())
    step = next(s for s in definition if s.id == "connect-cluster")
    assert step.screen_class is not None
    assert step.screen_class.__name__ == "ConnectStepScreen"


def test_connect_cluster_post_connect_is_fetch_installed_instance_ids():
    """Test the connect-cluster step passes fetchInstalledInstanceIds as post_connect.

    GIVEN an app instance with a fetchInstalledInstanceIds method
    WHEN buildUpgradeWorkflow(app) is called
    THEN the 'connect-cluster' step screen_kwargs['post_connect'] is
         app.fetchInstalledInstanceIds, so the instance list is populated
         inside the connection worker and a cluster with no MAS instances
         surfaces its error on the connect screen.
    """
    app = _make_app()
    definition = buildUpgradeWorkflow(app)
    step = next(s for s in definition if s.id == "connect-cluster")
    assert step.screen_kwargs.get("post_connect") is app.fetchInstalledInstanceIds


def test_instance_selection_step_has_validator_and_select_field():
    """Test the instance-selection step has prepareUpgrade as validator and a lazy select field.

    GIVEN an app instance mock
    WHEN buildUpgradeWorkflow(app) is called
    THEN the 'instance-selection' step has a callable validator
         (prepareUpgrade), no custom screen_class, and a mas_instance_id
         select field whose options is a zero-argument callable resolved at
         widget-build time (after post_connect has populated the list).
    """
    app = _make_app()
    definition = buildUpgradeWorkflow(app)
    step = next(s for s in definition if s.id == "instance-selection")
    assert step.screen_class is None
    assert step.validator is app.prepareUpgrade
    field = next(f for f in step.fields if f.id == "mas_instance_id")
    assert field.type == "select"
    assert field.required is True
    assert field.options_loader is None
    assert callable(field.options), "options must be a callable resolved at render time"


def test_instance_selection_options_callable_reads_installed_instances():
    """Test the instance-selection options callable returns the cached instance IDs.

    GIVEN an app instance whose _installedInstanceIds is ['inst1', 'inst2']
    WHEN the mas_instance_id field's options callable is invoked
    THEN it returns the cached list, so the select is populated from
         post_connect state rather than a static list.
    """
    app = _make_app()
    app._installedInstanceIds = ["inst1", "inst2"]
    definition = buildUpgradeWorkflow(app)
    step = next(s for s in definition if s.id == "instance-selection")
    field = next(f for f in step.fields if f.id == "mas_instance_id")
    assert field.options() == ["inst1", "inst2"]


def test_all_conditions_accept_params_dict():
    """Test that every step condition is None or callable with a dict argument.

    GIVEN an app instance mock
    WHEN buildUpgradeWorkflow(app) is called
    THEN every step.condition is either None or callable without raising
         TypeError when called with a plain dict.
    """
    definition = buildUpgradeWorkflow(_make_app())
    for step in definition:
        if step.condition is not None:
            try:
                step.condition({})
            except TypeError as e:
                raise AssertionError(f"Step '{step.id}' condition raised TypeError with empty dict: {e}") from e


def test_review_step_uses_review_screen_class():
    """Test that the 'review' step uses ReviewScreen as its screen_class.

    GIVEN an app instance mock
    WHEN buildUpgradeWorkflow(app) is called
    THEN the 'review' step screen_class is ReviewScreen.
    """
    from mas.cli.tui.screens import ReviewScreen

    definition = buildUpgradeWorkflow(_make_app())
    step = next(s for s in definition if s.id == "review")
    assert step.screen_class is ReviewScreen, f"Expected ReviewScreen, got {step.screen_class}"


def test_review_step_has_summary_items():
    """Test that the 'review' step has summary items for the upgrade settings.

    GIVEN an app instance mock
    WHEN buildUpgradeWorkflow(app) is called
    THEN the 'review' step has a non-empty summary with the instance ID param
         and the channel / storage class attributes, mirroring the classic
         wizard's Review Settings block.
    """
    definition = buildUpgradeWorkflow(_make_app())
    step = next(s for s in definition if s.id == "review")
    assert step.summary, "Expected non-empty summary on review step"
    params = [item.param for item in step.summary if item.param]
    attrs = [item.attr for item in step.summary if item.attr]
    assert "mas_instance_id" in params
    for expected_attr in ["currentChannel", "nextChannel", "pipelineStorageClass", "pipelineStorageAccessMode"]:
        assert expected_attr in attrs, f"Expected '{expected_attr}' in review step summary attrs: {attrs}"


def test_review_step_command_builder_delegates_to_buildCommand():
    """Test the review step renders the non-interactive command via buildCommand.

    GIVEN an app instance mock whose buildCommand returns a sentinel
    WHEN buildUpgradeWorkflow(app) is called and the review step's
        command_builder is invoked with the app
    THEN it returns the app's buildCommand() output, so the TUI review
        screen shows exactly what the classic interactive wizard prints
        (the round-trip-tested upgradeArgBuilderMixin from PR #2713).
    """
    app = _make_app()
    app.buildCommand.return_value = "mas upgrade --no-confirm"
    definition = buildUpgradeWorkflow(app)
    step = next(s for s in definition if s.id == "review")
    command_builder = step.screen_kwargs.get("command_builder")
    assert callable(command_builder), "Expected 'command_builder' in review step screen_kwargs"
    assert command_builder(app) == "mas upgrade --no-confirm"
    app.buildCommand.assert_called_once()


def test_review_step_script_filename_mirrors_interactive_flow():
    """Test the review step's Save Script default filename.

    GIVEN an app instance with mas_instance_id set
    WHEN the review step's script_filename_builder is invoked
    THEN it returns mas-upgrade-<instance-id>.sh, mirroring the filename
        the classic interactive flow offers (the offerCommandScript call
        in UpgradeApp.upgrade()).
    """
    app = _make_app()
    app.params = {"mas_instance_id": "inst1"}
    definition = buildUpgradeWorkflow(app)
    step = next(s for s in definition if s.id == "review")
    filename_builder = step.screen_kwargs.get("script_filename_builder")
    assert callable(filename_builder), "Expected 'script_filename_builder' in review step screen_kwargs"
    assert filename_builder(app) == "mas-upgrade-inst1.sh"


def test_review_builder_renders_channels_and_storage():
    """Test buildUpgradeReview renders the classic review settings as Markdown.

    GIVEN a scenario app in the post-prepareUpgrade state (9.1.x to 9.2.x
        with a resolved pipeline storage class)
    WHEN buildUpgradeReview(app) is called
    THEN the Markdown contains the instance ID, both channels, and the
        pipeline storage class and access mode.
    """
    from scenarios.upgrade import upgrade_scenario

    mas_app = upgrade_scenario("upgrade-9-1-to-9-2")
    review = buildUpgradeReview(mas_app)

    assert "inst1" in review
    assert "9.1.x" in review
    assert "9.2.x" in review
    assert "ocs-storagecluster-cephfs" in review
    assert "ReadWriteMany" in review


def test_review_builder_renders_placeholder_for_missing_values():
    """Test buildUpgradeReview renders placeholders for missing state.

    GIVEN a scenario app whose channels could not be detected and whose
        storage class is unset
    WHEN buildUpgradeReview(app) is called
    THEN the missing values render as em dashes rather than raising.
    """
    from scenarios.upgrade import upgrade_scenario

    mas_app = upgrade_scenario("unknown-channel")
    review = buildUpgradeReview(mas_app)

    assert "Unknown" in review
    assert "—" in review


def test_launch_step_uses_launch_screen_class():
    """Test that the 'launch' step uses LaunchScreen as its screen_class.

    GIVEN an app instance mock
    WHEN buildUpgradeWorkflow(app) is called
    THEN the 'launch' step screen_class is LaunchScreen and is the last step.
    """
    from mas.cli.tui.screens import LaunchScreen

    definition = buildUpgradeWorkflow(_make_app())
    assert definition[-1].id == "launch", f"Expected last step to be 'launch', got {definition[-1].id}"
    assert definition[-1].screen_class is LaunchScreen, f"Expected LaunchScreen, got {definition[-1].screen_class}"


def test_launch_step_dispatches_to_launchUpgrade():
    """Test the launch step submits the pipeline via launchUpgrade.

    GIVEN an app instance mock
    WHEN buildUpgradeWorkflow(app) is called
    THEN the 'launch' step screen_kwargs names 'launchUpgrade' as the
         launch method, so LaunchScreen calls UpgradeApp.launchUpgrade
         (not UpdateApp.launchUpdate) with the progress callbacks.
    """
    definition = buildUpgradeWorkflow(_make_app())
    step = next(s for s in definition if s.id == "launch")
    assert step.screen_kwargs.get("launch_method") == "launchUpgrade"


def test_launch_step_command_builder_delegates_to_buildCommand():
    """Test the launch step re-displays the non-interactive command.

    GIVEN an app instance mock whose buildCommand returns a sentinel
    WHEN the launch step's command_builder is invoked with the app
    THEN it returns the app's buildCommand() output, so the command is
        re-printed after pipeline submission (as the CLI does) rather than
        being lost when the review screen is gone.
    """
    app = _make_app()
    app.buildCommand.return_value = "mas upgrade --no-confirm"
    definition = buildUpgradeWorkflow(app)
    step = next(s for s in definition if s.id == "launch")
    command_builder = step.screen_kwargs.get("command_builder")
    assert callable(command_builder), "Expected 'command_builder' in launch step screen_kwargs"
    assert command_builder(app) == "mas upgrade --no-confirm"


def test_command_builder_renders_real_upgrade_command():
    """Test the wired builder renders a real command from a scenario app.

    GIVEN a real UpgradeApp scenario (tests/scenarios/upgrade.py) in the
        post-prepareUpgrade state
    WHEN the review step's command_builder is invoked
    THEN the output is a mas upgrade command referencing the selected
        instance and the always-required --no-confirm flag, satisfying the
        test_upgrade_arg_builder.py round-trip contract.
    """
    from scenarios.upgrade import upgrade_scenario

    mas_app = upgrade_scenario("upgrade-9-1-to-9-2")
    definition = buildUpgradeWorkflow(mas_app)
    step = next(s for s in definition if s.id == "review")
    command = step.screen_kwargs["command_builder"](mas_app)

    assert command.startswith("mas upgrade \\")
    assert "--mas-instance-id inst1" in command
    assert "--no-confirm" in command
