# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
# *****************************************************************************

"""
Unit tests for UpgradeApp.

Covers the TUI execution path: fetchInstalledInstanceIds (the connect
step's post_connect hook), prepareUpgrade (the instance-selection step
validator), and the launchUpgrade stage helpers.
"""

from unittest.mock import MagicMock, patch

import pytest

from mas.cli.upgrade.app import UpgradeApp

pytestmark = pytest.mark.upgrade


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_app(**attrs) -> UpgradeApp:
    """Build a minimal UpgradeApp instance without touching the CLI arg parser.

    Args:
        **attrs: Instance attributes to override after construction.

    Returns:
        UpgradeApp: App with a mocked dynamic client and TUI-friendly
            defaults (the state serveTuiMode constructs).
    """
    app = UpgradeApp()
    app.tuiMode = True
    app._dynClient = MagicMock()
    # Pin the SNO detection so setDB2DefaultSettings takes a deterministic
    # branch instead of querying the mocked client
    app._isSNO = False
    app.lookupTargetArchitecture = MagicMock()
    for key, value in attrs.items():
        setattr(app, key, value)
    return app


# ---------------------------------------------------------------------------
# fetchInstalledInstanceIds
# ---------------------------------------------------------------------------


def test_fetch_installed_instance_ids_caches_sorted_list():
    """Test that fetchInstalledInstanceIds stores sorted IDs on the instance.

    GIVEN a connected dynamicClient returning two MAS Suite CRs
    WHEN fetchInstalledInstanceIds is called
    THEN _installedInstanceIds is set to a sorted list of instance ID strings.
    """
    app = _make_app()

    suites = [
        {"metadata": {"labels": {"mas.ibm.com/instanceId": "prod"}}},
        {"metadata": {"labels": {"mas.ibm.com/instanceId": "dev"}}},
    ]
    with patch("mas.cli.upgrade.app.listMasInstances", return_value=suites):
        app.fetchInstalledInstanceIds()

    assert app._installedInstanceIds == ["dev", "prod"]


def test_fetch_installed_instance_ids_raises_when_none_found():
    """Test that fetchInstalledInstanceIds raises RuntimeError when no MAS instances exist.

    GIVEN a connected dynamicClient returning an empty list
    WHEN fetchInstalledInstanceIds is called
    THEN RuntimeError is raised with a message about no instances found, so
         the error surfaces on the connect screen (via post_connect) rather
         than leaving the instance-selection step empty.
    """
    app = _make_app()

    with patch("mas.cli.upgrade.app.listMasInstances", return_value=[]):
        with pytest.raises(RuntimeError, match="No MAS instances were found"):
            app.fetchInstalledInstanceIds()


# ---------------------------------------------------------------------------
# prepareUpgrade
# ---------------------------------------------------------------------------


def _patch_cluster(**kwargs):
    """Patch the cluster-query functions prepareUpgrade depends on.

    Defaults describe a healthy 9.1.x instance with Manage installed and a
    resolvable pipeline storage class; individual tests override returns
    via kwargs.
    """
    defaults = {
        "getMasChannel": "9.1.x",
        "getAppsSubscriptionChannel": [{"appId": "manage", "channel": "9.1.x"}],
        "verifyAppInstance": True,
        "getWorkspaceId": None,
        "evaluatePreinstallRBACAccess": False,
        "lookupPipelineStorageClass": ("ocs-storagecluster-cephfs", "ReadWriteMany"),
    }
    defaults.update(kwargs)
    patches = [patch(f"mas.cli.upgrade.app.{name}", return_value=value) for name, value in defaults.items()]
    return patches


def _run_patches(patches):
    """Enter every patch and return the started mock patchers."""
    started = [p.start() for p in patches]
    return started


def test_prepare_upgrade_happy_path_derives_next_channel():
    """Test that prepareUpgrade derives the next channel and storage state.

    GIVEN a 9.1.x instance with all apps on 9.1.x and the license accepted
    WHEN prepareUpgrade runs as the instance-selection validator
    THEN nextChannel is 9.2.x (from upgrade_path), currentChannel and
         effectiveCurrentChannel are 9.1.x, masInstanceId is set, and the
         pipeline storage class is read from the existing config-pvc.
    """
    app = _make_app(licenseAccepted=True)
    app.params["mas_instance_id"] = "inst1"

    patchers = _run_patches(_patch_cluster())
    try:
        app.prepareUpgrade()
    finally:
        for p in patchers:
            p.stop()

    assert app.currentChannel == "9.1.x"
    assert app.nextChannel == "9.2.x"
    assert app.effectiveCurrentChannel == "9.1.x"
    assert app.masInstanceId == "inst1"
    assert app.pipelineStorageClass == "ocs-storagecluster-cephfs"
    assert app.pipelineStorageAccessMode == "ReadWriteMany"
    assert app.noConfirm is True


def test_prepare_upgrade_oldest_app_channel_drives_target():
    """Test that a behind app holds the upgrade target back one hop.

    GIVEN a Core on 9.2.x but Manage still on 9.1.x
    WHEN prepareUpgrade runs
    THEN effectiveCurrentChannel is 9.1.x and nextChannel is 9.2.x (not
         9.3.x-feature), so partial upgrade resumption targets the right hop.
    """
    app = _make_app(licenseAccepted=True)
    app.params["mas_instance_id"] = "inst1"

    patchers = _run_patches(_patch_cluster(getMasChannel="9.2.x", getAppsSubscriptionChannel=[{"appId": "manage", "channel": "9.1.x"}]))
    try:
        app.prepareUpgrade()
    finally:
        for p in patchers:
            p.stop()

    assert app.effectiveCurrentChannel == "9.1.x"
    assert app.nextChannel == "9.2.x"


def test_prepare_upgrade_already_fully_upgraded_raises():
    """Test that a fully upgraded instance raises instead of advancing.

    GIVEN an instance on 9.3.x-feature with all apps on the same channel
    WHEN prepareUpgrade runs
    THEN RuntimeError is raised with a "No action required" message, shown
         inline on the instance-selection step.
    """
    app = _make_app()
    app.params["mas_instance_id"] = "inst1"

    patchers = _run_patches(_patch_cluster(getMasChannel="9.3.x-feature", getAppsSubscriptionChannel=[{"appId": "manage", "channel": "9.3.x-feature"}]))
    try:
        with pytest.raises(RuntimeError, match="No action required"):
            app.prepareUpgrade()
    finally:
        for p in patchers:
            p.stop()


def test_prepare_upgrade_incompatible_apps_raise():
    """Test that apps incompatible with the target channel raise.

    GIVEN a 9.1.x instance with Assist installed (withdrawn in MAS 9.2)
    WHEN prepareUpgrade runs
    THEN RuntimeError is raised listing the compatibility issue, so the
         upgrade is blocked before the review screen.
    """
    app = _make_app(licenseAccepted=True)
    app.params["mas_instance_id"] = "inst1"

    patchers = _run_patches(_patch_cluster(getAppsSubscriptionChannel=[{"appId": "assist", "channel": "9.1.x"}]))
    try:
        with pytest.raises(RuntimeError, match="Cannot upgrade to 9.2.x"):
            app.prepareUpgrade()
    finally:
        for p in patchers:
            p.stop()


def test_prepare_upgrade_app_on_wrong_channel_raises():
    """Test that an app on an incompatible channel for the target raises.

    GIVEN a 9.0.x instance with Manage still on 8.7.x (not compatible with
        the 9.1.x target derived from the oldest channel)
    WHEN prepareUpgrade runs
    THEN RuntimeError is raised naming the app and the channels it must be on.
    """
    app = _make_app(licenseAccepted=True)
    app.params["mas_instance_id"] = "inst1"

    patchers = _run_patches(_patch_cluster(getMasChannel="9.0.x", getAppsSubscriptionChannel=[{"appId": "manage", "channel": "8.7.x"}]))
    try:
        with pytest.raises(RuntimeError, match="manage"):
            app.prepareUpgrade()
    finally:
        for p in patchers:
            p.stop()


def test_prepare_upgrade_license_pending_does_not_block():
    """Test that an unaccepted license does not block the instance-selection validator.

    GIVEN a 9.1.x instance and licenseAccepted False (the TUI default)
    WHEN prepareUpgrade runs
    THEN it completes all remaining checks (RBAC mode detection and the
         pipeline storage class resolution run) and
         licenseAcceptancePending() is True, so the conditional
         license-acceptance step is shown after instance-selection instead
         of the validator dead-ending the workflow.
    """
    app = _make_app()
    app.params["mas_instance_id"] = "inst1"

    patchers = _run_patches(_patch_cluster(evaluatePreinstallRBACAccess=True))
    try:
        app.prepareUpgrade()
    finally:
        for p in patchers:
            p.stop()

    assert app.licenseAcceptancePending() is True
    # The checks after the license point in the classic flow still ran
    assert app.detectedMode == "cluster"
    assert app.applyPreInstallMASRBAC is True
    assert app.pipelineStorageClass == "ocs-storagecluster-cephfs"


def test_license_acceptance_pending_cleared_by_acceptance():
    """Test that licenseAcceptancePending reflects the acceptance state.

    GIVEN an app in the post-prepareUpgrade state for a licensed target
        channel (9.2.x)
    WHEN the license is accepted (as the license-acceptance step does)
    THEN licenseAcceptancePending() returns False, so the step is skipped on
         re-evaluation and going back to instance-selection does not show it
         again.
    """
    app = _make_app()
    app.params["mas_instance_id"] = "inst1"

    patchers = _run_patches(_patch_cluster())
    try:
        app.prepareUpgrade()
    finally:
        for p in patchers:
            p.stop()

    assert app.licenseAcceptancePending() is True
    app.licenseAccepted = True
    assert app.licenseAcceptancePending() is False


def test_prepare_upgrade_unknown_channel_proceeds_with_placeholders():
    """Test that an undetectable channel proceeds with Unknown placeholders.

    GIVEN a cluster where getMasChannel returns None (e.g. upgrade queued
        after install)
    WHEN prepareUpgrade runs
    THEN currentChannel and nextChannel are "Unknown" and no RuntimeError is
         raised (the license and compatibility gates are skipped).
    """
    app = _make_app()
    app.params["mas_instance_id"] = "inst1"

    patchers = _run_patches(_patch_cluster(getMasChannel=None))
    try:
        app.prepareUpgrade()
    finally:
        for p in patchers:
            p.stop()

    assert app.currentChannel == "Unknown"
    assert app.nextChannel == "Unknown"


def test_prepare_upgrade_detects_manage_foundation():
    """Test that a Manage Foundation upgrade is detected, not blocked.

    GIVEN a 9.0.x instance without Manage installed (the 9.0.x to 9.1.x
        upgrade that needs to install Manage Foundation)
    WHEN prepareUpgrade runs
    THEN it completes without raising, isManageFoundation is set and
         manageFoundationPending() is True, so the conditional
         manage-foundation step collects the inputs instead of the
         validator dead-ending the workflow.
    """
    app = _make_app(licenseAccepted=True)
    app.params["mas_instance_id"] = "inst1"

    patchers = _run_patches(_patch_cluster(getMasChannel="9.0.x", verifyAppInstance=False))
    try:
        app.prepareUpgrade()
    finally:
        for p in patchers:
            p.stop()

    assert app.isManageFoundation is True
    assert app.manageFoundationPending() is True
    assert app.nextChannel == "9.1.x"


def test_prepare_upgrade_resets_manage_foundation_for_other_instances():
    """Test that a non-Manage-Foundation upgrade resets the pending state.

    GIVEN an app that previously detected a Manage Foundation upgrade
        (should_install_manage_foundation set)
    WHEN prepareUpgrade re-runs for an instance that does not need Manage
        Foundation (e.g. the user went back and changed the selection)
    THEN isManageFoundation is False, the step is no longer pending, and
         should_install_manage_foundation is reset to "false" for the
         pipeline.
    """
    app = _make_app(licenseAccepted=True)
    app.params["mas_instance_id"] = "inst1"
    app.isManageFoundation = True
    app.setParam("should_install_manage_foundation", "true")

    patchers = _run_patches(_patch_cluster())
    try:
        app.prepareUpgrade()
    finally:
        for p in patchers:
            p.stop()

    assert app.isManageFoundation is False
    assert app.manageFoundationPending() is False
    assert app.getParam("should_install_manage_foundation") == "false"


def test_prepare_manage_foundation_configures_installation():
    """Test prepareManageFoundation sets the Manage Foundation pipeline params.

    GIVEN an app in the post-prepareUpgrade state for a Manage Foundation
        upgrade, with the entitlement key and both storage classes entered
        on the manage-foundation step, and the cluster functions mocked
    WHEN prepareManageFoundation runs as the step validator
    THEN the install flags and Manage Foundation params are set (matching
         the classic wizard's block), the storage classes are validated
         against the cluster, the silent-mode Db2 configuration runs, and
         the step is no longer pending.
    """
    app = _make_app(currentChannel="9.0.x", nextChannel="9.1.x", isManageFoundation=True)
    app.params["mas_instance_id"] = "inst1"
    app.params["ibm_entitlement_key"] = "ent-key"
    app.params["storage_class_rwo"] = "rwo-sc"
    app.params["storage_class_rwx"] = "rwx-sc"
    app.validateEntitlementKey = MagicMock(return_value=True)

    with (
        patch("mas.cli.upgrade.app.getWorkspaceId", return_value="workspace1") as mock_workspace,
        patch("mas.cli.upgrade.app.getStorageClass", return_value=object()) as mock_get_sc,
        patch("mas.cli.upgrade.app.getDefaultStorageClasses") as mock_defaults,
    ):
        app.prepareManageFoundation()

    mock_workspace.assert_called_once_with(app._dynClient, "inst1")
    mock_get_sc.assert_any_call(app._dynClient, "rwo-sc")
    mock_get_sc.assert_any_call(app._dynClient, "rwx-sc")
    mock_defaults.assert_not_called()  # both classes provided — no auto-detection

    assert app.installManage is True
    assert app.installIoT is False
    assert app.manageAppName == "Manage foundation"
    assert app.getParam("should_install_manage_foundation") == "true"
    assert app.getParam("mas_app_channel_manage") == "9.1.x"
    assert app.getParam("mas_workspace_id") == "workspace1"
    assert app.getParam("mas_appws_components") == ""
    assert app.getParam("mas_app_settings_aio_flag") == "false"
    # Silent-mode Db2 configuration: dedicated Db2 Warehouse for Manage
    assert app.getParam("db2_action_manage") == "install"
    assert app.getParam("mas_appws_bindings_jdbc_manage") == "workspace-application"
    assert app.getParam("db2_type") == "db2wh"
    assert app.manageFoundationPending() is False


def test_prepare_manage_foundation_auto_detects_blank_storage_classes():
    """Test blank storage class fields fall back to cluster auto-detection.

    GIVEN an app in the post-prepareUpgrade state for a Manage Foundation
        upgrade with no storage classes entered
    WHEN prepareManageFoundation runs and the cluster has a detectable
        storage provider
    THEN the auto-detected classes are used and no error is raised.
    """
    app = _make_app(currentChannel="9.0.x", nextChannel="9.1.x", isManageFoundation=True)
    app.params["mas_instance_id"] = "inst1"
    app.params["ibm_entitlement_key"] = "ent-key"
    app.validateEntitlementKey = MagicMock(return_value=True)

    defaults = MagicMock()
    defaults.provider = "ocs"
    defaults.rwo = "auto-rwo"
    defaults.rwx = "auto-rwx"
    with (
        patch("mas.cli.upgrade.app.getWorkspaceId", return_value="workspace1"),
        patch("mas.cli.upgrade.app.getDefaultStorageClasses", return_value=defaults) as mock_defaults,
    ):
        app.prepareManageFoundation()

    mock_defaults.assert_called_once()
    assert app.getParam("storage_class_rwo") == "auto-rwo"
    assert app.getParam("storage_class_rwx") == "auto-rwx"


def test_prepare_manage_foundation_invalid_storage_class_raises():
    """Test a storage class that does not exist on the cluster blocks the step.

    GIVEN an app with a storage class entered that is not on the cluster
    WHEN prepareManageFoundation runs
    THEN RuntimeError is raised naming the storage class, shown inline on
         the manage-foundation step.
    """
    app = _make_app(currentChannel="9.0.x", nextChannel="9.1.x", isManageFoundation=True)
    app.params["mas_instance_id"] = "inst1"
    app.params["ibm_entitlement_key"] = "ent-key"
    app.params["storage_class_rwo"] = "missing-sc"
    app.validateEntitlementKey = MagicMock(return_value=True)

    with (
        patch("mas.cli.upgrade.app.getWorkspaceId", return_value="workspace1"),
        patch("mas.cli.upgrade.app.getStorageClass", return_value=None),
    ):
        with pytest.raises(RuntimeError, match="missing-sc"):
            app.prepareManageFoundation()

    # The step is still pending — the failed validation did not configure
    # the Manage Foundation installation
    assert app.manageFoundationPending() is True


def test_prepare_manage_foundation_invalid_entitlement_key_warns_only():
    """Test an entitlement key that fails validation does not block the step.

    GIVEN an app whose entitlement key fails validation against the IBM
        Container Registry (e.g. an air-gapped cluster)
    WHEN prepareManageFoundation runs
    THEN the configuration completes anyway (warn-only, matching the
         classic --no-confirm behaviour) — the key surfaces again at
         pipeline launch if it is genuinely invalid.
    """
    app = _make_app(currentChannel="9.0.x", nextChannel="9.1.x", isManageFoundation=True)
    app.params["mas_instance_id"] = "inst1"
    app.params["ibm_entitlement_key"] = "bad-key"
    app.params["storage_class_rwo"] = "rwo-sc"
    app.params["storage_class_rwx"] = "rwx-sc"
    app.validateEntitlementKey = MagicMock(return_value=False)

    with (
        patch("mas.cli.upgrade.app.getWorkspaceId", return_value="workspace1"),
        patch("mas.cli.upgrade.app.getStorageClass", return_value=object()),
        patch("mas.cli.upgrade.app.getDefaultStorageClasses"),
    ):
        app.prepareManageFoundation()

    assert app.getParam("should_install_manage_foundation") == "true"


# ---------------------------------------------------------------------------
# lookupEntitlementKey / entitlement resolution
# ---------------------------------------------------------------------------


def _make_dockerconfig_secret(password: str = "the-key", registry: str = "cp.icr.io/cp") -> MagicMock:
    """Return a secrets API mock serving an ibm-entitlement secret.

    Args:
        password (str): The entitlement key stored in the dockerconfigjson.
        registry (str): The registry the credentials are stored under.

    Returns:
        MagicMock: A secrets API whose get() returns the secret as a dict.
    """
    import base64
    import json as jsonlib

    dockerconfig = {"auths": {registry: {"username": "cp", "password": password}}}
    encoded = base64.b64encode(jsonlib.dumps(dockerconfig).encode()).decode()
    secretsAPI = MagicMock()
    secretsAPI.get.return_value = {"data": {".dockerconfigjson": encoded}}
    return secretsAPI


def test_lookup_entitlement_key_reads_cluster_secret():
    """Test that lookupEntitlementKey reads the key from ibm-entitlement.

    GIVEN a cluster whose mas-inst1-core namespace has an ibm-entitlement
        secret with cp.icr.io/cp credentials (as the installation writes)
    WHEN lookupEntitlementKey is called
    THEN the cp.icr.io/cp password is returned, so the user is never asked
         to re-enter a key the installation already stored.
    """
    app = _make_app()
    secretsAPI = _make_dockerconfig_secret()
    app._dynClient.resources.get.return_value = secretsAPI

    assert app.lookupEntitlementKey("inst1") == "the-key"
    app._dynClient.resources.get.assert_called_once_with(api_version="v1", kind="Secret")
    secretsAPI.get.assert_called_once_with(name="ibm-entitlement", namespace="mas-inst1-core")


def test_lookup_entitlement_key_accepts_bare_registry_spelling():
    """Test that a cp.icr.io (without /cp) entry is also accepted.

    GIVEN an ibm-entitlement secret whose credentials are stored under the
        bare cp.icr.io registry spelling
    WHEN lookupEntitlementKey is called
    THEN the password is returned.
    """
    app = _make_app()
    app._dynClient.resources.get.return_value = _make_dockerconfig_secret(registry="cp.icr.io")

    assert app.lookupEntitlementKey("inst1") == "the-key"


def test_lookup_entitlement_key_returns_none_when_secret_missing():
    """Test that a missing ibm-entitlement secret returns None.

    GIVEN a cluster with no ibm-entitlement secret in the instance's core
        namespace
    WHEN lookupEntitlementKey is called
    THEN None is returned (no raise) — the caller decides whether to ask
         for the key instead.
    """
    from kubernetes.dynamic.exceptions import ResourceNotFoundError

    app = _make_app()
    app._dynClient.resources.get.return_value = MagicMock(get=MagicMock(side_effect=ResourceNotFoundError("not found")))

    assert app.lookupEntitlementKey("inst1") is None


def test_lookup_entitlement_key_returns_none_without_cp_credentials():
    """Test that an ibm-entitlement secret without cp.icr.io entries yields None.

    GIVEN an ibm-entitlement secret whose dockerconfigjson only carries
        Artifactory credentials
    WHEN lookupEntitlementKey is called
    THEN None is returned.
    """
    app = _make_app()
    app._dynClient.resources.get.return_value = _make_dockerconfig_secret(registry="docker-na-public.artifactory.swg-devops.com/wiotp-docker-local")

    assert app.lookupEntitlementKey("inst1") is None


def test_prepare_manage_foundation_reads_entitlement_from_cluster():
    """Test that a blank entitlement field falls back to the cluster secret.

    GIVEN an app in the post-prepareUpgrade state for a Manage Foundation
        upgrade with no entitlement key entered, whose cluster has an
        ibm-entitlement secret
    WHEN prepareManageFoundation runs
    THEN the key from the cluster secret is stored in the params (ready for
         the launch secrets step) and the configuration completes.
    """
    app = _make_app(currentChannel="9.0.x", nextChannel="9.1.x", isManageFoundation=True)
    app.params["mas_instance_id"] = "inst1"
    app.params["storage_class_rwo"] = "rwo-sc"
    app.params["storage_class_rwx"] = "rwx-sc"
    app.validateEntitlementKey = MagicMock(return_value=True)

    with (
        patch("mas.cli.upgrade.app.getWorkspaceId", return_value="workspace1"),
        patch("mas.cli.upgrade.app.getStorageClass", return_value=object()),
        patch("mas.cli.upgrade.app.getDefaultStorageClasses"),
        patch.object(UpgradeApp, "lookupEntitlementKey", return_value="cluster-key"),
    ):
        app.prepareManageFoundation()

    assert app.getParam("ibm_entitlement_key") == "cluster-key"
    assert app.getParam("should_install_manage_foundation") == "true"


def test_prepare_manage_foundation_entitlement_not_resolvable_raises():
    """Test that a missing entitlement key everywhere blocks with guidance.

    GIVEN an app with no entitlement key entered and no ibm-entitlement
        secret on the cluster
    WHEN prepareManageFoundation runs
    THEN RuntimeError is raised telling the user to enter the key on the
         step, shown inline so the input can be corrected.
    """
    app = _make_app(currentChannel="9.0.x", nextChannel="9.1.x", isManageFoundation=True)
    app.params["mas_instance_id"] = "inst1"

    with patch.object(UpgradeApp, "lookupEntitlementKey", return_value=None):
        with pytest.raises(RuntimeError, match="IBM entitlement key"):
            app.prepareManageFoundation()

    # The step is still pending — the failed validation did not configure
    # the Manage Foundation installation
    assert app.manageFoundationPending() is True


def test_prepare_upgrade_detects_rbac_mode_for_9_2_target():
    """Test that a 9.2.x target defaults to cluster mode and evaluates RBAC.

    GIVEN a 9.1.x instance being upgraded to 9.2.x
    WHEN prepareUpgrade runs
    THEN detectedMode is "cluster" and evaluatePreinstallRBACAccess is
         called with that mode, its result stored for launchUpgrade.
    """
    app = _make_app(licenseAccepted=True)
    app.params["mas_instance_id"] = "inst1"

    patchers = _run_patches(_patch_cluster(evaluatePreinstallRBACAccess=True))
    try:
        app.prepareUpgrade()
    finally:
        for p in patchers:
            p.stop()

    assert app.detectedMode == "cluster"
    assert app.applyPreInstallMASRBAC is True


# ---------------------------------------------------------------------------
# launchUpgrade stage helpers
# ---------------------------------------------------------------------------


def test_validate_openshift_pipelines_success():
    """Test _validateOpenShiftPipelines returns success when operator installs.

    GIVEN an UpgradeApp instance
    WHEN _validateOpenShiftPipelines is called and the operator installs
    THEN it returns (True, success_message).
    """
    app = _make_app()

    with patch("mas.cli.upgrade.app.installOpenShiftPipelines", return_value=True):
        success, detail = app._validateOpenShiftPipelines()

    assert success is True
    assert "installed and ready" in detail.lower()


def test_validate_openshift_pipelines_failure():
    """Test _validateOpenShiftPipelines returns failure when operator fails.

    GIVEN an UpgradeApp instance
    WHEN _validateOpenShiftPipelines is called and installation fails
    THEN it returns (False, failure_message).
    """
    app = _make_app()

    with patch("mas.cli.upgrade.app.installOpenShiftPipelines", return_value=False):
        success, detail = app._validateOpenShiftPipelines()

    assert success is False
    assert "failed" in detail.lower()


def test_prepare_upgrade_namespace_passes_storage_class_and_secrets():
    """Test _prepareUpgradeNamespace prepares the instance pipelines namespace.

    GIVEN an UpgradeApp with the pipeline storage class resolved and params set
    WHEN _prepareUpgradeNamespace is called
    THEN the namespace is created, preparePipelinesNamespace receives the
         instance ID and storage class, and prepareUpgradeSecrets receives
         the entitlement / artifactory params.
    """
    app = _make_app(pipelineStorageClass="ocs-sc", pipelineStorageAccessMode="ReadWriteMany")
    app.params["ibm_entitlement_key"] = "ent-key"

    with (
        patch("mas.cli.upgrade.app.createNamespace") as mock_create,
        patch("mas.cli.upgrade.app.preparePipelinesNamespace") as mock_prepare,
        patch("mas.cli.upgrade.app.prepareUpgradeSecrets") as mock_secrets,
    ):
        success, detail = app._prepareUpgradeNamespace("mas-inst1-pipelines", "inst1")

    mock_create.assert_called_once_with(app._dynClient, "mas-inst1-pipelines")
    mock_prepare.assert_called_once_with(
        dynClient=app._dynClient,
        instanceId="inst1",
        storageClass="ocs-sc",
        accessMode="ReadWriteMany",
    )
    mock_secrets.assert_called_once_with(
        dynClient=app._dynClient,
        namespace="mas-inst1-pipelines",
        ibm_entitlement_key="ent-key",
        artifactory_token="",
        artifactory_username="",
    )
    assert success is True
    assert detail == "mas-inst1-pipelines"


def test_install_tekton_definitions_updates_definitions():
    """Test _installTektonDefinitions updates Tekton definitions.

    GIVEN an UpgradeApp with version and tektonDefsPath set
    WHEN _installTektonDefinitions is called
    THEN Tekton definitions are updated and the version is returned.
    """
    app = _make_app()
    app.version = "1.2.3"
    app.tektonDefsPath = "/path/to/defs"

    with patch("mas.cli.upgrade.app.updateTektonDefinitions") as mock_update:
        success, detail = app._installTektonDefinitions("mas-inst1-pipelines")

    mock_update.assert_called_once_with(app._dynClient, "mas-inst1-pipelines", "/path/to/defs")
    assert success is True
    assert detail == "v1.2.3"


def test_submit_upgrade_pipeline_run_passes_effective_channel():
    """Test _submitUpgradePipelineRun passes the effective current channel.

    GIVEN an app in the post-prepareUpgrade state (9.1.x to 9.2.x)
    WHEN _submitUpgradePipelineRun is called
    THEN launchUpgradePipeline is called with the instance ID, skip flag and
         masChannel=9.1.x, and the pipeline URL is returned as the detail.
    """
    app = _make_app(
        masInstanceId="inst1",
        currentChannel="9.1.x",
        nextChannel="9.2.x",
        effectiveCurrentChannel="9.1.x",
    )

    with patch("mas.cli.upgrade.app.launchUpgradePipeline", return_value="https://example.com/pipelinerun") as mock_launch:
        success, detail = app._submitUpgradePipelineRun()

    mock_launch.assert_called_once_with(app._dynClient, "inst1", False, masChannel="9.1.x", params=app.params)
    assert success is True
    assert detail == "https://example.com/pipelinerun"


def test_submit_upgrade_pipeline_run_retry_passes_previous_channel():
    """Test the retry scenario passes the previous channel to the pipeline.

    GIVEN an app whose next channel equals its current channel (core already
        on 9.0.x, apps still behind)
    WHEN _submitUpgradePipelineRun is called
    THEN masChannel is the channel that precedes the current one (the first
         upgrade_path entry mapping to it, as in the classic launch logic),
         so Ansible upgrades the remaining apps to the current channel.
    """
    app = _make_app(
        masInstanceId="inst1",
        currentChannel="9.0.x",
        nextChannel="9.0.x",
        effectiveCurrentChannel="8.11.x",
    )

    with patch("mas.cli.upgrade.app.launchUpgradePipeline", return_value="https://example.com/pipelinerun") as mock_launch:
        app._submitUpgradePipelineRun()

    assert mock_launch.call_args.kwargs["masChannel"] == "8.11.x"


def test_submit_upgrade_pipeline_run_failure():
    """Test _submitUpgradePipelineRun returns failure when the launch fails.

    GIVEN an app in the post-prepareUpgrade state
    WHEN launchUpgradePipeline returns None
    THEN it returns (False, failure_message).
    """
    app = _make_app(masInstanceId="inst1", currentChannel="9.1.x", nextChannel="9.2.x", effectiveCurrentChannel="9.1.x")

    with patch("mas.cli.upgrade.app.launchUpgradePipeline", return_value=None):
        success, detail = app._submitUpgradePipelineRun()

    assert success is False
    assert "failed" in detail.lower()


# ---------------------------------------------------------------------------
# launchUpgrade orchestration
# ---------------------------------------------------------------------------


def test_launch_upgrade_reports_stages_and_submits_pipeline():
    """Test launchUpgrade drives every stage through the progress callbacks.

    GIVEN an app in the post-prepareUpgrade state with RBAC not required,
        with the cluster functions mocked
    WHEN launchUpgrade runs with TUI progress callbacks
    THEN every stage is started and reported successful in order, and the
         PipelineRun is submitted for the selected instance.
    """
    app = _make_app(
        masInstanceId="inst1",
        currentChannel="9.1.x",
        nextChannel="9.2.x",
        effectiveCurrentChannel="9.1.x",
        pipelineStorageClass="ocs-sc",
        pipelineStorageAccessMode="ReadWriteMany",
    )
    app.params["mas_instance_id"] = "inst1"
    app.createTektonFileWithDigest = MagicMock()

    events = []

    with (
        patch("mas.cli.upgrade.app.installOpenShiftPipelines", return_value=True),
        patch("mas.cli.upgrade.app.createNamespace"),
        patch("mas.cli.upgrade.app.preparePipelinesNamespace"),
        patch("mas.cli.upgrade.app.prepareUpgradeSecrets"),
        patch("mas.cli.upgrade.app.updateTektonDefinitions"),
        patch("mas.cli.upgrade.app.launchUpgradePipeline", return_value="https://example.com/pipelinerun") as mock_launch,
    ):
        app.launchUpgrade(
            progressCallback=lambda label, ok, detail: events.append(("done", label, ok, detail)),
            startCallback=lambda label: events.append(("start", label)),
        )

    started = [e[1] for e in events if e[0] == "start"]
    assert started == ["Validate OpenShift Pipelines", "Prepare pipelines namespace", "Install Tekton definitions", "Submit PipelineRun"]

    done = {e[1]: e for e in events if e[0] == "done"}
    assert all(e[2] is True for e in done.values())
    assert done["Submit PipelineRun"][3] == "https://example.com/pipelinerun"

    mock_launch.assert_called_once_with(app._dynClient, "inst1", False, masChannel="9.1.x", params=app.params)


def test_launch_upgrade_applies_rbac_when_required():
    """Test launchUpgrade applies pre-install RBAC between pipelines and namespace stages.

    GIVEN an app whose prepareUpgrade detected RBAC is required (9.2.x
        target, cluster mode)
    WHEN launchUpgrade runs
    THEN applyPreInstallMASRBAC is called with the target version and mode,
         reported as a stage between OpenShift Pipelines validation and
         namespace preparation.
    """
    app = _make_app(
        masInstanceId="inst1",
        currentChannel="9.1.x",
        nextChannel="9.2.x",
        effectiveCurrentChannel="9.1.x",
        applyPreInstallMASRBAC=True,
        detectedMode="cluster",
    )
    app.params["mas_instance_id"] = "inst1"
    app.createTektonFileWithDigest = MagicMock()

    events = []

    with (
        patch("mas.cli.upgrade.app.installOpenShiftPipelines", return_value=True),
        patch("mas.cli.upgrade.app.getInstalledApps", return_value=["manage"]) as mock_apps,
        patch("mas.cli.upgrade.app.applyPreInstallMASRBAC") as mock_apply,
        patch("mas.cli.upgrade.app.createNamespace"),
        patch("mas.cli.upgrade.app.preparePipelinesNamespace"),
        patch("mas.cli.upgrade.app.prepareUpgradeSecrets"),
        patch("mas.cli.upgrade.app.updateTektonDefinitions"),
        patch("mas.cli.upgrade.app.launchUpgradePipeline", return_value="https://example.com/pipelinerun"),
    ):
        app.launchUpgrade(
            progressCallback=lambda label, ok, detail: events.append(("done", label, ok, detail)),
            startCallback=lambda label: events.append(("start", label)),
        )

    mock_apply.assert_called_once()
    assert mock_apply.call_args.kwargs["masVersion"] == "9.2"
    assert mock_apply.call_args.kwargs["adminMode"] == "cluster"
    assert mock_apply.call_args.kwargs["selectedApps"] == ["manage"]
    mock_apps.assert_called_once()

    started = [e[1] for e in events if e[0] == "start"]
    assert started.index("Apply pre-install MAS RBAC") == 1
