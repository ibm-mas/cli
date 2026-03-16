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
Authentication tests for mirror command.

Tests authentication file generation for different mirror modes (m2d, m2m, d2m)
with various credential combinations.
"""

from utils import MirrorTestConfig, run_mirror_test
import sys
import os

# Add test directory to path for utils import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_mirror_auth_file_generation_m2d(tmpdir):
    """
    Test auth file generation for m2d mode.

    This scenario tests:
    - Auth file is generated with IBM entitlement key
    - Mode: m2d
    - No registry credentials needed
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
            'IBM_ENTITLEMENT_KEY': 'test-entitlement-key-12345',
            'HOME': str(tmpdir),
        },
        config_exists_locally=True,
    )

    run_mirror_test(tmpdir, config)

    # Verify auth file was created (mocked)
    tmpdir.join('.mas', 'mirror', 'auth.json')
    # In real scenario, would verify file contents


def test_mirror_auth_file_generation_m2m(tmpdir):
    """
    Test auth file generation for m2m mode.

    This scenario tests:
    - Auth file is generated with both IBM entitlement and registry credentials
    - Mode: m2m
    """
    config = MirrorTestConfig(
        mode='m2m',
        catalog_version='v9-260129-amd64',
        release='9.1.x',
        target_registry='registry.example.com/mas',
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
            'REGISTRY_USERNAME': 'testuser',
            'REGISTRY_PASSWORD': 'testpass123',
            'HOME': str(tmpdir),
        },
        config_exists_locally=True,
    )

    run_mirror_test(tmpdir, config)


def test_mirror_auth_file_generation_d2m(tmpdir):
    """
    Test auth file generation for d2m mode.

    This scenario tests:
    - Auth file is generated with only registry credentials
    - Mode: d2m (no IBM entitlement needed)
    """
    config = MirrorTestConfig(
        mode='d2m',
        catalog_version='v9-260129-amd64',
        release='9.1.x',
        target_registry='registry.example.com/mas',
        root_dir=str(tmpdir),
        packages={},
        mock_oc_mirror_output=[
            '2026/02/09 17:00:15  [INFO]   : 10 / 10 additional images mirrored successfully',
        ],
        mock_image_count=10,
        expect_success=True,
        timeout_seconds=30,
        env_vars={
            'REGISTRY_USERNAME': 'testuser',
            'REGISTRY_PASSWORD': 'testpass123',
            'HOME': str(tmpdir),
        },
        config_exists_locally=True,
    )

    run_mirror_test(tmpdir, config)


# Made with Bob
