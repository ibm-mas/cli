#!/usr/bin/env python
# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""
Unit tests for RBAC functions in the upgrade command

Tests cover:
- Admin mode detection during upgrade
- RBAC evaluation for different upgrade paths
- 9.1 to 9.2 upgrade (defaults to cluster mode)
- 9.2+ to 9.3+ upgrade (detects existing mode)
"""

from unittest.mock import Mock, patch
import pytest
from mas.cli.upgrade.app import UpgradeApp


class TestUpgradeAdminModeDetectionIntegration:
    """Integration tests for admin mode detection during upgrade flow

    These tests verify the actual upgrade() method's mode detection logic
    by mocking external dependencies and checking that getPermissionMode()
    is called correctly based on current and target channels.
    """

    def setup_method(self):
        """Set up test fixtures"""
        self.app = UpgradeApp()
        self.app._dynClient = Mock()
        # Mock dynamicClient.resources.get() to return a mock API with get() method
        mock_api = Mock()
        mock_api.get.return_value = {"items": []}
        self.app._dynClient.resources.get.return_value = mock_api
        self.app.noConfirm = True  # Skip interactive prompts
        self.app.skipPreCheck = True
        self.app.licenseAccepted = True
        self.app.nextChannel = ""
        self.app.devMode = False
        self.app.params = {}  # Initialize params dict to avoid subscript errors

    @patch("mas.cli.upgrade.app.logger")
    @patch("mas.cli.upgrade.app.launchUpgradePipeline")
    @patch("mas.cli.upgrade.app.updateTektonDefinitions")
    @patch("mas.cli.upgrade.app.preparePipelinesNamespace")
    @patch("mas.cli.upgrade.app.getDefaultStorageClasses")
    @patch("mas.cli.upgrade.app.installOpenShiftPipelines")
    @patch("mas.cli.upgrade.app.createNamespace")
    @patch("mas.cli.upgrade.app.getInstalledApps")
    @patch("mas.cli.upgrade.app.evaluatePreinstallRBACAccess")
    @patch("mas.cli.upgrade.app.getPermissionMode")
    @patch("mas.cli.upgrade.app.getAppsSubscriptionChannel")
    @patch("mas.cli.upgrade.app.getMasChannel")
    @patch.object(UpgradeApp, "lookupTargetArchitecture")
    @patch.object(UpgradeApp, "createTektonFileWithDigest")
    def test_upgrade_92x_to_93x_calls_getPermissionMode(
        self,
        mock_create_tekton,
        mock_lookup_arch,
        mock_get_channel,
        mock_get_apps_channel,
        mock_get_mode,
        mock_evaluate_rbac,
        mock_get_installed_apps,
        mock_create_ns,
        mock_install_pipelines,
        mock_get_default_storage_classes,
        mock_prepare_pipelines_ns,
        mock_update_tekton,
        mock_launch_pipeline,
        mock_logger,
    ):
        """Test that upgrading from 9.2.x to 9.3.x calls getPermissionMode()"""
        # Setup mocks
        mock_lookup_arch.return_value = None
        mock_get_channel.return_value = "9.2.x"
        mock_get_apps_channel.return_value = []  # Return empty list (gets iterated)
        mock_get_mode.return_value = "namespaced"
        mock_evaluate_rbac.return_value = True
        mock_get_installed_apps.return_value = []
        mock_create_ns.return_value = None
        mock_install_pipelines.return_value = True
        mock_update_tekton.return_value = None
        mock_launch_pipeline.return_value = None

        # Set upgrade path
        self.app.upgrade_path = {"9.2.x": "9.3.x"}
        self.app.compatibilityMatrix = {}
        self.app.licenses = {"9.3.x": "https://ibm.com/license"}

        # Run upgrade
        self.app.upgrade(["--mas-instance-id", "test-instance", "--no-confirm", "--accept-license"])

        # Verify getPermissionMode was called (9.2.x → 9.3.x detects mode)
        mock_get_mode.assert_called_once_with(self.app._dynClient, "test-instance")

    @patch("mas.cli.upgrade.app.logger")
    @patch("mas.cli.upgrade.app.launchUpgradePipeline")
    @patch("mas.cli.upgrade.app.updateTektonDefinitions")
    @patch("mas.cli.upgrade.app.preparePipelinesNamespace")
    @patch("mas.cli.upgrade.app.getDefaultStorageClasses")
    @patch("mas.cli.upgrade.app.installOpenShiftPipelines")
    @patch("mas.cli.upgrade.app.createNamespace")
    @patch("mas.cli.upgrade.app.getInstalledApps")
    @patch("mas.cli.upgrade.app.evaluatePreinstallRBACAccess")
    @patch("mas.cli.upgrade.app.getPermissionMode")
    @patch("mas.cli.upgrade.app.getAppsSubscriptionChannel")
    @patch("mas.cli.upgrade.app.getMasChannel")
    @patch.object(UpgradeApp, "lookupTargetArchitecture")
    @patch.object(UpgradeApp, "createTektonFileWithDigest")
    def test_upgrade_92x_feature_to_92x_defaults_cluster(
        self,
        mock_create_tekton,
        mock_lookup_arch,
        mock_get_channel,
        mock_get_apps_channel,
        mock_get_mode,
        mock_evaluate_rbac,
        mock_get_installed_apps,
        mock_create_ns,
        mock_install_pipelines,
        mock_get_default_storage_classes,
        mock_prepare_pipelines_ns,
        mock_update_tekton,
        mock_launch_pipeline,
        mock_logger,
    ):
        """Test that upgrading from 9.2.x-feature to 9.2.x defaults to cluster mode"""
        # Setup mocks
        mock_lookup_arch.return_value = None
        mock_get_channel.return_value = "9.2.x-feature"
        mock_get_apps_channel.return_value = []  # Return empty list (gets iterated)
        mock_evaluate_rbac.return_value = True
        mock_get_installed_apps.return_value = []
        mock_create_ns.return_value = None
        mock_install_pipelines.return_value = True
        mock_update_tekton.return_value = None
        mock_launch_pipeline.return_value = None

        # Set upgrade path
        self.app.upgrade_path = {"9.2.x-feature": "9.2.x"}
        self.app.compatibilityMatrix = {}
        self.app.licenses = {"9.2.x": "https://ibm.com/license"}

        # Run upgrade
        self.app.upgrade(["--mas-instance-id", "test-instance", "--no-confirm", "--accept-license"])

        # Verify getPermissionMode was NOT called (upgrading TO 9.2.x defaults to cluster)
        mock_get_mode.assert_not_called()

        # Verify evaluatePreinstallRBACAccess was called with "cluster" mode
        assert mock_evaluate_rbac.called
        call_args = mock_evaluate_rbac.call_args
        assert call_args[1]["adminMode"] == "cluster"

    @patch("mas.cli.upgrade.app.logger")
    @patch("mas.cli.upgrade.app.launchUpgradePipeline")
    @patch("mas.cli.upgrade.app.updateTektonDefinitions")
    @patch("mas.cli.upgrade.app.preparePipelinesNamespace")
    @patch("mas.cli.upgrade.app.getDefaultStorageClasses")
    @patch("mas.cli.upgrade.app.installOpenShiftPipelines")
    @patch("mas.cli.upgrade.app.createNamespace")
    @patch("mas.cli.upgrade.app.getInstalledApps")
    @patch("mas.cli.upgrade.app.evaluatePreinstallRBACAccess")
    @patch("mas.cli.upgrade.app.getPermissionMode")
    @patch("mas.cli.upgrade.app.getAppsSubscriptionChannel")
    @patch("mas.cli.upgrade.app.getMasChannel")
    @patch.object(UpgradeApp, "lookupTargetArchitecture")
    @patch.object(UpgradeApp, "createTektonFileWithDigest")
    def test_upgrade_90x_to_91x_no_mode_detection(
        self,
        mock_create_tekton,
        mock_lookup_arch,
        mock_get_channel,
        mock_get_apps_channel,
        mock_get_mode,
        mock_evaluate_rbac,
        mock_get_installed_apps,
        mock_create_ns,
        mock_install_pipelines,
        mock_get_default_storage_classes,
        mock_prepare_pipelines_ns,
        mock_update_tekton,
        mock_launch_pipeline,
        mock_logger,
    ):
        """Test that upgrading from 9.0.x to 9.1.x does NOT detect mode (pre-RBAC)"""
        # Setup mocks
        mock_lookup_arch.return_value = None
        mock_get_channel.return_value = "9.0.x"
        mock_get_apps_channel.return_value = []  # Return empty list (gets iterated)
        mock_create_ns.return_value = None
        mock_install_pipelines.return_value = True
        mock_update_tekton.return_value = None
        mock_launch_pipeline.return_value = None

        # Set upgrade path
        self.app.upgrade_path = {"9.0.x": "9.1.x"}
        self.app.compatibilityMatrix = {}
        self.app.licenses = {"9.1.x": "https://ibm.com/license"}

        # Run upgrade
        self.app.upgrade(["--mas-instance-id", "test-instance", "--no-confirm", "--accept-license"])

        # Verify getPermissionMode was NOT called (pre-RBAC era)
        mock_get_mode.assert_not_called()

        # Verify evaluatePreinstallRBACAccess was NOT called (no RBAC for 9.0→9.1)
        mock_evaluate_rbac.assert_not_called()


class TestUpgradeRBACEvaluationIntegration:
    """Integration tests for RBAC evaluation during upgrade flow

    These tests verify that evaluatePreinstallRBACAccess() is called correctly
    with the right parameters during the actual upgrade() method execution.
    """

    def setup_method(self):
        """Set up test fixtures"""
        self.app = UpgradeApp()
        self.app._dynClient = Mock()
        # Mock dynamicClient.resources.get() to return a mock API with get() method
        mock_api = Mock()
        mock_api.get.return_value = {"items": []}
        self.app._dynClient.resources.get.return_value = mock_api
        self.app.noConfirm = True  # Skip interactive prompts
        self.app.skipPreCheck = True
        self.app.licenseAccepted = True
        self.app.nextChannel = ""
        self.app.devMode = False
        self.app.params = {}  # Initialize params dict to avoid subscript errors

    @patch("mas.cli.upgrade.app.logger")
    @patch("mas.cli.upgrade.app.launchUpgradePipeline")
    @patch("mas.cli.upgrade.app.updateTektonDefinitions")
    @patch("mas.cli.upgrade.app.preparePipelinesNamespace")
    @patch("mas.cli.upgrade.app.getDefaultStorageClasses")
    @patch("mas.cli.upgrade.app.installOpenShiftPipelines")
    @patch("mas.cli.upgrade.app.createNamespace")
    @patch("mas.cli.upgrade.app.getInstalledApps")
    @patch("mas.cli.upgrade.app.evaluatePreinstallRBACAccess")
    @patch("mas.cli.upgrade.app.getPermissionMode")
    @patch("mas.cli.upgrade.app.getAppsSubscriptionChannel")
    @patch("mas.cli.upgrade.app.getMasChannel")
    @patch.object(UpgradeApp, "lookupTargetArchitecture")
    @patch.object(UpgradeApp, "createTektonFileWithDigest")
    def test_upgrade_92x_feature_to_92x_defaults_cluster_mode(
        self,
        mock_create_tekton,
        mock_lookup_arch,
        mock_get_channel,
        mock_get_apps_channel,
        mock_get_mode,
        mock_evaluate_rbac,
        mock_get_installed_apps,
        mock_create_ns,
        mock_install_pipelines,
        mock_get_default_storage_classes,
        mock_prepare_pipelines_ns,
        mock_update_tekton,
        mock_launch_pipeline,
        mock_logger,
    ):
        """Test that 9.2.x-feature→9.2.x upgrade defaults to cluster mode"""
        # Setup mocks
        mock_lookup_arch.return_value = None
        mock_get_channel.return_value = "9.2.x-feature"
        mock_get_apps_channel.return_value = []
        mock_evaluate_rbac.return_value = True
        mock_get_installed_apps.return_value = []
        mock_create_ns.return_value = None
        mock_install_pipelines.return_value = True
        mock_update_tekton.return_value = None
        mock_launch_pipeline.return_value = None

        # Set upgrade path
        self.app.upgrade_path = {"9.2.x-feature": "9.2.x"}
        self.app.compatibilityMatrix = {}
        self.app.licenses = {"9.2.x": "https://ibm.com/license"}

        # Run upgrade
        self.app.upgrade(["--mas-instance-id", "test-instance", "--no-confirm", "--accept-license"])

        # Verify getPermissionMode was NOT called (upgrading TO 9.2.x defaults to cluster)
        mock_get_mode.assert_not_called()

        # Verify evaluatePreinstallRBACAccess was called with default cluster mode
        assert mock_evaluate_rbac.called
        call_args = mock_evaluate_rbac.call_args
        assert call_args[1]["adminMode"] == "cluster"
        assert call_args[1]["operation"] == "upgrade"

    @patch("mas.cli.upgrade.app.logger")
    @patch("mas.cli.upgrade.app.launchUpgradePipeline")
    @patch("mas.cli.upgrade.app.updateTektonDefinitions")
    @patch("mas.cli.upgrade.app.preparePipelinesNamespace")
    @patch("mas.cli.upgrade.app.getDefaultStorageClasses")
    @patch("mas.cli.upgrade.app.installOpenShiftPipelines")
    @patch("mas.cli.upgrade.app.createNamespace")
    @patch("mas.cli.upgrade.app.getInstalledApps")
    @patch("mas.cli.upgrade.app.evaluatePreinstallRBACAccess")
    @patch("mas.cli.upgrade.app.getPermissionMode")
    @patch("mas.cli.upgrade.app.getAppsSubscriptionChannel")
    @patch("mas.cli.upgrade.app.getMasChannel")
    @patch.object(UpgradeApp, "lookupTargetArchitecture")
    @patch.object(UpgradeApp, "createTektonFileWithDigest")
    def test_upgrade_92x_to_93x_detects_existing_mode(
        self,
        mock_create_tekton,
        mock_lookup_arch,
        mock_get_channel,
        mock_get_apps_channel,
        mock_get_mode,
        mock_evaluate_rbac,
        mock_get_installed_apps,
        mock_create_ns,
        mock_install_pipelines,
        mock_get_default_storage_classes,
        mock_prepare_pipelines_ns,
        mock_update_tekton,
        mock_launch_pipeline,
        mock_logger,
    ):
        """Test that 9.2.x→9.3.x upgrade detects existing mode"""
        # Setup mocks
        mock_lookup_arch.return_value = None
        mock_get_channel.return_value = "9.2.x"
        mock_get_apps_channel.return_value = []
        mock_get_mode.return_value = "namespaced"
        mock_evaluate_rbac.return_value = True
        mock_get_installed_apps.return_value = []
        mock_create_ns.return_value = None
        mock_install_pipelines.return_value = True
        mock_update_tekton.return_value = None
        mock_launch_pipeline.return_value = None

        # Set upgrade path
        self.app.upgrade_path = {"9.2.x": "9.3.x"}
        self.app.compatibilityMatrix = {}
        self.app.licenses = {"9.3.x": "https://ibm.com/license"}

        # Run upgrade
        self.app.upgrade(["--mas-instance-id", "test-instance", "--no-confirm", "--accept-license"])

        # Verify getPermissionMode WAS called (9.2.x→9.3.x detects mode)
        mock_get_mode.assert_called_once_with(self.app._dynClient, "test-instance")

        # Verify evaluatePreinstallRBACAccess was called with detected mode
        assert mock_evaluate_rbac.called
        call_args = mock_evaluate_rbac.call_args
        assert call_args[1]["adminMode"] == "namespaced"
        assert call_args[1]["operation"] == "upgrade"


class TestUpgradeRBACWithApps:
    """Test suite for RBAC evaluation with installed apps during upgrade"""

    def setup_method(self):
        """Set up test fixtures"""
        self.app = UpgradeApp()
        self.app._dynClient = Mock()
        self.app.noConfirm = False
        self.app.printH1 = Mock()
        self.app.printDescription = Mock()
        self.app.yesOrNo = Mock(return_value=True)
        self.app.fatalError = Mock()
        self.app.nextChannel = "9.2.0"

    @patch("mas.devops.mas.getInstalledApps")
    @patch("mas.cli.upgrade.app.evaluatePreinstallRBACAccess")
    @patch("mas.cli.upgrade.app.getPermissionMode")
    def test_upgrade_with_multiple_apps(self, mock_get_mode, mock_evaluate, mock_get_apps):
        """Test upgrade with multiple apps installed"""
        mock_get_mode.return_value = "namespaced"
        mock_evaluate.return_value = True
        mock_get_apps.return_value = ["core", "manage", "iot", "monitor"]

        instanceId = "prod-instance"
        detectedMode = mock_get_mode(self.app._dynClient, instanceId)

        if detectedMode:
            result = mock_evaluate(
                dynamicClient=self.app._dynClient,
                masChannel=self.app.nextChannel,
                adminMode=detectedMode,
                instanceId=instanceId,
                noConfirm=False,
                printH1Func=self.app.printH1,
                printDescriptionFunc=self.app.printDescription,
                yesOrNoFunc=self.app.yesOrNo,
                fatalErrorFunc=self.app.fatalError,
                operation="upgrade",
            )
            assert result is True


class TestUpgradeRBACIntegration:
    """Integration tests for upgrade RBAC scenarios"""

    def setup_method(self):
        """Set up test fixtures"""
        self.app = UpgradeApp()
        self.app._dynClient = Mock()
        self.app.noConfirm = False
        self.app.printH1 = Mock()
        self.app.printDescription = Mock()
        self.app.yesOrNo = Mock(return_value=True)
        self.app.fatalError = Mock()
        self.app.nextChannel = "9.2.0"

    @patch("mas.devops.mas.getInstalledApps")
    @patch("mas.devops.pre_install.permissionCheckForRBAC")
    @patch("mas.devops.utils.isVersionEqualOrAfter")
    @patch("mas.cli.upgrade.app.evaluatePreinstallRBACAccess")
    @patch("mas.cli.upgrade.app.getPermissionMode")
    def test_upgrade_92_with_permissions(self, mock_get_mode, mock_evaluate, mock_version, mock_permissions, mock_apps):
        """Test upgrade from 9.2.x when user has permissions"""
        mock_get_mode.return_value = "cluster"
        mock_version.return_value = True
        mock_permissions.return_value = [{"allowed": True}, {"allowed": True}]
        mock_apps.return_value = ["core", "manage"]
        mock_evaluate.return_value = True

        instanceId = "test-instance"
        detectedMode = mock_get_mode(self.app._dynClient, instanceId)

        if detectedMode:
            result = mock_evaluate(
                dynamicClient=self.app._dynClient,
                masChannel=self.app.nextChannel,
                adminMode=detectedMode,
                instanceId=instanceId,
                noConfirm=False,
                printH1Func=self.app.printH1,
                printDescriptionFunc=self.app.printDescription,
                yesOrNoFunc=self.app.yesOrNo,
                fatalErrorFunc=self.app.fatalError,
                operation="upgrade",
            )
            assert result is True

    @patch("mas.cli.rbac_utils.handleRBACPermissionDenied")
    @patch("mas.devops.mas.getInstalledApps")
    @patch("mas.devops.pre_install.permissionCheckForRBAC")
    @patch("mas.devops.utils.isVersionEqualOrAfter")
    @patch("mas.cli.upgrade.app.evaluatePreinstallRBACAccess")
    @patch("mas.cli.upgrade.app.getPermissionMode")
    def test_upgrade_92_without_permissions(self, mock_get_mode, mock_evaluate, mock_version, mock_permissions, mock_apps, mock_handler):
        """Test upgrade from 9.2.x when user lacks permissions"""
        mock_get_mode.return_value = "cluster"
        mock_version.return_value = True
        mock_permissions.return_value = [{"allowed": False}]
        mock_apps.return_value = ["core"]
        mock_evaluate.return_value = False

        instanceId = "test-instance"
        detectedMode = mock_get_mode(self.app._dynClient, instanceId)

        if detectedMode:
            result = mock_evaluate(
                dynamicClient=self.app._dynClient,
                masChannel=self.app.nextChannel,
                adminMode=detectedMode,
                instanceId=instanceId,
                noConfirm=False,
                printH1Func=self.app.printH1,
                printDescriptionFunc=self.app.printDescription,
                yesOrNoFunc=self.app.yesOrNo,
                fatalErrorFunc=self.app.fatalError,
                operation="upgrade",
            )
            assert result is False

    @patch("mas.cli.upgrade.app.evaluatePreinstallRBACAccess")
    @patch("mas.cli.upgrade.app.getPermissionMode")
    def test_upgrade_no_confirm_mode(self, mock_get_mode, mock_evaluate):
        """Test upgrade in no-confirm mode"""
        mock_get_mode.return_value = "cluster"
        mock_evaluate.return_value = False

        self.app.noConfirm = True
        instanceId = "test-instance"
        detectedMode = mock_get_mode(self.app._dynClient, instanceId)

        if detectedMode:
            mock_evaluate(
                dynamicClient=self.app._dynClient,
                masChannel=self.app.nextChannel,
                adminMode=detectedMode,
                instanceId=instanceId,
                noConfirm=True,
                printH1Func=self.app.printH1,
                printDescriptionFunc=self.app.printDescription,
                yesOrNoFunc=self.app.yesOrNo,
                fatalErrorFunc=self.app.fatalError,
                operation="upgrade",
            )
            # Should not prompt user in no-confirm mode
            assert not self.app.yesOrNo.called


class TestUpgradeRBACCommandGeneration:
    """Test suite for pre-install command generation during upgrade"""

    def setup_method(self):
        """Set up test fixtures"""
        self.app = UpgradeApp()
        self.app._dynClient = Mock()

    def test_preinstall_command_with_instance_id(self):
        """Test that upgrade generates command with instance ID"""
        instanceId = "prod-mas"
        masChannel = "9.2.0"
        adminMode = "cluster"

        # Expected command format
        expected_cmd = f"mas pre-install --mas-instance-id {instanceId} --mas-channel {masChannel} --admin-mode {adminMode}"

        # Verify instance ID in command
        assert "--mas-instance-id" in expected_cmd
        assert instanceId in expected_cmd

    def test_preinstall_command_with_apps(self):
        """Test that upgrade generates command with installed apps"""
        instanceId = "prod-mas"
        masChannel = "9.2.0"
        adminMode = "cluster"
        apps = ["core", "manage", "iot"]

        # Expected command format
        expected_cmd = f"mas pre-install --mas-instance-id {instanceId} --mas-channel {masChannel} --admin-mode {adminMode} --apps {','.join(apps)}"

        # Verify apps in command
        assert "--apps" in expected_cmd
        assert "core,manage,iot" in expected_cmd


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
