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

from utils.install_test_helper import InstallTestConfig, run_install_test
import sys
import os

# Add test directory to path for utils import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_install_dev_mode_arcgis_with_manage_spatial_cluster_mode(tmpdir):
    """Test installation with Manage Spatial and ArcGIS requiring cluster admin mode.

    This test verifies that ArcGIS works correctly when Manage with Spatial
    component is installed with cluster admin mode on MAS 9.2+.
    """

    # Define prompt handlers
    prompt_handlers = {
        # 1. Cluster connection
        ".*Proceed with this cluster?.*": lambda msg: "y",
        # 2. Install flavour (advanced options) - MUST be 'y' to enable routing mode
        ".*Show advanced installation options.*": lambda msg: "y",
        # 3. Catalog selection
        ".*Select catalog.*": lambda msg: "v9-master-amd64",
        ".*Select channel.*": lambda msg: "9.2.x-dev",  # Use 9.2.x-dev channel
        # 4. Routing Mode Configuration - Select path-based routing
        ".*Routing Mode.*": lambda msg: "1",  # Select path-based routing
        # Note: IngressController selection prompt does NOT appear because there's only one controller
        # 5. Service Mesh Configuration
        ".*Enable OpenShift Service Mesh support for MAS.*": lambda msg: "y",
        # 6. Configure IngressController for path-based routing
        ".*Configure ingress namespace ownership.*": lambda msg: "y",  # Agree to configure
        # 5. Storage classes
        ".*Use the auto-detected storage classes.*": lambda msg: "y",
        # 6. SLS configuration
        ".*SLS Mode.*": lambda msg: "1",  # SLS Mode prompt (appears with advanced options)
        ".*SLS channel.*": lambda msg: "1.x-stable",
        ".*>License file<.*": lambda msg: f"{tmpdir}/authorized_entitlement.lic",  # SLS License (exact match with HTML tags)
        ".*>Db2 License file<.*": lambda msg: "",  # Db2 License (exact match with HTML tags)
        # 7. DRO configuration
        ".*DRO.*Namespace.*": lambda msg: "",  # DRO Namespace prompt (appears with advanced options)
        ".*Contact e-mail address.*": lambda msg: "maximo@ibm.com",
        ".*Contact first name.*": lambda msg: "Test",
        ".*Contact last name.*": lambda msg: "Test",
        # 8. ICR & Artifactory credentials
        ".*IBM entitlement key.*": lambda msg: "testEntitlementKey",
        ".*Artifactory username.*": lambda msg: "testUsername",
        ".*Artifactory token.*": lambda msg: "testToken",
        # 9. MAS Instance configuration
        ".*Instance ID.*": lambda msg: "testinst",
        ".*Workspace ID.*": lambda msg: "testws",
        ".*Workspace.*name.*": lambda msg: "Test Workspace",
        # 10. Operational mode
        ".*Operational Mode.*": lambda msg: "1",
        # 11. Permission mode
        ".*Mas Admin Mode.*": lambda msg: "1",  # Cluster mode
        # 12. Internal certificate issuer kind (appears when Permission Mode is cluster)
        ".*Certificate issuer kind.*": lambda msg: "2",  # Select ClusterIssuer
        # 13. Certificate Authority Trust
        ".*Trust default CAs.*": lambda msg: "y",
        # 14. Cluster ingress certificate secret name
        ".*Cluster ingress certificate secret name.*": lambda msg: "",  # Leave empty for auto-detection
        # 15. Domain & certificate management
        ".*Configure domain.*certificate management.*": lambda msg: "n",  # Skip domain/cert config for simplicity
        # 16. SSO properties
        ".*Configure SSO properties.*": lambda msg: "n",  # Skip SSO config
        # 17. Special characters for user IDs
        ".*Allow special characters for user IDs and usernames.*": lambda msg: "n",
        # 18. Guided Tour
        ".*Enable Guided Tour.*": lambda msg: "y",
        # 19. Feature adoption metrics
        ".*Enable feature adoption metrics.*": lambda msg: "y",
        # 20. Deployment progression metrics
        ".*Enable deployment progression metrics.*": lambda msg: "y",
        # 21. Usability metrics
        ".*Enable usability metrics.*": lambda msg: "y",
        # 22. Application selection
        ".*Install IoT.*": lambda msg: "y",
        ".*Custom channel for iot.*": lambda msg: "9.2.x-dev",
        ".*Install Monitor.*": lambda msg: "y",
        ".*Custom channel for monitor.*": lambda msg: "9.2.x-dev",
        ".*Install Manage.*": lambda msg: "y",
        ".*Custom channel for manage.*": lambda msg: "9.2.x-dev",
        ".*Select a server bundle configuration.*": lambda msg: "1",
        ".*Customize database settings.*": lambda msg: "n",
        ".*Create demo data.*": lambda msg: "n",
        ".*Manage server timezone.*": lambda msg: "GMT",
        ".*Base language.*": lambda msg: "EN",
        ".*Secondary language.*": lambda msg: "",
        ".*Select components to enable.*": lambda msg: "y",
        # 11.1. Manage Component Selection (individual prompts)
        ".*Asset Configuration Manager.*": lambda msg: "n",
        ".*Aviation.*": lambda msg: "n",
        ".*Civil Infrastructure.*": lambda msg: "n",
        ".*Envizi.*": lambda msg: "n",
        ".*Health\\?.*": lambda msg: "n",  # Match "Health?" exactly
        ".*Health, Safety and Environment.*": lambda msg: "n",  # Match HSE
        ".*Maximo IT.*": lambda msg: "n",
        ".*Nuclear.*": lambda msg: "n",
        ".*Oil.*Gas.*": lambda msg: "n",
        ".*Connector for Oracle Applications.*": lambda msg: "n",
        ".*Connector for SAP Application.*": lambda msg: "n",
        ".*Service Provider.*": lambda msg: "n",
        ".*Spatial.*": lambda msg: "y",  # Enable Spatial for ArcGIS
        ".*Strategize.*": lambda msg: "n",
        ".*Transportation.*": lambda msg: "n",
        ".*Tririga.*": lambda msg: "n",
        ".*Utilities.*": lambda msg: "n",
        ".*Workday Applications.*": lambda msg: "n",
        ".*AIP.*": lambda msg: "n",
        ".*Collaborate.*": lambda msg: "n",
        ".*Include customization archive.*": lambda msg: "n",
        ".*Install Predict.*": lambda msg: "n",
        ".*Install Assist.*": lambda msg: "n",
        ".*Install Optimizer.*": lambda msg: "n",
        ".*Install Visual Inspection.*": lambda msg: "n",
        ".*Install.*Real Estate and Facilities.*": lambda msg: "n",
        ".*Install AI Service.*": lambda msg: "n",
        ".*Include IBM Maximo Location Services for Esri.*": lambda msg: "y",
        ".*Do you accept the license terms?.*": lambda msg: "y",
        # 23. Grafana configuration (appears when advanced options are enabled)
        ".*Install Grafana.*": lambda msg: "y",
        # 24. MongoDB configuration
        ".*MongoDb namespace.*": lambda msg: "mongoce",  # Use default MongoDB namespace
        ".*Create MongoDb cluster.*": lambda msg: "y",
        # 25. Db2 configuration
        ".*Create system Db2 instance.*": lambda msg: "y",
        ".*Re-use System Db2 instance for Manage application.*": lambda msg: "n",
        ".*Create Manage dedicated Db2 instance.*": lambda msg: "y",
        ".*Select the Manage dedicated DB2 instance type.*": lambda msg: "1",  # Select default DB2 type
        ".*Install namespace.*": lambda msg: "db2u",  # DB2 install namespace
        ".*Configure node affinity.*": lambda msg: "n",  # Skip node affinity configuration
        ".*Configure node tolerations.*": lambda msg: "n",  # Skip node tolerations configuration
        ".*Customize CPU and memory request/limit.*": lambda msg: "n",  # Skip CPU/memory customization
        ".*Customize storage capacity.*": lambda msg: "n",  # Skip storage capacity customization
        r".*Select Db2 Custom Resource\(CR\).*": lambda msg: "n",  # Skip Db2 CR selection
        ".*Select Kafka provider.*": lambda msg: "1",  # Select default Kafka provider
        ".*Strimzi namespace.*": lambda msg: "strimzi",  # Strimzi namespace
        ".*Use pod templates.*": lambda msg: "n",  # Skip pod templates
        # 26. Kafka configuration
        ".*Create system Kafka instance.*": lambda msg: "y",
        ".*Kafka version.*": lambda msg: "3.8.0",
        # 24. AiCfg configuration
        ".*Do you want to configure AiCfg.*": lambda msg: "n",
        # 27. Final confirmation
        ".*Use additional configurations.*": lambda msg: "n",
        ".*Proceed with these settings.*": lambda msg: "y",
    }

    # Create test configuration
    config = InstallTestConfig(
        prompt_handlers=prompt_handlers,
        current_catalog=None,
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
