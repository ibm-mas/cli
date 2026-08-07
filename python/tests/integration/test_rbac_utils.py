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
Unit tests for RBAC utility functions in cli/python/src/mas/cli/rbac_utils.py

These are GENERIC tests for RBAC utility functions used by ALL commands:
- install command
- upgrade command
- update command

Tests cover:
- handleRBACPermissionDenied function (used by all commands)
- evaluatePreinstallRBACAccess function (used by all commands)
- Various permission scenarios and user interactions
- Integration tests for install, upgrade, and update operations
"""

from unittest.mock import Mock, patch
import pytest
from mas.cli.rbac_utils import handleRBACPermissionDenied, evaluatePreinstallRBACAccess


class TestHandleRBACPermissionDenied:
    """Test suite for handleRBACPermissionDenied function"""

    def test_no_confirm_mode_prints_warning(self):
        """Test that no-confirm mode prints appropriate warning messages"""
        printFunc = Mock()
        yesOrNoFunc = Mock()
        fatalErrorFunc = Mock()

        handleRBACPermissionDenied(
            printFunc=printFunc,
            yesOrNoFunc=yesOrNoFunc,
            fatalErrorFunc=fatalErrorFunc,
            noConfirm=True,
            adminMode="cluster",
            preinstallCommand="mas pre-install --mas-channel 9.2.0 --admin-mode cluster",
            operation="installation",
        )

        # Verify printFunc was called with warning message
        assert printFunc.called
        call_args = printFunc.call_args[0][0]
        assert any("Installation will continue" in msg for msg in call_args)
        assert any("mas pre-install" in msg for msg in call_args)

        # Verify yesOrNoFunc was NOT called in no-confirm mode
        assert not yesOrNoFunc.called

        # Verify fatalErrorFunc was NOT called
        assert not fatalErrorFunc.called

    def test_interactive_mode_user_confirms_rbac_applied(self):
        """Test interactive mode when user confirms RBAC was already applied"""
        printFunc = Mock()
        yesOrNoFunc = Mock(return_value=True)  # User confirms
        fatalErrorFunc = Mock()

        handleRBACPermissionDenied(
            printFunc=printFunc,
            yesOrNoFunc=yesOrNoFunc,
            fatalErrorFunc=fatalErrorFunc,
            noConfirm=False,
            adminMode="namespaced",
            preinstallCommand="mas pre-install --mas-instance-id prod --mas-channel 9.2.0 --admin-mode namespaced",
            operation="upgrade",
        )

        # Verify printFunc was called with instructions
        assert printFunc.called
        call_args = printFunc.call_args[0][0]
        assert any("Ask your OpenShift administrator" in msg for msg in call_args)

        # Verify yesOrNoFunc was called to ask user
        assert yesOrNoFunc.called
        assert "Has your OpenShift administrator already run 'mas pre-install'" in yesOrNoFunc.call_args[0][0]

        # Verify fatalErrorFunc was NOT called (user confirmed)
        assert not fatalErrorFunc.called

    def test_interactive_mode_user_denies_rbac_applied(self):
        """Test interactive mode when user denies RBAC was applied"""
        printFunc = Mock()
        yesOrNoFunc = Mock(return_value=False)  # User denies
        fatalErrorFunc = Mock()

        handleRBACPermissionDenied(
            printFunc=printFunc,
            yesOrNoFunc=yesOrNoFunc,
            fatalErrorFunc=fatalErrorFunc,
            noConfirm=False,
            adminMode="cluster",
            preinstallCommand="mas pre-install --mas-channel 9.3.0 --admin-mode cluster",
            operation="update",
        )

        # Verify fatalErrorFunc WAS called (user denied)
        assert fatalErrorFunc.called
        error_msg = fatalErrorFunc.call_args[0][0]
        assert "Update aborted" in error_msg
        assert "Ask your OpenShift administrator" in error_msg

    def test_different_operations_in_messages(self):
        """Test that operation name appears correctly in messages"""
        for operation in ["installation", "upgrade", "update"]:
            printFunc = Mock()
            yesOrNoFunc = Mock(return_value=True)
            fatalErrorFunc = Mock()

            handleRBACPermissionDenied(
                printFunc=printFunc,
                yesOrNoFunc=yesOrNoFunc,
                fatalErrorFunc=fatalErrorFunc,
                noConfirm=False,
                adminMode="cluster",
                preinstallCommand="mas pre-install --mas-channel 9.2.0 --admin-mode cluster",
                operation=operation,
            )

            # Check that operation appears in the prompt
            prompt_text = yesOrNoFunc.call_args[0][0]
            assert operation in prompt_text.lower()


class TestevaluatePreinstallRBACAccess:
    """Test suite for evaluatePreinstallRBACAccess function"""

    @patch("mas.cli.rbac_utils.isVersionEqualOrAfter")
    def test_version_less_than_920_returns_false(self, mock_version_check):
        """Test that versions < 9.2.0 return False (no RBAC needed)"""
        mock_version_check.return_value = False
        dynamicClient = Mock()

        result = evaluatePreinstallRBACAccess(dynamicClient=dynamicClient, masChannel="9.1.0", adminMode="cluster", instanceId="test-instance")

        assert result is False
        mock_version_check.assert_called_once_with("9.2.0", "9.1.0")

    @patch("mas.cli.rbac_utils.isVersionEqualOrAfter")
    def test_minimal_mode_returns_false(self, mock_version_check):
        """Test that minimal admin mode returns False (no RBAC needed)"""
        mock_version_check.return_value = True
        dynamicClient = Mock()

        result = evaluatePreinstallRBACAccess(dynamicClient=dynamicClient, masChannel="9.2.0", adminMode="minimal", instanceId="test-instance")

        assert result is False

    @patch("mas.cli.rbac_utils.getInstalledApps")
    @patch("mas.cli.rbac_utils.permissionCheckForRBAC")
    @patch("mas.cli.rbac_utils.isVersionEqualOrAfter")
    def test_user_has_permissions_returns_true(self, mock_version_check, mock_permission_check, mock_get_apps):
        """Test that when user has permissions, function returns True"""
        mock_version_check.return_value = True
        mock_permission_check.return_value = [{"allowed": True}, {"allowed": True}, {"allowed": True}]
        dynamicClient = Mock()

        result = evaluatePreinstallRBACAccess(dynamicClient=dynamicClient, masChannel="9.2.0", adminMode="cluster", instanceId="test-instance")

        assert result is True
        mock_permission_check.assert_called_once_with(dynamicClient)

    @patch("mas.cli.rbac_utils.handleRBACPermissionDenied")
    @patch("mas.cli.rbac_utils.getInstalledApps")
    @patch("mas.cli.rbac_utils.permissionCheckForRBAC")
    @patch("mas.cli.rbac_utils.isVersionEqualOrAfter")
    def test_user_lacks_permissions_calls_handler(self, mock_version_check, mock_permission_check, mock_get_apps, mock_handler):
        """Test that when user lacks permissions, handler is called"""
        mock_version_check.return_value = True
        mock_permission_check.return_value = [{"allowed": True}, {"allowed": False}, {"allowed": True}]  # One permission denied
        mock_get_apps.return_value = ["core", "manage"]

        dynamicClient = Mock()
        printH1Func = Mock()
        printDescriptionFunc = Mock()
        yesOrNoFunc = Mock(return_value=True)  # User confirms RBAC was applied
        fatalErrorFunc = Mock()

        result = evaluatePreinstallRBACAccess(
            dynamicClient=dynamicClient,
            masChannel="9.2.0",
            adminMode="cluster",
            instanceId="test-instance",
            noConfirm=False,
            printH1Func=printH1Func,
            printDescriptionFunc=printDescriptionFunc,
            yesOrNoFunc=yesOrNoFunc,
            fatalErrorFunc=fatalErrorFunc,
            operation="installation",
        )

        # Should return False (user doesn't have permissions, but confirmed RBAC was applied)
        assert result is False

        # Verify handler was called
        assert mock_handler.called
        call_kwargs = mock_handler.call_args[1]
        assert call_kwargs["adminMode"] == "cluster"
        assert call_kwargs["operation"] == "installation"
        assert "mas pre-install" in call_kwargs["preinstallCommand"]
        assert "--apps core,manage" in call_kwargs["preinstallCommand"]

    @patch("mas.cli.rbac_utils.getInstalledApps")
    @patch("mas.cli.rbac_utils.permissionCheckForRBAC")
    @patch("mas.cli.rbac_utils.isVersionEqualOrAfter")
    def test_no_instance_id_no_apps_in_command(self, mock_version_check, mock_permission_check, mock_get_apps):
        """Test that when no instance ID provided, no apps are included in command"""
        mock_version_check.return_value = True
        mock_permission_check.return_value = [{"allowed": False}]

        dynamicClient = Mock()
        printDescriptionFunc = Mock()

        # Call without instance ID
        evaluatePreinstallRBACAccess(
            dynamicClient=dynamicClient, masChannel="9.2.0", adminMode="cluster", instanceId=None, printDescriptionFunc=printDescriptionFunc  # No instance ID
        )

        # getInstalledApps should NOT be called
        assert not mock_get_apps.called

    @patch("mas.cli.rbac_utils.handleRBACPermissionDenied")
    @patch("mas.cli.rbac_utils.getInstalledApps")
    @patch("mas.cli.rbac_utils.permissionCheckForRBAC")
    @patch("mas.cli.rbac_utils.isVersionEqualOrAfter")
    def test_with_instance_id_includes_apps(self, mock_version_check, mock_permission_check, mock_get_apps, mock_handler):
        """Test that when instance ID provided, apps are included in command"""
        mock_version_check.return_value = True
        mock_permission_check.return_value = [{"allowed": False}]
        mock_get_apps.return_value = ["core", "iot", "monitor"]

        dynamicClient = Mock()
        printDescriptionFunc = Mock()
        yesOrNoFunc = Mock(return_value=True)  # User confirms RBAC was applied
        fatalErrorFunc = Mock()

        evaluatePreinstallRBACAccess(
            dynamicClient=dynamicClient,
            masChannel="9.3.0",
            adminMode="namespaced",
            instanceId="prod-instance",
            printDescriptionFunc=printDescriptionFunc,
            yesOrNoFunc=yesOrNoFunc,
            fatalErrorFunc=fatalErrorFunc,
        )

        # Verify getInstalledApps was called with instance ID
        mock_get_apps.assert_called_once_with(dynamicClient, "prod-instance")

        # Verify command includes apps
        call_kwargs = mock_handler.call_args[1]
        assert "--apps core,iot,monitor" in call_kwargs["preinstallCommand"]
        assert "--mas-instance-id prod-instance" in call_kwargs["preinstallCommand"]

    @patch("mas.cli.rbac_utils.permissionCheckForRBAC")
    @patch("mas.cli.rbac_utils.isVersionEqualOrAfter")
    def test_different_admin_modes(self, mock_version_check, mock_permission_check):
        """Test function works with different admin modes"""
        mock_version_check.return_value = True
        mock_permission_check.return_value = [{"allowed": True}]

        dynamicClient = Mock()

        for admin_mode in ["cluster", "namespaced"]:
            result = evaluatePreinstallRBACAccess(dynamicClient=dynamicClient, masChannel="9.2.0", adminMode=admin_mode, instanceId="test")
            assert result is True


class TestIntegrationScenarios:
    """Integration tests for common RBAC scenarios"""

    @patch("mas.cli.rbac_utils.handleRBACPermissionDenied")
    @patch("mas.cli.rbac_utils.getInstalledApps")
    @patch("mas.cli.rbac_utils.permissionCheckForRBAC")
    @patch("mas.cli.rbac_utils.isVersionEqualOrAfter")
    def test_install_scenario_no_permissions(self, mock_version_check, mock_permission_check, mock_get_apps, mock_handler):
        """Test typical install scenario where user lacks permissions"""
        mock_version_check.return_value = True
        mock_permission_check.return_value = [{"allowed": False}]
        mock_get_apps.return_value = []

        dynamicClient = Mock()
        printH1Func = Mock()
        printDescriptionFunc = Mock()
        yesOrNoFunc = Mock(return_value=True)  # User confirms RBAC applied
        fatalErrorFunc = Mock()

        result = evaluatePreinstallRBACAccess(
            dynamicClient=dynamicClient,
            masChannel="9.2.x",
            adminMode="cluster",
            instanceId=None,  # Install has no instance ID yet
            noConfirm=False,
            printH1Func=printH1Func,
            printDescriptionFunc=printDescriptionFunc,
            yesOrNoFunc=yesOrNoFunc,
            fatalErrorFunc=fatalErrorFunc,
            operation="installation",
        )

        assert result is False
        assert printH1Func.called
        assert mock_handler.called

    @patch("mas.cli.rbac_utils.getInstalledApps")
    @patch("mas.cli.rbac_utils.permissionCheckForRBAC")
    @patch("mas.cli.rbac_utils.isVersionEqualOrAfter")
    def test_upgrade_scenario_with_permissions(self, mock_version_check, mock_permission_check, mock_get_apps):
        """Test typical upgrade scenario where user has permissions"""
        mock_version_check.return_value = True
        mock_permission_check.return_value = [{"allowed": True}, {"allowed": True}]
        mock_get_apps.return_value = ["core", "manage", "iot"]

        dynamicClient = Mock()

        result = evaluatePreinstallRBACAccess(
            dynamicClient=dynamicClient, masChannel="9.3.0", adminMode="namespaced", instanceId="prod-mas", operation="upgrade"
        )

        assert result is True
        # getInstalledApps is NOT called when user has permissions (only called when lacking permissions)
        assert not mock_get_apps.called

    @patch("mas.cli.rbac_utils.handleRBACPermissionDenied")
    @patch("mas.cli.rbac_utils.getInstalledApps")
    @patch("mas.cli.rbac_utils.permissionCheckForRBAC")
    @patch("mas.cli.rbac_utils.isVersionEqualOrAfter")
    def test_update_scenario_no_confirm_mode(self, mock_version_check, mock_permission_check, mock_get_apps, mock_handler):
        """Test update scenario in no-confirm mode"""
        mock_version_check.return_value = True
        mock_permission_check.return_value = [{"allowed": False}]
        mock_get_apps.return_value = ["core"]

        dynamicClient = Mock()
        printDescriptionFunc = Mock()
        yesOrNoFunc = Mock()
        fatalErrorFunc = Mock()

        result = evaluatePreinstallRBACAccess(
            dynamicClient=dynamicClient,
            masChannel="9.2.0",
            adminMode="cluster",
            instanceId="dev-mas",
            noConfirm=True,  # No-confirm mode
            printDescriptionFunc=printDescriptionFunc,
            yesOrNoFunc=yesOrNoFunc,
            fatalErrorFunc=fatalErrorFunc,
            operation="update",
        )

        assert result is False
        # Verify handler was called with noConfirm=True
        call_kwargs = mock_handler.call_args[1]
        assert call_kwargs["noConfirm"] is True
        # yesOrNoFunc should NOT be called in no-confirm mode (handler handles this)
        # We can't assert yesOrNoFunc.called because handleRBACPermissionDenied is mocked


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
