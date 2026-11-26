# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Bare-app pilot harness for driving a single TUI screen with a live pilot.

A pilot test mounts exactly one workflow screen (constructed with a stubbed
or scenario-built MAS app) inside a minimal Textual App, drives it with a
pilot (clicks, keystrokes, input values), and asserts on what the screen
posted and wrote rather than on shell navigation:

* posted workflow messages are recorded on ``app.posted`` as tuples like
  ``("step_completed", 3)`` — the shell-level tests in tests/unit/tui own
  the wiring between these messages and step advancement
* params written via ``mas_app.setParam`` land in the real app instance the
  test supplied, so scenario apps can be asserted on directly
* ``start_dynamic_loaders()`` is invoked after mount (as the real shell
  does) so auto-running screens (auto-run, launch) start their workers

The app loads the same stylesheet as the production shell so layout-related
assertions see production CSS.
"""

import asyncio
import time
from typing import Any, Awaitable, Callable

from textual.app import App

from mas.cli.tui.shell import TextualShell


class ScreenPilotApp(App):
    """Minimal app hosting one workflow screen and recording its messages.

    Attributes:
        posted: List of (message_name, payload) tuples for every workflow
            message the mounted screen posts.
        return_value: Set by App.exit (e.g. the screen's abort button).
    """

    # Same stylesheet as the production shell so pilot tests render with
    # production CSS.
    CSS_PATH = TextualShell.CSS_PATH

    def __init__(self, screen: Any) -> None:
        """Initialise the pilot app around a single screen widget.

        Args:
            screen: The workflow screen widget to mount.
        """
        super().__init__()
        self._screen = screen
        self.posted: list = []

    def compose(self):
        """Mount the screen under test as the only content."""
        yield self._screen

    def on_step_completed(self, event) -> None:
        """Record a StepCompleted message posted by the screen."""
        self.posted.append(("step_completed", event.step_index))

    def on_action_complete(self, event) -> None:
        """Record an ActionComplete message posted by the screen."""
        self.posted.append(("action_complete", event.step_index))


async def wait_for(predicate: Callable[[], bool], timeout: float = 5.0) -> bool:
    """Await a predicate, giving worker threads time to make it true.

    Args:
        predicate (Callable): Zero-arg callable evaluated on the event loop.
        timeout (float): Maximum seconds to wait.

    Returns:
        bool: Final value of the predicate (True when satisfied in time).
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        await asyncio.sleep(0.05)
    return predicate()


async def wait_for_widget(pilot, selector: str, timeout: float = 5.0) -> bool:
    """Wait for a widget matching the selector to be mounted and visible.

    Unlike ``wait_for``, this pumps ``pilot.pause()`` rather than plain
    sleeping: lazily-mounted panels (the shell mounts step panels via
    ``call_after_refresh``) only appear once a refresh cycle runs, and
    plain ``asyncio.sleep`` does not drive Textual's refresh.

    Args:
        pilot: The active Textual pilot.
        selector (str): Selector to wait for.
        timeout (float): Maximum seconds to wait.

    Returns:
        bool: True when the selector matches at least one widget.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if pilot.app.query(selector):
            return True
        await pilot.pause()
    return bool(pilot.app.query(selector))


async def click_button(pilot, selector: str) -> bool:
    """Click a button via the pilot, then wait out its press animation.

    Textual's Button ignores a Click while its ``-active`` animation class
    is present, so a second pilot click on the same button fired too soon
    after the first is swallowed (humans cannot click within the animation
    window; pilots can). Waiting for the class to clear makes repeated
    clicks on the same button reliable.

    The button is resolved before the click and the animation wait stops
    early if the click's action unmounts it (e.g. an exit that tears down
    the panel the button lives on).

    Args:
        pilot: The active Textual pilot.
        selector (str): Selector for the button to click.

    Returns:
        bool: The pilot.click return value (whether the click landed on
            the selected widget).
    """
    from textual.widgets import Button

    button = pilot.app.query_one(selector, Button)

    def _button_idle() -> bool:
        try:
            button.screen  # noqa: B018 — raises when the button is unmounted
        except Exception:
            return True
        return not button.has_class("-active")

    await wait_for(_button_idle)
    landed = await pilot.click(selector)
    await wait_for(_button_idle)
    return landed


def run_screen_pilot(
    screen: Any,
    drive: Callable[[Any, ScreenPilotApp], Awaitable[None]],
    size: tuple = (100, 40),
) -> ScreenPilotApp:
    """Mount a screen in the bare pilot app, drive it, and return the app.

    Follows the repository's asyncio.run-inside-sync-test pattern (no
    pytest-asyncio dependency).

    Args:
        screen: The workflow screen widget under test, already constructed
            with its (stubbed or scenario) MAS app.
        drive (Callable): Async ``drive(pilot, app)`` performing the
            interactions; assertions on app state can also be made by the
            caller afterwards via the returned app.
        size (tuple): Terminal size for the headless run.

    Returns:
        ScreenPilotApp: The app instance, with ``posted`` populated and the
            screen still attached for post-drive widget assertions.
    """
    app = ScreenPilotApp(screen)

    async def _run() -> None:
        async with app.run_test(size=size) as pilot:
            await pilot.pause()
            # Mirrors TextualShell._activate_step(): auto-running screens
            # start their workers when the step becomes active.
            starter = getattr(screen, "start_dynamic_loaders", None)
            if callable(starter):
                starter()
            await pilot.pause()
            await drive(pilot, app)

    asyncio.run(_run())
    return app
