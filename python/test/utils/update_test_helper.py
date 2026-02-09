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
import contextlib
from typing import Dict, Callable, Optional, List
from unittest import mock
from unittest.mock import MagicMock
from openshift.dynamic import DynamicClient
from mas.cli.update.app import UpdateApp
from utils.prompt_tracker import create_prompt_handler


class UpdateTestConfig:
    """Configuration for an update test scenario."""

    def __init__(
        self,
        prompt_handlers: Dict[str, Callable[[str], str]],
        installed_catalog_id: str = "v9-251231-amd64",
        target_catalog_version: str = "v9-260129-amd64",
        architecture: str = "amd64",
        db2u_namespaces: Optional[List[str]] = None,
        db2u_resource_kind: str = "Db2uCluster",
        db2u_namespace_arg: Optional[str] = None,
        kafka_namespaces: Optional[List[str]] = None,
        kafka_namespace_arg: Optional[str] = None,
        kafka_provider: Optional[str] = None,
        mas_instances: Optional[List[Dict]] = None,
        aiservice_instances: Optional[List[Dict]] = None,
        mongodb_namespaces: Optional[List[str]] = None,
        mongodb_namespace_arg: Optional[str] = None,
        ocp_version: str = '4.18.0',
        timeout_seconds: int = 30,
        expect_system_exit: bool = False,
        expected_exit_code: Optional[int] = None,
        argv: Optional[list] = None
    ):
        """
        Initialize update test configuration.

        Args:
            prompt_handlers: Dictionary mapping regex patterns to handler functions
            installed_catalog_id: Currently installed catalog version
            target_catalog_version: Target catalog version for update
            architecutre: Architecture of the cluster
            db2u_namespaces: List of namespaces containing Db2U resources (None = no resources)
            db2u_resource_kind: Type of Db2U resource ("Db2uCluster" or "Db2uInstance")
            db2u_namespace_arg: Value for --db2-namespace CLI argument
            kafka_namespaces: List of namespaces containing Kafka resources
            kafka_namespace_arg: Value for --kafka-namespace CLI argument
            kafka_provider: Kafka provider type ("strimzi" or "redhat")
            mas_instances: List of MAS instance dicts
            aiservice_instances: List of AI Service instance dicts
            mongodb_namespaces: List of namespaces containing MongoDB resources
            mongodb_namespace_arg: Value for --mongodb-namespace CLI argument
            ocp_version: OpenShift version
            timeout_seconds: Timeout for watchdog (default 30s)
            expect_system_exit: Whether to expect SystemExit to be raised
            expected_exit_code: Expected exit code if SystemExit is raised
            argv: Command line arguments to pass to app.update() (default: [])
        """
        self.prompt_handlers = prompt_handlers
        self.installed_catalog_id = installed_catalog_id
        self.target_catalog_version = target_catalog_version
        self.architecture = architecture
        self.db2u_namespaces = db2u_namespaces if db2u_namespaces is not None else []
        self.db2u_resource_kind = db2u_resource_kind
        self.db2u_namespace_arg = db2u_namespace_arg
        self.kafka_namespaces = kafka_namespaces if kafka_namespaces is not None else []
        self.kafka_namespace_arg = kafka_namespace_arg
        self.kafka_provider = kafka_provider
        self.mas_instances = mas_instances if mas_instances is not None else []
        self.aiservice_instances = aiservice_instances if aiservice_instances is not None else []
        self.mongodb_namespaces = mongodb_namespaces if mongodb_namespaces is not None else []
        self.mongodb_namespace_arg = mongodb_namespace_arg
        self.ocp_version = ocp_version
        self.timeout_seconds = timeout_seconds
        self.expect_system_exit = expect_system_exit
        self.expected_exit_code = expected_exit_code
        self.argv = argv if argv is not None else []


class UpdateTestHelper:
    """Helper class to run update tests with minimal code duplication."""

    def __init__(self, tmpdir, config: UpdateTestConfig):
        """
        Initialize the test helper.

        Args:
            tmpdir: pytest tmpdir fixture
            config: Test configuration
        """
        self.tmpdir = tmpdir
        self.config = config
        self.test_failed = {'failed': False, 'message': ''}
        self.last_prompt_time = {'time': time.time()}
        self.watchdog_thread = None
        self.prompt_tracker = None
        self.app = None

    def setup_test_files(self):
        """Create test files in tmpdir."""
        # Update tests don't typically need test files, but we keep this for consistency
        pass

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

    def create_db2u_resource(self, kind: str, name: str, namespace: str) -> Dict:
        """Create a mock Db2U resource."""
        return {
            "metadata": {
                "name": name,
                "namespace": namespace
            },
            "spec": {
                "version": "11.5.9.0",
                "license": {"accept": True}
            },
            "status": {
                "state": "Ready"
            }
        }

    def create_kafka_resource(self, name: str, namespace: str) -> Dict:
        """Create a mock Kafka resource."""
        return {
            "metadata": {
                "name": name,
                "namespace": namespace
            },
            "spec": {
                "kafka": {
                    "version": "3.7.0",
                    "replicas": 3
                }
            },
            "status": {
                "conditions": [{"type": "Ready", "status": "True"}]
            }
        }

    def create_mongodb_resource(self, name: str, namespace: str) -> Dict:
        """Create a mock MongoDB resource."""
        return {
            "metadata": {
                "name": name,
                "namespace": namespace
            },
            "spec": {
                "members": 3,
                "type": "ReplicaSet",
                "version": "6.0.5"
            },
            "status": {
                "version": "6.0.5",
                "phase": "Running"
            }
        }

    def create_pod_resource(self, name: str, namespace: str) -> Dict:
        """Create a mock pod resource."""
        return {
            "metadata": {
                "name": name,
                "namespace": namespace
            },
            "spec": {
                "containers": [{
                    "name": name,
                    "image": ""
                }],
            },
            "status": {
                "phase": "Running"
            }
        }

    def setup_mocks(self):
        """Setup all mock objects and return context managers."""
        # Create mock APIs
        dynamic_client = MagicMock(DynamicClient)
        resources = MagicMock()
        dynamic_client.resources = resources

        # Create individual API mocks
        catalog_api = MagicMock()
        crd_api = MagicMock()
        namespace_api = MagicMock()
        cluster_version_api = MagicMock()
        suite_api = MagicMock()
        aiservice_app_api = MagicMock()
        db2ucluster_api = MagicMock()
        db2uinstance_api = MagicMock()
        kafka_api = MagicMock()
        mongodb_api = MagicMock()
        subscription_api = MagicMock()
        grafana_api = MagicMock()
        watson_discovery_api = MagicMock()
        watson_openscale_api = MagicMock()
        cpd_api = MagicMock()
        routes_api = MagicMock()
        pods_api = MagicMock()

        # Map resource kinds to APIs
        resource_apis = {
            'CatalogSource': catalog_api,
            'Route': routes_api,
            'CustomResourceDefinition': crd_api,
            'Namespace': namespace_api,
            'ClusterVersion': cluster_version_api,
            'Suite': suite_api,
            'AIServiceApp': aiservice_app_api,
            'Db2uCluster': db2ucluster_api,
            'Db2uInstance': db2uinstance_api,
            'Kafka': kafka_api,
            'MongoDBCommunity': mongodb_api,
            'Subscription': subscription_api,
            'Grafana': grafana_api,
            'WatsonDiscovery': watson_discovery_api,
            'WOService': watson_openscale_api,
            'Ibmcpd': cpd_api,
            'Pod': pods_api
        }
        resources.get.side_effect = lambda **kwargs: resource_apis.get(kwargs['kind'], None)

        # Configure catalog mock
        catalog = MagicMock()
        catalog.spec = MagicMock()
        catalog.spec.displayName = f"IBM Maximo Operator Catalog ({self.config.installed_catalog_id})"
        catalog.spec.image = f"icr.io/cpopen/ibm-maximo-operator-catalog:{self.config.installed_catalog_id}"
        catalog_api.get.return_value = catalog

        # Configure route mock
        route = MagicMock()
        route.spec = MagicMock()
        route.spec.host = 'maximo.ibm.com'
        route.spec.displayName = self.config.installed_catalog_id
        routes_api.get.return_value = route

        # Configure ClusterVersion mock
        cluster_version = MagicMock()
        cluster_version.status = MagicMock()
        history_record = MagicMock()
        history_record.state = 'Completed'
        history_record.version = self.config.ocp_version
        cluster_version.status.history = [history_record]
        cluster_version_api.get.return_value = cluster_version

        # Configure MAS instances mock
        mas_list = MagicMock()
        mas_list.to_dict.return_value = {'items': self.config.mas_instances}
        suite_api.get.return_value = mas_list

        # Configure AI Service instances mock
        aiservice_list = MagicMock()
        aiservice_list.to_dict.return_value = {'items': self.config.aiservice_instances}
        aiservice_app_api.get.return_value = aiservice_list

        # Configure Db2U mocks
        self.setup_db2u_mocks(db2ucluster_api, db2uinstance_api)

        # Configure Kafka mocks
        self.setup_kafka_mocks(kafka_api, subscription_api)

        # Configure MongoDB mocks
        self.setup_mongodb_mocks(mongodb_api)

        # Configure dependency check mocks (all return empty/not found)
        grafana_list = MagicMock()
        grafana_list.to_dict.return_value = {'items': []}
        grafana_api.get.return_value = grafana_list

        watson_discovery_list = MagicMock()
        watson_discovery_list.to_dict.return_value = {'items': []}
        watson_discovery_api.get.return_value = watson_discovery_list

        watson_openscale_list = MagicMock()
        watson_openscale_list.to_dict.return_value = {'items': []}
        watson_openscale_api.get.return_value = watson_openscale_list

        cpd_list = MagicMock()
        cpd_list.to_dict.return_value = {'items': []}
        cpd_api.get.return_value = cpd_list

        pods_list = MagicMock()
        pods_list.to_dict.return_value = self.create_pod_resource("cert-manager-cainjector", "ibm-common-services")
        return dynamic_client, resource_apis

    def setup_db2u_mocks(self, db2ucluster_api, db2uinstance_api):
        """Setup Db2U API mocks based on configuration."""
        if len(self.config.db2u_namespaces) == 0:
            # No Db2U resources scenario
            empty_list = MagicMock()
            empty_list.to_dict.return_value = {"items": []}
            db2ucluster_api.get.return_value = empty_list
            db2uinstance_api.get.return_value = empty_list
        else:
            # Create resources in specified namespaces
            resources = []
            for idx, namespace in enumerate(self.config.db2u_namespaces):
                resource = self.create_db2u_resource(
                    kind=self.config.db2u_resource_kind,
                    name=f"db2u-{idx + 1}",
                    namespace=namespace
                )
                resources.append(resource)

            mock_list = MagicMock()
            mock_list.to_dict.return_value = {"items": resources}

            # Set appropriate API based on resource kind
            if self.config.db2u_resource_kind == "Db2uCluster":
                db2ucluster_api.get.return_value = mock_list
                empty_list = MagicMock()
                empty_list.to_dict.return_value = {"items": []}
                db2uinstance_api.get.return_value = empty_list
            else:
                db2uinstance_api.get.return_value = mock_list
                empty_list = MagicMock()
                empty_list.to_dict.return_value = {"items": []}
                db2ucluster_api.get.return_value = empty_list

    def setup_kafka_mocks(self, kafka_api, subscription_api):
        """Setup Kafka API mocks based on configuration."""
        if len(self.config.kafka_namespaces) == 0:
            # No Kafka resources
            empty_list = MagicMock()
            empty_list.to_dict.return_value = {"items": []}
            kafka_api.get.return_value = empty_list
        else:
            # Create Kafka resources
            resources = []
            for idx, namespace in enumerate(self.config.kafka_namespaces):
                resource = self.create_kafka_resource(
                    name=f"kafka-{idx + 1}",
                    namespace=namespace
                )
                resources.append(resource)

            mock_list = MagicMock()
            mock_list.to_dict.return_value = {"items": resources}
            kafka_api.get.return_value = mock_list

        # Setup Kafka provider subscription mock
        if self.config.kafka_provider:
            sub_name = "amq-streams" if self.config.kafka_provider == "redhat" else "strimzi-kafka-operator"
            subscription = {
                "spec": {"name": sub_name}
            }
            sub_list = MagicMock()
            sub_list.to_dict.return_value = {"items": [subscription]}
            subscription_api.get.return_value = sub_list
        else:
            empty_list = MagicMock()
            empty_list.to_dict.return_value = {"items": []}
            subscription_api.get.return_value = empty_list

    def setup_mongodb_mocks(self, mongodb_api):
        """Setup MongoDB API mocks based on configuration."""
        if len(self.config.mongodb_namespaces) == 0:
            # No MongoDB resources
            empty_list = MagicMock()
            empty_list.to_dict.return_value = {"items": []}
            mongodb_api.get.return_value = empty_list
        else:
            # Create MongoDB resources
            resources = []
            for idx, namespace in enumerate(self.config.mongodb_namespaces):
                resource = self.create_mongodb_resource(
                    name=f"mongodb-{idx + 1}",
                    namespace=namespace
                )
                resources.append(resource)

            mock_list = MagicMock()
            mock_list.to_dict.return_value = {"items": resources}
            mongodb_api.get.return_value = mock_list

    def setup_prompt_handler(self, mixins_prompt, prompt_session_instance):
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

    def run_update_test(self):
        """
        Run the update test with all mocks configured.

        Raises:
            TimeoutError: If test times out
            AssertionError: If prompt verification fails or assertions fail
            SystemExit: If expect_system_exit is True and SystemExit is raised
        """
        self.setup_test_files()
        self.start_watchdog()

        system_exit_raised = False
        exit_code = None

        with mock.patch('mas.cli.cli.config'):
            dynamic_client, resource_apis = self.setup_mocks()

            # Use ExitStack to manage all patches dynamically (avoids "too many statically nested blocks" error)
            with contextlib.ExitStack() as stack:
                # Define all patches
                patches = [
                    ('dynamic_client_class', mock.patch('mas.cli.cli.DynamicClient')),
                    ('get_nodes', mock.patch('mas.cli.cli.getNodes')),
                    ('get_current_catalog', mock.patch('mas.cli.update.app.getCurrentCatalog')),
                    ('list_mas_instances', mock.patch('mas.cli.update.app.listMasInstances')),
                    ('list_aiservice_instances', mock.patch('mas.cli.update.app.listAiServiceInstances')),
                    ('get_cluster_version', mock.patch('mas.cli.update.app.getClusterVersion')),
                    ('install_pipelines', mock.patch('mas.cli.update.app.installOpenShiftPipelines')),
                    ('create_namespace', mock.patch('mas.cli.update.app.createNamespace')),
                    ('prepare_pipelines_namespace', mock.patch('mas.cli.update.app.preparePipelinesNamespace')),
                    ('update_tekton_definitions', mock.patch('mas.cli.update.app.updateTektonDefinitions')),
                    ('launch_update_pipeline', mock.patch('mas.cli.update.app.launchUpdatePipeline')),
                    ('mixins_prompt', mock.patch('mas.cli.displayMixins.prompt')),
                    ('prompt_session_class', mock.patch('mas.cli.displayMixins.PromptSession')),
                    ('get_catalog', mock.patch('mas.cli.update.app.getCatalog')),
                    ('is_cluster_version_in_range', mock.patch('mas.cli.update.app.isClusterVersionInRange')),
                    ('is_airgap_install', mock.patch('mas.cli.cli.isAirgapInstall')),
                    ('is_sno', mock.patch('mas.cli.cli.isSNO'))
                ]

                # Enter all context managers and store mocks in a dictionary
                mocks = {}
                for name, patch in patches:
                    mocks[name] = stack.enter_context(patch)

                # Configure mock return values
                mocks['dynamic_client_class'].return_value = dynamic_client

                # Return the architecture
                mocks['get_nodes'].return_value = [{'status': {'nodeInfo': {'architecture': self.config.architecture}}}]

                # getCurrentCatalog returns catalog info
                mocks['get_current_catalog'].return_value = {
                    'catalogId': self.config.installed_catalog_id,
                    'displayName': f'IBM Maximo Operator Catalog ({self.config.installed_catalog_id})',
                    'image': f'icr.io/cpopen/ibm-maximo-operator-catalog:{self.config.installed_catalog_id}'
                }

                # MAS and AI Service instances
                mocks['list_mas_instances'].return_value = self.config.mas_instances
                mocks['list_aiservice_instances'].return_value = self.config.aiservice_instances

                # Cluster version
                mocks['get_cluster_version'].return_value = self.config.ocp_version
                mocks['is_cluster_version_in_range'].return_value = True

                # Catalog info
                mocks['get_catalog'].return_value = {
                    'ocp_compatibility': ['4.16', '4.17', '4.18'],
                    'mongo_extras_version_default': '6.0.5',
                    'cpd_product_version_default': '5.2.0'
                }

                # Pipeline setup
                mocks['install_pipelines'].return_value = True
                mocks['launch_update_pipeline'].return_value = 'https://pipeline.test.maximo.ibm.com'

                # Cluster checks
                mocks['is_airgap_install'].return_value = False
                mocks['is_sno'].return_value = False

                # Configure PromptSession mock
                prompt_session_instance = MagicMock()
                mocks['prompt_session_class'].return_value = prompt_session_instance

                # Setup prompt handler
                self.setup_prompt_handler(mocks['mixins_prompt'], prompt_session_instance)

                try:
                    self.app = UpdateApp()
                    self.app.update(argv=self.config.argv)
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

                # Verify exit code if specified
                if self.config.expect_system_exit and self.config.expected_exit_code is not None:
                    if exit_code != self.config.expected_exit_code:
                        raise AssertionError(f"Expected exit code {self.config.expected_exit_code} but got {exit_code}")
                elif self.config.expect_system_exit and exit_code == 0:
                    raise AssertionError(f"Expected non-zero exit code but got {exit_code}")

                # Verify all prompts were matched (allow unmatched if SystemExit expected)
                if len(self.config.prompt_handlers) > 0:
                    self.prompt_tracker.verify_all_prompts_matched(allow_unmatched=self.config.expect_system_exit)


def run_update_test(tmpdir, config: UpdateTestConfig):
    """
    Convenience function to run an update test.

    Args:
        tmpdir: pytest tmpdir fixture
        config: Test configuration

    Raises:
        TimeoutError: If test times out
        AssertionError: If prompt verification or assertions fail
    """
    helper = UpdateTestHelper(tmpdir, config)
    helper.run_update_test()

# Made with Bob
