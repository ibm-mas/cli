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

from utils import create_prompt_handler
import sys
import os
from unittest import mock
from unittest.mock import MagicMock
from kubernetes.client.rest import ApiException
from openshift.dynamic import DynamicClient
from openshift.dynamic.exceptions import NotFoundError
from mas.cli.install.catalogs import supportedCatalogs
from mas.cli.aiservice.install.app import AiServiceInstallApp

# Add test directory to path for utils import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

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

            # Define prompt handlers with expected patterns and responses
            mixin_prompt_handlers = {
                '.*Proceed with this cluster?.*': lambda msg: 'y',
                '.*Show advanced installation options?.*': lambda msg: 'y',
                '.*Do you accept the license terms?.*': lambda msg: 'y',
                '.*ReadWriteOnce (RWO) storage class.*': lambda msg: 'nfs-client',
                '.*ReadWriteMany (RWX) storage class.*': lambda msg: 'nfs-client',
                '.*SLS Mode.*': lambda msg: '1',
                '.*License file.*': lambda msg: f'{tmpdir}/authorized_entitlement.lic',
                '.*Instance ID.*': lambda msg: 'apmdevops',
                '.*Operational Mode.*': lambda msg: '1',
                '.*Install Minio.*': lambda msg: 'y',
                '.*minio root username.*': lambda msg: 'username',
                '.*minio root password.*': lambda msg: 'password',
                '.*Configure certificate issuer?.*': lambda msg: 'y',
                '.*Certificate issuer name.*': lambda msg: 'cert-issuer',
                '.*RSL url.*': lambda msg: 'https://rls.maximo.test.ibm.com',
                '.*ORG Id of RSL.*': lambda msg: 'rslOrgId',
                '.*Token for RSL.*': lambda msg: 'rslToken',
                '.*Watsonxai machine learning url.*': lambda msg: 'watsonxUrl',
                '.*Does the RSL API use a self-signed certificate.*': lambda msg: 'n',
                '.*Does the Watsonxai AI use a self-signed certificate.*': lambda msg: 'n',
                '.*Create MongoDb cluster.*': lambda msg: 'n',
                '.*Select Local configuration directory.*': lambda msg: str(tmpdir),
                '.*MongoDb Username.*': lambda msg: 'mongodbUser',
                '.*MongoDb Password.*': lambda msg: 'mongodbPassword',
                '.*Path to certificate file.*': lambda msg: f'{tmpdir}/cert.crt',
                ".*System mongodb configuration file 'mongodb-system.yaml' already exists": lambda msg: 'n',
                ".*Proceed with these settings.*": lambda msg: 'y',
            }

            # Create prompt tracker for mixin prompts
            mixin_prompt_tracker, mixin_prompt_handler = create_prompt_handler(mixin_prompt_handlers)
            mixins_prompt.side_effect = mixin_prompt_handler

            # Note: app_prompt patterns are duplicates of mixin patterns, so we track them separately
            app_prompt_handlers = {
                '.*ReadWriteOnce (RWO) storage class.*': lambda msg: 'nfs-client',
                '.*ReadWriteMany (RWX) storage class.*': lambda msg: 'nfs-client',
            }
            app_prompt_tracker, app_prompt_handler = create_prompt_handler(app_prompt_handlers)
            app_prompt.side_effect = app_prompt_handler

            storage_class = MagicMock()
            get_storage_classes.return_value = [storage_class]
            storage_class.metadata = MagicMock()
            storage_class.metadata.name = 'nfs-client'
            app = AiServiceInstallApp()
            app.install(argv=[])

            # Verify all prompts were matched exactly once
            mixin_prompt_tracker.verify_all_prompts_matched()
            app_prompt_tracker.verify_all_prompts_matched()


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

            # Define prompt handlers with expected patterns and responses
            mixin_prompt_handlers = {
                '.*Proceed with this cluster?.*': lambda msg: 'y',
                '.*Show advanced installation options?.*': lambda msg: 'n',
                '.*Do you accept the license terms?.*': lambda msg: 'y',
                '.*ReadWriteOnce (RWO) storage class.*': lambda msg: 'nfs-client',
                '.*ReadWriteMany (RWX) storage class.*': lambda msg: 'nfs-client',
                '.*SLS Mode.*': lambda msg: '1',
                '.*License file.*': lambda msg: f'{tmpdir}/authorized_entitlement.lic',
                '.*Instance ID.*': lambda msg: 'apmdevops',
                '.*Operational Mode.*': lambda msg: '1',
                '.*Install Minio.*': lambda msg: 'y',
                '.*minio root username.*': lambda msg: 'username',
                '.*minio root password.*': lambda msg: 'password',
                '.*RSL url.*': lambda msg: 'https://rls.maximo.test.ibm.com',
                '.*ORG Id of RSL.*': lambda msg: 'rslOrgId',
                '.*Token for RSL.*': lambda msg: 'rslToken',
                '.*Watsonxai machine learning url.*': lambda msg: 'watsonxUrl',
                '.*Does the RSL API use a self-signed certificate.*': lambda msg: 'n',
                '.*Does the Watsonxai AI use a self-signed certificate.*': lambda msg: 'n',
                '.*Create MongoDb cluster.*': lambda msg: 'n',
                '.*Select Local configuration directory.*': lambda msg: str(tmpdir),
                '.*MongoDb Username.*': lambda msg: 'mongodbUser',
                '.*MongoDb Password.*': lambda msg: 'mongodbPassword',
                '.*Path to certificate file.*': lambda msg: f'{tmpdir}/cert.crt',
                ".*System mongodb configuration file 'mongodb-system.yaml' already exists": lambda msg: 'n',
                ".*Proceed with these settings.*": lambda msg: 'y',
            }

            # Create prompt tracker for mixin prompts
            mixin_prompt_tracker, mixin_prompt_handler = create_prompt_handler(mixin_prompt_handlers)
            mixins_prompt.side_effect = mixin_prompt_handler

            # Note: app_prompt patterns are duplicates of mixin patterns, so we track them separately
            app_prompt_handlers = {
                '.*ReadWriteOnce (RWO) storage class.*': lambda msg: 'nfs-client',
                '.*ReadWriteMany (RWX) storage class.*': lambda msg: 'nfs-client',
            }
            app_prompt_tracker, app_prompt_handler = create_prompt_handler(app_prompt_handlers)
            app_prompt.side_effect = app_prompt_handler

            storage_class = MagicMock()
            get_storage_classes.return_value = [storage_class]
            storage_class.metadata = MagicMock()
            storage_class.metadata.name = 'nfs-client'
            app = AiServiceInstallApp()
            app.install(argv=[])

            # Verify all prompts were matched exactly once
            mixin_prompt_tracker.verify_all_prompts_matched()
            app_prompt_tracker.verify_all_prompts_matched()
