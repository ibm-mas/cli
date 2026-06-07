# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for MAS Apps must-gather collector."""

import os
import tempfile
from unittest.mock import Mock, patch

from mas.cli.must_gather.mas.apps import collectMASApp, getReconcileLogsOperatorsForApp


def test_getReconcileLogsOperatorsForApp_manage():
    """Test that Manage app returns correct operator list.

    GIVEN the Manage app ID
    WHEN getReconcileLogsOperatorsForApp is called
    THEN it returns 7 operators with correct label selectors.
    """
    namespace = "mas-inst1-manage"
    operators = getReconcileLogsOperatorsForApp(namespace, "manage")

    assert len(operators) == 7
    assert (namespace, "control-plane", "ibm-mas-manage") in operators
    assert (namespace, "mas.ibm.com/appType", "imagestitching-entitymgr-operator") in operators
    assert (namespace, "mas.ibm.com/appType", "entitymgr-ws-operator") in operators
    assert (namespace, "mas.ibm.com/appType", "healthext-entitymgr-ws-operator") in operators
    assert (namespace, "mas.ibm.com/appType", "maxinstudb") in operators
    assert (namespace, "operator", "ibm-truststore-mgr") in operators
    assert (namespace, "mas.ibm.com/appType", "serverBundle") in operators


def test_getReconcileLogsOperatorsForApp_iot():
    """Test that IoT app returns correct operator list.

    GIVEN the IoT app ID
    WHEN getReconcileLogsOperatorsForApp is called
    THEN it returns operators with correct label selectors.
    """
    namespace = "mas-inst1-iot"
    operators = getReconcileLogsOperatorsForApp(namespace, "iot")

    assert len(operators) >= 3  # At least main operator, workspace, and truststore
    assert (namespace, "control-plane", "ibm-iot-operator") in operators
    assert (namespace, "control-plane", "workspace-operator") in operators
    assert (namespace, "operator", "ibm-truststore-mgr") in operators


def test_getReconcileLogsOperatorsForApp_unknown_app():
    """Test that unknown app returns empty list.

    GIVEN an unknown app ID
    WHEN getReconcileLogsOperatorsForApp is called
    THEN it returns an empty list.
    """
    namespace = "mas-inst1-unknown"
    operators = getReconcileLogsOperatorsForApp(namespace, "unknown")

    assert operators == []


def test_collectMASApp_calls_reconcile_logs():
    """Test that collectMASApp calls reconcile logs collector.

    GIVEN a MAS app namespace
    WHEN collectMASApp is called
    THEN collectReconcileLogsParallel is called with app-specific operators.
    """
    dynClient = Mock()
    namespace = "mas-inst1-manage"
    appId = "manage"

    with tempfile.TemporaryDirectory() as tmpDir:
        outputDir = os.path.join(tmpDir, "output")

        with patch("mas.cli.must_gather.mas.apps.collectReconcileLogsParallel") as mockCollect:
            mockCollect.return_value = True

            # Execute
            result = collectMASApp(dynClient, namespace, appId, outputDir)

            # Verify
            assert result is True
            mockCollect.assert_called_once()

            # Verify operators list
            operators = mockCollect.call_args[0][1]
            assert len(operators) == 7  # Manage has 7 operators


def test_collectMASApp_handles_reconcile_logs_failure():
    """Test that collectMASApp handles reconcile logs failure gracefully.

    GIVEN a MAS app namespace
    WHEN collectReconcileLogsParallel fails
    THEN collectMASApp continues and returns True.
    """
    dynClient = Mock()
    namespace = "mas-inst1-manage"
    appId = "manage"

    with tempfile.TemporaryDirectory() as tmpDir:
        outputDir = os.path.join(tmpDir, "output")

        with patch("mas.cli.must_gather.mas.apps.collectReconcileLogsParallel") as mockCollect:
            mockCollect.return_value = False

            # Execute
            result = collectMASApp(dynClient, namespace, appId, outputDir)

            # Verify - should still return True (graceful handling)
            assert result is True


def test_collectMASApp_with_genericMustGather():
    """Test that collectMASApp calls genericMustGather when provided.

    GIVEN a MAS app namespace and genericMustGather function
    WHEN collectMASApp is called
    THEN both reconcile logs and genericMustGather are called.
    """
    dynClient = Mock()
    namespace = "mas-inst1-manage"
    appId = "manage"
    genericMustGather = Mock(return_value=True)

    with tempfile.TemporaryDirectory() as tmpDir:
        outputDir = os.path.join(tmpDir, "output")

        with patch("mas.cli.must_gather.mas.apps.collectReconcileLogsParallel") as mockCollect:
            mockCollect.return_value = True

            # Execute
            result = collectMASApp(dynClient, namespace, appId, outputDir, genericMustGather=genericMustGather)

            # Verify both were called
            assert result is True
            mockCollect.assert_called_once()
            genericMustGather.assert_called_once()


# Made with Bob
