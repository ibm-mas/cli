# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Collection plan infrastructure for parallel must-gather execution.

This module provides classes for planning and organizing collection tasks
that can be executed in parallel while maintaining sequential display order.
"""

from typing import List, Tuple, Any


class CollectionGroup:
    """Represents a logical group of collection tasks.

    A collection group organizes related tasks that should be displayed together
    in the output, even though they may execute in parallel with other groups.
    """

    def __init__(self, name: str, tasks: List[Tuple]):
        """Initialize a collection group.

        Args:
            name (str): Display name for this group (e.g., "Kafka (strimzi)")
            tasks (list): List of task tuples in format (task_name, func, *args)
        """
        self.name = name
        self.tasks = tasks
        self.futures = []

    @property
    def taskGroups(self) -> List[Tuple[str, List[Any]]]:
        """Group tasks by type for display.

        Groups tasks by their type name (first element of task tuple) and
        associates each group with its corresponding futures for progress tracking.

        Returns:
            list: List of (task_type, futures) tuples in order of first occurrence
        """
        # Build a mapping of task type to indices
        taskTypeIndices = {}
        taskTypeOrder = []

        for i, task in enumerate(self.tasks):
            taskType = task[0]
            if taskType not in taskTypeIndices:
                taskTypeIndices[taskType] = []
                taskTypeOrder.append(taskType)
            taskTypeIndices[taskType].append(i)

        # Build result list with futures for each task type
        result = []
        for taskType in taskTypeOrder:
            indices = taskTypeIndices[taskType]
            futures = [self.futures[i] for i in indices] if self.futures else []
            result.append((taskType, futures))

        return result


class CollectionPlan:
    """Represents the complete collection plan with all tasks.

    The collection plan organizes all collection tasks into logical groups
    that can be executed in parallel while maintaining a clean sequential
    display in the output.
    """

    def __init__(self):
        """Initialize an empty collection plan."""
        self.groups = []
        self.total_tasks = 0
        self.total_groups = 0

    def addGroup(self, name: str, tasks: List[Tuple]):
        """Add a collection group to the plan.

        Args:
            name (str): Display name for the group
            tasks (list): List of task tuples in format (task_name, func, *args)
        """
        group = CollectionGroup(name, tasks)
        self.groups.append(group)
        self.total_tasks += len(tasks)
        self.total_groups += 1
