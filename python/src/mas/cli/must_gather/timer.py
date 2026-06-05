# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Timer utilities for tracking must-gather collection time."""

import time
from typing import Optional


class Timer:
    """Track elapsed time for must-gather operations.

    Provides simple start/stop timing functionality with formatted output
    matching the bash implementation's timer behavior.
    """

    def __init__(self):
        """Initialize timer."""
        self.startTime: Optional[float] = None
        self.endTime: Optional[float] = None

    def start(self) -> None:
        """Start the timer.

        Records the current time as the start time and resets end time.
        """
        self.endTime = None
        self.startTime = time.time()

    def stop(self) -> int:
        """Stop the timer and return elapsed time.

        Returns:
            int: Elapsed time in seconds (rounded down)
        """
        if self.startTime is None:
            return 0

        self.endTime = time.time()
        return int(self.endTime - self.startTime)

    def getElapsed(self) -> int:
        """Get current elapsed time without stopping the timer.

        Returns:
            int: Elapsed time in seconds (rounded down)
        """
        if self.startTime is None:
            return 0

        currentTime = time.time()
        return int(currentTime - self.startTime)

    def formatMessage(self, label: str) -> str:
        """Format a completion message with elapsed time.

        Args:
            label (str): Label describing what was timed

        Returns:
            str: Formatted message like "Collection for X completed in N seconds"
        """
        if self.endTime is None:
            elapsed = self.getElapsed()
        else:
            elapsed = int(self.endTime - (self.startTime or 0))
        return f"Collection for {label} completed in {elapsed} seconds"


# Made with Bob
