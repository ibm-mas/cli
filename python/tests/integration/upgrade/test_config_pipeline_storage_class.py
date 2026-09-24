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
Tests for UpgradeApp.configPipelineStorageClass()

Covers all 4 resolution paths:
  1. CLI args supplied (--storage-pipeline / --storage-accessmode)
  2. Existing config-pvc found on cluster
  3. No existing PVC, storage provider auto-detected, --no-confirm accepts it
  4. No existing PVC, no provider detected, --no-confirm → fatal error
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from mas.cli.upgrade.app import UpgradeApp


def _make_app(no_confirm=True, is_sno=False):
    """Create a minimal UpgradeApp with a mock dynamic client."""
    app = UpgradeApp()
    app._dynClient = MagicMock()
    app.noConfirm = no_confirm
    app.pipelineStorageClass = None
    app.pipelineStorageAccessMode = None
    app.params = {}

    # isSNO reads from the cluster; patch it at the instance level
    app._isSNO = is_sno
    return app


class TestConfigPipelineStorageClassFromCLIArgs:
    """Path 1 — CLI args pre-populate both values: method returns immediately."""

    def test_uses_cli_args_without_any_cluster_lookup(self):
        app = _make_app()
        app.pipelineStorageClass = "my-storage-class"
        app.pipelineStorageAccessMode = "ReadWriteMany"

        with patch("mas.cli.upgrade.app.lookupPipelineStorageClass") as mock_lookup:
            app.configPipelineStorageClass("inst1")

        mock_lookup.assert_not_called()
        assert app.pipelineStorageClass == "my-storage-class"
        assert app.pipelineStorageAccessMode == "ReadWriteMany"


class TestConfigPipelineStorageClassFromExistingPVC:
    """Path 2 — existing config-pvc found: use its storage class and access mode."""

    def test_uses_storage_class_from_existing_pvc(self):
        app = _make_app()

        with patch("mas.cli.upgrade.app.lookupPipelineStorageClass", return_value=("ibmc-file-gold-gid", "ReadWriteMany")):
            app.configPipelineStorageClass("inst1")

        assert app.pipelineStorageClass == "ibmc-file-gold-gid"
        assert app.pipelineStorageAccessMode == "ReadWriteMany"

    def test_falls_back_to_rwo_when_access_mode_missing_on_non_sno(self):
        """PVC exists but has no accessModes recorded; non-SNO defaults to ReadWriteMany."""
        app = _make_app()
        app.isSNO = Mock(return_value=False)

        with patch("mas.cli.upgrade.app.lookupPipelineStorageClass", return_value=("thin", None)):
            app.configPipelineStorageClass("inst1")

        assert app.pipelineStorageClass == "thin"
        assert app.pipelineStorageAccessMode == "ReadWriteMany"

    def test_falls_back_to_rwo_when_access_mode_missing_on_sno(self):
        """PVC exists but has no accessModes recorded; SNO defaults to ReadWriteOnce."""
        app = _make_app()
        app.isSNO = Mock(return_value=True)

        with patch("mas.cli.upgrade.app.lookupPipelineStorageClass", return_value=("thin", None)):
            app.configPipelineStorageClass("inst1")

        assert app.pipelineStorageClass == "thin"
        assert app.pipelineStorageAccessMode == "ReadWriteOnce"


class TestConfigPipelineStorageClassAutoDetect:
    """Path 3 — no existing PVC, storage provider auto-detected."""

    def _make_storage_classes(self, provider="ibmcloud", provider_name="IBM Cloud", rwx="ibmc-file-gold-gid", rwo="ibmc-block-gold"):
        sc = MagicMock()
        sc.provider = provider
        sc.providerName = provider_name
        sc.rwx = rwx
        sc.rwo = rwo
        return sc

    def test_no_confirm_accepts_rwx_auto_detected_class(self):
        app = _make_app(no_confirm=True)
        sc = self._make_storage_classes()

        with patch("mas.cli.upgrade.app.lookupPipelineStorageClass", return_value=(None, None)):
            with patch("mas.cli.upgrade.app.getDefaultStorageClasses", return_value=sc):
                with patch("mas.cli.cli.isSNO", return_value=False):
                    with patch("mas.cli.upgrade.app.print_formatted_text"):
                        app.configPipelineStorageClass("inst1")

        assert app.pipelineStorageClass == "ibmc-file-gold-gid"
        assert app.pipelineStorageAccessMode == "ReadWriteMany"

    def test_no_confirm_accepts_rwo_auto_detected_class_on_sno(self):
        app = _make_app(no_confirm=True)
        app.isSNO = Mock(return_value=True)
        sc = self._make_storage_classes()

        with patch("mas.cli.upgrade.app.lookupPipelineStorageClass", return_value=(None, None)):
            with patch("mas.cli.upgrade.app.getDefaultStorageClasses", return_value=sc):
                with patch("mas.cli.upgrade.app.print_formatted_text"):
                    app.configPipelineStorageClass("inst1")

        assert app.pipelineStorageClass == sc.rwo
        assert app.pipelineStorageAccessMode == "ReadWriteOnce"

    def test_no_confirm_accepts_rwo_when_rwx_is_none(self):
        """Provider detected but no RWX class available: falls back to RWO."""
        app = _make_app(no_confirm=True)
        sc = self._make_storage_classes(rwx=None)

        with patch("mas.cli.upgrade.app.lookupPipelineStorageClass", return_value=(None, None)):
            with patch("mas.cli.upgrade.app.getDefaultStorageClasses", return_value=sc):
                with patch("mas.cli.cli.isSNO", return_value=False):
                    with patch("mas.cli.upgrade.app.print_formatted_text"):
                        app.configPipelineStorageClass("inst1")

        assert app.pipelineStorageClass == sc.rwo
        assert app.pipelineStorageAccessMode == "ReadWriteOnce"


class TestConfigPipelineStorageClassNoDetection:
    """Path 4 — no existing PVC and no provider detected: fatal error in --no-confirm."""

    def test_no_confirm_fatal_error_when_no_provider_detected(self):
        app = _make_app(no_confirm=True)
        sc = MagicMock()
        sc.provider = None  # no provider detected

        app.fatalError = Mock(side_effect=SystemExit(1))

        with patch("mas.cli.upgrade.app.lookupPipelineStorageClass", return_value=(None, None)):
            with patch("mas.cli.upgrade.app.getDefaultStorageClasses", return_value=sc):
                with patch("mas.cli.cli.isSNO", return_value=False):
                    with pytest.raises(SystemExit):
                        app.configPipelineStorageClass("inst1")

        app.fatalError.assert_called_once()
        assert "--storage-pipeline" in app.fatalError.call_args[0][0]
