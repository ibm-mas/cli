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
Test entitlement key validation functionality in BaseApp.

GIVEN a BaseApp instance
WHEN validateEntitlementKey is called with various inputs
THEN it should correctly validate keys and handle errors

GIVEN a BaseApp instance in interactive mode
WHEN promptForEntitlementKey is called
THEN it should validate the key and offer retry options on failure

GIVEN a BaseApp instance in non-interactive mode
WHEN promptForEntitlementKey is called with invalid key
THEN it should warn but continue when --no-confirm is set
"""

import pytest
from unittest.mock import patch
from mas.cli.cli import BaseApp


class TestValidateEntitlementKey:
    """Test the validateEntitlementKey method."""

    @patch("mas.cli.cli.validateIBMEntitlementKey")
    def test_validate_with_valid_key(self, mock_validate):
        """Test validation with a valid entitlement key.

        GIVEN a valid entitlement key
        WHEN validateEntitlementKey is called
        THEN it should return True.
        """
        mock_validate.return_value = True
        app = BaseApp()

        result = app.validateEntitlementKey("valid-key-123")

        assert result is True
        mock_validate.assert_called_once_with("valid-key-123", "cp/mas/coreapi", 30)

    @patch("mas.cli.cli.validateIBMEntitlementKey")
    def test_validate_with_invalid_key(self, mock_validate):
        """Test validation with an invalid entitlement key.

        GIVEN an invalid entitlement key
        WHEN validateEntitlementKey is called
        THEN it should return False.
        """
        mock_validate.return_value = False
        app = BaseApp()

        result = app.validateEntitlementKey("invalid-key")

        assert result is False
        mock_validate.assert_called_once_with("invalid-key", "cp/mas/coreapi", 30)

    @patch("mas.cli.cli.validateIBMEntitlementKey")
    def test_validate_with_custom_repository(self, mock_validate):
        """Test validation with custom repository parameter.

        GIVEN a custom repository parameter
        WHEN validateEntitlementKey is called
        THEN it should use the custom repository.
        """
        mock_validate.return_value = True
        app = BaseApp()

        result = app.validateEntitlementKey("key-123", repository="custom/repo", timeout=60)

        assert result is True
        mock_validate.assert_called_once_with("key-123", "custom/repo", 60)

    @patch("mas.cli.cli.validateIBMEntitlementKey")
    def test_validate_with_network_error(self, mock_validate):
        """Test validation when network error occurs.

        GIVEN a network error during validation
        WHEN validateEntitlementKey is called
        THEN it should return False and log the error.
        """
        mock_validate.side_effect = ConnectionError("Network error")
        app = BaseApp()

        result = app.validateEntitlementKey("key-123")

        assert result is False

    @patch("mas.cli.cli.validateIBMEntitlementKey")
    def test_validate_with_timeout(self, mock_validate):
        """Test validation when timeout occurs.

        GIVEN a timeout during validation
        WHEN validateEntitlementKey is called
        THEN it should return False and log the error.
        """
        mock_validate.side_effect = TimeoutError("Validation timeout")
        app = BaseApp()

        result = app.validateEntitlementKey("key-123")

        assert result is False


class TestPromptForEntitlementKeyInteractive:
    """Test promptForEntitlementKey in interactive mode."""

    @patch("mas.cli.cli.BaseApp.validateEntitlementKey")
    @patch("mas.cli.cli.BaseApp.promptForString")
    @patch("mas.cli.cli.BaseApp.printHighlight")
    def test_valid_key_first_attempt(self, mock_print_highlight, mock_prompt_string, mock_validate):
        """Test successful validation on first attempt.

        GIVEN a valid entitlement key on first attempt
        WHEN promptForEntitlementKey is called
        THEN it should validate and return the key without retry.
        """
        mock_prompt_string.return_value = "valid-key-123"
        mock_validate.return_value = True

        app = BaseApp()
        app.noConfirm = False

        result = app.promptForEntitlementKey("IBM entitlement key", "ibm_entitlement_key")

        assert result == "valid-key-123"
        assert app.getParam("ibm_entitlement_key") == "valid-key-123"
        mock_validate.assert_called_once_with("valid-key-123", "cp/mas/coreapi", 30)
        mock_print_highlight.assert_called_once()

    @patch("mas.cli.cli.BaseApp.validateEntitlementKey")
    @patch("mas.cli.cli.BaseApp.promptForString")
    @patch("mas.cli.cli.BaseApp.promptForInt")
    @patch("mas.cli.cli.BaseApp.printWarning")
    @patch("mas.cli.cli.BaseApp.printDescription")
    @patch("mas.cli.cli.BaseApp.printHighlight")
    def test_invalid_then_valid_key(self, mock_print_highlight, mock_print_desc, mock_print_warn, mock_prompt_int, mock_prompt_string, mock_validate):
        """Test retry after invalid key, then valid key.

        GIVEN an invalid key followed by a valid key
        WHEN promptForEntitlementKey is called and user chooses to try again
        THEN it should loop and eventually succeed.
        """
        mock_prompt_string.side_effect = ["invalid-key", "valid-key-123"]
        mock_validate.side_effect = [False, True]
        mock_prompt_int.return_value = 1  # Try again

        app = BaseApp()
        app.noConfirm = False

        result = app.promptForEntitlementKey("IBM entitlement key", "ibm_entitlement_key")

        assert result == "valid-key-123"
        assert app.getParam("ibm_entitlement_key") == "valid-key-123"
        assert mock_validate.call_count == 2
        assert mock_prompt_string.call_count == 2
        mock_prompt_int.assert_called_once()

    @patch("mas.cli.cli.BaseApp.validateEntitlementKey")
    @patch("mas.cli.cli.BaseApp.promptForString")
    @patch("mas.cli.cli.BaseApp.promptForInt")
    @patch("mas.cli.cli.BaseApp.printWarning")
    @patch("mas.cli.cli.BaseApp.printDescription")
    def test_invalid_key_continue_anyway(self, mock_print_desc, mock_print_warn, mock_prompt_int, mock_prompt_string, mock_validate):
        """Test continuing with invalid key when user chooses option 2.

        GIVEN an invalid key
        WHEN promptForEntitlementKey is called and user chooses to continue anyway
        THEN it should return the invalid key.
        """
        mock_prompt_string.return_value = "invalid-key"
        mock_validate.return_value = False
        mock_prompt_int.return_value = 2  # Continue anyway

        app = BaseApp()
        app.noConfirm = False

        result = app.promptForEntitlementKey("IBM entitlement key", "ibm_entitlement_key")

        assert result == "invalid-key"
        assert app.getParam("ibm_entitlement_key") == "invalid-key"
        mock_validate.assert_called_once()
        mock_prompt_int.assert_called_once()

    @patch("mas.cli.cli.BaseApp.validateEntitlementKey")
    @patch("mas.cli.cli.BaseApp.promptForString")
    @patch("mas.cli.cli.BaseApp.promptForInt")
    @patch("mas.cli.cli.BaseApp.printWarning")
    @patch("mas.cli.cli.BaseApp.printDescription")
    def test_invalid_key_quit(self, mock_print_desc, mock_print_warn, mock_prompt_int, mock_prompt_string, mock_validate):
        """Test quitting when user chooses option 3.

        GIVEN an invalid key
        WHEN promptForEntitlementKey is called and user chooses to quit
        THEN it should raise SystemExit.
        """
        mock_prompt_string.return_value = "invalid-key"
        mock_validate.return_value = False
        mock_prompt_int.return_value = 3  # Quit

        app = BaseApp()
        app.noConfirm = False

        with pytest.raises(SystemExit) as exc_info:
            app.promptForEntitlementKey("IBM entitlement key", "ibm_entitlement_key")

        assert exc_info.value.code == 1
        mock_validate.assert_called_once()
        mock_prompt_int.assert_called_once()


class TestPromptForEntitlementKeyNonInteractive:
    """Test promptForEntitlementKey in non-interactive mode."""

    @patch("mas.cli.cli.BaseApp.validateEntitlementKey")
    @patch("mas.cli.cli.BaseApp.promptForString")
    @patch("mas.cli.cli.BaseApp.printWarning")
    def test_invalid_key_with_no_confirm(self, mock_print_warn, mock_prompt_string, mock_validate):
        """Test invalid key with --no-confirm flag.

        GIVEN an invalid key and --no-confirm flag is set
        WHEN promptForEntitlementKey is called
        THEN it should warn but continue without prompting.
        """
        mock_prompt_string.return_value = "invalid-key"
        mock_validate.return_value = False

        app = BaseApp()
        app.noConfirm = True

        result = app.promptForEntitlementKey("IBM entitlement key", "ibm_entitlement_key")

        assert result == "invalid-key"
        assert app.getParam("ibm_entitlement_key") == "invalid-key"
        mock_validate.assert_called_once()
        mock_print_warn.assert_called_once()

    @patch("mas.cli.cli.BaseApp.validateEntitlementKey")
    @patch("mas.cli.cli.BaseApp.promptForString")
    @patch("mas.cli.cli.BaseApp.printHighlight")
    def test_valid_key_with_no_confirm(self, mock_print_highlight, mock_prompt_string, mock_validate):
        """Test valid key with --no-confirm flag.

        GIVEN a valid key and --no-confirm flag is set
        WHEN promptForEntitlementKey is called
        THEN it should validate and continue normally.
        """
        mock_prompt_string.return_value = "valid-key-123"
        mock_validate.return_value = True

        app = BaseApp()
        app.noConfirm = True

        result = app.promptForEntitlementKey("IBM entitlement key", "ibm_entitlement_key")

        assert result == "valid-key-123"
        assert app.getParam("ibm_entitlement_key") == "valid-key-123"
        mock_validate.assert_called_once()
        mock_print_highlight.assert_called_once()

    @patch("mas.cli.cli.BaseApp.validateEntitlementKey")
    @patch("mas.cli.cli.BaseApp.promptForString")
    @patch("mas.cli.cli.BaseApp.promptForInt")
    @patch("mas.cli.cli.BaseApp.printWarning")
    @patch("mas.cli.cli.BaseApp.printDescription")
    def test_invalid_key_without_no_confirm(self, mock_print_desc, mock_print_warn, mock_prompt_int, mock_prompt_string, mock_validate):
        """Test invalid key without --no-confirm flag (should offer options).

        GIVEN an invalid key and --no-confirm flag is NOT set
        WHEN promptForEntitlementKey is called
        THEN it should offer the 3 options like interactive mode.
        """
        mock_prompt_string.return_value = "invalid-key"
        mock_validate.return_value = False
        mock_prompt_int.return_value = 2  # Continue anyway

        app = BaseApp()
        app.noConfirm = False

        result = app.promptForEntitlementKey("IBM entitlement key", "ibm_entitlement_key")

        assert result == "invalid-key"
        mock_validate.assert_called_once()
        mock_prompt_int.assert_called_once()
