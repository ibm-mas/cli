# *****************************************************************************
# Copyright (c) 2024, 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for progress reporter abstraction."""

from unittest.mock import Mock, patch, MagicMock


def test_halo_progress_reporter_imports():
    """Test that HaloProgressReporter can be imported.

    GIVEN the progress module exists
    WHEN importing HaloProgressReporter
    THEN the import succeeds without error.
    """
    from mas.cli.common.progress import HaloProgressReporter

    assert HaloProgressReporter is not None


def test_callback_progress_reporter_imports():
    """Test that CallbackProgressReporter can be imported.

    GIVEN the progress module exists
    WHEN importing CallbackProgressReporter
    THEN the import succeeds without error.
    """
    from mas.cli.common.progress import CallbackProgressReporter

    assert CallbackProgressReporter is not None


def test_halo_reporter_start_creates_spinner():
    """Test that HaloProgressReporter.start() creates a Halo spinner.

    GIVEN a HaloProgressReporter instance
    WHEN start() is called with a label
    THEN a Halo spinner is created and started.
    """
    from mas.cli.common.progress import HaloProgressReporter

    with patch("mas.cli.common.progress.Halo") as mock_halo_class:
        mock_halo = MagicMock()
        mock_halo_class.return_value = mock_halo

        reporter = HaloProgressReporter("dots", "✓", "✗")
        reporter.start("Test stage")

        mock_halo_class.assert_called_once_with(text="Test stage", spinner="dots")
        mock_halo.start.assert_called_once()


def test_halo_reporter_success_stops_spinner():
    """Test that HaloProgressReporter.success() stops the spinner.

    GIVEN a HaloProgressReporter with an active spinner
    WHEN success() is called
    THEN the spinner is stopped with success icon and message.
    """
    from mas.cli.common.progress import HaloProgressReporter

    with patch("mas.cli.common.progress.Halo") as mock_halo_class:
        mock_halo = MagicMock()
        mock_halo_class.return_value = mock_halo

        reporter = HaloProgressReporter("dots", "✓", "✗")
        reporter.start("Test stage")
        reporter.success("Test stage", "completed successfully")

        mock_halo.stop_and_persist.assert_called_once_with(symbol="✓", text="Test stage: completed successfully")


def test_halo_reporter_success_without_detail():
    """Test that HaloProgressReporter.success() works without detail.

    GIVEN a HaloProgressReporter with an active spinner
    WHEN success() is called with empty detail
    THEN the spinner is stopped with just the label.
    """
    from mas.cli.common.progress import HaloProgressReporter

    with patch("mas.cli.common.progress.Halo") as mock_halo_class:
        mock_halo = MagicMock()
        mock_halo_class.return_value = mock_halo

        reporter = HaloProgressReporter("dots", "✓", "✗")
        reporter.start("Test stage")
        reporter.success("Test stage", "")

        mock_halo.stop_and_persist.assert_called_once_with(symbol="✓", text="Test stage")


def test_halo_reporter_failure_stops_spinner():
    """Test that HaloProgressReporter.failure() stops the spinner.

    GIVEN a HaloProgressReporter with an active spinner
    WHEN failure() is called
    THEN the spinner is stopped with failure icon and message.
    """
    from mas.cli.common.progress import HaloProgressReporter

    with patch("mas.cli.common.progress.Halo") as mock_halo_class:
        mock_halo = MagicMock()
        mock_halo_class.return_value = mock_halo

        reporter = HaloProgressReporter("dots", "✓", "✗")
        reporter.start("Test stage")
        reporter.failure("Test stage", "failed with error")

        mock_halo.stop_and_persist.assert_called_once_with(symbol="✗", text="Test stage: failed with error")


def test_callback_reporter_start_calls_callback():
    """Test that CallbackProgressReporter.start() calls start_callback.

    GIVEN a CallbackProgressReporter with start_callback
    WHEN start() is called
    THEN start_callback is invoked with the label.
    """
    from mas.cli.common.progress import CallbackProgressReporter

    start_callback = Mock()
    progress_callback = Mock()

    reporter = CallbackProgressReporter(progress_callback, start_callback)
    reporter.start("Test stage")

    start_callback.assert_called_once_with("Test stage")


def test_callback_reporter_start_without_callback():
    """Test that CallbackProgressReporter.start() works without start_callback.

    GIVEN a CallbackProgressReporter without start_callback
    WHEN start() is called
    THEN no error occurs.
    """
    from mas.cli.common.progress import CallbackProgressReporter

    progress_callback = Mock()
    reporter = CallbackProgressReporter(progress_callback, None)
    reporter.start("Test stage")  # Should not raise


def test_callback_reporter_success_calls_callback():
    """Test that CallbackProgressReporter.success() calls progress_callback.

    GIVEN a CallbackProgressReporter
    WHEN success() is called
    THEN progress_callback is invoked with (label, True, detail).
    """
    from mas.cli.common.progress import CallbackProgressReporter

    progress_callback = Mock()
    reporter = CallbackProgressReporter(progress_callback)

    reporter.success("Test stage", "completed successfully")

    progress_callback.assert_called_once_with("Test stage", True, "completed successfully")


def test_callback_reporter_failure_calls_callback():
    """Test that CallbackProgressReporter.failure() calls progress_callback.

    GIVEN a CallbackProgressReporter
    WHEN failure() is called
    THEN progress_callback is invoked with (label, False, detail).
    """
    from mas.cli.common.progress import CallbackProgressReporter

    progress_callback = Mock()
    reporter = CallbackProgressReporter(progress_callback)

    reporter.failure("Test stage", "failed with error")

    progress_callback.assert_called_once_with("Test stage", False, "failed with error")
