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
import pytest

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
        # 2. Install flavour (advanced mode required)
        ".*Show advanced installation options.*": lambda msg: "y",
        # 3. Catalog selection
        ".*Select catalog.*": lambda msg: "v9-master-amd64",
        ".*Select channel.*": lambda msg: "9.2.x-dev",
        # 4. Routing Mode
        ".*Routing Mode.*": lambda msg: "2",
        # 5. Service Mesh
        ".*Enable OpenShift Service Mesh support for MAS.*": lambda msg: "n",
        # 6. Storage classes
        ".*Use the auto-detected storage classes.*": lambda msg: "y",
        # 7. SLS configuration
        ".*SLS Mode.*": lambda msg: "1",
        ".*SLS channel.*": lambda msg: "1.x-stable",
        ".*License file.*": lambda msg: f"{tmpdir}/authorized_entitlement.lic",
        ".*Db2 License file.*": lambda msg: "",
        # 8. DRO configuration
        ".*DRO.*Namespace.*": lambda msg: "",
        ".*Contact e-mail address.*": lambda msg: "test@ibm.com",
        ".*Contact first name.*": lambda msg: "Test",
        ".*Contact last name.*": lambda msg: "User",
        # 9. ICR & Artifactory credentials
        ".*IBM entitlement key.*": lambda msg: "testEntitlementKey",
        ".*Artifactory username.*": lambda msg: "testUsernamed@us.ibm.com",
        ".*Artifactory token.*": lambda msg: "testArtifactoryToken",
        # 10. MAS Instance configuration
        ".*Instance ID.*": lambda msg: "dev92",
        ".*Workspace ID.*": lambda msg: "main",
        ".*Workspace.*name.*": lambda msg: "main",
        # 11. Operational mode
        ".*Operational Mode.*": lambda msg: "1",
        # 12. Admin mode - MUST be cluster for ArcGIS
        ".*Mas Admin Mode.*": lambda msg: "1",
        # 13. Certificate issuer kind
        ".*Certificate issuer kind.*": lambda msg: "2",
        # 14. Certificate Authority Trust
        ".*Trust default CAs.*": lambda msg: "y",
        # 15. Cluster ingress certificate
        ".*Cluster ingress certificate secret name.*": lambda msg: "",
        # 16. Domain & certificate management
        ".*Configure domain.*certificate management.*": lambda msg: "n",
        # 17. SSO properties
        ".*Configure SSO properties.*": lambda msg: "n",
        # 18. Special characters
        ".*Allow special characters for user IDs and usernames.*": lambda msg: "n",
        # 19. Guided Tour
        ".*Enable Guided Tour.*": lambda msg: "y",
        # 20. Feature adoption metrics
        ".*Enable feature adoption metrics.*": lambda msg: "y",
        # 21. Deployment progression metrics
        ".*Enable deployment progression metrics.*": lambda msg: "y",
        # 22. Usability metrics
        ".*Enable usability metrics.*": lambda msg: "y",
        # 23. Application selection
        ".*Install IoT.*": lambda msg: "n",
        ".*Install Monitor.*": lambda msg: "n",
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
        ".*Health.*": lambda msg: "n",
        ".*Health, Safety and Environment.*": lambda msg: "n",
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
        ".*Install Assist.*": lambda msg: "n",
        ".*Install Optimizer.*": lambda msg: "n",
        ".*Install Visual Inspection.*": lambda msg: "n",
        ".*Install.*Real Estate and Facilities.*": lambda msg: "n",
        ".*Install AI Service.*": lambda msg: "n",
        # 24. ArcGIS prompt (appears because Spatial is enabled)
        ".*Include IBM Maximo Location Services for Esri.*": lambda msg: "y",
        ".*Do you accept the license terms.*": lambda msg: "y",
        # 25. Grafana
        ".*Install Grafana.*": lambda msg: "y",
        # 26. MongoDB
        ".*MongoDb namespace.*": lambda msg: "mongoce",
        ".*Create MongoDb cluster.*": lambda msg: "y",
        # 27. Db2 configuration
        ".*Create system Db2 instance.*": lambda msg: "y",
        ".*Re-use System Db2 instance for Manage application.*": lambda msg: "n",
        ".*Create Manage dedicated Db2 instance.*": lambda msg: "y",
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
        # 28. Kafka
        ".*Create system Kafka instance.*": lambda msg: "y",
        ".*Kafka version.*": lambda msg: "3.8.0",
        # 29. AiCfg
        ".*Do you want to configure AiCfg.*": lambda msg: "n",
        # 30. Additional configurations
        ".*Use additional configurations.*": lambda msg: "n",
        # 31. Final confirmation
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


# Made with Bob