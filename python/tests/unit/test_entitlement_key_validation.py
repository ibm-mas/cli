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
from mas.devops.utils import EntitlementKeySSLError


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
    def test_validate_with_ssl_error(self, mock_validate):
        """Test validation when an SSL certificate error occurs.

        GIVEN an SSL certificate error during validation (e.g. corporate proxy)
        utils.py raises EntitlementKeySSLError.
        WHEN validateEntitlementKey is called
        THEN it should re-raise EntitlementKeySSLError so callers can tell it apart from an invalid key.
        """
        mock_validate.side_effect = EntitlementKeySSLError("self-signed certificate in certificate chain")
        app = BaseApp()

        with pytest.raises(EntitlementKeySSLError):
            app.validateEntitlementKey("key-123")

    @patch("mas.cli.cli.validateIBMEntitlementKey")
    def test_validate_with_network_error(self, mock_validate):
        """Test validation when a non-SSL network error occurs.

        GIVEN a network error during validation
        utils.py re-raises non-SSL RequestException.
        WHEN validateEntitlementKey is called
        THEN it should re-raise it (key status unknown) and NOT return False (which means key rejected).
        """
        from requests.exceptions import ConnectionError as RequestsConnectionError

        mock_validate.side_effect = RequestsConnectionError("Network unreachable")
        app = BaseApp()

        with pytest.raises(RequestsConnectionError):
            app.validateEntitlementKey("key-123")

    @patch("mas.cli.cli.validateIBMEntitlementKey")
    def test_validate_with_timeout(self, mock_validate):
        """Test validation when a timeout occurs.

        GIVEN a timeout during validation
        utils.py re-raises non-SSL RequestException.
        WHEN validateEntitlementKey is called
        THEN it should re-raise it (key status unknown) and NOT return False (which means key rejected).
        """
        from requests.exceptions import Timeout as RequestsTimeout

        mock_validate.side_effect = RequestsTimeout("Request timed out")
        app = BaseApp()

        with pytest.raises(RequestsTimeout):
            app.validateEntitlementKey("key-123")


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


class TestPromptForEntitlementKeySSLError:
    """Test promptForEntitlementKey when an SSL error prevents validation."""

    @patch("mas.cli.cli.BaseApp.validateEntitlementKey")
    @patch("mas.cli.cli.BaseApp.promptForString")
    @patch("mas.cli.cli.BaseApp.promptForInt")
    @patch("mas.cli.cli.BaseApp.printWarning")
    @patch("mas.cli.cli.BaseApp.printDescription")
    def test_ssl_error_continue_anyway(self, mock_print_desc, mock_print_warn, mock_prompt_int, mock_prompt_string, mock_validate):
        """Test continuing when SSL error occurs and user chooses option 2.

        GIVEN an SSL error during validation
        WHEN promptForEntitlementKey is called and user chooses to continue anyway
        THEN it should return the key and show an SSL-specific warning message.
        """
        mock_prompt_string.return_value = "valid-key-123"
        mock_validate.side_effect = EntitlementKeySSLError("SSL error")
        mock_prompt_int.return_value = 2  # Continue anyway

        app = BaseApp()
        app.noConfirm = False

        result = app.promptForEntitlementKey("IBM entitlement key", "ibm_entitlement_key")

        assert result == "valid-key-123"
        assert app.getParam("ibm_entitlement_key") == "valid-key-123"
        mock_validate.assert_called_once()
        mock_prompt_int.assert_called_once()
        # Warning should mention SSL, not "validation failed"
        warn_message = mock_print_warn.call_args[0][0]
        assert "SSL" in warn_message

    @patch("mas.cli.cli.BaseApp.validateEntitlementKey")
    @patch("mas.cli.cli.BaseApp.promptForString")
    @patch("mas.cli.cli.BaseApp.printWarning")
    def test_ssl_error_with_no_confirm(self, mock_print_warn, mock_prompt_string, mock_validate):
        """Test SSL error with --no-confirm flag.

        GIVEN an SSL error and --no-confirm flag is set
        WHEN promptForEntitlementKey is called
        THEN it should warn with an SSL-specific message and continue without prompting.
        """
        mock_prompt_string.return_value = "valid-key-123"
        mock_validate.side_effect = EntitlementKeySSLError("SSL error")

        app = BaseApp()
        app.noConfirm = True

        result = app.promptForEntitlementKey("IBM entitlement key", "ibm_entitlement_key")

        assert result == "valid-key-123"
        assert app.getParam("ibm_entitlement_key") == "valid-key-123"
        mock_validate.assert_called_once()
        mock_print_warn.assert_called_once()
        # Warning should mention SSL, not generic "validation failed"
        warn_message = mock_print_warn.call_args[0][0]
        assert "SSL" in warn_message

    @patch("mas.cli.cli.BaseApp.validateEntitlementKey")
    @patch("mas.cli.cli.BaseApp.promptForString")
    @patch("mas.cli.cli.BaseApp.promptForInt")
    @patch("mas.cli.cli.BaseApp.printWarning")
    @patch("mas.cli.cli.BaseApp.printDescription")
    def test_ssl_error_quit(self, mock_print_desc, mock_print_warn, mock_prompt_int, mock_prompt_string, mock_validate):
        """Test quitting when SSL error occurs and user chooses option 3.

        GIVEN an SSL error during validation
        WHEN promptForEntitlementKey is called and user chooses to quit
        THEN it should raise SystemExit.
        """
        mock_prompt_string.return_value = "valid-key-123"
        mock_validate.side_effect = EntitlementKeySSLError("SSL error")
        mock_prompt_int.return_value = 3  # Quit

        app = BaseApp()
        app.noConfirm = False

        with pytest.raises(SystemExit) as exc_info:
            app.promptForEntitlementKey("IBM entitlement key", "ibm_entitlement_key")

        assert exc_info.value.code == 1


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


class TestPromptForEntitlementKeyMessages:
    """Test that the message shown matches the reason validation did not succeed."""

    @patch("mas.cli.cli.BaseApp.validateEntitlementKey")
    @patch("mas.cli.cli.BaseApp.promptForString")
    @patch("mas.cli.cli.BaseApp.promptForInt")
    @patch("mas.cli.cli.BaseApp.printWarning")
    @patch("mas.cli.cli.BaseApp.printDescription")
    def test_wrong_key_says_key_is_not_valid(self, mock_print_desc, mock_print_warn, mock_prompt_int, mock_prompt_string, mock_validate):
        """GIVEN cp.icr.io rejected the key WHEN prompting THEN the warning says the key is not valid."""
        mock_prompt_string.return_value = "wrong-key"
        mock_validate.return_value = False
        mock_prompt_int.return_value = 2

        app = BaseApp()
        app.noConfirm = False
        app.promptForEntitlementKey("IBM entitlement key", "ibm_entitlement_key")

        warn_message = mock_print_warn.call_args[0][0]
        assert "key is not valid" in warn_message
        assert "SSL" not in warn_message
        assert "Network" not in warn_message

    @patch("mas.cli.cli.BaseApp.validateEntitlementKey")
    @patch("mas.cli.cli.BaseApp.promptForString")
    @patch("mas.cli.cli.BaseApp.promptForInt")
    @patch("mas.cli.cli.BaseApp.printWarning")
    @patch("mas.cli.cli.BaseApp.printDescription")
    def test_network_error_says_could_not_connect(self, mock_print_desc, mock_print_warn, mock_prompt_int, mock_prompt_string, mock_validate):
        """GIVEN a non-SSL network error WHEN prompting THEN the warning says the CLI could not connect, not that the key is wrong."""
        from requests.exceptions import ConnectionError as RequestsConnectionError

        mock_prompt_string.return_value = "maybe-valid-key"
        mock_validate.side_effect = RequestsConnectionError("Network unreachable")
        mock_prompt_int.return_value = 2

        app = BaseApp()
        app.noConfirm = False
        result = app.promptForEntitlementKey("IBM entitlement key", "ibm_entitlement_key")

        assert result == "maybe-valid-key"
        warn_message = mock_print_warn.call_args[0][0]
        assert "Could not validate the entitlement key" in warn_message
        assert "key is not valid" not in warn_message
        assert "SSL" not in warn_message
        # The explanation must also tell the user the key may still be fine
        description = " ".join(mock_print_desc.call_args[0][0])
        assert "does NOT necessarily mean your entitlement key is wrong" in description

    @patch("mas.cli.cli.BaseApp.validateEntitlementKey")
    @patch("mas.cli.cli.BaseApp.promptForString")
    @patch("mas.cli.cli.BaseApp.printWarning")
    def test_network_error_with_no_confirm(self, mock_print_warn, mock_prompt_string, mock_validate):
        """GIVEN a network error and --no-confirm WHEN prompting THEN it warns (network, not wrong key) and continues."""
        from requests.exceptions import Timeout as RequestsTimeout

        mock_prompt_string.return_value = "maybe-valid-key"
        mock_validate.side_effect = RequestsTimeout("Request timed out")

        app = BaseApp()
        app.noConfirm = True
        result = app.promptForEntitlementKey("IBM entitlement key", "ibm_entitlement_key")

        assert result == "maybe-valid-key"
        mock_print_warn.assert_called_once()
        warn_message = mock_print_warn.call_args[0][0]
        assert "Could not validate the entitlement key" in warn_message
        assert "key is not valid" not in warn_message


class TestValidateEntitlementKeyNonInteractive:
    """Test validateEntitlementKeyNonInteractive, used by install / restore / aiservice-install."""

    @patch("mas.cli.cli.BaseApp.validateEntitlementKey")
    @patch("mas.cli.cli.BaseApp.printWarning")
    def test_valid_key_prints_nothing(self, mock_print_warn, mock_validate):
        mock_validate.return_value = True
        app = BaseApp()
        app.noConfirm = False

        app.validateEntitlementKeyNonInteractive("good-key")

        mock_print_warn.assert_not_called()

    @patch("mas.cli.cli.BaseApp.validateEntitlementKey")
    @patch("mas.cli.cli.BaseApp.printWarning")
    def test_wrong_key_with_no_confirm_warns_key_not_valid(self, mock_print_warn, mock_validate):
        mock_validate.return_value = False
        app = BaseApp()
        app.noConfirm = True

        app.validateEntitlementKeyNonInteractive("bad-key")

        mock_print_warn.assert_called_once()
        assert "key is not valid" in mock_print_warn.call_args[0][0]

    @patch("mas.cli.cli.BaseApp.validateEntitlementKey")
    @patch("mas.cli.cli.BaseApp.promptForInt")
    @patch("mas.cli.cli.BaseApp.printWarning")
    @patch("mas.cli.cli.BaseApp.printDescription")
    def test_wrong_key_quit(self, mock_print_desc, mock_print_warn, mock_prompt_int, mock_validate):
        mock_validate.return_value = False
        mock_prompt_int.return_value = 2  # Quit
        app = BaseApp()
        app.noConfirm = False

        with pytest.raises(SystemExit) as exc_info:
            app.validateEntitlementKeyNonInteractive("bad-key")

        assert exc_info.value.code == 1

    @patch("mas.cli.cli.BaseApp.validateEntitlementKey")
    @patch("mas.cli.cli.BaseApp.printWarning")
    def test_ssl_error_with_no_confirm_warns_ssl(self, mock_print_warn, mock_validate):
        mock_validate.side_effect = EntitlementKeySSLError("SSL error")
        app = BaseApp()
        app.noConfirm = True

        app.validateEntitlementKeyNonInteractive("maybe-valid-key")

        mock_print_warn.assert_called_once()
        assert "SSL" in mock_print_warn.call_args[0][0]

    @patch("mas.cli.cli.BaseApp.validateEntitlementKey")
    @patch("mas.cli.cli.BaseApp.printWarning")
    def test_network_error_with_no_confirm_warns_network(self, mock_print_warn, mock_validate):
        from requests.exceptions import ConnectionError as RequestsConnectionError

        mock_validate.side_effect = RequestsConnectionError("unreachable")
        app = BaseApp()
        app.noConfirm = True

        app.validateEntitlementKeyNonInteractive("maybe-valid-key")

        mock_print_warn.assert_called_once()
        warn_message = mock_print_warn.call_args[0][0]
        assert "Could not validate the entitlement key" in warn_message
        assert "key is not valid" not in warn_message

    @patch("mas.cli.cli.BaseApp.validateEntitlementKey")
    @patch("mas.cli.cli.BaseApp.promptForInt")
    @patch("mas.cli.cli.BaseApp.printWarning")
    @patch("mas.cli.cli.BaseApp.printDescription")
    def test_network_error_quit(self, mock_print_desc, mock_print_warn, mock_prompt_int, mock_validate):
        from requests.exceptions import Timeout as RequestsTimeout

        mock_validate.side_effect = RequestsTimeout("timed out")
        mock_prompt_int.return_value = 2  # Quit
        app = BaseApp()
        app.noConfirm = False

        with pytest.raises(SystemExit) as exc_info:
            app.validateEntitlementKeyNonInteractive("maybe-valid-key")

        assert exc_info.value.code == 1

    @patch("mas.cli.cli.BaseApp.validateEntitlementKey")
    @patch("mas.cli.cli.BaseApp.promptForInt")
    @patch("mas.cli.cli.BaseApp.printWarning")
    @patch("mas.cli.cli.BaseApp.printDescription")
    def test_network_error_continue_anyway(self, mock_print_desc, mock_print_warn, mock_prompt_int, mock_validate):
        from requests.exceptions import Timeout as RequestsTimeout

        mock_validate.side_effect = RequestsTimeout("timed out")
        mock_prompt_int.return_value = 1  # Continue anyway
        app = BaseApp()
        app.noConfirm = False

        app.validateEntitlementKeyNonInteractive("maybe-valid-key")  # must not raise or exit

        mock_prompt_int.assert_called_once()
