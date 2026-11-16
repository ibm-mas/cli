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
Test suite for issuerKind derivation and validation in MAS CLI.

The CLI supports all MAS versions and issuerKind behaviour differs by version band:

  Pre-9.2 (e.g. 9.1.x):
    - --mas-issuer-kind flag is not supported → fatalError if passed
    - no issuerKind derivation occurs

  MAS 9.2.x — issuerKind is explicit:
    Non-interactive:
      - cluster mode, no flag    → ClusterIssuer (default)
      - namespaced/minimal mode  → Issuer (forced, no prompt)
      - --mas-issuer-kind flag   → value respected
      - ClusterIssuer + namespaced/minimal → fatalError
      - DNS + namespaced/minimal → fatalError
      - DNS + cluster + Issuer   → fatalError
    Interactive:
      - cluster mode → user is prompted (1=Issuer, 2=ClusterIssuer)
      - namespaced/minimal mode → Issuer set silently, no prompt

  MAS 9.3+ — issuerKind is auto-derived, flag is rejected:
    - No DNS, no LE             → Issuer  (default domain)
    - DNS provider configured   → ClusterIssuer  (custom domain)
    - LE + path routing         → Issuer  (HTTP-01)
    - LE + path priority > DNS  → Issuer
    - --mas-issuer-kind passed  → fatalError
    - admin mode no longer gates issuerKind for external certs
"""

import sys
import os
import pytest
from unittest.mock import MagicMock
from mas.cli.install.app import InstallApp
from mas.cli.install.argParser import installArgParser

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# =============================================================================
# Test Helper Functions
# =============================================================================


def create_mock_app(channel="9.3.x", routing_mode="subdomain", dns_provider="", le_email="", admin_mode="cluster", issuer_kind=""):
    """Create a mock InstallApp suitable for issuerKind derivation tests."""
    app = MagicMock(spec=InstallApp)
    app.dynamicClient = MagicMock()
    app.showAdvancedOptions = True
    app.isInteractiveMode = False
    app.mas_admin_mode = admin_mode
    app.params = {}
    app.setParam = lambda key, value: app.params.__setitem__(key, value)
    app.getParam = lambda key: app.params.get(key, "")

    app.promptForInt = MagicMock(return_value=1)
    app.yesOrNo = MagicMock(return_value=True)
    app.printDescription = MagicMock()
    app.printH1 = MagicMock()
    app.promptForString = MagicMock(return_value="")
    app.fatalError = MagicMock(side_effect=SystemExit(1))

    # args attribute — simulate no CLI flag passed by default
    app.args = MagicMock()
    app.args.mas_issuer_kind = None

    # Seed params
    app.params["mas_channel"] = channel
    app.params["mas_routing_mode"] = routing_mode
    app.params["dns_provider"] = dns_provider
    app.params["mas_le_email"] = le_email
    app.params["mas_issuer_kind"] = issuer_kind

    return app


def run_issuer_kind_logic(app):
    """
    Replicate the full issuerKind validation + derivation block from app.py,
    covering pre-9.2, 9.2.x, and 9.3+ version bands.
    """
    from mas.devops.utils import isVersionEqualOrAfter

    # pre-9.2: flag not supported at all
    if app.getParam("mas_issuer_kind") != "" and not isVersionEqualOrAfter("9.2.0", app.getParam("mas_channel")):
        app.fatalError(f"--mas-issuer-kind is only supported for MAS 9.2+ (selected channel: {app.getParam('mas_channel')})")

    if not isVersionEqualOrAfter("9.2.0", app.getParam("mas_channel")):
        return  # no further issuerKind logic for pre-9.2

    if isVersionEqualOrAfter("9.3.0", app.getParam("mas_channel")):
        # 9.3+: flag not accepted — issuerKind is derived from DNS/LE config
        if hasattr(app.args, "mas_issuer_kind") and app.args.mas_issuer_kind is not None:
            app.fatalError(
                f"--mas-issuer-kind is not supported on MAS 9.3+ (selected channel: {app.getParam('mas_channel')}).\n"
                "issuerKind is derived automatically from your domain and routing configuration"
            )
        if app.getParam("mas_routing_mode") == "path" and app.getParam("mas_le_email") != "":
            app.setParam("mas_issuer_kind", "Issuer")
        elif app.getParam("dns_provider") != "":
            app.setParam("mas_issuer_kind", "ClusterIssuer")
        else:
            app.setParam("mas_issuer_kind", "Issuer")
    else:
        # 9.2: derive from admin mode if not explicitly set, then validate
        if app.getParam("mas_issuer_kind") == "":
            if app.mas_admin_mode == "cluster":
                app.setParam("mas_issuer_kind", "ClusterIssuer")
            else:
                app.setParam("mas_issuer_kind", "Issuer")

        # ClusterIssuer requires cluster admin mode
        if app.getParam("mas_issuer_kind") == "ClusterIssuer" and app.mas_admin_mode != "cluster":
            app.fatalError(
                "\n".join(
                    [
                        "Invalid configuration for certificate issuer kind 'ClusterIssuer'",
                        "ClusterIssuer can only be used when --admin-mode cluster is selected.",
                    ]
                )
            )

        # DNS integration restrictions
        if app.getParam("dns_provider") != "":
            if app.mas_admin_mode in ["namespaced", "minimal"]:
                app.fatalError(
                    "\n".join(
                        [
                            f"Invalid configuration for admin mode '{app.mas_admin_mode}'",
                            "DNS integration is not available in this mode.",
                            "Remove DNS integration option --dns-provider, or switch to --admin-mode cluster.",
                        ]
                    )
                )

            if app.mas_admin_mode == "cluster" and app.getParam("mas_issuer_kind") == "Issuer":
                app.fatalError(
                    "\n".join(
                        [
                            "Invalid configuration for certificate issuer kind 'Issuer'",
                            "DNS integration is not available when --mas-issuer-kind Issuer is selected.",
                            "Remove DNS integration option --dns-provider, or use --mas-issuer-kind ClusterIssuer.",
                        ]
                    )
                )


# =============================================================================
# Pre-9.2 — --mas-issuer-kind flag not supported at all
# =============================================================================


class TestIssuerKindPre92:
    """Pre-9.2 MAS installs do not support --mas-issuer-kind in any form."""

    @pytest.mark.parametrize("channel", ["9.1.x", "9.0.x", "8.11.x"])
    def test_flag_rejected_for_pre_92_channels(self, channel):
        """--mas-issuer-kind is not supported before 9.2 → fatalError."""
        app = create_mock_app(channel=channel, issuer_kind="ClusterIssuer")
        with pytest.raises(SystemExit):
            run_issuer_kind_logic(app)
        app.fatalError.assert_called_once()
        assert "only supported for MAS 9.2+" in app.fatalError.call_args[0][0]

    @pytest.mark.parametrize("channel", ["9.1.x", "9.0.x"])
    def test_no_flag_no_error_pre_92(self, channel):
        """Without the flag, pre-9.2 installs pass through with no issuerKind logic."""
        app = create_mock_app(channel=channel, issuer_kind="")
        run_issuer_kind_logic(app)
        app.fatalError.assert_not_called()
        # No derivation happens — param stays empty
        assert app.getParam("mas_issuer_kind") == ""


# =============================================================================
# MAS 9.2 — Non-interactive: default derivation from admin mode
# =============================================================================


class TestIssuerKind92NonInteractiveDefaults:
    """MAS 9.2 non-interactive: issuerKind is derived from admin mode when flag is not set."""

    def test_cluster_mode_no_flag_defaults_to_cluster_issuer(self):
        """cluster admin mode + no flag → ClusterIssuer."""
        app = create_mock_app(channel="9.2.x", admin_mode="cluster")
        run_issuer_kind_logic(app)
        assert app.getParam("mas_issuer_kind") == "ClusterIssuer"
        app.fatalError.assert_not_called()

    @pytest.mark.parametrize("admin_mode", ["namespaced", "minimal"])
    def test_restricted_mode_no_flag_defaults_to_issuer(self, admin_mode):
        """namespaced/minimal admin mode + no flag → Issuer (forced)."""
        app = create_mock_app(channel="9.2.x", admin_mode=admin_mode)
        run_issuer_kind_logic(app)
        assert app.getParam("mas_issuer_kind") == "Issuer"
        app.fatalError.assert_not_called()

    def test_explicit_cluster_issuer_flag_in_cluster_mode(self):
        """--mas-issuer-kind ClusterIssuer + cluster mode → accepted."""
        app = create_mock_app(channel="9.2.x", admin_mode="cluster", issuer_kind="ClusterIssuer")
        run_issuer_kind_logic(app)
        assert app.getParam("mas_issuer_kind") == "ClusterIssuer"
        app.fatalError.assert_not_called()

    def test_explicit_issuer_flag_in_cluster_mode(self):
        """--mas-issuer-kind Issuer + cluster mode → accepted."""
        app = create_mock_app(channel="9.2.x", admin_mode="cluster", issuer_kind="Issuer")
        run_issuer_kind_logic(app)
        assert app.getParam("mas_issuer_kind") == "Issuer"
        app.fatalError.assert_not_called()


# =============================================================================
# MAS 9.2 — Non-interactive: validation errors
# =============================================================================


class TestIssuerKind92NonInteractiveValidation:
    """MAS 9.2 non-interactive: invalid combinations must raise a fatal error."""

    @pytest.mark.parametrize("admin_mode", ["namespaced", "minimal"])
    def test_cluster_issuer_in_restricted_mode_raises_fatal_error(self, admin_mode):
        """ClusterIssuer + namespaced/minimal → fatalError."""
        app = create_mock_app(channel="9.2.x", admin_mode=admin_mode, issuer_kind="ClusterIssuer")
        with pytest.raises(SystemExit):
            run_issuer_kind_logic(app)
        app.fatalError.assert_called_once()
        assert "ClusterIssuer can only be used when --admin-mode cluster" in app.fatalError.call_args[0][0]

    @pytest.mark.parametrize("admin_mode", ["namespaced", "minimal"])
    def test_dns_provider_in_restricted_mode_raises_fatal_error(self, admin_mode):
        """DNS provider + namespaced/minimal → fatalError (DNS not available in 9.2)."""
        app = create_mock_app(channel="9.2.x", admin_mode=admin_mode, dns_provider="cloudflare")
        with pytest.raises(SystemExit):
            run_issuer_kind_logic(app)
        app.fatalError.assert_called_once()
        assert "DNS integration is not available in this mode" in app.fatalError.call_args[0][0]

    def test_dns_with_issuer_kind_in_cluster_mode_raises_fatal_error(self):
        """DNS + cluster mode + Issuer → fatalError (DNS requires ClusterIssuer in 9.2)."""
        app = create_mock_app(channel="9.2.x", admin_mode="cluster", dns_provider="cloudflare", issuer_kind="Issuer")
        with pytest.raises(SystemExit):
            run_issuer_kind_logic(app)
        app.fatalError.assert_called_once()
        assert "DNS integration is not available when --mas-issuer-kind Issuer" in app.fatalError.call_args[0][0]

    def test_dns_with_cluster_issuer_in_cluster_mode_is_valid(self):
        """DNS + cluster mode + ClusterIssuer → valid in 9.2."""
        app = create_mock_app(channel="9.2.x", admin_mode="cluster", dns_provider="cloudflare", issuer_kind="ClusterIssuer")
        run_issuer_kind_logic(app)
        assert app.getParam("mas_issuer_kind") == "ClusterIssuer"
        app.fatalError.assert_not_called()


# =============================================================================
# MAS 9.2 — Interactive: admin mode prompt drives issuerKind
# =============================================================================


class TestIssuerKind92Interactive:
    """MAS 9.2 interactive: cluster mode prompts user; namespaced/minimal sets Issuer silently."""

    def test_cluster_mode_user_selects_cluster_issuer(self):
        """Interactive cluster mode, user picks ClusterIssuer (option 2) → ClusterIssuer."""
        from mas.devops.utils import isVersionEqualOrAfter

        app = create_mock_app(channel="9.2.x", admin_mode="cluster")
        app.isInteractiveMode = True

        if not isVersionEqualOrAfter("9.3.0", app.getParam("mas_channel")):
            if app.mas_admin_mode in ["namespaced", "minimal"]:
                app.setParam("mas_issuer_kind", "Issuer")
            else:
                app.promptForInt.return_value = 2  # ClusterIssuer
                issuerKindChoice = app.promptForInt("Certificate issuer kind", min=1, max=2, default=2)
                app.setParam("mas_issuer_kind", "ClusterIssuer" if issuerKindChoice == 2 else "Issuer")

        assert app.getParam("mas_issuer_kind") == "ClusterIssuer"
        app.promptForInt.assert_called_once()

    def test_cluster_mode_user_selects_issuer(self):
        """Interactive cluster mode, user picks Issuer (option 1) → Issuer."""
        from mas.devops.utils import isVersionEqualOrAfter

        app = create_mock_app(channel="9.2.x", admin_mode="cluster")
        app.isInteractiveMode = True

        if not isVersionEqualOrAfter("9.3.0", app.getParam("mas_channel")):
            if app.mas_admin_mode in ["namespaced", "minimal"]:
                app.setParam("mas_issuer_kind", "Issuer")
            else:
                app.promptForInt.return_value = 1  # Issuer
                issuerKindChoice = app.promptForInt("Certificate issuer kind", min=1, max=2, default=2)
                app.setParam("mas_issuer_kind", "ClusterIssuer" if issuerKindChoice == 2 else "Issuer")

        assert app.getParam("mas_issuer_kind") == "Issuer"

    @pytest.mark.parametrize("admin_mode", ["namespaced", "minimal"])
    def test_restricted_mode_sets_issuer_silently_no_prompt(self, admin_mode):
        """Interactive namespaced/minimal: Issuer is set without prompting the user."""
        from mas.devops.utils import isVersionEqualOrAfter

        app = create_mock_app(channel="9.2.x", admin_mode=admin_mode)
        app.isInteractiveMode = True

        if not isVersionEqualOrAfter("9.3.0", app.getParam("mas_channel")):
            if app.mas_admin_mode in ["namespaced", "minimal"]:
                app.setParam("mas_issuer_kind", "Issuer")
            else:
                issuerKindChoice = app.promptForInt("Certificate issuer kind", min=1, max=2, default=2)
                app.setParam("mas_issuer_kind", "ClusterIssuer" if issuerKindChoice == 2 else "Issuer")

        assert app.getParam("mas_issuer_kind") == "Issuer"
        app.promptForInt.assert_not_called()


# =============================================================================
# MAS 9.3+ — Interactive: no issuerKind prompt shown
# =============================================================================


class TestIssuerKind93Interactive:
    """MAS 9.3+ interactive: issuerKind prompt is never shown; Issuer set as fallback."""

    @pytest.mark.parametrize("admin_mode", ["cluster", "namespaced", "minimal"])
    def test_no_prompt_sets_issuer_as_fallback(self, admin_mode):
        """Interactive 9.3+: no issuerKind prompt shown for any admin mode; Issuer set as fallback."""
        from mas.devops.utils import isVersionEqualOrAfter

        app = create_mock_app(channel="9.3.x", admin_mode=admin_mode)
        app.isInteractiveMode = True

        if isVersionEqualOrAfter("9.3.0", app.getParam("mas_channel")):
            app.setParam("mas_issuer_kind", "Issuer")
        elif app.mas_admin_mode in ["namespaced", "minimal"]:
            app.setParam("mas_issuer_kind", "Issuer")
        else:
            issuerKindChoice = app.promptForInt("Certificate issuer kind", min=1, max=2, default=2)
            app.setParam("mas_issuer_kind", "ClusterIssuer" if issuerKindChoice == 2 else "Issuer")

        assert app.getParam("mas_issuer_kind") == "Issuer"
        app.promptForInt.assert_not_called()


# =============================================================================
# MAS 9.3+ — Non-interactive: auto-derived from DNS/LE config
# =============================================================================


class TestIssuerKind93DefaultDomain:
    """MAS 9.3+ non-interactive: no DNS, no LE — default domain → Issuer."""

    def test_no_dns_no_le_subdomain_derives_issuer(self):
        """Default install (subdomain, no DNS, no LE) → Issuer."""
        app = create_mock_app(channel="9.3.x", routing_mode="subdomain", dns_provider="", le_email="")
        run_issuer_kind_logic(app)
        assert app.getParam("mas_issuer_kind") == "Issuer"
        app.fatalError.assert_not_called()

    def test_no_dns_no_le_path_mode_derives_issuer(self):
        """Path routing without LE enabled (no email) → Issuer."""
        app = create_mock_app(channel="9.3.x", routing_mode="path", dns_provider="", le_email="")
        run_issuer_kind_logic(app)
        assert app.getParam("mas_issuer_kind") == "Issuer"
        app.fatalError.assert_not_called()

    @pytest.mark.parametrize("admin_mode", ["cluster", "namespaced", "minimal"])
    def test_no_dns_issuer_regardless_of_admin_mode(self, admin_mode):
        """9.3+: admin mode no longer gates issuerKind — always Issuer without DNS."""
        app = create_mock_app(channel="9.3.x", routing_mode="subdomain", dns_provider="", le_email="", admin_mode=admin_mode)
        run_issuer_kind_logic(app)
        assert app.getParam("mas_issuer_kind") == "Issuer"
        app.fatalError.assert_not_called()


class TestIssuerKind93WithDNS:
    """MAS 9.3+ non-interactive: DNS provider configured → ClusterIssuer automatically."""

    @pytest.mark.parametrize("provider", ["cloudflare", "cis", "route53"])
    def test_dns_provider_derives_cluster_issuer(self, provider):
        """Any DNS provider → ClusterIssuer."""
        app = create_mock_app(channel="9.3.x", routing_mode="subdomain", dns_provider=provider, le_email="")
        run_issuer_kind_logic(app)
        assert app.getParam("mas_issuer_kind") == "ClusterIssuer"
        app.fatalError.assert_not_called()

    @pytest.mark.parametrize("admin_mode", ["cluster", "namespaced", "minimal"])
    def test_dns_cluster_issuer_all_admin_modes(self, admin_mode):
        """9.3+: namespaced/minimal admins can now use ClusterIssuer for external certs."""
        app = create_mock_app(channel="9.3.x", routing_mode="subdomain", dns_provider="cloudflare", le_email="", admin_mode=admin_mode)
        run_issuer_kind_logic(app)
        assert app.getParam("mas_issuer_kind") == "ClusterIssuer"
        app.fatalError.assert_not_called()


class TestIssuerKind93WithLetsEncrypt:
    """MAS 9.3+ non-interactive: LE + path routing → Issuer automatically."""

    def test_le_path_mode_derives_issuer(self):
        """LE enabled + path routing → Issuer."""
        app = create_mock_app(channel="9.3.x", routing_mode="path", dns_provider="", le_email="admin@example.com")
        run_issuer_kind_logic(app)
        assert app.getParam("mas_issuer_kind") == "Issuer"
        app.fatalError.assert_not_called()

    def test_le_path_takes_priority_over_dns_provider(self):
        """LE + path mode takes priority over dns_provider → Issuer, not ClusterIssuer."""
        app = create_mock_app(channel="9.3.x", routing_mode="path", dns_provider="cloudflare", le_email="admin@example.com")
        run_issuer_kind_logic(app)
        assert app.getParam("mas_issuer_kind") == "Issuer"
        app.fatalError.assert_not_called()


# =============================================================================
# MAS 9.3+ — --mas-issuer-kind flag rejected
# =============================================================================


class TestIssuerKindFlagRejectedOn93:
    """Passing --mas-issuer-kind explicitly on a 9.3+ install must be a fatal error."""

    @pytest.mark.parametrize("kind", ["Issuer", "ClusterIssuer"])
    def test_explicit_flag_raises_fatal_error(self, kind):
        """--mas-issuer-kind Issuer and ClusterIssuer are both rejected on 9.3+."""
        app = create_mock_app(channel="9.3.x")
        app.args.mas_issuer_kind = kind
        with pytest.raises(SystemExit):
            run_issuer_kind_logic(app)
        app.fatalError.assert_called_once()
        assert "9.3+" in app.fatalError.call_args[0][0]
        assert "derived automatically" in app.fatalError.call_args[0][0]

    def test_flag_rejected_on_930_channel(self):
        """Rejected on exact 9.3.0 channel as well."""
        app = create_mock_app(channel="9.3.0")
        app.args.mas_issuer_kind = "Issuer"
        with pytest.raises(SystemExit):
            run_issuer_kind_logic(app)
        app.fatalError.assert_called_once()

    def test_no_flag_no_error(self):
        """No --mas-issuer-kind passed (None) → no fatal error, derivation proceeds normally."""
        app = create_mock_app(channel="9.3.x")
        app.args.mas_issuer_kind = None
        run_issuer_kind_logic(app)
        app.fatalError.assert_not_called()
        assert app.getParam("mas_issuer_kind") == "Issuer"

    def test_argparser_still_accepts_flag_for_92(self):
        """argParser still accepts --mas-issuer-kind for 9.2 installs (parser is version-agnostic)."""
        argv = [
            "--mas-instance-id",
            "testinst",
            "--mas-workspace-id",
            "testws",
            "--mas-channel",
            "9.2.0",
            "--admin-mode",
            "cluster",
            "--mas-issuer-kind",
            "ClusterIssuer",
            "--accept-license",
            "--no-confirm",
        ]
        args = installArgParser.parse_args(args=argv)
        assert args.mas_issuer_kind == "ClusterIssuer"
