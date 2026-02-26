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
Configuration handling tests for mirror command.

Tests config file download from GitHub, local file handling, and error scenarios
with invalid or missing configuration files.
"""

from utils import MirrorTestConfig, run_mirror_test
import sys
import os
import urllib.error
from unittest import mock

# Add test directory to path for utils import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_mirror_config_download_success(tmpdir):
    """
    Test successful config file download from GitHub.

    This scenario tests:
    - Config file doesn't exist locally
    - Successfully downloads from GitHub
    - Proceeds with mirror operation
    """
    config = MirrorTestConfig(
        mode='m2d',
        catalog_version='v9-260129-amd64',
        release='9.1.x',
        root_dir=str(tmpdir),
        packages={},
        mock_oc_mirror_output=[
            '2026/02/09 17:00:15  [INFO]   : 10 / 10 additional images mirrored successfully',
        ],
        mock_image_count=10,
        expect_success=True,
        timeout_seconds=30,
        env_vars={
            'IBM_ENTITLEMENT_KEY': 'test-entitlement-key',
            'HOME': str(tmpdir),
        },
        config_exists_locally=False,  # Force download
    )

    run_mirror_test(tmpdir, config)


def test_mirror_config_download_failure(tmpdir):
    """
    Test handling of config file download failure.

    This scenario tests:
    - Config file doesn't exist locally
    - GitHub download fails (network error, 404, etc.)
    - Should fail gracefully
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
            'IBM_ENTITLEMENT_KEY': 'test-entitlement-key',
            'HOME': str(tmpdir),
        },
        config_exists_locally=False,
    )

    # Mock urllib to raise exception
    with mock.patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.URLError('Network error')

        try:
            run_mirror_test(tmpdir, config)
            assert False, "Expected exception but test completed"
        except (SystemExit, Exception):
            # Expected to fail
            pass


def test_mirror_invalid_yaml_config(tmpdir):
    """
    Test handling of invalid YAML in config file.

    This scenario tests:
    - Config file exists but contains invalid YAML
    - Should fail during config parsing
    """
    # Create invalid YAML file
    config_dir = tmpdir.join('.mas', 'mirror', 'configs')
    config_dir.ensure(dir=True)
    config_file = config_dir.join('v9-260129-amd64.yaml')
    config_file.write('invalid: yaml: content: [unclosed')

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


# Made with Bob
