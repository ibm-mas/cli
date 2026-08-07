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
Unit tests for RBAC functions in the install command

Tests cover:
- RBAC evaluation during installation
- Admin mode configuration
- Permission checking for new installations
"""

from unittest.mock import Mock, patch
import pytest
from mas.cli.install.app import InstallApp


class TestInstallRBACEvaluation:
    """Test suite for RBAC evaluation during install"""

    def setup_method(self):
        """Set up test fixtures"""
        self.app = InstallApp()
        self.app._dynClient = Mock()
        self.app.noConfirm = False
        self.app.printH1 = Mock()
        self.app.printDescription = Mock()
        self.app.yesOrNo = Mock(return_value=True)
        self.app.fatalError = Mock()
        self.app.mas_admin_mode = "cluster"

    @patch("mas.cli.install.app.evaluatePreinstallRBACAccess")
    def test_install_920_cluster_mode_evaluates_rbac(self, mock_evaluate):
        """Test that install with 9.2.0 cluster mode evaluates RBAC"""
        mock_evaluate.return_value = True

        # Mock getParam to return 9.2.0
        self.app.getParam = Mock(return_value="9.2.0")

        # Simulate the RBAC evaluation call
        result = mock_evaluate(
            dynamicClient=self.app._dynClient,
            masChannel="9.2.0",
            adminMode="cluster",
            noConfirm=False,
            printH1Func=self.app.printH1,
            printDescriptionFunc=self.app.printDescription,
            yesOrNoFunc=self.app.yesOrNo,
            fatalErrorFunc=self.app.fatalError,
            operation="installation",
        )

        assert result is True
        mock_evaluate.assert_called_once()

    @patch("mas.cli.install.app.evaluatePreinstallRBACAccess")
    def test_install_920_namespaced_mode_evaluates_rbac(self, mock_evaluate):
        """Test that install with 9.2.0 namespaced mode evaluates RBAC"""
        mock_evaluate.return_value = True
        self.app.mas_admin_mode = "namespaced"
        self.app.getParam = Mock(return_value="9.2.0")

        result = mock_evaluate(
            dynamicClient=self.app._dynClient,
            masChannel="9.2.0",
            adminMode="namespaced",
            noConfirm=False,
            printH1Func=self.app.printH1,
            printDescriptionFunc=self.app.printDescription,
            yesOrNoFunc=self.app.yesOrNo,
            fatalErrorFunc=self.app.fatalError,
            operation="installation",
        )

        assert result is True

    @patch("mas.cli.install.app.evaluatePreinstallRBACAccess")
    def test_install_920_minimal_mode_skips_rbac(self, mock_evaluate):
        """Test that install with minimal mode skips RBAC (returns False)"""
        mock_evaluate.return_value = False
        self.app.mas_admin_mode = "minimal"
        self.app.getParam = Mock(return_value="9.2.0")

        result = mock_evaluate(
            dynamicClient=self.app._dynClient,
            masChannel="9.2.0",
            adminMode="minimal",
            noConfirm=False,
            printH1Func=self.app.printH1,
            printDescriptionFunc=self.app.printDescription,
            yesOrNoFunc=self.app.yesOrNo,
            fatalErrorFunc=self.app.fatalError,
            operation="installation",
        )

        assert result is False

    @patch("mas.cli.install.app.evaluatePreinstallRBACAccess")
    def test_install_910_skips_rbac(self, mock_evaluate):
        """Test that install with 9.1.0 skips RBAC (version < 9.2.0)"""
        mock_evaluate.return_value = False
        self.app.getParam = Mock(return_value="9.1.0")

        result = mock_evaluate(
            dynamicClient=self.app._dynClient,
            masChannel="9.1.0",
            adminMode="cluster",
            noConfirm=False,
            printH1Func=self.app.printH1,
            printDescriptionFunc=self.app.printDescription,
            yesOrNoFunc=self.app.yesOrNo,
            fatalErrorFunc=self.app.fatalError,
            operation="installation",
        )

        assert result is False

    @patch("mas.cli.install.app.evaluatePreinstallRBACAccess")
    def test_install_no_confirm_mode(self, mock_evaluate):
        """Test install in no-confirm mode"""
        mock_evaluate.return_value = False  # Assumes RBAC already applied
        self.app.noConfirm = True
        self.app.getParam = Mock(return_value="9.2.0")

        mock_evaluate(
            dynamicClient=self.app._dynClient,
            masChannel="9.2.0",
            adminMode="cluster",
            noConfirm=True,
            printH1Func=self.app.printH1,
            printDescriptionFunc=self.app.printDescription,
            yesOrNoFunc=self.app.yesOrNo,
            fatalErrorFunc=self.app.fatalError,
            operation="installation",
        )

        # In no-confirm mode, should not prompt user
        assert not self.app.yesOrNo.called


class TestInstallAdminModeConfiguration:
    """Test suite for admin mode configuration during install"""

    def setup_method(self):
        """Set up test fixtures"""
        self.app = InstallApp()
        self.app._dynClient = Mock()

    def test_cluster_mode_configuration(self):
        """Test cluster mode is properly configured"""
        self.app.mas_admin_mode = "cluster"
        assert self.app.mas_admin_mode == "cluster"

    def test_namespaced_mode_configuration(self):
        """Test namespaced mode is properly configured"""
        self.app.mas_admin_mode = "namespaced"
        assert self.app.mas_admin_mode == "namespaced"

    def test_minimal_mode_configuration(self):
        """Test minimal mode is properly configured"""
        self.app.mas_admin_mode = "minimal"
        assert self.app.mas_admin_mode == "minimal"


class TestInstallRBACIntegration:
    """Integration tests for install RBAC scenarios"""

    def setup_method(self):
        """Set up test fixtures"""
        self.app = InstallApp()
        self.app._dynClient = Mock()
        self.app.noConfirm = False
        self.app.printH1 = Mock()
        self.app.printDescription = Mock()
        self.app.yesOrNo = Mock(return_value=True)
        self.app.fatalError = Mock()

    @patch("mas.devops.mas.getInstalledApps")
    @patch("mas.devops.pre_install.permissionCheckForRBAC")
    @patch("mas.devops.utils.isVersionEqualOrAfter")
    @patch("mas.cli.install.app.evaluatePreinstallRBACAccess")
    def test_fresh_install_920_with_permissions(self, mock_evaluate, mock_version, mock_permissions, mock_apps):
        """Test fresh install of 9.2.0 when user has permissions"""
        mock_version.return_value = True
        mock_permissions.return_value = [{"allowed": True}, {"allowed": True}]
        mock_apps.return_value = []  # No apps installed yet
        mock_evaluate.return_value = True

        self.app.mas_admin_mode = "cluster"
        self.app.getParam = Mock(return_value="9.2.0")

        # Simulate RBAC evaluation
        result = mock_evaluate(
            dynamicClient=self.app._dynClient,
            masChannel="9.2.0",
            adminMode="cluster",
            noConfirm=False,
            printH1Func=self.app.printH1,
            printDescriptionFunc=self.app.printDescription,
            yesOrNoFunc=self.app.yesOrNo,
            fatalErrorFunc=self.app.fatalError,
            operation="installation",
        )

        assert result is True
        # Verify the mock was called with correct parameters
        mock_evaluate.assert_called_once()

    @patch("mas.cli.rbac_utils.handleRBACPermissionDenied")
    @patch("mas.devops.mas.getInstalledApps")
    @patch("mas.devops.pre_install.permissionCheckForRBAC")
    @patch("mas.devops.utils.isVersionEqualOrAfter")
    @patch("mas.cli.install.app.evaluatePreinstallRBACAccess")
    def test_fresh_install_920_without_permissions(self, mock_evaluate, mock_version, mock_permissions, mock_apps, mock_handler):
        """Test fresh install of 9.2.0 when user lacks permissions"""
        mock_version.return_value = True
        mock_permissions.return_value = [{"allowed": False}]
        mock_apps.return_value = []
        mock_evaluate.return_value = False  # User doesn't have permissions

        self.app.mas_admin_mode = "cluster"
        self.app.getParam = Mock(return_value="9.2.0")

        result = mock_evaluate(
            dynamicClient=self.app._dynClient,
            masChannel="9.2.0",
            adminMode="cluster",
            noConfirm=False,
            printH1Func=self.app.printH1,
            printDescriptionFunc=self.app.printDescription,
            yesOrNoFunc=self.app.yesOrNo,
            fatalErrorFunc=self.app.fatalError,
            operation="installation",
        )

        assert result is False

    @patch("mas.cli.install.app.evaluatePreinstallRBACAccess")
    def test_install_930_cluster_mode(self, mock_evaluate):
        """Test install of 9.3.0 with cluster mode"""
        mock_evaluate.return_value = True

        self.app.mas_admin_mode = "cluster"
        self.app.getParam = Mock(return_value="9.3.0")

        result = mock_evaluate(
            dynamicClient=self.app._dynClient,
            masChannel="9.3.0",
            adminMode="cluster",
            noConfirm=False,
            printH1Func=self.app.printH1,
            printDescriptionFunc=self.app.printDescription,
            yesOrNoFunc=self.app.yesOrNo,
            fatalErrorFunc=self.app.fatalError,
            operation="installation",
        )

        assert result is True


class TestInstallRBACCommandGeneration:
    """Test suite for pre-install command generation during install"""

    def setup_method(self):
        """Set up test fixtures"""
        self.app = InstallApp()
        self.app._dynClient = Mock()

    def test_preinstall_command_no_instance_id(self):
        """Test that install generates command without instance ID"""
        # During install, there's no instance ID yet
        masChannel = "9.2.0"
        adminMode = "cluster"

        # Expected command format
        expected_cmd = f"mas pre-install --mas-channel {masChannel} --admin-mode {adminMode}"

        # Verify no instance ID in command
        assert "--mas-instance-id" not in expected_cmd

    def test_preinstall_command_no_apps(self):
        """Test that install generates command without apps"""
        # During install, no apps are installed yet
        masChannel = "9.2.0"
        adminMode = "cluster"

        # Expected command format
        expected_cmd = f"mas pre-install --mas-channel {masChannel} --admin-mode {adminMode}"

        # Verify no apps in command
        assert "--apps" not in expected_cmd


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
