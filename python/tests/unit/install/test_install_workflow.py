# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
# *****************************************************************************

"""Tests for the install workflow builder (install/workflow.py).

Covers the step list, field configurations, validators, review screen builder,
command builder, and launch dispatch.
"""

from unittest.mock import MagicMock

from mas.cli.install.workflow import _nonInteractiveCommand, _scriptFilename, buildInstallReview, buildInstallWorkflow
from mas.cli.tui.screens import LaunchScreen, LicenseAcceptanceScreen, ReviewScreen


def _make_app():
    """Return a minimal mock that satisfies buildInstallWorkflow."""
    app = MagicMock()
    app.params = {}
    app.getCatalogOptions.return_value = ["v9-260625-amd64", "v9-260527-amd64"]
    app.catalogReleases = {"v9-260625-amd64": "9.2.x", "v9-260527-amd64": "9.1.x"}
    app.postConnectChecks = MagicMock()
    app.validateCatalogSelection = MagicMock()
    app.licenseAcceptancePending = MagicMock(return_value=False)
    app.validateEntitlementKeyStep = MagicMock()
    app.validateStorageClasses = MagicMock()
    app.validateLicensing = MagicMock()
    app.validateMasInstance = MagicMock()
    app.validateSelectedApps = MagicMock()
    app.buildCommand = MagicMock(return_value="mas install --mas-instance-id inst1 --no-confirm")
    app.getParam = lambda k: app.params.get(k)
    return app


def test_build_install_workflow_returns_definition():
    """Test buildInstallWorkflow returns a non-empty list."""
    definition = buildInstallWorkflow(_make_app())
    assert isinstance(definition, list)
    assert len(definition) > 0


def test_build_install_workflow_step_ids_order():
    """Test buildInstallWorkflow returns steps with expected IDs in exact order."""
    expected_ids = [
        "connect-cluster",
        "choose-catalog",
        "license-acceptance",
        "icr-credentials",
        "storage-classes",
        "licensing-sls",
        "mas-instance",
        "applications",
        "review",
        "launch",
    ]
    app = _make_app()
    definition = buildInstallWorkflow(app)
    step_ids = [step.id for step in definition]
    assert step_ids == expected_ids, f"Expected step ids {expected_ids}, got {step_ids}"


def test_connect_cluster_step_configuration():
    """Test connect-cluster step uses ConnectStepScreen and sets post_connect."""
    app = _make_app()
    definition = buildInstallWorkflow(app)
    step = next(s for s in definition if s.id == "connect-cluster")
    assert step.screen_class is not None
    assert step.screen_class.__name__ == "ConnectStepScreen"
    assert step.screen_kwargs.get("post_connect") is app.postConnectChecks


def test_choose_catalog_step_fields_and_validator():
    """Test choose-catalog step fields and validator."""
    app = _make_app()
    definition = buildInstallWorkflow(app)
    step = next(s for s in definition if s.id == "choose-catalog")
    assert step.validator is app.validateCatalogSelection

    fields = {f.id: f for f in step.fields}
    assert "mas_catalog_version" in fields
    assert fields["mas_catalog_version"].type == "select"
    assert fields["mas_catalog_version"].options == ["v9-260625-amd64", "v9-260527-amd64"]
    assert fields["mas_catalog_version"].required is True

    assert "mas_channel" in fields
    assert fields["mas_channel"].type == "select"
    assert callable(fields["mas_channel"].options)
    assert fields["mas_channel"].options() == ["9.2.x", "9.1.x"]


def test_license_acceptance_step_condition():
    """Test license-acceptance step uses LicenseAcceptanceScreen and conditions on app state."""
    app = _make_app()
    app.licenseAcceptancePending.return_value = True
    definition = buildInstallWorkflow(app)
    step = next(s for s in definition if s.id == "license-acceptance")
    assert step.screen_class is LicenseAcceptanceScreen
    assert step.condition({}) is True

    app.licenseAcceptancePending.return_value = False
    assert step.condition({}) is False


def test_icr_credentials_step_fields():
    """Test icr-credentials step has password-masked entitlement key."""
    app = _make_app()
    definition = buildInstallWorkflow(app)
    step = next(s for s in definition if s.id == "icr-credentials")
    assert step.validator is app.validateEntitlementKeyStep

    field = step.fields[0]
    assert field.id == "ibm_entitlement_key"
    assert field.type == "password"
    assert field.sensitive is True
    assert field.required is True


def test_storage_classes_step_fields():
    """Test storage-classes step fields and validator."""
    app = _make_app()
    definition = buildInstallWorkflow(app)
    step = next(s for s in definition if s.id == "storage-classes")
    assert step.validator is app.validateStorageClasses

    fields = {f.id: f for f in step.fields}
    assert "storage_class_rwo" in fields
    assert "storage_class_rwx" in fields
    assert fields["storage_class_rwo"].required is True
    assert fields["storage_class_rwx"].required is True


def test_licensing_sls_step_fields():
    """Test licensing-sls step fields and validator."""
    app = _make_app()
    definition = buildInstallWorkflow(app)
    step = next(s for s in definition if s.id == "licensing-sls")
    assert step.validator is app.validateLicensing

    fields = {f.id: f for f in step.fields}
    assert "license_file" in fields
    assert fields["license_file"].type == "file"
    assert fields["license_file"].required is False

    assert "dro_contact_email" in fields
    assert "dro_contact_firstname" in fields
    assert "dro_contact_lastname" in fields
    assert fields["dro_contact_email"].required is True


def test_mas_instance_step_fields():
    """Test mas-instance step fields and validator."""
    app = _make_app()
    definition = buildInstallWorkflow(app)
    step = next(s for s in definition if s.id == "mas-instance")
    assert step.validator is app.validateMasInstance

    fields = {f.id: f for f in step.fields}
    assert "mas_instance_id" in fields
    assert "mas_workspace_id" in fields
    assert "mas_workspace_name" in fields
    assert "environment_type" in fields
    assert "mas_admin_mode" in fields
    assert fields["mas_instance_id"].required is True
    assert fields["environment_type"].options == ["production", "non-production"]


def test_applications_step_fields():
    """Test applications step has multi_select field."""
    app = _make_app()
    definition = buildInstallWorkflow(app)
    step = next(s for s in definition if s.id == "applications")
    assert step.validator is app.validateSelectedApps

    field = step.fields[0]
    assert field.id == "selected_apps"
    assert field.type == "multi_select"
    assert "manage" in field.options
    assert "iot" in field.options
    assert "monitor" in field.options


def test_review_step_configuration():
    """Test review step uses ReviewScreen and has summary items."""
    app = _make_app()
    definition = buildInstallWorkflow(app)
    step = next(s for s in definition if s.id == "review")
    assert step.screen_class is ReviewScreen
    assert step.screen_kwargs.get("review_builder") is buildInstallReview
    assert callable(step.screen_kwargs.get("command_builder"))
    assert callable(step.screen_kwargs.get("script_filename_builder"))

    summary_params = [item.param for item in step.summary if item.param]
    assert "mas_instance_id" in summary_params
    assert "mas_catalog_version" in summary_params
    assert "mas_channel" in summary_params
    assert "mas_workspace_id" in summary_params


def test_launch_step_configuration():
    """Test launch step uses LaunchScreen with launchInstall."""
    app = _make_app()
    definition = buildInstallWorkflow(app)
    step = next(s for s in definition if s.id == "launch")
    assert step.screen_class is LaunchScreen
    assert step.screen_kwargs.get("launch_method") == "launchInstall"
    assert callable(step.screen_kwargs.get("command_builder"))


def test_all_conditions_accept_empty_params():
    """Test all conditions accept empty params dict without raising TypeError."""
    app = _make_app()
    definition = buildInstallWorkflow(app)
    for step in definition:
        if step.condition is not None:
            try:
                step.condition({})
            except TypeError as e:
                raise AssertionError(f"Step {step.id} condition failed with empty params: {e}") from e


def test_non_interactive_command_helper():
    """Test _nonInteractiveCommand delegates to app.buildCommand()."""
    app = _make_app()
    cmd = _nonInteractiveCommand(app)
    assert cmd == "mas install --mas-instance-id inst1 --no-confirm"
    app.buildCommand.assert_called_once()


def test_script_filename_helper():
    """Test _scriptFilename generates appropriate script filename."""
    app = _make_app()
    app.params["mas_instance_id"] = "prod1"
    assert _scriptFilename(app) == "mas-install-prod1.sh"

    app.params.clear()
    assert _scriptFilename(app) == "mas-install-instance.sh"


def test_build_install_review_formatting():
    """Test buildInstallReview outputs Markdown with sections and values."""
    app = _make_app()
    app.params = {
        "mas_catalog_version": "v9-260625-amd64",
        "mas_channel": "9.2.x",
        "mas_instance_id": "inst1",
        "mas_workspace_id": "masdev",
        "mas_workspace_name": "MAS Dev Workspace",
        "environment_type": "production",
        "mas_admin_mode": "cluster",
        "storage_class_rwo": "gp3-csi",
        "storage_class_rwx": "efs-csi",
        "sls_action": "install",
        "sls_namespace": "ibm-sls",
        "dro_contact_email": "admin@example.com",
        "mas_app_channel_manage": "9.0.x",
        "mas_app_channel_monitor": "9.0.x",
    }
    app.pipelineStorageClass = "efs-csi"
    app.pipelineStorageAccessMode = "ReadWriteMany"
    app.installManage = True
    app.installMonitor = True

    review = buildInstallReview(app)

    assert "## IBM Maximo Operator Catalog" in review
    assert "v9-260625-amd64" in review
    assert "9.2.x" in review
    assert "## MAS Instance Configuration" in review
    assert "inst1" in review
    assert "masdev" in review
    assert "## Storage Configuration" in review
    assert "gp3-csi" in review
    assert "efs-csi" in review
    assert "## Licensing (SLS & DRO)" in review
    assert "admin@example.com" in review
    assert "## Selected Applications" in review
    assert "Manage (`9.0.x`)" in review
    assert "Monitor (`9.0.x`)" in review


def test_build_install_review_core_platform_only():
    """Test buildInstallReview renders 'Core Platform Only' when no apps selected."""
    app = _make_app()
    app.params = {
        "mas_catalog_version": "v9-260625-amd64",
        "mas_channel": "9.2.x",
        "mas_instance_id": "inst1",
    }
    review = buildInstallReview(app)
    assert "Core Platform Only" in review


def test_install_app_initialization_defaults():
    """Test InstallApp initializes with safe defaults required by TUI mode."""
    from mas.cli.install.app import InstallApp

    app = InstallApp()
    assert app.devMode is False
    assert app.licenseAccepted is False
    assert app.noConfirm is False
    assert app.skipPreCheck is False
    assert app.operationalMode == 1
    assert app.installManage is False
    assert app.installIoT is False
    assert app.installMonitor is False
    assert app.installAssist is False
    assert app.licenseAcceptancePending() is False


def test_install_workflow_with_real_install_app():
    """Test buildInstallWorkflow works with a real InstallApp instance without AttributeError."""
    from mas.cli.install.app import InstallApp

    app = InstallApp()
    app.tuiMode = True
    definition = buildInstallWorkflow(app)
    assert len(definition) == 10

    # Ensure all step conditions evaluate safely on freshly mounted app
    for step in definition:
        if step.condition is not None:
            # Should not raise AttributeError (e.g. devMode or licenseAccepted missing)
            result = step.condition(app.params)
            assert isinstance(result, bool)

    # license-acceptance is skipped initially before channel is selected
    license_step = next(s for s in definition if s.id == "license-acceptance")
    assert license_step.condition(app.params) is False

    # license-acceptance becomes pending once a licensed channel is selected
    app.setParam("mas_channel", "9.2.x")
    assert license_step.condition(app.params) is True

    # license-acceptance is skipped if license was accepted
    app.licenseAccepted = True
    assert license_step.condition(app.params) is False

    # license-acceptance is skipped in devMode
    app.licenseAccepted = False
    app.devMode = True
    assert license_step.condition(app.params) is False
