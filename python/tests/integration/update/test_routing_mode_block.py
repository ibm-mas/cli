# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for UpdateApp.checkRoutingModeForUpdate().

Verifies that the update pre-flight check blocks a catalog update when a MAS 9.2+
instance has spec.settings.routingMode set to "path" while the installed catalog does
not support path-based routing and the target catalog does.
"""

import pytest
from unittest.mock import MagicMock, patch
from mas.cli.update.app import UpdateApp

UNSUPPORTED_CATALOG = "v9-260827-amd64"
SUPPORTED_CATALOG = "v9-260924-amd64"


def _make_app(installedCatalogId, targetCatalog) -> UpdateApp:
    """Create a minimal UpdateApp instance for direct method testing.

    Args:
        installedCatalogId (str | None): The catalog ID currently installed on the cluster.
        targetCatalog (str): The catalog version selected for the update.

    Returns:
        UpdateApp: App instance with a mocked dynamic client.
    """
    app = UpdateApp()
    app._dynClient = MagicMock()
    app.params = {"mas_catalog_version": targetCatalog}
    app.installedCatalogId = installedCatalogId
    return app


def _make_instance(reconciledVersion, routingMode, name="inst1") -> dict:
    """Build a minimal Suite CR dict.

    Args:
        reconciledVersion (str): Value for status.versions.reconciled.
        routingMode (str | None): Value for spec.settings.routingMode, or None to omit the field.
        name (str, optional): Instance ID. Defaults to "inst1".

    Returns:
        dict: A Suite CR dict.
    """
    settings = {}
    if routingMode is not None:
        settings["routingMode"] = routingMode
    return {"metadata": {"name": name}, "spec": {"settings": settings}, "status": {"versions": {"reconciled": reconciledVersion}}}


class TestRoutingModeBlockForUpdate:
    """Tests for the routing mode pre-flight check in the update flow."""

    @patch("mas.cli.update.app.listMasInstances")
    def test_blocks_when_on_92_unsupported_catalog_to_supported_catalog_with_path(self, mockList):
        """Test that updating a 9.2 instance with routingMode=path off an unsupported catalog is blocked.

        GIVEN a 9.2.x instance with routingMode "path" and an installed catalog that does not support path routing
        WHEN checkRoutingModeForUpdate is called with a target catalog that supports path routing
        THEN fatalError is called and the update is blocked.
        """
        mockList.return_value = [_make_instance("9.2.1", "path")]
        app = _make_app(UNSUPPORTED_CATALOG, SUPPORTED_CATALOG)

        with pytest.raises(SystemExit) as excInfo:
            app.checkRoutingModeForUpdate()

        assert excInfo.value.code == 1

    @patch("mas.cli.update.app.listMasInstances")
    def test_error_message_contains_instance_id_and_oc_patch_command(self, mockList):
        """Test that the fatal error message includes the instanceId and oc patch remediation command.

        GIVEN a blocked instance named "myinst"
        WHEN checkRoutingModeForUpdate is called
        THEN the error message contains "myinst", "routingMode" and the oc patch command.
        """
        mockList.return_value = [_make_instance("9.2.1", "path", name="myinst")]
        app = _make_app(UNSUPPORTED_CATALOG, SUPPORTED_CATALOG)

        captured = []
        originalFatal = app.fatalError

        def capturingFatal(msg, exception=None):
            captured.append(msg)
            originalFatal(msg, exception)

        app.fatalError = capturingFatal

        with pytest.raises(SystemExit):
            app.checkRoutingModeForUpdate()

        assert len(captured) == 1
        assert "myinst" in captured[0]
        assert "routingMode" in captured[0]
        assert "oc patch" in captured[0]

    @patch("mas.cli.update.app.listMasInstances")
    def test_does_not_block_when_routing_mode_is_subdomain(self, mockList):
        """Test that routingMode=subdomain does not block.

        GIVEN a 9.2.x instance with routingMode "subdomain"
        WHEN checkRoutingModeForUpdate is called moving off an unsupported catalog
        THEN no error is raised.
        """
        mockList.return_value = [_make_instance("9.2.1", "subdomain")]
        app = _make_app(UNSUPPORTED_CATALOG, SUPPORTED_CATALOG)

        app.checkRoutingModeForUpdate()

    @patch("mas.cli.update.app.listMasInstances")
    def test_does_not_block_when_routing_mode_is_absent(self, mockList):
        """Test that a missing routingMode does not block.

        GIVEN a 9.2.x instance with no routingMode field
        WHEN checkRoutingModeForUpdate is called moving off an unsupported catalog
        THEN no error is raised.
        """
        mockList.return_value = [_make_instance("9.2.1", None)]
        app = _make_app(UNSUPPORTED_CATALOG, SUPPORTED_CATALOG)

        app.checkRoutingModeForUpdate()

    @patch("mas.cli.update.app.listMasInstances")
    def test_does_not_block_when_installed_catalog_supports_path_routing(self, mockList):
        """Test that an installed catalog that supports path routing does not block.

        GIVEN a 9.2.x instance with routingMode "path" and an installed catalog that supports path routing
        WHEN checkRoutingModeForUpdate is called
        THEN no error is raised.
        """
        mockList.return_value = [_make_instance("9.2.1", "path")]
        app = _make_app("v9-260924-amd64", "v9-261007-amd64")

        app.checkRoutingModeForUpdate()

    @patch("mas.cli.update.app.listMasInstances")
    def test_does_not_block_when_target_catalog_also_unsupported(self, mockList):
        """Test that updating between two unsupported catalogs does not block.

        GIVEN a 9.2.x instance with routingMode "path" on an unsupported catalog
        WHEN checkRoutingModeForUpdate is called with a target catalog that is also unsupported
        THEN no error is raised.
        """
        mockList.return_value = [_make_instance("9.2.1", "path")]
        app = _make_app("v9-260827-amd64", "v9-260902-amd64")

        app.checkRoutingModeForUpdate()

    @patch("mas.cli.update.app.listMasInstances")
    def test_does_not_block_when_instance_is_pre_92(self, mockList):
        """Test that a pre-9.2 instance is not checked by the update pre-flight.

        GIVEN a 9.1.x instance with routingMode "path"
        WHEN checkRoutingModeForUpdate is called moving off an unsupported catalog
        THEN no error is raised.
        """
        mockList.return_value = [_make_instance("9.1.5", "path")]
        app = _make_app(UNSUPPORTED_CATALOG, SUPPORTED_CATALOG)

        app.checkRoutingModeForUpdate()

    @patch("mas.cli.update.app.listMasInstances")
    def test_does_not_block_when_installed_catalog_unknown(self, mockList):
        """Test that an unknown installed catalog does not block.

        GIVEN installedCatalogId is None
        WHEN checkRoutingModeForUpdate is called
        THEN no error is raised and instances are not listed.
        """
        app = _make_app(None, SUPPORTED_CATALOG)

        app.checkRoutingModeForUpdate()

        mockList.assert_not_called()

    @patch("mas.cli.update.app.listMasInstances")
    def test_blocks_when_any_of_multiple_instances_matches(self, mockList):
        """Test that one offending instance among several blocks the update.

        GIVEN two instances, only the second having routingMode "path" on 9.2.x
        WHEN checkRoutingModeForUpdate is called moving off an unsupported catalog
        THEN fatalError is called.
        """
        mockList.return_value = [_make_instance("9.2.1", "subdomain", name="a"), _make_instance("9.2.1", "path", name="b")]
        app = _make_app(UNSUPPORTED_CATALOG, SUPPORTED_CATALOG)

        with pytest.raises(SystemExit):
            app.checkRoutingModeForUpdate()
