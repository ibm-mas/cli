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

import time
import threading
from typing import Dict, Callable, Optional
from unittest import mock
from unittest.mock import MagicMock
from kubernetes.client.rest import ApiException
from openshift.dynamic import DynamicClient
from openshift.dynamic.exceptions import NotFoundError
from mas.cli.install.catalogs import supportedCatalogs
from mas.cli.install.app import InstallApp
from utils.prompt_tracker import create_prompt_handler


class InstallTestConfig:
    """Configuration for an install test scenario."""

    def __init__(
        self,
        prompt_handlers: Dict[str, Callable[[str], str]],
        current_catalog: Optional[Dict[str, str]] = None,
        architecture: str = 'amd64',
        is_sno: bool = False,
        is_airgap: bool = False,
        storage_class_name: str = 'nfs-client',
        storage_provider: str = 'nfs',
        storage_provider_name: str = 'NFS Client',
        ocp_version: str = '4.18.0',
        timeout_seconds: int = 30,
        expect_system_exit: bool = False,
        argv: Optional[list] = None
    ):
        """
        Initialize test configuration.

        Args:
            prompt_handlers: Dictionary mapping regex patterns to handler functions
            current_catalog: Current catalog dict or None if no catalog installed
            architecture: Node architecture (amd64, s390x, ppc64le)
            is_sno: Whether cluster is Single Node OpenShift
            is_airgap: Whether this is an airgap installation
            storage_class_name: Name of the storage class to use
            storage_provider: Storage provider type (nfs, ocs, etc.)
            storage_provider_name: Display name of storage provider
            ocp_version: OpenShift version
            timeout_seconds: Timeout for watchdog (default 30s)
            expect_system_exit: Whether to expect SystemExit to be raised
            argv: Command line arguments to pass to app.install() (default: [])
        """
        self.prompt_handlers = prompt_handlers
        self.current_catalog = current_catalog
        self.architecture = architecture
        self.is_sno = is_sno
        self.is_airgap = is_airgap
        self.storage_class_name = storage_class_name
        self.storage_provider = storage_provider
        self.storage_provider_name = storage_provider_name
        self.ocp_version = ocp_version
        self.timeout_seconds = timeout_seconds
        self.expect_system_exit = expect_system_exit
        self.argv = argv if argv is not None else []


class InstallTestHelper:
    """Helper class to run install tests with minimal code duplication."""

    def __init__(self, tmpdir, config: InstallTestConfig, install_type: str = 'mas'):
        """
        Initialize the test helper.

        Args:
            tmpdir: pytest tmpdir fixture
            config: Test configuration
            install_type: Type of installation - 'mas' or 'aiservice' (default: 'mas')
        """
        self.tmpdir = tmpdir
        self.config = config
        self.install_type = install_type
        self.test_failed = {'failed': False, 'message': ''}
        self.last_prompt_time = {'time': time.time()}
        self.watchdog_thread = None
        self.prompt_tracker = None

    def setup_test_files(self):
        """Create test files in tmpdir."""
        self.tmpdir.join('authorized_entitlement.lic').write('testLicense')
        self.tmpdir.join('mongodb-system.yaml').write('#')
        self.tmpdir.join('cert.crt').write('#')

    def start_watchdog(self):
        """Start watchdog thread to detect hanging prompts."""
        def watchdog():
            while not self.test_failed['failed']:
                time.sleep(1)
                elapsed = time.time() - self.last_prompt_time['time']
                if elapsed > self.config.timeout_seconds:
                    self.test_failed['failed'] = True
                    self.test_failed['message'] = f"Test hung: No prompt received for {self.config.timeout_seconds}s"
                    break

        self.watchdog_thread = threading.Thread(target=watchdog, daemon=True)
        self.watchdog_thread.start()

    def stop_watchdog(self):
        """Stop the watchdog thread."""
        self.test_failed['failed'] = True

    def setup_mocks(self):
        """Setup all mock objects and return context managers."""
        # Create mock APIs
        dynamic_client = MagicMock(DynamicClient)
        resources = MagicMock()
        dynamic_client.resources = resources

        # Create individual API mocks
        routes_api = MagicMock()
        catalog_api = MagicMock()
        crd_api = MagicMock()
        namespace_api = MagicMock()
        cluster_role_binding_api = MagicMock()
        pvc_api = MagicMock()
        configmap_api = MagicMock()
        secret_api = MagicMock()
        storage_class_api = MagicMock()
        license_api = MagicMock()
        service_api = MagicMock()
        cluster_version_api = MagicMock()
        aiservice_tenant_api = MagicMock()
        aiservice_api = MagicMock()
        aiservice_app_api = MagicMock()
        ingress_controller_api = MagicMock()

        # Map resource kinds to APIs
        resource_apis = {
            'CatalogSource': catalog_api,
            'Route': routes_api,
            'CustomResourceDefinition': crd_api,
            'Namespace': namespace_api,
            'ClusterRoleBinding': cluster_role_binding_api,
            'PersistentVolumeClaim': pvc_api,
            'ConfigMap': configmap_api,
            'Secret': secret_api,
            'StorageClass': storage_class_api,
            'LicenseService': license_api,
            'Service': service_api,
            'ClusterVersion': cluster_version_api,
            'AIServiceTenant': aiservice_tenant_api,
            'AIService': aiservice_api,
            'AIServiceApp': aiservice_app_api,
            'IngressController': ingress_controller_api
        }
        resources.get.side_effect = lambda **kwargs: resource_apis.get(kwargs['kind'], None)

        # Configure route mock
        route = MagicMock()
        route.spec = MagicMock()
        route.spec.host = 'maximo.ibm.com'
        route.spec.displayName = supportedCatalogs[self.config.architecture][1]
        routes_api.get.return_value = route

        # Configure catalog mock
        catalog_api.get.side_effect = NotFoundError(ApiException(status='404'))

        # Configure service mock for image registry
        image_registry_service = MagicMock()
        image_registry_service.metadata = MagicMock()
        image_registry_service.metadata.name = 'image-registry'
        service_api.get.return_value = image_registry_service

        # Configure AIService mocks (empty lists)
        for api in [aiservice_tenant_api, aiservice_api, aiservice_app_api]:
            mock_list = MagicMock()
            mock_list.to_dict.return_value = {'items': []}
            api.get.return_value = mock_list

        # Configure ClusterVersion mock
        cluster_version = MagicMock()
        cluster_version.status = MagicMock()
        history_record = MagicMock()
        history_record.state = 'Completed'
        history_record.version = self.config.ocp_version
        cluster_version.status.history = [history_record]
        cluster_version_api.get.return_value = cluster_version

        # Configure IngressController mock only for MAS install (not needed for aiservice)
        if self.install_type == 'mas':
            # NOT configured for path-based routing initially
            # This will trigger the prompt to configure it
            ingress_controller = MagicMock()
            ingress_controller.metadata = MagicMock()
            ingress_controller.metadata.name = 'default'
            ingress_controller.status = MagicMock()
            ingress_controller.status.domain = 'apps.cluster.example.com'
            ingress_controller.status.conditions = [
                MagicMock(type='Available', status='True')
            ]
            ingress_controller.spec = MagicMock()
            ingress_controller.spec.routeAdmission = MagicMock()
            # Set to 'Strict' initially (not configured for path-based routing)
            ingress_controller.spec.routeAdmission.namespaceOwnership = 'Strict'

            # Support dict-style access for _checkIngressControllerForPathRouting
            # Initially returns 'Strict' (not configured)
            def ingress_controller_get(key, default=None):
                if key == 'spec':
                    spec_dict = {
                        'routeAdmission': {
                            'namespaceOwnership': 'Strict'  # Not configured for path-based routing
                        }
                    }
                    return type('obj', (object,), {
                        'get': lambda self, k, d=None: spec_dict.get(k, d)
                    })()
                return default

            ingress_controller.get = ingress_controller_get

            # Configure get() to return single controller when queried by name
            # and list when queried without name
            def ingress_controller_api_get(**kwargs):
                if 'name' in kwargs:
                    # Return single controller when queried by name
                    return ingress_controller
                else:
                    # Return list when querying all controllers
                    ingress_controller_list = MagicMock()
                    ingress_controller_list.items = [ingress_controller]
                    return ingress_controller_list

            ingress_controller_api.get.side_effect = ingress_controller_api_get

            # Mock patch operation to succeed
            ingress_controller_api.patch = MagicMock(return_value=ingress_controller)

        return dynamic_client, resource_apis

    def setup_prompt_handler(self, mixins_prompt, prompt_session_instance, app_prompt):
        """Setup prompt handler with tracking and watchdog integration."""
        # Create prompt tracker
        self.prompt_tracker, prompt_handler = create_prompt_handler(self.config.prompt_handlers)

        def wrapped_prompt_handler(*args, **kwargs):
            """Handle prompts and update watchdog timer."""
            # Check if test has timed out
            if self.test_failed['failed']:
                raise TimeoutError(self.test_failed['message'])

            # Update last prompt time
            self.last_prompt_time['time'] = time.time()

            # Use the prompt tracker to handle the prompt
            return prompt_handler(*args, **kwargs)

        # Set the same handler for all prompt mocks
        mixins_prompt.side_effect = wrapped_prompt_handler
        prompt_session_instance.prompt.side_effect = wrapped_prompt_handler
        app_prompt.side_effect = wrapped_prompt_handler

    def run_install_test(self):
        """
        Run the install test with all mocks configured.

        Raises:
            TimeoutError: If test times out
            AssertionError: If prompt verification fails
            SystemExit: If expect_system_exit is True and SystemExit is raised
        """
        # Determine which app class and module to use based on install_type
        if self.install_type == 'aiservice':
            from mas.cli.aiservice.install.app import AiServiceInstallApp
            app_class = AiServiceInstallApp
            app_module = 'mas.cli.aiservice.install.app'
            prepare_namespace_func = 'prepareAiServicePipelinesNamespace'
        else:
            app_class = InstallApp
            app_module = 'mas.cli.install.app'
            prepare_namespace_func = 'preparePipelinesNamespace'

        self.setup_test_files()
        self.start_watchdog()

        system_exit_raised = False
        exit_code = None

        with mock.patch('mas.cli.cli.config'):
            dynamic_client, resource_apis = self.setup_mocks()

            with (
                mock.patch('mas.cli.cli.DynamicClient') as dynamic_client_class,
                mock.patch('mas.cli.cli.getNodes') as get_nodes,
                mock.patch('mas.cli.cli.isAirgapInstall') as is_airgap_install,
                mock.patch(f'{app_module}.getCurrentCatalog') as get_current_catalog,
                mock.patch(f'{app_module}.installOpenShiftPipelines'),
                mock.patch(f'{app_module}.updateTektonDefinitions'),
                mock.patch(f'{app_module}.createNamespace'),
                mock.patch(f'{app_module}.{prepare_namespace_func}'),
                mock.patch(f'{app_module}.launchInstallPipeline') as launch_install_pipeline,
                mock.patch('mas.cli.install.app.configureIngressForPathBasedRouting') as configure_ingress,
                mock.patch('mas.cli.cli.isSNO') as is_sno,
                mock.patch('mas.cli.displayMixins.prompt') as mixins_prompt,
                mock.patch('mas.cli.displayMixins.PromptSession') as prompt_session_class,
                mock.patch(f'{app_module}.prompt') as app_prompt,
                mock.patch(f'{app_module}.getStorageClasses') as get_storage_classes,
                mock.patch(f'{app_module}.getDefaultStorageClasses') as get_default_storage_classes,
            ):

                # Configure mock return values
                dynamic_client_class.return_value = dynamic_client
                get_nodes.return_value = [{'status': {'nodeInfo': {'architecture': self.config.architecture}}}]
                is_airgap_install.return_value = self.config.is_airgap
                get_current_catalog.return_value = self.config.current_catalog
                launch_install_pipeline.return_value = 'https://pipeline.test.maximo.ibm.com'
                is_sno.return_value = self.config.is_sno
                configure_ingress.return_value = True

                # Configure PromptSession mock
                prompt_session_instance = MagicMock()
                prompt_session_class.return_value = prompt_session_instance

                # Setup prompt handler
                self.setup_prompt_handler(mixins_prompt, prompt_session_instance, app_prompt)

                # Configure storage class mocks
                storage_class = MagicMock()
                storage_class.metadata = MagicMock()
                storage_class.metadata.name = self.config.storage_class_name
                get_storage_classes.return_value = [storage_class]

                default_storage_classes = MagicMock()
                default_storage_classes.provider = self.config.storage_provider
                default_storage_classes.providerName = self.config.storage_provider_name
                default_storage_classes.rwo = self.config.storage_class_name
                default_storage_classes.rwx = self.config.storage_class_name
                get_default_storage_classes.return_value = default_storage_classes

                try:
                    app = app_class()
                    app.install(argv=self.config.argv)
                except SystemExit as e:
                    system_exit_raised = True
                    exit_code = e.code
                    if not self.config.expect_system_exit:
                        raise
                finally:
                    self.stop_watchdog()

                # Check if test timed out
                if self.test_failed['message']:
                    raise TimeoutError(self.test_failed['message'])

                # Verify SystemExit was raised if expected
                if self.config.expect_system_exit and not system_exit_raised:
                    raise AssertionError("Expected SystemExit to be raised but it was not")

                # Verify exit code is non-zero if SystemExit was expected
                if self.config.expect_system_exit and exit_code == 0:
                    raise AssertionError(f"Expected non-zero exit code but got {exit_code}")

                # Always verify all prompts were matched exactly once
                # This will fail if any prompts weren't reached (e.g., due to early SystemExit)
                # which is the desired behavior to ensure tests accurately reflect what prompts are shown
                assert self.prompt_tracker is not None, "prompt_tracker should be initialized"
                self.prompt_tracker.verify_all_prompts_matched()


def run_install_test(tmpdir, config: InstallTestConfig, install_type: str = 'mas'):
    """
    Convenience function to run an install test.

    Args:
        tmpdir: pytest tmpdir fixture
        config: Test configuration
        install_type: Type of installation - 'mas' or 'aiservice' (default: 'mas')

    Raises:
        TimeoutError: If test times out
        AssertionError: If prompt verification fails
    """
    helper = InstallTestHelper(tmpdir, config, install_type)
    helper.run_install_test()


def run_aiservice_install_test(tmpdir, config: InstallTestConfig):
    """
    Convenience function to run an aiservice install test.

    Args:
        tmpdir: pytest tmpdir fixture
        config: Test configuration

    Raises:
        TimeoutError: If test times out
        AssertionError: If prompt verification fails
    """
    run_install_test(tmpdir, config, install_type='aiservice')


# Made with Bob
