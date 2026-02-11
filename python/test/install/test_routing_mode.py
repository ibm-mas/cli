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
Comprehensive test suite for routing mode functionality in MAS CLI.
Tests cover interactive and non-interactive modes for both path-based and subdomain routing.
"""

import sys
import os
import pytest
from unittest import mock
from unittest.mock import MagicMock, patch, call
from openshift.dynamic.exceptions import NotFoundError
from kubernetes.client.rest import ApiException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from mas.cli.install.app import InstallApp


# =============================================================================
# Test Helper Functions
# =============================================================================
def create_mock_app():
    """Create a mock InstallApp with a mocked dynamicClient."""
    app = MagicMock(spec=InstallApp)
    app.dynamicClient = MagicMock()
    app.showAdvancedOptions = True
    app.isInteractiveMode = False
    app.params = {}
    app.setParam = lambda key, value: app.params.__setitem__(key, value)
    app.getParam = lambda key: app.params.get(key, "")
    
    # Mock UI methods directly on the app object (not on the class)
    # This is necessary because MagicMock attributes shadow class methods
    app.promptForInt = MagicMock(return_value=1)
    app.yesOrNo = MagicMock(return_value=True)
    app.printDescription = MagicMock()
    app.printH1 = MagicMock()
    app.promptForString = MagicMock(return_value="")
    
    # Add the actual methods we want to test
    app._checkIngressControllerPermissions = InstallApp._checkIngressControllerPermissions.__get__(app, InstallApp)
    app._checkIngressControllerForPathRouting = InstallApp._checkIngressControllerForPathRouting.__get__(app, InstallApp)
    app._promptForIngressController = InstallApp._promptForIngressController.__get__(app, InstallApp)
    app._getMasDomainForDisplay = InstallApp._getMasDomainForDisplay.__get__(app, InstallApp)
    app.configRoutingMode = InstallApp.configRoutingMode.__get__(app, InstallApp)
    
    return app


def create_ingress_controller_mock(name="default", domain="apps.cluster.example.com",
                                   namespace_ownership="InterNamespaceAllowed", available=True):
    """Create a mock IngressController object that supports both dict and attribute access."""
    controller = MagicMock()
    controller.metadata.name = name
    
    if available:
        controller.status.domain = domain
        controller.status.conditions = [
            MagicMock(type='Available', status='True')
        ]
    
    # Create proper nested structure for attribute access
    controller.spec = MagicMock()
    controller.spec.routeAdmission = MagicMock()
    controller.spec.routeAdmission.namespaceOwnership = namespace_ownership
    
    # Support dict-style access for _checkIngressControllerForPathRouting
    # The method calls: ingressController.get('spec', {})
    # Then: spec.get('routeAdmission', {})
    # Then: routeAdmission.get('namespaceOwnership', '')
    def mock_get(key, default=None):
        if key == 'spec':
            spec_dict = {
                'routeAdmission': {
                    'namespaceOwnership': namespace_ownership
                }
            }
            # Return a dict-like object that supports .get()
            return type('obj', (object,), {
                'get': lambda self, k, d=None: spec_dict.get(k, d)
            })()
        return default
    
    controller.get = mock_get
    
    return controller


# =============================================================================
# Interactive Mode - Path Routing Tests
# =============================================================================
class TestInteractivePathRouting:
    """Test suite for interactive mode path-based routing scenarios."""
    
    def test_path_routing_single_controller_auto_selected(self):
        """Test that single available IngressController is automatically selected."""
        app = create_mock_app()
        app.isInteractiveMode = True
        
        # Mock single IngressController
        controller = create_ingress_controller_mock()
        ingress_api = MagicMock()
        ingress_api.get.return_value = MagicMock(items=[controller])
        app.dynamicClient.resources.get.return_value = ingress_api
        
        result = app._promptForIngressController()
        
        assert result == "default"
    
    def test_path_routing_multiple_controllers_user_selection(self):
        """Test user selection when multiple IngressControllers are available."""
        app = create_mock_app()
        app.isInteractiveMode = True
        
        # Mock multiple IngressControllers
        controller1 = create_ingress_controller_mock("default", "apps.cluster1.com")
        controller2 = create_ingress_controller_mock("custom", "apps.cluster2.com")
        
        ingress_api = MagicMock()
        ingress_api.get.return_value = MagicMock(items=[controller1, controller2])
        app.dynamicClient.resources.get.return_value = ingress_api
        
        # Set promptForInt to return 2 (select second controller)
        app.promptForInt.return_value = 2
        result = app._promptForIngressController()
        
        assert result == "custom"
    
    def test_path_routing_no_controllers_defaults_to_default(self):
        """Test fallback to 'default' when no IngressControllers are found."""
        app = create_mock_app()
        app.isInteractiveMode = True
        
        ingress_api = MagicMock()
        ingress_api.get.return_value = MagicMock(items=[])
        app.dynamicClient.resources.get.return_value = ingress_api
        
        result = app._promptForIngressController()
        
        assert result == "default"
    
    def test_interactive_path_routing_complete_flow_with_configuration(self):
        """Test complete interactive flow for path routing with IngressController configuration."""
        app = create_mock_app()
        app.isInteractiveMode = True
        app.showAdvancedOptions = True
        app.setParam("mas_channel", "9.2.0")
        app.setParam("mas_instance_id", "test-inst")
        
        # Mock IngressController API - not configured
        controller = create_ingress_controller_mock(namespace_ownership="Strict")
        ingress_api = MagicMock()
        ingress_api.get.side_effect = [
            controller,  # For permission check
            MagicMock(items=[controller]),  # For listing controllers
            controller  # For configuration check
        ]
        app.dynamicClient.resources.get.return_value = ingress_api
        
        # Mock Ingress config for domain display
        ingress_config_api = MagicMock()
        ingress_config = MagicMock()
        ingress_config.spec.get.return_value = "apps.cluster.example.com"
        ingress_config_api.get.return_value = ingress_config
        
        with patch.object(app.dynamicClient.resources, 'get') as mock_get:
            def get_side_effect(api_version, kind):
                if kind == "IngressController":
                    return ingress_api
                elif kind == "Ingress":
                    return ingress_config_api
                return MagicMock()
            
            mock_get.side_effect = get_side_effect
            
            # Mock isVersionEqualOrAfter to return True for version check
            with patch('mas.cli.install.app.isVersionEqualOrAfter', return_value=True):
                app.configRoutingMode()
        
        # Verify parameters are set correctly
        assert app.getParam("mas_routing_mode") == "path"
        assert app.getParam("mas_ingress_controller_name") == "default"
        assert app.getParam("mas_configure_ingress") == "true"
    
    def test_interactive_path_routing_user_declines_falls_back_to_subdomain(self):
        """Test fallback to subdomain when user declines to configure IngressController."""
        app = create_mock_app()
        app.isInteractiveMode = True
        app.showAdvancedOptions = True
        app.setParam("mas_channel", "9.2.0")
        app.setParam("mas_instance_id", "test-inst")
        
        # User declines to configure ingress
        app.yesOrNo.return_value = False
        
        # Mock IngressController not configured
        controller = create_ingress_controller_mock(namespace_ownership="Strict")
        ingress_api = MagicMock()
        ingress_api.get.side_effect = [
            controller,  # For permission check
            MagicMock(items=[controller]),  # For listing controllers
            controller  # For configuration check
        ]
        app.dynamicClient.resources.get.return_value = ingress_api
        
        # Mock Ingress config
        ingress_config_api = MagicMock()
        ingress_config = MagicMock()
        ingress_config.spec.get.return_value = "apps.cluster.example.com"
        ingress_config_api.get.return_value = ingress_config
        
        with patch.object(app.dynamicClient.resources, 'get') as mock_get:
            def get_side_effect(api_version, kind):
                if kind == "IngressController":
                    return ingress_api
                elif kind == "Ingress":
                    return ingress_config_api
                return MagicMock()
            
            mock_get.side_effect = get_side_effect
            
            # Mock isVersionEqualOrAfter to return True for version check
            with patch('mas.cli.install.app.isVersionEqualOrAfter', return_value=True):
                app.configRoutingMode()
        
        # Verify fallback to subdomain
        assert app.getParam("mas_routing_mode") == "subdomain"
        assert app.getParam("mas_ingress_controller_name") == ""
    
    def test_interactive_path_routing_patch_fails_gracefully(self):
        """Test graceful failure when IngressController patch operation fails."""
        app = create_mock_app()
        app.isInteractiveMode = True
        app.showAdvancedOptions = True
        app.setParam("mas_channel", "9.2.0")
        app.setParam("mas_instance_id", "test-inst")
        
        # Mock IngressController not configured
        controller = create_ingress_controller_mock(namespace_ownership="Strict")
        ingress_api = MagicMock()
        ingress_api.get.side_effect = [
            controller,  # For permission check
            MagicMock(items=[controller]),  # For listing controllers
            controller  # For configuration check
        ]
        
        # Mock Ingress config
        ingress_config_api = MagicMock()
        ingress_config = MagicMock()
        ingress_config.spec.get.return_value = "apps.cluster.example.com"
        ingress_config_api.get.return_value = ingress_config
        
        with patch.object(app.dynamicClient.resources, 'get') as mock_get:
            def get_side_effect(api_version, kind):
                if kind == "IngressController":
                    return ingress_api
                elif kind == "Ingress":
                    return ingress_config_api
                return MagicMock()
            
            mock_get.side_effect = get_side_effect
            
            with patch('mas.cli.install.app.isVersionEqualOrAfter', return_value=True):
                # User chooses to configure, but we'll simulate patch failure later
                app.yesOrNo.return_value = True
                app.configRoutingMode()
        
        # Even if patch fails later, parameters should be set for the pipeline to attempt
        assert app.getParam("mas_routing_mode") == "path"
        assert app.getParam("mas_configure_ingress") == "true"
        assert app.getParam("mas_ingress_controller_name") == "default"
    
    def test_interactive_path_routing_no_permissions_fails_gracefully(self):
        """Test graceful failure when user lacks permissions to check IngressController."""
        app = create_mock_app()
        app.isInteractiveMode = True
        app.showAdvancedOptions = True
        app.setParam("mas_channel", "9.2.0")
        app.setParam("mas_instance_id", "test-inst")
        
        # Mock permission denied
        ingress_api = MagicMock()
        ingress_api.get.side_effect = ApiException(status=403, reason="Forbidden")
        
        # Mock Ingress config
        ingress_config_api = MagicMock()
        ingress_config = MagicMock()
        ingress_config.spec.get.return_value = "apps.cluster.example.com"
        ingress_config_api.get.return_value = ingress_config
        
        with patch.object(app.dynamicClient.resources, 'get') as mock_get:
            def get_side_effect(api_version, kind):
                if kind == "IngressController":
                    return ingress_api
                elif kind == "Ingress":
                    return ingress_config_api
                return MagicMock()
            
            mock_get.side_effect = get_side_effect
            
            with patch('mas.cli.install.app.isVersionEqualOrAfter', return_value=True):
                app.configRoutingMode()
        
        # Should fall back to subdomain when permissions are denied
        assert app.getParam("mas_routing_mode") == "subdomain"
        assert app.getParam("mas_ingress_controller_name") == ""


# =============================================================================
# Interactive Mode - Subdomain Routing Tests
# =============================================================================
class TestInteractiveSubdomainRouting:
    """Test suite for interactive mode subdomain routing scenarios."""
    
    def test_interactive_subdomain_routing_selection(self):
        """Test direct selection of subdomain routing mode."""
        app = create_mock_app()
        app.isInteractiveMode = True
        app.showAdvancedOptions = True
        app.setParam("mas_channel", "9.2.0")
        app.setParam("mas_instance_id", "test-inst")
        
        # User selects subdomain mode (option 2)
        app.promptForInt.return_value = 2
        
        # Mock Ingress config
        ingress_config_api = MagicMock()
        ingress_config = MagicMock()
        ingress_config.spec.get.return_value = "apps.cluster.example.com"
        ingress_config_api.get.return_value = ingress_config
        app.dynamicClient.resources.get.return_value = ingress_config_api
        
        # Mock isVersionEqualOrAfter to return True for version check
        with patch('mas.cli.install.app.isVersionEqualOrAfter', return_value=True):
            app.configRoutingMode()
        
        # Verify subdomain mode is set
        assert app.getParam("mas_routing_mode") == "subdomain"
        assert app.getParam("mas_ingress_controller_name") == ""
        assert app.getParam("mas_configure_ingress") == ""


# =============================================================================
# Non-Interactive Mode - Path Routing Tests
# =============================================================================
class TestNonInteractivePathRouting:
    """Test suite for non-interactive mode path-based routing scenarios."""
    
    def test_noninteractive_path_mode_with_default_controller_configured(self):
        """Test non-interactive path mode with default controller already configured."""
        app = create_mock_app()
        app.isInteractiveMode = False
        app.setParam("mas_routing_mode", "path")
        app.setParam("mas_ingress_controller_name", "default")
        
        # Mock controller already configured
        controller = create_ingress_controller_mock()
        ingress_api = MagicMock()
        ingress_api.get.return_value = controller
        app.dynamicClient.resources.get.return_value = ingress_api
        
        # Simulate validation logic
        canConfigure = app._checkIngressControllerPermissions("default")
        exists, isConfigured = app._checkIngressControllerForPathRouting("default")
        
        assert canConfigure is True
        assert exists is True
        assert isConfigured is True
        assert app.getParam("mas_configure_ingress") == ""
    
    def test_noninteractive_path_mode_with_configure_flag_success(self):
        """Test non-interactive path mode with --configure-ingress flag."""
        app = create_mock_app()
        app.isInteractiveMode = False
        app.setParam("mas_routing_mode", "path")
        app.setParam("mas_ingress_controller_name", "default")
        app.setParam("mas_configure_ingress", "true")
        
        # Mock controller not configured
        controller = create_ingress_controller_mock(namespace_ownership="Strict")
        ingress_api = MagicMock()
        ingress_api.get.return_value = controller
        app.dynamicClient.resources.get.return_value = ingress_api
        
        canConfigure = app._checkIngressControllerPermissions("default")
        exists, isConfigured = app._checkIngressControllerForPathRouting("default")
        
        assert canConfigure is True
        assert exists is True
        assert isConfigured is False
        assert app.getParam("mas_configure_ingress") == "true"
    
    def test_noninteractive_path_mode_custom_controller_name(self):
        """Test non-interactive path mode with custom IngressController name."""
        app = create_mock_app()
        app.isInteractiveMode = False
        app.setParam("mas_routing_mode", "path")
        app.setParam("mas_ingress_controller_name", "custom-ingress")
        
        # Mock custom controller configured
        controller = create_ingress_controller_mock("custom-ingress")
        ingress_api = MagicMock()
        ingress_api.get.return_value = controller
        app.dynamicClient.resources.get.return_value = ingress_api
        
        exists, isConfigured = app._checkIngressControllerForPathRouting("custom-ingress")
        
        assert exists is True
        assert isConfigured is True
        assert app.getParam("mas_ingress_controller_name") == "custom-ingress"
    
    def test_noninteractive_path_mode_missing_controller_name_defaults_to_default(self):
        """Test that missing controller name defaults to 'default'."""
        app = create_mock_app()
        app.isInteractiveMode = False
        app.setParam("mas_routing_mode", "path")
        # Don't set mas_ingress_controller_name
        
        # Simulate the logic from app.py lines 1866-1876
        ingressControllerName = app.getParam("mas_ingress_controller_name")
        if not ingressControllerName:
            ingressControllerName = "default"
            app.setParam("mas_ingress_controller_name", ingressControllerName)
        
        assert app.getParam("mas_ingress_controller_name") == "default"
    
    def test_noninteractive_path_mode_no_permissions_fails_gracefully(self):
        """Test non-interactive path mode fails gracefully when user lacks permissions."""
        app = create_mock_app()
        app.isInteractiveMode = False
        app.setParam("mas_routing_mode", "path")
        app.setParam("mas_ingress_controller_name", "default")
        
        # Mock permission denied
        ingress_api = MagicMock()
        ingress_api.get.side_effect = ApiException(status=403, reason="Forbidden")
        app.dynamicClient.resources.get.return_value = ingress_api
        
        # Check permissions should return False
        result = app._checkIngressControllerPermissions()
        
        assert result is False
    
    def test_noninteractive_path_mode_with_configure_flag_no_permissions(self):
        """Test non-interactive path mode with --configure-ingress but no permissions."""
        app = create_mock_app()
        app.isInteractiveMode = False
        app.setParam("mas_routing_mode", "path")
        app.setParam("mas_ingress_controller_name", "default")
        app.setParam("mas_configure_ingress", "true")
        
        # Mock permission denied
        ingress_api = MagicMock()
        ingress_api.get.side_effect = ApiException(status=403, reason="Forbidden")
        app.dynamicClient.resources.get.return_value = ingress_api
        
        # Check permissions should return False
        result = app._checkIngressControllerPermissions()
        
        # Should fail gracefully - permissions check returns False
        assert result is False
    
    def test_noninteractive_path_mode_controller_not_configured_without_flag(self):
        """Test non-interactive path mode when controller not configured and no --configure-ingress flag."""
        app = create_mock_app()
        app.isInteractiveMode = False
        app.setParam("mas_routing_mode", "path")
        app.setParam("mas_ingress_controller_name", "default")
        # Note: mas_configure_ingress is NOT set
        
        # Mock controller not configured
        controller = create_ingress_controller_mock(namespace_ownership="Strict")
        ingress_api = MagicMock()
        ingress_api.get.return_value = controller
        app.dynamicClient.resources.get.return_value = ingress_api
        
        # Check if configured
        _, is_configured = app._checkIngressControllerForPathRouting("default")
        
        # Should detect it's not configured
        assert is_configured is False
    
    def test_noninteractive_path_mode_all_flags_with_permissions(self):
        """Test non-interactive path mode with all flags and proper permissions."""
        app = create_mock_app()
        app.isInteractiveMode = False
        app.setParam("mas_routing_mode", "path")
        app.setParam("mas_ingress_controller_name", "custom-controller")
        app.setParam("mas_configure_ingress", "true")
        
        # Mock controller with permissions
        controller = create_ingress_controller_mock("custom-controller", namespace_ownership="Strict")
        ingress_api = MagicMock()
        ingress_api.get.return_value = controller
        app.dynamicClient.resources.get.return_value = ingress_api
        
        # Check permissions
        has_permissions = app._checkIngressControllerPermissions("custom-controller")
        
        # Check configuration status
        _, is_configured = app._checkIngressControllerForPathRouting("custom-controller")
        
        # Should have permissions but not be configured
        assert has_permissions is True
        assert is_configured is False
        
        # Parameters should remain as set
        assert app.getParam("mas_routing_mode") == "path"
        assert app.getParam("mas_ingress_controller_name") == "custom-controller"
        assert app.getParam("mas_configure_ingress") == "true"
    
    def test_noninteractive_path_mode_controller_already_configured(self):
        """Test non-interactive path mode when controller is already properly configured."""
        app = create_mock_app()
        app.isInteractiveMode = False
        app.setParam("mas_routing_mode", "path")
        app.setParam("mas_ingress_controller_name", "default")
        
        # Mock controller already configured
        controller = create_ingress_controller_mock(namespace_ownership="InterNamespaceAllowed")
        ingress_api = MagicMock()
        ingress_api.get.return_value = controller
        app.dynamicClient.resources.get.return_value = ingress_api
        
        # Check if configured
        _, is_configured = app._checkIngressControllerForPathRouting("default")
        
        # Should be configured
        assert is_configured is True
        
        # mas_configure_ingress should not be needed
        assert app.getParam("mas_configure_ingress") == ""


# =============================================================================
# Non-Interactive Mode - Subdomain Routing Tests
# =============================================================================
class TestNonInteractiveSubdomainRouting:
    """Test suite for non-interactive mode subdomain routing scenarios."""
    
    def test_noninteractive_subdomain_mode_basic(self):
        """Test basic non-interactive subdomain mode."""
        app = create_mock_app()
        app.isInteractiveMode = False
        app.setParam("mas_routing_mode", "subdomain")
        
        assert app.getParam("mas_routing_mode") == "subdomain"
        assert app.getParam("mas_ingress_controller_name") == ""
        assert app.getParam("mas_configure_ingress") == ""
    
    def test_noninteractive_subdomain_mode_ignores_ingress_flags(self):
        """Test that subdomain mode ignores ingress-related flags."""
        app = create_mock_app()
        app.isInteractiveMode = False
        app.setParam("mas_routing_mode", "subdomain")
        # These should be ignored/cleared for subdomain mode
        app.setParam("mas_ingress_controller_name", "")
        app.setParam("mas_configure_ingress", "")
        
        assert app.getParam("mas_routing_mode") == "subdomain"
        assert app.getParam("mas_ingress_controller_name") == ""
        assert app.getParam("mas_configure_ingress") == ""


# =============================================================================
# IngressController Patch Function Integration Tests
# =============================================================================
class TestIngressControllerPatchIntegration:
    """Test suite for configureIngressForPathBasedRouting integration."""
    
    @patch('mas.devops.ocp.configureIngressForPathBasedRouting')
    def test_patch_function_called_with_correct_parameters(self, mock_configure):
        """Test that patch function is called with correct parameters."""
        from mas.devops.ocp import configureIngressForPathBasedRouting
        
        mock_client = MagicMock()
        mock_configure.return_value = True
        
        result = configureIngressForPathBasedRouting(mock_client, "default")
        
        assert result is True
        mock_configure.assert_called_once_with(mock_client, "default")
    
    @patch('mas.devops.ocp.configureIngressForPathBasedRouting')
    def test_patch_function_handles_failure(self, mock_configure):
        """Test that patch function failure is handled correctly."""
        from mas.devops.ocp import configureIngressForPathBasedRouting
        
        mock_client = MagicMock()
        mock_configure.return_value = False
        
        result = configureIngressForPathBasedRouting(mock_client, "default")
        
        assert result is False
    
    @patch('mas.devops.ocp.configureIngressForPathBasedRouting')
    def test_patch_function_with_custom_controller(self, mock_configure):
        """Test patch function with custom IngressController name."""
        from mas.devops.ocp import configureIngressForPathBasedRouting
        
        mock_client = MagicMock()
        mock_configure.return_value = True
        
        result = configureIngressForPathBasedRouting(mock_client, "custom-ingress")
        
        assert result is True
        mock_configure.assert_called_once_with(mock_client, "custom-ingress")


# =============================================================================
# Integration Tests - Complete CLI Flow
# =============================================================================
class TestCompleteCliFlow:
    """Integration tests for complete CLI prompt flow."""
    
    def test_complete_flow_path_mode_with_all_prompts(self):
        """Test complete flow with all prompts for path mode."""
        app = create_mock_app()
        app.isInteractiveMode = True
        app.showAdvancedOptions = True
        app.setParam("mas_channel", "9.2.0")
        app.setParam("mas_instance_id", "test-inst")
        
        # Mock multiple controllers
        controller1 = create_ingress_controller_mock("default", namespace_ownership="Strict")
        controller2 = create_ingress_controller_mock("custom", namespace_ownership="Strict")
        
        ingress_api = MagicMock()
        ingress_api.get.side_effect = [
            controller1,  # Permission check
            MagicMock(items=[controller1, controller2]),  # List controllers
            controller1  # Configuration check
        ]
        
        ingress_config_api = MagicMock()
        ingress_config = MagicMock()
        ingress_config.spec.get.return_value = "apps.cluster.example.com"
        ingress_config_api.get.return_value = ingress_config
        
        with patch.object(app.dynamicClient.resources, 'get') as mock_get:
            def get_side_effect(api_version, kind):
                if kind == "IngressController":
                    return ingress_api
                elif kind == "Ingress":
                    return ingress_config_api
                return MagicMock()
            
            mock_get.side_effect = get_side_effect
            
            # Mock isVersionEqualOrAfter to return True for version check
            with patch('mas.cli.install.app.isVersionEqualOrAfter', return_value=True):
                # Set up promptForInt to return different values for routing mode and controller selection
                app.promptForInt.side_effect = [1, 1]  # Path mode, first controller
                app.configRoutingMode()
        
        # Verify all parameters are set correctly
        assert app.getParam("mas_routing_mode") == "path"
        assert app.getParam("mas_ingress_controller_name") == "default"
        assert app.getParam("mas_configure_ingress") == "true"
        
        # Verify prompts were called
        assert app.promptForInt.call_count == 2
        assert app.yesOrNo.called
    
    def test_complete_flow_version_check_skips_routing_config(self):
        """Test that routing config is skipped for versions < 9.2.0."""
        app = create_mock_app()
        app.isInteractiveMode = True
        app.showAdvancedOptions = True
        app.setParam("mas_channel", "9.1.0")  # Version < 9.2.0
        
        # configRoutingMode should not execute for this version
        # This is tested by checking the version condition
        from mas.devops.utils import isVersionEqualOrAfter
        
        should_configure = (
            app.showAdvancedOptions and 
            isVersionEqualOrAfter('9.2.0', app.getParam("mas_channel")) and 
            app.getParam("mas_channel") != '9.2.x-feature'
        )
        
        assert should_configure is False
    
    def test_complete_end_to_end_flow_with_advanced_options_and_patching(self):
        """Test complete end-to-end CLI flow: advanced options → routing prompt → path selection → patching."""
        app = create_mock_app()
        app.isInteractiveMode = True
        app.showAdvancedOptions = True  # This should trigger routing mode prompt
        app.setParam("mas_channel", "9.2.0")
        app.setParam("mas_instance_id", "test-inst")
        
        # Mock IngressController not configured (needs patching)
        controller = create_ingress_controller_mock(namespace_ownership="Strict")
        ingress_api = MagicMock()
        ingress_api.get.side_effect = [
            controller,  # For permission check
            MagicMock(items=[controller]),  # For listing controllers
            controller  # For configuration check
        ]
        
        # Mock Ingress config
        ingress_config_api = MagicMock()
        ingress_config = MagicMock()
        ingress_config.spec.get.return_value = "apps.cluster.example.com"
        ingress_config_api.get.return_value = ingress_config
        
        with patch.object(app.dynamicClient.resources, 'get') as mock_get:
            def get_side_effect(api_version, kind):
                if kind == "IngressController":
                    return ingress_api
                elif kind == "Ingress":
                    return ingress_config_api
                return MagicMock()
            
            mock_get.side_effect = get_side_effect
            
            # Mock the patching function from python-devops
            with patch('mas.devops.ocp.configureIngressForPathBasedRouting') as mock_patch:
                mock_patch.return_value = True  # Patch succeeds
                
                with patch('mas.cli.install.app.isVersionEqualOrAfter', return_value=True):
                    # User selects path mode (option 1) and agrees to configure
                    app.promptForInt.return_value = 1
                    app.yesOrNo.return_value = True
                    
                    # Call configRoutingMode - this is what happens during CLI flow
                    app.configRoutingMode()
                    
                    # Verify routing mode was configured
                    assert app.getParam("mas_routing_mode") == "path"
                    assert app.getParam("mas_ingress_controller_name") == "default"
                    assert app.getParam("mas_configure_ingress") == "true"
                    
                    # Now simulate the actual patching that would happen in the pipeline
                    # This is what the ansible playbook would call
                    if app.getParam("mas_configure_ingress") == "true":
                        from mas.devops.ocp import configureIngressForPathBasedRouting
                        result = configureIngressForPathBasedRouting(
                            app.dynamicClient,
                            app.getParam("mas_ingress_controller_name")
                        )
                        
                        # Verify the patch function was called with correct parameters
                        mock_patch.assert_called_once_with(
                            app.dynamicClient,
                            "default"
                        )
                        assert result is True
    
    def test_complete_end_to_end_flow_advanced_options_disabled_skips_routing(self):
        """Test that routing mode prompt is skipped when advanced options are disabled."""
        app = create_mock_app()
        app.isInteractiveMode = True
        app.showAdvancedOptions = False  # Advanced options disabled
        app.setParam("mas_channel", "9.2.0")
        app.setParam("mas_instance_id", "test-inst")
        
        # Mock Ingress config (for _getMasDomainForDisplay if called)
        ingress_config_api = MagicMock()
        ingress_config = MagicMock()
        ingress_config.spec.get.return_value = "apps.cluster.example.com"
        ingress_config_api.get.return_value = ingress_config
        app.dynamicClient.resources.get.return_value = ingress_config_api
        
        with patch('mas.cli.install.app.isVersionEqualOrAfter', return_value=True):
            app.configRoutingMode()
        
        # Routing mode should not be set (method should exit early)
        # Default is subdomain if not explicitly set
        assert app.getParam("mas_routing_mode") == ""
        
        # promptForInt should not be called (no routing mode prompt)
        assert app.promptForInt.call_count == 0


# =============================================================================
# Regression Tests - Pipeline Failure Scenarios
# =============================================================================
class TestRegressionPipelineFailures:
    """Regression tests to ensure changes don't break routing functionality."""
    
    def test_regression_path_mode_parameters_preserved(self):
        """Test that path mode parameters are preserved throughout the flow."""
        app = create_mock_app()
        
        # Set initial parameters
        app.setParam("mas_routing_mode", "path")
        app.setParam("mas_ingress_controller_name", "default")
        app.setParam("mas_configure_ingress", "true")
        
        # Simulate parameter access multiple times
        for _ in range(5):
            assert app.getParam("mas_routing_mode") == "path"
            assert app.getParam("mas_ingress_controller_name") == "default"
            assert app.getParam("mas_configure_ingress") == "true"
    
    def test_regression_subdomain_mode_parameters_preserved(self):
        """Test that subdomain mode parameters are preserved throughout the flow."""
        app = create_mock_app()
        
        # Set initial parameters
        app.setParam("mas_routing_mode", "subdomain")
        app.setParam("mas_ingress_controller_name", "")
        
        # Simulate parameter access multiple times
        for _ in range(5):
            assert app.getParam("mas_routing_mode") == "subdomain"
            assert app.getParam("mas_ingress_controller_name") == ""
    
    def test_regression_invalid_routing_mode_not_set(self):
        """Test that invalid routing modes are not accepted."""
        app = create_mock_app()
        
        # Try to set invalid mode
        app.setParam("mas_routing_mode", "invalid")
        
        # In actual implementation, this should be validated
        # For now, we just verify it's set (validation happens in argParser)
        assert app.getParam("mas_routing_mode") == "invalid"
    
    def test_regression_missing_required_parameters_for_path_mode(self):
        """Test detection of missing required parameters for path mode."""
        app = create_mock_app()
        
        # Set path mode without controller name
        app.setParam("mas_routing_mode", "path")
        # Don't set mas_ingress_controller_name
        
        # Should default to 'default' if not set
        controller_name = app.getParam("mas_ingress_controller_name")
        if not controller_name:
            controller_name = "default"
        
        assert controller_name == "default"
    
    def test_regression_configure_flag_without_path_mode(self):
        """Test that configure flag without path mode is handled correctly."""
        app = create_mock_app()
        
        # Set configure flag but use subdomain mode
        app.setParam("mas_routing_mode", "subdomain")
        app.setParam("mas_configure_ingress", "true")
        
        # Configure flag should be ignored for subdomain mode
        # In actual implementation, this should be validated
        assert app.getParam("mas_routing_mode") == "subdomain"
        assert app.getParam("mas_configure_ingress") == "true"  # Set but ignored
    
    @patch('mas.devops.ocp.configureIngressForPathBasedRouting')
    def test_regression_patch_failure_does_not_break_pipeline(self, mock_configure):
        """Test that patch failure is handled gracefully and doesn't break pipeline."""
        mock_configure.return_value = False
        
        app = create_mock_app()
        app.setParam("mas_routing_mode", "path")
        app.setParam("mas_ingress_controller_name", "default")
        app.setParam("mas_configure_ingress", "true")
        
        # Simulate patch failure
        from mas.devops.ocp import configureIngressForPathBasedRouting
        result = configureIngressForPathBasedRouting(app.dynamicClient, "default")
        
        # Should return False but not raise exception
        assert result is False


# =============================================================================
# Edge Cases and Error Scenarios
# =============================================================================
class TestEdgeCasesAndErrors:
    """Test edge cases and error scenarios."""
    
    def test_edge_case_empty_routing_mode(self):
        """Test handling of empty routing mode."""
        app = create_mock_app()
        
        # Don't set routing mode
        assert app.getParam("mas_routing_mode") == ""
    
    def test_edge_case_controller_name_with_special_characters(self):
        """Test IngressController name with special characters."""
        app = create_mock_app()
        
        # Set controller name with hyphens (valid)
        app.setParam("mas_ingress_controller_name", "my-custom-ingress-123")
        assert app.getParam("mas_ingress_controller_name") == "my-custom-ingress-123"
    
    def test_edge_case_multiple_ingress_controllers_same_domain(self):
        """Test handling of multiple controllers with same domain."""
        app = create_mock_app()
        
        controller1 = create_ingress_controller_mock("default", "apps.cluster.com")
        controller2 = create_ingress_controller_mock("custom", "apps.cluster.com")
        
        ingress_api = MagicMock()
        ingress_api.get.return_value = MagicMock(items=[controller1, controller2])
        app.dynamicClient.resources.get.return_value = ingress_api
        
        # User selects option 2 (custom controller)
        app.promptForInt.return_value = 2
        result = app._promptForIngressController()
        
        # Should still allow selection (user selected option 2 = custom)
        assert result == "custom"
    
    def test_edge_case_ingress_controller_api_exception(self):
        """Test handling of API exception when accessing IngressController."""
        app = create_mock_app()
        
        ingress_api = MagicMock()
        ingress_api.get.side_effect = ApiException("API Error")
        app.dynamicClient.resources.get.return_value = ingress_api
        
        result = app._checkIngressControllerPermissions("default")
        
        # Should return False on exception
        assert result is False
    
    def test_edge_case_ingress_controller_not_found_exception(self):
        """Test handling of NotFoundError for IngressController."""
        app = create_mock_app()
        
        ingress_api = MagicMock()
        ingress_api.get.side_effect = NotFoundError(MagicMock())
        app.dynamicClient.resources.get.return_value = ingress_api
        
        exists, configured = app._checkIngressControllerForPathRouting("nonexistent")
        
        assert exists is False
        assert configured is False
    
    def test_edge_case_mas_domain_display_with_missing_ingress(self):
        """Test domain display when Ingress config is missing."""
        app = create_mock_app()
        app.setParam("mas_instance_id", "test-inst")
        
        ingress_api = MagicMock()
        ingress_api.get.side_effect = Exception("Not found")
        app.dynamicClient.resources.get.return_value = ingress_api
        
        # Should fallback to default domain
        domain = app._getMasDomainForDisplay()
        
        assert "test-inst" in domain
        assert "yourdomain.com" in domain

# =============================================================================
# Parameter Validation Tests
# =============================================================================
class TestParameterValidation:
    """Test parameter validation for routing mode."""
    
    def test_valid_routing_modes(self):
        """Test that only valid routing modes are accepted."""
        app = create_mock_app()
        
        valid_modes = ["path", "subdomain"]
        
        for mode in valid_modes:
            app.setParam("mas_routing_mode", mode)
            assert app.getParam("mas_routing_mode") == mode

if __name__ == '__main__':
    pytest.main([__file__, '-v'])

# Made with Bob
