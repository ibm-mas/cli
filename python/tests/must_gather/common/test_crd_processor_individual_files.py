# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for CRD processor individual file storage."""

import os
import tempfile
import yaml
from unittest.mock import Mock
from mas.cli.must_gather.common.crd_processor import processCRDs


class TestProcessCRDsIndividualFiles:
    """Test CRD processing with individual file storage."""

    def test_process_crds_writes_individual_yaml_files(self):
        """Test that each CRD is written to its own YAML file.

        GIVEN multiple CRDs in the cluster
        WHEN processCRDs is called
        THEN each CRD is written to customresourcedefinitions/{name}.yaml.
        """
        crd1 = {
            "metadata": {"name": "suites.core.mas.ibm.com"},
            "spec": {"group": "core.mas.ibm.com", "names": {"kind": "Suite"}, "versions": [{"name": "v1", "served": True, "storage": True}]},
        }

        crd2 = {
            "metadata": {"name": "kafkas.kafka.strimzi.io"},
            "spec": {"group": "kafka.strimzi.io", "names": {"kind": "Kafka"}, "versions": [{"name": "v1beta2", "served": True, "storage": True}]},
        }

        mockClient = Mock()
        mockCRDApi = Mock()
        mockCRDList = Mock()
        mockCRDList.items = [Mock(to_dict=lambda: crd1), Mock(to_dict=lambda: crd2)]
        mockCRDApi.get.return_value = mockCRDList
        mockClient.resources.get.return_value = mockCRDApi

        with tempfile.TemporaryDirectory() as tmpdir:
            processCRDs(mockClient, tmpdir)

            # Verify individual CRD files exist
            crdDir = os.path.join(tmpdir, "resources", "_cluster", "customresourcedefinitions")
            assert os.path.exists(crdDir)

            crd1File = os.path.join(crdDir, "suites.core.mas.ibm.com.yaml")
            assert os.path.exists(crd1File)

            crd2File = os.path.join(crdDir, "kafkas.kafka.strimzi.io.yaml")
            assert os.path.exists(crd2File)

            # Verify content of first CRD file
            with open(crd1File, "r") as f:
                loadedCRD = yaml.safe_load(f)
                assert loadedCRD["metadata"]["name"] == "suites.core.mas.ibm.com"

    def test_process_crds_generates_markdown_index(self):
        """Test that a markdown index file is generated for CRDs.

        GIVEN multiple CRDs in the cluster
        WHEN processCRDs is called
        THEN a customresourcedefinitions.md index file is created.
        """
        crd1 = {
            "metadata": {"name": "suites.core.mas.ibm.com", "creationTimestamp": "2024-01-01T00:00:00Z"},
            "spec": {
                "group": "core.mas.ibm.com",
                "names": {"kind": "Suite", "plural": "suites"},
                "versions": [{"name": "v1", "served": True, "storage": True}],
            },
        }

        crd2 = {
            "metadata": {"name": "kafkas.kafka.strimzi.io", "creationTimestamp": "2024-01-02T00:00:00Z"},
            "spec": {
                "group": "kafka.strimzi.io",
                "names": {"kind": "Kafka", "plural": "kafkas"},
                "versions": [{"name": "v1beta2", "served": True, "storage": True}],
            },
        }

        mockClient = Mock()
        mockCRDApi = Mock()
        mockCRDList = Mock()
        mockCRDList.items = [Mock(to_dict=lambda: crd1), Mock(to_dict=lambda: crd2)]
        mockCRDApi.get.return_value = mockCRDList
        mockClient.resources.get.return_value = mockCRDApi

        with tempfile.TemporaryDirectory() as tmpdir:
            processCRDs(mockClient, tmpdir)

            # Verify markdown index exists
            indexFile = os.path.join(tmpdir, "resources", "_cluster", "customresourcedefinitions.md")
            assert os.path.exists(indexFile)

            # Verify markdown content
            with open(indexFile, "r") as f:
                content = f.read()
                assert "# CustomResourceDefinition" in content
                assert "| Name |" in content
                assert "[suites.core.mas.ibm.com](customresourcedefinitions/suites.core.mas.ibm.com.yaml)" in content
                assert "[kafkas.kafka.strimzi.io](customresourcedefinitions/kafkas.kafka.strimzi.io.yaml)" in content

    def test_process_crds_does_not_create_single_yaml_file(self):
        """Test that the old single YAML file is not created.

        GIVEN CRDs in the cluster
        WHEN processCRDs is called
        THEN customresourcedefinitions.yaml is NOT created.
        """
        crd = {
            "metadata": {"name": "suites.core.mas.ibm.com"},
            "spec": {"group": "core.mas.ibm.com", "names": {"kind": "Suite"}, "versions": [{"name": "v1", "served": True, "storage": True}]},
        }

        mockClient = Mock()
        mockCRDApi = Mock()
        mockCRDList = Mock()
        mockCRDList.items = [Mock(to_dict=lambda: crd)]
        mockCRDApi.get.return_value = mockCRDList
        mockClient.resources.get.return_value = mockCRDApi

        with tempfile.TemporaryDirectory() as tmpdir:
            processCRDs(mockClient, tmpdir)

            # Verify old single file does NOT exist
            oldFile = os.path.join(tmpdir, "resources", "_cluster", "customresourcedefinitions.yaml")
            assert not os.path.exists(oldFile)
