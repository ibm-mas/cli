# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for CollectionPlan and CollectionGroup classes."""

from mas.cli.must_gather.collection_plan import CollectionPlan, CollectionGroup


def test_collectionPlan_initializes_empty():
    """Test that CollectionPlan initializes with empty state.

    GIVEN a new CollectionPlan instance
    WHEN it is created
    THEN it has empty groups list and zero counters.
    """
    plan = CollectionPlan()

    assert plan.groups == []
    assert plan.total_tasks == 0
    assert plan.total_groups == 0


def test_collectionPlan_addGroup_adds_group_and_updates_counters():
    """Test that addGroup adds a group and updates task/group counters.

    GIVEN a CollectionPlan instance
    WHEN addGroup is called with a group name and tasks
    THEN the group is added and counters are updated correctly.
    """
    plan = CollectionPlan()

    def mockTask1():
        pass

    def mockTask2():
        pass

    tasks = [("task1", mockTask1, "arg1"), ("task2", mockTask2, "arg2")]

    plan.addGroup("Test Group", tasks)

    assert len(plan.groups) == 1
    assert plan.total_groups == 1
    assert plan.total_tasks == 2
    assert plan.groups[0].name == "Test Group"
    assert len(plan.groups[0].tasks) == 2


def test_collectionPlan_addGroup_accumulates_multiple_groups():
    """Test that addGroup correctly accumulates multiple groups.

    GIVEN a CollectionPlan instance
    WHEN multiple groups are added
    THEN all groups are stored and counters reflect total tasks and groups.
    """
    plan = CollectionPlan()

    def mockTask():
        pass

    plan.addGroup("Group 1", [("task1", mockTask, "arg1")])
    plan.addGroup("Group 2", [("task2", mockTask, "arg2"), ("task3", mockTask, "arg3")])

    assert len(plan.groups) == 2
    assert plan.total_groups == 2
    assert plan.total_tasks == 3


def test_collectionGroup_initializes_with_name_and_tasks():
    """Test that CollectionGroup initializes with name and tasks.

    GIVEN a group name and task list
    WHEN CollectionGroup is created
    THEN it stores the name and tasks correctly.
    """

    def mockTask():
        pass

    tasks = [("task1", mockTask, "arg1"), ("task2", mockTask, "arg2")]
    group = CollectionGroup("Test Group", tasks)

    assert group.name == "Test Group"
    assert group.tasks == tasks
    assert group.futures == []


def test_collectionGroup_taskGroups_groups_tasks_by_type():
    """Test that taskGroups property groups tasks by their type name.

    GIVEN a CollectionGroup with multiple tasks of different types
    WHEN taskGroups property is accessed
    THEN tasks are grouped by their type name (first element of tuple).
    """

    def mockTask():
        pass

    tasks = [
        ("ibm_resources", mockTask, "arg1"),
        ("ibm_resources", mockTask, "arg2"),
        ("secrets", mockTask, "arg3"),
        ("pods", mockTask, "arg4"),
        ("pods", mockTask, "arg5"),
    ]
    group = CollectionGroup("Test Group", tasks)

    # Simulate futures being set
    group.futures = [f"future{i}" for i in range(5)]

    taskGroups = group.taskGroups

    assert len(taskGroups) == 3
    # Check that we have the right task types
    taskTypes = [tg[0] for tg in taskGroups]
    assert "ibm_resources" in taskTypes
    assert "secrets" in taskTypes
    assert "pods" in taskTypes

    # Check that futures are grouped correctly
    for taskType, futures in taskGroups:
        if taskType == "ibm_resources":
            assert len(futures) == 2
        elif taskType == "secrets":
            assert len(futures) == 1
        elif taskType == "pods":
            assert len(futures) == 2


def test_collectionGroup_taskGroups_preserves_order():
    """Test that taskGroups preserves the order of first occurrence.

    GIVEN a CollectionGroup with tasks in a specific order
    WHEN taskGroups property is accessed
    THEN task groups appear in order of first occurrence.
    """

    def mockTask():
        pass

    tasks = [
        ("type_a", mockTask, "arg1"),
        ("type_b", mockTask, "arg2"),
        ("type_a", mockTask, "arg3"),
        ("type_c", mockTask, "arg4"),
    ]
    group = CollectionGroup("Test Group", tasks)
    group.futures = [f"future{i}" for i in range(4)]

    taskGroups = group.taskGroups
    taskTypes = [tg[0] for tg in taskGroups]

    assert taskTypes == ["type_a", "type_b", "type_c"]
