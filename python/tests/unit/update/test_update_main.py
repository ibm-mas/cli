# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
# *****************************************************************************

"""Tests for the update command dispatch in __main__.py.

The dispatch rule: interactive mode is the Textual TUI, launched whenever the required non-interactive parameter (--mas-catalog-version, the one
thing the guided workflow exists to choose) is absent -- including invocations carrying optional flags such as --image-pull-policy, which are passed
through to the wizard. Providing the required parameter selects the non-interactive path.
"""

from unittest.mock import MagicMock, patch

import pytest

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


def test_main_update_optional_flag_without_catalog_calls_tui():
    """Test that an optional flag without --mas-catalog-version launches the TUI.

    GIVEN argv is ['mas-cli', 'update', '--image-pull-policy', 'Always']
    WHEN main() is called
    THEN serveTuiMode is called (optional flags pass through to the guided workflow; only the required parameter selects non-interactive mode) and
         UpdateApp.update is NOT called.
    """
    with (
        patch.object(main_module, "argv", ["mas-cli", "update", "--image-pull-policy", "Always"]),
        patch("mas.cli.tui.shell.serveTuiMode") as mockServeTui,
    ):
        main_module.main()

    mockServeTui.assert_called_once()
    call_args = mockServeTui.call_args
    assert call_args[0][0] == "update"
    # The flags are handed to the TUI for applyCliArgs passthrough
    assert call_args[0][1] == ["--image-pull-policy", "Always"]


def test_main_update_confirmation_flag_without_catalog_calls_tui():
    """Test that --no-confirm alone does not select non-interactive mode.

    GIVEN argv is ['mas-cli', 'update', '--no-confirm'] (no --mas-catalog-version)
    WHEN main() is called
    THEN serveTuiMode is called: only the required parameter selects the non-interactive path, so the guided workflow still runs.
    """
    with (
        patch.object(main_module, "argv", ["mas-cli", "update", "--no-confirm"]),
        patch("mas.cli.tui.shell.serveTuiMode") as mockServeTui,
    ):
        main_module.main()

    mockServeTui.assert_called_once()


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


def test_main_update_with_catalog_equals_form_does_not_call_tui():
    """Test that '--catalog=v9-amd64' (equals form) selects the non-interactive path.

    GIVEN argv is ['mas-cli', 'update', '--catalog=v9-amd64']
    WHEN main() is called
    THEN serveTuiMode is NOT called and UpdateApp.update IS called.
    """
    mock_update_app = MagicMock()
    mock_update_app_class = MagicMock(return_value=mock_update_app)

    with (
        patch.object(main_module, "argv", ["mas-cli", "update", "--catalog=v9-amd64"]),
        patch("mas.cli.tui.shell.serveTuiMode") as mockServeTui,
        patch("mas.cli.update.app.UpdateApp", mock_update_app_class),
    ):
        try:
            main_module.main()
        except SystemExit:
            pass

    mockServeTui.assert_not_called()
    mock_update_app.update.assert_called_once()


def test_main_update_help_is_handled_by_argparse_at_dispatch():
    """Test that 'update --help' prints usage and exits at the dispatch parse.

    GIVEN argv is ['mas-cli', 'update', '--help']
    WHEN main() is called
    THEN argparse handles --help during the dispatch parse (SystemExit) -- neither the TUI nor UpdateApp is constructed.
    """
    with (
        patch.object(main_module, "argv", ["mas-cli", "update", "--help"]),
        patch("mas.cli.tui.shell.serveTuiMode") as mockServeTui,
        patch("mas.cli.update.app.UpdateApp") as mock_update_app_class,
    ):
        with pytest.raises(SystemExit) as excinfo:
            main_module.main()

        # argparse exits 0 for --help
        assert excinfo.value.code == 0

    mockServeTui.assert_not_called()
    mock_update_app_class.assert_not_called()


def test_main_update_unknown_flag_fails_with_usage_at_dispatch():
    """Test that an unknown flag fails with usage before either path runs.

    GIVEN argv is ['mas-cli', 'update', '--not-a-real-flag']
    WHEN main() is called
    THEN the dispatch parse exits with argparse's usage error -- the flag is neither silently ignored by the TUI nor deferred to the classic path.
    """
    with (
        patch.object(main_module, "argv", ["mas-cli", "update", "--not-a-real-flag"]),
        patch("mas.cli.tui.shell.serveTuiMode") as mockServeTui,
        patch("mas.cli.update.app.UpdateApp") as mock_update_app_class,
    ):
        with pytest.raises(SystemExit) as excinfo:
            main_module.main()

        # argparse exits 2 for usage errors
        assert excinfo.value.code == 2

    mockServeTui.assert_not_called()
    mock_update_app_class.assert_not_called()
