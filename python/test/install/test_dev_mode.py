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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# Common prompt handlers shared across ALL interactive tests
# Tests can override or extend these by merging with test-specific handlers
# Note: tmpdir-dependent prompts must be defined in test_prompts
COMMON_PROMPTS = {
    # Cluster connection
    ".*Proceed with this cluster?.*": lambda msg: "y",
    # Storage classes
    ".*Use the auto-detected storage classes.*": lambda msg: "y",
    # Catalog selection
    ".*Select catalog.*": lambda msg: "v9-master-amd64",
    # ICR & Artifactory credentials
    ".*IBM entitlement key.*": lambda msg: "testEntitlementKey",
    ".*Artifactory username.*": lambda msg: "testUsername",
    ".*Artifactory token.*": lambda msg: "testToken",
    # DRO configuration
    ".*Contact e-mail address.*": lambda msg: "maximo@ibm.com",
    ".*Contact first name.*": lambda msg: "Test",
    ".*Contact last name.*": lambda msg: "Test",
    # MAS Instance configuration
    ".*Instance ID.*": lambda msg: "testinst",
    ".*Workspace ID.*": lambda msg: "testws",
    ".*Workspace.*name.*": lambda msg: "Test Workspace",
    ".*Operational Mode.*": lambda msg: "1",
    # Application selection
    ".*Install IoT.*": lambda msg: "y",
    ".*Install Monitor.*": lambda msg: "y",
    ".*Install Manage.*": lambda msg: "y",
    # Manage application configuration
    ".*Select components to enable.*": lambda msg: "n",
    ".*Include customization archive.*": lambda msg: "n",
    # Application selection - disabled by default
    ".*Install Predict.*": lambda msg: "n",
    ".*Install Assist.*": lambda msg: "n",
    ".*Install Optimizer.*": lambda msg: "n",
    ".*Install Visual Inspection.*": lambda msg: "n",
    ".*Install.*Real Estate and Facilities.*": lambda msg: "n",
    ".*Install AI Service.*": lambda msg: "n",
    # Infrastructure
    ".*Install Grafana.*": lambda msg: "y",
    ".*Create MongoDb cluster.*": lambda msg: "y",
    ".*Create system Db2 instance.*": lambda msg: "y",
    ".*Re-use System Db2 instance for Manage application.*": lambda msg: "n",
    ".*Create Manage dedicated Db2 instance.*": lambda msg: "y",
    ".*Create system Kafka instance.*": lambda msg: "y",
    ".*Kafka version.*": lambda msg: "3.8.0",
    # Configuration
    ".*Do you want to configure AiCfg.*": lambda msg: "n",
    # Final confirmation
    ".*Use additional configurations.*": lambda msg: "n",
    ".*Proceed with these settings.*": lambda msg: "y",
}


def test_install_master_no_dev_mode(tmpdir):
    """Test expected NoSuchCatalogError is raised"""

    # Test-specific prompts (merged with COMMON_PROMPTS)
    test_prompts = {
        ".*Show advanced installation options.*": lambda msg: "n",
        ".*Select catalog.*": lambda msg: "v9-master-amd64",
    }
    prompt_handlers = {**COMMON_PROMPTS, **test_prompts}

    # Create test configuration with no existing catalog
    config = InstallTestConfig(
        prompt_handlers=prompt_handlers,
        current_catalog=None,  # No catalog installed
        architecture="amd64",
        is_sno=False,
        is_airgap=False,
        storage_class_name="nfs-client",
        storage_provider="nfs",
        storage_provider_name="NFS Client",
        ocp_version="4.18.0",
        timeout_seconds=30,
    )

    # Run the test and expect NoSuchCatalogError to be raised
    with pytest.raises(NoSuchCatalogError):
        run_install_test(tmpdir, config)


def test_install_master_dev_mode(tmpdir):
    """Test interactive installation when no catalog is installed with --dev-mode flag."""

    # Test-specific prompts (merged with COMMON_PROMPTS)
    test_prompts = {
        ".*Show advanced installation options.*": lambda msg: "n",
        ".*Select channel.*": lambda msg: "9.1.x-dev",
        ".*SLS channel.*": lambda msg: "1.x-stable",
        ".*>License file<.*": lambda msg: f"{tmpdir}/authorized_entitlement.lic",
        ".*>Db2 License file<.*": lambda msg: "",
        ".*Custom channel for iot.*": lambda msg: "9.1.x-dev",
        ".*Custom channel for monitor.*": lambda msg: "9.1.x-dev",
        ".*Custom channel for manage.*": lambda msg: "9.1.x-dev",
    }
    prompt_handlers = {**COMMON_PROMPTS, **test_prompts}

    # Create test configuration with no existing catalog and --dev-mode flag
    config = InstallTestConfig(
        prompt_handlers=prompt_handlers,
        current_catalog=None,  # No catalog installed
        architecture="amd64",
        is_sno=False,
        is_airgap=False,
        storage_class_name="nfs-client",
        storage_provider="nfs",
        storage_provider_name="NFS Client",
        ocp_version="4.18.0",
        timeout_seconds=30,
        argv=["--dev-mode"],
    )

    # Run the test
    run_install_test(tmpdir, config)


def test_install_master_dev_mode_existing_catalog(tmpdir):
    """Test interactive installation when no catalog is installed with --dev-mode flag."""

    # Test-specific prompts (merged with COMMON_PROMPTS)
    test_prompts = {
        ".*Show advanced installation options.*": lambda msg: "n",
        ".*Select channel.*": lambda msg: "9.1.x-dev",
        ".*SLS channel.*": lambda msg: "1.x-stable",
        ".*>License file<.*": lambda msg: f"{tmpdir}/authorized_entitlement.lic",
        ".*>Db2 License file<.*": lambda msg: "",
        ".*Custom channel for iot.*": lambda msg: "9.1.x-dev",
        ".*Custom channel for monitor.*": lambda msg: "9.1.x-dev",
        ".*Custom channel for manage.*": lambda msg: "9.1.x-dev",
    }
    prompt_handlers = {**COMMON_PROMPTS, **test_prompts}

    # Create test configuration with no existing catalog and --dev-mode flag
    config = InstallTestConfig(
        prompt_handlers=prompt_handlers,
        current_catalog={"catalogId": "v9-master-amd64"},
        architecture="amd64",
        is_sno=False,
        is_airgap=False,
        storage_class_name="nfs-client",
        storage_provider="nfs",
        storage_provider_name="NFS Client",
        ocp_version="4.18.0",
        timeout_seconds=30,
        argv=["--dev-mode"],
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

    # Test-specific prompts for advanced configuration with path routing
    test_prompts = {
        ".*Show advanced installation options.*": lambda msg: "y",
        ".*Select channel.*": lambda msg: "9.2.x-dev",
        ".*Routing Mode.*": lambda msg: "1",
        ".*Disable Route Creation.*": lambda msg: "y",
        ".*Use Service Mesh.*": lambda msg: "y",
        ".*Configure ingress namespace ownership.*": lambda msg: "y",
        ".*SLS Mode.*": lambda msg: "1",
        ".*SLS channel.*": lambda msg: "1.x-stable",
        ".*>License file<.*": lambda msg: f"{tmpdir}/authorized_entitlement.lic",
        ".*>Db2 License file<.*": lambda msg: "",
        ".*DRO.*Namespace.*": lambda msg: "",
        ".*Permission Mode.*": lambda msg: "1",
        ".*Certificate issuer kind.*": lambda msg: "2",
        ".*Trust default CAs.*": lambda msg: "y",
        ".*Cluster ingress certificate secret name.*": lambda msg: "",
        ".*Configure domain.*certificate management.*": lambda msg: "n",
        ".*Configure SSO properties.*": lambda msg: "n",
        ".*Allow special characters for user IDs and usernames.*": lambda msg: "n",
        ".*Enable Guided Tour.*": lambda msg: "y",
        ".*Enable feature adoption metrics.*": lambda msg: "y",
        ".*Enable deployment progression metrics.*": lambda msg: "y",
        ".*Enable usability metrics.*": lambda msg: "y",
        ".*Custom channel for iot.*": lambda msg: "9.2.x-dev",
        ".*Custom channel for monitor.*": lambda msg: "9.2.x-dev",
        ".*Custom channel for manage.*": lambda msg: "9.2.x-dev",
        ".*Select a server bundle configuration.*": lambda msg: "1",
        ".*Customize database settings.*": lambda msg: "n",
        ".*Create demo data.*": lambda msg: "n",
        ".*Manage server timezone.*": lambda msg: "GMT",
        ".*Base language.*": lambda msg: "EN",
        ".*Secondary language.*": lambda msg: "",
        ".*MongoDb namespace.*": lambda msg: "mongoce",
        ".*Select the Manage dedicated DB2 instance type.*": lambda msg: "1",
        ".*Install namespace.*": lambda msg: "db2u",
        ".*Configure node affinity.*": lambda msg: "n",
        ".*Configure node tolerations.*": lambda msg: "n",
        ".*Customize CPU and memory request/limit.*": lambda msg: "n",
        ".*Customize storage capacity.*": lambda msg: "n",
        r".*Select Db2 Custom Resource\(CR\).*": lambda msg: "n",
        ".*Select Kafka provider.*": lambda msg: "1",
        ".*Strimzi namespace.*": lambda msg: "strimzi",
        ".*Use pod templates.*": lambda msg: "n",
        ".*Enable integration with Cognos Analytics.*": lambda msg: "n",
        ".*Enable integration with Watson Studio Local?.*": lambda msg: "n",
    }
    prompt_handlers = {**COMMON_PROMPTS, **test_prompts}

    # Create test configuration with --dev-mode flag and 9.2.x-dev channel
    config = InstallTestConfig(
        prompt_handlers=prompt_handlers,
        current_catalog={"catalogId": "v9-master-amd64"},
        architecture="amd64",
        is_sno=False,
        is_airgap=False,
        storage_class_name="nfs-client",
        storage_provider="nfs",
        storage_provider_name="NFS Client",
        ocp_version="4.18.0",
        timeout_seconds=30,
        argv=["--dev-mode"],
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
        architecture="amd64",
        is_sno=False,
        is_airgap=False,
        storage_class_name="nfs-client",
        storage_provider="nfs",
        storage_provider_name="NFS Client",
        ocp_version="4.18.0",
        timeout_seconds=30,
        argv=[
            "--dev-mode",
            "--artifactory-username",
            "ARTIFACTORY_USERNAME",
            "--artifactory-token",
            "ARTIFACTORY_TOKEN",
            "--mas-catalog-version",
            "v9-master-amd64",
            "--mas-instance-id",
            "fvtcore",
            "--mas-workspace-id",
            "masdev",
            "--mas-workspace-name",
            "MAS Development",
            "--superuser-username",
            "MAS_SUPERUSER_USERNAME",
            "--superuser-password",
            "MAS_SUPERUSER_PASSWORD",
            "--mas-channel",
            "9.2.x-dev",
            "--iot-channel",
            "9.2.x-dev",
            "--db2-system",
            "--kafka-provider",
            "strimzi",
            "--monitor-channel",
            "9.2.x-dev",
            "--manage-channel",
            "9.2.x-dev",
            "--manage-components",
            "",
            "--db2-manage",
            "--manage-jdbc",
            "workspace-application",
            "--manage-customization-archive-name",
            "fvtcustomarchive",
            "--manage-customization-archive-url",
            "https://ibm.com/manage-custom-archive-latest.zip",
            "--manage-customization-archive-username",
            "FVT_ARTIFACTORY_USERNAME",
            "--manage-customization-archive-password",
            "FVT_ARTIFACTORY_TOKEN",
            "--optimizer-channel",
            "",
            "--predict-channel",
            "",
            "--visualinspection-channel",
            "",
            "--facilities-channel",
            "",
            "--cos",
            "ibm",
            "--cos-resourcegroup",
            "fvt-layer3",
            "--cos-apikey",
            "IBMCLOUD_APIKEY",
            "--cos-instance-name",
            "Object Storage for MAS - fvtcore",
            "--cos-bucket-name",
            "fvtcore-masdev-bucket-20260209-0209",
            "--db2-channel",
            "rotate",
            "--skip-grafana-install",
            "--grafana-v5-namespace",
            "grafana5",
            "--grafana-instance-storage-size",
            "10Gi",
            "--additional-configs",
            f"{tmpdir}",
            "--storage-class-rwx",
            "ibmc-file-gold-gid",
            "--storage-class-rwo",
            "ibmc-block-gold",
            "--storage-pipeline",
            "ibmc-file-gold-gid",
            "--storage-accessmode",
            "ReadWriteMany",
            "--ibm-entitlement-key",
            "IBM_ENTITLEMENT_KEY",
            "--license-file",
            f"{tmpdir}/authorized_entitlement.lic",
            "--uds-email",
            "iotf@uk.ibm.com",
            "--uds-firstname",
            "First",
            "--uds-lastname",
            "Last",
            "--sls-namespace",
            "sls-fvtcore",
            "--sls-channel",
            "3.x-dev",
            "--approval-core",
            "100:300:true",
            "--approval-iot",
            "100:300:true",
            "--approval-manage",
            "100:600:true",
            "--approval-monitor",
            "100:300:true",
            "--approval-optimizer",
            "100:300:true",
            "--approval-predict",
            "100:300:true",
            "--approval-visualinspection",
            "100:300:true",
            "--approval-facilities",
            "100:300:true",
            "--accept-license",
            "--no-confirm",
        ],
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
        architecture="amd64",
        is_sno=False,
        is_airgap=False,
        storage_class_name="nfs-client",
        storage_provider="nfs",
        storage_provider_name="NFS Client",
        ocp_version="4.18.0",
        timeout_seconds=30,
        argv=[
            "--dev-mode",
            "--artifactory-username",
            "ARTIFACTORY_USERNAME",
            "--artifactory-token",
            "ARTIFACTORY_TOKEN",
            "--mas-catalog-version",
            "v9-master-amd64",
            "--mas-instance-id",
            "fvtcore",
            "--mas-workspace-id",
            "masdev",
            "--mas-workspace-name",
            "MAS Development",
            "--superuser-username",
            "MAS_SUPERUSER_USERNAME",
            "--superuser-password",
            "MAS_SUPERUSER_PASSWORD",
            "--mas-channel",
            "9.2.x-dev",
            "--routing",
            "path",
            "--ingress-controller-name",
            "default",
            "--configure-ingress",
            "--iot-channel",
            "9.2.x-dev",
            "--db2-system",
            "--kafka-provider",
            "strimzi",
            "--monitor-channel",
            "9.2.x-dev",
            "--manage-channel",
            "9.2.x-dev",
            "--manage-components",
            "",
            "--db2-manage",
            "--manage-jdbc",
            "workspace-application",
            "--manage-customization-archive-name",
            "fvtcustomarchive",
            "--manage-customization-archive-url",
            "https://ibm.com/manage-custom-archive-latest.zip",
            "--manage-customization-archive-username",
            "FVT_ARTIFACTORY_USERNAME",
            "--manage-customization-archive-password",
            "FVT_ARTIFACTORY_TOKEN",
            "--optimizer-channel",
            "",
            "--predict-channel",
            "",
            "--visualinspection-channel",
            "",
            "--facilities-channel",
            "",
            "--cos",
            "ibm",
            "--cos-resourcegroup",
            "fvt-layer3",
            "--cos-apikey",
            "IBMCLOUD_APIKEY",
            "--cos-instance-name",
            "Object Storage for MAS - fvtcore",
            "--cos-bucket-name",
            "fvtcore-masdev-bucket-20260209-0209",
            "--db2-channel",
            "rotate",
            "--skip-grafana-install",
            "--grafana-v5-namespace",
            "grafana5",
            "--grafana-instance-storage-size",
            "10Gi",
            "--additional-configs",
            f"{tmpdir}",
            "--storage-class-rwx",
            "ibmc-file-gold-gid",
            "--storage-class-rwo",
            "ibmc-block-gold",
            "--storage-pipeline",
            "ibmc-file-gold-gid",
            "--storage-accessmode",
            "ReadWriteMany",
            "--ibm-entitlement-key",
            "IBM_ENTITLEMENT_KEY",
            "--license-file",
            f"{tmpdir}/authorized_entitlement.lic",
            "--uds-email",
            "iotf@uk.ibm.com",
            "--uds-firstname",
            "First",
            "--uds-lastname",
            "Last",
            "--sls-namespace",
            "sls-fvtcore",
            "--sls-channel",
            "3.x-dev",
            "--approval-core",
            "100:300:true",
            "--approval-iot",
            "100:300:true",
            "--approval-manage",
            "100:600:true",
            "--approval-monitor",
            "100:300:true",
            "--approval-optimizer",
            "100:300:true",
            "--approval-predict",
            "100:300:true",
            "--approval-visualinspection",
            "100:300:true",
            "--approval-facilities",
            "100:300:true",
            "--accept-license",
            "--no-confirm",
        ],
    )
    # Run the test
    run_install_test(tmpdir, config)


def test_install_master_dev_mode_non_interactive_with_slack(tmpdir):
    """Test non-interactive installation with Slack notification parameters.

    This test verifies that slack_token and slack_channel parameters are properly
    handled in non-interactive mode and passed through to the pipeline configuration.
    """

    # Define prompt handlers - should be empty for non-interactive mode
    prompt_handlers = {}

    # Create test configuration with Slack parameters
    config = InstallTestConfig(
        prompt_handlers=prompt_handlers,
        current_catalog=None,  # No catalog installed
        architecture="amd64",
        is_sno=False,
        is_airgap=False,
        storage_class_name="nfs-client",
        storage_provider="nfs",
        storage_provider_name="NFS Client",
        ocp_version="4.18.0",
        timeout_seconds=30,
        argv=[
            "--dev-mode",
            "--artifactory-username",
            "ARTIFACTORY_USERNAME",
            "--artifactory-token",
            "ARTIFACTORY_TOKEN",
            "--mas-catalog-version",
            "v9-master-amd64",
            "--mas-instance-id",
            "fvtcore",
            "--mas-workspace-id",
            "masdev",
            "--mas-workspace-name",
            "MAS Development",
            "--superuser-username",
            "MAS_SUPERUSER_USERNAME",
            "--superuser-password",
            "MAS_SUPERUSER_PASSWORD",
            "--mas-channel",
            "9.2.x-dev",
            "--iot-channel",
            "9.2.x-dev",
            "--db2-system",
            "--kafka-provider",
            "strimzi",
            "--manage-channel",
            "9.2.x-dev",
            "--manage-components",
            "",
            "--db2-manage",
            "--manage-jdbc",
            "workspace-application",
            "--cos",
            "ibm",
            "--cos-resourcegroup",
            "fvt-layer3",
            "--cos-apikey",
            "IBMCLOUD_APIKEY",
            "--cos-instance-name",
            "Object Storage for MAS - fvtcore",
            "--cos-bucket-name",
            "fvtcore-masdev-bucket-20260209-0209",
            "--db2-channel",
            "rotate",
            "--skip-grafana-install",
            "--additional-configs",
            f"{tmpdir}",
            "--storage-class-rwx",
            "ibmc-file-gold-gid",
            "--storage-class-rwo",
            "ibmc-block-gold",
            "--storage-pipeline",
            "ibmc-file-gold-gid",
            "--storage-accessmode",
            "ReadWriteMany",
            "--ibm-entitlement-key",
            "IBM_ENTITLEMENT_KEY",
            "--license-file",
            f"{tmpdir}/authorized_entitlement.lic",
            "--uds-email",
            "iotf@uk.ibm.com",
            "--uds-firstname",
            "First",
            "--uds-lastname",
            "Last",
            "--sls-namespace",
            "sls-fvtcore",
            "--sls-channel",
            "3.x-dev",
            # Slack notification parameters
            "--slack-token",
            "xoxb-test-slack-token-12345",
            "--slack-channel",
            "mas-notifications,mas-alerts",
            "--accept-license",
            "--no-confirm",
        ],
    )
    # Run the test
    run_install_test(tmpdir, config)


def test_install_master_dev_mode_with_cognos(tmpdir):
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

    # Test-specific prompts for Cognos Analytics integration
    test_prompts = {
        ".*Show advanced installation options.*": lambda msg: "y",
        ".*Select channel.*": lambda msg: "9.2.x-dev",
        ".*Routing Mode.*": lambda msg: "2",
        ".*Disable Route Creation.*": lambda msg: "n",
        ".*Use Service Mesh.*": lambda msg: "n",
        ".*SLS Mode.*": lambda msg: "1",
        ".*SLS channel.*": lambda msg: "1.x-stable",
        ".*>License file<.*": lambda msg: f"{tmpdir}/authorized_entitlement.lic",
        ".*>Db2 License file<.*": lambda msg: "",
        ".*DRO.*Namespace.*": lambda msg: "",
        ".*Permission Mode.*": lambda msg: "1",
        ".*Certificate issuer kind.*": lambda msg: "2",
        ".*Trust default CAs.*": lambda msg: "y",
        ".*Cluster ingress certificate secret name.*": lambda msg: "",
        ".*Configure domain.*certificate management.*": lambda msg: "n",
        ".*Configure SSO properties.*": lambda msg: "n",
        ".*Allow special characters for user IDs and usernames.*": lambda msg: "n",
        ".*Enable Guided Tour.*": lambda msg: "y",
        ".*Enable feature adoption metrics.*": lambda msg: "y",
        ".*Enable deployment progression metrics.*": lambda msg: "y",
        ".*Enable usability metrics.*": lambda msg: "y",
        ".*Custom channel for iot.*": lambda msg: "9.2.x-dev",
        ".*Custom channel for monitor.*": lambda msg: "9.2.x-dev",
        ".*Custom channel for manage.*": lambda msg: "9.2.x-dev",
        ".*Select a server bundle configuration.*": lambda msg: "1",
        ".*Customize database settings.*": lambda msg: "n",
        ".*Create demo data.*": lambda msg: "n",
        ".*Manage server timezone.*": lambda msg: "GMT",
        ".*Base language.*": lambda msg: "EN",
        ".*Secondary language.*": lambda msg: "",
        ".*MongoDb namespace.*": lambda msg: "mongoce",
        ".*Select the Manage dedicated DB2 instance type.*": lambda msg: "1",
        ".*Install namespace.*": lambda msg: "db2u",
        ".*Configure node affinity.*": lambda msg: "n",
        ".*Configure node tolerations.*": lambda msg: "n",
        ".*Customize CPU and memory request/limit.*": lambda msg: "n",
        ".*Customize storage capacity.*": lambda msg: "n",
        r".*Select Db2 Custom Resource\(CR\).*": lambda msg: "n",
        ".*Select Kafka provider.*": lambda msg: "1",
        ".*Strimzi namespace.*": lambda msg: "strimzi",
        ".*Enable integration with Cognos Analytics.*": lambda msg: "y",
        ".*Enable integration with Watson Studio Local?.*": lambda msg: "y",
        ".*Cloud Pak for Data product version.*": lambda msg: "5.2.0",
        ".*Use pod templates.*": lambda msg: "n",
    }
    prompt_handlers = {**COMMON_PROMPTS, **test_prompts}

    # Create test configuration with --dev-mode flag and 9.2.x-dev channel
    config = InstallTestConfig(
        prompt_handlers=prompt_handlers,
        current_catalog={"catalogId": "v9-master-amd64"},
        architecture="amd64",
        is_sno=False,
        is_airgap=False,
        storage_class_name="nfs-client",
        storage_provider="nfs",
        storage_provider_name="NFS Client",
        ocp_version="4.18.0",
        timeout_seconds=30,
        argv=["--dev-mode"],
    )

    # Run the test
    run_install_test(tmpdir, config)


# Made with Bob
