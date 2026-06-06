# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for CRD processor module."""

import os
import tempfile
from unittest.mock import Mock
from mas.cli.must_gather.common.crd_processor import (
    PrinterColumn,
    CRDInfo,
    processCRDs,
    getPrinterColumns,
    extractValueFromJsonPath,
)


class TestPrinterColumn:
    """Test PrinterColumn dataclass."""

    def test_printer_column_creation(self):
        """Test that PrinterColumn can be created with all fields.

        GIVEN printer column attributes
        WHEN PrinterColumn is instantiated
        THEN all attributes are set correctly.
        """
        column = PrinterColumn(name="Status", type="string", jsonPath=".status.phase", description="Current status", priority=0)

        assert column.name == "Status"
        assert column.type == "string"
        assert column.jsonPath == ".status.phase"
        assert column.description == "Current status"
        assert column.priority == 0


class TestCRDInfo:
    """Test CRDInfo dataclass."""

    def test_crd_info_creation(self):
        """Test that CRDInfo can be created with all fields.

        GIVEN CRD attributes including printer columns
        WHEN CRDInfo is instantiated
        THEN all attributes are set correctly.
        """
        printerColumns = [PrinterColumn("Status", "string", ".status.phase", "Status", 0)]
        crdInfo = CRDInfo(kind="Suite", apiVersion="core.mas.ibm.com/v1", group="core.mas.ibm.com", printerColumns=printerColumns, isIBM=True)

        assert crdInfo.kind == "Suite"
        assert crdInfo.apiVersion == "core.mas.ibm.com/v1"
        assert crdInfo.group == "core.mas.ibm.com"
        assert len(crdInfo.printerColumns) == 1
        assert crdInfo.isIBM is True


class TestExtractValueFromJsonPath:
    """Test JSONPath value extraction."""

    def test_extract_simple_field(self):
        """Test extracting a simple top-level field.

        GIVEN a resource with a simple field
        WHEN extractValueFromJsonPath is called with simple path
        THEN the field value is returned.
        """
        resource = {"metadata": {"name": "test-resource"}}
        value = extractValueFromJsonPath(resource, ".metadata.name")
        assert value == "test-resource"

    def test_extract_nested_field(self):
        """Test extracting a nested field.

        GIVEN a resource with nested fields
        WHEN extractValueFromJsonPath is called with nested path
        THEN the nested field value is returned.
        """
        resource = {"status": {"conditions": [{"type": "Ready", "status": "True"}]}}
        value = extractValueFromJsonPath(resource, ".status.conditions[0].status")
        assert value == "True"

    def test_extract_missing_field_returns_empty(self):
        """Test extracting a missing field returns empty string.

        GIVEN a resource without the requested field
        WHEN extractValueFromJsonPath is called
        THEN empty string is returned.
        """
        resource = {"metadata": {"name": "test"}}
        value = extractValueFromJsonPath(resource, ".status.phase")
        assert value == ""

    def test_extract_with_filter_expression(self):
        """Test extracting with JSONPath filter expression.

        GIVEN a resource with array and filter condition
        WHEN extractValueFromJsonPath is called with filter
        THEN the filtered value is returned.
        """
        resource = {"status": {"conditions": [{"type": "Ready", "status": "True"}, {"type": "Available", "status": "False"}]}}
        value = extractValueFromJsonPath(resource, '.status.conditions[?(@.type=="Ready")].status')
        assert value == "True"


class TestGetPrinterColumns:
    """Test printer column lookup."""

    def test_get_printer_columns_for_unknown_resource_returns_name_only(self):
        """Test that unknown resources return name-only column.

        GIVEN an unknown resource kind and apiVersion
        WHEN getPrinterColumns is called
        THEN a single Name column is returned.
        """
        columns = getPrinterColumns("UnknownKind", "v1")
        assert len(columns) == 1
        assert columns[0].name == "Name"
        assert columns[0].jsonPath == ".metadata.name"


class TestProcessCRDs:
    """Test CRD processing."""

    def test_process_crds_identifies_ibm_crds(self):
        """Test that IBM CRDs are correctly identified.

        GIVEN a cluster with IBM and non-IBM CRDs
        WHEN processCRDs is called
        THEN IBM CRDs are identified and returned separately.
        """
        # Create mock CRDs
        ibmCRD = {
            "metadata": {"name": "suites.core.mas.ibm.com"},
            "spec": {
                "group": "core.mas.ibm.com",
                "names": {"kind": "Suite"},
                "versions": [
                    {
                        "name": "v1",
                        "served": True,
                        "storage": True,
                        "additionalPrinterColumns": [{"name": "Status", "type": "string", "jsonPath": ".status.phase"}],
                    }
                ],
            },
        }

        nonIBMCRD = {
            "metadata": {"name": "kafkas.kafka.strimzi.io"},
            "spec": {
                "group": "kafka.strimzi.io",
                "names": {"kind": "Kafka"},
                "versions": [{"name": "v1beta2", "served": True, "storage": True, "additionalPrinterColumns": []}],
            },
        }

        # Mock DynamicClient
        mockClient = Mock()
        mockCRDApi = Mock()
        mockCRDList = Mock()
        mockCRDList.items = [Mock(to_dict=lambda: ibmCRD), Mock(to_dict=lambda: nonIBMCRD)]
        mockCRDApi.get.return_value = mockCRDList
        mockClient.resources.get.return_value = mockCRDApi

        # Create temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            printerColumnsCache, ibmCRDsList = processCRDs(mockClient, tmpdir)

            # Verify IBM CRD identified
            assert len(ibmCRDsList) == 1
            assert ibmCRDsList[0] == ("Suite", "core.mas.ibm.com/v1")

            # Verify printer columns cached
            assert ("Suite", "core.mas.ibm.com/v1") in printerColumnsCache

    def test_process_crds_extracts_printer_columns(self):
        """Test that printer columns are extracted from CRDs.

        GIVEN a CRD with additionalPrinterColumns
        WHEN processCRDs is called
        THEN printer columns are extracted and cached.
        """
        crd = {
            "metadata": {"name": "suites.core.mas.ibm.com"},
            "spec": {
                "group": "core.mas.ibm.com",
                "names": {"kind": "Suite"},
                "versions": [
                    {
                        "name": "v1",
                        "served": True,
                        "storage": True,
                        "additionalPrinterColumns": [
                            {"name": "Status", "type": "string", "jsonPath": ".status.phase", "description": "Current phase"},
                            {"name": "Age", "type": "date", "jsonPath": ".metadata.creationTimestamp"},
                        ],
                    }
                ],
            },
        }

        mockClient = Mock()
        mockCRDApi = Mock()
        mockCRDList = Mock()
        mockCRDList.items = [Mock(to_dict=lambda: crd)]
        mockCRDApi.get.return_value = mockCRDList
        mockClient.resources.get.return_value = mockCRDApi

        with tempfile.TemporaryDirectory() as tmpdir:
            printerColumnsCache, _ = processCRDs(mockClient, tmpdir)

            columns = printerColumnsCache[("Suite", "core.mas.ibm.com/v1")]
            assert len(columns) == 2
            assert columns[0].name == "Status"
            assert columns[0].jsonPath == ".status.phase"
            assert columns[1].name == "Age"

    def test_process_crds_writes_individual_files_and_index(self):
        """Test that CRDs are written to individual files with markdown index.

        GIVEN CRDs in the cluster
        WHEN processCRDs is called
        THEN each CRD is written to its own file and a markdown index is created.
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

            # Verify individual CRD file exists
            crdFile = os.path.join(tmpdir, "_cluster", "customresourcedefinitions", "suites.core.mas.ibm.com.yaml")
            assert os.path.exists(crdFile)

            # Verify markdown index exists
            indexFile = os.path.join(tmpdir, "_cluster", "customresourcedefinitions.md")
            assert os.path.exists(indexFile)
