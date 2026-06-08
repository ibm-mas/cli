# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for reconcile logs collection utilities."""

import io
import os
import tarfile
import tempfile
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

from mas.cli.must_gather.common.reconcile_logs import (
    collectReconcileLogs,
    _stripAnsiCodes,
    _getTimestampFromFile,
)


class TestStripAnsiCodes:
    """Test ANSI code stripping functionality."""

    def test_strip_ansi_codes_with_color_codes(self):
        """Test stripping ANSI color codes from text.

        GIVEN text with ANSI color codes
        WHEN _stripAnsiCodes is called
        THEN ANSI codes are removed and clean text is returned.
        """
        text = "\x1b[31mError\x1b[0m: Something went wrong"
        result = _stripAnsiCodes(text)
        assert result == "Error: Something went wrong"

    def test_strip_ansi_codes_with_multiple_codes(self):
        """Test stripping multiple ANSI codes from text.

        GIVEN text with multiple ANSI codes
        WHEN _stripAnsiCodes is called
        THEN all ANSI codes are removed.
        """
        text = "\x1b[1;32mSuccess\x1b[0m \x1b[33mWarning\x1b[0m"
        result = _stripAnsiCodes(text)
        assert result == "Success Warning"

    def test_strip_ansi_codes_no_codes(self):
        """Test stripping when no ANSI codes present.

        GIVEN text without ANSI codes
        WHEN _stripAnsiCodes is called
        THEN text is returned unchanged.
        """
        text = "Plain text without codes"
        result = _stripAnsiCodes(text)
        assert result == "Plain text without codes"

    def test_strip_ansi_codes_empty_string(self):
        """Test stripping with empty string.

        GIVEN empty string
        WHEN _stripAnsiCodes is called
        THEN empty string is returned.
        """
        result = _stripAnsiCodes("")
        assert result == ""


class TestGetTimestampFromFile:
    """Test timestamp conversion functionality."""

    def test_get_timestamp_from_file(self):
        """Test converting file mtime to timestamp string.

        GIVEN file path with modification time
        WHEN _getTimestampFromFile is called
        THEN timestamp string in format YYYYMMDD-HHMMSS is returned.
        """
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(b"test content")

        try:
            # Set specific mtime (2026-06-06 12:30:45)
            test_time = datetime(2026, 6, 6, 12, 30, 45).timestamp()
            os.utime(tmp_path, (test_time, test_time))

            result = _getTimestampFromFile(tmp_path)
            assert result == "20260606-123045"
        finally:
            os.unlink(tmp_path)

    def test_get_timestamp_from_nonexistent_file(self):
        """Test timestamp conversion with nonexistent file.

        GIVEN nonexistent file path
        WHEN _getTimestampFromFile is called
        THEN None is returned.
        """
        result = _getTimestampFromFile("/nonexistent/file.log")
        assert result is None


class TestCollectReconcileLogs:
    """Test reconcile logs collection functionality."""

    def test_collect_reconcile_logs_pod_not_found(self, caplog):
        """Test reconcile log collection when pod not found.

        GIVEN namespace and label selector with no matching pods
        WHEN collectReconcileLogs is called
        THEN warning is logged and True is returned (graceful handling).
        """
        mockDynClient = MagicMock()
        mockApi = MagicMock()
        mockDynClient.resources.get.return_value = mockApi
        mockApi.get.return_value.items = []

        with tempfile.TemporaryDirectory() as tmpDir:
            result = collectReconcileLogs(
                dynClient=mockDynClient,
                namespace="test-namespace",
                labelSelector="control-plane",
                labelValue="test-operator",
                outputDir=tmpDir,
            )

        assert result is True
        assert "No pods found with label" in caplog.text

    def test_collect_reconcile_logs_no_logs_available(self, caplog):
        """Test reconcile log collection when no logs available in pod.

        GIVEN pod exists but has no reconcile logs
        WHEN collectReconcileLogs is called
        THEN info message is logged and True is returned.
        """
        import logging

        caplog.set_level(logging.INFO)

        mockDynClient = MagicMock()
        mockApi = MagicMock()
        mockPod = Mock()
        mockPod.metadata.name = "test-pod"
        mockDynClient.resources.get.return_value = mockApi
        mockApi.get.return_value.items = [mockPod]

        mockCoreV1Api = MagicMock()

        with tempfile.TemporaryDirectory() as tmpDir:
            with patch("mas.cli.must_gather.common.reconcile_logs.client.CoreV1Api", return_value=mockCoreV1Api):
                with patch("mas.cli.must_gather.common.reconcile_logs.stream") as mockStream:
                    # Mock find command returning empty (no logs)
                    mockStream.return_value = ""

                    result = collectReconcileLogs(
                        dynClient=mockDynClient,
                        namespace="test-namespace",
                        labelSelector="control-plane",
                        labelValue="test-operator",
                        outputDir=tmpDir,
                    )

        assert result is True
        assert "No reconcile logs available" in caplog.text

    def test_collect_reconcile_logs_tar_creation_fails(self, caplog):
        """Test reconcile log collection when tar creation fails.

        GIVEN pod with logs but tar command fails
        WHEN collectReconcileLogs is called
        THEN warning is logged and True is returned (graceful handling).
        """
        mockDynClient = MagicMock()
        mockApi = MagicMock()
        mockPod = Mock()
        mockPod.metadata.name = "test-pod"
        mockDynClient.resources.get.return_value = mockApi
        mockApi.get.return_value.items = [mockPod]

        mockCoreV1Api = MagicMock()

        with tempfile.TemporaryDirectory() as tmpDir:
            with patch("mas.cli.must_gather.common.reconcile_logs.client.CoreV1Api", return_value=mockCoreV1Api):
                with patch("mas.cli.must_gather.common.reconcile_logs.stream") as mockStream:
                    # Mock find command returning log paths, then tar command fails
                    mockStream.side_effect = [
                        "/tmp/ansible-operator/runner/mas.ibm.com/v1/Suite/test-ns/test-instance/artifacts/123/stdout\n",
                        Exception("Tar command failed"),
                    ]

                    result = collectReconcileLogs(
                        dynClient=mockDynClient,
                        namespace="test-namespace",
                        labelSelector="control-plane",
                        labelValue="test-operator",
                        outputDir=tmpDir,
                    )

        assert result is True
        assert "Failed to execute tar command" in caplog.text or "Error downloading and extracting" in caplog.text

    def test_collect_reconcile_logs_successful_collection(self):
        """Test successful reconcile log collection.

        GIVEN pod with reconcile logs
        WHEN collectReconcileLogs is called
        THEN logs are extracted, organized, and written to output directory.
        """
        mockDynClient = MagicMock()
        mockApi = MagicMock()
        mockPod = Mock()
        mockPod.metadata.name = "test-pod"
        mockDynClient.resources.get.return_value = mockApi
        mockApi.get.return_value.items = [mockPod]

        mockCoreV1Api = MagicMock()

        # Create a mock tar archive with reconcile logs
        tarBuffer = io.BytesIO()
        with tarfile.open(fileobj=tarBuffer, mode="w:gz") as tar:
            # Create log file content with ANSI codes
            logContent = b"\x1b[32mINFO\x1b[0m: Reconciliation started\nProcessing resources\n"

            # Add file to tar: /tmp/ansible-operator/runner/mas.ibm.com/v1/Suite/test-ns/test-instance/artifacts/123/stdout
            logInfo = tarfile.TarInfo(name="tmp/ansible-operator/runner/mas.ibm.com/v1/Suite/test-ns/test-instance/artifacts/123/stdout")
            logInfo.size = len(logContent)
            logInfo.mtime = datetime(2026, 6, 6, 12, 30, 45).timestamp()
            tar.addfile(logInfo, io.BytesIO(logContent))

        tarBuffer.seek(0)
        tarData = tarBuffer.read()

        with tempfile.TemporaryDirectory() as tmpDir:
            with patch("mas.cli.must_gather.common.reconcile_logs.client.CoreV1Api", return_value=mockCoreV1Api):
                with patch("mas.cli.must_gather.common.reconcile_logs.stream") as mockStream:
                    # Create mock stream object for tar command
                    mockTarStream = Mock()
                    mockTarStream.is_open.side_effect = [True, False]  # Open then closed
                    mockTarStream.peek_stdout.return_value = True
                    mockTarStream.read_stdout.return_value = tarData
                    mockTarStream.peek_stderr.return_value = False
                    mockTarStream.close = Mock()

                    # Mock find command returning log paths, then tar stream
                    mockStream.side_effect = [
                        "/tmp/ansible-operator/runner/mas.ibm.com/v1/Suite/test-ns/test-instance/artifacts/123/stdout\n",
                        mockTarStream,
                    ]

                    result = collectReconcileLogs(
                        dynClient=mockDynClient,
                        namespace="test-namespace",
                        labelSelector="control-plane",
                        labelValue="test-operator",
                        outputDir=tmpDir,
                    )

            assert result is True

            # Verify output directory structure
            expectedLogDir = os.path.join(tmpDir, "reconcile-logs", "test-namespace", "suite", "test-instance")
            assert os.path.exists(expectedLogDir)

            # Verify log file created with timestamp
            logFiles = os.listdir(expectedLogDir)
            assert len(logFiles) == 1
            assert logFiles[0] == "20260606-123045.log"

            # Verify log content (ANSI codes stripped)
            logPath = os.path.join(expectedLogDir, logFiles[0])
            with open(logPath, "r") as f:
                content = f.read()
            assert "INFO: Reconciliation started" in content
            assert "\x1b[32m" not in content  # ANSI codes removed

    def test_collect_reconcile_logs_multiple_instances(self):
        """Test reconcile log collection with multiple instances.

        GIVEN pod with logs for multiple CR instances
        WHEN collectReconcileLogs is called
        THEN logs are organized by instance in separate directories.
        """
        mockDynClient = MagicMock()
        mockApi = MagicMock()
        mockPod = Mock()
        mockPod.metadata.name = "test-pod"
        mockDynClient.resources.get.return_value = mockApi
        mockApi.get.return_value.items = [mockPod]

        mockCoreV1Api = MagicMock()

        # Create tar archive with logs for two instances
        tarBuffer = io.BytesIO()
        with tarfile.open(fileobj=tarBuffer, mode="w:gz") as tar:
            # Instance 1
            log1Content = b"Instance 1 reconciliation\n"
            log1Info = tarfile.TarInfo(name="tmp/ansible-operator/runner/mas.ibm.com/v1/Workspace/test-ns/instance1/artifacts/123/stdout")
            log1Info.size = len(log1Content)
            log1Info.mtime = datetime(2026, 6, 6, 12, 0, 0).timestamp()
            tar.addfile(log1Info, io.BytesIO(log1Content))

            # Instance 2
            log2Content = b"Instance 2 reconciliation\n"
            log2Info = tarfile.TarInfo(name="tmp/ansible-operator/runner/mas.ibm.com/v1/Workspace/test-ns/instance2/artifacts/456/stdout")
            log2Info.size = len(log2Content)
            log2Info.mtime = datetime(2026, 6, 6, 13, 0, 0).timestamp()
            tar.addfile(log2Info, io.BytesIO(log2Content))

        tarBuffer.seek(0)
        tarData = tarBuffer.read()

        with tempfile.TemporaryDirectory() as tmpDir:
            with patch("mas.cli.must_gather.common.reconcile_logs.client.CoreV1Api", return_value=mockCoreV1Api):
                with patch("mas.cli.must_gather.common.reconcile_logs.stream") as mockStream:
                    # Create mock stream object for tar command
                    mockTarStream = Mock()
                    mockTarStream.is_open.side_effect = [True, False]
                    mockTarStream.peek_stdout.return_value = True
                    mockTarStream.read_stdout.return_value = tarData
                    mockTarStream.peek_stderr.return_value = False
                    mockTarStream.close = Mock()

                    mockStream.side_effect = [
                        "/tmp/ansible-operator/runner/mas.ibm.com/v1/Workspace/test-ns/instance1/artifacts/123/stdout\n"
                        "/tmp/ansible-operator/runner/mas.ibm.com/v1/Workspace/test-ns/instance2/artifacts/456/stdout\n",
                        mockTarStream,
                    ]

                    result = collectReconcileLogs(
                        dynClient=mockDynClient,
                        namespace="test-namespace",
                        labelSelector="control-plane",
                        labelValue="test-operator",
                        outputDir=tmpDir,
                    )

            assert result is True

            # Verify both instances have separate directories
            instance1Dir = os.path.join(tmpDir, "reconcile-logs", "test-namespace", "workspace", "instance1")
            instance2Dir = os.path.join(tmpDir, "reconcile-logs", "test-namespace", "workspace", "instance2")
            assert os.path.exists(instance1Dir)
            assert os.path.exists(instance2Dir)

            # Verify log files
            assert len(os.listdir(instance1Dir)) == 1
            assert len(os.listdir(instance2Dir)) == 1

    def test_collect_reconcile_logs_lowercase_kind_names(self):
        """Test that kind names are converted to lowercase in output paths.

        GIVEN pod with logs for CRs with mixed-case kind names
        WHEN collectReconcileLogs is called
        THEN output directories use lowercase kind names.
        """
        mockDynClient = MagicMock()
        mockApi = MagicMock()
        mockPod = Mock()
        mockPod.metadata.name = "test-pod"
        mockDynClient.resources.get.return_value = mockApi
        mockApi.get.return_value.items = [mockPod]

        mockCoreV1Api = MagicMock()

        tarBuffer = io.BytesIO()
        with tarfile.open(fileobj=tarBuffer, mode="w:gz") as tar:
            logContent = b"Test log\n"
            # Use mixed-case kind name "BASCfg"
            logInfo = tarfile.TarInfo(name="tmp/ansible-operator/runner/config.mas.ibm.com/v1/BASCfg/test-ns/test-bas/artifacts/123/stdout")
            logInfo.size = len(logContent)
            logInfo.mtime = datetime(2026, 6, 6, 12, 0, 0).timestamp()
            tar.addfile(logInfo, io.BytesIO(logContent))

        tarBuffer.seek(0)
        tarData = tarBuffer.read()

        with tempfile.TemporaryDirectory() as tmpDir:
            with patch("mas.cli.must_gather.common.reconcile_logs.client.CoreV1Api", return_value=mockCoreV1Api):
                with patch("mas.cli.must_gather.common.reconcile_logs.stream") as mockStream:
                    # Create mock stream object for tar command
                    mockTarStream = Mock()
                    mockTarStream.is_open.side_effect = [True, False]
                    mockTarStream.peek_stdout.return_value = True
                    mockTarStream.read_stdout.return_value = tarData
                    mockTarStream.peek_stderr.return_value = False
                    mockTarStream.close = Mock()

                    mockStream.side_effect = [
                        "/tmp/ansible-operator/runner/config.mas.ibm.com/v1/BASCfg/test-ns/test-bas/artifacts/123/stdout\n",
                        mockTarStream,
                    ]

                    result = collectReconcileLogs(
                        dynClient=mockDynClient,
                        namespace="test-namespace",
                        labelSelector="control-plane",
                        labelValue="test-operator",
                        outputDir=tmpDir,
                    )

            assert result is True

            # Verify lowercase kind name in path
            expectedDir = os.path.join(tmpDir, "reconcile-logs", "test-namespace", "bascfg", "test-bas")
            assert os.path.exists(expectedDir)


class TestCollectReconcileLogsParallel:
    """Test parallel reconcile logs collection functionality."""

    def test_collect_reconcile_logs_parallel_successful(self):
        """Test successful parallel collection of multiple operators.

        GIVEN multiple operators with reconcile logs
        WHEN collectReconcileLogsParallel is called
        THEN all operators are collected in parallel and True is returned.
        """
        from mas.cli.must_gather.common.reconcile_logs import collectReconcileLogsParallel

        mockDynClient = MagicMock()
        mockApi = MagicMock()

        # Create mock pods for each operator
        mockPod1 = Mock()
        mockPod1.metadata.name = "operator-1"
        mockPod2 = Mock()
        mockPod2.metadata.name = "operator-2"
        mockPod3 = Mock()
        mockPod3.metadata.name = "operator-3"

        # Mock pod discovery to return different pods for different labels
        def mockGetPods(namespace, label_selector):
            mockResult = Mock()
            if "operator-1" in label_selector:
                mockResult.items = [mockPod1]
            elif "operator-2" in label_selector:
                mockResult.items = [mockPod2]
            elif "operator-3" in label_selector:
                mockResult.items = [mockPod3]
            else:
                mockResult.items = []
            return mockResult

        mockDynClient.resources.get.return_value = mockApi
        mockApi.get.side_effect = mockGetPods

        mockCoreV1Api = MagicMock()

        # Create mock tar archives for each operator
        # Format: (namespace, labelSelector, labelValue)
        operators = [
            ("test-ns-1", "control-plane", "operator-1"),
            ("test-ns-2", "control-plane", "operator-2"),
            ("test-ns-3", "control-plane", "operator-3"),
        ]

        with tempfile.TemporaryDirectory() as tmpDir:
            with patch("mas.cli.must_gather.common.reconcile_logs.client.CoreV1Api", return_value=mockCoreV1Api):
                with patch("mas.cli.must_gather.common.reconcile_logs.stream") as mockStream:
                    # Create tar archive
                    tarBuffer = io.BytesIO()
                    with tarfile.open(fileobj=tarBuffer, mode="w:gz") as tar:
                        logContent = b"Test reconciliation\n"
                        logInfo = tarfile.TarInfo(name="tmp/ansible-operator/runner/mas.ibm.com/v1/Suite/test-ns/instance/artifacts/123/stdout")
                        logInfo.size = len(logContent)
                        logInfo.mtime = datetime(2026, 6, 6, 12, 0, 0).timestamp()
                        tar.addfile(logInfo, io.BytesIO(logContent))
                    tarBuffer.seek(0)
                    tarData = tarBuffer.read()

                    # Create a function that returns appropriate response based on command
                    def streamSideEffect(*args, **kwargs):
                        command = kwargs.get("command", [])
                        if command[0] == "find":
                            # Return find results for any operator
                            return "/tmp/ansible-operator/runner/mas.ibm.com/v1/Suite/test-ns/instance/artifacts/123/stdout\n"
                        elif command[0] == "tar":
                            # Return mock stream object
                            mockTarStream = Mock()
                            mockTarStream.is_open.side_effect = [True, False]
                            mockTarStream.peek_stdout.return_value = True
                            mockTarStream.read_stdout.return_value = tarData
                            mockTarStream.peek_stderr.return_value = False
                            mockTarStream.close = Mock()
                            return mockTarStream
                        return ""

                    mockStream.side_effect = streamSideEffect

                    result = collectReconcileLogsParallel(
                        dynClient=mockDynClient,
                        operators=operators,
                        outputDir=tmpDir,
                    )

            assert result is True

            # Verify reconcile-logs directory was created and has content
            reconcileLogsDir = os.path.join(tmpDir, "reconcile-logs")
            assert os.path.exists(reconcileLogsDir), "reconcile-logs directory not created"

            # Verify at least some logs were collected (all 3 operators should have logs)
            collectedNamespaces = os.listdir(reconcileLogsDir) if os.path.exists(reconcileLogsDir) else []
            assert len(collectedNamespaces) == 3, f"Expected 3 namespaces, got {len(collectedNamespaces)}"

    def test_collect_reconcile_logs_parallel_with_failures(self):
        """Test parallel collection when some operators fail.

        GIVEN multiple operators where some fail to collect
        WHEN collectReconcileLogsParallel is called
        THEN successful collections complete and True is returned (graceful handling).
        """
        from mas.cli.must_gather.common.reconcile_logs import collectReconcileLogsParallel

        mockDynClient = MagicMock()
        mockApi = MagicMock()

        # Only first operator has a pod
        mockPod1 = Mock()
        mockPod1.metadata.name = "operator-1"

        def mockGetPods(namespace, label_selector):
            mockResult = Mock()
            if "operator-1" in label_selector:
                mockResult.items = [mockPod1]
            else:
                mockResult.items = []  # Other operators have no pods
            return mockResult

        mockDynClient.resources.get.return_value = mockApi
        mockApi.get.side_effect = mockGetPods

        mockCoreV1Api = MagicMock()

        operators = [
            ("test-ns-1", "control-plane", "operator-1"),
            ("test-ns-2", "control-plane", "operator-2"),  # Will fail - no pod
            ("test-ns-3", "control-plane", "operator-3"),  # Will fail - no pod
        ]

        with tempfile.TemporaryDirectory() as tmpDir:
            with patch("mas.cli.must_gather.common.reconcile_logs.client.CoreV1Api", return_value=mockCoreV1Api):
                with patch("mas.cli.must_gather.common.reconcile_logs.stream") as mockStream:
                    # Only provide responses for operator-1
                    tarBuffer = io.BytesIO()
                    with tarfile.open(fileobj=tarBuffer, mode="w:gz") as tar:
                        logContent = b"operator-1 reconciliation\n"
                        logInfo = tarfile.TarInfo(name="tmp/ansible-operator/runner/mas.ibm.com/v1/Suite/test-ns-1/instance/artifacts/123/stdout")
                        logInfo.size = len(logContent)
                        logInfo.mtime = datetime(2026, 6, 6, 12, 0, 0).timestamp()
                        tar.addfile(logInfo, io.BytesIO(logContent))
                    tarBuffer.seek(0)
                    tarData = tarBuffer.read()

                    # Create mock stream object for tar command
                    mockTarStream = Mock()
                    mockTarStream.is_open.side_effect = [True, False]
                    mockTarStream.peek_stdout.return_value = True
                    mockTarStream.read_stdout.return_value = tarData
                    mockTarStream.peek_stderr.return_value = False
                    mockTarStream.close = Mock()

                    mockStream.side_effect = [
                        "/tmp/ansible-operator/runner/mas.ibm.com/v1/Suite/test-ns-1/instance/artifacts/123/stdout\n",
                        mockTarStream,
                    ]

                    result = collectReconcileLogsParallel(
                        dynClient=mockDynClient,
                        operators=operators,
                        outputDir=tmpDir,
                    )

            assert result is True  # Graceful handling

            # Verify operator-1 collected
            expectedDir = os.path.join(tmpDir, "reconcile-logs", "test-ns-1", "suite", "instance")
            assert os.path.exists(expectedDir)

    def test_collect_reconcile_logs_parallel_with_progress_callback(self):
        """Test parallel collection with progress callback.

        GIVEN multiple operators and a progress callback
        WHEN collectReconcileLogsParallel is called
        THEN callback is invoked with progress updates.
        """
        from mas.cli.must_gather.common.reconcile_logs import collectReconcileLogsParallel

        mockDynClient = MagicMock()
        mockApi = MagicMock()
        mockDynClient.resources.get.return_value = mockApi
        mockApi.get.return_value.items = []  # No pods found

        operators = [
            ("test-ns-1", "control-plane", "operator-1"),
            ("test-ns-2", "control-plane", "operator-2"),
        ]

        progressCalls = []

        def progressCallback(completed, total):
            progressCalls.append((completed, total))

        with tempfile.TemporaryDirectory() as tmpDir:
            result = collectReconcileLogsParallel(
                dynClient=mockDynClient,
                operators=operators,
                outputDir=tmpDir,
                progressCallback=progressCallback,
            )

        assert result is True
        # Verify callback was called with progress
        assert len(progressCalls) > 0
        # Last call should be (2, 2) - all completed
        assert progressCalls[-1] == (2, 2)

    def test_collect_reconcile_logs_parallel_empty_list(self):
        """Test parallel collection with empty operator list.

        GIVEN empty operator list
        WHEN collectReconcileLogsParallel is called
        THEN True is returned immediately.
        """
        from mas.cli.must_gather.common.reconcile_logs import collectReconcileLogsParallel

        mockDynClient = MagicMock()

        with tempfile.TemporaryDirectory() as tmpDir:
            result = collectReconcileLogsParallel(
                dynClient=mockDynClient,
                operators=[],
                outputDir=tmpDir,
            )

        assert result is True

    def test_collect_reconcile_logs_parallel_max_workers(self):
        """Test parallel collection respects max_workers parameter.

        GIVEN multiple operators and custom max_workers
        WHEN collectReconcileLogsParallel is called
        THEN collection completes successfully with custom max_workers.
        """
        from mas.cli.must_gather.common.reconcile_logs import collectReconcileLogsParallel

        mockDynClient = MagicMock()
        mockApi = MagicMock()
        mockDynClient.resources.get.return_value = mockApi
        mockApi.get.return_value.items = []  # No pods found

        operators = [
            ("test-ns-1", "control-plane", "operator-1"),
            ("test-ns-2", "control-plane", "operator-2"),
        ]

        with tempfile.TemporaryDirectory() as tmpDir:
            # Just verify it completes successfully with custom max_workers
            result = collectReconcileLogsParallel(
                dynClient=mockDynClient,
                operators=operators,
                outputDir=tmpDir,
                max_workers=5,
            )

        assert result is True


# Made with Bob
