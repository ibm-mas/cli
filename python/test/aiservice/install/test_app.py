#!/usr/bin/env python
# *****************************************************************************
# Copyright (c) 2024, 2025 IBM Corporation and other Contributors.
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
from openshift.dynamic import DynamicClient
from openshift.dynamic.exceptions import NotFoundError
from mas.cli.install.catalogs import supportedCatalogs
from mas.cli.aiservice.install.app import AiServiceInstallApp


def test_install_noninteractive(tmpdir):
    tmpdir.join('authorized_entitlement.lic').write('testLicense')
    with mock.patch('mas.cli.cli.config'):
        dynamic_client = MagicMock(DynamicClient)
        resources = MagicMock()
        dynamic_client.resources = resources
        routes_api = MagicMock()
        catalog_api = MagicMock()
        crd_api = MagicMock()
        namespace_api = MagicMock()
        cluster_role_binding_api = MagicMock()
        pvc_api = MagicMock()
        secret_api = MagicMock()
        resource_apis = {'CatalogSource': catalog_api, 'Route': routes_api, 'CustomResourceDefinition': crd_api, 'Namespace': namespace_api,
                         'ClusterRoleBinding': cluster_role_binding_api, 'PersistentVolumeClaim': pvc_api, 'Secret': secret_api}
        resources.get.side_effect = lambda **kwargs: resource_apis.get(kwargs['kind'], None)
        route = MagicMock()
        route.spec = MagicMock()
        route.spec.host = 'maximo.ibm.com'
        route.spec.displayName = supportedCatalogs['amd64'][1]
        routes_api.get.return_value = route
        catalog_api.get.side_effect = NotFoundError(ApiException(status='404'))
        with mock.patch('mas.cli.cli.DynamicClient') as dynamic_client_class:
            dynamic_client_class.return_value = dynamic_client
            with mock.patch('mas.cli.cli.getNodes') as get_nodes:
                get_nodes.return_value = [{'status': {'nodeInfo': {'architecture': 'amd64'}}}]
                with mock.patch('mas.cli.cli.isAirgapInstall') as is_airgap_install:
                    is_airgap_install.return_value = False
                    with mock.patch('mas.cli.aiservice.install.app.getCurrentCatalog') as get_current_catalog:
                        get_current_catalog.return_value = {'catalogId': supportedCatalogs['amd64'][1]}
                        with mock.patch('mas.cli.aiservice.install.app.updateTektonDefinitions'):
                            with mock.patch('mas.cli.aiservice.install.app.launchAiServiceInstallPipeline') as launch_ai_service_install_pipeline:
                                launch_ai_service_install_pipeline.return_value = 'https://pipeline.test.maximo.ibm.com'
                                with mock.patch('mas.cli.cli.isSNO') as is_sno:
                                    is_sno.return_value = False
                                    app = AiServiceInstallApp()
                                    app.install(['--mas-catalog-version', 'v9-250828-amd64',
                                                 '--ibm-entitlement-key', 'testEntitlementKey',
                                                 '--aiservice-instance-id', 'testInstanceId',
                                                 '--storage-class-rwo', 'nfs-client',
                                                 '--storage-class-rwx', 'nfs-client',
                                                 '--storage-pipeline', 'nfs-client',
                                                 '--storage-accessmode', 'ReadWriteMany',
                                                 '--license-file', f'{tmpdir}/authorized_entitlement.lic',
                                                 '--uds-email', 'maximo@ibm.com',
                                                 '--uds-firstname', 'Test',
                                                 '--uds-lastname', 'Test',
                                                 '--dro-namespace', 'redhat-marketplace',
                                                 '--mongodb-namespace', 'mongoce',
                                                 '--aiservice-channel', '9.1.x',
                                                 '--s3-accesskey', 'test',
                                                 '--s3-secretkey', 'test',
                                                 '--s3-host', 'minio-service.minio.svc.cluster.local',
                                                 '--s3-port', '9000',
                                                 '--s3-ssl', 'false',
                                                 '--s3-region', 'none',
                                                 '--s3-bucket-prefix', 'aiservice',
                                                 '--s3-tenants-bucket', 'km-tenants',
                                                 '--s3-templates-bucket', 'km-templates',
                                                 '--watsonxai-apikey', 'test',
                                                 '--watsonxai-url', 'https://us-south.ml.cloud.ibm.com',
                                                 '--watsonxai-project-id', 'test',
                                                 '--minio-root-user', 'test',
                                                 '--minio-root-password', 'test',
                                                 '--tenant-entitlement-type', 'standard',
                                                 '--tenant-entitlement-start-date', '2025-08-28',
                                                 '--tenant-entitlement-end-date', '2026-08-28',
                                                 '--rsl-url', 'https:/test.rsl.maximo.ibm.com/api/v3/vector/query',
                                                 '--rsl-org-id', 'testOrgId',
                                                 '--rsl-token', 'testRslToken',
                                                 '--rsl-ca-crt', 'testRslCaCert',
                                                 '--accept-license', '--no-confirm',
                                                 '--skip-pre-check'])
