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
    """Test interactive update when exactly one namespace contains Db2U resources."""

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
    """Test interactive update when multiple namespaces contain Db2U resources."""

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
    """Test interactive update when no Db2U resources exist."""

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


# Made with Bob
