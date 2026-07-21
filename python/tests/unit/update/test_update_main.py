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

All tests follow the RED-GREEN-REFACTOR TDD cycle.
"""

from unittest.mock import MagicMock, patch

import mas.cli.__main__ as main_module


def test_main_update_no_catalog_calls_serve_tui_mode():
    """Test that calling main() with 'update' (no --catalog) invokes serveTuiMode.

    GIVEN argv is ['mas-cli', 'update'] with no --catalog flag
    WHEN main() is called
    THEN serveTuiMode is called and UpdateApp.update is NOT called.
    """
    with (
        patch.object(main_module, "argv", ["mas-cli", "update"]),
        patch.object(main_module, "serveTuiMode") as mockServeTui,
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
        patch.object(main_module, "serveTuiMode") as mockServeTui,
        patch("mas.cli.update.app.UpdateApp", mock_update_app_class),
    ):
        try:
            main_module.main()
        except SystemExit:
            pass

    mockServeTui.assert_not_called()
    mock_update_app.update.assert_called_once()
