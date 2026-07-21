# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for mas.cli.update.rbac — UpdateRBACMixin.

All tests follow the GIVEN-WHEN-THEN convention and verify that:
- UpdateRBACMixin is importable from its own module
- UpdateApp inherits UpdateRBACMixin
- Both RBAC methods are accessible on UpdateApp
"""

from mas.cli.update.rbac import UpdateRBACMixin
from mas.cli.update.app import UpdateApp


def test_update_rbac_mixin_is_importable():
    """Test that UpdateRBACMixin can be imported from mas.cli.update.rbac.

    GIVEN the refactored package structure
    WHEN UpdateRBACMixin is imported from mas.cli.update.rbac
    THEN the import succeeds without error.
    """
    assert UpdateRBACMixin is not None


def test_update_app_inherits_update_rbac_mixin():
    """Test that UpdateApp includes UpdateRBACMixin in its MRO.

    GIVEN the refactored UpdateApp class
    WHEN its MRO is inspected
    THEN UpdateRBACMixin appears in the inheritance chain.
    """
    assert UpdateRBACMixin in UpdateApp.__mro__


def test_rbac_methods_present_on_update_app():
    """Test that both RBAC methods are accessible on UpdateApp.

    GIVEN the refactored UpdateApp class
    WHEN each RBAC method name is looked up on the class
    THEN each method is present (inherited from UpdateRBACMixin).
    """
    expectedMethods = [
        "shouldApplyRBACForInstance",
        "evaluatePreinstallRBACAccessForUpdate",
    ]
    for methodName in expectedMethods:
        assert hasattr(UpdateApp, methodName), f"UpdateApp is missing method: {methodName}"
