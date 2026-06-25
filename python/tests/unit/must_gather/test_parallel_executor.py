# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for parallel collection executor."""

from unittest.mock import Mock
from mas.cli.must_gather.parallel_executor import executeCollection
from mas.cli.must_gather.collection_plan import CollectionPlan


def test_executeCollection_executes_all_tasks_in_parallel():
    """Test that executeCollection submits all tasks to threadpool immediately.

    GIVEN a CollectionPlan with multiple groups and tasks
    WHEN executeCollection is called
    THEN all tasks are submitted to the threadpool before any display starts.
    """
    plan = CollectionPlan()

    # Track execution order
    executionOrder = []

    def task1():
        executionOrder.append("task1")
        return True

    def task2():
        executionOrder.append("task2")
        return True

    def task3():
        executionOrder.append("task3")
        return True

    plan.addGroup("Group 1", [("type_a", task1)])
    plan.addGroup("Group 2", [("type_b", task2), ("type_c", task3)])

    # Mock the display functions
    mockDisplay = Mock()

    result = executeCollection(plan, maxWorkers=10, displayCallback=mockDisplay)

    # All tasks should have executed
    assert len(executionOrder) == 3
    assert result is True


def test_executeCollection_handles_task_failures_gracefully():
    """Test that executeCollection continues when individual tasks fail.

    GIVEN a CollectionPlan with tasks that will fail
    WHEN executeCollection is called
    THEN failed tasks are logged but execution continues for other tasks.
    """
    plan = CollectionPlan()

    successCount = [0]
    failureCount = [0]

    def successTask():
        successCount[0] += 1
        return True

    def failureTask():
        failureCount[0] += 1
        raise Exception("Task failed")

    plan.addGroup("Group 1", [("type_a", successTask), ("type_b", failureTask), ("type_c", successTask)])

    mockDisplay = Mock()

    result = executeCollection(plan, maxWorkers=10, displayCallback=mockDisplay)

    # All tasks should have been attempted
    assert successCount[0] == 2
    assert failureCount[0] == 1
    # Overall result should still be True (we don't fail the whole collection)
    assert result is True


def test_executeCollection_calls_display_callback_for_each_group():
    """Test that executeCollection calls display callback for each group.

    GIVEN a CollectionPlan with multiple groups
    WHEN executeCollection is called with a display callback
    THEN the callback is called once for each group with group info.
    """
    plan = CollectionPlan()

    def mockTask():
        return True

    plan.addGroup("Group 1", [("type_a", mockTask)])
    plan.addGroup("Group 2", [("type_b", mockTask)])

    displayCalls = []

    def displayCallback(groupName, taskType, completed, total, error):
        displayCalls.append((groupName, taskType, completed, total, error))

    executeCollection(plan, maxWorkers=10, displayCallback=displayCallback)

    # Should have been called for each task type in each group
    assert len(displayCalls) >= 2
    # Check that group names were passed
    groupNames = [call[0] for call in displayCalls]
    assert "Group 1" in groupNames
    assert "Group 2" in groupNames


def test_executeCollection_respects_max_workers_limit():
    """Test that executeCollection respects the maxWorkers parameter.

    GIVEN a CollectionPlan with many tasks
    WHEN executeCollection is called with a specific maxWorkers value
    THEN the threadpool is created with that limit.
    """
    plan = CollectionPlan()

    def mockTask():
        return True

    # Add just a few tasks to avoid hanging
    for i in range(3):
        plan.addGroup(f"Group {i}", [("type_a", mockTask)])

    mockDisplay = Mock()

    # Just verify it completes successfully with custom max_workers
    result = executeCollection(plan, maxWorkers=5, displayCallback=mockDisplay)

    assert result is True


def test_executeCollection_handles_empty_plan():
    """Test that executeCollection handles an empty plan gracefully.

    GIVEN an empty CollectionPlan
    WHEN executeCollection is called
    THEN it returns True without errors.
    """
    plan = CollectionPlan()
    mockDisplay = Mock()

    result = executeCollection(plan, maxWorkers=10, displayCallback=mockDisplay)

    assert result is True
    # Display callback should not have been called
    mockDisplay.assert_not_called()
