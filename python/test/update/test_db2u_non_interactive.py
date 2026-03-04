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
def test_db2u_one_namespace_no_arg(tmpdir, resource_kind):
    """Test non-interactive update with one namespace and no --db2-namespace arg.

    Expected behavior:
    - Automatically detects and selects the single namespace
    - Sets db2_namespace parameter
    - No prompts (--no-confirm mode)
    - Update proceeds successfully
    """

    config = UpdateTestConfig(
        prompt_handlers={},  # No prompts in non-interactive mode
        installed_catalog_id="v9-251231-amd64",
        target_catalog_version="v9-260129-amd64",
        db2u_namespaces=["db2u-system"],  # Single namespace
        db2u_resource_kind=resource_kind,
        mas_instances=[{
            "metadata": {"name": "inst1"},
            "status": {"versions": {"reconciled": "9.1.7"}}
        }],
        argv=['--catalog', 'v9-260129-amd64', '--no-confirm'],
        timeout_seconds=30
    )

    run_update_test(tmpdir, config)


@pytest.mark.parametrize("resource_kind", ["Db2uCluster", "Db2uInstance"])
def test_db2u_one_namespace_with_arg(tmpdir, resource_kind):
    """Test non-interactive update with explicit --db2-namespace argument.

    Expected behavior:
    - Uses the explicitly provided namespace
    - Sets db2_namespace parameter to provided value
    - No namespace detection needed
    - Update proceeds successfully
    """

    config = UpdateTestConfig(
        prompt_handlers={},  # No prompts in non-interactive mode
        installed_catalog_id="v9-251231-amd64",
        target_catalog_version="v9-260129-amd64",
        db2u_namespaces=["db2u-system"],  # Single namespace exists
        db2u_resource_kind=resource_kind,
        db2u_namespace_arg="db2u-system",  # Explicit namespace argument
        mas_instances=[{
            "metadata": {"name": "inst1"},
            "status": {"versions": {"reconciled": "9.1.7"}}
        }],
        argv=['--catalog', 'v9-260129-amd64', '--db2-namespace', 'db2u-system', '--no-confirm'],
        timeout_seconds=30
    )

    run_update_test(tmpdir, config)


@pytest.mark.parametrize("resource_kind", ["Db2uCluster", "Db2uInstance"])
def test_db2u_multiple_namespaces_no_arg(tmpdir, resource_kind):
    """Test non-interactive update with multiple namespaces and no arg - should fail.

    Expected behavior:
    - Detects resources in multiple namespaces
    - Displays failure message about multiple namespaces
    - Raises SystemExit with non-zero exit code
    - Error message indicates --db2-namespace argument is required
    """

    config = UpdateTestConfig(
        prompt_handlers={},  # No prompts in non-interactive mode
        installed_catalog_id="v9-251231-amd64",
        target_catalog_version="v9-260129-amd64",
        db2u_namespaces=["db2u-ns1", "db2u-ns2", "db2u-ns3"],  # Multiple namespaces
        db2u_resource_kind=resource_kind,
        mas_instances=[{
            "metadata": {"name": "inst1"},
            "status": {"versions": {"reconciled": "9.1.7"}}
        }],
        argv=['--catalog', 'v9-260129-amd64', '--no-confirm'],
        expect_system_exit=True,  # Expect failure
        timeout_seconds=30
    )

    run_update_test(tmpdir, config)


@pytest.mark.parametrize("resource_kind", ["Db2uCluster", "Db2uInstance"])
def test_db2u_multiple_namespaces_with_arg(tmpdir, resource_kind):
    """Test non-interactive update with multiple namespaces but explicit arg.

    Expected behavior:
    - Uses the explicitly provided namespace (db2u-ns2)
    - Ignores other namespaces with Db2U resources
    - Sets db2_namespace parameter to provided value
    - Update proceeds successfully
    """

    config = UpdateTestConfig(
        prompt_handlers={},  # No prompts in non-interactive mode
        installed_catalog_id="v9-251231-amd64",
        target_catalog_version="v9-260129-amd64",
        db2u_namespaces=["db2u-ns1", "db2u-ns2", "db2u-ns3"],  # Multiple namespaces
        db2u_resource_kind=resource_kind,
        db2u_namespace_arg="db2u-ns2",  # Explicit namespace argument
        mas_instances=[{
            "metadata": {"name": "inst1"},
            "status": {"versions": {"reconciled": "9.1.7"}}
        }],
        argv=['--catalog', 'v9-260129-amd64', '--db2-namespace', 'db2u-ns2', '--no-confirm'],
        timeout_seconds=30
    )

    run_update_test(tmpdir, config)


@pytest.mark.parametrize("resource_kind,with_arg", [
    ("Db2uCluster", False),
    ("Db2uCluster", True),
    ("Db2uInstance", False),
    ("Db2uInstance", True),
])
def test_db2u_no_namespaces(tmpdir, resource_kind, with_arg):
    """Test non-interactive update when no Db2U resources found.

    Expected behavior:
    - Displays message that no resources were found
    - db2_namespace parameter remains empty
    - Update continues without error (not a failure condition)
    """

    argv = ['--catalog', 'v9-260129-amd64', '--no-confirm']
    if with_arg:
        argv.extend(['--db2-namespace', 'db2u-system'])

    config = UpdateTestConfig(
        prompt_handlers={},  # No prompts in non-interactive mode
        installed_catalog_id="v9-251231-amd64",
        target_catalog_version="v9-260129-amd64",
        db2u_namespaces=[],  # No resources
        db2u_resource_kind=resource_kind,
        db2u_namespace_arg="db2u-system" if with_arg else None,
        mas_instances=[{
            "metadata": {"name": "inst1"},
            "status": {"versions": {"reconciled": "9.1.7"}}
        }],
        argv=argv,
        timeout_seconds=30
    )

    run_update_test(tmpdir, config)


# Made with Bob
