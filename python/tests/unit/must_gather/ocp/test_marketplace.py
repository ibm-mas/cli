# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Test OCP marketplace resource collection."""

import os
import tempfile
import shutil
from unittest.mock import Mock, patch
from kubernetes.dynamic import DynamicClient


class TestGenerateMarketplaceCollectionTasks:
    """Test generation of marketplace collection task tuples."""

    def setup_method(self):
        """Set up test fixtures.

        GIVEN a test environment
        WHEN tests are run
        THEN create temporary directory and mock Kubernetes client.
        """
        self.testDir = tempfile.mkdtemp()
        self.mockClient = Mock(spec=DynamicClient)
        self.mockClient.client = Mock()

    def teardown_method(self):
        """Clean up test fixtures.

        GIVEN test completion
        WHEN teardown is called
        THEN remove temporary directory.
        """
        if os.path.exists(self.testDir):
            shutil.rmtree(self.testDir)

    @patch("mas.cli.must_gather.common.task_generation.generatePodCollectionTasks", return_value=[])
    def test_generates_tasks_via_namespace_collection(self, mockPodTasks):
        """Test that tasks are generated via generateNamespaceCollectionTasks.

        GIVEN a dynamic client and output directory
        WHEN generateMarketplaceCollectionTasks is called
        THEN tasks from generateNamespaceCollectionTasks are returned (not a hand-rolled list).
        """
        from mas.cli.must_gather.ocp.marketplace import generateMarketplaceCollectionTasks

        tasks = generateMarketplaceCollectionTasks(dynClient=self.mockClient, outputDir=self.testDir)

        # generateNamespaceCollectionTasks includes standard resources (ConfigMap, Service, etc.)
        taskNames = [t[0] for t in tasks]
        assert any("configmap" in n.lower() for n in taskNames), "Should include standard ConfigMap task"
        assert any("service" in n.lower() for n in taskNames), "Should include standard Service task"
        assert any("secret" in n.lower() for n in taskNames), "Should include secrets task"

    @patch("mas.cli.must_gather.common.task_generation.generatePodCollectionTasks", return_value=[])
    def test_includes_catalogsource_as_custom_resource(self, mockPodTasks):
        """Test that CatalogSource is included as a custom resource task.

        GIVEN a dynamic client and output directory
        WHEN generateMarketplaceCollectionTasks is called
        THEN a task for CatalogSource is present.
        """
        from mas.cli.must_gather.ocp.marketplace import generateMarketplaceCollectionTasks

        tasks = generateMarketplaceCollectionTasks(dynClient=self.mockClient, outputDir=self.testDir)

        taskNames = [t[0] for t in tasks]
        assert any("catalogsource" in n.lower() for n in taskNames), "Should include a task for CatalogSource"

    @patch("mas.cli.must_gather.common.task_generation.generatePodCollectionTasks", return_value=[])
    def test_tasks_target_openshift_marketplace_namespace(self, mockPodTasks):
        """Test that generated tasks target the openshift-marketplace namespace.

        GIVEN a dynamic client and output directory
        WHEN generateMarketplaceCollectionTasks is called
        THEN collectResources tasks pass openshift-marketplace as the namespace argument.
        """
        from mas.cli.must_gather.ocp.marketplace import generateMarketplaceCollectionTasks
        from mas.cli.must_gather.common.resources import collectResources

        tasks = generateMarketplaceCollectionTasks(dynClient=self.mockClient, outputDir=self.testDir)

        # All collectResources tasks should target openshift-marketplace
        for task in tasks:
            if task[1] is collectResources:
                assert task[2] == "openshift-marketplace", f"Task {task[0]} must target openshift-marketplace, got {task[2]}"

    @patch("mas.cli.must_gather.common.task_generation.generatePodCollectionTasks", return_value=[("pod_test", Mock())])
    def test_includes_pod_tasks_when_logs_enabled(self, mockPodTasks):
        """Test that pod tasks are included when noLogs is False.

        GIVEN a dynamic client and noLogs=False
        WHEN generateMarketplaceCollectionTasks is called
        THEN generatePodCollectionTasks is called with podLogs=True.
        """
        from mas.cli.must_gather.ocp.marketplace import generateMarketplaceCollectionTasks

        generateMarketplaceCollectionTasks(dynClient=self.mockClient, outputDir=self.testDir, noLogs=False)

        mockPodTasks.assert_called_once_with(dynClient=self.mockClient, namespace="openshift-marketplace", outputDir=self.testDir, podLogs=True)

    @patch("mas.cli.must_gather.common.task_generation.generatePodCollectionTasks", return_value=[])
    def test_suppresses_pod_logs_when_no_logs_true(self, mockPodTasks):
        """Test that pod logs are suppressed when noLogs is True.

        GIVEN a dynamic client and noLogs=True
        WHEN generateMarketplaceCollectionTasks is called
        THEN generatePodCollectionTasks is called with podLogs=False.
        """
        from mas.cli.must_gather.ocp.marketplace import generateMarketplaceCollectionTasks

        generateMarketplaceCollectionTasks(dynClient=self.mockClient, outputDir=self.testDir, noLogs=True)

        mockPodTasks.assert_called_once_with(dynClient=self.mockClient, namespace="openshift-marketplace", outputDir=self.testDir, podLogs=False)


class TestAddMarketplaceToCollectionPlan:
    """Test adding marketplace collection to a plan."""

    def setup_method(self):
        """Set up test fixtures.

        GIVEN a test environment
        WHEN tests are run
        THEN create temporary directory and mock plan and dynamic client.
        """
        self.testDir = tempfile.mkdtemp()
        self.mockPlan = Mock()
        self.mockClient = Mock(spec=DynamicClient)
        self.mockClient.client = Mock()

    def teardown_method(self):
        """Clean up test fixtures.

        GIVEN test completion
        WHEN teardown is called
        THEN remove temporary directory.
        """
        if os.path.exists(self.testDir):
            shutil.rmtree(self.testDir)

    @patch("mas.cli.must_gather.common.task_generation.generatePodCollectionTasks", return_value=[])
    def test_adds_group_to_plan(self, mockPodTasks):
        """Test that a collection group is added to the plan.

        GIVEN a collection plan and dynamic client
        WHEN addMarketplaceToCollectionPlan is called
        THEN plan.addGroup is called with marketplace tasks.
        """
        from mas.cli.must_gather.ocp.marketplace import addMarketplaceToCollectionPlan

        addMarketplaceToCollectionPlan(plan=self.mockPlan, dynClient=self.mockClient, outputDir=self.testDir)

        self.mockPlan.addGroup.assert_called_once()
        callArgs = self.mockPlan.addGroup.call_args
        groupName = callArgs[0][0]
        tasks = callArgs[0][1]
        assert "Marketplace" in groupName or "marketplace" in groupName.lower(), f"Group name should reference Marketplace, got: {groupName}"
        assert len(tasks) > 0, "Should add at least one task to the group"
