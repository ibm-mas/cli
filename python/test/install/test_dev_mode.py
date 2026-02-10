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

# Add test directory to path for utils import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_install_master_no_dev_mode(tmpdir):
    """Test that master catalogs automatically resolve to newest catalog.

    Dev catalog resolution is now automatic and unconditional, so master
    catalogs work without requiring --dev-mode flag.
    """

    # Define prompt handlers with expected patterns and responses
    prompt_handlers = {
        # 1. Cluster connection
        '.*Proceed with this cluster?.*': lambda msg: 'y',
        # 2. Install flavour (advanced options)
        '.*Show advanced installation options.*': lambda msg: 'n',
        # 3. Catalog selection
        '.*Select catalog.*': lambda msg: "v9-master-amd64",
        '.*Select channel.*': lambda msg: '9.1.x-stable',
        # 4. Storage classes
        ".*Use the auto-detected storage classes.*": lambda msg: 'y',
        # 5. SLS configuration
        '.*SLS channel.*': lambda msg: '1.x-stable',
        '.*License file.*': lambda msg: f'{tmpdir}/authorized_entitlement.lic',
        # 6. DRO configuration
        ".*Contact e-mail address.*": lambda msg: 'maximo@ibm.com',
        ".*Contact first name.*": lambda msg: 'Test',
        ".*Contact last name.*": lambda msg: 'Test',
        # 7. ICR & Artifactory credentials
        ".*IBM entitlement key.*": lambda msg: 'testEntitlementKey',
        ".*Artifactory username.*": lambda msg: 'testUsername',
        ".*Artifactory token.*": lambda msg: 'testToken',
        # 8. MAS Instance configuration
        '.*Instance ID.*': lambda msg: 'testinst',
        '.*Workspace ID.*': lambda msg: 'testws',
        '.*Workspace.*name.*': lambda msg: 'Test Workspace',
        # 9. Operational mode
        '.*Operational Mode.*': lambda msg: '1',
        # 10. Application selection
        '.*Install IoT.*': lambda msg: 'n',
        '.*Install Monitor.*': lambda msg: 'n',
        '.*Install Manage.*': lambda msg: 'n',
        '.*Install Predict.*': lambda msg: 'n',
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

    # Run the test - master catalog should now resolve successfully
    run_install_test(tmpdir, config)


def test_install_master_dev_mode(tmpdir):
    """Test interactive installation when no catalog is installed with --dev-mode flag."""

    # Define prompt handlers with expected patterns and responses
    prompt_handlers = {
        # 1. Cluster connection
        '.*Proceed with this cluster?.*': lambda msg: 'y',
        # 2. Install flavour (advanced options)
        '.*Show advanced installation options.*': lambda msg: 'n',
        # 3. Catalog selection
        '.*Select catalog.*': lambda msg: "v9-master-amd64",
        '.*Select channel.*': lambda msg: '9.1.x-dev',
        # 4. Storage classes
        ".*Use the auto-detected storage classes.*": lambda msg: 'y',
        # 5. SLS configuration
        '.*SLS channel.*': lambda msg: '1.x-stable',
        '.*License file.*': lambda msg: f'{tmpdir}/authorized_entitlement.lic',
        # 6. DRO configuration
        ".*Contact e-mail address.*": lambda msg: 'maximo@ibm.com',
        ".*Contact first name.*": lambda msg: 'Test',
        ".*Contact last name.*": lambda msg: 'Test',
        # 7. ICR & Artifactory credentials
        ".*IBM entitlement key.*": lambda msg: 'testEntitlementKey',
        ".*Artifactory username.*": lambda msg: 'testUsername',
        ".*Artifactory token.*": lambda msg: 'testToken',
        # 8. MAS Instance configuration
        '.*Instance ID.*': lambda msg: 'testinst',
        '.*Workspace ID.*': lambda msg: 'testws',
        '.*Workspace.*name.*': lambda msg: 'Test Workspace',
        # 9. Operational mode
        '.*Operational Mode.*': lambda msg: '1',
        # 10. Application selection
        '.*Install IoT.*': lambda msg: 'y',
        '.*Custom channel for iot.*': lambda msg: '9.1.x-dev',
        '.*Install Monitor.*': lambda msg: 'n',
        '.*Install Manage.*': lambda msg: 'y',
        '.*Custom channel for manage.*': lambda msg: '9.1.x-dev',
        '.*Select components to enable.*': lambda msg: 'n',
        '.*Include customization archive.*': lambda msg: 'n',
        '.*Install Predict.*': lambda msg: 'n',
        '.*Install Assist.*': lambda msg: 'n',
        '.*Install Optimizer.*': lambda msg: 'n',
        '.*Install Visual Inspection.*': lambda msg: 'n',
        '.*Install.*Real Estate and Facilities.*': lambda msg: 'n',
        '.*Install AI Service.*': lambda msg: 'n',
        # 11. MongoDB configuration
        '.*Create MongoDb cluster.*': lambda msg: 'y',
        # 12. Db2 configuration
        '.*Create system Db2 instance.*': lambda msg: 'y',
        '.*Re-use System Db2 instance for Manage application.*': lambda msg: 'n',
        '.*Create Manage dedicated Db2 instance.*': lambda msg: 'y',
        # 13. Kafka configuration
        '.*Create system Kafka instance.*': lambda msg: 'y',
        '.*Kafka version.*': lambda msg: '3.8.0',
        # 14. Final confirmation
        '.*Use additional configurations.*': lambda msg: 'n',
        ".*Proceed with these settings.*": lambda msg: 'y',
    }

    # Create test configuration with no existing catalog and --dev-mode flag
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
        timeout_seconds=30,
        argv=['--dev-mode']
    )

    # Run the test
    run_install_test(tmpdir, config)


def test_install_master_dev_mode_existing_catalog(tmpdir):
    """Test interactive installation when no catalog is installed with --dev-mode flag."""

    # Define prompt handlers with expected patterns and responses
    prompt_handlers = {
        # 1. Cluster connection
        '.*Proceed with this cluster?.*': lambda msg: 'y',
        # 2. Install flavour (advanced options)
        '.*Show advanced installation options.*': lambda msg: 'n',
        # 3. Catalog selection
        '.*Select catalog.*': lambda msg: "v9-master-amd64",
        '.*Select channel.*': lambda msg: '9.1.x-dev',
        # 4. Storage classes
        ".*Use the auto-detected storage classes.*": lambda msg: 'y',
        # 5. SLS configuration
        '.*SLS channel.*': lambda msg: '1.x-stable',
        '.*License file.*': lambda msg: f'{tmpdir}/authorized_entitlement.lic',
        # 6. DRO configuration
        ".*Contact e-mail address.*": lambda msg: 'maximo@ibm.com',
        ".*Contact first name.*": lambda msg: 'Test',
        ".*Contact last name.*": lambda msg: 'Test',
        # 7. ICR & Artifactory credentials
        ".*IBM entitlement key.*": lambda msg: 'testEntitlementKey',
        ".*Artifactory username.*": lambda msg: 'testUsername',
        ".*Artifactory token.*": lambda msg: 'testToken',
        # 8. MAS Instance configuration
        '.*Instance ID.*': lambda msg: 'testinst',
        '.*Workspace ID.*': lambda msg: 'testws',
        '.*Workspace.*name.*': lambda msg: 'Test Workspace',
        # 9. Operational mode
        '.*Operational Mode.*': lambda msg: '1',
        # 10. Application selection
        '.*Install IoT.*': lambda msg: 'y',
        '.*Custom channel for iot.*': lambda msg: '9.1.x-dev',
        '.*Install Monitor.*': lambda msg: 'n',
        '.*Install Manage.*': lambda msg: 'y',
        '.*Custom channel for manage.*': lambda msg: '9.1.x-dev',
        '.*Select components to enable.*': lambda msg: 'n',
        '.*Include customization archive.*': lambda msg: 'n',
        '.*Install Predict.*': lambda msg: 'n',
        '.*Install Assist.*': lambda msg: 'n',
        '.*Install Optimizer.*': lambda msg: 'n',
        '.*Install Visual Inspection.*': lambda msg: 'n',
        '.*Install.*Real Estate and Facilities.*': lambda msg: 'n',
        '.*Install AI Service.*': lambda msg: 'n',
        # 11. MongoDB configuration
        '.*Create MongoDb cluster.*': lambda msg: 'y',
        # 12. Db2 configuration
        '.*Create system Db2 instance.*': lambda msg: 'y',
        '.*Re-use System Db2 instance for Manage application.*': lambda msg: 'n',
        '.*Create Manage dedicated Db2 instance.*': lambda msg: 'y',
        # 13. Kafka configuration
        '.*Create system Kafka instance.*': lambda msg: 'y',
        '.*Kafka version.*': lambda msg: '3.8.0',
        # 14. Final confirmation
        '.*Use additional configurations.*': lambda msg: 'n',
        ".*Proceed with these settings.*": lambda msg: 'y',
    }

    # Create test configuration with no existing catalog and --dev-mode flag
    config = InstallTestConfig(
        prompt_handlers=prompt_handlers,
        current_catalog={'catalogId': "v9-master-amd64"},
        architecture='amd64',
        is_sno=False,
        is_airgap=False,
        storage_class_name='nfs-client',
        storage_provider='nfs',
        storage_provider_name='NFS Client',
        ocp_version='4.18.0',
        timeout_seconds=30,
        argv=['--dev-mode']
    )

    # Run the test
    run_install_test(tmpdir, config)


def test_install_master_dev_mode_non_interactive(tmpdir):
    """Test non-interactive installation when no catalog is installed with --dev-mode flag."""

    # Define prompt handlers with expected patterns and responses
    prompt_handlers = {}

    # Create test configuration with no existing catalog and --dev-mode flag
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
        timeout_seconds=30,
        argv=[
            "--dev-mode",
            "--artifactory-username", "ARTIFACTORY_USERNAME",
            "--artifactory-token", "ARTIFACTORY_TOKEN",
            "--mas-catalog-version", "v9-master-amd64",
            "--mas-instance-id", "fvtcore",
            "--mas-workspace-id", "masdev",
            "--mas-workspace-name", "MAS Development",
            "--superuser-username", "MAS_SUPERUSER_USERNAME",
            "--superuser-password", "MAS_SUPERUSER_PASSWORD",
            "--mas-channel", "9.2.x-dev",
            "--assist-channel", "9.2.x-dev",
            "--iot-channel", "9.2.x-dev",
            "--db2-system", "--kafka-provider", "strimzi",
            "--monitor-channel", "9.2.x-dev",
            "--manage-channel", "9.2.x-dev",
            "--manage-components", "",
            "--db2-manage", "--manage-jdbc", "workspace-application",
            "--manage-customization-archive-name", "fvtcustomarchive",
            "--manage-customization-archive-url", "https://ibm.com/manage-custom-archive-latest.zip",
            "--manage-customization-archive-username", "FVT_ARTIFACTORY_USERNAME",
            "--manage-customization-archive-password", "FVT_ARTIFACTORY_TOKEN",
            "--optimizer-channel", "",
            "--predict-channel", "",
            "--visualinspection-channel", "",
            "--facilities-channel", "",
            "--cos", "ibm",
            "--cos-resourcegroup", "fvt-layer3",
            "--cos-apikey", "IBMCLOUD_APIKEY",
            "--cos-instance-name", "Object Storage for MAS - fvtcore",
            "--cos-bucket-name", "fvtcore-masdev-bucket-20260209-0209",
            "--db2-channel", "rotate",
            "--additional-configs", f"{tmpdir}",
            "--storage-class-rwx", "ibmc-file-gold-gid",
            "--storage-class-rwo", "ibmc-block-gold",
            "--storage-pipeline", "ibmc-file-gold-gid",
            "--storage-accessmode", "ReadWriteMany",
            "--ibm-entitlement-key", "IBM_ENTITLEMENT_KEY",
            "--license-file", f"{tmpdir}/authorized_entitlement.lic",
            "--uds-email", "iotf@uk.ibm.com",
            "--uds-firstname", "First",
            "--uds-lastname", "Last",
            "--sls-namespace", "sls-fvtcore",
            "--sls-channel", "3.x-dev",
            "--approval-core", "100:300:true",
            "--approval-assist", "100:300:true",
            "--approval-iot", "100:300:true",
            "--approval-manage", "100:600:true",
            "--approval-monitor", "100:300:true",
            "--approval-optimizer", "100:300:true",
            "--approval-predict", "100:300:true",
            "--approval-visualinspection", "100:300:true",
            "--approval-facilities", "100:300:true",
            "--accept-license",
            "--no-confirm",
        ]
    )
    # Run the test
    run_install_test(tmpdir, config)

# Made with Bob
