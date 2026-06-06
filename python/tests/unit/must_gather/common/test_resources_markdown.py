# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for markdown index generation in resources module."""

import os
import tempfile
from unittest.mock import Mock
from mas.cli.must_gather.common.resources import _writeMarkdownIndex
from mas.cli.must_gather.common.crd_processor import PrinterColumn


class TestMarkdownIndexGeneration:
    """Test markdown index file generation."""

    def test_write_markdown_index_with_printer_columns(self):
        """Test markdown generation with CRD printer columns.

        GIVEN resources and printer columns from CRD
        WHEN _writeMarkdownIndex is called
        THEN markdown file is created with proper table format.
        """
        # Create mock resources
        mockResource1 = Mock()
        mockResource1.metadata.name = "test-suite-1"
        mockResource1.to_dict.return_value = {"metadata": {"name": "test-suite-1"}, "status": {"phase": "Ready"}}

        mockResource2 = Mock()
        mockResource2.metadata.name = "test-suite-2"
        mockResource2.to_dict.return_value = {"metadata": {"name": "test-suite-2"}, "status": {"phase": "Pending"}}

        mockResources = Mock()
        mockResources.items = [mockResource1, mockResource2]

        # Define printer columns
        printerColumns = [
            PrinterColumn("Name", "string", ".metadata.name", "Resource name", 0),
            PrinterColumn("Status", "string", ".status.phase", "Current phase", 0),
        ]

        # Write markdown
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as f:
            outputFile = f.name

        try:
            _writeMarkdownIndex(mockResources, outputFile, "Suite", "core.mas.ibm.com/v1", printerColumns)

            # Read and verify content
            with open(outputFile, "r") as f:
                content = f.read()

            # Verify header
            assert "# Suite (core.mas.ibm.com/v1)" in content

            # Verify table header
            assert "| Name |" in content
            assert "| Status |" in content

            # Verify separator
            assert "|---|" in content or "| --- |" in content

            # Verify data rows
            assert "test-suite-1" in content
            assert "test-suite-2" in content
            assert "Ready" in content
            assert "Pending" in content

        finally:
            os.unlink(outputFile)

    def test_write_markdown_index_with_default_columns(self):
        """Test markdown generation with default name-only column.

        GIVEN resources without printer columns
        WHEN _writeMarkdownIndex is called with empty columns
        THEN markdown file shows only Name column.
        """
        mockResource = Mock()
        mockResource.metadata.name = "test-resource"
        mockResource.to_dict.return_value = {"metadata": {"name": "test-resource"}}

        mockResources = Mock()
        mockResources.items = [mockResource]

        # Empty printer columns (should default to name only)
        printerColumns = [PrinterColumn("Name", "string", ".metadata.name", "Resource name", 0)]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as f:
            outputFile = f.name

        try:
            _writeMarkdownIndex(mockResources, outputFile, "CustomResource", "example.com/v1", printerColumns)

            with open(outputFile, "r") as f:
                content = f.read()

            assert "# CustomResource (example.com/v1)" in content
            assert "| Name |" in content
            assert "test-resource" in content

        finally:
            os.unlink(outputFile)

    def test_write_markdown_index_empty_resources(self):
        """Test markdown generation with no resources.

        GIVEN empty resource list
        WHEN _writeMarkdownIndex is called
        THEN markdown file indicates no resources found.
        """
        mockResources = Mock()
        mockResources.items = []

        printerColumns = [PrinterColumn("Name", "string", ".metadata.name", "Resource name", 0)]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as f:
            outputFile = f.name

        try:
            _writeMarkdownIndex(mockResources, outputFile, "Pod", "v1", printerColumns)

            with open(outputFile, "r") as f:
                content = f.read()

            assert "# Pod (v1)" in content
            assert "no resources found" in content.lower()

        finally:
            os.unlink(outputFile)

    def test_write_markdown_index_with_complex_jsonpath(self):
        """Test markdown generation with complex JSONPath expressions.

        GIVEN resources with nested fields
        WHEN _writeMarkdownIndex is called with complex JSONPath
        THEN values are correctly extracted and displayed.
        """
        mockResource = Mock()
        mockResource.metadata.name = "test-pod"
        mockResource.to_dict.return_value = {
            "metadata": {"name": "test-pod"},
            "status": {"phase": "Running", "conditions": [{"type": "Ready", "status": "True"}]},
        }

        mockResources = Mock()
        mockResources.items = [mockResource]

        printerColumns = [
            PrinterColumn("Name", "string", ".metadata.name", "Pod name", 0),
            PrinterColumn("Ready", "string", '.status.conditions[?(@.type=="Ready")].status', "Ready status", 0),
            PrinterColumn("Status", "string", ".status.phase", "Phase", 0),
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as f:
            outputFile = f.name

        try:
            _writeMarkdownIndex(mockResources, outputFile, "Pod", "v1", printerColumns)

            with open(outputFile, "r") as f:
                content = f.read()

            assert "test-pod" in content
            assert "True" in content
            assert "Running" in content

        finally:
            os.unlink(outputFile)

    def test_write_markdown_index_handles_missing_fields(self):
        """Test markdown generation handles missing fields gracefully.

        GIVEN resources with missing fields
        WHEN _writeMarkdownIndex is called
        THEN empty values are shown without errors.
        """
        mockResource = Mock()
        mockResource.metadata.name = "incomplete-resource"
        mockResource.to_dict.return_value = {
            "metadata": {"name": "incomplete-resource"}
            # Missing status field
        }

        mockResources = Mock()
        mockResources.items = [mockResource]

        printerColumns = [PrinterColumn("Name", "string", ".metadata.name", "Name", 0), PrinterColumn("Status", "string", ".status.phase", "Phase", 0)]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as f:
            outputFile = f.name

        try:
            _writeMarkdownIndex(mockResources, outputFile, "Resource", "v1", printerColumns)

            with open(outputFile, "r") as f:
                content = f.read()

            assert "incomplete-resource" in content
            # Should handle missing status gracefully

        finally:
            os.unlink(outputFile)
