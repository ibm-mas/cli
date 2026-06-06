# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Test OCP collection integration in MustGatherApp."""

import tempfile
import shutil
from unittest.mock import Mock, patch
from mas.cli.must_gather.app import MustGatherApp


class TestMustGatherAppOCP:
    """Test OCP collection integration."""

    def setup_method(self):
        """Set up test fixtures.

        GIVEN a test environment
        WHEN tests are run
        THEN create MustGatherApp instance.
        """
        self.app = MustGatherApp()
        self.testDir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures.

        GIVEN test completion
        WHEN teardown is called
        THEN remove temporary directory.
        """
        if self.testDir:
            shutil.rmtree(self.testDir, ignore_errors=True)

    @patch("mas.cli.must_gather.ocp.collectClusterResources")
    @patch("mas.cli.must_gather.ocp.collectNodes")
    @patch("mas.cli.must_gather.ocp.collectAirgapResources")
    @patch("mas.cli.must_gather.ocp.collectMarketplaceResources")
    @patch("mas.cli.must_gather.ocp.collectOperatorResources")
    def test_collect_ocp_calls_all_collectors(self, mockOperators, mockMarketplace, mockAirgap, mockNodes, mockCluster):
        """Test that collectOCP calls all OCP collectors.

        GIVEN OCP collection is enabled
        WHEN collectOCP is called
        THEN all OCP collectors are invoked.
        """
        # Setup mocks
        mockCluster.return_value = (True, {}, [])
        mockNodes.return_value = True
        mockAirgap.return_value = True
        mockMarketplace.return_value = True
        mockOperators.return_value = True

        # Initialize client
        self.app.dynClient = Mock()

        # Call collectOCP
        result = self.app.collectOCP(outputDir=self.testDir, noDetail=False)

        assert result is True
        mockCluster.assert_called_once()
        mockNodes.assert_called_once()
        mockAirgap.assert_called_once()
        mockMarketplace.assert_called_once()

    @patch("mas.cli.must_gather.ocp.collectClusterResources")
    def test_collect_ocp_respects_no_detail_flag(self, mockCluster):
        """Test that noDetail flag is passed to collectors.

        GIVEN noDetail=True
        WHEN collectOCP is called
        THEN collectors receive noDetail=True.
        """
        mockCluster.return_value = (True, {}, [])
        self.app.dynClient = Mock()

        self.app.collectOCP(outputDir=self.testDir, noDetail=True)

        # Verify noDetail was passed
        mockCluster.assert_called_once_with(dynClient=self.app.dynClient, outputDir=f"{self.testDir}/resources", noDetail=True)

    @patch("mas.cli.must_gather.ocp.collectClusterResources")
    @patch("mas.cli.must_gather.ocp.collectNodes")
    def test_collect_ocp_continues_on_partial_failure(self, mockNodes, mockCluster):
        """Test that collection continues even if some collectors fail.

        GIVEN one collector fails
        WHEN collectOCP is called
        THEN other collectors still run and True is returned.
        """
        mockCluster.return_value = (False, {}, [])  # Fails
        mockNodes.return_value = True  # Succeeds
        self.app.dynClient = Mock()

        result = self.app.collectOCP(outputDir=self.testDir, noDetail=False)

        # Should still return True (partial success)
        assert result is True
        mockCluster.assert_called_once()
        mockNodes.assert_called_once()
