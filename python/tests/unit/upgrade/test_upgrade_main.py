# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
# *****************************************************************************

"""Tests for the upgrade command dispatch in __main__.py.

The dispatch rule: a bare ``mas-cli upgrade`` invocation launches the
Textual TUI; any command-line flag falls through to the classic CLI path so
that nothing the TUI does not yet support is silently ignored.
"""

from unittest.mock import MagicMock, patch

import mas.cli.__main__ as main_module


def test_main_upgrade_bare_invocation_calls_serve_tui_mode():
    """Test that calling main() with a bare 'upgrade' invokes serveTuiMode.

    GIVEN argv is ['mas-cli', 'upgrade'] with no arguments
    WHEN main() is called
    THEN serveTuiMode is called for the upgrade command and UpgradeApp.upgrade is NOT called.
    """
    with (
        patch.object(main_module, "argv", ["mas-cli", "upgrade"]),
        patch("mas.cli.tui.shell.serveTuiMode") as mockServeTui,
    ):
        main_module.main()

    mockServeTui.assert_called_once()
    call_args = mockServeTui.call_args
    assert call_args[0][0] == "upgrade"


def test_main_upgrade_with_instance_does_not_call_tui():
    """Test that calling main() with 'upgrade --mas-instance-id ...' does NOT invoke serveTuiMode.

    GIVEN argv is ['mas-cli', 'upgrade', '--mas-instance-id', 'inst1']
    WHEN main() is called
    THEN serveTuiMode is NOT called and UpgradeApp.upgrade IS called.
    """
    mock_upgrade_app = MagicMock()
    mock_upgrade_app_class = MagicMock(return_value=mock_upgrade_app)

    with (
        patch.object(main_module, "argv", ["mas-cli", "upgrade", "--mas-instance-id", "inst1"]),
        patch("mas.cli.tui.shell.serveTuiMode") as mockServeTui,
        patch("mas.cli.upgrade.app.UpgradeApp", mock_upgrade_app_class),
    ):
        try:
            main_module.main()
        except SystemExit:
            pass

    mockServeTui.assert_not_called()
    mock_upgrade_app.printBanner.assert_called_once()
    mock_upgrade_app.upgrade.assert_called_once()


def test_main_upgrade_with_any_flag_falls_through_to_cli():
    """Test that any flag on 'upgrade' takes the classic CLI path.

    GIVEN argv is ['mas-cli', 'upgrade', '--no-confirm']
    WHEN main() is called
    THEN serveTuiMode is NOT called (flags are never silently ignored by the TUI)
         and UpgradeApp.upgrade IS called.
    """
    mock_upgrade_app = MagicMock()
    mock_upgrade_app_class = MagicMock(return_value=mock_upgrade_app)

    with (
        patch.object(main_module, "argv", ["mas-cli", "upgrade", "--no-confirm"]),
        patch("mas.cli.tui.shell.serveTuiMode") as mockServeTui,
        patch("mas.cli.upgrade.app.UpgradeApp", mock_upgrade_app_class),
    ):
        try:
            main_module.main()
        except SystemExit:
            pass

    mockServeTui.assert_not_called()
    mock_upgrade_app.upgrade.assert_called_once()


def test_main_upgrade_help_falls_through_to_cli():
    """Test that 'upgrade --help' takes the classic CLI path (argparse help).

    GIVEN argv is ['mas-cli', 'upgrade', '--help']
    WHEN main() is called
    THEN serveTuiMode is NOT called and UpgradeApp.upgrade IS called (argparse
         handles --help by printing usage and exiting).
    """
    mock_upgrade_app = MagicMock()
    mock_upgrade_app_class = MagicMock(return_value=mock_upgrade_app)

    with (
        patch.object(main_module, "argv", ["mas-cli", "upgrade", "--help"]),
        patch("mas.cli.tui.shell.serveTuiMode") as mockServeTui,
        patch("mas.cli.upgrade.app.UpgradeApp", mock_upgrade_app_class),
    ):
        try:
            main_module.main()
        except SystemExit:
            pass

    mockServeTui.assert_not_called()
    mock_upgrade_app.upgrade.assert_called_once()
