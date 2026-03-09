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
Basic mirror operation tests.

Tests the fundamental mirror operations across different modes (m2d, m2m, d2m).
"""

from utils import MirrorTestConfig, run_mirror_test
import sys
import os

# Add test directory to path for utils import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_mirror_m2d_catalog_only(tmpdir):
    """
    Test mirror-to-disk (m2d) mode with catalog only.

    This is the simplest mirror scenario:
    - Mode: m2d (mirror to disk)
    - Only mirrors the operator catalog
    - No additional packages
    - Uses local config file (no download)
    - Simulates successful mirroring of 10 images
    """
    config = MirrorTestConfig(
        mode='m2d',
        catalog_version='v9-260129-amd64',
        release='9.1.x',
        root_dir=str(tmpdir),
        packages={},  # No packages, catalog only
        mock_oc_mirror_output=[
            '2026/02/09 17:00:00  [INFO]   : Hello, welcome to oc-mirror',
            '2026/02/09 17:00:01  [INFO]   : setting up the environment for you...',
            '2026/02/09 17:00:05  [INFO]   : Success copying image1 ➡️',
            '2026/02/09 17:00:06  [INFO]   : Success copying image2 ➡️',
            '2026/02/09 17:00:07  [INFO]   : Success copying image3 ➡️',
            '2026/02/09 17:00:08  [INFO]   : Success copying image4 ➡️',
            '2026/02/09 17:00:09  [INFO]   : Success copying image5 ➡️',
            '2026/02/09 17:00:10  [INFO]   : Success copying image6 ➡️',
            '2026/02/09 17:00:11  [INFO]   : Success copying image7 ➡️',
            '2026/02/09 17:00:12  [INFO]   : Success copying image8 ➡️',
            '2026/02/09 17:00:13  [INFO]   : Success copying image9 ➡️',
            '2026/02/09 17:00:14  [INFO]   : Success copying image10 ➡️',
            '2026/02/09 17:00:15  [INFO]   : 10 / 10 additional images mirrored successfully',
        ],
        mock_image_count=10,
        expect_success=True,
        timeout_seconds=30,
        env_vars={
            'IBM_ENTITLEMENT_KEY': 'test-entitlement-key',
            'HOME': str(tmpdir),
        },
        config_exists_locally=True,
    )

    run_mirror_test(tmpdir, config)


def test_mirror_m2m_with_packages(tmpdir):
    """
    Test mirror-to-mirror (m2m) mode with catalog and packages.

    This scenario tests:
    - Mode: m2m (mirror to mirror)
    - Mirrors catalog + SLS + Core packages
    - Requires target registry
    - Requires authentication (registry + IBM entitlement)
    - Simulates successful mirroring
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
        },
        mock_oc_mirror_output=[
            '2026/02/09 17:00:00  [INFO]   : Hello, welcome to oc-mirror',
            '2026/02/09 17:00:15  [INFO]   : 10 / 10 additional images mirrored successfully',
        ],
        mock_image_count=10,
        expect_success=True,
        timeout_seconds=30,
        env_vars={
            'IBM_ENTITLEMENT_KEY': 'test-entitlement-key',
            'REGISTRY_USERNAME': 'test-user',
            'REGISTRY_PASSWORD': 'test-password',
            'HOME': str(tmpdir),
        },
        config_exists_locally=True,
    )

    run_mirror_test(tmpdir, config)


def test_mirror_d2m_resume(tmpdir):
    """
    Test disk-to-mirror (d2m) mode for resuming from disk.

    This scenario tests:
    - Mode: d2m (disk to mirror)
    - Resumes mirroring from previously saved disk content
    - Requires target registry
    - Requires registry authentication only (no IBM entitlement needed)
    """
    config = MirrorTestConfig(
        mode='d2m',
        catalog_version='v9-260129-amd64',
        release='9.1.x',
        target_registry='registry.example.com/mas',
        root_dir=str(tmpdir),
        packages={},  # Catalog only
        mock_oc_mirror_output=[
            '2026/02/09 17:00:00  [INFO]   : Hello, welcome to oc-mirror',
            '2026/02/09 17:00:15  [INFO]   : 10 / 10 additional images mirrored successfully',
        ],
        mock_image_count=10,
        expect_success=True,
        timeout_seconds=30,
        env_vars={
            'REGISTRY_USERNAME': 'test-user',
            'REGISTRY_PASSWORD': 'test-password',
            'HOME': str(tmpdir),
        },
        config_exists_locally=True,
    )

    run_mirror_test(tmpdir, config)


def test_mirror_with_custom_authfile(tmpdir):
    """
    Test mirror with custom authentication file.

    This scenario tests:
    - Using a pre-existing auth file instead of generating one
    - Mode: m2d
    - Catalog only
    """
    # Create a mock auth file
    auth_file_path = str(tmpdir.join('custom-auth.json'))
    tmpdir.join('custom-auth.json').write('{"auths": {}}')

    config = MirrorTestConfig(
        mode='m2d',
        catalog_version='v9-260129-amd64',
        release='9.1.x',
        root_dir=str(tmpdir),
        authfile=auth_file_path,
        packages={},
        mock_oc_mirror_output=[
            '2026/02/09 17:00:15  [INFO]   : 10 / 10 additional images mirrored successfully',
        ],
        mock_image_count=10,
        expect_success=True,
        timeout_seconds=30,
        env_vars={
            'HOME': str(tmpdir),
        },
        config_exists_locally=True,
    )

    run_mirror_test(tmpdir, config)


def test_mirror_with_config_download(tmpdir):
    """
    Test mirror with config file download from GitHub.

    This scenario tests:
    - Config file doesn't exist locally
    - Should download from GitHub
    - Mode: m2d
    - Catalog only
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


# Made with Bob
