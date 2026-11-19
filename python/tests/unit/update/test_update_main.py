# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for the update command dispatch in __main__.py.

The dispatch rule: a bare ``mas-cli update`` invocation launches the Textual
TUI; any command-line flag falls through to the classic CLI path so that
nothing the TUI does not yet support is silently ignored.
"""

from unittest.mock import MagicMock, patch

import mas.cli.__main__ as main_module


def test_main_update_bare_invocation_calls_serve_tui_mode():
    """Test that calling main() with a bare 'update' invokes serveTuiMode.

    GIVEN argv is ['mas-cli', 'update'] with no arguments
    WHEN main() is called
    THEN serveTuiMode is called for the update command and UpdateApp.update is NOT called.
    """
    with (
        patch.object(main_module, "argv", ["mas-cli", "update"]),
        patch("mas.cli.tui.shell.serveTuiMode") as mockServeTui,
    ):
        main_module.main()

    mockServeTui.assert_called_once()
    call_args = mockServeTui.call_args
    assert call_args[0][0] == "update"


def test_main_update_with_catalog_does_not_call_tui():
    """Test that calling main() with 'update --catalog ...' does NOT invoke serveTuiMode.

    GIVEN argv is ['mas-cli', 'update', '--catalog', 'v9-amd64']
    WHEN main() is called
    THEN serveTuiMode is NOT called and UpdateApp.update IS called.
    """
    mock_update_app = MagicMock()
    mock_update_app_class = MagicMock(return_value=mock_update_app)

    with (
        patch.object(main_module, "argv", ["mas-cli", "update", "--catalog", "v9-amd64"]),
        patch("mas.cli.tui.shell.serveTuiMode") as mockServeTui,
        patch("mas.cli.update.app.UpdateApp", mock_update_app_class),
    ):
        try:
            main_module.main()
        except SystemExit:
            pass

    mockServeTui.assert_not_called()
    mock_update_app.printBanner.assert_called_once()
    mock_update_app.update.assert_called_once()


def test_main_update_with_any_flag_falls_through_to_cli():
    """Test that any flag on 'update' takes the classic CLI path.

    GIVEN argv is ['mas-cli', 'update', '--no-confirm']
    WHEN main() is called
    THEN serveTuiMode is NOT called (flags are never silently ignored by the TUI)
         and UpdateApp.update IS called.
    """
    mock_update_app = MagicMock()
    mock_update_app_class = MagicMock(return_value=mock_update_app)

    with (
        patch.object(main_module, "argv", ["mas-cli", "update", "--no-confirm"]),
        patch("mas.cli.tui.shell.serveTuiMode") as mockServeTui,
        patch("mas.cli.update.app.UpdateApp", mock_update_app_class),
    ):
        try:
            main_module.main()
        except SystemExit:
            pass

    mockServeTui.assert_not_called()
    mock_update_app.update.assert_called_once()


def test_main_update_help_falls_through_to_cli():
    """Test that 'update --help' takes the classic CLI path (argparse help).

    GIVEN argv is ['mas-cli', 'update', '--help']
    WHEN main() is called
    THEN serveTuiMode is NOT called and UpdateApp.update IS called (argparse
         handles --help by printing usage and exiting).
    """
    mock_update_app = MagicMock()
    mock_update_app_class = MagicMock(return_value=mock_update_app)

    with (
        patch.object(main_module, "argv", ["mas-cli", "update", "--help"]),
        patch("mas.cli.tui.shell.serveTuiMode") as mockServeTui,
        patch("mas.cli.update.app.UpdateApp", mock_update_app_class),
    ):
        try:
            main_module.main()
        except SystemExit:
            pass

    mockServeTui.assert_not_called()
    mock_update_app.update.assert_called_once()
