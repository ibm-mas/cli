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

"""Test that the install CLI injects the McpiCfg resource into the additional configs secret."""

from base64 import b64decode

from mas.cli.install.settings.additionalConfigs import AdditionalConfigsMixin, MCPI_CONFIG_FILENAME


class FakeApp(AdditionalConfigsMixin):
    """Minimal host for AdditionalConfigsMixin."""

    def __init__(self, installMcpi, localConfigDir=None):
        self.isInteractiveMode = False
        self.noConfirm = True
        self.installMcpi = installMcpi
        self.localConfigDir = localConfigDir
        self.additionalConfigsSecret = None


def test_mcpi_config_added_when_mcpi_enabled():
    """Test that the McpiCfg file is added to the secret when MCPI is enabled.

    GIVEN MCPI is enabled and no local config directory is set
    WHEN additionalConfigs() runs
    THEN the pipeline-additional-configs secret contains the McpiCfg YAML
    """
    app = FakeApp(installMcpi=True)
    app.additionalConfigs()

    assert app.additionalConfigsSecret["metadata"]["name"] == "pipeline-additional-configs"
    content = b64decode(app.additionalConfigsSecret["data"][MCPI_CONFIG_FILENAME]).decode()
    assert "kind: McpiCfg" in content
    assert "{{ mas_instance_id }}-mcpi-system" in content


def test_mcpi_config_not_added_when_mcpi_disabled():
    """Test that no secret is created when MCPI is disabled.

    GIVEN MCPI is not enabled and no local config directory is set
    WHEN additionalConfigs() runs
    THEN no additional configs secret is created
    """
    app = FakeApp(installMcpi=False)
    app.additionalConfigs()

    assert app.additionalConfigsSecret is None


def test_mcpi_config_merged_with_user_configs(tmp_path):
    """Test that the McpiCfg file is merged with user supplied configs.

    GIVEN MCPI is enabled and a local config directory with one YAML file
    WHEN additionalConfigs() runs
    THEN the secret contains both the user file and the McpiCfg file
    """
    (tmp_path / "user.yaml").write_text("kind: ConfigMap\n")
    app = FakeApp(installMcpi=True, localConfigDir=str(tmp_path))
    app.additionalConfigs()

    assert set(app.additionalConfigsSecret["data"].keys()) == {"user.yaml", MCPI_CONFIG_FILENAME}


def test_user_supplied_mcpi_config_takes_precedence(tmp_path):
    """Test that a user supplied file with the same name is not overwritten.

    GIVEN MCPI is enabled and the local config directory already has the MCPI file
    WHEN additionalConfigs() runs
    THEN the user's content is preserved
    """
    (tmp_path / MCPI_CONFIG_FILENAME).write_text("kind: McpiCfg\n# custom\n")
    app = FakeApp(installMcpi=True, localConfigDir=str(tmp_path))
    app.additionalConfigs()

    assert "# custom" in b64decode(app.additionalConfigsSecret["data"][MCPI_CONFIG_FILENAME]).decode()
