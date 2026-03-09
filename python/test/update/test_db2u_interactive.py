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

from utils import UpdateTestConfig, run_update_test
import sys
import os
import pytest

# Add test directory to path for utils import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.mark.parametrize("resource_kind", ["Db2uCluster", "Db2uInstance"])
def test_db2u_one_namespace(tmpdir, resource_kind):
    """Test interactive update when exactly one namespace contains Db2U resources.

    Expected behavior:
    - Automatically detects single namespace
    - Sets db2_namespace parameter
    - No namespace selection prompt needed
    - Update proceeds successfully
    """

    prompt_handlers = {
        # Proceed with current cluster
        '.*Proceed with this cluster?.*': lambda msg: 'y',
        # Catalog selection
        '.*Select catalog version.*': lambda msg: '1',
        # Final confirmation
        '.*Proceed with these settings.*': lambda msg: 'y',
    }

    config = UpdateTestConfig(
        prompt_handlers=prompt_handlers,
        installed_catalog_id="v9-251231-amd64",
        target_catalog_version="v9-260129-amd64",
        db2u_namespaces=["db2u-system"],  # Single namespace
        db2u_resource_kind=resource_kind,
        mas_instances=[{
            "metadata": {"name": "inst1"},
            "status": {"versions": {"reconciled": "9.1.7"}}
        }],
        timeout_seconds=30
    )

    run_update_test(tmpdir, config)


@pytest.mark.parametrize("resource_kind", ["Db2uCluster", "Db2uInstance"])
def test_db2u_multiple_namespaces(tmpdir, resource_kind):
    """Test interactive update when multiple namespaces contain Db2U resources.

    Expected behavior:
    - Detects resources in multiple namespaces
    - Prompts user to select namespace
    - User selects second namespace (db2u-ns2)
    - Sets db2_namespace parameter to selected namespace
    - Update proceeds successfully
    """

    prompt_handlers = {
        # Proceed with current cluster
        '.*Proceed with this cluster?.*': lambda msg: 'y',
        # Catalog selection
        '.*Select catalog version.*': lambda msg: '1',
        # Namespace selection - user chooses second namespace
        '.*Select namespace.*': lambda msg: '2',
        # Final confirmation
        '.*Proceed with these settings.*': lambda msg: 'y',
    }

    config = UpdateTestConfig(
        prompt_handlers=prompt_handlers,
        installed_catalog_id="v9-251231-amd64",
        target_catalog_version="v9-260129-amd64",
        db2u_namespaces=["db2u-ns1", "db2u-ns2", "db2u-ns3"],  # Multiple namespaces
        db2u_resource_kind=resource_kind,
        mas_instances=[{
            "metadata": {"name": "inst1"},
            "status": {"versions": {"reconciled": "9.1.7"}}
        }],
        timeout_seconds=30
    )

    run_update_test(tmpdir, config)


@pytest.mark.parametrize("resource_kind", ["Db2uCluster", "Db2uInstance"])
def test_db2u_none_found(tmpdir, resource_kind):
    """Test interactive update when no Db2U resources exist.

    Expected behavior:
    - Detects no Db2U resources
    - db2_namespace parameter remains empty
    - No prompts for namespace selection
    - Update continues without error (not a failure condition)
    """

    prompt_handlers = {
        # Proceed with current cluster
        '.*Proceed with this cluster?.*': lambda msg: 'y',
        # Catalog selection
        '.*Select catalog version.*': lambda msg: '1',
        # Final confirmation
        '.*Proceed with these settings.*': lambda msg: 'y',
    }

    config = UpdateTestConfig(
        prompt_handlers=prompt_handlers,
        installed_catalog_id="v9-251231-amd64",
        target_catalog_version="v9-260129-amd64",
        db2u_namespaces=[],  # No Db2U resources
        db2u_resource_kind=resource_kind,
        mas_instances=[{
            "metadata": {"name": "inst1"},
            "status": {"versions": {"reconciled": "9.1.7"}}
        }],
        timeout_seconds=30
    )

    run_update_test(tmpdir, config)


@pytest.mark.parametrize("resource_kind", ["Db2uCluster", "Db2uInstance"])
def test_db2u_major_version_upgrade_accepted(tmpdir, resource_kind):
    """Test interactive update with Db2 major version upgrade - user accepts.

    Expected behavior:
    - Detects Db2 v11 needs upgrade to v12
    - Prompts user to confirm major version upgrade
    - User accepts the upgrade
    - Sets db2_v12_upgrade parameter to true
    - Update proceeds successfully
    """

    prompt_handlers = {
        # Proceed with current cluster
        '.*Proceed with this cluster.*': lambda msg: 'y',
        # Catalog selection
        '.*Select catalog version.*': lambda msg: '1',
        # Db2 version upgrade confirmation - match the exact format
        '.*Confirm update from Db2 11 to 12.*': lambda msg: 'y',
        # Final confirmation
        '.*Proceed with these settings.*': lambda msg: 'y',
    }

    config = UpdateTestConfig(
        prompt_handlers=prompt_handlers,
        installed_catalog_id="v9-251231-amd64",
        target_catalog_version="v9-260129-amd64",
        db2u_namespaces=["db2u-system"],
        db2u_resource_kind=resource_kind,
        db2u_version="11.5.9.0",  # Current version
        db2u_target_version="v12.0",  # Target requires upgrade
        mas_instances=[{
            "metadata": {"name": "inst1"},
            "status": {"versions": {"reconciled": "9.1.7"}}
        }],
        timeout_seconds=60
    )

    run_update_test(tmpdir, config)


@pytest.mark.parametrize("resource_kind", ["Db2uCluster", "Db2uInstance"])
def test_db2u_major_version_upgrade_rejected(tmpdir, resource_kind):
    """Test interactive update with Db2 major version upgrade - user rejects.

    Expected behavior:
    - Detects Db2 v11 needs upgrade to v12
    - Prompts user to confirm major version upgrade
    - User rejects the upgrade
    - Raises SystemExit with exit code 1
    - Update does not proceed
    """

    prompt_handlers = {
        # Proceed with current cluster
        '.*Proceed with this cluster.*': lambda msg: 'y',
        # Catalog selection
        '.*Select catalog version.*': lambda msg: '1',
        # Db2 version upgrade confirmation - user rejects - match exact format
        '.*Confirm update from Db2 11 to 12.*': lambda msg: 'n',
    }

    config = UpdateTestConfig(
        prompt_handlers=prompt_handlers,
        installed_catalog_id="v9-251231-amd64",
        target_catalog_version="v9-260129-amd64",
        db2u_namespaces=["db2u-system"],
        db2u_resource_kind=resource_kind,
        db2u_version="11.5.9.0",  # Current version
        db2u_target_version="v12.0",  # Target requires upgrade
        mas_instances=[{
            "metadata": {"name": "inst1"},
            "status": {"versions": {"reconciled": "9.1.7"}}
        }],
        expect_system_exit=True,
        expected_exit_code=1,
        timeout_seconds=60
    )

    run_update_test(tmpdir, config)


@pytest.mark.parametrize("resource_kind", ["Db2uCluster", "Db2uInstance"])
def test_db2u_minor_version_upgrade_no_prompt(tmpdir, resource_kind):
    """Test interactive update with Db2 minor version upgrade - no prompt needed.

    Expected behavior:
    - Detects Db2 v11.5.8.0 needs upgrade to v11.5.9.0
    - No prompt for minor version upgrade
    - Update proceeds automatically
    """

    prompt_handlers = {
        # Proceed with current cluster
        '.*Proceed with this cluster?.*': lambda msg: 'y',
        # Catalog selection
        '.*Select catalog version.*': lambda msg: '1',
        # Final confirmation
        '.*Proceed with these settings.*': lambda msg: 'y',
    }

    config = UpdateTestConfig(
        prompt_handlers=prompt_handlers,
        installed_catalog_id="v9-251231-amd64",
        target_catalog_version="v9-260129-amd64",
        db2u_namespaces=["db2u-system"],
        db2u_resource_kind=resource_kind,
        db2u_version="11.5.8.0",  # Current version
        db2u_target_version="v11.5",  # Same major version
        mas_instances=[{
            "metadata": {"name": "inst1"},
            "status": {"versions": {"reconciled": "9.1.7"}}
        }],
        timeout_seconds=30
    )

    run_update_test(tmpdir, config)


@pytest.mark.parametrize("resource_kind", ["Db2uCluster", "Db2uInstance"])
def test_db2u_multiple_namespaces_first_selection(tmpdir, resource_kind):
    """Test interactive update - user selects first namespace from multiple.

    Expected behavior:
    - Detects resources in multiple namespaces
    - User selects first namespace (db2u-ns1)
    - Sets db2_namespace parameter to first namespace
    - Update proceeds successfully
    """

    prompt_handlers = {
        '.*Proceed with this cluster?.*': lambda msg: 'y',
        '.*Select catalog version.*': lambda msg: '1',
        '.*Select namespace.*': lambda msg: '1',  # Select first
        '.*Proceed with these settings.*': lambda msg: 'y',
    }

    config = UpdateTestConfig(
        prompt_handlers=prompt_handlers,
        installed_catalog_id="v9-251231-amd64",
        target_catalog_version="v9-260129-amd64",
        db2u_namespaces=["db2u-ns1", "db2u-ns2"],
        db2u_resource_kind=resource_kind,
        mas_instances=[{
            "metadata": {"name": "inst1"},
            "status": {"versions": {"reconciled": "9.1.7"}}
        }],
        timeout_seconds=30
    )

    run_update_test(tmpdir, config)


@pytest.mark.parametrize("resource_kind", ["Db2uCluster", "Db2uInstance"])
def test_db2u_multiple_namespaces_last_selection(tmpdir, resource_kind):
    """Test interactive update - user selects last namespace from multiple.

    Expected behavior:
    - Detects resources in multiple namespaces
    - User selects last namespace (db2u-ns3)
    - Sets db2_namespace parameter to last namespace
    - Update proceeds successfully
    """

    prompt_handlers = {
        '.*Proceed with this cluster?.*': lambda msg: 'y',
        '.*Select catalog version.*': lambda msg: '1',
        '.*Select namespace.*': lambda msg: '3',  # Select last
        '.*Proceed with these settings.*': lambda msg: 'y',
    }

    config = UpdateTestConfig(
        prompt_handlers=prompt_handlers,
        installed_catalog_id="v9-251231-amd64",
        target_catalog_version="v9-260129-amd64",
        db2u_namespaces=["db2u-ns1", "db2u-ns2", "db2u-ns3"],
        db2u_resource_kind=resource_kind,
        mas_instances=[{
            "metadata": {"name": "inst1"},
            "status": {"versions": {"reconciled": "9.1.7"}}
        }],
        timeout_seconds=30
    )

    run_update_test(tmpdir, config)


# Made with Bob
