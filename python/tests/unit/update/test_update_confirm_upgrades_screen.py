# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Logic tests for the ConfirmUpgradesScreen (tui/screens/confirm_upgrades.py).

Covers the confirmation-validation and params write-back logic without a
running Textual app, using real UpdateApp instances from the shared
scenario registry so the pending-confirmation helpers compute exactly as
production code does. The live button flow is covered by the pilot tests in
tests/pilot/update/test_confirm_upgrades_screen.py.
"""

import pytest
from unittest.mock import patch

from mas.cli.tui.models import WorkflowStep
from scenarios.update import update_scenario

pytestmark = pytest.mark.tui


def _make_screen(scenario: str, license_path: str | None = None):
    """Return a ConfirmUpgradesScreen constructed without Textual.

    Args:
        scenario (str): Named UpdateApp state (see scenarios/update.py).
        license_path (str, optional): Pre-provided Db2 license path.

    Returns:
        tuple: (screen, mas_app) — the screen and its scenario app.
    """
    from mas.cli.tui.screens.confirm_upgrades import ConfirmUpgradesScreen

    mas_app = update_scenario(scenario, license_path=license_path)
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

    GIVEN a screen in the mongo-major scenario and a mock unchecked checkbox
    WHEN _requiredChecked() is called
    THEN it returns False.
    """
    screen, _ = _make_screen("mongo-major")

    checkbox = type("Checkbox", (), {"value": False})()
    with patch.object(screen, "query_one", return_value=checkbox):
        assert screen._requiredChecked() is False


def test_required_checked_false_when_db2_unchecked():
    """Test that _requiredChecked returns False while the Db2 checkbox is unchecked.

    GIVEN a screen in the db2-major-no-license scenario (checkbox rendered)
         and a mock unchecked checkbox
    WHEN _requiredChecked() is called
    THEN it returns False.
    """
    screen, _ = _make_screen("db2-major-no-license")

    checkbox = type("Checkbox", (), {"value": False})()
    with patch.object(screen, "query_one", return_value=checkbox):
        assert screen._requiredChecked() is False


def test_required_checked_true_when_all_checked():
    """Test that _requiredChecked returns True when all required checkboxes are checked.

    GIVEN a screen in the mongo-major scenario and a mock checked checkbox
    WHEN _requiredChecked() is called
    THEN it returns True.
    """
    screen, _ = _make_screen("mongo-major")

    checkbox = type("Checkbox", (), {"value": True})()
    with patch.object(screen, "query_one", return_value=checkbox):
        assert screen._requiredChecked() is True


def test_required_checked_true_when_license_covers_db2():
    """Test that no Db2 checkbox is required when the license path is the confirmation.

    GIVEN a screen in the db2-v11-to-v12 scenario (license file needed)
    WHEN _requiredChecked() is called with no Db2 checkbox rendered
    THEN it returns True — the license path input is the confirmation.
    """
    screen, _ = _make_screen("db2-v11-to-v12")

    with patch.object(screen, "query_one", side_effect=Exception("no such widget")):
        assert screen._requiredChecked() is True


def test_license_provided_false_when_empty():
    """Test that _licenseProvided returns False when the license input is empty.

    GIVEN a screen in the db2-v11-to-v12 scenario and a mock empty input
    WHEN _licenseProvided() is called
    THEN it returns False.
    """
    screen, _ = _make_screen("db2-v11-to-v12")

    inp = type("Input", (), {"value": "   "})()
    with patch.object(screen, "query_one", return_value=inp):
        assert screen._licenseProvided() is False


def test_license_provided_true_when_path_entered():
    """Test that _licenseProvided returns True when the license input has a path.

    GIVEN a screen in the db2-v11-to-v12 scenario and a mock filled input
    WHEN _licenseProvided() is called
    THEN it returns True.
    """
    screen, _ = _make_screen("db2-v11-to-v12")

    inp = type("Input", (), {"value": " /path/to/license "})()
    with patch.object(screen, "query_one", return_value=inp):
        assert screen._licenseProvided() is True


def test_license_provided_true_when_not_needed():
    """Test that _licenseProvided returns True when no license file is needed.

    GIVEN a screen in the clean scenario
    WHEN _licenseProvided() is called
    THEN it returns True without querying any widget.
    """
    screen, _ = _make_screen("clean")

    with patch.object(screen, "query_one", side_effect=AssertionError("should not query")):
        assert screen._licenseProvided() is True


def test_write_confirmations_sets_params_and_license():
    """Test that _writeConfirmations writes the confirmation params and license path.

    GIVEN a screen in the mongo-and-db2-v12 scenario
    WHEN _writeConfirmations() is called with a mock license input
    THEN mongodb_v8_upgrade and db2_v12_upgrade are set to "true" and
         db2LicenseFileLocal is set on the app.
    """
    screen, mas_app = _make_screen("mongo-and-db2-v12")

    inp = type("Input", (), {"value": "/path/to/license"})()
    with patch.object(screen, "query_one", return_value=inp):
        screen._writeConfirmations()

    assert mas_app.getParam("mongodb_v8_upgrade") == "true"
    assert mas_app.getParam("db2_v12_upgrade") == "true"
    assert mas_app.db2LicenseFileLocal == "/path/to/license"


def test_write_confirmations_noop_when_nothing_pending():
    """Test that _writeConfirmations sets nothing when no confirmations are pending.

    GIVEN a screen in the clean scenario
    WHEN _writeConfirmations() is called
    THEN no params are written and db2LicenseFileLocal stays None.
    """
    screen, mas_app = _make_screen("clean")

    screen._writeConfirmations()

    assert not [k for k in mas_app.params if k.endswith("_upgrade")]
    assert mas_app.db2LicenseFileLocal is None


def test_write_confirmations_skips_db2_param_when_already_confirmed():
    """Test that _writeConfirmations writes only the license when the Db2 upgrade is pre-confirmed.

    GIVEN a screen in the db2-license-only scenario (db2_v12_upgrade already
         "true", license still needed)
    WHEN _writeConfirmations() is called with a mock license input
    THEN the license path is written and the db2_v12_upgrade param is
         unchanged.
    """
    screen, mas_app = _make_screen("db2-license-only")

    inp = type("Input", (), {"value": "/path/to/license"})()
    with patch.object(screen, "query_one", return_value=inp):
        screen._writeConfirmations()

    assert mas_app.getParam("db2_v12_upgrade") == "true"
    assert mas_app.db2LicenseFileLocal == "/path/to/license"
