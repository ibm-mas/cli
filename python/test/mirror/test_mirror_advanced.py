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
Advanced configuration tests for mirror command.

Tests advanced mirror options including TLS verification settings and
custom timeout configurations.
"""

from utils import MirrorTestConfig, run_mirror_test
import sys
import os

# Add test directory to path for utils import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_mirror_with_tls_verify_disabled(tmpdir):
    """
    Test mirror with TLS verification disabled.

    This scenario tests:
    - dest-tls-verify=false flag
    - Should pass flag to oc-mirror command
    """
    config = MirrorTestConfig(
        mode='m2m',
        catalog_version='v9-260129-amd64',
        release='9.1.x',
        target_registry='registry.example.com/mas',
        root_dir=str(tmpdir),
        dest_tls_verify=False,  # Disable TLS verification
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
            'REGISTRY_PASSWORD': 'testpass',
            'HOME': str(tmpdir),
        },
        config_exists_locally=True,
    )

    run_mirror_test(tmpdir, config)


def test_mirror_with_custom_image_timeout(tmpdir):
    """
    Test mirror with custom image timeout.

    This scenario tests:
    - Custom --image-timeout flag
    - Should pass timeout to oc-mirror command
    """
    config = MirrorTestConfig(
        mode='m2d',
        catalog_version='v9-260129-amd64',
        release='9.1.x',
        root_dir=str(tmpdir),
        image_timeout='30m',  # Custom timeout
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
        config_exists_locally=True,
    )

    run_mirror_test(tmpdir, config)


# Made with Bob
