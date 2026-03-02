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
import pytest
from mas.devops.data import NoSuchCatalogError

# Add test directory to path for utils import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_install_master_no_dev_mode(tmpdir):
    """Test expected NoSuchCatalogError is raised"""

    # Define prompt handlers with expected patterns and responses
    prompt_handlers = {
        # 1. Cluster connection
        '.*Proceed with this cluster?.*': lambda msg: 'y',
        # 2. Install flavour (advanced options)
        '.*Show advanced installation options.*': lambda msg: 'n',
        # 3. Catalog selection
        '.*Select catalog.*': lambda msg: "v9-master-amd64"
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

    # Run the test and expect NoSuchCatalogError to be raised
    with pytest.raises(NoSuchCatalogError):
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


def test_install_master_dev_mode_with_path_routing(tmpdir):
    """Test interactive installation with 9.2.0 channel including path-based routing mode configuration.

    This test verifies the complete routing mode flow including IngressController configuration:
    - Mock IngressController is initially NOT configured (namespaceOwnership='Strict')
    - User selects path-based routing mode
    - CLI detects IngressController needs configuration
    - User agrees to configure it
    - IngressController will be patched during installation

    Flow:
    1. User selects path-based routing mode
    2. CLI checks permissions (mocked to succeed)
    3. CLI auto-selects the only available IngressController ('default')
    4. CLI detects IngressController is NOT configured for path-based routing
    5. User is prompted to configure it
    6. User agrees (responds 'y')
    7. mas_configure_ingress parameter is set to 'true'
    8. IngressController will be patched during installation
    """

    # Define prompt handlers with expected patterns and responses
    prompt_handlers = {
        # 1. Cluster connection
        '.*Proceed with this cluster?.*': lambda msg: 'y',
        # 2. Install flavour (advanced options) - MUST be 'y' to enable routing mode
        '.*Show advanced installation options.*': lambda msg: 'y',
        # 3. Catalog selection
        '.*Select catalog.*': lambda msg: "v9-master-amd64",
        '.*Select channel.*': lambda msg: '9.2.x-dev',  # Use 9.2.x-dev channel
        # 4. Routing Mode Configuration - Select path-based routing
        '.*Routing Mode.*': lambda msg: '1',  # Select path-based routing
        # Note: IngressController selection prompt does NOT appear because there's only one controller
        # 5. Configure IngressController for path-based routing
        '.*Configure ingress namespace ownership.*': lambda msg: 'y',  # Agree to configure
        # 5. Storage classes
        ".*Use the auto-detected storage classes.*": lambda msg: 'y',
        # 6. SLS configuration
        '.*SLS Mode.*': lambda msg: '1',  # SLS Mode prompt (appears with advanced options)
        '.*SLS channel.*': lambda msg: '1.x-stable',
        '.*License file.*': lambda msg: f'{tmpdir}/authorized_entitlement.lic',
        # 7. DRO configuration
        '.*DRO.*Namespace.*': lambda msg: '',  # DRO Namespace prompt (appears with advanced options)
        ".*Contact e-mail address.*": lambda msg: 'maximo@ibm.com',
        ".*Contact first name.*": lambda msg: 'Test',
        ".*Contact last name.*": lambda msg: 'Test',
        # 8. ICR & Artifactory credentials
        ".*IBM entitlement key.*": lambda msg: 'testEntitlementKey',
        ".*Artifactory username.*": lambda msg: 'testUsername',
        ".*Artifactory token.*": lambda msg: 'testToken',
        # 9. MAS Instance configuration
        '.*Instance ID.*': lambda msg: 'testinst',
        '.*Workspace ID.*': lambda msg: 'testws',
        '.*Workspace.*name.*': lambda msg: 'Test Workspace',
        # 10. Operational mode
        '.*Operational Mode.*': lambda msg: '1',
        # 11. Certificate Authority Trust
        '.*Trust default CAs.*': lambda msg: 'y',
        # 12. Cluster ingress certificate secret name
        '.*Cluster ingress certificate secret name.*': lambda msg: '',  # Leave empty for auto-detection
        # 13. Domain & certificate management
        '.*Configure domain.*certificate management.*': lambda msg: 'n',  # Skip domain/cert config for simplicity
        # 14. SSO properties
        '.*Configure SSO properties.*': lambda msg: 'n',  # Skip SSO config
        # 15. Special characters for user IDs
        '.*Allow special characters for user IDs and usernames.*': lambda msg: 'n',
        # 16. Guided Tour
        '.*Enable Guided Tour.*': lambda msg: 'y',
        # 17. Feature adoption metrics
        '.*Enable feature adoption metrics.*': lambda msg: 'y',
        # 18. Deployment progression metrics
        '.*Enable deployment progression metrics.*': lambda msg: 'y',
        # 19. Usability metrics
        '.*Enable usability metrics.*': lambda msg: 'y',
        # 20. Application selection
        '.*Install IoT.*': lambda msg: 'y',
        '.*Custom channel for iot.*': lambda msg: '9.2.x-dev',
        '.*Install Monitor.*': lambda msg: 'n',
        '.*Install Manage.*': lambda msg: 'y',
        '.*Custom channel for manage.*': lambda msg: '9.2.x-dev',
        '.*Select a server bundle configuration.*': lambda msg: '1',  # Select dev server bundle
        '.*Customize database settings.*': lambda msg: 'n',  # Skip database customization
        '.*Create demo data.*': lambda msg: 'n',  # Skip demo data
        '.*Manage server timezone.*': lambda msg: 'GMT',  # Use GMT timezone
        '.*Base language.*': lambda msg: 'EN',  # Use English as base language
        '.*Secondary language.*': lambda msg: '',  # No secondary language
        '.*Select components to enable.*': lambda msg: 'n',
        '.*Include customization archive.*': lambda msg: 'n',
        '.*Install Predict.*': lambda msg: 'n',
        '.*Install Assist.*': lambda msg: 'n',
        '.*Install Optimizer.*': lambda msg: 'n',
        '.*Install Visual Inspection.*': lambda msg: 'n',
        '.*Install.*Real Estate and Facilities.*': lambda msg: 'n',
        '.*Install AI Service.*': lambda msg: 'n',
        # 21. MongoDB configuration
        '.*MongoDb namespace.*': lambda msg: 'mongoce',  # Use default MongoDB namespace
        '.*Create MongoDb cluster.*': lambda msg: 'y',
        # 22. Db2 configuration
        '.*Create system Db2 instance.*': lambda msg: 'y',
        '.*Re-use System Db2 instance for Manage application.*': lambda msg: 'n',
        '.*Create Manage dedicated Db2 instance.*': lambda msg: 'y',
        '.*Select the Manage dedicated DB2 instance type.*': lambda msg: '1',  # Select default DB2 type
        '.*Install namespace.*': lambda msg: 'db2u',  # DB2 install namespace
        '.*Configure node affinity.*': lambda msg: 'n',  # Skip node affinity configuration
        '.*Configure node tolerations.*': lambda msg: 'n',  # Skip node tolerations configuration
        '.*Customize CPU and memory request/limit.*': lambda msg: 'n',  # Skip CPU/memory customization
        '.*Customize storage capacity.*': lambda msg: 'n',  # Skip storage capacity customization
        r'.*Select Db2 Custom Resource\(CR\).*': lambda msg: 'n',  # Skip Db2 CR selection
        '.*Select Kafka provider.*': lambda msg: '1',  # Select default Kafka provider
        '.*Strimzi namespace.*': lambda msg: 'strimzi',  # Strimzi namespace
        '.*Use pod templates.*': lambda msg: 'n',  # Skip pod templates
        # 23. Kafka configuration
        '.*Create system Kafka instance.*': lambda msg: 'y',
        '.*Kafka version.*': lambda msg: '3.8.0',
        # 24. Final confirmation
        '.*Use additional configurations.*': lambda msg: 'n',
        ".*Proceed with these settings.*": lambda msg: 'y',
    }

    # Create test configuration with --dev-mode flag and 9.2.x-dev channel
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


def test_install_master_dev_mode_non_interactive_with_path_routing(tmpdir):
    """Test non-interactive installation with path-based routing mode using CLI flags.

    This test verifies the complete non-interactive flow with path-based routing:
    - Uses --routing flag to specify path mode
    - Uses --ingress-controller-name to specify the controller
    - Uses --configure-ingress to enable IngressController patching
    """

    # Define prompt handlers - should be empty for non-interactive mode
    prompt_handlers = {}

    # Create test configuration with routing flags
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
            "--routing", "path",
            "--ingress-controller-name", "default",
            "--configure-ingress",
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
