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
Unit tests for the promptForSelect helper in PromptMixin.

promptForSelect presents a short option set as a select list (arrow keys +
Enter) with the default pre-selected, replacing the numeric
"choose 1 or 2" promptForListSelect interaction for short lists.  The
radiolist_dialog it builds on is mocked, so these tests cover the wrapper
contract: default pre-selection, param storage and cancellation.
"""

from unittest.mock import patch

from mas.cli.displayMixins import PromptMixin


class SelectStub(PromptMixin):
    """Minimal host for PromptMixin providing the params dict and setParam."""

    def __init__(self):
        self.params = {}

    def setParam(self, param: str, value: str) -> None:
        self.params[param] = value


class TestPromptForSelect:
    """Tests for PromptMixin.promptForSelect."""

    @patch("mas.cli.displayMixins.radiolist_dialog")
    def test_selection_is_stored_under_param(self, mock_dialog):
        """GIVEN the dialog returns a selection
        WHEN promptForSelect runs
        THEN the selection is stored under the param and returned
        """
        mock_dialog.return_value.run.return_value = "Manual"
        stub = SelectStub()

        result = stub.promptForSelect("Select the mode", ["Automatic", "Manual"], "olm_approval_mode", default="Automatic")

        assert result == "Manual"
        assert stub.params["olm_approval_mode"] == "Manual"

    @patch("mas.cli.displayMixins.radiolist_dialog")
    def test_default_is_pre_selected(self, mock_dialog):
        """GIVEN an explicit default
        WHEN promptForSelect runs
        THEN the dialog is built with that default and it is labelled
        """
        mock_dialog.return_value.run.return_value = "Manual"
        stub = SelectStub()

        stub.promptForSelect("Select the mode", ["Automatic", "Manual"], default="Manual")

        assert mock_dialog.call_args.kwargs["default"] == "Manual"
        values = mock_dialog.call_args.kwargs["values"]
        assert ("Manual", "Manual (default)") in values
        assert ("Automatic", "Automatic") in values

    @patch("mas.cli.displayMixins.radiolist_dialog")
    def test_first_option_is_the_default_when_unspecified(self, mock_dialog):
        """GIVEN no default
        WHEN promptForSelect runs
        THEN the first option is pre-selected
        """
        mock_dialog.return_value.run.return_value = "Automatic"
        stub = SelectStub()

        stub.promptForSelect("Select the mode", ["Automatic", "Manual"])

        assert mock_dialog.call_args.kwargs["default"] == "Automatic"

    @patch("mas.cli.displayMixins.radiolist_dialog")
    def test_unknown_default_falls_back_to_first_option(self, mock_dialog):
        """GIVEN a default that is not among the options
        WHEN promptForSelect runs
        THEN the first option is pre-selected rather than raising
        """
        mock_dialog.return_value.run.return_value = "Automatic"
        stub = SelectStub()

        stub.promptForSelect("Select the mode", ["Automatic", "Manual"], default="Banana")

        assert mock_dialog.call_args.kwargs["default"] == "Automatic"

    @patch("mas.cli.displayMixins.radiolist_dialog")
    def test_cancellation_returns_none_without_storing(self, mock_dialog):
        """GIVEN the dialog is cancelled (Esc)
        WHEN promptForSelect runs
        THEN None is returned and no param is stored (the caller decides)
        """
        mock_dialog.return_value.run.return_value = None
        stub = SelectStub()

        result = stub.promptForSelect("Select the mode", ["Automatic", "Manual"], "olm_approval_mode")

        assert result is None
        assert "olm_approval_mode" not in stub.params

    def test_empty_options_are_rejected(self):
        """GIVEN no options
        WHEN promptForSelect runs
        THEN ValueError is raised
        """
        stub = SelectStub()
        try:
            stub.promptForSelect("Select the mode", [])
        except ValueError as e:
            assert "at least one option" in str(e)
        else:
            raise AssertionError("expected ValueError")
