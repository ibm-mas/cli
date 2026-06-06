# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for IBM CRD caching functionality.

GIVEN IBM CRDs need to be discovered
WHEN getIBMCRDs is called multiple times
THEN CRDs are only fetched once and cached for subsequent calls.
"""

from unittest.mock import Mock
from mas.cli.must_gather.common.ibm_resources import getIBMCRDs, _clearIBMCRDCache


class TestIBMCRDCaching:
    """Test IBM CRD caching functionality."""

    def setup_method(self):
        """Clear cache before each test."""
        _clearIBMCRDCache()

    def test_getIBMCRDs_caches_results(self):
        """Test that IBM CRDs are cached after first call.

        GIVEN a DynamicClient
        WHEN getIBMCRDs is called multiple times
        THEN CRDs are only fetched from API once.
        """
        # Setup
        mockDynClient = Mock()
        mockCrdApi = Mock()
        mockDynClient.resources.get.return_value = mockCrdApi

        # Create mock CRD items
        mockCrd1 = Mock()
        mockCrd1.metadata.name = "suites.core.mas.ibm.com"
        mockCrd1.to_dict.return_value = {
            "metadata": {"name": "suites.core.mas.ibm.com"},
            "spec": {
                "group": "core.mas.ibm.com",
                "names": {"kind": "Suite"},
                "versions": [{"name": "v1", "served": True}],
            },
        }

        mockCrd2 = Mock()
        mockCrd2.metadata.name = "workspaceconfigs.apps.mas.ibm.com"
        mockCrd2.to_dict.return_value = {
            "metadata": {"name": "workspaceconfigs.apps.mas.ibm.com"},
            "spec": {
                "group": "apps.mas.ibm.com",
                "names": {"kind": "WorkspaceConfig"},
                "versions": [{"name": "v1", "served": True}],
            },
        }

        mockCrds = Mock()
        mockCrds.items = [mockCrd1, mockCrd2]
        mockCrdApi.get.return_value = mockCrds

        # Execute - first call
        result1 = getIBMCRDs(mockDynClient)

        # Verify first call fetched from API
        assert len(result1) == 2
        assert ("Suite", "core.mas.ibm.com/v1") in result1
        assert ("WorkspaceConfig", "apps.mas.ibm.com/v1") in result1
        mockCrdApi.get.assert_called_once()

        # Execute - second call
        result2 = getIBMCRDs(mockDynClient)

        # Verify second call used cache (API not called again)
        assert result2 == result1
        mockCrdApi.get.assert_called_once()  # Still only called once

    def test_getIBMCRDs_filters_non_ibm_crds(self):
        """Test that only IBM CRDs are returned.

        GIVEN CRDs with both IBM and non-IBM names
        WHEN getIBMCRDs is called
        THEN only IBM CRDs are included in results.
        """
        # Setup
        mockDynClient = Mock()
        mockCrdApi = Mock()
        mockDynClient.resources.get.return_value = mockCrdApi

        # Create mock CRD items - one IBM, one non-IBM
        mockIbmCrd = Mock()
        mockIbmCrd.metadata.name = "suites.core.mas.ibm.com"
        mockIbmCrd.to_dict.return_value = {
            "metadata": {"name": "suites.core.mas.ibm.com"},
            "spec": {
                "group": "core.mas.ibm.com",
                "names": {"kind": "Suite"},
                "versions": [{"name": "v1", "served": True}],
            },
        }

        mockNonIbmCrd = Mock()
        mockNonIbmCrd.metadata.name = "deployments.apps"
        mockNonIbmCrd.to_dict.return_value = {
            "metadata": {"name": "deployments.apps"},
            "spec": {
                "group": "apps",
                "names": {"kind": "Deployment"},
                "versions": [{"name": "v1", "served": True}],
            },
        }

        mockCrds = Mock()
        mockCrds.items = [mockIbmCrd, mockNonIbmCrd]
        mockCrdApi.get.return_value = mockCrds

        # Execute
        result = getIBMCRDs(mockDynClient)

        # Verify only IBM CRD is returned
        assert len(result) == 1
        assert ("Suite", "core.mas.ibm.com/v1") in result
        assert ("Deployment", "apps/v1") not in result

    def test_clearIBMCRDCache_clears_cache(self):
        """Test that cache can be cleared.

        GIVEN cached IBM CRDs
        WHEN _clearIBMCRDCache is called
        THEN subsequent getIBMCRDs call fetches from API again.
        """
        # Setup
        mockDynClient = Mock()
        mockCrdApi = Mock()
        mockDynClient.resources.get.return_value = mockCrdApi

        mockCrd = Mock()
        mockCrd.metadata.name = "suites.core.mas.ibm.com"
        mockCrd.to_dict.return_value = {
            "metadata": {"name": "suites.core.mas.ibm.com"},
            "spec": {
                "group": "core.mas.ibm.com",
                "names": {"kind": "Suite"},
                "versions": [{"name": "v1", "served": True}],
            },
        }

        mockCrds = Mock()
        mockCrds.items = [mockCrd]
        mockCrdApi.get.return_value = mockCrds

        # Execute - first call to populate cache
        getIBMCRDs(mockDynClient)
        assert mockCrdApi.get.call_count == 1

        # Clear cache
        _clearIBMCRDCache()

        # Execute - second call after cache clear
        getIBMCRDs(mockDynClient)

        # Verify API was called again
        assert mockCrdApi.get.call_count == 2
