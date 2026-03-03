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


def test_install_interactive_no_catalog(tmpdir):
    """Test interactive installation when no catalog is installed."""

    # Define prompt handlers with expected patterns and responses
    prompt_handlers = {
        # 1. Cluster connection
        '.*Proceed with this cluster?.*': lambda msg: 'y',
        # 2. Install flavour (advanced options)
        '.*Show advanced installation options.*': lambda msg: 'n',
        # 3. Catalog selection
        '.*Select catalog.*': lambda msg: supportedCatalogs['amd64'][1],
        '.*Select release.*': lambda msg: '9.1',
        # 4. License acceptance
        '.*Do you accept the license terms?.*': lambda msg: 'y',
        # 5. Storage classes
        ".*Use the auto-detected storage classes.*": lambda msg: 'y',
        # 6. SLS configuration
        '.*License file.*': lambda msg: f'{tmpdir}/authorized_entitlement.lic',
        # 7. DRO configuration
        ".*Contact e-mail address.*": lambda msg: 'maximo@ibm.com',
        ".*Contact first name.*": lambda msg: 'Test',
        ".*Contact last name.*": lambda msg: 'Test',
        # 8. ICR credentials
        ".*IBM entitlement key.*": lambda msg: 'testEntitlementKey',
        # 9. MAS Instance configuration
        '.*Instance ID.*': lambda msg: 'testinst',
        '.*Workspace ID.*': lambda msg: 'testws',
        '.*Workspace.*name.*': lambda msg: 'Test Workspace',
        # 10. Operational mode
        '.*Operational Mode.*': lambda msg: '1',
        # 11. Application selection
        '.*Install IoT.*': lambda msg: 'y',
        '.*Install Monitor.*': lambda msg: 'n',
        '.*Install Manage.*': lambda msg: 'y',
        '.*Select components to enable.*': lambda msg: 'n',
        '.*Include customization archive.*': lambda msg: 'n',
        '.*Install Predict.*': lambda msg: 'n',
        '.*Install Assist.*': lambda msg: 'n',
        '.*Install Optimizer.*': lambda msg: 'n',
        '.*Install Visual Inspection.*': lambda msg: 'n',
        '.*Install.*Real Estate and Facilities.*': lambda msg: 'n',
        '.*Install AI Service.*': lambda msg: 'n',
        # 12a. Grafana configuration
        '.*Install Grafana.*': lambda msg: 'y',
        # 12. MongoDB configuration
        '.*Create MongoDb cluster.*': lambda msg: 'y',
        # 13. Db2 configuration
        '.*Create system Db2 instance.*': lambda msg: 'y',
        '.*Re-use System Db2 instance for Manage application.*': lambda msg: 'n',
        '.*Create Manage dedicated Db2 instance.*': lambda msg: 'y',
        # 14. Kafka configuration
        '.*Create system Kafka instance.*': lambda msg: 'y',
        '.*Kafka version.*': lambda msg: '3.8.0',
        # 15. Final confirmation
        '.*Use additional configurations.*': lambda msg: 'n',
        ".*Proceed with these settings.*": lambda msg: 'y',
    }

    # Create test configuration with no existing catalog
    config = InstallTestConfig(
        prompt_handlers=prompt_handlers,
        current_catalog=None,  # No catalog installed
        architecture='amd64',
        is_sno=False,
        is_airgap=False,
        storage_class_name='nfs-client',
        storage_provider='nfs',
        storage_provider_name='NFS Client',
        ocp_version='4.18.0',
        timeout_seconds=30
    )

    # Run the test
    run_install_test(tmpdir, config)


# Made with Bob
