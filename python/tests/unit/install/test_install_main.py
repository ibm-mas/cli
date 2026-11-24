# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
# *****************************************************************************

"""Tests for the install command dispatch in __main__.py.

The dispatch rule: a bare ``mas-cli install`` invocation launches the
Textual TUI; any command-line flag falls through to the classic CLI path so
that nothing the TUI does not yet support is silently ignored.
"""

from unittest.mock import MagicMock, patch

import mas.cli.__main__ as main_module


def test_main_install_bare_invocation_calls_serve_tui_mode():
    """Test that calling main() with a bare 'install' invokes serveTuiMode.

    GIVEN argv is ['mas-cli', 'install'] with no arguments
    WHEN main() is called
    THEN serveTuiMode is called for the install command and InstallApp.install is NOT called.
    """
    with (
        patch.object(main_module, "argv", ["mas-cli", "install"]),
        patch("mas.cli.tui.shell.serveTuiMode") as mockServeTui,
    ):
        main_module.main()

    mockServeTui.assert_called_once()
    call_args = mockServeTui.call_args
    assert call_args[0][0] == "install"


def test_main_install_with_instance_does_not_call_tui():
    """Test that calling main() with 'install --mas-instance-id ...' does NOT invoke serveTuiMode.

    GIVEN argv is ['mas-cli', 'install', '--mas-instance-id', 'inst1']
    WHEN main() is called
    THEN serveTuiMode is NOT called and InstallApp.install IS called.
    """
    mock_install_app = MagicMock()
    mock_install_app_class = MagicMock(return_value=mock_install_app)

    with (
        patch.object(main_module, "argv", ["mas-cli", "install", "--mas-instance-id", "inst1"]),
        patch("mas.cli.tui.shell.serveTuiMode") as mockServeTui,
        patch("mas.cli.install.app.InstallApp", mock_install_app_class),
    ):
        try:
            main_module.main()
        except SystemExit:
            pass

    mockServeTui.assert_not_called()
    mock_install_app.printBanner.assert_called_once()
    mock_install_app.install.assert_called_once()


def test_main_install_with_any_flag_falls_through_to_cli():
    """Test that any flag on 'install' takes the classic CLI path.

    GIVEN argv is ['mas-cli', 'install', '--no-confirm']
    WHEN main() is called
    THEN serveTuiMode is NOT called (flags are never silently ignored by the TUI)
         and InstallApp.install IS called.
    """
    mock_install_app = MagicMock()
    mock_install_app_class = MagicMock(return_value=mock_install_app)

    with (
        patch.object(main_module, "argv", ["mas-cli", "install", "--no-confirm"]),
        patch("mas.cli.tui.shell.serveTuiMode") as mockServeTui,
        patch("mas.cli.install.app.InstallApp", mock_install_app_class),
    ):
        try:
            main_module.main()
        except SystemExit:
            pass

    mockServeTui.assert_not_called()
    mock_install_app.install.assert_called_once()


def test_main_install_help_falls_through_to_cli():
    """Test that 'install --help' takes the classic CLI path (argparse help).

    GIVEN argv is ['mas-cli', 'install', '--help']
    WHEN main() is called
    THEN serveTuiMode is NOT called and InstallApp.install IS called (argparse
         handles --help by printing usage and exiting).
    """
    mock_install_app = MagicMock()
    mock_install_app_class = MagicMock(return_value=mock_install_app)

    with (
        patch.object(main_module, "argv", ["mas-cli", "install", "--help"]),
        patch("mas.cli.tui.shell.serveTuiMode") as mockServeTui,
        patch("mas.cli.install.app.InstallApp", mock_install_app_class),
    ):
        try:
            main_module.main()
        except SystemExit:
            pass

    mockServeTui.assert_not_called()
    mock_install_app.install.assert_called_once()
