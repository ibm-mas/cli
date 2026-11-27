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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_mirror_all_packages(tmpdir):
    """
    Test mirroring with all available packages.

    This scenario tests:
    - All packages enabled (sls, core, assist, iot, manage, monitor, optimizer, predict, visualinspection)
    - Mode: m2m
    - Should generate config with all package images
    """
    config = MirrorTestConfig(
        mode="m2m",
        catalog_version="v9-260129-amd64",
        release="9.1.x",
        target_registry="registry.example.com/mas",
        root_dir=str(tmpdir),
        packages={
            "sls": True,
            "core": True,
            "assist": True,
            "iot": True,
            "manage": True,
            "monitor": True,
            "optimizer": True,
            "predict": True,
            "visualinspection": True,
        },
        mock_oc_mirror_output=[
            "2026/02/09 17:00:00  [INFO]   : Hello, welcome to oc-mirror",
            "2026/02/09 17:00:15  [INFO]   : 50 / 50 additional images mirrored successfully",
        ],
        mock_image_count=50,
        expect_success=True,
        timeout_seconds=30,
        env_vars={
            "IBM_ENTITLEMENT_KEY": "test-entitlement-key",
            "REGISTRY_USERNAME": "testuser",
            "REGISTRY_PASSWORD": "testpass",
            "HOME": str(tmpdir),
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
        mode="m2m",
        catalog_version="v9-260129-amd64",
        release="9.1.x",
        target_registry="registry.example.com/mas",
        root_dir=str(tmpdir),
        packages={
            "sls": True,
            "manage": True,
            "monitor": True,
        },
        mock_oc_mirror_output=[
            "2026/02/09 17:00:00  [INFO]   : Hello, welcome to oc-mirror",
            "2026/02/09 17:00:15  [INFO]   : 20 / 20 additional images mirrored successfully",
        ],
        mock_image_count=20,
        expect_success=True,
        timeout_seconds=30,
        env_vars={
            "IBM_ENTITLEMENT_KEY": "test-entitlement-key",
            "REGISTRY_USERNAME": "testuser",
            "REGISTRY_PASSWORD": "testpass",
            "HOME": str(tmpdir),
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
        mode="m2m",
        catalog_version="v9-260129-amd64",
        release="9.1.x",
        target_registry="registry.example.com/mas",
        root_dir=str(tmpdir),
        packages={
            "db2u-s11": True,
            "db2u-s12": True,
        },
        mock_oc_mirror_output=[
            "2026/02/09 17:00:00  [INFO]   : Hello, welcome to oc-mirror",
            "2026/02/09 17:00:15  [INFO]   : 5 / 5 additional images mirrored successfully",
        ],
        mock_image_count=5,
        expect_success=True,
        timeout_seconds=30,
        env_vars={
            "IBM_ENTITLEMENT_KEY": "test-entitlement-key",
            "REGISTRY_USERNAME": "testuser",
            "REGISTRY_PASSWORD": "testpass",
            "HOME": str(tmpdir),
        },
        config_exists_locally=True,
    )

    run_mirror_test(tmpdir, config)


def test_mirror_cp4d_platform_packages(tmpdir):
    """
    Test mirroring CP4D Platform packages with multiple package names.

    This scenario tests:
    - CP4D Platform package (cp4d-platform) which includes multiple packages:
      ibm-cp-common-services, ibm-zen, ibm-cp-datacore, ibm-licensing, ibm-ccs,
      ibm-cloud-native-postgresql, ibm-datarefinery, ibm-elasticsearch-operator,
      ibm-opensearch-operator
    - Mode: m2m
    - Should generate config with all CP4D platform package images
    """
    config = MirrorTestConfig(
        mode="m2m",
        catalog_version="v9-260129-amd64",
        release="9.1.x",
        target_registry="registry.example.com/mas",
        root_dir=str(tmpdir),
        packages={
            "cp4d-platform": True,
        },
        mock_oc_mirror_output=[
            "2026/02/09 17:00:00  [INFO]   : Hello, welcome to oc-mirror",
            "2026/02/09 17:00:15  [INFO]   : 30 / 30 additional images mirrored successfully",
        ],
        mock_image_count=30,
        expect_success=True,
        timeout_seconds=30,
        env_vars={
            "IBM_ENTITLEMENT_KEY": "test-entitlement-key",
            "REGISTRY_USERNAME": "testuser",
            "REGISTRY_PASSWORD": "testpass",
            "HOME": str(tmpdir),
        },
        config_exists_locally=True,
    )

    run_mirror_test(tmpdir, config)


def test_mirror_cp4d_wsl_packages(tmpdir):
    """
    Test mirroring CP4D WSL packages with multiple package names.

    This scenario tests:
    - CP4D WSL package (cp4d-wsl) which includes: ibm-wsl, ibm-wsl-runtimes
    - Mode: m2m
    - Should generate config with all CP4D WSL package images
    """
    config = MirrorTestConfig(
        mode="m2m",
        catalog_version="v9-260129-amd64",
        release="9.1.x",
        target_registry="registry.example.com/mas",
        root_dir=str(tmpdir),
        packages={
            "cp4d-wsl": True,
        },
        mock_oc_mirror_output=[
            "2026/02/09 17:00:00  [INFO]   : Hello, welcome to oc-mirror",
            "2026/02/09 17:00:15  [INFO]   : 10 / 10 additional images mirrored successfully",
        ],
        mock_image_count=10,
        expect_success=True,
        timeout_seconds=30,
        env_vars={
            "IBM_ENTITLEMENT_KEY": "test-entitlement-key",
            "REGISTRY_USERNAME": "testuser",
            "REGISTRY_PASSWORD": "testpass",
            "HOME": str(tmpdir),
        },
        config_exists_locally=True,
    )

    run_mirror_test(tmpdir, config)


def test_mirror_all_cp4d_packages(tmpdir):
    """
    Test mirroring all CP4D packages together.

    This scenario tests:
    - All CP4D packages: cp4d-platform, cp4d-wsl, cp4d-wml, cp4d-spark
    - Mode: m2m
    - Should generate config with all CP4D package images
    """
    config = MirrorTestConfig(
        mode="m2m",
        catalog_version="v9-260129-amd64",
        release="9.1.x",
        target_registry="registry.example.com/mas",
        root_dir=str(tmpdir),
        packages={
            "cp4d-platform": True,
            "cp4d-wsl": True,
            "cp4d-wml": True,
            "cp4d-spark": True,
        },
        mock_oc_mirror_output=[
            "2026/02/09 17:00:00  [INFO]   : Hello, welcome to oc-mirror",
            "2026/02/09 17:00:15  [INFO]   : 60 / 60 additional images mirrored successfully",
        ],
        mock_image_count=60,
        expect_success=True,
        timeout_seconds=30,
        env_vars={
            "IBM_ENTITLEMENT_KEY": "test-entitlement-key",
            "REGISTRY_USERNAME": "testuser",
            "REGISTRY_PASSWORD": "testpass",
            "HOME": str(tmpdir),
        },
        config_exists_locally=True,
    )

    run_mirror_test(tmpdir, config)


def test_mirror_with_all_flag(tmpdir):
    """
    Test mirroring with --all flag to enable all packages.

    This scenario tests:
    - Using --all flag instead of individual package flags
    - Should mirror all available packages
    - Mode: m2m
    """
    config = MirrorTestConfig(
        mode="m2m",
        catalog_version="v9-260129-amd64",
        release="9.1.x",
        target_registry="registry.example.com/mas",
        root_dir=str(tmpdir),
        packages={},  # No individual packages specified
        mock_oc_mirror_output=[
            "2026/02/09 17:00:00  [INFO]   : Hello, welcome to oc-mirror",
            "2026/02/09 17:00:15  [INFO]   : 100 / 100 additional images mirrored successfully",
        ],
        mock_image_count=100,
        expect_success=True,
        timeout_seconds=30,
        env_vars={
            "IBM_ENTITLEMENT_KEY": "test-entitlement-key",
            "REGISTRY_USERNAME": "testuser",
            "REGISTRY_PASSWORD": "testpass",
            "HOME": str(tmpdir),
        },
        config_exists_locally=True,
        # Override argv to use --all flag
        argv=[
            "--catalog",
            "v9-260129-amd64",
            "--release",
            "9.1.x",
            "--mode",
            "m2m",
            "--dir",
            str(tmpdir),
            "--target-registry",
            "registry.example.com/mas",
            "--all",
        ],
    )

    run_mirror_test(tmpdir, config)


def test_mirror_assist_with_couchdb(tmpdir):
    """
    Test mirroring Assist package with CouchDB dependency.

    This scenario tests:
    - Assist package (assist) which includes: ibm-mas-assist, ibm-couchdb
    - Mode: m2m
    - Should generate config with both Assist and CouchDB package images
    - CouchDB version is retrieved from catalog's couchdb_version key
    """
    config = MirrorTestConfig(
        mode="m2m",
        catalog_version="v9-260129-amd64",
        release="9.1.x",
        target_registry="registry.example.com/mas",
        root_dir=str(tmpdir),
        packages={
            "assist": True,
        },
        mock_oc_mirror_output=[
            "2026/02/09 17:00:00  [INFO]   : Hello, welcome to oc-mirror",
            "2026/02/09 17:00:15  [INFO]   : 15 / 15 additional images mirrored successfully",
        ],
        mock_image_count=15,
        expect_success=True,
        timeout_seconds=30,
        env_vars={
            "IBM_ENTITLEMENT_KEY": "test-entitlement-key",
            "REGISTRY_USERNAME": "testuser",
            "REGISTRY_PASSWORD": "testpass",
            "HOME": str(tmpdir),
        },
        config_exists_locally=True,
    )

    run_mirror_test(tmpdir, config)


def test_mirror_all_flag_9_2_excludes_assist(tmpdir):
    """Test mirroring with --all flag on MAS 9.2.x where Assist is removed.

    GIVEN a catalog for release 9.2.x where Assist is not present
    WHEN mirroring is run with --all
    THEN Assist and CouchDB are excluded from mirroring without errors.
    """
    # Catalog data for 9.2.x without assist entry
    catalog_data_9_2 = {
        "sls_version": "3.10.0",
        "tsm_version": "1.5.0",
        "mas_core_version": {"9.2.x": "9.2.0"},
        "mas_assist_version": {"9.1.x": "9.1.0"},  # Only 9.1.x
        "couchdb_version": "1.0.13",
        "mas_iot_version": {"9.2.x": "9.2.0"},
        "mas_manage_version": {"9.2.x": "9.2.0"},
        "mas_monitor_version": {"9.2.x": "9.2.0"},
        "mas_predict_version": {"9.2.x": "9.2.0"},
        "mas_optimizer_version": {"9.2.x": "9.2.0"},
        "mas_visualinspection_version": {"9.2.x": "9.2.0"},
        "mas_facilities_version": {"9.2.x": "9.2.0"},
        "db2u_version": "11.5.9.0",
        "mongo_extras_version_default": "6.0.0",
        "cpd_product_version_default": "5.1.0",
    }

    config = MirrorTestConfig(
        mode="m2m",
        catalog_version="v9-260129-amd64",
        release="9.2.x",
        target_registry="registry.example.com/mas",
        root_dir=str(tmpdir),
        packages={},
        mock_catalog_data=catalog_data_9_2,
        mock_oc_mirror_output=[
            "2026/02/09 17:00:00  [INFO]   : Hello, welcome to oc-mirror",
            "2026/02/09 17:00:15  [INFO]   : 80 / 80 additional images mirrored successfully",
        ],
        mock_image_count=80,
        expect_success=True,
        timeout_seconds=30,
        env_vars={
            "IBM_ENTITLEMENT_KEY": "test-entitlement-key",
            "REGISTRY_USERNAME": "testuser",
            "REGISTRY_PASSWORD": "testpass",
            "HOME": str(tmpdir),
        },
        config_exists_locally=True,
        argv=[
            "--catalog",
            "v9-260129-amd64",
            "--release",
            "9.2.x",
            "--mode",
            "m2m",
            "--dir",
            str(tmpdir),
            "--target-registry",
            "registry.example.com/mas",
            "--all",
        ],
    )

    run_mirror_test(tmpdir, config)
