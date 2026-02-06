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
import time
import threading
import sys
import os
from unittest import mock
from unittest.mock import MagicMock
from kubernetes.client.rest import ApiException
from openshift.dynamic import DynamicClient
from openshift.dynamic.exceptions import NotFoundError
from mas.cli.install.catalogs import supportedCatalogs
from mas.cli.install.app import InstallApp

# Add test directory to path for utils import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# These tests do not cover all possible combinations of install parameters. They are a starting point.
# Future improvements should look at generating all possible permutations of the install parameters
# and passing to a set of parameterized tests to increase scenario coverage.


def test_install_interactive_existing_catalog(tmpdir):
    """Test interactive installation with 30s timeout for hanging prompts."""
    tmpdir.join('authorized_entitlement.lic').write('testLicense')
    tmpdir.join('mongodb-system.yaml').write('#')
    tmpdir.join('cert.crt').write('#')

    # Timeout watchdog to detect hanging prompts
    last_prompt_time = {'time': time.time()}
    timeout_seconds = 30
    test_failed = {'failed': False, 'message': ''}

    def watchdog():
        """Monitor for prompts that take longer than timeout_seconds."""
        while not test_failed['failed']:
            time.sleep(1)
            elapsed = time.time() - last_prompt_time['time']
            if elapsed > timeout_seconds:
                test_failed['failed'] = True
                test_failed['message'] = f"Test hung: No prompt received for {timeout_seconds}s"
                break

    # Start watchdog thread
    watchdog_thread = threading.Thread(target=watchdog, daemon=True)
    watchdog_thread.start()

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
        service_api = MagicMock()
        cluster_version_api = MagicMock()
        aiservice_tenant_api = MagicMock()
        aiservice_api = MagicMock()
        aiservice_app_api = MagicMock()
        resource_apis = {'CatalogSource': catalog_api, 'Route': routes_api, 'CustomResourceDefinition': crd_api, 'Namespace': namespace_api,
                         'ClusterRoleBinding': cluster_role_binding_api, 'PersistentVolumeClaim': pvc_api, 'Secret': secret_api,
                         'StorageClass': storage_class_api, 'LicenseService': license_api, 'Service': service_api, 'ClusterVersion': cluster_version_api,
                         'AIServiceTenant': aiservice_tenant_api, 'AIService': aiservice_api, 'AIServiceApp': aiservice_app_api}
        resources.get.side_effect = lambda **kwargs: resource_apis.get(kwargs['kind'], None)
        route = MagicMock()
        route.spec = MagicMock()
        route.spec.host = 'maximo.ibm.com'
        route.spec.displayName = supportedCatalogs['amd64'][1]
        routes_api.get.return_value = route
        catalog_api.get.side_effect = NotFoundError(ApiException(status='404'))

        # Mock Service API to return image-registry service for validateInternalRegistryAvailable()
        image_registry_service = MagicMock()
        image_registry_service.metadata = MagicMock()
        image_registry_service.metadata.name = 'image-registry'
        service_api.get.return_value = image_registry_service

        # Mock AIService APIs to return empty lists (no existing instances)
        aiservice_tenant_list = MagicMock()
        aiservice_tenant_list.to_dict.return_value = {'items': []}
        aiservice_tenant_api.get.return_value = aiservice_tenant_list

        aiservice_list = MagicMock()
        aiservice_list.to_dict.return_value = {'items': []}
        aiservice_api.get.return_value = aiservice_list

        aiservice_app_list = MagicMock()
        aiservice_app_list.to_dict.return_value = {'items': []}
        aiservice_app_api.get.return_value = aiservice_app_list

        # Mock ClusterVersion
        cluster_version = MagicMock()
        cluster_version.status = MagicMock()
        history_record = MagicMock()
        history_record.state = 'Completed'
        history_record.version = '4.18.0'
        cluster_version.status.history = [history_record]
        cluster_version_api.get.return_value = cluster_version
        with (
            mock.patch('mas.cli.cli.DynamicClient') as dynamic_client_class,
            mock.patch('mas.cli.cli.getNodes') as get_nodes,
            mock.patch('mas.cli.cli.isAirgapInstall') as is_airgap_install,
            mock.patch('mas.cli.install.app.getCurrentCatalog') as get_current_catalog,
            mock.patch('mas.cli.install.app.installOpenShiftPipelines'),
            mock.patch('mas.cli.install.app.updateTektonDefinitions'),
            mock.patch('mas.cli.install.app.createNamespace'),
            mock.patch('mas.cli.install.app.preparePipelinesNamespace'),
            mock.patch('mas.cli.install.app.launchInstallPipeline') as launch_install_pipeline,
            mock.patch('mas.cli.cli.isSNO') as is_sno,
            mock.patch('mas.cli.displayMixins.prompt') as mixins_prompt,
            mock.patch('mas.cli.displayMixins.PromptSession') as prompt_session_class,
            mock.patch('mas.cli.install.app.prompt') as app_prompt,
            mock.patch('mas.cli.install.app.getStorageClasses') as get_storage_classes,
            mock.patch('mas.cli.install.app.getDefaultStorageClasses') as get_default_storage_classes
        ):
            dynamic_client_class.return_value = dynamic_client
            get_nodes.return_value = [{'status': {'nodeInfo': {'architecture': 'amd64'}}}]
            is_airgap_install.return_value = False
            get_current_catalog.return_value = {'catalogId': supportedCatalogs['amd64'][1]}
            launch_install_pipeline.return_value = 'https://pipeline.test.maximo.ibm.com'
            is_sno.return_value = False

            # Configure PromptSession mock to use the same handler as regular prompt
            prompt_session_instance = MagicMock()
            prompt_session_class.return_value = prompt_session_instance

            # Define prompt handlers with expected patterns and responses
            prompt_handlers = {
                # 1. Cluster connection
                '.*Proceed with this cluster?.*': lambda msg: 'y',
                # 2. Install flavour (advanced options)
                '.*Show advanced installation options.*': lambda msg: 'n',
                # 3. Catalog selection
                # Note: We will not be prompted for the catalog because we are mocking that there is already a catalog installed
                '.*Select release.*': lambda msg: '9.1',
                # 4. License acceptance
                '.*Do you accept the license terms?.*': lambda msg: 'y',
                # 5. Storage classes
                ".*Use the auto-detected storage classes.*": lambda msg: 'y',
                # 6. SLS configuration
                '.*License file.*': lambda msg: f'{tmpdir}/authorized_entitlement.lic',
                # 7. DRO configuration
                ".*Contact e-mail address.*": lambda msg: 'maximo@ibm.com',
                ".*Contact first name.*": lambda msg: 'Test',
                ".*Contact last name.*": lambda msg: 'Test',
                # 8. ICR credentials
                ".*IBM entitlement key.*": lambda msg: 'testEntitlementKey',
                # 9. MAS Instance configuration
                '.*Instance ID.*': lambda msg: 'testinst',
                '.*Workspace ID.*': lambda msg: 'testws',
                '.*Workspace.*name.*': lambda msg: 'Test Workspace',
                # 10. Operational mode
                '.*Operational Mode.*': lambda msg: '1',
                # 11. Application selection
                # Note: because we choose not to install IoT we should not be prompted for Monitor or Predict
                '.*Install IoT.*': lambda msg: 'n',
                '.*Install Manage.*': lambda msg: 'y',
                '.*Select components to enable.*': lambda msg: 'n',
                '.*Include customization archive.*': lambda msg: 'n',
                '.*Install Assist.*': lambda msg: 'n',
                '.*Install Optimizer.*': lambda msg: 'n',
                '.*Install Visual Inspection.*': lambda msg: 'n',
                '.*Install.*Real Estate and Facilities.*': lambda msg: 'n',
                '.*Install AI Service.*': lambda msg: 'n',
                # 12. MongoDB configuration
                '.*Create MongoDb cluster.*': lambda msg: 'y',
                # 13. Db2 configuration
                '.*Create Manage dedicated Db2 instance.*': lambda msg: 'y',
                # 15. Final confirmation
                '.*Use additional configurations.*': lambda msg: 'n',
                ".*Proceed with these settings.*": lambda msg: 'y',
            }

            # Create prompt tracker
            prompt_tracker, prompt_handler = create_prompt_handler(prompt_handlers)

            def set_mixin_prompt_input(**kwargs):
                """Handle prompts and update watchdog timer."""
                # Check if test has timed out
                if test_failed['failed']:
                    raise TimeoutError(test_failed['message'])

                # Update last prompt time
                last_prompt_time['time'] = time.time()

                # Use the prompt tracker to handle the prompt
                return prompt_handler(**kwargs)

            # Set the same handler for all prompt mocks
            # This handles prompts from displayMixins.prompt, PromptSession.prompt, and any direct app.prompt calls
            mixins_prompt.side_effect = set_mixin_prompt_input
            prompt_session_instance.prompt.side_effect = set_mixin_prompt_input
            app_prompt.side_effect = set_mixin_prompt_input

            storage_class = MagicMock()
            get_storage_classes.return_value = [storage_class]
            storage_class.metadata = MagicMock()
            storage_class.metadata.name = 'nfs-client'

            # Mock getDefaultStorageClasses to return NFS storage classes
            default_storage_classes = MagicMock()
            default_storage_classes.provider = "nfs"
            default_storage_classes.providerName = "NFS Client"
            default_storage_classes.rwo = "nfs-client"
            default_storage_classes.rwx = "nfs-client"
            get_default_storage_classes.return_value = default_storage_classes

            try:
                app = InstallApp()
                app.install(argv=[])
            finally:
                # Stop watchdog
                test_failed['failed'] = True

            # Check if test timed out
            if test_failed['message']:
                raise TimeoutError(test_failed['message'])

            # Verify all prompts were matched exactly once
            prompt_tracker.verify_all_prompts_matched()


def test_install_interactive_no_catalog(tmpdir):
    """Test interactive installation with 30s timeout for hanging prompts."""
    tmpdir.join('authorized_entitlement.lic').write('testLicense')
    tmpdir.join('mongodb-system.yaml').write('#')
    tmpdir.join('cert.crt').write('#')

    # Timeout watchdog to detect hanging prompts
    last_prompt_time = {'time': time.time()}
    timeout_seconds = 30
    test_failed = {'failed': False, 'message': ''}

    def watchdog():
        """Monitor for prompts that take longer than timeout_seconds."""
        while not test_failed['failed']:
            time.sleep(1)
            elapsed = time.time() - last_prompt_time['time']
            if elapsed > timeout_seconds:
                test_failed['failed'] = True
                test_failed['message'] = f"Test hung: No prompt received for {timeout_seconds}s"
                break

    # Start watchdog thread
    watchdog_thread = threading.Thread(target=watchdog, daemon=True)
    watchdog_thread.start()

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
        service_api = MagicMock()
        cluster_version_api = MagicMock()
        aiservice_tenant_api = MagicMock()
        aiservice_api = MagicMock()
        aiservice_app_api = MagicMock()
        resource_apis = {'CatalogSource': catalog_api, 'Route': routes_api, 'CustomResourceDefinition': crd_api, 'Namespace': namespace_api,
                         'ClusterRoleBinding': cluster_role_binding_api, 'PersistentVolumeClaim': pvc_api, 'Secret': secret_api,
                         'StorageClass': storage_class_api, 'LicenseService': license_api, 'Service': service_api, 'ClusterVersion': cluster_version_api,
                         'AIServiceTenant': aiservice_tenant_api, 'AIService': aiservice_api, 'AIServiceApp': aiservice_app_api}
        resources.get.side_effect = lambda **kwargs: resource_apis.get(kwargs['kind'], None)
        route = MagicMock()
        route.spec = MagicMock()
        route.spec.host = 'maximo.ibm.com'
        route.spec.displayName = supportedCatalogs['amd64'][1]
        routes_api.get.return_value = route
        catalog_api.get.side_effect = NotFoundError(ApiException(status='404'))

        # Mock Service API to return image-registry service for validateInternalRegistryAvailable()
        image_registry_service = MagicMock()
        image_registry_service.metadata = MagicMock()
        image_registry_service.metadata.name = 'image-registry'
        service_api.get.return_value = image_registry_service

        # Mock AIService APIs to return empty lists (no existing instances)
        aiservice_tenant_list = MagicMock()
        aiservice_tenant_list.to_dict.return_value = {'items': []}
        aiservice_tenant_api.get.return_value = aiservice_tenant_list

        aiservice_list = MagicMock()
        aiservice_list.to_dict.return_value = {'items': []}
        aiservice_api.get.return_value = aiservice_list

        aiservice_app_list = MagicMock()
        aiservice_app_list.to_dict.return_value = {'items': []}
        aiservice_app_api.get.return_value = aiservice_app_list

        # Mock ClusterVersion
        cluster_version = MagicMock()
        cluster_version.status = MagicMock()
        history_record = MagicMock()
        history_record.state = 'Completed'
        history_record.version = '4.18.0'
        cluster_version.status.history = [history_record]
        cluster_version_api.get.return_value = cluster_version
        with (
            mock.patch('mas.cli.cli.DynamicClient') as dynamic_client_class,
            mock.patch('mas.cli.cli.getNodes') as get_nodes,
            mock.patch('mas.cli.cli.isAirgapInstall') as is_airgap_install,
            mock.patch('mas.cli.install.app.getCurrentCatalog') as get_current_catalog,
            mock.patch('mas.cli.install.app.installOpenShiftPipelines'),
            mock.patch('mas.cli.install.app.updateTektonDefinitions'),
            mock.patch('mas.cli.install.app.createNamespace'),
            mock.patch('mas.cli.install.app.preparePipelinesNamespace'),
            mock.patch('mas.cli.install.app.launchInstallPipeline') as launch_install_pipeline,
            mock.patch('mas.cli.cli.isSNO') as is_sno,
            mock.patch('mas.cli.displayMixins.prompt') as mixins_prompt,
            mock.patch('mas.cli.displayMixins.PromptSession') as prompt_session_class,
            mock.patch('mas.cli.install.app.prompt') as app_prompt,
            mock.patch('mas.cli.install.app.getStorageClasses') as get_storage_classes,
            mock.patch('mas.cli.install.app.getDefaultStorageClasses') as get_default_storage_classes
        ):
            dynamic_client_class.return_value = dynamic_client
            get_nodes.return_value = [{'status': {'nodeInfo': {'architecture': 'amd64'}}}]
            is_airgap_install.return_value = False
            get_current_catalog.return_value = None
            launch_install_pipeline.return_value = 'https://pipeline.test.maximo.ibm.com'
            is_sno.return_value = False

            # Configure PromptSession mock to use the same handler as regular prompt
            prompt_session_instance = MagicMock()
            prompt_session_class.return_value = prompt_session_instance

            # Define prompt handlers with expected patterns and responses
            prompt_handlers = {
                # 1. Cluster connection
                '.*Proceed with this cluster?.*': lambda msg: 'y',
                # 2. Install flavour (advanced options)
                '.*Show advanced installation options.*': lambda msg: 'n',
                # 3. Catalog selection
                '.*Select catalog.*': lambda msg: supportedCatalogs['amd64'][1],
                '.*Select release.*': lambda msg: '9.1',
                # 4. License acceptance
                '.*Do you accept the license terms?.*': lambda msg: 'y',
                # 5. Storage classes
                ".*Use the auto-detected storage classes.*": lambda msg: 'y',
                # 6. SLS configuration
                '.*License file.*': lambda msg: f'{tmpdir}/authorized_entitlement.lic',
                # 7. DRO configuration
                ".*Contact e-mail address.*": lambda msg: 'maximo@ibm.com',
                ".*Contact first name.*": lambda msg: 'Test',
                ".*Contact last name.*": lambda msg: 'Test',
                # 8. ICR credentials
                ".*IBM entitlement key.*": lambda msg: 'testEntitlementKey',
                # 9. MAS Instance configuration
                '.*Instance ID.*': lambda msg: 'testinst',
                '.*Workspace ID.*': lambda msg: 'testws',
                '.*Workspace.*name.*': lambda msg: 'Test Workspace',
                # 10. Operational mode
                '.*Operational Mode.*': lambda msg: '1',
                # 11. Application selection
                '.*Install IoT.*': lambda msg: 'y',
                '.*Install Monitor.*': lambda msg: 'n',
                '.*Install Manage.*': lambda msg: 'y',
                '.*Select components to enable.*': lambda msg: 'n',
                '.*Include customization archive.*': lambda msg: 'n',
                '.*Install Predict.*': lambda msg: 'n',
                '.*Install Assist.*': lambda msg: 'n',
                '.*Install Optimizer.*': lambda msg: 'n',
                '.*Install Visual Inspection.*': lambda msg: 'n',
                '.*Install.*Real Estate and Facilities.*': lambda msg: 'n',
                '.*Install AI Service.*': lambda msg: 'n',
                # 12. MongoDB configuration
                '.*Create MongoDb cluster.*': lambda msg: 'y',
                # 13. Db2 configuration
                '.*Create system Db2 instance.*': lambda msg: 'y',
                '.*Re-use System Db2 instance for Manage application.*': lambda msg: 'n',
                '.*Create Manage dedicated Db2 instance.*': lambda msg: 'y',
                # 14. Kafka configuration
                '.*Create system Kafka instance.*': lambda msg: 'y',
                '.*Kafka version.*': lambda msg: '3.8.0',
                # 15. Final confirmation
                '.*Use additional configurations.*': lambda msg: 'n',
                ".*Proceed with these settings.*": lambda msg: 'y',
            }

            # Create prompt tracker
            prompt_tracker, prompt_handler = create_prompt_handler(prompt_handlers)

            def set_mixin_prompt_input(**kwargs):
                """Handle prompts and update watchdog timer."""
                # Check if test has timed out
                if test_failed['failed']:
                    raise TimeoutError(test_failed['message'])

                # Update last prompt time
                last_prompt_time['time'] = time.time()

                # Use the prompt tracker to handle the prompt
                return prompt_handler(**kwargs)

            # Set the same handler for all prompt mocks
            # This handles prompts from displayMixins.prompt, PromptSession.prompt, and any direct app.prompt calls
            mixins_prompt.side_effect = set_mixin_prompt_input
            prompt_session_instance.prompt.side_effect = set_mixin_prompt_input
            app_prompt.side_effect = set_mixin_prompt_input

            storage_class = MagicMock()
            get_storage_classes.return_value = [storage_class]
            storage_class.metadata = MagicMock()
            storage_class.metadata.name = 'nfs-client'

            # Mock getDefaultStorageClasses to return NFS storage classes
            default_storage_classes = MagicMock()
            default_storage_classes.provider = "nfs"
            default_storage_classes.providerName = "NFS Client"
            default_storage_classes.rwo = "nfs-client"
            default_storage_classes.rwx = "nfs-client"
            get_default_storage_classes.return_value = default_storage_classes

            try:
                app = InstallApp()
                app.install(argv=[])
            finally:
                # Stop watchdog
                test_failed['failed'] = True

            # Check if test timed out
            if test_failed['message']:
                raise TimeoutError(test_failed['message'])

            # Verify all prompts were matched exactly once
            prompt_tracker.verify_all_prompts_matched()

# Made with Bob
