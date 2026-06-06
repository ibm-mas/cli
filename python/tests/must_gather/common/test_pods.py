# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Test pod collection utilities."""

import os
import tempfile
import shutil
from typing import Optional
from unittest.mock import Mock
from kubernetes.dynamic import DynamicClient


class TestCollectPods:
    """Test pod collection functionality."""

    def setup_method(self):
        """Set up test fixtures.

        GIVEN a test environment
        WHEN tests are run
        THEN create temporary directory and mock Kubernetes client.
        """
        self.testDir = tempfile.mkdtemp()
        self.mockClient = Mock(spec=DynamicClient)

    def teardown_method(self):
        """Clean up test fixtures.

        GIVEN test completion
        WHEN teardown is called
        THEN remove temporary directory.
        """
        if os.path.exists(self.testDir):
            shutil.rmtree(self.testDir)

    def _createMockPod(self, name: str, namespace: str, app: Optional[str] = None, containers: Optional[list] = None):
        """Create a mock Kubernetes pod.

        Args:
            name (str): Pod name
            namespace (str): Pod namespace
            app (str, optional): App label. Defaults to None.
            containers (list, optional): List of container names. Defaults to None.

        Returns:
            Mock: Mock pod object
        """
        mockPod = Mock()
        mockPod.metadata = Mock()
        mockPod.metadata.name = name
        mockPod.metadata.namespace = namespace
        mockPod.metadata.labels = {"app": app} if app else {}

        podDict = {"metadata": {"name": name, "namespace": namespace, "labels": mockPod.metadata.labels}, "status": {"phase": "Running"}}

        if containers:
            podDict["status"]["containerStatuses"] = [{"name": c, "ready": True, "restartCount": 0} for c in containers]

        mockPod.to_dict.return_value = podDict
        return mockPod

    def _createMockPodList(self, pods: list):
        """Create a mock pod list.

        Args:
            pods (list): List of mock pods

        Returns:
            Mock: Mock pod list object
        """
        mockList = Mock()
        mockList.items = pods
        mockList.to_dict.return_value = {"items": [p.to_dict() for p in pods]}
        return mockList

    def test_collect_pods_creates_namespace_directory(self):
        """Test that namespace directory is created.

        GIVEN a namespace
        WHEN collectPods is called
        THEN namespace directory is created.
        """
        from mas.cli.must_gather.common.pods import collectPods

        mockApi = Mock()
        mockApi.get.return_value = self._createMockPodList([])
        self.mockClient.resources.get.return_value = mockApi

        collectPods(dynClient=self.mockClient, namespace="test-ns", outputDir=self.testDir, podLogs=False, noDetail=False)

        namespaceDir = os.path.join(self.testDir, "test-ns")
        assert os.path.exists(namespaceDir)

    def test_collect_pods_creates_pods_directory(self):
        """Test that pods directory is created.

        GIVEN pods exist
        WHEN collectPods is called
        THEN pods directory is created.
        """
        from mas.cli.must_gather.common.pods import collectPods

        mockPod = self._createMockPod("test-pod", "test-ns", "myapp")
        mockApi = Mock()
        mockApi.get.return_value = self._createMockPodList([mockPod])
        self.mockClient.resources.get.return_value = mockApi

        collectPods(dynClient=self.mockClient, namespace="test-ns", outputDir=self.testDir, podLogs=False, noDetail=False)

        podsDir = os.path.join(self.testDir, "test-ns", "pods")
        assert os.path.exists(podsDir)

    def test_collect_pods_creates_markdown_summary_file(self):
        """Test that markdown summary file is created.

        GIVEN pods exist
        WHEN collectPods is called
        THEN summary pods.md file is created.
        """
        from mas.cli.must_gather.common.pods import collectPods

        mockPod = self._createMockPod("test-pod", "test-ns")
        mockApi = Mock()
        mockApi.get.return_value = self._createMockPodList([mockPod])
        self.mockClient.resources.get.return_value = mockApi

        success, count = collectPods(dynClient=self.mockClient, namespace="test-ns", outputDir=self.testDir, podLogs=False, noDetail=False)

        summaryFile = os.path.join(self.testDir, "test-ns", "pods.md")
        assert os.path.exists(summaryFile)

    def test_collect_pods_markdown_summary_links_yaml_and_logs(self):
        """Test that pod markdown summary links YAML and logs.

        GIVEN pods exist and pod logs are collected
        WHEN collectPods is called
        THEN pods.md contains markdown links for both YAML and log files.
        """
        from mas.cli.must_gather.common.pods import collectPods

        mockPod = self._createMockPod("test-pod", "test-ns", "myapp", ["container1"])
        mockApi = Mock()
        mockApi.get.return_value = self._createMockPodList([mockPod])
        self.mockClient.resources.get.return_value = mockApi

        collectPods(dynClient=self.mockClient, namespace="test-ns", outputDir=self.testDir, podLogs=True, noDetail=False)

        summaryFile = os.path.join(self.testDir, "test-ns", "pods.md")
        with open(summaryFile, "r") as f:
            content = f.read()

        assert "| NAME | READY | STATUS | RESTARTS | AGE | YAML | LOGS |" in content
        assert "[test-pod](pods/myapp/test-pod.yaml)" in content
        assert "[logs](pods/myapp/logs/)" in content

    def test_collect_pods_markdown_summary_omits_logs_link_when_logs_disabled(self):
        """Test that pod markdown summary omits logs link when logs are disabled.

        GIVEN pods exist and pod logs are not collected
        WHEN collectPods is called
        THEN pods.md contains YAML links and an empty logs column.
        """
        from mas.cli.must_gather.common.pods import collectPods

        mockPod = self._createMockPod("test-pod", "test-ns", "myapp")
        mockApi = Mock()
        mockApi.get.return_value = self._createMockPodList([mockPod])
        self.mockClient.resources.get.return_value = mockApi

        collectPods(dynClient=self.mockClient, namespace="test-ns", outputDir=self.testDir, podLogs=False, noDetail=False)

        summaryFile = os.path.join(self.testDir, "test-ns", "pods.md")
        with open(summaryFile, "r") as f:
            content = f.read()

        assert "[test-pod](pods/myapp/test-pod.yaml)" in content
        assert "[logs](pods/myapp/logs/)" not in content

    def test_collect_pods_organizes_by_app_label(self):
        """Test that pods are organized by app label.

        GIVEN pods with app labels
        WHEN collectPods is called
        THEN pods are organized into app subdirectories.
        """
        from mas.cli.must_gather.common.pods import collectPods

        mockPod = self._createMockPod("test-pod", "test-ns", "myapp")
        mockApi = Mock()
        mockApi.get.return_value = self._createMockPodList([mockPod])
        self.mockClient.resources.get.return_value = mockApi

        collectPods(dynClient=self.mockClient, namespace="test-ns", outputDir=self.testDir, podLogs=False, noDetail=False)

        appDir = os.path.join(self.testDir, "test-ns", "pods", "myapp")
        assert os.path.exists(appDir)

    def test_collect_pods_creates_yaml_file_when_detail_enabled(self):
        """Test that YAML file is created when noDetail is False.

        GIVEN noDetail is False
        WHEN collectPods is called
        THEN YAML file is created for each pod.
        """
        from mas.cli.must_gather.common.pods import collectPods

        mockPod = self._createMockPod("test-pod", "test-ns", "myapp")
        mockApi = Mock()
        mockApi.get.return_value = self._createMockPodList([mockPod])
        self.mockClient.resources.get.return_value = mockApi

        collectPods(dynClient=self.mockClient, namespace="test-ns", outputDir=self.testDir, podLogs=False, noDetail=False)

        yamlFile = os.path.join(self.testDir, "test-ns", "pods", "myapp", "test-pod.yaml")
        assert os.path.exists(yamlFile)

    def test_collect_pods_skips_yaml_when_no_detail(self):
        """Test that YAML file is not created when noDetail is True.

        GIVEN noDetail is True
        WHEN collectPods is called
        THEN no YAML file is created.
        """
        from mas.cli.must_gather.common.pods import collectPods

        mockPod = self._createMockPod("test-pod", "test-ns", "myapp")
        mockApi = Mock()
        mockApi.get.return_value = self._createMockPodList([mockPod])
        self.mockClient.resources.get.return_value = mockApi

        collectPods(dynClient=self.mockClient, namespace="test-ns", outputDir=self.testDir, podLogs=False, noDetail=True)

        yamlFile = os.path.join(self.testDir, "test-ns", "pods", "myapp", "test-pod.yaml")
        assert not os.path.exists(yamlFile)

    def test_collect_pods_collects_logs_when_enabled(self):
        """Test that container logs are collected when podLogs is True.

        GIVEN podLogs is True and pod has containers
        WHEN collectPods is called
        THEN log files are created for each container.
        """
        from mas.cli.must_gather.common.pods import collectPods

        mockPod = self._createMockPod("test-pod", "test-ns", "myapp", ["container1", "container2"])
        mockApi = Mock()
        mockApi.get.return_value = self._createMockPodList([mockPod])
        self.mockClient.resources.get.return_value = mockApi

        # Mock log retrieval
        mockCoreV1 = Mock()
        mockCoreV1.read_namespaced_pod_log.return_value = "log content"
        self.mockClient.resources.get.return_value.read_namespaced_pod_log = mockCoreV1.read_namespaced_pod_log

        collectPods(dynClient=self.mockClient, namespace="test-ns", outputDir=self.testDir, podLogs=True, noDetail=False)

        logsDir = os.path.join(self.testDir, "test-ns", "pods", "myapp", "logs")
        assert os.path.exists(logsDir)

    def test_collect_pods_skips_logs_when_disabled(self):
        """Test that logs are not collected when podLogs is False.

        GIVEN podLogs is False
        WHEN collectPods is called
        THEN no log files are created.
        """
        from mas.cli.must_gather.common.pods import collectPods

        mockPod = self._createMockPod("test-pod", "test-ns", "myapp", ["container1"])
        mockApi = Mock()
        mockApi.get.return_value = self._createMockPodList([mockPod])
        self.mockClient.resources.get.return_value = mockApi

        collectPods(dynClient=self.mockClient, namespace="test-ns", outputDir=self.testDir, podLogs=False, noDetail=False)

        logsDir = os.path.join(self.testDir, "test-ns", "pods", "myapp", "logs")
        assert not os.path.exists(logsDir)

    def test_collect_pods_handles_api_error(self):
        """Test graceful handling of API errors.

        GIVEN API call fails
        WHEN collectPods is called
        THEN function handles error gracefully and returns False.
        """
        from mas.cli.must_gather.common.pods import collectPods

        mockApi = Mock()
        mockApi.get.side_effect = Exception("API Error")
        self.mockClient.resources.get.return_value = mockApi

        success, count = collectPods(dynClient=self.mockClient, namespace="test-ns", outputDir=self.testDir, podLogs=False, noDetail=False)

        assert success is False

    def test_collect_pods_returns_true_on_success(self):
        """Test that function returns True on successful collection.

        GIVEN valid parameters
        WHEN collectPods completes successfully
        THEN function returns True.
        """
        from mas.cli.must_gather.common.pods import collectPods

        mockApi = Mock()
        mockApi.get.return_value = self._createMockPodList([])
        self.mockClient.resources.get.return_value = mockApi

        success, count = collectPods(dynClient=self.mockClient, namespace="test-ns", outputDir=self.testDir, podLogs=False, noDetail=False)

        assert success is True


# Made with Bob
