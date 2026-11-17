# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for UpgradeApp.checkRoutingModeForUpgrade().

Verifies that the upgrade pre-flight check blocks an upgrade from a pre-9.2
instance to 9.2+ when spec.settings.routingMode is "path" (a stale accidental
value). Upgrades where the current channel is already 9.2+ must NOT be blocked
because routingMode=path was set intentionally on those instances.
"""

import pytest
from unittest.mock import MagicMock
from mas.cli.upgrade.app import UpgradeApp


def _make_app(nextChannel) -> UpgradeApp:
    """Create a minimal UpgradeApp instance for direct method testing.

    Args:
        nextChannel (str): The upgrade target channel to set on the app.

    Returns:
        UpgradeApp: App instance with a mocked dynamic client.
    """
    app = UpgradeApp()
    app._dynClient = MagicMock()
    app.noConfirm = True
    app.params = {}
    app.nextChannel = nextChannel
    return app


def _make_suite_cr(routingMode) -> dict:
    """Build a minimal Suite CR dict with the given routingMode value.

    Args:
        routingMode (str | None): Value for spec.settings.routingMode,
            or None to omit the field entirely.

    Returns:
        dict: A Suite CR dict.
    """
    settings = {}
    if routingMode is not None:
        settings["routingMode"] = routingMode
    return {"spec": {"settings": settings}}


def _mock_suite_api(app: UpgradeApp, suite_cr: dict) -> MagicMock:
    """Wire app's dynamic client to return the given Suite CR dict.

    Args:
        app (UpgradeApp): The app whose dynamic client to configure.
        suite_cr (dict): The Suite CR dict to return from the API.

    Returns:
        MagicMock: The mocked Suite API object.
    """
    mock_suite_api = MagicMock()
    mock_suite_api.get.return_value = suite_cr
    app._dynClient.resources.get.return_value = mock_suite_api
    return mock_suite_api


class TestRoutingModeBlockForUpgrade:
    """Tests for the routing mode pre-flight check in the upgrade flow.

    Verifies that checkRoutingModeForUpgrade blocks upgrades from pre-9.2 to
    9.2+ when spec.settings.routingMode is "path", and is a no-op in all
    other scenarios — including intentional 9.2 → 9.3 upgrades.
    """

    def test_blocks_pre_9_2_to_9_2_when_routing_mode_is_path(self):
        """Test that upgrading from pre-9.2 to 9.2.x with routingMode=path triggers a fatal error.

        GIVEN a Suite CR on 9.1.x with spec.settings.routingMode set to "path"
        WHEN checkRoutingModeForUpgrade is called with currentChannel "9.1.x" and nextChannel "9.2.x"
        THEN fatalError is called and the upgrade is blocked.
        """
        app = _make_app("9.2.x")
        _mock_suite_api(app, _make_suite_cr("path"))

        with pytest.raises(SystemExit) as exc_info:
            app.checkRoutingModeForUpgrade("inst1", "9.1.x")

        assert exc_info.value.code == 1

    def test_blocks_pre_9_2_to_9_3_when_routing_mode_is_path(self):
        """Test that upgrading from pre-9.2 directly to 9.3.x with routingMode=path blocks.

        GIVEN a Suite CR on 9.1.x with spec.settings.routingMode set to "path"
        WHEN checkRoutingModeForUpgrade is called with currentChannel "9.1.x" and nextChannel "9.3.x"
        THEN fatalError is called and the upgrade is blocked.
        """
        app = _make_app("9.3.x")
        _mock_suite_api(app, _make_suite_cr("path"))

        with pytest.raises(SystemExit) as exc_info:
            app.checkRoutingModeForUpgrade("inst1", "9.1.x")

        assert exc_info.value.code == 1

    def test_does_not_block_when_current_is_9_2_and_target_is_9_3(self):
        """Test that upgrading from 9.2.x to 9.3.x with routingMode=path does not block.

        GIVEN a Suite CR on 9.2.x with spec.settings.routingMode set to "path" (intentionally configured)
        WHEN checkRoutingModeForUpgrade is called with currentChannel "9.2.x" and nextChannel "9.3.x"
        THEN no error is raised (routingMode=path was set intentionally on 9.2+).
        """
        app = _make_app("9.3.x")
        _mock_suite_api(app, _make_suite_cr("path"))

        # Should not raise
        app.checkRoutingModeForUpgrade("inst1", "9.2.x")

    def test_error_message_contains_instance_id_and_oc_patch_command(self):
        """Test that the fatal error message includes the instanceId and oc patch remediation command.

        GIVEN a pre-9.2 Suite CR with spec.settings.routingMode set to "path"
        WHEN checkRoutingModeForUpgrade is called with instanceId "myinst"
        THEN the error message contains "myinst" and the oc patch command.
        """
        app = _make_app("9.2.x")
        _mock_suite_api(app, _make_suite_cr("path"))

        captured_messages = []
        original_fatal = app.fatalError

        def capturingFatal(msg, exception=None):
            captured_messages.append(msg)
            original_fatal(msg, exception)

        app.fatalError = capturingFatal

        with pytest.raises(SystemExit):
            app.checkRoutingModeForUpgrade("myinst", "9.1.x")

        assert len(captured_messages) == 1
        msg = captured_messages[0]
        assert "myinst" in msg
        assert "routingMode" in msg
        assert "oc patch" in msg

    def test_does_not_block_when_routing_mode_is_subdomain(self):
        """Test that upgrading from pre-9.2 to 9.2.x with routingMode=subdomain does not block.

        GIVEN a Suite CR with spec.settings.routingMode set to "subdomain"
        WHEN checkRoutingModeForUpgrade is called with currentChannel "9.1.x" and nextChannel "9.2.x"
        THEN no error is raised.
        """
        app = _make_app("9.2.x")
        _mock_suite_api(app, _make_suite_cr("subdomain"))

        # Should not raise
        app.checkRoutingModeForUpgrade("inst1", "9.1.x")

    def test_does_not_block_when_routing_mode_is_absent(self):
        """Test that upgrading from pre-9.2 to 9.2.x with no routingMode field does not block.

        GIVEN a Suite CR with no spec.settings.routingMode field
        WHEN checkRoutingModeForUpgrade is called with currentChannel "9.1.x" and nextChannel "9.2.x"
        THEN no error is raised.
        """
        app = _make_app("9.2.x")
        _mock_suite_api(app, _make_suite_cr(None))

        # Should not raise
        app.checkRoutingModeForUpgrade("inst1", "9.1.x")

    def test_does_not_block_when_spec_settings_is_absent(self):
        """Test that upgrading from pre-9.2 to 9.2.x when spec.settings is missing does not block.

        GIVEN a Suite CR with no spec.settings key
        WHEN checkRoutingModeForUpgrade is called with currentChannel "9.1.x" and nextChannel "9.2.x"
        THEN no error is raised.
        """
        app = _make_app("9.2.x")
        _mock_suite_api(app, {"spec": {}})

        # Should not raise
        app.checkRoutingModeForUpgrade("inst1", "9.1.x")

    def test_does_not_block_when_spec_is_absent(self):
        """Test that upgrading from pre-9.2 to 9.2.x when spec is missing entirely does not block.

        GIVEN a Suite CR with no spec key at all
        WHEN checkRoutingModeForUpgrade is called with currentChannel "9.1.x" and nextChannel "9.2.x"
        THEN no error is raised.
        """
        app = _make_app("9.2.x")
        _mock_suite_api(app, {})

        # Should not raise
        app.checkRoutingModeForUpgrade("inst1", "9.1.x")

    def test_does_not_block_when_target_is_9_1_x(self):
        """Test that upgrading to 9.1.x with routingMode=path does not block.

        GIVEN a Suite CR with spec.settings.routingMode set to "path"
        WHEN checkRoutingModeForUpgrade is called with nextChannel "9.1.x"
        THEN no error is raised (check only applies to targets of 9.2.0 or later).
        """
        app = _make_app("9.1.x")
        _mock_suite_api(app, _make_suite_cr("path"))

        # Should not raise
        app.checkRoutingModeForUpgrade("inst1", "9.0.x")

    def test_does_not_block_when_suite_cr_query_fails(self):
        """Test that a Suite CR query exception is handled gracefully without blocking.

        GIVEN the Suite CR API raises an exception
        WHEN checkRoutingModeForUpgrade is called with currentChannel "9.1.x" and nextChannel "9.2.x"
        THEN no error is raised (resilient path — let the pipeline handle it).
        """
        app = _make_app("9.2.x")
        app._dynClient.resources.get.side_effect = Exception("API unavailable")

        # Should not raise
        app.checkRoutingModeForUpgrade("inst1", "9.1.x")

    def test_does_not_block_when_next_channel_is_none(self):
        """Test that a None nextChannel does not cause an error.

        GIVEN nextChannel is None (channel not yet determined)
        WHEN checkRoutingModeForUpgrade is called
        THEN no error is raised and no Suite CR API call is made.
        """
        app = _make_app(None)
        mock_api = _mock_suite_api(app, _make_suite_cr("path"))

        # Should not raise
        app.checkRoutingModeForUpgrade("inst1", "9.1.x")

        # Should not even query the Suite CR
        mock_api.get.assert_not_called()
