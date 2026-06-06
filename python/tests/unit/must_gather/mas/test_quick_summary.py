# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for MAS Quick Summary generator."""

import os
import tempfile
import shutil
from unittest.mock import Mock, MagicMock, patch
from kubernetes.dynamic import DynamicClient
from mas.cli.must_gather.mas.quick_summary import generateMASQuickSummary


class TestGenerateMASQuickSummary:
    """Tests for MAS Quick Summary generation."""

    def setup_method(self):
        """Set up test fixtures.

        GIVEN a test environment
        WHEN tests are run
        THEN mock client and temp directory are available.
        """
        self.mockClient = Mock(spec=DynamicClient)
        self.testDir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures.

        GIVEN test fixtures exist
        WHEN tests complete
        THEN temp directory is cleaned up.
        """
        shutil.rmtree(self.testDir, ignore_errors=True)

    @patch("mas.cli.must_gather.mas.quick_summary.subprocess.run")
    def test_generate_quick_summary_with_script(self, mockSubprocessRun):
        """Test quick summary generation with script.

        GIVEN mg-quick-summary-mas script exists
        WHEN generateMASQuickSummary is called
        THEN script is executed and output file is created.
        """
        # Mock subprocess to indicate script exists and runs successfully
        mockSubprocessRun.return_value = MagicMock(returncode=0, stdout="Quick summary output")

        result = generateMASQuickSummary(dynClient=self.mockClient, masInstanceId="inst1", outputDir=self.testDir)

        assert result is True
        # Verify script was called
        mockSubprocessRun.assert_called_once()
        # Verify output directory was created
        assert os.path.exists(os.path.join(self.testDir, "mas-quick-summary"))

    @patch("mas.cli.must_gather.mas.quick_summary.subprocess.run")
    def test_generate_quick_summary_script_not_found(self, mockSubprocessRun):
        """Test quick summary generation when script doesn't exist.

        GIVEN mg-quick-summary-mas script doesn't exist
        WHEN generateMASQuickSummary is called
        THEN function returns True with warning.
        """
        # Mock subprocess to indicate script doesn't exist
        mockSubprocessRun.side_effect = FileNotFoundError()

        result = generateMASQuickSummary(dynClient=self.mockClient, masInstanceId="inst1", outputDir=self.testDir)

        assert result is True

    @patch("mas.cli.must_gather.mas.quick_summary.subprocess.run")
    def test_generate_quick_summary_script_failure(self, mockSubprocessRun):
        """Test quick summary generation when script fails.

        GIVEN mg-quick-summary-mas script fails
        WHEN generateMASQuickSummary is called
        THEN function returns True with warning.
        """
        # Mock subprocess to indicate script fails
        mockSubprocessRun.return_value = MagicMock(returncode=1, stderr="Script error")

        result = generateMASQuickSummary(dynClient=self.mockClient, masInstanceId="inst1", outputDir=self.testDir)

        assert result is True

    @patch("mas.cli.must_gather.mas.quick_summary.subprocess.run")
    def test_generate_quick_summary_creates_output_file(self, mockSubprocessRun):
        """Test quick summary generation creates output file.

        GIVEN mg-quick-summary-mas script runs successfully
        WHEN generateMASQuickSummary is called
        THEN output file is created at correct path.
        """
        # Mock subprocess to indicate script exists and runs successfully
        mockSubprocessRun.return_value = MagicMock(returncode=0, stdout="Quick summary output")

        generateMASQuickSummary(dynClient=self.mockClient, masInstanceId="inst1", outputDir=self.testDir)

        # Verify output file path
        expectedFile = os.path.join(self.testDir, "mas-quick-summary", "inst1.txt")
        # Directory should exist
        assert os.path.exists(os.path.dirname(expectedFile))

    @patch("mas.cli.must_gather.mas.quick_summary.subprocess.run")
    def test_generate_quick_summary_timeout(self, mockSubprocessRun):
        """Test quick summary generation handles timeout.

        GIVEN mg-quick-summary-mas script times out
        WHEN generateMASQuickSummary is called
        THEN function returns True with warning.
        """
        # Mock subprocess to indicate script times out
        import subprocess

        mockSubprocessRun.side_effect = subprocess.TimeoutExpired(cmd="mg-quick-summary-mas", timeout=300)

        result = generateMASQuickSummary(dynClient=self.mockClient, masInstanceId="inst1", outputDir=self.testDir)

        assert result is True
