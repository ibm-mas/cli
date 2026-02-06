#!/usr/bin/env python
# *****************************************************************************
# Copyright (c) 2024, 2025 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

import pytest
from utils.prompt_tracker import create_prompt_handler


def test_prompt_tracker_single_match():
    """Test that a prompt matched exactly once passes verification."""
    handlers = {
        '.*test.*': lambda msg: 'response'
    }
    tracker, handler = create_prompt_handler(handlers)

    result = handler(message='test message')
    assert result == 'response'

    # Should pass verification
    tracker.verify_all_prompts_matched()


def test_prompt_tracker_never_matched():
    """Test that a prompt never matched fails verification."""
    handlers = {
        '.*test.*': lambda msg: 'response',
        '.*unused.*': lambda msg: 'unused'
    }
    tracker, handler = create_prompt_handler(handlers)

    handler(message='test message')

    # Should fail verification
    with pytest.raises(AssertionError, match='Prompt pattern never matched: .*unused.*'):
        tracker.verify_all_prompts_matched()


def test_prompt_tracker_multiple_matches():
    """Test that a prompt matched multiple times fails verification."""
    handlers = {
        '.*test.*': lambda msg: 'response'
    }
    tracker, handler = create_prompt_handler(handlers)

    handler(message='test 1')
    handler(message='test 2')

    # Should fail verification
    with pytest.raises(AssertionError, match='Prompt pattern matched 2 times'):
        tracker.verify_all_prompts_matched()


def test_prompt_tracker_unmatched_prompt():
    """Test that an unmatched prompt fails immediately."""
    handlers = {
        '.*test.*': lambda msg: 'response'
    }
    tracker, handler = create_prompt_handler(handlers)

    # Should fail immediately
    with pytest.raises(AssertionError, match='Unmatched prompt in test: unmatched'):
        handler(message='unmatched')


def test_prompt_tracker_get_match_counts():
    """Test that match counts are tracked correctly."""
    handlers = {
        '.*test1.*': lambda msg: 'response1',
        '.*test2.*': lambda msg: 'response2'
    }
    tracker, handler = create_prompt_handler(handlers)

    handler(message='test1')
    handler(message='test2')

    counts = tracker.get_match_counts()
    assert counts['.*test1.*'] == 1
    assert counts['.*test2.*'] == 1

# Made with Bob
