# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for the pre-install RBAC evaluation methods on UpdateApp.

All tests follow the GIVEN-WHEN-THEN convention and verify that:
- Both RBAC methods are accessible on UpdateApp
- shouldApplyRBACForInstance only applies RBAC for pre-release to GA transitions
"""

from unittest.mock import MagicMock, patch

from mas.cli.update.app import UpdateApp


def _make_app() -> UpdateApp:
    """Return a minimal UpdateApp instance with a mocked dynamic client."""
    app = UpdateApp()
    app._dynClient = MagicMock()
    return app


def test_rbac_methods_present_on_update_app():
    """Test that both RBAC methods are accessible on UpdateApp.

    GIVEN the UpdateApp class
    WHEN each RBAC method name is looked up on the class
    THEN each method is present.
    """
    expectedMethods = [
        "shouldApplyRBACForInstance",
        "evaluatePreinstallRBACAccessForUpdate",
    ]
    for methodName in expectedMethods:
        assert hasattr(UpdateApp, methodName), f"UpdateApp is missing method: {methodName}"


@patch("mas.cli.update.app.getMasChannel", return_value="9.2.x")
def test_should_apply_rbac_for_pre_release_to_ga(mock_channel):
    """Test that RBAC applies when transitioning from pre-release to GA.

    GIVEN an instance on 9.2.0-pre.stable+123 targeting a 9.2.0 GA catalog
    WHEN shouldApplyRBACForInstance is called
    THEN it returns True.
    """
    app = _make_app()
    targetCatalog = {"mas_core_version": {"9.2.x": "9.2.0"}}

    assert app.shouldApplyRBACForInstance("inst1", "9.2.0-pre.stable+123", targetCatalog) is True


@patch("mas.cli.update.app.getMasChannel", return_value="9.2.x")
def test_should_not_apply_rbac_for_ga_instance(mock_channel):
    """Test that RBAC does not apply when the instance is already GA.

    GIVEN an instance already on a GA version
    WHEN shouldApplyRBACForInstance is called
    THEN it returns False.
    """
    app = _make_app()
    targetCatalog = {"mas_core_version": {"9.2.x": "9.2.0"}}

    assert app.shouldApplyRBACForInstance("inst1", "9.2.0", targetCatalog) is False


@patch("mas.cli.update.app.getMasChannel", return_value="9.2.x")
def test_should_not_apply_rbac_when_target_stays_pre_release(mock_channel):
    """Test that RBAC does not apply when the target version is also pre-release.

    GIVEN an instance on a pre-release version targeting another pre-release
    WHEN shouldApplyRBACForInstance is called
    THEN it returns False.
    """
    app = _make_app()
    targetCatalog = {"mas_core_version": {"9.2.x": "9.2.1-pre.stable+999"}}

    assert app.shouldApplyRBACForInstance("inst1", "9.2.0-pre.stable+123", targetCatalog) is False
