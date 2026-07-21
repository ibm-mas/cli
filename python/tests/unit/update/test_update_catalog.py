# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for mas.cli.update.catalog — CatalogMixin.

All tests follow the GIVEN-WHEN-THEN convention and verify that:
- CatalogMixin is importable from its own module
- UpdateApp inherits CatalogMixin so all catalog methods are present
- The public API surface is unchanged after the refactor
"""

from mas.cli.update.catalog import CatalogMixin
from mas.cli.update.app import UpdateApp


def test_catalog_mixin_is_importable():
    """Test that CatalogMixin can be imported from mas.cli.update.catalog.

    GIVEN the refactored package structure
    WHEN CatalogMixin is imported from mas.cli.update.catalog
    THEN the import succeeds without error.
    """
    assert CatalogMixin is not None


def test_update_app_inherits_catalog_mixin():
    """Test that UpdateApp includes CatalogMixin in its MRO.

    GIVEN the refactored UpdateApp class
    WHEN its MRO is inspected
    THEN CatalogMixin appears in the inheritance chain.
    """
    assert CatalogMixin in UpdateApp.__mro__


def test_catalog_methods_present_on_update_app():
    """Test that all catalog methods are accessible on UpdateApp.

    GIVEN the refactored UpdateApp class
    WHEN each catalog method name is looked up on the class
    THEN each method is present (inherited from CatalogMixin).
    """
    expectedMethods = [
        "reviewCurrentCatalog",
        "reviewMASInstance",
        "reviewAiServiceInstance",
        "reviewInstances",
        "getCatalogOptions",
        "chooseCatalog",
        "checkCatalog",
        "validateCatalog",
    ]
    for methodName in expectedMethods:
        assert hasattr(UpdateApp, methodName), f"UpdateApp is missing method: {methodName}"


def test_get_catalog_options_returns_list():
    """Test that getCatalogOptions is defined on CatalogMixin and returns a list.

    GIVEN CatalogMixin
    WHEN getCatalogOptions is called on a minimal stub that satisfies the mixin
    THEN it returns a non-empty list of strings.
    """

    class Stub(CatalogMixin):
        pass

    stub = Stub()
    options = stub.getCatalogOptions()
    assert isinstance(options, list)
    assert len(options) > 0
    for option in options:
        assert isinstance(option, str)
