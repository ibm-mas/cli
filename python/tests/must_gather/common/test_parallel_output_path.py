# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for parallel resource collection output paths.

GIVEN a list of resources to collect
WHEN collectResourcesParallel is called with outputDir
THEN resources should be written to the correct directory without path duplication
"""

import os
import tempfile
import shutil
from unittest.mock import Mock, patch
from mas.cli.must_gather.common.parallel import collectResourcesParallel


def test_collectResourcesParallel_writes_to_correct_directory():
    """Test that resources are written to the correct output directory.

    GIVEN a mock DynamicClient and a list of resources
    WHEN collectResourcesParallel is called with outputDir="/tmp/test/resources"
    THEN resources should be written to "/tmp/test/resources/namespace/" not "/tmp/test/resources/resources/namespace/"
    """
    # Create temporary directory
    tempDir = tempfile.mkdtemp()
    try:
        outputDir = os.path.join(tempDir, "resources")
        namespace = "test-namespace"

        # Mock DynamicClient
        mockDynClient = Mock()
        mockApi = Mock()
        mockResources = Mock()
        mockResources.items = [Mock(metadata=Mock(name="test-resource"), to_dict=Mock(return_value={"metadata": {"name": "test-resource"}}))]

        mockApi.get.return_value = mockResources
        mockDynClient.resources.get.return_value = mockApi

        # Mock getPrinterColumns to return a simple column
        with patch("mas.cli.must_gather.common.resources.getPrinterColumns") as mockGetPrinterColumns:
            from mas.cli.must_gather.common.crd_processor import PrinterColumn

            mockGetPrinterColumns.return_value = [PrinterColumn(name="Name", type="string", jsonPath=".metadata.name")]

            # Call collectResourcesParallel
            resources = [("v1", "ConfigMap")]
            result = collectResourcesParallel(
                dynClient=mockDynClient, namespace=namespace, resources=resources, outputDir=outputDir, noDetail=False, max_workers=1
            )

            # Verify success
            assert result is True

            # Verify files are in correct location
            expectedNamespaceDir = os.path.join(outputDir, namespace)
            expectedMarkdownFile = os.path.join(expectedNamespaceDir, "configmaps.md")
            expectedResourceDir = os.path.join(expectedNamespaceDir, "configmaps")

            # Check that files exist in correct location
            assert os.path.exists(expectedMarkdownFile), f"Markdown file should exist at {expectedMarkdownFile}"
            assert os.path.exists(expectedResourceDir), f"Resource directory should exist at {expectedResourceDir}"

            # Check that files do NOT exist in wrong location (with duplicate /resources/)
            wrongNamespaceDir = os.path.join(outputDir, "resources", namespace)
            wrongMarkdownFile = os.path.join(wrongNamespaceDir, "configmaps.md")

            assert not os.path.exists(wrongMarkdownFile), f"Markdown file should NOT exist at {wrongMarkdownFile} (path duplication bug)"

    finally:
        # Cleanup
        shutil.rmtree(tempDir)


def test_collectResourcesParallel_ibm_resources_correct_path():
    """Test that IBM resources are written to the correct path.

    GIVEN a list of IBM CRD resources
    WHEN collectResourcesParallel is called
    THEN IBM resources should be in outputDir/namespace/ not outputDir/resources/namespace/
    """
    # Create temporary directory
    tempDir = tempfile.mkdtemp()
    try:
        outputDir = os.path.join(tempDir, "resources")
        namespace = "mas-core"

        # Mock DynamicClient
        mockDynClient = Mock()
        mockApi = Mock()
        mockResources = Mock()
        mockResources.items = [
            Mock(
                metadata=Mock(name="test-suite"),
                to_dict=Mock(return_value={"metadata": {"name": "test-suite", "creationTimestamp": "2024-01-01T00:00:00Z"}}),
            )
        ]

        mockApi.get.return_value = mockResources
        mockDynClient.resources.get.return_value = mockApi

        # Mock getPrinterColumns
        with patch("mas.cli.must_gather.common.resources.getPrinterColumns") as mockGetPrinterColumns:
            from mas.cli.must_gather.common.crd_processor import PrinterColumn

            mockGetPrinterColumns.return_value = [
                PrinterColumn(name="Name", type="string", jsonPath=".metadata.name"),
                PrinterColumn(name="Age", type="date", jsonPath=".metadata.creationTimestamp"),
            ]

            # Call with IBM CRD
            resources = [("core.mas.ibm.com/v1", "Suite")]
            result = collectResourcesParallel(
                dynClient=mockDynClient, namespace=namespace, resources=resources, outputDir=outputDir, noDetail=False, max_workers=1
            )

            # Verify success
            assert result is True

            # Verify IBM resources are in correct location
            expectedNamespaceDir = os.path.join(outputDir, namespace)
            expectedMarkdownFile = os.path.join(expectedNamespaceDir, "suites.md")
            expectedResourceDir = os.path.join(expectedNamespaceDir, "suites")

            assert os.path.exists(expectedMarkdownFile), f"Suite markdown should exist at {expectedMarkdownFile}"
            assert os.path.exists(expectedResourceDir), f"Suite directory should exist at {expectedResourceDir}"

            # Verify NOT in wrong location
            wrongPath = os.path.join(outputDir, "resources", namespace, "suites.md")
            assert not os.path.exists(wrongPath), f"Suite markdown should NOT exist at {wrongPath}"

    finally:
        # Cleanup
        shutil.rmtree(tempDir)


# Made with Bob
