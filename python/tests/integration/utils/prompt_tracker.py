#!/usr/bin/env python
# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

import re
from typing import Dict, Callable


class PromptTracker:
    """
    Utility class to track which prompts were matched during tests.

    By default every registered pattern must be matched exactly once.  Wrap the
    handler in a tuple ``(handler, expected_count)`` to declare a different
    expected hit count, e.g. ``(lambda msg: "y", 2)`` for a prompt that fires
    twice.  Use ``None`` as the count to skip the upper-bound check entirely.
    When only handler is provided the expected match count defaults to 1.
    """

    def __init__(self, prompt_handlers: Dict[str, Callable[[str], str]]):
        """
        Initialize the prompt tracker.

        Args:
            prompt_handlers: Dictionary mapping regex patterns to handler functions
                or ``(handler, expected_count)`` tuples.  ``expected_count`` may be
                an integer (exact match) or ``None`` (at-least-once, no upper bound).
        """
        # Normalise every entry to (callable, expected_count)
        self.prompt_handlers: Dict[str, tuple] = {}
        for pattern, value in prompt_handlers.items():
            if isinstance(value, tuple):
                handler, expected_count = value
            else:
                handler, expected_count = value, 1
            self.prompt_handlers[pattern] = (handler, expected_count)
        self.match_counts = {pattern: 0 for pattern in self.prompt_handlers.keys()}

    def handle_prompt(self, *args, **kwargs) -> str:
        """
        Handle a prompt by matching it against registered patterns.

        Args:
            *args: Positional arguments (first arg is typically the message/HTML object)
            **kwargs: Keyword arguments containing 'message' and other prompt parameters.

        Returns:
            The response string from the matched handler.

        Raises:
            AssertionError: If no pattern matches the prompt.
        """
        # Extract message from either positional args or kwargs
        if args:
            message = str(args[0])
        elif "message" in kwargs:
            message = str(kwargs["message"])
        else:
            raise AssertionError(f"No message found in prompt call. Args: {args}, Kwargs: {kwargs}")

        # Try to match against all registered patterns
        for pattern, (handler, _) in self.prompt_handlers.items():
            if re.match(pattern, message):
                self.match_counts[pattern] += 1
                return handler(message)

        # No pattern matched - fail the test with debug info
        raise AssertionError(f"Unmatched prompt in test: {message}\nFull args: {args}, kwargs: {kwargs}")

    def verify_all_prompts_matched(self, allow_unmatched: bool = False):
        """
        Verify that all expected prompts were matched exactly once.

        Args:
            allow_unmatched: If True, don't fail if some prompts were never matched
                           (useful for error scenarios where execution stops early)

        Raises:
            AssertionError: If any prompt was matched != 1 times (or 0 times if allow_unmatched=False).
        """
        errors = []
        for pattern, count in self.match_counts.items():
            _, expected_count = self.prompt_handlers[pattern]
            if count == 0:
                if not allow_unmatched:
                    errors.append(f"Prompt pattern never matched: {pattern}")
            elif expected_count is None:
                pass      # no upper-bound, matches indefinitely.
            elif count != expected_count:
                errors.append(f"Prompt pattern matched {count} times (expected {expected_count}): {pattern}")

        if len(errors) > 0:
            error_message = " | ".join(errors)
            raise AssertionError(error_message)

    def get_match_counts(self) -> Dict[str, int]:
        """
        Get the current match counts for all patterns.

        Returns:
            Dictionary mapping patterns to their match counts.
        """
        return self.match_counts.copy()


def create_prompt_handler(prompt_handlers: Dict[str, Callable[[str], str]]) -> tuple:
    """
    Create a prompt tracker and return both the tracker and handler function.

    Args:
        prompt_handlers: Dictionary mapping regex patterns to handler functions.

    Returns:
        Tuple of (PromptTracker instance, handler function for use with mock.side_effect)
    """
    tracker = PromptTracker(prompt_handlers)
    return tracker, tracker.handle_prompt
