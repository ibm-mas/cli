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

"""Unit tests for the configure-mcpi argument parser."""

from mas.cli.configure_mcpi.argParser import configureMcpiArgParser


def test_mas_instance_id_argument_sets_value():
    """Test that --mas-instance-id argument sets the instance ID.

    GIVEN the --mas-instance-id flag with value 'visionary'
    WHEN the arguments are parsed
    THEN mas_instance_id is 'visionary'
    """
    args = configureMcpiArgParser.parse_args(["--mas-instance-id", "visionary"])
    assert args.mas_instance_id == "visionary"


def test_mas_instance_id_short_flag_sets_value():
    """Test that -i short flag sets the instance ID.

    GIVEN the -i flag with value 'inst1'
    WHEN the arguments are parsed
    THEN mas_instance_id is 'inst1'
    """
    args = configureMcpiArgParser.parse_args(["-i", "inst1"])
    assert args.mas_instance_id == "inst1"


def test_mas_instance_id_defaults_to_none():
    """Test that mas_instance_id defaults to None when not provided.

    GIVEN no arguments
    WHEN the arguments are parsed
    THEN mas_instance_id is None
    """
    args = configureMcpiArgParser.parse_args([])
    assert args.mas_instance_id is None


def test_no_confirm_flag_sets_true():
    """Test that --no-confirm flag sets no_confirm to True.

    GIVEN the --no-confirm flag
    WHEN the arguments are parsed
    THEN no_confirm is True
    """
    args = configureMcpiArgParser.parse_args(["--no-confirm"])
    assert args.no_confirm is True


def test_no_confirm_defaults_to_false():
    """Test that no_confirm defaults to False when omitted.

    GIVEN no arguments
    WHEN the arguments are parsed
    THEN no_confirm is False
    """
    args = configureMcpiArgParser.parse_args([])
    assert args.no_confirm is False
