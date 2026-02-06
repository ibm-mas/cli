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

from utils import InstallTestConfig, run_install_test
import sys
import os
from mas.cli.install.catalogs import supportedCatalogs

# Add test directory to path for utils import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_install_interactive_unsupported_ocp(tmpdir):
    """Test that installation fails with unsupported OCP version.
    """

    prompt_handlers = {
        # 1. Cluster connection
        '.*Proceed with this cluster?.*': lambda msg: 'y',
        # 2. Install flavour (advanced options)
        '.*Show advanced installation options.*': lambda msg: 'n',
        # 3. Catalog selection
        '.*Select release.*': lambda msg: '9.1',
    }

    # Create test configuration with unsupported OCP version
    config = InstallTestConfig(
        prompt_handlers=prompt_handlers,
        current_catalog={'catalogId': supportedCatalogs['amd64'][1]},
        architecture='amd64',
        is_sno=False,
        is_airgap=False,
        storage_class_name='nfs-client',
        storage_provider='nfs',
        storage_provider_name='NFS Client',
        ocp_version='4.6.0',  # Unsupported version
        timeout_seconds=30,
        expect_system_exit=True  # We expect SystemExit to be raised
    )

    # Run the test - SystemExit will be caught and verified by the helper
    # The test will also fail if not all prompts are matched, proving that
    # the prompt verification works correctly even with SystemExit
    run_install_test(tmpdir, config)


# Made with Bob
