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

"""Unit tests for the configure-mcpi application logic."""

from unittest.mock import MagicMock, patch
import pytest
from kubernetes.dynamic.exceptions import NotFoundError

from mas.cli.configure_mcpi.app import ConfigureMcpiApp, buildMcpiCr


def test_mcpi_cr_dict_has_correct_api_version():
    """Test that McpiCfg has correct apiVersion.

    GIVEN an instance ID
    WHEN buildMcpiCr() is called
    THEN apiVersion is 'config.mas.ibm.com/v1'
    """
    cr = buildMcpiCr("testinst")
    assert cr["apiVersion"] == "config.mas.ibm.com/v1"


def test_mcpi_cr_dict_has_correct_kind():
    """Test that McpiCfg has correct kind.

    GIVEN an instance ID
    WHEN buildMcpiCr() is called
    THEN kind is 'McpiCfg'
    """
    cr = buildMcpiCr("testinst")
    assert cr["kind"] == "McpiCfg"


def test_mcpi_cr_dict_name_uses_instance_id():
    """Test that McpiCfg metadata name includes instance ID.

    GIVEN instance ID 'visionary'
    WHEN buildMcpiCr('visionary') is called
    THEN metadata name is 'visionary-mcpi-system'
    """
    cr = buildMcpiCr("visionary")
    assert cr["metadata"]["name"] == "visionary-mcpi-system"


def test_mcpi_cr_dict_namespace_uses_instance_id():
    """Test that McpiCfg namespace includes instance ID.

    GIVEN instance ID 'visionary'
    WHEN buildMcpiCr('visionary') is called
    THEN metadata namespace is 'mas-visionary-core'
    """
    cr = buildMcpiCr("visionary")
    assert cr["metadata"]["namespace"] == "mas-visionary-core"


def test_mcpi_cr_dict_has_required_labels():
    """Test that McpiCfg includes required system labels.

    GIVEN instance ID 'myinstance'
    WHEN buildMcpiCr('myinstance') is called
    THEN labels contain configScope=system and instanceId=myinstance
    """
    cr = buildMcpiCr("myinstance")
    labels = cr["metadata"]["labels"]
    assert labels["mas.ibm.com/configScope"] == "system"
    assert labels["mas.ibm.com/instanceId"] == "myinstance"


def test_mcpi_cr_dict_spec_enabled_true():
    """Test that McpiCfg spec has enabled set to True.

    GIVEN an instance ID
    WHEN buildMcpiCr() is called
    THEN spec.config.enabled is True
    """
    cr = buildMcpiCr("testinst")
    assert cr["spec"]["config"]["enabled"] is True
    assert cr["spec"]["displayName"] == "Maximo Cluster Performance Insights"


@patch("mas.cli.cli.which", return_value="/usr/local/bin/kubectl")
@patch("mas.cli.configure_mcpi.app.BaseApp.connect")
def test_configure_mcpi_fatal_error_when_namespace_missing(mockConnect, mockWhich):
    """Test that configureMcpi fails when target namespace is missing.

    GIVEN a cluster where mas-missing-core namespace does not exist
    WHEN configureMcpi is called
    THEN a fatal error is raised
    """
    app = ConfigureMcpiApp()
    mockDynClient = MagicMock()
    nsApi = MagicMock()
    nsApi.get.side_effect = NotFoundError(MagicMock(status=404))
    mockDynClient.resources.get.return_value = nsApi
    app._dynClient = mockDynClient

    with pytest.raises(SystemExit):
        app.configureMcpi(["--mas-instance-id", "missing", "--no-confirm"])


@patch("mas.cli.cli.which", return_value="/usr/local/bin/kubectl")
@patch("mas.cli.configure_mcpi.app.getMasChannel")
@patch("mas.cli.configure_mcpi.app.BaseApp.connect")
def test_configure_mcpi_fatal_error_when_channel_not_found(mockConnect, mockGetMasChannel, mockWhich):
    """Test that configureMcpi fails when MAS channel cannot be determined.

    GIVEN a cluster where MAS subscription channel is None
    WHEN configureMcpi is called
    THEN a fatal error is raised
    """
    app = ConfigureMcpiApp()
    mockDynClient = MagicMock()
    app._dynClient = mockDynClient
    mockGetMasChannel.return_value = None

    with pytest.raises(SystemExit):
        app.configureMcpi(["--mas-instance-id", "inst1", "--no-confirm"])


@patch("mas.cli.cli.which", return_value="/usr/local/bin/kubectl")
@patch("mas.cli.configure_mcpi.app.getMasChannel")
@patch("mas.cli.configure_mcpi.app.BaseApp.connect")
def test_configure_mcpi_fatal_error_when_mas_version_older_than_9_2(mockConnect, mockGetMasChannel, mockWhich):
    """Test that configureMcpi fails for MAS channel < 9.2.

    GIVEN a cluster with MAS channel 9.1.x
    WHEN configureMcpi is called
    THEN a fatal error is raised
    """
    app = ConfigureMcpiApp()
    mockDynClient = MagicMock()
    app._dynClient = mockDynClient
    mockGetMasChannel.return_value = "9.1.x"

    with pytest.raises(SystemExit):
        app.configureMcpi(["--mas-instance-id", "inst1", "--no-confirm"])


@patch("mas.cli.cli.which", return_value="/usr/local/bin/kubectl")
@patch("mas.cli.configure_mcpi.app.getMasChannel")
@patch("mas.cli.configure_mcpi.app.BaseApp.connect")
def test_configure_mcpi_applies_cr_successfully_when_not_exists(mockConnect, mockGetMasChannel, mockWhich):
    """Test that configureMcpi creates McpiCfg when it does not exist.

    GIVEN a valid MAS 9.2 instance and no existing McpiCfg
    WHEN configureMcpi is called with --no-confirm
    THEN McpiCfg is created via dynamicClient
    """
    app = ConfigureMcpiApp()
    mockDynClient = MagicMock()
    mockGetMasChannel.return_value = "9.2.x"

    mcpiApi = MagicMock()
    mcpiApi.get.side_effect = NotFoundError(MagicMock(status=404))

    def resourceGetSideEffect(api_version, kind):
        if kind == "Namespace":
            nsApi = MagicMock()
            return nsApi
        return mcpiApi

    mockDynClient.resources.get.side_effect = resourceGetSideEffect
    app._dynClient = mockDynClient

    app.configureMcpi(["--mas-instance-id", "visionary", "--no-confirm"])

    mcpiApi.create.assert_called_once()
    createdCr = mcpiApi.create.call_args[1]["body"]
    assert createdCr["metadata"]["name"] == "visionary-mcpi-system"
    assert createdCr["metadata"]["namespace"] == "mas-visionary-core"


@patch("mas.cli.cli.which", return_value="/usr/local/bin/kubectl")
@patch("mas.cli.configure_mcpi.app.getMasChannel")
@patch("mas.cli.configure_mcpi.app.BaseApp.connect")
def test_configure_mcpi_patches_cr_when_already_exists(mockConnect, mockGetMasChannel, mockWhich):
    """Test that configureMcpi patches McpiCfg when it already exists.

    GIVEN a valid MAS 9.2 instance and existing McpiCfg
    WHEN configureMcpi is called with --no-confirm
    THEN McpiCfg is patched via dynamicClient
    """
    app = ConfigureMcpiApp()
    mockDynClient = MagicMock()
    mockGetMasChannel.return_value = "9.2.x"

    mcpiApi = MagicMock()
    mcpiApi.get.return_value = {"metadata": {"name": "visionary-mcpi-system"}}

    def resourceGetSideEffect(api_version, kind):
        if kind == "Namespace":
            return MagicMock()
        return mcpiApi

    mockDynClient.resources.get.side_effect = resourceGetSideEffect
    app._dynClient = mockDynClient

    app.configureMcpi(["--mas-instance-id", "visionary", "--no-confirm"])

    mcpiApi.patch.assert_called_once()
    patchedCr = mcpiApi.patch.call_args[1]["body"]
    assert patchedCr["metadata"]["name"] == "visionary-mcpi-system"
    mcpiApi.create.assert_not_called()


@patch("mas.cli.cli.which", return_value="/usr/local/bin/kubectl")
@patch("mas.cli.configure_mcpi.app.ConfigureMcpiApp.promptForString")
@patch("mas.cli.configure_mcpi.app.getMasChannel")
@patch("mas.cli.configure_mcpi.app.BaseApp.connect")
def test_configure_mcpi_prompts_for_instance_id_in_interactive_mode(mockConnect, mockGetMasChannel, mockPromptForString, mockWhich):
    """Test that configureMcpi prompts for instance ID when omitted.

    GIVEN no --mas-instance-id argument
    WHEN configureMcpi is called with --no-confirm
    THEN instance ID is prompted and used
    """
    app = ConfigureMcpiApp()
    mockDynClient = MagicMock()
    mockPromptForString.return_value = "promptedinst"
    mockGetMasChannel.return_value = "9.2.x"

    mcpiApi = MagicMock()
    mcpiApi.get.side_effect = NotFoundError(MagicMock(status=404))

    def resourceGetSideEffect(api_version, kind):
        if kind == "Namespace":
            return MagicMock()
        return mcpiApi

    mockDynClient.resources.get.side_effect = resourceGetSideEffect
    app._dynClient = mockDynClient

    app.configureMcpi(["--no-confirm"])

    mockPromptForString.assert_called_once()
    mcpiApi.create.assert_called_once()
    createdCr = mcpiApi.create.call_args[1]["body"]
    assert createdCr["metadata"]["name"] == "promptedinst-mcpi-system"
    assert createdCr["metadata"]["namespace"] == "mas-promptedinst-core"


@patch("mas.cli.cli.which", return_value="/usr/local/bin/kubectl")
@patch("mas.cli.configure_mcpi.app.ConfigureMcpiApp.yesOrNo")
@patch("mas.cli.configure_mcpi.app.getMasChannel")
@patch("mas.cli.configure_mcpi.app.BaseApp.connect")
def test_configure_mcpi_aborts_when_user_declines_confirmation(mockConnect, mockGetMasChannel, mockYesOrNo, mockWhich):
    """Test that configureMcpi aborts when user declines confirmation.

    GIVEN an interactive prompt where user answers No
    WHEN configureMcpi is called
    THEN no CR is created or patched
    """
    app = ConfigureMcpiApp()
    mockDynClient = MagicMock()
    mockGetMasChannel.return_value = "9.2.x"
    mockYesOrNo.return_value = False

    mcpiApi = MagicMock()

    def resourceGetSideEffect(api_version, kind):
        if kind == "Namespace":
            return MagicMock()
        return mcpiApi

    mockDynClient.resources.get.side_effect = resourceGetSideEffect
    app._dynClient = mockDynClient

    app.configureMcpi(["--mas-instance-id", "visionary"])

    mockYesOrNo.assert_called_once()
    mcpiApi.create.assert_not_called()
    mcpiApi.patch.assert_not_called()


@patch("mas.cli.cli.which", return_value="/usr/local/bin/kubectl")
@patch("mas.cli.configure_mcpi.app.ConfigureMcpiApp.configureMcpi")
def test_main_dispatches_configure_mcpi(mockConfigureMcpi, mockWhich):
    """Test that __main__.py dispatches configure-mcpi command.

    GIVEN sys.argv containing 'configure-mcpi'
    WHEN main() runs
    THEN ConfigureMcpiApp.configureMcpi is called with remaining arguments
    """
    from mas.cli.__main__ import main

    with patch("mas.cli.__main__.argv", ["mas-cli", "configure-mcpi", "--mas-instance-id", "visionary", "--no-confirm"]):
        main()

    mockConfigureMcpi.assert_called_once_with(["--mas-instance-id", "visionary", "--no-confirm"])
