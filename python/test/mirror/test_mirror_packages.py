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
Package selection tests for mirror command.

Tests mirroring with different package combinations including all packages,
selective packages, and special handling for DB2.
"""

from utils import MirrorTestConfig, run_mirror_test
import sys
import os

# Add test directory to path for utils import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_mirror_all_packages(tmpdir):
    """
    Test mirroring with all available packages.

    This scenario tests:
    - All packages enabled (sls, core, assist, iot, manage, monitor, optimizer, predict, visualinspection)
    - Mode: m2m
    - Should generate config with all package images
    """
    config = MirrorTestConfig(
        mode='m2m',
        catalog_version='v9-260129-amd64',
        release='9.1.x',
        target_registry='registry.example.com/mas',
        root_dir=str(tmpdir),
        packages={
            'sls': True,
            'core': True,
            'assist': True,
            'iot': True,
            'manage': True,
            'monitor': True,
            'optimizer': True,
            'predict': True,
            'visualinspection': True,
        },
        mock_oc_mirror_output=[
            '2026/02/09 17:00:00  [INFO]   : Hello, welcome to oc-mirror',
            '2026/02/09 17:00:15  [INFO]   : 50 / 50 additional images mirrored successfully',
        ],
        mock_image_count=50,
        expect_success=True,
        timeout_seconds=30,
        env_vars={
            'IBM_ENTITLEMENT_KEY': 'test-entitlement-key',
            'REGISTRY_USERNAME': 'testuser',
            'REGISTRY_PASSWORD': 'testpass',
            'HOME': str(tmpdir),
        },
        config_exists_locally=True,
    )

    run_mirror_test(tmpdir, config)


def test_mirror_selective_packages(tmpdir):
    """
    Test mirroring with selective packages.

    This scenario tests:
    - Only specific packages enabled (sls, manage, monitor)
    - Mode: m2m
    - Should generate config with only selected package images
    """
    config = MirrorTestConfig(
        mode='m2m',
        catalog_version='v9-260129-amd64',
        release='9.1.x',
        target_registry='registry.example.com/mas',
        root_dir=str(tmpdir),
        packages={
            'sls': True,
            'manage': True,
            'monitor': True,
        },
        mock_oc_mirror_output=[
            '2026/02/09 17:00:00  [INFO]   : Hello, welcome to oc-mirror',
            '2026/02/09 17:00:15  [INFO]   : 20 / 20 additional images mirrored successfully',
        ],
        mock_image_count=20,
        expect_success=True,
        timeout_seconds=30,
        env_vars={
            'IBM_ENTITLEMENT_KEY': 'test-entitlement-key',
            'REGISTRY_USERNAME': 'testuser',
            'REGISTRY_PASSWORD': 'testpass',
            'HOME': str(tmpdir),
        },
        config_exists_locally=True,
    )

    run_mirror_test(tmpdir, config)


def test_mirror_db2_package_special_handling(tmpdir):
    """
    Test DB2 package special version handling.

    This scenario tests:
    - DB2 packages (db2u-s11 and db2u-s12) use different version format
    - Should handle DB2 version correctly
    """
    config = MirrorTestConfig(
        mode='m2m',
        catalog_version='v9-260129-amd64',
        release='9.1.x',
        target_registry='registry.example.com/mas',
        root_dir=str(tmpdir),
        packages={
            'db2u-s11': True,
            'db2u-s12': True,
        },
        mock_oc_mirror_output=[
            '2026/02/09 17:00:00  [INFO]   : Hello, welcome to oc-mirror',
            '2026/02/09 17:00:15  [INFO]   : 5 / 5 additional images mirrored successfully',
        ],
        mock_image_count=5,
        expect_success=True,
        timeout_seconds=30,
        env_vars={
            'IBM_ENTITLEMENT_KEY': 'test-entitlement-key',
            'REGISTRY_USERNAME': 'testuser',
            'REGISTRY_PASSWORD': 'testpass',
            'HOME': str(tmpdir),
        },
        config_exists_locally=True,
    )

    run_mirror_test(tmpdir, config)


# Made with Bob
