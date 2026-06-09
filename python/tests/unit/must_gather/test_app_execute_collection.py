# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for MustGatherApp.executeCollectionPlan() method."""

import unittest
from unittest.mock import patch
from mas.cli.must_gather.app import MustGatherApp
from mas.cli.must_gather.collection_plan import CollectionPlan


class TestExecuteCollectionPlan(unittest.TestCase):
    """Test the executeCollectionPlan method."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = MustGatherApp()

    def test_executeCollectionPlan_with_empty_plan(self):
        """Test that executeCollectionPlan handles empty plan.

        GIVEN an empty CollectionPlan
        WHEN executeCollectionPlan is called
        THEN it returns True without errors.
        """
        plan = CollectionPlan()

        result = self.app.executeCollectionPlan(plan)

        self.assertTrue(result)

    @patch("mas.cli.must_gather.parallel_executor.executeCollection")
    def test_executeCollectionPlan_calls_parallel_executor(self, mockExecuteCollection):
        """Test that executeCollectionPlan delegates to parallel executor.

        GIVEN a CollectionPlan with tasks
        WHEN executeCollectionPlan is called
        THEN it calls the parallel executor with the plan.
        """
        mockExecuteCollection.return_value = True

        plan = CollectionPlan()
        plan.addGroup("Test Group", [("task1", lambda: None)])

        result = self.app.executeCollectionPlan(plan)

        mockExecuteCollection.assert_called_once()
        self.assertTrue(result)

    @patch("mas.cli.must_gather.parallel_executor.executeCollection")
    def test_executeCollectionPlan_with_multiple_groups(self, mockExecuteCollection):
        """Test that executeCollectionPlan handles multiple groups.

        GIVEN a CollectionPlan with multiple groups
        WHEN executeCollectionPlan is called
        THEN all groups are executed.
        """
        mockExecuteCollection.return_value = True

        plan = CollectionPlan()
        plan.addGroup("Group 1", [("task1", lambda: None)])
        plan.addGroup("Group 2", [("task2", lambda: None)])

        result = self.app.executeCollectionPlan(plan)

        mockExecuteCollection.assert_called_once()
        self.assertTrue(result)
        self.assertEqual(plan.total_groups, 2)


if __name__ == "__main__":
    unittest.main()
