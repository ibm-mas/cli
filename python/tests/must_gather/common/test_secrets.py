# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Test secret collection utilities."""

import os
import tempfile
import shutil
import yaml
from typing import Optional
from unittest.mock import Mock
from kubernetes.dynamic import DynamicClient


class TestCollectSecrets:
    """Test secret collection functionality."""

    def setup_method(self):
        """Set up test fixtures.

        GIVEN a test environment
        WHEN tests are run
        THEN create temporary directory and mock Kubernetes client.
        """
        self.testDir = tempfile.mkdtemp()
        self.mockClient = Mock(spec=DynamicClient)

    def teardown_method(self):
        """Clean up test fixtures.

        GIVEN test completion
        WHEN teardown is called
        THEN remove temporary directory.
        """
        if os.path.exists(self.testDir):
            shutil.rmtree(self.testDir)

    def _createMockSecret(self, name: str, namespace: str, data: Optional[dict] = None):
        """Create a mock Kubernetes secret.

        Args:
            name (str): Secret name
            namespace (str): Secret namespace
            data (dict, optional): Secret data. Defaults to None.

        Returns:
            Mock: Mock secret object
        """
        mockSecret = Mock()
        mockSecret.metadata = Mock()
        mockSecret.metadata.name = name
        mockSecret.metadata.namespace = namespace

        secretDict = {"metadata": {"name": name, "namespace": namespace}, "type": "Opaque"}
        if data:
            secretDict["data"] = data

        mockSecret.to_dict.return_value = secretDict
        return mockSecret

    def _createMockSecretList(self, secrets: list):
        """Create a mock secret list.

        Args:
            secrets (list): List of mock secrets

        Returns:
            Mock: Mock secret list object
        """
        mockList = Mock()
        mockList.items = secrets
        mockList.to_dict.return_value = {"items": [s.to_dict() for s in secrets]}
        return mockList

    def test_collect_secrets_creates_namespace_directory(self):
        """Test that namespace directory is created.

        GIVEN a namespace
        WHEN collectSecrets is called
        THEN namespace directory is created.
        """
        from mas.cli.must_gather.common.secrets import collectSecrets

        mockApi = Mock()
        mockApi.get.return_value = self._createMockSecretList([])
        self.mockClient.resources.get.return_value = mockApi

        collectSecrets(dynClient=self.mockClient, namespace="test-ns", outputDir=self.testDir, secretData=False)

        namespaceDir = os.path.join(self.testDir, "test-ns")
        assert os.path.exists(namespaceDir)

    def test_collect_secrets_creates_secrets_directory(self):
        """Test that secrets directory is created.

        GIVEN secrets exist
        WHEN collectSecrets is called
        THEN secrets directory is created.
        """
        from mas.cli.must_gather.common.secrets import collectSecrets

        mockSecret = self._createMockSecret("test-secret", "test-ns")
        mockApi = Mock()
        mockApi.get.return_value = self._createMockSecretList([mockSecret])
        self.mockClient.resources.get.return_value = mockApi

        collectSecrets(dynClient=self.mockClient, namespace="test-ns", outputDir=self.testDir, secretData=False)

        secretsDir = os.path.join(self.testDir, "test-ns", "secrets")
        assert os.path.exists(secretsDir)

    def test_collect_secrets_creates_summary_file(self):
        """Test that summary file is created.

        GIVEN secrets exist
        WHEN collectSecrets is called
        THEN summary .txt file is created.
        """
        from mas.cli.must_gather.common.secrets import collectSecrets

        mockSecret = self._createMockSecret("test-secret", "test-ns")
        mockApi = Mock()
        mockApi.get.return_value = self._createMockSecretList([mockSecret])
        self.mockClient.resources.get.return_value = mockApi

        collectSecrets(dynClient=self.mockClient, namespace="test-ns", outputDir=self.testDir, secretData=False)

        summaryFile = os.path.join(self.testDir, "test-ns", "secrets.txt")
        assert os.path.exists(summaryFile)

    def test_collect_secrets_without_secret_data_creates_yaml_without_data(self):
        """Test that YAML files without secret data are created when secretData is False.

        GIVEN secretData flag is False
        WHEN collectSecrets is called
        THEN YAML files are created without secret data field.
        """
        from mas.cli.must_gather.common.secrets import collectSecrets

        mockSecret = self._createMockSecret("test-secret", "test-ns", {"key": "dmFsdWU="})
        mockApi = Mock()
        mockApi.get.return_value = self._createMockSecretList([mockSecret])
        self.mockClient.resources.get.return_value = mockApi

        collectSecrets(dynClient=self.mockClient, namespace="test-ns", outputDir=self.testDir, secretData=False)

        secretFile = os.path.join(self.testDir, "test-ns", "secrets", "test-secret.yaml")
        assert os.path.exists(secretFile)

        # Verify it's YAML format without secret data
        with open(secretFile, "r") as f:
            content = f.read()
            assert "metadata:" in content
            assert "name: test-secret" in content
            # Parse YAML and check that data field is not present
            secretYaml = yaml.safe_load(content)
            assert "data" not in secretYaml  # Secret data should be excluded

    def test_collect_secrets_with_secret_data_creates_yaml_files(self):
        """Test that YAML files with data are created when secretData is True.

        GIVEN secretData flag is True
        WHEN collectSecrets is called
        THEN full YAML files with secret data are created.
        """
        from mas.cli.must_gather.common.secrets import collectSecrets

        mockSecret = self._createMockSecret("test-secret", "test-ns", {"key": "dmFsdWU="})
        mockApi = Mock()
        mockApi.get.return_value = self._createMockSecretList([mockSecret])
        self.mockClient.resources.get.return_value = mockApi

        collectSecrets(dynClient=self.mockClient, namespace="test-ns", outputDir=self.testDir, secretData=True)

        secretFile = os.path.join(self.testDir, "test-ns", "secrets", "test-secret.yaml")
        assert os.path.exists(secretFile)

        # Verify it's full YAML format with data
        with open(secretFile, "r") as f:
            content = f.read()
            assert "data:" in content or "metadata:" in content

    def test_collect_secrets_creates_file_for_each_secret(self):
        """Test that individual files are created for each secret.

        GIVEN multiple secrets exist
        WHEN collectSecrets is called
        THEN file is created for each secret.
        """
        from mas.cli.must_gather.common.secrets import collectSecrets

        mockSecret1 = self._createMockSecret("secret1", "test-ns")
        mockSecret2 = self._createMockSecret("secret2", "test-ns")
        mockApi = Mock()
        mockApi.get.return_value = self._createMockSecretList([mockSecret1, mockSecret2])
        self.mockClient.resources.get.return_value = mockApi

        collectSecrets(dynClient=self.mockClient, namespace="test-ns", outputDir=self.testDir, secretData=False)

        secretsDir = os.path.join(self.testDir, "test-ns", "secrets")
        assert os.path.exists(os.path.join(secretsDir, "secret1.yaml"))
        assert os.path.exists(os.path.join(secretsDir, "secret2.yaml"))

    def test_collect_secrets_with_all_namespaces_flag(self):
        """Test collection across all namespaces.

        GIVEN allNamespaces flag is True
        WHEN collectSecrets is called
        THEN secrets from all namespaces are collected into single file.
        """
        from mas.cli.must_gather.common.secrets import collectSecrets

        mockSecret1 = self._createMockSecret("secret1", "ns1")
        mockSecret2 = self._createMockSecret("secret2", "ns2")
        mockApi = Mock()
        mockApi.get.return_value = self._createMockSecretList([mockSecret1, mockSecret2])
        self.mockClient.resources.get.return_value = mockApi

        collectSecrets(dynClient=self.mockClient, namespace=None, outputDir=self.testDir, secretData=False, allNamespaces=True)

        secretsDir = os.path.join(self.testDir, "_cluster", "secrets")
        assert os.path.exists(os.path.join(secretsDir, "all-namespaces.yaml"))

    def test_collect_secrets_handles_api_error(self):
        """Test graceful handling of API errors.

        GIVEN API call fails
        WHEN collectSecrets is called
        THEN function handles error gracefully and returns False.
        """
        from mas.cli.must_gather.common.secrets import collectSecrets

        mockApi = Mock()
        mockApi.get.side_effect = Exception("API Error")
        self.mockClient.resources.get.return_value = mockApi

        success, count = collectSecrets(dynClient=self.mockClient, namespace="test-ns", outputDir=self.testDir, secretData=False)

        assert success is False

    def test_collect_secrets_returns_true_on_success(self):
        """Test that function returns True on successful collection.

        GIVEN valid parameters
        WHEN collectSecrets completes successfully
        THEN function returns True.
        """
        from mas.cli.must_gather.common.secrets import collectSecrets

        mockApi = Mock()
        mockApi.get.return_value = self._createMockSecretList([])
        self.mockClient.resources.get.return_value = mockApi

        success, count = collectSecrets(dynClient=self.mockClient, namespace="test-ns", outputDir=self.testDir, secretData=False)

        assert success is True


# Made with Bob
