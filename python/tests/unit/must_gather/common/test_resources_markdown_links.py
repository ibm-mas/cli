# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for markdown link generation in resource index files."""

import os
import tempfile
from unittest.mock import Mock
from mas.cli.must_gather.common.resources import _writeMarkdownIndex
from mas.cli.must_gather.common.crd_processor import PrinterColumn


class TestMarkdownLinkGeneration:
    """Test markdown link generation in index files."""

    def test_write_markdown_index_with_name_links(self):
        """Test that resource names in first column are converted to links.

        GIVEN resources with names
        WHEN _writeMarkdownIndex is called
        THEN first column contains markdown links to YAML files.
        """
        mockResource1 = Mock()
        mockResource1.metadata.name = "test-suite-1"
        mockResource1.to_dict.return_value = {"metadata": {"name": "test-suite-1"}, "status": {"phase": "Ready"}}

        mockResource2 = Mock()
        mockResource2.metadata.name = "test-suite-2"
        mockResource2.to_dict.return_value = {"metadata": {"name": "test-suite-2"}, "status": {"phase": "Pending"}}

        mockResources = Mock()
        mockResources.items = [mockResource1, mockResource2]

        printerColumns = [
            PrinterColumn("Name", "string", ".metadata.name", "Resource name", 0),
            PrinterColumn("Status", "string", ".status.phase", "Current phase", 0),
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as f:
            outputFile = f.name

        try:
            _writeMarkdownIndex(mockResources, outputFile, "Suite", "core.mas.ibm.com/v1", printerColumns)

            with open(outputFile, "r") as f:
                content = f.read()

            # Verify markdown links are created for resource names
            assert (
                "[test-suite-1](suites/test-suite-1.yaml)" in content
            ), f"Markdown should contain link '[test-suite-1](suites/test-suite-1.yaml)' for first resource, but content is: {content}"
            assert (
                "[test-suite-2](suites/test-suite-2.yaml)" in content
            ), f"Markdown should contain link '[test-suite-2](suites/test-suite-2.yaml)' for second resource, but content is: {content}"

            # Verify status values are NOT links
            assert "[Ready]" not in content or "Ready" in content, f"Status values should not be converted to links, but found '[Ready]' in content: {content}"
            assert (
                "[Pending]" not in content or "Pending" in content
            ), f"Status values should not be converted to links, but found '[Pending]' in content: {content}"

        finally:
            os.unlink(outputFile)

    def test_write_markdown_index_links_use_plural_directory(self):
        """Test that links use pluralized resource kind as directory.

        GIVEN resources of different kinds
        WHEN _writeMarkdownIndex is called
        THEN links use plural form of kind (e.g., pods, suites, catalogsources).
        """
        mockResource = Mock()
        mockResource.metadata.name = "my-catalog"
        mockResource.to_dict.return_value = {"metadata": {"name": "my-catalog"}}

        mockResources = Mock()
        mockResources.items = [mockResource]

        printerColumns = [PrinterColumn("Name", "string", ".metadata.name", "Resource name", 0)]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as f:
            outputFile = f.name

        try:
            _writeMarkdownIndex(mockResources, outputFile, "CatalogSource", "operators.coreos.com/v1alpha1", printerColumns)

            with open(outputFile, "r") as f:
                content = f.read()

            # Should use plural form
            assert (
                "[my-catalog](catalogsources/my-catalog.yaml)" in content
            ), f"Markdown link should use plural directory name 'catalogsources', but content is: {content}"

        finally:
            os.unlink(outputFile)

    def test_write_markdown_index_only_first_column_linked(self):
        """Test that only the first column (name) gets links.

        GIVEN resources with multiple columns
        WHEN _writeMarkdownIndex is called
        THEN only first column values are converted to links.
        """
        mockResource = Mock()
        mockResource.metadata.name = "test-pod"
        mockResource.to_dict.return_value = {"metadata": {"name": "test-pod"}, "status": {"phase": "Running"}, "spec": {"nodeName": "worker-1"}}

        mockResources = Mock()
        mockResources.items = [mockResource]

        printerColumns = [
            PrinterColumn("Name", "string", ".metadata.name", "Pod name", 0),
            PrinterColumn("Status", "string", ".status.phase", "Phase", 0),
            PrinterColumn("Node", "string", ".spec.nodeName", "Node name", 0),
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as f:
            outputFile = f.name

        try:
            _writeMarkdownIndex(mockResources, outputFile, "Pod", "v1", printerColumns)

            with open(outputFile, "r") as f:
                content = f.read()

            # First column should be a link
            assert (
                "[test-pod](pods/test-pod.yaml)" in content
            ), f"First column (Name) should be converted to link '[test-pod](pods/test-pod.yaml)', but content is: {content}"

            # Other columns should NOT be links
            assert "[Running]" not in content, f"Status column should not be converted to link, but found '[Running]' in content: {content}"
            assert "[worker-1]" not in content, f"Node column should not be converted to link, but found '[worker-1]' in content: {content}"

        finally:
            os.unlink(outputFile)
