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
Tests for UpgradeApp.configStorageClasses()

Covers all resolution paths:
  1. CLI args supplied (--storage-class-rwo / --storage-class-rwx) — both valid on cluster
  2. CLI args supplied but one is invalid → fatalError
  3. Auto-detected provider, --no-confirm accepts automatically
  4. Auto-detected provider, interactive user accepts
  5. Auto-detected provider, interactive user declines → falls through to manual prompt
  6. No provider detected, --no-confirm → fatalError
  7. No provider detected, interactive → manual prompt
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from mas.cli.upgrade.app import UpgradeApp


def _make_app(no_confirm=True):
    """Create a minimal UpgradeApp with a mock dynamic client."""
    with patch("mas.cli.cli.which", return_value="/usr/bin/kubectl"):
        app = UpgradeApp()
    app._dynClient = MagicMock()
    app.noConfirm = no_confirm
    app.params = {}
    app.fatalError = Mock(side_effect=SystemExit(1))
    return app


def _make_storage_classes(provider="ibmcloud", provider_name="IBM Cloud", rwx="ibmc-file-gold-gid", rwo="ibmc-block-gold"):
    sc = MagicMock()
    sc.provider = provider
    sc.providerName = provider_name
    sc.rwx = rwx
    sc.rwo = rwo
    return sc


class TestConfigStorageClassesFromCLIArgs:
    """Path 1 — both --storage-class-rwo and --storage-class-rwx already in self.params."""

    def test_uses_cli_args_without_calling_auto_detect(self):
        app = _make_app()
        app.params["storage_class_rwo"] = "my-block-class"
        app.params["storage_class_rwx"] = "my-file-class"

        with patch("mas.cli.upgrade.app.getStorageClass", return_value=Mock()):
            with patch("mas.cli.upgrade.app.getDefaultStorageClasses") as mock_detect:
                app.configStorageClasses()

        mock_detect.assert_not_called()
        assert app.params["storage_class_rwo"] == "my-block-class"
        assert app.params["storage_class_rwx"] == "my-file-class"

    def test_validates_both_classes_exist_on_cluster(self):
        app = _make_app()
        app.params["storage_class_rwo"] = "my-block-class"
        app.params["storage_class_rwx"] = "my-file-class"

        with patch("mas.cli.upgrade.app.getStorageClass", return_value=Mock()) as mock_sc:
            app.configStorageClasses()

        assert mock_sc.call_count == 2
        mock_sc.assert_any_call(app.dynamicClient, "my-block-class")
        mock_sc.assert_any_call(app.dynamicClient, "my-file-class")


class TestConfigStorageClassesFromCLIArgsInvalid:
    """Path 2 — CLI args provided but a class does not exist on the cluster."""

    def test_fatal_error_when_rwo_not_found(self):
        app = _make_app()
        app.params["storage_class_rwo"] = "bad-rwo"
        app.params["storage_class_rwx"] = "my-file-class"

        def _sc_lookup(client, name):
            return None if name == "bad-rwo" else Mock()

        with patch("mas.cli.upgrade.app.getStorageClass", side_effect=_sc_lookup):
            with pytest.raises(SystemExit):
                app.configStorageClasses()

        app.fatalError.assert_called_once()
        assert "--storage-class-rwo" in app.fatalError.call_args[0][0]

    def test_fatal_error_when_rwx_not_found(self):
        app = _make_app()
        app.params["storage_class_rwo"] = "my-block-class"
        app.params["storage_class_rwx"] = "bad-rwx"

        def _sc_lookup(client, name):
            return None if name == "bad-rwx" else Mock()

        with patch("mas.cli.upgrade.app.getStorageClass", side_effect=_sc_lookup):
            with pytest.raises(SystemExit):
                app.configStorageClasses()

        app.fatalError.assert_called_once()
        assert "--storage-class-rwx" in app.fatalError.call_args[0][0]


class TestConfigStorageClassesAutoDetectNoConfirm:
    """Path 3 — auto-detected provider, --no-confirm accepts automatically."""

    def test_sets_rwo_and_rwx_from_auto_detected_provider(self):
        app = _make_app(no_confirm=True)
        sc = _make_storage_classes()

        with patch("mas.cli.upgrade.app.getDefaultStorageClasses", return_value=sc):
            with patch("mas.cli.upgrade.app.print_formatted_text"):
                app.configStorageClasses()

        assert app.params["storage_class_rwo"] == "ibmc-block-gold"
        assert app.params["storage_class_rwx"] == "ibmc-file-gold-gid"

    def test_does_not_prompt_in_no_confirm_mode(self):
        app = _make_app(no_confirm=True)
        sc = _make_storage_classes()
        app.yesOrNo = Mock()

        with patch("mas.cli.upgrade.app.getDefaultStorageClasses", return_value=sc):
            with patch("mas.cli.upgrade.app.print_formatted_text"):
                app.configStorageClasses()

        app.yesOrNo.assert_not_called()


class TestConfigStorageClassesAutoDetectInteractiveAccept:
    """Path 4 — auto-detected provider, interactive user accepts."""

    def test_sets_params_when_user_accepts_detected_classes(self):
        app = _make_app(no_confirm=False)
        sc = _make_storage_classes()
        app.yesOrNo = Mock(return_value=True)

        with patch("mas.cli.upgrade.app.getDefaultStorageClasses", return_value=sc):
            with patch("mas.cli.upgrade.app.print_formatted_text"):
                app.configStorageClasses()

        app.yesOrNo.assert_called_once_with("Use the auto-detected storage classes")
        assert app.params["storage_class_rwo"] == "ibmc-block-gold"
        assert app.params["storage_class_rwx"] == "ibmc-file-gold-gid"


class TestConfigStorageClassesAutoDetectInteractiveDecline:
    """Path 5 — auto-detected provider, interactive user declines → manual prompt."""

    def test_falls_through_to_manual_prompt_when_user_declines(self):
        app = _make_app(no_confirm=False)
        sc = _make_storage_classes()
        app.yesOrNo = Mock(return_value=False)
        app.printDescription = Mock()

        mock_sc_entry = MagicMock()
        mock_sc_entry.metadata.name = "thin"

        with patch("mas.cli.upgrade.app.getDefaultStorageClasses", return_value=sc):
            with patch("mas.cli.upgrade.app.getStorageClasses", return_value=[mock_sc_entry]):
                with patch("mas.cli.upgrade.app.print_formatted_text"):
                    with patch("mas.cli.upgrade.app.prompt", side_effect=["custom-rwo", "custom-rwx"]):
                        app.configStorageClasses()

        assert app.params["storage_class_rwo"] == "custom-rwo"
        assert app.params["storage_class_rwx"] == "custom-rwx"


class TestConfigStorageClassesNoDetectionNoConfirm:
    """Path 6 — no provider detected, --no-confirm → fatalError."""

    def test_fatal_error_when_no_provider_and_no_confirm(self):
        app = _make_app(no_confirm=True)
        sc = MagicMock()
        sc.provider = None

        with patch("mas.cli.upgrade.app.getDefaultStorageClasses", return_value=sc):
            with pytest.raises(SystemExit):
                app.configStorageClasses()

        app.fatalError.assert_called_once()
        assert "--storage-class-rwo" in app.fatalError.call_args[0][0]
        assert "--storage-class-rwx" in app.fatalError.call_args[0][0]


class TestConfigStorageClassesNoDetectionInteractive:
    """Path 7 — no provider detected, interactive → manual prompt for both classes."""

    def test_prompts_for_rwo_and_rwx_when_no_provider_detected(self):
        app = _make_app(no_confirm=False)
        sc = MagicMock()
        sc.provider = None
        app.printDescription = Mock()

        mock_sc_entry = MagicMock()
        mock_sc_entry.metadata.name = "thin"

        with patch("mas.cli.upgrade.app.getDefaultStorageClasses", return_value=sc):
            with patch("mas.cli.upgrade.app.getStorageClasses", return_value=[mock_sc_entry]):
                with patch("mas.cli.upgrade.app.print_formatted_text"):
                    with patch("mas.cli.upgrade.app.prompt", side_effect=["my-rwo", "my-rwx"]):
                        app.configStorageClasses()

        assert app.params["storage_class_rwo"] == "my-rwo"
        assert app.params["storage_class_rwx"] == "my-rwx"


class TestArgParserStorageClassArgs:
    """Verify --storage-class-rwo and --storage-class-rwx are accepted by the arg parser."""

    def test_storage_class_args_parsed_correctly(self):
        from mas.cli.upgrade.argParser import upgradeArgParser

        args = upgradeArgParser.parse_args(["--mas-instance-id", "test", "--storage-class-rwo", "my-block", "--storage-class-rwx", "my-file"])
        assert args.storage_class_rwo == "my-block"
        assert args.storage_class_rwx == "my-file"

    def test_storage_class_args_default_to_none(self):
        from mas.cli.upgrade.argParser import upgradeArgParser

        args = upgradeArgParser.parse_args(["--mas-instance-id", "test"])
        assert args.storage_class_rwo is None
        assert args.storage_class_rwx is None

    def test_storage_class_args_independent_of_pipeline_args(self):
        """--storage-class-rwo/rwx are independent from --storage-pipeline."""
        from mas.cli.upgrade.argParser import upgradeArgParser

        args = upgradeArgParser.parse_args(
            [
                "--mas-instance-id",
                "test",
                "--storage-pipeline",
                "ibmc-file-gold-gid",
                "--storage-accessmode",
                "ReadWriteMany",
                "--storage-class-rwo",
                "ibmc-block-gold",
                "--storage-class-rwx",
                "ibmc-file-gold-gid",
            ]
        )
        assert args.storage_pipeline == "ibmc-file-gold-gid"
        assert args.storage_accessmode == "ReadWriteMany"
        assert args.storage_class_rwo == "ibmc-block-gold"
        assert args.storage_class_rwx == "ibmc-file-gold-gid"
