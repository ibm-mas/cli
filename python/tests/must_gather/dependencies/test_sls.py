# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for SLS dependency must-gather collector."""

import os
import tempfile
from unittest.mock import Mock, patch

from mas.cli.must_gather.dependencies.sls import collectSLSNamespace


def test_collectSLSNamespace_calls_reconcile_logs():
    """Test that collectSLSNamespace calls reconcile logs collector.

    GIVEN an SLS namespace
    WHEN collectSLSNamespace is called
    THEN collectReconcileLogsParallel is called with 2 operators.
    """
    dynClient = Mock()
    namespace = "ibm-sls"

    with tempfile.TemporaryDirectory() as tmpDir:
        outputDir = os.path.join(tmpDir, "output")

        # Mock all the collection functions - they're imported from ..common
        with (
            patch("mas.cli.must_gather.dependencies.sls.collectReconcileLogsParallel") as mockReconcile,
            patch("mas.cli.must_gather.common.collectIBMCustomResources") as mockIBM,
            patch("mas.cli.must_gather.common.collectResources") as mockResources,
            patch("mas.cli.must_gather.common.collectPods") as mockPods,
            patch("mas.cli.must_gather.common.collectSecrets") as mockSecrets,
        ):

            mockReconcile.return_value = True
            mockIBM.return_value = True
            mockResources.return_value = True
            mockPods.return_value = True
            mockSecrets.return_value = True

            # Execute
            result = collectSLSNamespace(dynClient, namespace, outputDir)

            # Verify
            assert result is True
            mockReconcile.assert_called_once()

            # Verify operators list
            operators = mockReconcile.call_args[0][1]
            assert len(operators) == 2
            assert (namespace, "control-plane", "controller-manager") in operators
            assert (namespace, "operator", "ibm-truststore-mgr") in operators


def test_collectSLSNamespace_handles_reconcile_logs_failure():
    """Test that collectSLSNamespace handles reconcile logs failure gracefully.

    GIVEN an SLS namespace
    WHEN collectReconcileLogsParallel fails
    THEN collectSLSNamespace continues and returns True.
    """
    dynClient = Mock()
    namespace = "ibm-sls"

    with tempfile.TemporaryDirectory() as tmpDir:
        outputDir = os.path.join(tmpDir, "output")

        with (
            patch("mas.cli.must_gather.dependencies.sls.collectReconcileLogsParallel") as mockReconcile,
            patch("mas.cli.must_gather.common.collectIBMCustomResources") as mockIBM,
            patch("mas.cli.must_gather.common.collectResources") as mockResources,
            patch("mas.cli.must_gather.common.collectPods") as mockPods,
            patch("mas.cli.must_gather.common.collectSecrets") as mockSecrets,
        ):

            mockReconcile.return_value = False
            mockIBM.return_value = True
            mockResources.return_value = True
            mockPods.return_value = True
            mockSecrets.return_value = True

            # Execute
            result = collectSLSNamespace(dynClient, namespace, outputDir)

            # Verify - should still return True (graceful handling)
            assert result is True


# Made with Bob
