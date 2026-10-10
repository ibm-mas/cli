# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Integration tests for McpiInstallApp non-interactive mode.

Tests verify that the CLI correctly collects parameters and launches the
Tekton MCPI install pipeline.
"""

from unittest import mock
from unittest.mock import MagicMock

from kubernetes.dynamic import DynamicClient
from kubernetes.dynamic.exceptions import NotFoundError
from kubernetes.client.exceptions import ApiException

from mas.cli.mcpi.install.app import McpiInstallApp


def test_install_noninteractive(tmpdir):
    """Test full non-interactive MCPI install completes without error.

    GIVEN all required CLI flags are provided (mas-catalog-version, ibm-entitlement-key,
          mas-instance-id, storage classes, license-file, contact details, mcpi-channel)
    WHEN McpiInstallApp.install() is called with those flags and --no-confirm
    THEN launchMcpiInstallPipeline is called exactly once and returns without error.
    """
    tmpdir.join("authorized_entitlement.lic").write("testLicense")

    with mock.patch("mas.cli.cli.config"):
        dynamicClient = MagicMock(DynamicClient)
        resources = MagicMock()
        dynamicClient.resources = resources

        routesApi = MagicMock()
        catalogApi = MagicMock()
        crdApi = MagicMock()
        namespaceApi = MagicMock()
        clusterRoleBindingApi = MagicMock()
        pvcApi = MagicMock()
        secretApi = MagicMock()

        resourceApis = {
            "CatalogSource": catalogApi,
            "Route": routesApi,
            "CustomResourceDefinition": crdApi,
            "Namespace": namespaceApi,
            "ClusterRoleBinding": clusterRoleBindingApi,
            "PersistentVolumeClaim": pvcApi,
            "Secret": secretApi,
        }
        resources.get.side_effect = lambda **kwargs: resourceApis.get(kwargs["kind"], None)

        route = MagicMock()
        route.spec = MagicMock()
        route.spec.host = "maximo.ibm.com"
        routesApi.get.return_value = route
        catalogApi.get.side_effect = NotFoundError(ApiException(status="404"))

        with (
            mock.patch("mas.cli.cli.DynamicClient") as mockDynamicClientClass,
            mock.patch("mas.cli.cli.getNodes") as mockGetNodes,
            mock.patch("mas.cli.cli.isAirgapInstall") as mockIsAirgapInstall,
            mock.patch("mas.cli.mcpi.install.app.installOpenShiftPipelines"),
            mock.patch("mas.cli.mcpi.install.app.updateTektonDefinitions"),
            mock.patch("mas.cli.mcpi.install.app.prepareMcpiPipelinesNamespace"),
            mock.patch("mas.cli.mcpi.install.app.prepareInstallSecrets"),
            mock.patch("mas.cli.mcpi.install.app.testCLI"),
            mock.patch("mas.cli.mcpi.install.app.launchMcpiInstallPipeline") as mockLaunchPipeline,
        ):
            mockDynamicClientClass.return_value = dynamicClient
            mockGetNodes.return_value = [{"status": {"nodeInfo": {"architecture": "amd64"}}}]
            mockIsAirgapInstall.return_value = False
            mockLaunchPipeline.return_value = "https://pipeline.test.maximo.ibm.com"

            with mock.patch("mas.cli.cli.isSNO") as mockIsSno:
                mockIsSno.return_value = False
                app = McpiInstallApp()
                app.install(
                    [
                        "--mas-catalog-version",
                        "v9-250828-amd64",
                        "--ibm-entitlement-key",
                        "testEntitlementKey",
                        "--mas-instance-id",
                        "test1",
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
                        "User",
                        "--mcpi-channel",
                        "v9.2",
                        "--accept-license",
                        "--no-confirm",
                    ]
                )

                mockLaunchPipeline.assert_called_once()
