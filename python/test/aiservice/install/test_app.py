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

import re
from unittest import mock
from unittest.mock import MagicMock
from kubernetes.client.rest import ApiException
from openshift.dynamic import DynamicClient
from openshift.dynamic.exceptions import NotFoundError
from mas.cli.install.catalogs import supportedCatalogs
from mas.cli.aiservice.install.app import AiServiceInstallApp

# These tests do not cover all possible combinations of install parameters. They are a starting point.
# Future improvements should look at generating all possible permutations of the install parameters
# and passing to a set of parameterized tests to increase scenario coverage.


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
        with (
            mock.patch('mas.cli.cli.DynamicClient') as dynamic_client_class,
            mock.patch('mas.cli.cli.getNodes') as get_nodes,
            mock.patch('mas.cli.cli.isAirgapInstall') as is_airgap_install,
            mock.patch('mas.cli.aiservice.install.app.getCurrentCatalog') as get_current_catalog,
            mock.patch('mas.cli.aiservice.install.app.installOpenShiftPipelines'),
            mock.patch('mas.cli.aiservice.install.app.updateTektonDefinitions'),
            mock.patch('mas.cli.aiservice.install.app.prepareAiServicePipelinesNamespace'),
            mock.patch('mas.cli.aiservice.install.app.launchInstallPipeline') as launch_ai_service_install_pipeline
        ):
            dynamic_client_class.return_value = dynamic_client
            get_nodes.return_value = [{'status': {'nodeInfo': {'architecture': 'amd64'}}}]
            is_airgap_install.return_value = False
            get_current_catalog.return_value = {'catalogId': supportedCatalogs['amd64'][1]}
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
                             '--contact-email', 'maximo@ibm.com',
                             '--contact-firstname', 'Test',
                             '--contact-lastname', 'Test',
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
                             '--watsonxai-ca-crt', 'testWxCaCrt',
                             '--watsonxai-deployment-id', 'testDeploymentId',
                             '--watsonxai-space-id', 'testSpaceId',
                             '--watsonxai-instance-id', 'testWxInstanceId',
                             '--watsonxai-username', 'testWxUsername',
                             '--watsonxai-version', 'testWxVersion',
                             '--watsonxai-onprem', 'testWxonprem',
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


def test_install_interactive_advanced(tmpdir):
    tmpdir.join('authorized_entitlement.lic').write('testLicense')
    tmpdir.join('mongodb-system.yaml').write('#')
    tmpdir.join('cert.crt').write('#')
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
        storage_class_api = MagicMock()
        license_api = MagicMock()
        resource_apis = {'CatalogSource': catalog_api, 'Route': routes_api, 'CustomResourceDefinition': crd_api, 'Namespace': namespace_api,
                         'ClusterRoleBinding': cluster_role_binding_api, 'PersistentVolumeClaim': pvc_api, 'Secret': secret_api,
                         'StorageClass': storage_class_api, 'LicenseService': license_api}
        resources.get.side_effect = lambda **kwargs: resource_apis.get(kwargs['kind'], None)
        route = MagicMock()
        route.spec = MagicMock()
        route.spec.host = 'maximo.ibm.com'
        route.spec.displayName = supportedCatalogs['amd64'][1]
        routes_api.get.return_value = route
        catalog_api.get.side_effect = NotFoundError(ApiException(status='404'))
        with (
            mock.patch('mas.cli.cli.DynamicClient') as dynamic_client_class,
            mock.patch('mas.cli.cli.getNodes') as get_nodes,
            mock.patch('mas.cli.cli.isAirgapInstall') as is_airgap_install,
            mock.patch('mas.cli.aiservice.install.app.getCurrentCatalog') as get_current_catalog,
            mock.patch('mas.cli.aiservice.install.app.installOpenShiftPipelines'),
            mock.patch('mas.cli.aiservice.install.app.updateTektonDefinitions'),
            mock.patch('mas.cli.aiservice.install.app.prepareAiServicePipelinesNamespace'),
            mock.patch('mas.cli.aiservice.install.app.launchInstallPipeline') as launch_ai_service_install_pipeline,
            mock.patch('mas.cli.cli.isSNO') as is_sno,
            mock.patch('mas.cli.displayMixins.prompt') as mixins_prompt,
            mock.patch('mas.cli.aiservice.install.app.prompt') as app_prompt,
            mock.patch('mas.cli.aiservice.install.app.getStorageClasses') as get_storage_classes
        ):
            dynamic_client_class.return_value = dynamic_client
            get_nodes.return_value = [{'status': {'nodeInfo': {'architecture': 'amd64'}}}]
            is_airgap_install.return_value = False
            get_current_catalog.return_value = {'catalogId': supportedCatalogs['amd64'][1]}
            launch_ai_service_install_pipeline.return_value = 'https://pipeline.test.maximo.ibm.com'
            is_sno.return_value = False

            def set_mixin_prompt_input(**kwargs):
                message = str(kwargs['message'])
                if re.match('.*Proceed with this cluster?.*', message):
                    return 'y'
                if re.match('.*Show advanced installation options?.*', message):
                    return 'y'
                if re.match('.*Do you accept the license terms?.*', message):
                    return 'y'
                if re.match('.*ReadWriteOnce (RWO) storage class.*', message):
                    return 'nfs-client'
                if re.match('.*ReadWriteMany (RWX) storage class.*', message):
                    return 'nfs-client'
                if re.match('.*SLS Mode.*', message):
                    return '1'
                if re.match('.*License file.*', message):
                    return f'{tmpdir}/authorized_entitlement.lic'
                if re.match('.*Instance ID.*', message):
                    return 'apmdevops'
                if re.match('.*Operational Mode.*', message):
                    return '1'
                if re.match('.*Install Minio.*', message):
                    return 'y'
                if re.match('.*minio root username.*', message):
                    return 'username'
                if re.match('.*minio root password.*', message):
                    return 'password'
                if re.match('.*Configure certificate issuer?.*', message):
                    return 'y'
                if re.match('.*Certificate issuer name.*', message):
                    return 'cert-issuer'
                if re.match('.*RSL url.*', message):
                    return 'https://rls.maximo.test.ibm.com'
                if re.match('.*ORG Id of RSL.*', message):
                    return 'rslOrgId'
                if re.match('.*Token for RSL.*', message):
                    return 'rslToken'
                if re.match('.*Watsonxai machine learning url.*', message):
                    return 'watsonxUrl'
                if re.match('.*Does the RSL API use a self-signed certificate.*', message):
                    return 'n'
                if re.match('.*Does the Watsonxai AI use a self-signed certificate.*', message):
                    return 'n'
                if re.match('.*Create MongoDb cluster.*', message):
                    return 'n'
                if re.match('.*Select Local configuration directory.*', message):
                    return str(tmpdir)
                if re.match('.*MongoDb Username.*', message):
                    return 'mongodbUser'
                if re.match('.*MongoDb Password.*', message):
                    return 'mongodbPassword'
                if re.match('.*Path to certificate file.*', message):
                    return f'{tmpdir}/cert.crt'
                if re.match(".*System mongodb configuration file 'mongodb-system.yaml' already exists", message):
                    return 'n'
                if re.match(".*Proceed with these settings.*", message):
                    return 'y'
                if re.match(".*Wait for PVCs to bind.*", message):
                    return 'n'
            mixins_prompt.side_effect = set_mixin_prompt_input

            def set_app_prompt_input(**kwargs):
                message = str(kwargs['message'])
                if re.match('.*ReadWriteOnce (RWO) storage class.*', message):
                    return 'nfs-client'
                if re.match('.*ReadWriteMany (RWX) storage class.*', message):
                    return 'nfs-client'
            app_prompt.side_effect = set_app_prompt_input

            storage_class = MagicMock()
            get_storage_classes.return_value = [storage_class]
            storage_class.metadata = MagicMock()
            storage_class.metadata.name = 'nfs-client'
            app = AiServiceInstallApp()
            app.install(argv=[])


def test_install_interactive_simplified(tmpdir):
    tmpdir.join('authorized_entitlement.lic').write('testLicense')
    tmpdir.join('mongodb-system.yaml').write('#')
    tmpdir.join('cert.crt').write('#')
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
        storage_class_api = MagicMock()
        license_api = MagicMock()
        resource_apis = {'CatalogSource': catalog_api, 'Route': routes_api, 'CustomResourceDefinition': crd_api, 'Namespace': namespace_api,
                         'ClusterRoleBinding': cluster_role_binding_api, 'PersistentVolumeClaim': pvc_api, 'Secret': secret_api,
                         'StorageClass': storage_class_api, 'LicenseService': license_api}
        resources.get.side_effect = lambda **kwargs: resource_apis.get(kwargs['kind'], None)
        route = MagicMock()
        route.spec = MagicMock()
        route.spec.host = 'maximo.ibm.com'
        route.spec.displayName = supportedCatalogs['amd64'][1]
        routes_api.get.return_value = route
        catalog_api.get.side_effect = NotFoundError(ApiException(status='404'))
        with (
            mock.patch('mas.cli.cli.DynamicClient') as dynamic_client_class,
            mock.patch('mas.cli.cli.getNodes') as get_nodes,
            mock.patch('mas.cli.cli.isAirgapInstall') as is_airgap_install,
            mock.patch('mas.cli.aiservice.install.app.getCurrentCatalog') as get_current_catalog,
            mock.patch('mas.cli.aiservice.install.app.installOpenShiftPipelines'),
            mock.patch('mas.cli.aiservice.install.app.updateTektonDefinitions'),
            mock.patch('mas.cli.aiservice.install.app.prepareAiServicePipelinesNamespace'),
            mock.patch('mas.cli.aiservice.install.app.launchInstallPipeline') as launch_ai_service_install_pipeline,
            mock.patch('mas.cli.cli.isSNO') as is_sno,
            mock.patch('mas.cli.displayMixins.prompt') as mixins_prompt,
            mock.patch('mas.cli.aiservice.install.app.prompt') as app_prompt,
            mock.patch('mas.cli.aiservice.install.app.getStorageClasses') as get_storage_classes
        ):
            dynamic_client_class.return_value = dynamic_client
            get_nodes.return_value = [{'status': {'nodeInfo': {'architecture': 'amd64'}}}]
            is_airgap_install.return_value = False
            get_current_catalog.return_value = {'catalogId': supportedCatalogs['amd64'][1]}
            launch_ai_service_install_pipeline.return_value = 'https://pipeline.test.maximo.ibm.com'
            is_sno.return_value = False

            def set_mixin_prompt_input(**kwargs):
                message = str(kwargs['message'])
                if re.match('.*Proceed with this cluster?.*', message):
                    return 'y'
                if re.match('.*Show advanced installation options?.*', message):
                    return 'n'
                if re.match('.*Do you accept the license terms?.*', message):
                    return 'y'
                if re.match('.*ReadWriteOnce (RWO) storage class.*', message):
                    return 'nfs-client'
                if re.match('.*ReadWriteMany (RWX) storage class.*', message):
                    return 'nfs-client'
                if re.match('.*SLS Mode.*', message):
                    return '1'
                if re.match('.*License file.*', message):
                    return f'{tmpdir}/authorized_entitlement.lic'
                if re.match('.*Instance ID.*', message):
                    return 'apmdevops'
                if re.match('.*Operational Mode.*', message):
                    return '1'
                if re.match('.*Install Minio.*', message):
                    return 'y'
                if re.match('.*minio root username.*', message):
                    return 'username'
                if re.match('.*minio root password.*', message):
                    return 'password'
                if re.match('.*RSL url.*', message):
                    return 'https://rls.maximo.test.ibm.com'
                if re.match('.*ORG Id of RSL.*', message):
                    return 'rslOrgId'
                if re.match('.*Token for RSL.*', message):
                    return 'rslToken'
                if re.match('.*Watsonxai machine learning url.*', message):
                    return 'watsonxUrl'
                if re.match('.*Does the RSL API use a self-signed certificate.*', message):
                    return 'n'
                if re.match('.*Does the Watsonxai AI use a self-signed certificate.*', message):
                    return 'n'
                if re.match('.*Create MongoDb cluster.*', message):
                    return 'n'
                if re.match('.*Select Local configuration directory.*', message):
                    return str(tmpdir)
                if re.match('.*MongoDb Username.*', message):
                    return 'mongodbUser'
                if re.match('.*MongoDb Password.*', message):
                    return 'mongodbPassword'
                if re.match('.*Path to certificate file.*', message):
                    return f'{tmpdir}/cert.crt'
                if re.match(".*System mongodb configuration file 'mongodb-system.yaml' already exists", message):
                    return 'n'
                if re.match(".*Proceed with these settings.*", message):
                    return 'y'
                if re.match(".*Wait for PVCs to bind.*", message):
                    return 'n'
            mixins_prompt.side_effect = set_mixin_prompt_input

            def set_app_prompt_input(**kwargs):
                message = str(kwargs['message'])
                if re.match('.*ReadWriteOnce (RWO) storage class.*', message):
                    return 'nfs-client'
                if re.match('.*ReadWriteMany (RWX) storage class.*', message):
                    return 'nfs-client'
            app_prompt.side_effect = set_app_prompt_input

            storage_class = MagicMock()
            get_storage_classes.return_value = [storage_class]
            storage_class.metadata = MagicMock()
            storage_class.metadata.name = 'nfs-client'
            app = AiServiceInstallApp()
            app.install(argv=[])
