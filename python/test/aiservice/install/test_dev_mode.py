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

import sys
import os
import pytest
from mas.devops.data import NoSuchCatalogError

# Add test directory to path for utils import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from utils import AiServiceInstallTestConfig, run_aiservice_install_test


def test_aiservice_install_master_no_dev_mode(tmpdir):
    """Test expected NoSuchCatalogError is raised when using master catalog without dev mode"""

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
    config = AiServiceInstallTestConfig(
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
        run_aiservice_install_test(tmpdir, config)


def test_aiservice_install_master_dev_mode(tmpdir):
    """Test interactive aiservice installation when no catalog is installed with --dev-mode flag."""

    # Define prompt handlers with expected patterns and responses
    prompt_handlers = {
        # 1. Cluster connection
        '.*Proceed with this cluster?.*': lambda msg: 'y',
        # 2. Install flavour (advanced options)
        '.*Show advanced installation options.*': lambda msg: 'n',
        # 3. Catalog selection
        '.*Select catalog.*': lambda msg: "v9-master-amd64",
        '.*Custom channel for AI Service.*': lambda msg: '9.1.x-dev',
        # 4. Storage classes
        ".*Use the auto-detected storage classes.*": lambda msg: 'y',
        # 5. SLS configuration
        '.*License file.*': lambda msg: f'{tmpdir}/authorized_entitlement.lic',
        # 6. DRO configuration
        ".*Contact e-mail address.*": lambda msg: 'maximo@ibm.com',
        ".*Contact first name.*": lambda msg: 'Test',
        ".*Contact last name.*": lambda msg: 'Test',
        # 7. ICR & Artifactory credentials
        ".*IBM entitlement key.*": lambda msg: 'testEntitlementKey',
        ".*Artifactory username.*": lambda msg: 'testUsername',
        ".*Artifactory token.*": lambda msg: 'testToken',
        # 8. AI Service Instance configuration
        '.*Instance ID.*': lambda msg: 'testinst',
        # 9. Operational mode
        '.*Operational Mode.*': lambda msg: '1',
        # 10. Storage Configuration (MinIO)
        '.*Install Minio.*': lambda msg: 'y',
        '.*minio root username.*': lambda msg: 'miniouser',
        '.*minio root password.*': lambda msg: 'miniopass',
        # 11. Tenant Settings
        '.*Entitlement end date.*': lambda msg: '2027-02-16',
        # 12. WatsonX Integration
        '.*Watsonxai api key.*': lambda msg: 'testWxApiKey',
        '.*Watsonxai machine learning url.*': lambda msg: 'https://us-south.ml.cloud.ibm.com',
        '.*Watsonxai project id.*': lambda msg: 'testProjectId',
        '.*Does the Watsonxai AI use a self-signed certificate.*': lambda msg: 'n',
        '.*Watsonxai Deployment ID.*': lambda msg: '',
        '.*Watsonxai Space ID.*': lambda msg: '',
        # 13. RSL Integration
        '.*RSL url.*': lambda msg: 'https://api.rsl-service.suite.maximo.com',
        '.*ORG Id of RSL.*': lambda msg: 'testOrgId',
        '.*Token for RSL.*': lambda msg: 'testRslToken',
        '.*Does the RSL API use a self-signed certificate.*': lambda msg: 'n',
        # 14. MongoDB configuration
        '.*Create MongoDb cluster.*': lambda msg: 'y',
        # 15. Final confirmation
        ".*Proceed with these settings.*": lambda msg: 'y',
    }

    # Create test configuration with no existing catalog and --dev-mode flag
    config = AiServiceInstallTestConfig(
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
    run_aiservice_install_test(tmpdir, config)


def test_aiservice_install_master_dev_mode_existing_catalog(tmpdir):
    """Test interactive aiservice installation with existing catalog and --dev-mode flag."""

    # Define prompt handlers with expected patterns and responses
    prompt_handlers = {
        # 1. Cluster connection
        '.*Proceed with this cluster?.*': lambda msg: 'y',
        # 2. Install flavour (advanced options)
        '.*Show advanced installation options.*': lambda msg: 'n',
        # 3. Catalog selection (catalog already exists)
        '.*Custom channel for AI Service.*': lambda msg: '9.1.x-dev',
        # 4. Storage classes
        ".*Use the auto-detected storage classes.*": lambda msg: 'y',
        # 5. SLS configuration
        '.*License file.*': lambda msg: f'{tmpdir}/authorized_entitlement.lic',
        # 6. DRO configuration
        ".*Contact e-mail address.*": lambda msg: 'maximo@ibm.com',
        ".*Contact first name.*": lambda msg: 'Test',
        ".*Contact last name.*": lambda msg: 'Test',
        # 7. ICR & Artifactory credentials
        ".*IBM entitlement key.*": lambda msg: 'testEntitlementKey',
        ".*Artifactory username.*": lambda msg: 'testUsername',
        ".*Artifactory token.*": lambda msg: 'testToken',
        # 8. AI Service Instance configuration
        '.*Instance ID.*': lambda msg: 'testinst',
        # 9. Operational mode
        '.*Operational Mode.*': lambda msg: '1',
        # 10. Storage Configuration (MinIO)
        '.*Install Minio.*': lambda msg: 'y',
        '.*minio root username.*': lambda msg: 'miniouser',
        '.*minio root password.*': lambda msg: 'miniopass',
        # 11. Tenant Settings
        '.*Entitlement end date.*': lambda msg: '2027-02-16',
        # 12. WatsonX Integration
        '.*Watsonxai api key.*': lambda msg: 'testWxApiKey',
        '.*Watsonxai machine learning url.*': lambda msg: 'https://us-south.ml.cloud.ibm.com',
        '.*Watsonxai project id.*': lambda msg: 'testProjectId',
        '.*Does the Watsonxai AI use a self-signed certificate.*': lambda msg: 'n',
        '.*Watsonxai Deployment ID.*': lambda msg: '',
        '.*Watsonxai Space ID.*': lambda msg: '',
        # 13. RSL Integration
        '.*RSL url.*': lambda msg: 'https://api.rsl-service.suite.maximo.com',
        '.*ORG Id of RSL.*': lambda msg: 'testOrgId',
        '.*Token for RSL.*': lambda msg: 'testRslToken',
        '.*Does the RSL API use a self-signed certificate.*': lambda msg: 'n',
        # 14. MongoDB configuration
        '.*Create MongoDb cluster.*': lambda msg: 'y',
        # 15. Final confirmation
        ".*Proceed with these settings.*": lambda msg: 'y',
    }

    # Create test configuration with existing catalog and --dev-mode flag
    config = AiServiceInstallTestConfig(
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
    run_aiservice_install_test(tmpdir, config)


def test_aiservice_install_master_dev_mode_non_interactive(tmpdir):
    """Test non-interactive aiservice installation when no catalog is installed with --dev-mode flag."""

    # Define prompt handlers with expected patterns and responses
    prompt_handlers = {}

    # Create test configuration with no existing catalog and --dev-mode flag
    config = AiServiceInstallTestConfig(
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
            "--aiservice-instance-id", "testinst",
            "--aiservice-channel", "9.1.x-dev",
            "--storage-class-rwx", "nfs-client",
            "--storage-class-rwo", "nfs-client",
            "--storage-pipeline", "nfs-client",
            "--storage-accessmode", "ReadWriteMany",
            "--ibm-entitlement-key", "IBM_ENTITLEMENT_KEY",
            "--license-file", f"{tmpdir}/authorized_entitlement.lic",
            "--contact-email", "maximo@ibm.com",
            "--contact-firstname", "Test",
            "--contact-lastname", "Test",
            "--dro-namespace", "redhat-marketplace",
            "--mongodb-namespace", "mongoce",
            "--install-minio", "true",
            "--minio-root-user", "miniouser",
            "--minio-root-password", "miniopass",
            "--tenant-entitlement-type", "standard",
            "--tenant-entitlement-start-date", "2026-02-16",
            "--tenant-entitlement-end-date", "2027-02-16",
            "--watsonxai-apikey", "testWxApiKey",
            "--watsonxai-url", "https://us-south.ml.cloud.ibm.com",
            "--watsonxai-project-id", "testProjectId",
            "--rsl-url", "https://api.rsl-service.suite.maximo.com",
            "--rsl-org-id", "testOrgId",
            "--rsl-token", "testRslToken",
            "--accept-license",
            "--no-confirm",
            "--skip-pre-check",
        ]
    )
    # Run the test
    run_aiservice_install_test(tmpdir, config)
