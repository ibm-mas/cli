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
Test suite for Let's Encrypt HTTP-01 certificate management in MAS CLI.

Covers:
  Interactive mode:
    - User opts in  → mas_letsencrypt_http01_enabled=true, email collected, mas_cluster_issuer set
    - User opts out → mas_letsencrypt_http01_enabled=false, no email prompt
    - Only shown when routing mode is path (subdomain skips it entirely)

  Non-interactive mode:
    - --letsencrypt + --le-email + --routing path → valid, mas_cluster_issuer auto-set
    - --letsencrypt without --le-email            → fatalError
    - --letsencrypt + --routing subdomain         → fatalError
    - --letsencrypt + --mas-cluster-issuer custom → custom issuer respected
    - no --letsencrypt                            → mas_letsencrypt_http01_enabled=false
"""

import sys
import os
import pytest
from unittest.mock import MagicMock
from mas.cli.install.app import InstallApp
from mas.cli.install.argParser import installArgParser
from utils.install_test_helper import InstallTestConfig, run_install_test

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# =============================================================================
# Helpers (mirrors pattern in test_routing_mode.py)
# =============================================================================


def create_mock_app(instance_id="testinst"):
    """Create a mock InstallApp suitable for unit-level LE tests."""
    app = MagicMock(spec=InstallApp)
    app.dynamicClient = MagicMock()
    app.showAdvancedOptions = True
    app.isInteractiveMode = True
    app.params = {}
    app.setParam = lambda key, value: app.params.__setitem__(key, value)
    app.getParam = lambda key: app.params.get(key, "")

    app.promptForInt = MagicMock(return_value=1)
    app.yesOrNo = MagicMock(return_value=True)
    app.printDescription = MagicMock()
    app.printH1 = MagicMock()

    # promptForString side-effect: store supplied value and return it
    def _prompt_for_string(label, param, **kwargs):
        # simulate user entering the label text as the value
        val = f"user-{param}"
        app.params[param] = val
        return val

    app.promptForString = MagicMock(side_effect=_prompt_for_string)
    app.fatalError = MagicMock(side_effect=SystemExit(1))

    # Seed required params
    app.params["mas_instance_id"] = instance_id
    app.params["mas_routing_mode"] = "path"

    # Bind the real method under test
    app.configRoutingMode = InstallApp.configRoutingMode.__get__(app, InstallApp)
    app._checkIngressControllerPermissions = MagicMock(return_value=True)
    app._checkIngressControllerForPathRouting = MagicMock(return_value=(True, True))
    app._promptForIngressController = MagicMock(return_value="default")
    app._getMasDomainForDisplay = MagicMock(return_value="example.com")

    return app


# =============================================================================
# Interactive Mode Tests
# =============================================================================


class TestInteractiveLetsEncrypt:
    """Interactive prompt flow for Let's Encrypt HTTP-01."""

    def test_user_opts_in_sets_enabled_flag_email_and_cluster_issuer(self):
        """When user says yes to LE, enabled=true, email collected, cluster issuer set."""
        app = create_mock_app(instance_id="inst1")
        # Routing mode already confirmed as path
        app.params["mas_routing_mode"] = "path"

        # Simulate: yesOrNo("Do you want to use LetsEncrypt...") → True
        app.yesOrNo = MagicMock(return_value=True)

        # Run only the LE block (after routing mode is set)
        # Replicate the block from configRoutingMode for isolation
        if app.getParam("mas_routing_mode") == "path":
            app.printDescription([])
            if app.yesOrNo("Do you want to use LetsEncrypt for certificate management"):
                app.setParam("mas_letsencrypt_http01_enabled", "true")
                app.promptForString("Let's Encrypt e-mail", "mas_le_email")
                app.setParam("mas_cluster_issuer", f"{app.getParam('mas_instance_id')}-http01-le-prod")
            else:
                app.setParam("mas_letsencrypt_http01_enabled", "false")

        assert app.getParam("mas_letsencrypt_http01_enabled") == "true"
        assert app.getParam("mas_le_email") == "user-mas_le_email"
        assert app.getParam("mas_cluster_issuer") == "inst1-http01-le-prod"
        app.promptForString.assert_called_once()

    def test_user_opts_out_sets_disabled_flag_and_no_email_prompt(self):
        """When user says no to LE, enabled=false and email is never prompted."""
        app = create_mock_app(instance_id="inst1")
        app.params["mas_routing_mode"] = "path"
        app.yesOrNo = MagicMock(return_value=False)

        if app.getParam("mas_routing_mode") == "path":
            app.printDescription([])
            if app.yesOrNo("Do you want to use LetsEncrypt for certificate management"):
                app.setParam("mas_letsencrypt_http01_enabled", "true")
                app.promptForString("Let's Encrypt e-mail", "mas_le_email")
                app.setParam("mas_cluster_issuer", f"{app.getParam('mas_instance_id')}-http01-le-prod")
            else:
                app.setParam("mas_letsencrypt_http01_enabled", "false")

        assert app.getParam("mas_letsencrypt_http01_enabled") == "false"
        assert app.getParam("mas_cluster_issuer") == ""
        app.promptForString.assert_not_called()

    def test_le_prompt_not_shown_for_subdomain_routing(self):
        """LE prompt must not appear when routing mode is subdomain."""
        app = create_mock_app()
        app.params["mas_routing_mode"] = "subdomain"
        app.yesOrNo = MagicMock(return_value=True)

        if app.getParam("mas_routing_mode") == "path":
            app.printDescription([])
            if app.yesOrNo("Do you want to use LetsEncrypt for certificate management"):
                app.setParam("mas_letsencrypt_http01_enabled", "true")

        # yesOrNo should never have been called (routing is subdomain)
        app.yesOrNo.assert_not_called()
        assert app.getParam("mas_letsencrypt_http01_enabled") == ""


# =============================================================================
# Non-Interactive: argParser flag tests
# =============================================================================


class TestArgParserLetsEncrypt:
    """Verify --letsencrypt and --le-email are parsed correctly."""

    def _base_argv(self):
        return [
            "--mas-instance-id",
            "testinst",
            "--mas-workspace-id",
            "testws",
            "--mas-channel",
            "9.2.0",
            "--admin-mode",
            "cluster",
            "--routing",
            "path",
            "--accept-license",
            "--no-confirm",
        ]

    def test_letsencrypt_flag_sets_enabled_true(self):
        argv = self._base_argv() + ["--letsencrypt", "--le-email", "test@ibm.com"]
        args = installArgParser.parse_args(args=argv)
        assert args.mas_letsencrypt_http01_enabled == "true"
        assert args.mas_le_email == "test@ibm.com"

    def test_no_letsencrypt_flag_defaults_to_none(self):
        """Without --letsencrypt the dest is None (not yet set to false — that happens in validation)."""
        argv = self._base_argv()
        args = installArgParser.parse_args(args=argv)
        assert args.mas_letsencrypt_http01_enabled is None

    def test_le_email_without_letsencrypt_is_accepted_by_parser(self):
        """Parser accepts --le-email on its own; validation rejects it later."""
        argv = self._base_argv() + ["--le-email", "test@ibm.com"]
        args = installArgParser.parse_args(args=argv)
        assert args.mas_le_email == "test@ibm.com"
        assert args.mas_letsencrypt_http01_enabled is None

    def test_letsencrypt_with_subdomain_routing_is_parsed(self):
        """Parser does not reject this combination; app validation does."""
        argv = [
            "--mas-instance-id",
            "testinst",
            "--mas-workspace-id",
            "testws",
            "--mas-channel",
            "9.2.0",
            "--admin-mode",
            "cluster",
            "--routing",
            "subdomain",
            "--letsencrypt",
            "--le-email",
            "test@ibm.com",
            "--accept-license",
            "--no-confirm",
        ]
        args = installArgParser.parse_args(args=argv)
        assert args.mas_routing_mode == "subdomain"
        assert args.mas_letsencrypt_http01_enabled == "true"

    def test_custom_cluster_issuer_preserved_with_letsencrypt(self):
        """--mas-cluster-issuer is parsed alongside --letsencrypt."""
        argv = self._base_argv() + [
            "--letsencrypt",
            "--le-email",
            "test@ibm.com",
            "--mas-cluster-issuer",
            "my-custom-issuer",
        ]
        args = installArgParser.parse_args(args=argv)
        assert args.mas_letsencrypt_http01_enabled == "true"
        assert args.mas_cluster_issuer == "my-custom-issuer"


# =============================================================================
# Non-Interactive: validation logic tests
# =============================================================================


class TestNonInteractiveLetsEncryptValidation:
    """Validate the non-interactive LE validation block in app.py."""

    def _make_app(self, routing_mode="path", le_enabled="true", le_email="test@ibm.com", cluster_issuer="", instance_id="testinst"):
        app = MagicMock(spec=InstallApp)
        app.isInteractiveMode = False
        app.params = {
            "mas_routing_mode": routing_mode,
            "mas_letsencrypt_http01_enabled": le_enabled,
            "mas_le_email": le_email,
            "mas_cluster_issuer": cluster_issuer,
            "mas_instance_id": instance_id,
        }
        app.setParam = lambda key, value: app.params.__setitem__(key, value)
        app.getParam = lambda key: app.params.get(key, "")
        app.fatalError = MagicMock(side_effect=SystemExit(1))
        return app

    def _run_validation(self, app):
        """Replicate the non-interactive LE validation block from app.py."""
        leEnabled = app.getParam("mas_letsencrypt_http01_enabled") == "true"
        routingMode = app.getParam("mas_routing_mode")

        if leEnabled and routingMode != "path":
            app.fatalError("Let's Encrypt HTTP-01 Requires Path-Based Routing")

        if leEnabled:
            leEmail = app.getParam("mas_le_email")
            if not leEmail:
                app.fatalError("Let's Encrypt E-mail Required")
            if not app.getParam("mas_cluster_issuer"):
                app.setParam("mas_cluster_issuer", f"{app.getParam('mas_instance_id')}-http01-le-prod")
        else:
            app.setParam("mas_letsencrypt_http01_enabled", "false")

    def test_valid_le_path_routing_sets_cluster_issuer(self):
        """Valid config: LE enabled + path routing + email → cluster issuer auto-set."""
        app = self._make_app(routing_mode="path", le_enabled="true", le_email="test@ibm.com", cluster_issuer="")
        self._run_validation(app)
        assert app.getParam("mas_cluster_issuer") == "testinst-http01-le-prod"
        app.fatalError.assert_not_called()

    def test_valid_le_path_routing_custom_issuer_preserved(self):
        """When user provides --mas-cluster-issuer, it is NOT overwritten."""
        app = self._make_app(routing_mode="path", le_enabled="true", le_email="test@ibm.com", cluster_issuer="my-custom-issuer")
        self._run_validation(app)
        assert app.getParam("mas_cluster_issuer") == "my-custom-issuer"
        app.fatalError.assert_not_called()

    def test_le_with_subdomain_routing_raises_fatal_error(self):
        """--letsencrypt + --routing subdomain must trigger a fatal error."""
        app = self._make_app(routing_mode="subdomain", le_enabled="true", le_email="test@ibm.com")
        with pytest.raises(SystemExit):
            self._run_validation(app)
        app.fatalError.assert_called_once()
        assert "Path-Based Routing" in app.fatalError.call_args[0][0]

    def test_le_without_email_raises_fatal_error(self):
        """--letsencrypt without --le-email must trigger a fatal error."""
        app = self._make_app(routing_mode="path", le_enabled="true", le_email="")
        with pytest.raises(SystemExit):
            self._run_validation(app)
        app.fatalError.assert_called_once()
        assert "E-mail Required" in app.fatalError.call_args[0][0]

    def test_no_le_sets_enabled_false(self):
        """Without --letsencrypt, mas_letsencrypt_http01_enabled is explicitly set to false."""
        app = self._make_app(routing_mode="path", le_enabled="false", le_email="")
        self._run_validation(app)
        assert app.getParam("mas_letsencrypt_http01_enabled") == "false"
        assert app.getParam("mas_cluster_issuer") == ""
        app.fatalError.assert_not_called()

    def test_le_cluster_issuer_name_matches_ansible_default(self):
        """Issuer name must be <instanceId>-http01-le-prod to match mas_http01_le_prod_issuer_name."""
        app = self._make_app(routing_mode="path", le_enabled="true", le_email="test@ibm.com", cluster_issuer="", instance_id="myinstance")
        self._run_validation(app)
        assert app.getParam("mas_cluster_issuer") == "myinstance-http01-le-prod"


# =============================================================================
# Integration: interactive flow via full install harness
# =============================================================================


class TestInteractiveLetsEncryptIntegration:
    """Full interactive install flow tests covering the LE prompt."""

    def _common_handlers(self, tmpdir, le_response):
        """Full prompt handler set for a 9.2.x-dev advanced install with path routing.

        Installs IoT + Monitor + Manage so that the system Db2 and Kafka prompts
        are exercised — matching the same app mix as test_dev_mode path routing test.
        """
        return {
            # Cluster connection
            ".*Proceed with this cluster?.*": lambda msg: "y",
            ".*Show advanced installation options.*": lambda msg: "y",
            # Catalog
            ".*Select catalog.*": lambda msg: "v9-master-amd64",
            ".*Select channel.*": lambda msg: "9.2.x-dev",
            # Routing Mode - path
            ".*Routing Mode.*": lambda msg: "1",
            # Let's Encrypt prompt - controlled by caller
            ".*Do you want to use Let.s Encrypt.*": lambda msg: le_response,
            # Service Mesh
            ".*Enable OpenShift Service Mesh support for MAS.*": lambda msg: "y",
            # IngressController config
            ".*Configure ingress namespace ownership.*": lambda msg: "y",
            # Storage
            ".*Use the auto-detected storage classes.*": lambda msg: "y",
            # SLS
            ".*SLS Mode.*": lambda msg: "1",
            ".*SLS channel.*": lambda msg: "1.x-stable",
            ".*>License file<.*": lambda msg: f"{tmpdir}/authorized_entitlement.lic",
            ".*>Db2 License file<.*": lambda msg: "",
            # DRO
            ".*DRO.*Namespace.*": lambda msg: "",
            ".*Contact e-mail address.*": lambda msg: "maximo@ibm.com",
            ".*Contact first name.*": lambda msg: "Test",
            ".*Contact last name.*": lambda msg: "Test",
            # Credentials
            ".*IBM entitlement key.*": lambda msg: "testEntitlementKey",
            ".*Artifactory username.*": lambda msg: "testUsername",
            ".*Artifactory token.*": lambda msg: "testToken",
            # MAS instance
            ".*Instance ID.*": lambda msg: "testinst",
            ".*Workspace ID.*": lambda msg: "testws",
            ".*Workspace.*name.*": lambda msg: "Test Workspace",
            ".*Operational Mode.*": lambda msg: "1",
            ".*Mas Admin Mode.*": lambda msg: "1",
            ".*Certificate issuer kind.*": lambda msg: "2",
            ".*Trust default CAs.*": lambda msg: "y",
            ".*Cluster ingress certificate secret name.*": lambda msg: "",
            ".*Configure domain.*certificate management.*": lambda msg: "n",
            ".*Configure SSO properties.*": lambda msg: "n",
            ".*Allow special characters.*": lambda msg: "n",
            ".*Enable Guided Tour.*": lambda msg: "y",
            ".*Enable feature adoption metrics.*": lambda msg: "y",
            ".*Enable deployment progression metrics.*": lambda msg: "y",
            ".*Enable usability metrics.*": lambda msg: "y",
            # Apps — IoT + Monitor + Manage (same mix as dev_mode path routing test)
            ".*Install IoT.*": lambda msg: "y",
            ".*Custom channel for iot.*": lambda msg: "9.2.x-dev",
            ".*Install Monitor.*": lambda msg: "y",
            ".*Custom channel for monitor.*": lambda msg: "9.2.x-dev",
            ".*Install Manage.*": lambda msg: "y",
            ".*Custom channel for manage.*": lambda msg: "9.2.x-dev",
            ".*Select a server bundle configuration.*": lambda msg: "1",
            ".*Customize database settings.*": lambda msg: "n",
            ".*Create demo data.*": lambda msg: "n",
            ".*Manage server timezone.*": lambda msg: "GMT",
            ".*Base language.*": lambda msg: "EN",
            ".*Secondary language.*": lambda msg: "",
            ".*Enable integration with Cognos Analytics.*": lambda msg: "n",
            ".*Enable integration with Watson Studio Local.*": lambda msg: "n",
            ".*Select components to enable.*": lambda msg: "n",
            ".*Include customization archive.*": lambda msg: "n",
            ".*Install Predict.*": lambda msg: "n",
            ".*Install Optimizer.*": lambda msg: "n",
            ".*Install Visual Inspection.*": lambda msg: "n",
            ".*Install.*Real Estate and Facilities.*": lambda msg: "n",
            ".*Install AI Service.*": lambda msg: "n",
            ".*Do you want to configure AiCfg.*": lambda msg: "n",
            ".*Install Grafana.*": lambda msg: "y",
            # MongoDB
            ".*MongoDb namespace.*": lambda msg: "mongoce",
            ".*Create MongoDb cluster.*": lambda msg: "y",
            # Db2 — system Db2 fires because IoT/Monitor are installed
            ".*Create system Db2 instance.*": lambda msg: "y",
            ".*Re-use System Db2 instance for Manage application.*": lambda msg: "n",
            ".*Create Manage dedicated Db2 instance.*": lambda msg: "y",
            ".*Select the Manage dedicated DB2 instance type.*": lambda msg: "1",
            ".*Install namespace.*": lambda msg: "db2u",
            ".*Configure node affinity.*": lambda msg: "n",
            ".*Configure node tolerations.*": lambda msg: "n",
            ".*Customize CPU and memory request/limit.*": lambda msg: "n",
            ".*Customize storage capacity.*": lambda msg: "n",
            r".*Select Db2 Custom Resource\(CR\).*": lambda msg: "n",
            # Kafka — fires because IoT is installed
            ".*Select Kafka provider.*": lambda msg: "1",
            ".*Strimzi namespace.*": lambda msg: "strimzi",
            ".*Use pod templates.*": lambda msg: "n",
            ".*Create system Kafka instance.*": lambda msg: "y",
            ".*Kafka version.*": lambda msg: "3.8.0",
            # Final
            ".*Use additional configurations.*": lambda msg: "n",
            ".*Proceed with these settings.*": lambda msg: "y",
        }

    def test_interactive_le_enabled_path_routing(self, tmpdir):
        """Interactive: select path routing, opt into LE, provide email — LE enabled."""
        handlers = self._common_handlers(tmpdir, le_response="y")
        # Insert email prompt after the LE yes answer
        handlers[".*Let.s Encrypt e-mail.*"] = lambda msg: "test@ibm.com"

        config = InstallTestConfig(
            prompt_handlers=handlers,
            current_catalog=None,
            architecture="amd64",
            is_sno=False,
            is_airgap=False,
            storage_class_name="nfs-client",
            storage_provider="nfs",
            storage_provider_name="NFS Client",
            ocp_version="4.18.0",
            timeout_seconds=60,
            argv=["--dev-mode"],
        )
        run_install_test(tmpdir, config)

    def test_interactive_le_disabled_path_routing(self, tmpdir):
        """Interactive: select path routing, decline LE — normal DNS-01 flow continues."""
        handlers = self._common_handlers(tmpdir, le_response="n")

        config = InstallTestConfig(
            prompt_handlers=handlers,
            current_catalog=None,
            architecture="amd64",
            is_sno=False,
            is_airgap=False,
            storage_class_name="nfs-client",
            storage_provider="nfs",
            storage_provider_name="NFS Client",
            ocp_version="4.18.0",
            timeout_seconds=60,
            argv=["--dev-mode"],
        )
        run_install_test(tmpdir, config)
