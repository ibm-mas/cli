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

from unittest import mock
from unittest.mock import MagicMock
from kubernetes.client.rest import ApiException
from kubernetes.dynamic import DynamicClient
from kubernetes.dynamic.exceptions import NotFoundError
from mas.cli.install.catalogs import supportedCatalogs
from mas.cli.install.app import InstallApp


def test_install_noninteractive_cis_enhanced_security(tmpdir):
    """Test non-interactive integrated install with CIS enhanced security options.

    GIVEN a complete set of CLI arguments for the MAS+AI Service integrated install
        including CIS enhanced security flags
    WHEN the install command runs in non-interactive mode
    THEN all CIS enhanced security parameters are stored correctly in the pipeline params.
    """
    tmpdir.join("authorized_entitlement.lic").write("testLicense")
    with mock.patch("mas.cli.cli.config"):
        dynamic_client = MagicMock(DynamicClient)
        resources = MagicMock()
        dynamic_client.resources = resources
        dynamic_client.client = MagicMock()

        routes_api = MagicMock()
        catalog_api = MagicMock()
        crd_api = MagicMock()
        namespace_api = MagicMock()
        cluster_role_binding_api = MagicMock()
        pvc_api = MagicMock()
        configmap_api = MagicMock()
        secret_api = MagicMock()
        storage_class_api = MagicMock()
        service_api = MagicMock()
        cluster_version_api = MagicMock()
        ingress_controller_api = MagicMock()

        resource_apis = {
            "CatalogSource": catalog_api,
            "Route": routes_api,
            "CustomResourceDefinition": crd_api,
            "Namespace": namespace_api,
            "ClusterRoleBinding": cluster_role_binding_api,
            "PersistentVolumeClaim": pvc_api,
            "ConfigMap": configmap_api,
            "Secret": secret_api,
            "StorageClass": storage_class_api,
            "Service": service_api,
            "ClusterVersion": cluster_version_api,
            "IngressController": ingress_controller_api,
        }
        resources.get.side_effect = lambda **kwargs: resource_apis.get(kwargs["kind"], None)

        route = MagicMock()
        route.spec = MagicMock()
        route.spec.host = "maximo.ibm.com"
        route.spec.displayName = supportedCatalogs["amd64"][1]
        routes_api.get.return_value = route
        catalog_api.get.side_effect = NotFoundError(ApiException(status="404"))

        image_registry_service = MagicMock()
        image_registry_service.metadata = MagicMock()
        image_registry_service.metadata.name = "image-registry"
        service_api.get.return_value = image_registry_service

        cluster_version = MagicMock()
        cluster_version.status = MagicMock()
        history_record = MagicMock()
        history_record.state = "Completed"
        history_record.version = "4.18.0"
        cluster_version.status.history = [history_record]
        cluster_version_api.get.return_value = cluster_version

        ingress_controller = MagicMock()
        ingress_controller.metadata = MagicMock()
        ingress_controller.metadata.name = "default"
        ingress_controller.status = MagicMock()
        ingress_controller.status.domain = "apps.cluster.example.com"
        ingress_controller.status.conditions = [MagicMock(type="Available", status="True")]
        ingress_controller.spec = MagicMock()
        ingress_controller.spec.routeAdmission = MagicMock()
        ingress_controller.spec.routeAdmission.namespaceOwnership = "Strict"
        ingress_controller_api.get.return_value = ingress_controller
        ingress_controller_api.patch = MagicMock(return_value=ingress_controller)

        with (
            mock.patch("mas.cli.cli.DynamicClient") as dynamic_client_class,
            mock.patch("mas.cli.cli.getNodes") as get_nodes,
            mock.patch("mas.cli.cli.isAirgapInstall") as is_airgap_install,
            mock.patch("mas.cli.install.app.getCurrentCatalog") as get_current_catalog,
            mock.patch("mas.cli.install.app.installOpenShiftPipelines"),
            mock.patch("mas.cli.install.app.updateTektonDefinitions"),
            mock.patch("mas.cli.install.app.preparePipelinesNamespace"),
            mock.patch("mas.cli.install.app.createNamespace"),
            mock.patch("mas.cli.install.app.configureIngressForPathBasedRouting"),
            mock.patch("mas.cli.install.app.launchInstallPipeline") as launch_install_pipeline,
            mock.patch("mas.cli.cli.isSNO") as is_sno,
        ):
            dynamic_client_class.return_value = dynamic_client
            get_nodes.return_value = [{"status": {"nodeInfo": {"architecture": "amd64"}}}]
            is_airgap_install.return_value = False
            get_current_catalog.return_value = {"catalogId": supportedCatalogs["amd64"][1]}
            launch_install_pipeline.return_value = "https://pipeline.test.maximo.ibm.com"
            is_sno.return_value = False

            app = InstallApp()
            app.install(
                [
                    "--mas-catalog-version",
                    "v9-250828-amd64",
                    "--ibm-entitlement-key",
                    "testEntitlementKey",
                    "--mas-instance-id",
                    "testinst",
                    "--mas-workspace-id",
                    "testws",
                    "--mas-workspace-name",
                    "Test Workspace",
                    "--mas-channel",
                    "9.1.x",
                    "--storage-class-rwo",
                    "nfs-client",
                    "--storage-class-rwx",
                    "nfs-client",
                    "--storage-pipeline",
                    "nfs-client",
                    "--storage-accessmode",
                    "ReadWriteMany",
                    "--license-file",
                    f"{tmpdir}/authorized_entitlement.lic",
                    "--contact-email",
                    "maximo@ibm.com",
                    "--contact-firstname",
                    "Test",
                    "--contact-lastname",
                    "Test",
                    "--domain",
                    "mas.example.com",
                    "--dns-provider",
                    "cis",
                    "--cis-email",
                    "cis@example.com",
                    "--cis-apikey",
                    "testCisApiKey",
                    "--cis-crn",
                    "crn:v1:test",
                    "--cis-subdomain",
                    "mas",
                    "--cis-service-name",
                    "test-cis-service",
                    "--cis-enhanced-security",
                    "--update-dns-entries",
                    "--cis-waf",
                    "--delete-wildcards",
                    "--override-edge-certs",
                    "--accept-license",
                    "--no-confirm",
                    "--skip-pre-check",
                ]
            )

            assert app.getParam("dns_provider") == "cis"
            assert app.getParam("cis_enhanced_security") == "true"
            assert app.getParam("cis_service_name") == "test-cis-service"
            assert app.getParam("update_dns_entries") == "true"
            assert app.getParam("cis_waf") == "true"
            assert app.getParam("cis_proxy") == "false"
            assert app.getParam("delete_wildcards") == "true"
            assert app.getParam("override_edge_certs") == "true"


def _make_install_app_mocks(tmpdir, dynamic_client):
    """Create the standard set of mock API objects for InstallApp tests."""
    resources = MagicMock()
    dynamic_client.resources = resources
    dynamic_client.client = MagicMock()

    routes_api = MagicMock()
    catalog_api = MagicMock()
    crd_api = MagicMock()
    namespace_api = MagicMock()
    cluster_role_binding_api = MagicMock()
    pvc_api = MagicMock()
    configmap_api = MagicMock()
    secret_api = MagicMock()
    storage_class_api = MagicMock()
    service_api = MagicMock()
    cluster_version_api = MagicMock()
    ingress_controller_api = MagicMock()

    resource_apis = {
        "CatalogSource": catalog_api,
        "Route": routes_api,
        "CustomResourceDefinition": crd_api,
        "Namespace": namespace_api,
        "ClusterRoleBinding": cluster_role_binding_api,
        "PersistentVolumeClaim": pvc_api,
        "ConfigMap": configmap_api,
        "Secret": secret_api,
        "StorageClass": storage_class_api,
        "Service": service_api,
        "ClusterVersion": cluster_version_api,
        "IngressController": ingress_controller_api,
    }
    resources.get.side_effect = lambda **kwargs: resource_apis.get(kwargs["kind"], None)

    route = MagicMock()
    route.spec = MagicMock()
    route.spec.host = "maximo.ibm.com"
    route.spec.displayName = supportedCatalogs["amd64"][1]
    routes_api.get.return_value = route
    catalog_api.get.side_effect = NotFoundError(ApiException(status="404"))

    image_registry_service = MagicMock()
    image_registry_service.metadata = MagicMock()
    image_registry_service.metadata.name = "image-registry"
    service_api.get.return_value = image_registry_service

    cluster_version = MagicMock()
    cluster_version.status = MagicMock()
    history_record = MagicMock()
    history_record.state = "Completed"
    history_record.version = "4.18.0"
    cluster_version.status.history = [history_record]
    cluster_version_api.get.return_value = cluster_version

    ingress_controller = MagicMock()
    ingress_controller.metadata = MagicMock()
    ingress_controller.metadata.name = "default"
    ingress_controller.status = MagicMock()
    ingress_controller.status.domain = "apps.cluster.example.com"
    ingress_controller.status.conditions = [MagicMock(type="Available", status="True")]
    ingress_controller.spec = MagicMock()
    ingress_controller.spec.routeAdmission = MagicMock()
    ingress_controller.spec.routeAdmission.namespaceOwnership = "Strict"
    ingress_controller_api.get.return_value = ingress_controller
    ingress_controller_api.patch = MagicMock(return_value=ingress_controller)

    tmpdir.join("authorized_entitlement.lic").write("testLicense")


_BASE_MAS_AISERVICE_ARGS = [
    "--mas-catalog-version",
    "v9-250828-amd64",
    "--ibm-entitlement-key",
    "testEntitlementKey",
    "--mas-instance-id",
    "inst1",
    "--mas-workspace-id",
    "testws",
    "--mas-workspace-name",
    "Test Workspace",
    "--mas-channel",
    "9.1.x",
    "--aiservice-instance-id",
    "inst2",
    "--aiservice-channel",
    "9.1.x",
    "--storage-class-rwo",
    "nfs-client",
    "--storage-class-rwx",
    "nfs-client",
    "--storage-pipeline",
    "nfs-client",
    "--storage-accessmode",
    "ReadWriteMany",
    "--contact-email",
    "maximo@ibm.com",
    "--contact-firstname",
    "Test",
    "--contact-lastname",
    "Test",
    "--install-minio",
    "--minio-root-user",
    "minioadmin",
    "--minio-root-password",
    "minioadmin",
    "--watsonxai-apikey",
    "testKey",
    "--watsonxai-url",
    "https://us-south.ml.cloud.ibm.com",
    "--watsonxai-project-id",
    "testProjectId",
    "--tenant-entitlement-type",
    "standard",
    "--tenant-entitlement-start-date",
    "2025-08-28",
    "--tenant-entitlement-end-date",
    "2026-08-28",
    "--accept-license",
    "--no-confirm",
    "--skip-pre-check",
]


def _run_install_app(tmpdir, extra_args):
    """Run InstallApp.install with standard mocks and return the app instance."""
    with mock.patch("mas.cli.cli.config"):
        dynamic_client = MagicMock(DynamicClient)
        _make_install_app_mocks(tmpdir, dynamic_client)
        with (
            mock.patch("mas.cli.cli.DynamicClient") as dynamic_client_class,
            mock.patch("mas.cli.cli.getNodes") as get_nodes,
            mock.patch("mas.cli.cli.isAirgapInstall") as is_airgap_install,
            mock.patch("mas.cli.install.app.getCurrentCatalog") as get_current_catalog,
            mock.patch("mas.cli.install.app.installOpenShiftPipelines"),
            mock.patch("mas.cli.install.app.updateTektonDefinitions"),
            mock.patch("mas.cli.install.app.preparePipelinesNamespace"),
            mock.patch("mas.cli.install.app.createNamespace"),
            mock.patch("mas.cli.install.app.configureIngressForPathBasedRouting"),
            mock.patch("mas.cli.install.app.launchInstallPipeline") as launch_install_pipeline,
            mock.patch("mas.cli.cli.isSNO") as is_sno,
        ):
            dynamic_client_class.return_value = dynamic_client
            get_nodes.return_value = [{"status": {"nodeInfo": {"architecture": "amd64"}}}]
            is_airgap_install.return_value = False
            get_current_catalog.return_value = {"catalogId": supportedCatalogs["amd64"][1]}
            launch_install_pipeline.return_value = "https://pipeline.test.maximo.ibm.com"
            is_sno.return_value = False

            app = InstallApp()
            license_args = ["--license-file", f"{tmpdir}/authorized_entitlement.lic"]
            app.install(_BASE_MAS_AISERVICE_ARGS + license_args + extra_args)
            return app


def test_install_noninteractive_aiservice_cis_dns(tmpdir):
    """Test that AI Service inherits CIS DNS config and derives its certificate issuer from MAS.

    GIVEN --domain and --dns-provider cis are set for MAS, --mas-cluster-issuer is inst1-cis-le-prod,
        and AI Service instance ID is inst2
    WHEN the install command runs in non-interactive mode
    THEN AI Service domain equals the MAS domain and the AI Service certificate issuer is
        derived from mas_cluster_issuer by replacing the MAS instance ID with the AI Service instance ID.
    """
    app = _run_install_app(
        tmpdir,
        [
            "--domain",
            "mas.example.com",
            "--dns-provider",
            "cis",
            "--cis-email",
            "cis@example.com",
            "--cis-apikey",
            "testCisApiKey",
            "--cis-crn",
            "crn:v1:test",
            "--cis-subdomain",
            "mas",
            "--mas-cluster-issuer",
            "inst1-cis-le-prod",
        ],
    )

    assert app.getParam("dns_provider") == "cis"
    assert app.getParam("mas_domain") == "mas.example.com"
    assert app.getParam("aiservice_domain") == "mas.example.com"
    assert app.getParam("mas_cluster_issuer") == "inst1-cis-le-prod"
    assert app.getParam("aiservice_certificate_issuer") == "inst2-cis-le-prod"


def test_install_noninteractive_aiservice_route53_dns(tmpdir):
    """Test that AI Service inherits Route53 DNS config and derives its certificate issuer from MAS.

    GIVEN --domain and --dns-provider route53 are set for MAS, --mas-cluster-issuer is inst1-route53-le-prod,
        and AI Service instance ID is inst2
    WHEN the install command runs in non-interactive mode
    THEN AI Service domain equals the MAS domain and the AI Service certificate issuer is
        derived from mas_cluster_issuer by replacing the MAS instance ID with the AI Service instance ID.
    """
    app = _run_install_app(
        tmpdir,
        [
            "--domain",
            "mas.example.com",
            "--dns-provider",
            "route53",
            "--aws-access-key-id",
            "testAwsKeyId",
            "--aws-secret-access-key",
            "testAwsSecretKey",
            "--route53-hosted-zone-name",
            "example.com",
            "--route53-hosted-zone-region",
            "us-east-1",
            "--route53-subdomain",
            "mas",
            "--route53-email",
            "route53@example.com",
            "--mas-cluster-issuer",
            "inst1-route53-le-prod",
        ],
    )

    assert app.getParam("dns_provider") == "route53"
    assert app.getParam("mas_domain") == "mas.example.com"
    assert app.getParam("aiservice_domain") == "mas.example.com"
    assert app.getParam("mas_cluster_issuer") == "inst1-route53-le-prod"
    assert app.getParam("aiservice_certificate_issuer") == "inst2-route53-le-prod"


def test_install_noninteractive_aiservice_cloudflare_dns_skipped(tmpdir):
    """Test that AI Service DNS configuration is skipped when MAS uses Cloudflare.

    GIVEN --domain and --dns-provider cloudflare are set for MAS and AI Service instance ID is inst2
    WHEN the install command runs in non-interactive mode
    THEN AI Service domain and certificate issuer are cleared because Cloudflare is not supported
        for AI Service DNS configuration.
    """
    app = _run_install_app(
        tmpdir,
        [
            "--domain",
            "mas.example.com",
            "--dns-provider",
            "cloudflare",
            "--cloudflare-email",
            "cf@example.com",
            "--cloudflare-apitoken",
            "testCfToken",
            "--cloudflare-zone",
            "example.com",
            "--cloudflare-subdomain",
            "mas",
            "--mas-cluster-issuer",
            "inst1-cloudflare-le-prod",
        ],
    )

    assert app.getParam("dns_provider") == "cloudflare"
    assert app.getParam("mas_domain") == "mas.example.com"
    assert app.getParam("aiservice_domain") == ""
    assert app.getParam("aiservice_certificate_issuer") == ""


def test_install_noninteractive_domain_shared_with_aiservice(tmpdir):
    """Test that --domain is used for both MAS and AI Service in non-interactive mode.

    GIVEN --domain mas.example.com and CIS DNS provider are set, and AI Service is being installed
    WHEN the install command runs in non-interactive mode
    THEN both MAS and AI Service are configured with the same domain.
    """
    app = _run_install_app(
        tmpdir,
        [
            "--domain",
            "mas.example.com",
            "--dns-provider",
            "cis",
            "--cis-email",
            "cis@example.com",
            "--cis-apikey",
            "testCisApiKey",
            "--cis-crn",
            "crn:v1:test",
            "--cis-subdomain",
            "mas",
            "--mas-cluster-issuer",
            "inst1-cis-le-prod",
        ],
    )

    assert app.getParam("mas_domain") == "mas.example.com"
    assert app.getParam("aiservice_domain") == app.getParam("mas_domain")


def test_install_noninteractive_aiservice_cloudflare_no_dns_args(tmpdir):
    """Test that AI Service DNS is skipped in non-interactive mode when Cloudflare is configured.

    GIVEN --dns-provider cloudflare is set for MAS (no --mas-cluster-issuer provided)
        and AI Service instance ID is inst2
    WHEN the install command runs in non-interactive mode
    THEN AI Service domain and certificate issuer are both empty.
    """
    app = _run_install_app(
        tmpdir,
        [
            "--domain",
            "mas.example.com",
            "--dns-provider",
            "cloudflare",
            "--cloudflare-email",
            "cf@example.com",
            "--cloudflare-apitoken",
            "testCfToken",
            "--cloudflare-zone",
            "example.com",
            "--cloudflare-subdomain",
            "mas",
        ],
    )

    assert app.getParam("dns_provider") == "cloudflare"
    assert app.getParam("aiservice_domain") == ""
    assert app.getParam("aiservice_certificate_issuer") == ""
