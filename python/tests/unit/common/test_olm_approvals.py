#!/usr/bin/env python
# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
# *****************************************************************************

"""
Unit tests for the OLM approval mode/timeout resolution helpers.

The CLI mirrors the collection's precedence (flag > OLM_APPROVAL_MODE /
OLM_APPROVAL_TIMEOUT environment variable > omitted), validating environment
variable values up front so a bad value fails with a message naming the
variable. These tests inject the environment lookup so no real environment
is mutated.
"""

import pytest

from mas.cli.common.olmApprovals import (
    DEFAULT_OLM_APPROVAL_TIMEOUT,
    resolveOlmApprovalMode,
    resolveOlmApprovalTimeout,
)


class TestResolveOlmApprovalMode:
    """Tests for resolveOlmApprovalMode."""

    def test_flag_wins_over_environment(self):
        """GIVEN both the flag and the environment variable are set
        WHEN the mode is resolved
        THEN the flag value is returned
        """
        assert resolveOlmApprovalMode("Manual", getenv=lambda _k: "Automatic") == "Manual"

    def test_environment_variable_used_when_flag_unset(self):
        """GIVEN only the environment variable is set
        WHEN the mode is resolved
        THEN the environment value is returned
        """
        assert resolveOlmApprovalMode(None, getenv=lambda _k: "Manual") == "Manual"

    def test_none_when_neither_set(self):
        """GIVEN neither the flag nor the environment variable is set
        WHEN the mode is resolved
        THEN None is returned (omitted from the PipelineRun)
        """
        assert resolveOlmApprovalMode(None, getenv=lambda _k: None) is None

    def test_empty_environment_variable_treated_as_unset(self):
        """GIVEN the environment variable is set to an empty string
        WHEN the mode is resolved
        THEN None is returned, matching the collection's empty-is-unset rule
        """
        assert resolveOlmApprovalMode(None, getenv=lambda _k: "") is None

    def test_invalid_environment_value_raises_naming_the_variable(self):
        """GIVEN the environment variable holds an invalid mode
        WHEN the mode is resolved
        THEN ValueError names OLM_APPROVAL_MODE so the fix is obvious
        """
        with pytest.raises(ValueError, match="OLM_APPROVAL_MODE must be one of: Automatic, Manual \\(found 'banana'\\)"):
            resolveOlmApprovalMode(None, getenv=lambda _k: "banana")


class TestResolveOlmApprovalTimeout:
    """Tests for resolveOlmApprovalTimeout."""

    def test_flag_wins_over_environment(self):
        assert resolveOlmApprovalTimeout(300, getenv=lambda _k: "9999") == 300

    def test_environment_variable_used_when_flag_unset(self):
        assert resolveOlmApprovalTimeout(None, getenv=lambda _k: "600") == 600

    def test_none_when_neither_set(self):
        """None means omitted: the collection's 7200s default then applies."""
        assert resolveOlmApprovalTimeout(None, getenv=lambda _k: None) is None

    def test_empty_environment_variable_treated_as_unset(self):
        assert resolveOlmApprovalTimeout(None, getenv=lambda _k: "") is None

    def test_non_integer_environment_value_raises_naming_the_variable(self):
        with pytest.raises(ValueError, match="OLM_APPROVAL_TIMEOUT must be an integer number of seconds \\(found 'ten'\\)"):
            resolveOlmApprovalTimeout(None, getenv=lambda _k: "ten")

    def test_collection_default_is_two_hours(self):
        """The documented default matches the collection's DEFAULT_APPROVAL_TIMEOUT."""
        assert DEFAULT_OLM_APPROVAL_TIMEOUT == 7200
