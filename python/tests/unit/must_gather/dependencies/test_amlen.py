# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for Amlen Message Gateway collector."""

from unittest.mock import MagicMock, Mock, patch

from mas.cli.must_gather.collection_plan import CollectionPlan


class TestCollectAmlenLogs:
    """Tests for collectAmlenLogs function."""

    def test_collectAmlenLogs_returns_true_when_no_pods_found(self):
        """Test graceful handling when no mbgx pods exist.

        GIVEN a namespace with no mbgx-messagesight pods
        WHEN collectAmlenLogs is called
        THEN True is returned without error.
        """
        from mas.cli.must_gather.dependencies.amlen import collectAmlenLogs

        mockApi = MagicMock()
        mockApi.get.return_value.items = []

        with patch("mas.cli.must_gather.dependencies.amlen.createThreadLocalDynamicClient") as mockDynClient:
            mockDynClient.return_value.resources.get.return_value = mockApi
            mockDynClient.return_value.client = MagicMock()

            result = collectAmlenLogs(
                namespace="mas-test-messaging",
                outputDir="/tmp/output",
            )

        assert result is True, "collectAmlenLogs should return True when no pods are found"

    def test_collectAmlenLogs_returns_true_when_no_log_files_found(self):
        """Test graceful handling when pod exists but has no log files.

        GIVEN a mbgx pod with no log files in /var/messagesight/diag/logs/
        WHEN collectAmlenLogs is called
        THEN True is returned without error.
        """
        from mas.cli.must_gather.dependencies.amlen import collectAmlenLogs

        mockPod = Mock()
        mockPod.metadata.name = "mbgx-messagesight-0"

        mockApi = MagicMock()
        mockApi.get.return_value.items = [mockPod]

        with (
            patch("mas.cli.must_gather.dependencies.amlen.createThreadLocalDynamicClient") as mockDynClient,
            patch("mas.cli.must_gather.dependencies.amlen._findAmlenLogFiles") as mockFind,
            patch("mas.cli.must_gather.dependencies.amlen.client") as mockClient,
        ):
            mockDynClient.return_value.resources.get.return_value = mockApi
            mockDynClient.return_value.client = MagicMock()
            mockClient.CoreV1Api.return_value = MagicMock()
            mockFind.return_value = []

            result = collectAmlenLogs(
                namespace="mas-test-messaging",
                outputDir="/tmp/output",
            )

        assert result is True, "collectAmlenLogs should return True when no log files are found"

    def test_collectAmlenLogs_discovers_pods_with_correct_label(self):
        """Test that pods are discovered using app=mbgx-messagesight label.

        GIVEN a namespace
        WHEN collectAmlenLogs is called
        THEN pods are queried with the app=mbgx-messagesight label selector.
        """
        from mas.cli.must_gather.dependencies.amlen import collectAmlenLogs

        mockApi = MagicMock()
        mockApi.get.return_value.items = []

        with patch("mas.cli.must_gather.dependencies.amlen.createThreadLocalDynamicClient") as mockDynClient:
            mockDynClient.return_value.resources.get.return_value = mockApi
            mockDynClient.return_value.client = MagicMock()

            collectAmlenLogs(
                namespace="mas-test-messaging",
                outputDir="/tmp/output",
            )

        mockApi.get.assert_called_once_with(
            namespace="mas-test-messaging",
            label_selector="app=mbgx-messagesight",
        )


class TestFindAmlenLogFiles:
    """Tests for _findAmlenLogFiles function."""

    def test_findAmlenLogFiles_returns_log_files(self):
        """Test that log files are found in the correct directory.

        GIVEN a pod with log files in /var/messagesight/diag/logs/
        WHEN _findAmlenLogFiles is called
        THEN the list of log file paths is returned.
        """
        from mas.cli.must_gather.dependencies.amlen import _findAmlenLogFiles

        mockStream = MagicMock()
        mockStream.return_value = "/var/messagesight/diag/logs/server.log\n/var/messagesight/diag/logs/trace.log\n"

        with patch("mas.cli.must_gather.dependencies.amlen.stream", mockStream):
            mockCoreV1 = MagicMock()
            result = _findAmlenLogFiles(mockCoreV1, "test-ns", "mbgx-pod-0")

        assert result == [
            "/var/messagesight/diag/logs/server.log",
            "/var/messagesight/diag/logs/trace.log",
        ], f"_findAmlenLogFiles should return list of log paths, got: {result}"

    def test_findAmlenLogFiles_returns_empty_on_exception(self):
        """Test that _findAmlenLogFiles returns empty list on exception.

        GIVEN a pod exec that raises an exception (e.g. pod not running)
        WHEN _findAmlenLogFiles is called
        THEN an empty list is returned without raising.
        """
        from mas.cli.must_gather.dependencies.amlen import _findAmlenLogFiles

        with patch("mas.cli.must_gather.dependencies.amlen.stream", side_effect=Exception("exec failed")):
            mockCoreV1 = MagicMock()
            result = _findAmlenLogFiles(mockCoreV1, "test-ns", "mbgx-pod-0")

        assert result == [], f"_findAmlenLogFiles should return empty list on exception, got: {result}"


class TestAddAmlenToCollectionPlan:
    """Tests for addAmlenToCollectionPlan function."""

    def test_addAmlenToCollectionPlan_adds_group_per_namespace(self):
        """Test that an amlen collection group is added to the plan.

        GIVEN a collection plan and a messaging namespace
        WHEN addAmlenToCollectionPlan is called
        THEN a collection group is added for the namespace.
        """
        from mas.cli.must_gather.dependencies.amlen import addAmlenToCollectionPlan

        plan = CollectionPlan()

        addAmlenToCollectionPlan(
            plan=plan,
            namespace="mas-test-messaging",
            outputDir="/tmp/output",
        )

        assert plan.total_groups == 1, f"Should have 1 group for the messaging namespace, got {plan.total_groups}"
        assert plan.total_tasks > 0, "Should have tasks generated for amlen collection"

    def test_addAmlenToCollectionPlan_task_name_includes_namespace(self):
        """Test that the amlen collection task name references the namespace.

        GIVEN a collection plan and a messaging namespace
        WHEN addAmlenToCollectionPlan is called
        THEN the group name includes the namespace for identification.
        """
        from mas.cli.must_gather.dependencies.amlen import addAmlenToCollectionPlan

        plan = CollectionPlan()

        addAmlenToCollectionPlan(
            plan=plan,
            namespace="mas-inst1-messaging",
            outputDir="/tmp/output",
        )

        groupNames = [g.name for g in plan.groups]
        assert any(
            "mas-inst1-messaging" in name for name in groupNames
        ), f"Group name should reference the namespace 'mas-inst1-messaging', got groups: {groupNames}"
