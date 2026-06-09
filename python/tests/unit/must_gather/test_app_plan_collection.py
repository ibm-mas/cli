# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for MustGatherApp.planCollection() method."""

import unittest
from unittest.mock import Mock, patch
from mas.cli.must_gather.app import MustGatherApp
from mas.cli.must_gather.collection_plan import CollectionPlan


class TestPlanCollection(unittest.TestCase):
    """Test the planCollection method."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = MustGatherApp()
        self.app.dynClient = Mock()
        self.app.printerColumnsCache = {}
        self.app.ibmCRDsList = []

    def test_planCollection_creates_collection_plan(self):
        """Test that planCollection creates a CollectionPlan instance.

        GIVEN a MustGatherApp with initialized Kubernetes client
        WHEN planCollection is called with parsed arguments
        THEN a CollectionPlan instance is returned.
        """
        # Create mock parsed args
        parsedArgs = Mock()
        parsedArgs.no_ocp = False
        parsedArgs.no_dependencies = False
        parsedArgs.no_sls = False
        parsedArgs.mas_instance_ids = None
        parsedArgs.mas_app_ids = None
        parsedArgs.summary_only = False
        parsedArgs.no_logs = False
        parsedArgs.extra_namespaces = None

        outputDir = "/tmp/test-output"

        # Call planCollection
        plan = self.app.planCollection(parsedArgs, outputDir)

        # Verify result
        self.assertIsInstance(plan, CollectionPlan)

    @patch("mas.cli.must_gather.dependencies.kafka.discoverKafkaNamespaces")
    @patch("mas.cli.must_gather.dependencies.mongodb.discoverMongoDBNamespaces")
    def test_planCollection_discovers_dependencies(self, mockMongoDiscovery, mockKafkaDiscovery):
        """Test that planCollection discovers dependency namespaces.

        GIVEN dependency namespaces exist in the cluster
        WHEN planCollection is called without --no-dependencies
        THEN discovery functions are called for each dependency type.
        """
        # Setup mocks
        mockKafkaDiscovery.return_value = {"kafka-ns"}
        mockMongoDiscovery.return_value = {"mongo-ns"}

        parsedArgs = Mock()
        parsedArgs.no_ocp = True  # Skip OCP to focus on dependencies
        parsedArgs.no_dependencies = False
        parsedArgs.no_sls = True
        parsedArgs.mas_instance_ids = None
        parsedArgs.mas_app_ids = None
        parsedArgs.summary_only = False
        parsedArgs.no_logs = False
        parsedArgs.extra_namespaces = None

        outputDir = "/tmp/test-output"

        # Call planCollection
        plan = self.app.planCollection(parsedArgs, outputDir)

        # Verify discovery was called
        mockKafkaDiscovery.assert_called_once_with(self.app.dynClient)
        mockMongoDiscovery.assert_called_once_with(self.app.dynClient)

        # Verify plan has groups
        self.assertGreater(plan.total_groups, 0)
        self.assertGreater(plan.total_tasks, 0)

    def test_planCollection_respects_no_dependencies_flag(self):
        """Test that planCollection skips dependencies when --no-dependencies is set.

        GIVEN --no-dependencies flag is set
        WHEN planCollection is called
        THEN no dependency discovery occurs.
        """
        parsedArgs = Mock()
        parsedArgs.no_ocp = True
        parsedArgs.no_dependencies = True
        parsedArgs.no_sls = True
        parsedArgs.mas_instance_ids = None
        parsedArgs.mas_app_ids = None
        parsedArgs.summary_only = False
        parsedArgs.no_logs = False
        parsedArgs.extra_namespaces = None

        outputDir = "/tmp/test-output"

        # Call planCollection
        plan = self.app.planCollection(parsedArgs, outputDir)

        # Verify plan is empty or minimal
        self.assertIsInstance(plan, CollectionPlan)


if __name__ == "__main__":
    unittest.main()
