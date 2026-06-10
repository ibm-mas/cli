# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Parallel execution engine for collection tasks.

This module provides the execution infrastructure for running collection tasks
in parallel while maintaining sequential display order for user feedback.
"""

import logging
from typing import Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from .collection_plan import CollectionPlan

logger = logging.getLogger(__name__)


def executeCollection(
    plan: CollectionPlan,
    maxWorkers: int = 50,
    displayCallback: Optional[Callable[[str, str, int, int, Any], None]] = None,
) -> bool:
    """Execute all collection tasks in parallel with sequential display.

    Submits all tasks from all groups to a shared threadpool immediately,
    then displays progress sequentially by group while tasks complete in
    the background.

    Args:
        plan (CollectionPlan): The collection plan containing all tasks
        maxWorkers (int, optional): Maximum number of parallel threads. Defaults to 50.
        displayCallback (callable, optional): Callback for progress display.
            Called with (groupName, taskType, completed, total, progressBar). Defaults to None.

    Returns:
        bool: True if execution completed (even if some tasks failed)
    """
    # Handle empty plan
    if not plan.groups:
        return True

    # Single massive threadpool - submit ALL tasks immediately
    with ThreadPoolExecutor(max_workers=maxWorkers) as executor:
        # Submit every single task to the pool upfront
        allFutures = {}
        for group in plan.groups:
            groupFutures = []
            for taskName, func, *args in group.tasks:
                future = executor.submit(func, *args)
                allFutures[future] = (group.name, taskName)
                groupFutures.append(future)
            group.futures = groupFutures

        # Now show sequential progress for each group
        # Tasks are already running in background!
        for group in plan.groups:
            # Show progress for each task type in the group
            for taskType, futuresSubset in group.taskGroups:
                total = len(futuresSubset)
                completed = 0

                # Wait for this subset of futures to complete
                # Many may already be done by the time we get here!
                for future in as_completed(futuresSubset):
                    try:
                        future.result()
                        completed += 1
                        if displayCallback:
                            displayCallback(group.name, taskType, completed, total, None)
                    except Exception as e:
                        logger.error(f"❌ Task failed in {group.name}/{taskType}: {e}")
                        completed += 1
                        if displayCallback:
                            displayCallback(group.name, taskType, completed, total, None)

    return True
