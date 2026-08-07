# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Test timer utilities for must-gather."""

import time
from mas.cli.must_gather.timer import Timer


class TestTimer:
    """Test timer functionality."""

    def test_timer_tracks_elapsed_time(self):
        """Test that timer tracks elapsed time correctly.

        GIVEN timer instance
        WHEN start and stop are called with delay
        THEN elapsed time is approximately correct.
        """
        timer = Timer()
        timer.start()
        time.sleep(0.1)
        elapsed = timer.stop()

        assert elapsed >= 0
        assert elapsed < 1  # Should be much less than 1 second

    def test_timer_returns_elapsed_seconds(self):
        """Test that timer returns elapsed time in seconds.

        GIVEN timer instance
        WHEN stop is called after start
        THEN elapsed time is returned as integer seconds.
        """
        timer = Timer()
        timer.start()
        time.sleep(0.1)
        elapsed = timer.stop()

        assert isinstance(elapsed, int)

    def test_timer_can_be_reused(self):
        """Test that timer can be started and stopped multiple times.

        GIVEN timer instance
        WHEN start/stop called multiple times
        THEN each measurement is independent.
        """
        timer = Timer()

        timer.start()
        time.sleep(1.1)
        elapsed1 = timer.stop()

        timer.start()
        time.sleep(2.1)
        elapsed2 = timer.stop()

        assert elapsed2 > elapsed1

    def test_timer_get_elapsed_without_stop(self):
        """Test that getElapsed returns current elapsed time without stopping.

        GIVEN running timer
        WHEN getElapsed is called
        THEN current elapsed time is returned without stopping timer.
        """
        timer = Timer()
        timer.start()
        time.sleep(1.1)

        elapsed1 = timer.getElapsed()
        time.sleep(1.1)
        elapsed2 = timer.getElapsed()

        assert elapsed2 > elapsed1
        assert timer.startTime is not None  # Timer still running

    def test_timer_format_message(self):
        """Test that formatMessage creates properly formatted output.

        GIVEN timer with elapsed time
        WHEN formatMessage is called with label
        THEN formatted message includes label and time.
        """
        timer = Timer()
        timer.start()
        time.sleep(0.1)
        elapsed = timer.stop()

        message = timer.formatMessage("Test Operation")

        assert "Test Operation" in message
        assert "completed" in message
        assert str(elapsed) in message
        assert "seconds" in message

    def test_stop_without_start_returns_zero(self):
        """Test that stop without start returns zero.

        GIVEN timer that was never started
        WHEN stop is called
        THEN zero is returned.
        """
        timer = Timer()
        elapsed = timer.stop()

        assert elapsed == 0

    def test_get_elapsed_without_start_returns_zero(self):
        """Test that getElapsed without start returns zero.

        GIVEN timer that was never started
        WHEN getElapsed is called
        THEN zero is returned.
        """
        timer = Timer()
        elapsed = timer.getElapsed()

        assert elapsed == 0
