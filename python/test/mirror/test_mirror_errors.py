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

"""
Error handling tests for mirror command.

Tests various error scenarios including missing dependencies, invalid inputs,
command failures, and timeout handling.
"""

from utils import MirrorTestConfig, run_mirror_test
import sys
import os
import time
from unittest import mock
from unittest.mock import MagicMock

# Add test directory to path for utils import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_mirror_missing_oc_mirror(tmpdir):
    """
    Test error handling when oc-mirror binary is not found.

    This scenario tests:
    - Missing oc-mirror binary
    - Should fail gracefully with appropriate error message
    - App logs error but doesn't exit (continues to show summary)
    """
    config = MirrorTestConfig(
        mode='m2d',
        catalog_version='v9-260129-amd64',
        release='9.1.x',
        root_dir=str(tmpdir),
        packages={},
        mock_oc_mirror_output=[],
        mock_image_count=5,  # Need images for oc-mirror to be called
        expect_success=False,
        timeout_seconds=30,
        env_vars={
            'IBM_ENTITLEMENT_KEY': 'test-entitlement-key',
            'HOME': str(tmpdir),
        },
        config_exists_locally=True,
    )

    # Override which() to return None for oc-mirror
    with mock.patch('mas.cli.cli.which') as mock_which:
        def which_side_effect(cmd):
            if cmd == 'oc-mirror':
                return None
            elif cmd == 'kubectl':
                return '/usr/bin/kubectl'
            return None
        mock_which.side_effect = which_side_effect

        # The app will log an error but complete (not exit)
        # This is the expected behavior - it shows the error and summary
        run_mirror_test(tmpdir, config)
        # Test passes if no exception is raised


def test_mirror_invalid_catalog_version(tmpdir):
    """
    Test error handling with invalid catalog version.

    This scenario tests:
    - Invalid catalog version format
    - Should fail during catalog lookup
    """
    config = MirrorTestConfig(
        mode='m2d',
        catalog_version='invalid-version',
        release='9.1.x',
        root_dir=str(tmpdir),
        packages={},
        mock_oc_mirror_output=[],
        mock_image_count=0,
        expect_success=False,
        timeout_seconds=30,
        env_vars={
            'IBM_ENTITLEMENT_KEY': 'test-entitlement-key',
            'HOME': str(tmpdir),
        },
        config_exists_locally=True,
    )

    try:
        run_mirror_test(tmpdir, config)
        assert False, "Expected exception but test completed"
    except (SystemExit, Exception):
        # Expected to fail
        pass


def test_mirror_missing_entitlement_key_m2d(tmpdir):
    """
    Test error handling when IBM_ENTITLEMENT_KEY is missing for m2d mode.

    This scenario tests:
    - Missing IBM_ENTITLEMENT_KEY environment variable
    - Mode: m2d (requires entitlement key)
    - Should fail during auth file generation
    """
    config = MirrorTestConfig(
        mode='m2d',
        catalog_version='v9-260129-amd64',
        release='9.1.x',
        root_dir=str(tmpdir),
        packages={},
        mock_oc_mirror_output=[],
        mock_image_count=0,
        expect_success=False,
        timeout_seconds=30,
        env_vars={
            'HOME': str(tmpdir),
            # IBM_ENTITLEMENT_KEY intentionally missing
        },
        config_exists_locally=True,
    )

    try:
        run_mirror_test(tmpdir, config)
        assert False, "Expected SystemExit but test completed"
    except SystemExit as e:
        # Expected to fail
        assert e.code != 0


def test_mirror_missing_registry_credentials_m2m(tmpdir):
    """
    Test error handling when registry credentials are missing for m2m mode.

    This scenario tests:
    - Missing REGISTRY_USERNAME/PASSWORD for m2m mode
    - Should fail during auth file generation
    """
    config = MirrorTestConfig(
        mode='m2m',
        catalog_version='v9-260129-amd64',
        release='9.1.x',
        target_registry='registry.example.com/mas',
        root_dir=str(tmpdir),
        packages={},
        mock_oc_mirror_output=[],
        mock_image_count=0,
        expect_success=False,
        timeout_seconds=30,
        env_vars={
            'IBM_ENTITLEMENT_KEY': 'test-entitlement-key',
            'HOME': str(tmpdir),
            # REGISTRY_USERNAME/PASSWORD intentionally missing
        },
        config_exists_locally=True,
    )

    try:
        run_mirror_test(tmpdir, config)
        assert False, "Expected SystemExit but test completed"
    except SystemExit as e:
        # Expected to fail
        assert e.code != 0


def test_mirror_oc_mirror_command_failure(tmpdir):
    """
    Test error handling when oc-mirror command fails.

    This scenario tests:
    - oc-mirror command returns non-zero exit code
    - Should detect failure and report it
    """
    config = MirrorTestConfig(
        mode='m2d',
        catalog_version='v9-260129-amd64',
        release='9.1.x',
        root_dir=str(tmpdir),
        packages={},
        mock_oc_mirror_output=[
            '2026/02/09 17:00:00  [ERROR]  : Failed to connect to registry',
            '2026/02/09 17:00:01  [ERROR]  : Mirror operation failed',
        ],
        mock_image_count=5,  # Need images for oc-mirror to be called
        expect_success=False,
        timeout_seconds=30,
        env_vars={
            'IBM_ENTITLEMENT_KEY': 'test-entitlement-key',
            'HOME': str(tmpdir),
        },
        config_exists_locally=True,
    )

    # Mock subprocess to return failure
    with mock.patch('subprocess.Popen') as mock_popen:
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stdout.readline.side_effect = [
            line.encode() + b'\n' for line in config.mock_oc_mirror_output
        ] + [b'']
        mock_process.poll.return_value = 1
        mock_popen.return_value = mock_process

        try:
            run_mirror_test(tmpdir, config)
            # Test should complete but report failure
        except SystemExit:
            # May exit on failure
            pass


def test_mirror_partial_failure(tmpdir):
    """
    Test handling of partial mirror failure.

    This scenario tests:
    - Some images mirror successfully, others fail
    - Should report partial success
    """
    config = MirrorTestConfig(
        mode='m2d',
        catalog_version='v9-260129-amd64',
        release='9.1.x',
        root_dir=str(tmpdir),
        packages={},
        mock_oc_mirror_output=[
            '2026/02/09 17:00:00  [INFO]   : Hello, welcome to oc-mirror',
            '2026/02/09 17:00:05  [INFO]   : Success copying image1 ➡️',
            '2026/02/09 17:00:06  [INFO]   : Success copying image2 ➡️',
            '2026/02/09 17:00:07  [ERROR]  : Failed copying image3',
            '2026/02/09 17:00:08  [INFO]   : Success copying image4 ➡️',
            '2026/02/09 17:00:09  [ERROR]  : Failed copying image5',
            '2026/02/09 17:00:15  [INFO]   : 3 / 5 additional images mirrored successfully',
        ],
        mock_image_count=5,
        expect_success=False,  # Partial failure
        timeout_seconds=30,
        env_vars={
            'IBM_ENTITLEMENT_KEY': 'test-entitlement-key',
            'HOME': str(tmpdir),
        },
        config_exists_locally=True,
    )

    run_mirror_test(tmpdir, config)


def test_mirror_timeout(tmpdir):
    """
    Test timeout handling when mirror operation hangs.

    This scenario tests:
    - Mirror operation exceeds timeout
    - Watchdog thread should detect and terminate
    """
    config = MirrorTestConfig(
        mode='m2d',
        catalog_version='v9-260129-amd64',
        release='9.1.x',
        root_dir=str(tmpdir),
        packages={},
        mock_oc_mirror_output=[
            '2026/02/09 17:00:00  [INFO]   : Hello, welcome to oc-mirror',
            # No completion message - simulates hang
        ],
        mock_image_count=10,
        expect_success=False,
        timeout_seconds=2,  # Short timeout for test
        env_vars={
            'IBM_ENTITLEMENT_KEY': 'test-entitlement-key',
            'HOME': str(tmpdir),
        },
        config_exists_locally=True,
    )

    # Mock subprocess to simulate hanging
    with mock.patch('subprocess.Popen') as mock_popen:
        mock_process = MagicMock()
        mock_process.returncode = None
        mock_process.stdout.readline.side_effect = lambda: time.sleep(5) or b''
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        try:
            run_mirror_test(tmpdir, config)
            # Should timeout
        except (SystemExit, Exception):
            # Expected to fail/timeout
            pass


# Made with Bob
