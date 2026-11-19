# *****************************************************************************
# Copyright (c) 2024, 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Progress reporting abstraction for CLI and TUI execution paths.

Provides a unified interface for reporting progress during long-running
operations, with implementations for both CLI (Halo spinners) and TUI
(callback-based) execution modes.
"""

from typing import Protocol, Optional, Callable
from halo import Halo


class ProgressReporter(Protocol):
    """Protocol for reporting progress during long-running operations.

    Defines the interface that both CLI and TUI progress reporters must
    implement, enabling a single execution path to report progress through
    different mechanisms.
    """

    def start(self, label: str) -> None:
        """Signal that a stage is starting.

        Args:
            label (str): Human-readable description of the stage
        """
        ...

    def success(self, label: str, detail: str) -> None:
        """Report successful completion of a stage.

        Args:
            label (str): Human-readable description of the stage
            detail (str): Additional detail about the success (e.g., version, URL)
        """
        ...

    def failure(self, label: str, detail: str) -> None:
        """Report failure of a stage.

        Args:
            label (str): Human-readable description of the stage
            detail (str): Error message or failure reason
        """
        ...


class HaloProgressReporter:
    """CLI progress reporter using Halo spinners.

    Implements the ProgressReporter protocol using Halo spinners for
    terminal-based progress indication. Each stage gets its own spinner
    that is started, then stopped with a success or failure icon.
    """

    def __init__(self, spinner: str, success_icon: str, failure_icon: str):
        """Initialize the Halo progress reporter.

        Args:
            spinner (str): Halo spinner style (e.g., "dots", "line")
            success_icon (str): Icon to display on success (e.g., "✓")
            failure_icon (str): Icon to display on failure (e.g., "✗")
        """
        self.spinner = spinner
        self.success_icon = success_icon
        self.failure_icon = failure_icon
        self._current_halo: Optional[Halo] = None

    def start(self, label: str) -> None:
        """Start a Halo spinner for the stage.

        Args:
            label (str): Stage description to display
        """
        self._current_halo = Halo(text=label, spinner=self.spinner)
        self._current_halo.start()

    def success(self, label: str, detail: str) -> None:
        """Stop the spinner with success icon and message.

        Args:
            label (str): Stage description
            detail (str): Success detail (appended to label if non-empty)
        """
        if self._current_halo:
            text = f"{label}: {detail}" if detail else label
            self._current_halo.stop_and_persist(symbol=self.success_icon, text=text)
            self._current_halo = None

    def failure(self, label: str, detail: str) -> None:
        """Stop the spinner with failure icon and message.

        Args:
            label (str): Stage description
            detail (str): Failure reason
        """
        if self._current_halo:
            self._current_halo.stop_and_persist(symbol=self.failure_icon, text=f"{label}: {detail}")
            self._current_halo = None


class CallbackProgressReporter:
    """TUI progress reporter using callbacks.

    Implements the ProgressReporter protocol by invoking user-supplied
    callbacks. Used by the Textual TUI to stream progress updates to
    the LaunchScreen's step list.
    """

    def __init__(
        self,
        progress_callback: Callable[[str, bool, str], None],
        start_callback: Optional[Callable[[str], None]] = None,
    ):
        """Initialize the callback progress reporter.

        Args:
            progress_callback (Callable): Called as (label, ok, detail) after
                each stage completes
            start_callback (Callable, optional): Called as (label) when a stage
                starts. Defaults to None.
        """
        self.progress_callback = progress_callback
        self.start_callback = start_callback

    def start(self, label: str) -> None:
        """Invoke start_callback if provided.

        Args:
            label (str): Stage description
        """
        if self.start_callback:
            self.start_callback(label)

    def success(self, label: str, detail: str) -> None:
        """Invoke progress_callback with success status.

        Args:
            label (str): Stage description
            detail (str): Success detail
        """
        self.progress_callback(label, True, detail)

    def failure(self, label: str, detail: str) -> None:
        """Invoke progress_callback with failure status.

        Args:
            label (str): Stage description
            detail (str): Failure reason
        """
        self.progress_callback(label, False, detail)
