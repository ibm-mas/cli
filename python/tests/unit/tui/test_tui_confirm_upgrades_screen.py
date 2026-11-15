# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for the ConfirmUpgradesScreen TUI widget (tui/screens/confirm_upgrades.py).

Tests that do not require a running Textual app (importability, confirmation
validation, and params write-back) are covered here. Rendering and the
Confirm / Abort button behaviour with a live Textual pilot are documented as
a manual smoke test.
"""

import pytest
from unittest.mock import MagicMock, patch

from mas.cli.tui.models import WorkflowStep

pytestmark = pytest.mark.tui


def _make_screen(mongoPending=False, db2Pending=False, licenseNeeded=False, params=None):
    """Return a ConfirmUpgradesScreen constructed without Textual.

    Args:
        mongoPending (bool): Whether a MongoDB confirmation is pending.
        db2Pending (bool): Whether a Db2 confirmation is pending.
        licenseNeeded (bool): Whether a Db2 v12 license file is needed.
        params (dict, optional): Initial params dict on the stub app.

    Returns:
        tuple: (screen, mas_app) — the screen and its stub app.
    """
    from mas.cli.tui.screens.confirm_upgrades import ConfirmUpgradesScreen

    mas_app = MagicMock()
    mas_app.params = params if params is not None else {}
    mas_app.mongoUpgradeConfirmationPending.return_value = mongoPending
    mas_app.db2UpgradeConfirmationPending.return_value = db2Pending
    mas_app.db2LicenseFileNeeded.return_value = licenseNeeded
    mas_app.mongoTargetVersion = "8.0.14"
    mas_app.mongoCurrentVersion = "7.0.5"
    mas_app.db2CurrentMajorVersion = 11
    mas_app.db2TargetMajorVersion = 12
    mas_app.getParam = lambda key: mas_app.params.get(key, "")
    mas_app.setParam = lambda key, value: mas_app.params.__setitem__(key, value)

    step = WorkflowStep(id="confirm-upgrades", heading="Confirm Upgrade Requirements")
    screen = ConfirmUpgradesScreen.__new__(ConfirmUpgradesScreen)
    ConfirmUpgradesScreen.__init__(screen, mas_app, step, 3)
    return screen, mas_app


def test_confirm_upgrades_screen_is_importable():
    """Test that ConfirmUpgradesScreen can be imported from the screens package.

    GIVEN the mas.cli.tui.screens package
    WHEN ConfirmUpgradesScreen is imported
    THEN no ImportError is raised.
    """
    from mas.cli.tui.screens import ConfirmUpgradesScreen  # noqa: F401

    assert ConfirmUpgradesScreen is not None


def test_required_checked_false_when_mongo_unchecked():
    """Test that _requiredChecked returns False while a required checkbox is unchecked.

    GIVEN a screen with a pending MongoDB confirmation and a mock unchecked checkbox
    WHEN _requiredChecked() is called
    THEN it returns False.
    """
    screen, _ = _make_screen(mongoPending=True)

    checkbox = MagicMock()
    checkbox.value = False
    with patch.object(screen, "query_one", return_value=checkbox):
        assert screen._requiredChecked() is False


def test_required_checked_true_when_all_checked():
    """Test that _requiredChecked returns True when all required checkboxes are checked.

    GIVEN a screen with pending MongoDB and Db2 confirmations and mock checked checkboxes
    WHEN _requiredChecked() is called
    THEN it returns True.
    """
    screen, _ = _make_screen(mongoPending=True, db2Pending=True)

    checkbox = MagicMock()
    checkbox.value = True
    with patch.object(screen, "query_one", return_value=checkbox):
        assert screen._requiredChecked() is True


def test_license_provided_false_when_empty():
    """Test that _licenseProvided returns False when the license input is empty.

    GIVEN a screen with a pending Db2 v11 to v12 license requirement and a mock empty input
    WHEN _licenseProvided() is called
    THEN it returns False.
    """
    screen, _ = _make_screen(licenseNeeded=True)

    inp = MagicMock()
    inp.value = "   "
    with patch.object(screen, "query_one", return_value=inp):
        assert screen._licenseProvided() is False


def test_license_provided_true_when_path_entered():
    """Test that _licenseProvided returns True when the license input has a path.

    GIVEN a screen with a pending Db2 v11 to v12 license requirement and a mock filled input
    WHEN _licenseProvided() is called
    THEN it returns True.
    """
    screen, _ = _make_screen(licenseNeeded=True)

    inp = MagicMock()
    inp.value = " /path/to/license "
    with patch.object(screen, "query_one", return_value=inp):
        assert screen._licenseProvided() is True


def test_license_provided_true_when_not_needed():
    """Test that _licenseProvided returns True when no license file is needed.

    GIVEN a screen with no pending license requirement
    WHEN _licenseProvided() is called
    THEN it returns True without querying any widget.
    """
    screen, _ = _make_screen(licenseNeeded=False)

    with patch.object(screen, "query_one", side_effect=AssertionError("should not query")):
        assert screen._licenseProvided() is True


def test_write_confirmations_sets_params_and_license():
    """Test that _writeConfirmations writes the confirmation params and license path.

    GIVEN a screen with pending MongoDB and Db2 v11 to v12 confirmations
    WHEN _writeConfirmations() is called with a mock license input
    THEN mongodb_v8_upgrade and db2_v12_upgrade are set to "true" and
         db2LicenseFileLocal is set on the app.
    """
    screen, mas_app = _make_screen(mongoPending=True, db2Pending=True, licenseNeeded=True)

    inp = MagicMock()
    inp.value = "/path/to/license"
    with patch.object(screen, "query_one", return_value=inp):
        screen._writeConfirmations()

    assert mas_app.params.get("mongodb_v8_upgrade") == "true"
    assert mas_app.params.get("db2_v12_upgrade") == "true"
    assert mas_app.db2LicenseFileLocal == "/path/to/license"


def test_write_confirmations_noop_when_nothing_pending():
    """Test that _writeConfirmations sets nothing when no confirmations are pending.

    GIVEN a screen with no pending confirmations
    WHEN _writeConfirmations() is called
    THEN no params are written and db2LicenseFileLocal is untouched.
    """
    screen, mas_app = _make_screen()

    screen._writeConfirmations()

    assert not [k for k in mas_app.params if k.endswith("_upgrade")]
