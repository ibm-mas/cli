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

"""
Interactive install tests for AI Service DNS configuration scenarios.

Three scenarios are covered:
  1. MAS is configured with a non-Cloudflare DNS provider (CIS) — AI Service inherits the
     same domain and derives its certificate issuer automatically.
  2. MAS is configured with Cloudflare — AI Service DNS config is skipped (description
     printed, no DNS prompts presented).
  3. MAS has no custom domain — AI Service is configured independently with CIS DNS.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mas.cli.install.catalogs import supportedCatalogs
from utils import InstallTestConfig, run_install_test


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _base_prompts(tmpdir):
    """Return the prompt handlers common to all three interactive DNS tests.

    These cover every step that runs before and after the DNS/AI Service DNS
    sections, so each test only needs to add the DNS-specific overrides.
    """
    return {
        ".*Proceed with this cluster.*": lambda msg: "y",
        ".*Show advanced installation options.*": lambda msg: "y",
        ".*Select catalog source.*": lambda msg: "v9-master-amd64",
        ".*Select channel.*": lambda msg: "9.2.x",
        ".*Use the auto-detected storage classes.*": lambda msg: "y",
        ".*SLS Mode.*": lambda msg: "1",
        ".*SLS channel.*": lambda msg: "3.x",
        ".*>License file<.*": lambda msg: f"{tmpdir}/authorized_entitlement.lic",
        ".*Contact e-mail address.*": lambda msg: "maximo@ibm.com",
        ".*Contact first name.*": lambda msg: "Test",
        ".*Contact last name.*": lambda msg: "Test",
        r".*IBM Data Reporter Operator \(DRO\) Namespace.*": lambda msg: "redhat-marketplace",
        ".*IBM entitlement key.*": lambda msg: "testEntitlementKey",
        ".*Artifactory username.*": lambda msg: "artiuser",
        ".*Artifactory token.*": lambda msg: "artipass",
        ".*Mas Admin Mode.*": lambda msg: "1",
        ".*Certificate issuer kind.*": lambda msg: "2",
        # Fires twice: once for MAS instance ID, once for AI Service instance ID
        ".*Instance ID.*": (lambda msg: "inst1", 2),
        ".*Workspace ID.*": lambda msg: "testws",
        ".*Workspace.*name.*": lambda msg: "Test Workspace",
        ".*Operational Mode.*": lambda msg: "1",
        ".*Trust default CAs.*": lambda msg: "y",
        ".*Cluster ingress certificate secret name.*": lambda msg: "",
        ".*Configure manual certificates.*": lambda msg: "n",
        ".*Routing Mode.*": lambda msg: "1",
        ".*Configure ingress namespace ownership policy to enable path-based routing for MAS.*": lambda msg: "y",
        ".*Enable OpenShift Service Mesh support for MAS.*": lambda msg: "n",
        ".*Configure SSO properties.*": lambda msg: "n",
        ".*Allow special characters for user IDs.*": lambda msg: "n",
        ".*Enable feature adoption metrics.*": lambda msg: "n",
        ".*Enable deployment progression metrics.*": lambda msg: "n",
        ".*Enable usability metrics.*": lambda msg: "n",
        ".*Enable Guided Tour.*": lambda msg: "n",
        ".*Install IoT.*": lambda msg: "n",
        ".*Install Monitor.*": lambda msg: "n",
        ".*Install Manage.*": lambda msg: "n",
        ".*Install Optimizer.*": lambda msg: "n",
        ".*Install Visual Inspection.*": lambda msg: "n",
        ".*Install.*Real Estate and Facilities.*": lambda msg: "n",
        ".*Install AI Service.*": lambda msg: "y",
        ".*Custom channel for AI Service.*": lambda msg: "9.2.x",
        ".*Customize database settings.*": lambda msg: "n",
        ".*Enter AI Service Tenant ID to bind with Manage:.*": lambda msg: "user",
        ".*Manage foundation server timezone.*": lambda msg: "GMT",
        ".*Base language.*": lambda msg: "EN",
        ".*Secondary language.*": lambda msg: "ES",
        ".*Install Minio.*": lambda msg: "y",
        ".*minio root username.*": lambda msg: "minioadmin",
        ".*minio root password.*": lambda msg: "minioadmin",
        ".*Entitlement end date.*": lambda msg: "2027-08-28",
        ".*Configure Scheduling policies for AI Service tenant.*": lambda msg: "n",
        ".*Customize the AI Service tenant operator deployment.*": lambda msg: "n",
        ".*Watsonxai api key.*": lambda msg: "testWxApiKey",
        ".*Watsonxai machine learning url.*": lambda msg: "https://us-south.ml.cloud.ibm.com",
        ".*Watsonxai project id.*": lambda msg: "testProjectId",
        ".*Does the Watsonxai AI use a self-signed certificate.*": lambda msg: "n",
        ".*Watsonxai Deployment ID.*": lambda msg: "",
        ".*Watsonxai Space ID.*": lambda msg: "",
        ".*Does the RSL API use a self-signed certificate.*": lambda msg: "n",
        ".*Create MongoDb cluster.*": lambda msg: "y",
        ".*MongoDb namespace.*": lambda msg: "mongoce",
        ".*Create Manage foundation dedicated Db2 instance using the IBM Db2 Universal Operator.*": lambda msg: "y",
        ".*Select the Manage foundation dedicated DB2 instance type.*": lambda msg: "1",
        # Fires twice: once for Manage Db2, once for AI Service Db2
        ".*Db2 License file.*": (lambda msg: "", 2),
        ".*Install namespace.*": lambda msg: "db2u",
        ".*Configure node affinity.*": lambda msg: "n",
        ".*Configure node tolerations.*": lambda msg: "n",
        ".*Customize CPU and memory request/limit.*": lambda msg: "n",
        ".*Customize storage capacity.*": lambda msg: "n",
        r".*Select Db2 Custom Resource\(CR\).*": lambda msg: "n",
        ".*Do you want to use an external database.*": lambda msg: "n",
        ".*Do you want to configure AiCfg.*": lambda msg: "n",
        ".*Install Grafana.*": lambda msg: "n",
        ".*Use additional configurations.*": lambda msg: "n",
        ".*Use pod templates.*": lambda msg: "n",
        ".*Proceed with these settings.*": lambda msg: "y",
    }


def _config(prompt_handlers, tmpdir):
    """Return an InstallTestConfig for an advanced interactive install."""
    return InstallTestConfig(
        prompt_handlers=prompt_handlers,
        current_catalog={"catalogId": supportedCatalogs["amd64"][1]},
        architecture="amd64",
        is_sno=False,
        is_airgap=False,
        storage_class_name="nfs-client",
        storage_provider="nfs",
        storage_provider_name="NFS Client",
        ocp_version="4.18.0",
        timeout_seconds=30,
        argv=['--dev-mode']
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_install_interactive_aiservice_inherits_cis_dns(tmpdir):
    """Test that AI Service inherits MAS CIS DNS config in interactive mode.

    GIVEN MAS is configured with a custom domain and CIS as the DNS provider,
        and the user confirms AI Service DNS configuration
    WHEN the install command runs interactively in advanced mode
    THEN AI Service domain is set to the MAS domain and the AI Service certificate
        issuer is derived from the MAS cluster issuer by replacing the MAS instance
        ID with the AI Service instance ID.
    """
    prompts = _base_prompts(tmpdir)

    # 13. MAS DNS section: custom domain + CIS
    prompts.update(
        {
            # Matches only the MAS DNS prompt — ends with "management?" not "management for AI Service?"
            ".*Configure domain.*certificate management\?.*": lambda msg: "y",
            ".*Configure custom domain.*": lambda msg: "y",
            ".*MAS top-level domain.*": lambda msg: "mas.example.com",
            ".*DNS Provider.*": lambda msg: "2",  # IBM Cloud Internet Services
            ".*CIS e-mail.*": lambda msg: "cis@example.com",
            ".*CIS API token.*": lambda msg: "testCisApiKey",
            ".*CIS CRN.*": lambda msg: "crn:v1:test",
            ".*CIS subdomain.*": lambda msg: "mas",
            ".*Certificate issuer.*": lambda msg: "1",  # LetsEncrypt Production
            ".*Configure enhanced security for CIS.*": lambda msg: "n",
            ".*Cluster Ingress Domain Override.*": lambda msg: "",
            # 18. AI Service DNS: user opts in; MAS domain/CIS already set → inherited automatically
            ".*Configure.*domain.*certificate management for AI Service.*": lambda msg: "y",
        }
    )

    app = run_install_test(tmpdir, _config(prompts, tmpdir))

    assert app.getParam("dns_provider") == "cis"
    assert app.getParam("mas_domain") == "mas.example.com"
    assert app.getParam("aiservice_domain") == "mas.example.com"
    # cert issuer: inst1-cis-le-prod → inst2 not set so replace inst1 with aiservice_instance_id
    assert app.getParam("mas_cluster_issuer") == "inst1-cis-le-prod"
    assert app.getParam("aiservice_certificate_issuer") == "inst1-cis-le-prod"


def test_install_interactive_aiservice_cloudflare_dns_skipped(tmpdir):
    """Test that AI Service DNS configuration is skipped when MAS uses Cloudflare.

    GIVEN MAS is configured with Cloudflare as the DNS provider,
        and the user confirms AI Service DNS configuration
    WHEN the install command runs interactively in advanced mode
    THEN the CLI prints a description explaining Cloudflare is unsupported for AI Service
        and leaves aiservice_domain and aiservice_certificate_issuer empty.
    """
    prompts = _base_prompts(tmpdir)

    # 13. MAS DNS section: custom domain + Cloudflare
    prompts.update(
        {
            # Matches only the MAS DNS prompt — ends with "management?" not "management for AI Service?"
            ".*Configure domain.*certificate management\?.*": lambda msg: "y",
            ".*Configure custom domain.*": lambda msg: "y",
            ".*MAS top-level domain.*": lambda msg: "mas.example.com",
            ".*DNS Provider.*": lambda msg: "1",  # Cloudflare
            ".*Cloudflare e-mail.*": lambda msg: "cf@example.com",
            ".*Cloudflare API token.*": lambda msg: "testCfToken",
            ".*Cloudflare zone.*": lambda msg: "example.com",
            ".*Cloudflare subdomain.*": lambda msg: "mas",
            ".*Certificate issuer.*": lambda msg: "1",  # LetsEncrypt Production
            ".*Cluster Ingress Domain Override.*": lambda msg: "",
            # 18. AI Service DNS: user opts in; MAS provider is cloudflare → description printed, no DNS sub-prompts
            ".*Configure.*domain.*certificate management for AI Service.*": lambda msg: "y",
        }
    )

    app = run_install_test(tmpdir, _config(prompts, tmpdir))

    assert app.getParam("dns_provider") == "cloudflare"
    assert app.getParam("mas_domain") == "mas.example.com"
    assert app.getParam("aiservice_domain") == ""
    assert app.getParam("aiservice_certificate_issuer") == ""


def test_install_interactive_aiservice_cis_dns_no_mas_domain(tmpdir):
    """Test that AI Service can configure CIS DNS independently when MAS has no custom domain.

    GIVEN MAS is NOT configured with a custom domain (user answers n to Configure custom domain),
        and the user opts in to AI Service DNS configuration
    WHEN the install command runs interactively in advanced mode
    THEN the CLI prompts for the AI Service domain and DNS provider independently,
        and the AI Service certificate issuer is set from the CIS LetsEncrypt issuer.
    """
    prompts = _base_prompts(tmpdir)

    # 13. MAS DNS section: no custom domain
    prompts.update(
        {
            # Matches only the MAS DNS prompt — ends with "management?" not "management for AI Service?"
            ".*Configure domain.*certificate management\?.*": lambda msg: "y",
            ".*Configure custom domain.*": lambda msg: "n",
            # 18. AI Service DNS: MAS has no domain → full independent DNS flow
            ".*Configure.*domain.*certificate management for AI Service.*": lambda msg: "y",
            ".*AI Service domain.*": lambda msg: "aiservice.example.com",
            ".*DNS Provider.*": lambda msg: "1",  # IBM Cloud Internet Services (first in the AI Service list)
            ".*CIS e-mail.*": lambda msg: "cis@example.com",
            ".*CIS API token.*": lambda msg: "testCisApiKey",
            ".*CIS CRN.*": lambda msg: "crn:v1:test",
            ".*CIS subdomain.*": lambda msg: "aiservice",
            ".*Certificate issuer.*": lambda msg: "1",  # LetsEncrypt Production
            ".*Configure enhanced security for CIS.*": lambda msg: "n",
            ".*Cluster Ingress Domain Override.*": lambda msg: "",
        }
    )

    app = run_install_test(tmpdir, _config(prompts, tmpdir))

    assert app.getParam("dns_provider") == "cis"
    assert app.getParam("mas_domain") == ""
    assert app.getParam("aiservice_domain") == "aiservice.example.com"
    assert app.getParam("aiservice_certificate_issuer") == f"{app.getParam('aiservice_instance_id')}-cis-le-prod"
