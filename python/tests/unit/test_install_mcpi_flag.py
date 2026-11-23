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

"""Test the --install-mcpi flag on the install command argument parser."""

import pytest

from mas.cli.install.argParser import installArgParser


def test_install_mcpi_defaults_to_false():
    """Test that MCPI is not installed unless requested.

    GIVEN no --install-mcpi argument
    WHEN the install arguments are parsed
    THEN install_mcpi is False
    """
    args = installArgParser.parse_args([])
    assert args.install_mcpi is False


def test_install_mcpi_flag_sets_true():
    """Test that --install-mcpi enables the install.

    GIVEN the --install-mcpi argument
    WHEN the install arguments are parsed
    THEN install_mcpi is True
    """
    args = installArgParser.parse_args(["--install-mcpi"])
    assert args.install_mcpi is True


def test_install_mcpi_flag_takes_no_value():
    """Test that --install-mcpi is a plain on/off flag.

    GIVEN --install-mcpi followed by a value
    WHEN the install arguments are parsed
    THEN the parser rejects the unrecognized value
    """
    with pytest.raises(SystemExit):
        installArgParser.parse_args(["--install-mcpi", "v9.2"])
