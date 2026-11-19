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
    THEN the step IDs are 'connect-cluster', 'instance-selection',
         'license-acceptance', 'manage-foundation', 'review', 'launch' in
         that order.
    """
    expected_ids = ["connect-cluster", "instance-selection", "license-acceptance", "manage-foundation", "review", "launch"]
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


def test_license_acceptance_step_uses_license_screen_class():
    """Test that the 'license-acceptance' step uses LicenseAcceptanceScreen.

    GIVEN an app instance mock
    WHEN buildUpgradeWorkflow(app) is called
    THEN the 'license-acceptance' step screen_class is LicenseAcceptanceScreen
         and sits between instance-selection and review.
    """
    from mas.cli.tui.screens import LicenseAcceptanceScreen

    definition = buildUpgradeWorkflow(_make_app())
    ids = [step.id for step in definition]
    step = next(s for s in definition if s.id == "license-acceptance")
    assert step.screen_class is LicenseAcceptanceScreen, f"Expected LicenseAcceptanceScreen, got {step.screen_class}"
    assert ids.index("instance-selection") < ids.index("license-acceptance") < ids.index("review")


def test_license_acceptance_step_condition_reads_app_state():
    """Test the license-acceptance step condition calls licenseAcceptancePending.

    GIVEN an app instance mock whose licenseAcceptancePending returns True,
        then False
    WHEN the step condition is evaluated with a params dict
    THEN it returns True (the step is shown) and then False (skipped), and
         the app method was called — so the step is shown only when the
         instance-selection validator resolved a target channel whose
         license has not been accepted yet.
    """
    app = _make_app()
    app.licenseAcceptancePending.return_value = True
    definition = buildUpgradeWorkflow(app)
    step = next(s for s in definition if s.id == "license-acceptance")
    assert step.condition is not None
    assert step.condition({}) is True
    app.licenseAcceptancePending.assert_called()

    app.licenseAcceptancePending.reset_mock()
    app.licenseAcceptancePending.return_value = False
    assert step.condition({}) is False


def test_license_acceptance_step_condition_with_real_scenario_apps():
    """Test the license step condition against real app states.

    GIVEN real UpgradeApp scenario apps: one with an unaccepted licensed
        target channel (9.2.x), one with the license already accepted, and
        one with no resolved target channel yet
    WHEN the license-acceptance step condition is evaluated
    THEN it is True only for the first — the step appears right after
         instance-selection when the license must be accepted, and is
         skipped otherwise.
    """
    from scenarios.upgrade import upgrade_scenario

    app = upgrade_scenario("upgrade-9-1-to-9-2")
    definition = buildUpgradeWorkflow(app)
    step = next(s for s in definition if s.id == "license-acceptance")

    # nextChannel 9.2.x carries a license and licenseAccepted is False
    assert step.condition({}) is True

    app.licenseAccepted = True
    assert step.condition({}) is False

    unresolved = upgrade_scenario("single-instance")
    unresolved_definition = buildUpgradeWorkflow(unresolved)
    unresolved_step = next(s for s in unresolved_definition if s.id == "license-acceptance")
    assert unresolved_step.condition({}) is False


def test_manage_foundation_step_has_validator_and_fields():
    """Test the manage-foundation step collects the Manage Foundation inputs.

    GIVEN an app instance mock
    WHEN buildUpgradeWorkflow(app) is called
    THEN the 'manage-foundation' step has prepareManageFoundation as its
         validator, an optional password field for the entitlement key
         (blank = read the key back from the cluster's ibm-entitlement
         secret), and optional storage class fields (blank = auto-detect).
    """
    app = _make_app()
    definition = buildUpgradeWorkflow(app)
    step = next(s for s in definition if s.id == "manage-foundation")
    assert step.screen_class is None
    assert step.validator is app.prepareManageFoundation
    fields = {field.id: field for field in step.fields}
    assert fields["ibm_entitlement_key"].type == "password"
    assert fields["ibm_entitlement_key"].required is False
    assert fields["ibm_entitlement_key"].sensitive is True
    assert fields["storage_class_rwo"].required is False
    assert fields["storage_class_rwx"].required is False


def test_manage_foundation_step_condition_reads_app_state():
    """Test the manage-foundation step condition calls manageFoundationPending.

    GIVEN an app instance mock whose manageFoundationPending returns True,
        then False
    WHEN the step condition is evaluated with a params dict
    THEN it returns True (the step is shown) and then False (skipped), and
         the app method was called.
    """
    app = _make_app()
    app.manageFoundationPending.return_value = True
    definition = buildUpgradeWorkflow(app)
    step = next(s for s in definition if s.id == "manage-foundation")
    assert step.condition is not None
    assert step.condition({}) is True
    app.manageFoundationPending.assert_called()

    app.manageFoundationPending.reset_mock()
    app.manageFoundationPending.return_value = False
    assert step.condition({}) is False


def test_manage_foundation_step_condition_with_real_scenario_apps():
    """Test the manage-foundation step condition against real app states.

    GIVEN real UpgradeApp scenario apps: one where prepareUpgrade detected
        a Manage Foundation upgrade (before and after its step completed),
        and one where Manage Foundation is not involved
    WHEN the manage-foundation step condition is evaluated
    THEN it is True only before the step has completed — the step appears
         after the license step, and once its inputs are collected it is
         skipped even when navigating back and forward.
    """
    from scenarios.upgrade import upgrade_scenario

    pending = upgrade_scenario("manage-foundation")
    definition = buildUpgradeWorkflow(pending)
    step = next(s for s in definition if s.id == "manage-foundation")
    assert step.condition({}) is True

    configured = upgrade_scenario("manage-foundation-configured")
    configured_definition = buildUpgradeWorkflow(configured)
    configured_step = next(s for s in configured_definition if s.id == "manage-foundation")
    assert configured_step.condition({}) is False

    plain = upgrade_scenario("upgrade-9-1-to-9-2")
    plain_definition = buildUpgradeWorkflow(plain)
    plain_step = next(s for s in plain_definition if s.id == "manage-foundation")
    assert plain_step.condition({}) is False


def test_review_builder_renders_manage_foundation_section():
    """Test buildUpgradeReview renders the Manage Foundation inputs.

    GIVEN a scenario app whose manage-foundation step completed
    WHEN buildUpgradeReview(app) is called
    THEN the Markdown includes a Manage Foundation section with the Db2
        storage classes — and no entitlement key (it is a secret).
    """
    from scenarios.upgrade import upgrade_scenario

    mas_app = upgrade_scenario("manage-foundation-configured")
    review = buildUpgradeReview(mas_app)

    assert "Manage Foundation" in review
    assert "ocs-storagecluster-ceph-rbd" in review
    assert "ocs-storagecluster-cephfs" in review
    # The entitlement key is a secret and must never appear in the review
    assert "entitlement" not in review.lower()


def test_review_builder_omits_manage_foundation_section_when_not_needed():
    """Test buildUpgradeReview omits the Manage Foundation section by default.

    GIVEN a scenario app for a plain 9.1.x to 9.2.x upgrade
    WHEN buildUpgradeReview(app) is called
    THEN the Markdown has no Manage Foundation section.
    """
    from scenarios.upgrade import upgrade_scenario

    mas_app = upgrade_scenario("upgrade-9-1-to-9-2")
    review = buildUpgradeReview(mas_app)

    assert "Manage Foundation" not in review


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
