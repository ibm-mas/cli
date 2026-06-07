# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for AI Service instance must-gather collector."""

import os
import tempfile
from unittest.mock import Mock, patch

from mas.cli.must_gather.aiservice.instance import collectAIServiceInstance


def test_collectAIServiceInstance_calls_reconcile_logs():
    """Test that collectAIServiceInstance calls reconcile logs collector.

    GIVEN an AI Service instance ID
    WHEN collectAIServiceInstance is called
    THEN collectReconcileLogsParallel is called with 3 operators.
    """
    dynClient = Mock()
    instanceId = "inst1"

    with tempfile.TemporaryDirectory() as tmpDir:
        outputDir = os.path.join(tmpDir, "output")

        with patch("mas.cli.must_gather.aiservice.instance.collectReconcileLogsParallel") as mockCollect:
            mockCollect.return_value = True

            # Execute
            result = collectAIServiceInstance(dynClient, instanceId, outputDir)

            # Verify
            assert result is True
            mockCollect.assert_called_once()

            # Verify operators list
            operators = mockCollect.call_args[0][1]
            assert len(operators) == 3
            assert ("aiservice-inst1", "control-plane", "ibm-aiservice") in operators
            assert ("aiservice-inst1", "aiservice.ibm.com/appType", "entitymgr-tenant-operator") in operators
            assert ("aiservice-inst1", "operator", "ibm-truststore-mgr") in operators


def test_collectAIServiceInstance_handles_reconcile_logs_failure():
    """Test that collectAIServiceInstance handles reconcile logs failure gracefully.

    GIVEN an AI Service instance ID
    WHEN collectReconcileLogsParallel fails
    THEN collectAIServiceInstance continues and returns True.
    """
    dynClient = Mock()
    instanceId = "inst1"

    with tempfile.TemporaryDirectory() as tmpDir:
        outputDir = os.path.join(tmpDir, "output")

        with patch("mas.cli.must_gather.aiservice.instance.collectReconcileLogsParallel") as mockCollect:
            mockCollect.return_value = False

            # Execute
            result = collectAIServiceInstance(dynClient, instanceId, outputDir)

            # Verify - should still return True (graceful handling)
            assert result is True


def test_collectAIServiceInstance_with_genericMustGather():
    """Test that collectAIServiceInstance calls genericMustGather when provided.

    GIVEN an AI Service instance ID and genericMustGather function
    WHEN collectAIServiceInstance is called
    THEN both reconcile logs and genericMustGather are called.
    """
    dynClient = Mock()
    instanceId = "inst1"
    genericMustGather = Mock(return_value=True)

    with tempfile.TemporaryDirectory() as tmpDir:
        outputDir = os.path.join(tmpDir, "output")

        with patch("mas.cli.must_gather.aiservice.instance.collectReconcileLogsParallel") as mockCollect:
            mockCollect.return_value = True

            # Execute
            result = collectAIServiceInstance(dynClient, instanceId, outputDir, genericMustGather=genericMustGather)

            # Verify both were called
            assert result is True
            mockCollect.assert_called_once()
            genericMustGather.assert_called_once()


# Made with Bob
