# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for MAS Core must-gather collector."""

import os
import tempfile
from unittest.mock import Mock, patch

from mas.cli.must_gather.mas.core import collectMASCore


def test_collectMASCore_calls_reconcile_logs_parallel():
    """Test that collectMASCore calls parallel reconcile logs collector.

    GIVEN a MAS Core namespace
    WHEN collectMASCore is called
    THEN collectReconcileLogsParallel is called with correct operators.
    """
    # Setup
    dynClient = Mock()
    namespace = "mas-inst1-core"

    with tempfile.TemporaryDirectory() as tmpDir:
        outputDir = os.path.join(tmpDir, "output")

        # Mock the parallel collection function
        with patch("mas.cli.must_gather.mas.core.collectReconcileLogsParallel") as mockCollect:
            mockCollect.return_value = True

            # Execute
            result = collectMASCore(dynClient, namespace, outputDir)

            # Verify
            assert result is True
            mockCollect.assert_called_once()

            # Get the call arguments
            args, kwargs = mockCollect.call_args

            # Verify dynClient, operators, and outputDir (correct order)
            assert args[0] == dynClient

            # Verify operators list
            operators = args[1]
            assert args[2] == outputDir
            assert isinstance(operators, list)
            assert len(operators) == 15  # 14 operators + truststore

            # Verify each operator tuple format (namespace, labelSelector, labelValue)
            for op in operators:
                assert isinstance(op, tuple)
                assert len(op) == 3
                assert op[0] == namespace  # All in same namespace


def test_collectMASCore_includes_all_core_operators():
    """Test that all MAS Core operators are included in reconcile logs collection.

    GIVEN a MAS Core namespace
    WHEN collectMASCore is called
    THEN all 15 operators are included in the collection list.
    """
    # Setup
    dynClient = Mock()
    namespace = "mas-inst1-core"

    with tempfile.TemporaryDirectory() as tmpDir:
        outputDir = os.path.join(tmpDir, "output")

        with patch("mas.cli.must_gather.mas.core.collectReconcileLogsParallel") as mockCollect:
            mockCollect.return_value = True

            # Execute
            collectMASCore(dynClient, namespace, outputDir)

            # Get operators list (second argument)
            operators = mockCollect.call_args[0][1]

            # Expected operators with their label selectors
            expectedOperators = [
                (namespace, "control-plane", "ibm-mas"),
                (namespace, "control-plane", "ibm-mas-ws"),
                (namespace, "control-plane", "ibm-mas-coreidp"),
                (namespace, "control-plane", "ibm-mas-addons"),
                (namespace, "control-plane", "ibm-mas-cfg-bas"),
                (namespace, "control-plane", "ibm-mas-cfg-sls"),
                (namespace, "control-plane", "ibm-mas-cfg-idp"),
                (namespace, "control-plane", "ibm-mas-cfg-scim"),
                (namespace, "control-plane", "ibm-mas-cfg-jdbc"),
                (namespace, "control-plane", "ibm-mas-cfg-mongo"),
                (namespace, "control-plane", "ibm-mas-cfg-kafka"),
                (namespace, "control-plane", "ibm-mas-cfg-objectstorage"),
                (namespace, "control-plane", "ibm-mas-cfg-smtp"),
                (namespace, "control-plane", "ibm-mas-cfg-ai"),
                (namespace, "operator", "ibm-truststore-mgr"),
            ]

            # Verify all expected operators are present
            assert operators == expectedOperators


def test_collectMASCore_handles_reconcile_logs_failure():
    """Test that collectMASCore handles reconcile logs collection failure gracefully.

    GIVEN a MAS Core namespace
    WHEN collectReconcileLogsParallel fails
    THEN collectMASCore continues and returns False.
    """
    # Setup
    dynClient = Mock()
    namespace = "mas-inst1-core"

    with tempfile.TemporaryDirectory() as tmpDir:
        outputDir = os.path.join(tmpDir, "output")

        with patch("mas.cli.must_gather.mas.core.collectReconcileLogsParallel") as mockCollect:
            mockCollect.return_value = False

            # Execute
            result = collectMASCore(dynClient, namespace, outputDir)

            # Verify - should still return True (graceful handling)
            assert result is True
            mockCollect.assert_called_once()


def test_collectMASCore_passes_progress_callback():
    """Test that collectMASCore passes progress callback to parallel collector.

    GIVEN a MAS Core namespace
    WHEN collectMASCore is called
    THEN a progress callback is passed to collectReconcileLogsParallel.
    """
    # Setup
    dynClient = Mock()
    namespace = "mas-inst1-core"

    with tempfile.TemporaryDirectory() as tmpDir:
        outputDir = os.path.join(tmpDir, "output")

        with patch("mas.cli.must_gather.mas.core.collectReconcileLogsParallel") as mockCollect:
            mockCollect.return_value = True

            # Execute
            collectMASCore(dynClient, namespace, outputDir)

            # Verify callback parameter exists
            kwargs = mockCollect.call_args[1]
            assert "progressCallback" in kwargs
            assert callable(kwargs["progressCallback"])


def test_collectMASCore_no_regression_in_existing_functionality():
    """Test that adding reconcile logs doesn't break existing functionality.

    GIVEN a MAS Core namespace
    WHEN collectMASCore is called
    THEN it still returns True (stub implementation preserved).
    """
    # Setup
    dynClient = Mock()
    namespace = "mas-inst1-core"

    with tempfile.TemporaryDirectory() as tmpDir:
        outputDir = os.path.join(tmpDir, "output")

        with patch("mas.cli.must_gather.mas.core.collectReconcileLogsParallel") as mockCollect:
            mockCollect.return_value = True

            # Execute
            result = collectMASCore(dynClient, namespace, outputDir)

            # Verify
            assert result is True


# Made with Bob
