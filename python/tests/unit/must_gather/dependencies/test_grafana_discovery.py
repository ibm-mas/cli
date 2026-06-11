# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for Grafana discovery functions."""

from unittest.mock import Mock
from mas.cli.must_gather.dependencies.grafana import discoverGrafanaNamespaces


def test_discoverGrafanaNamespaces_returns_empty_set_when_no_grafana_found():
    """Test that discoverGrafanaNamespaces returns empty set when no Grafana CRs exist.

    GIVEN a cluster with no Grafana custom resources
    WHEN discoverGrafanaNamespaces is called
    THEN an empty set is returned.
    """
    dynClient = Mock()
    grafanaApi = Mock()
    grafanaApi.get.return_value = Mock(items=[])
    dynClient.resources.get.return_value = grafanaApi

    result = discoverGrafanaNamespaces(dynClient)

    assert result == set(), f"Grafana discovery should return empty set when no Grafana CRs exist, but got: {result}"
    dynClient.resources.get.assert_called_once_with(kind="Grafana")


def test_discoverGrafanaNamespaces_returns_namespaces_from_grafana_crs():
    """Test that discoverGrafanaNamespaces returns namespaces where Grafana CRs exist.

    GIVEN a cluster with Grafana CRs in multiple namespaces
    WHEN discoverGrafanaNamespaces is called
    THEN a set of those namespace names is returned.
    """
    grafana1 = Mock()
    grafana1.metadata.namespace = "grafana"

    grafana2 = Mock()
    grafana2.metadata.namespace = "monitoring"

    grafana3 = Mock()
    grafana3.metadata.namespace = "grafana"

    dynClient = Mock()
    grafanaApi = Mock()
    grafanaApi.get.return_value = Mock(items=[grafana1, grafana2, grafana3])
    dynClient.resources.get.return_value = grafanaApi

    result = discoverGrafanaNamespaces(dynClient)

    assert result == {"grafana", "monitoring"}, f"Grafana discovery should return namespaces where Grafana CRs exist, but got: {result}"
    dynClient.resources.get.assert_called_once_with(kind="Grafana")


def test_discoverGrafanaNamespaces_handles_api_exception():
    """Test that discoverGrafanaNamespaces handles API exceptions gracefully.

    GIVEN a cluster where the Grafana API call fails
    WHEN discoverGrafanaNamespaces is called
    THEN an empty set is returned without raising an exception.
    """
    dynClient = Mock()
    dynClient.resources.get.side_effect = Exception("API error")

    result = discoverGrafanaNamespaces(dynClient)

    assert result == set(), f"Grafana discovery should handle API exceptions gracefully and return empty set, but got: {result}"


def test_discoverGrafanaNamespaces_ignores_cluster_scoped_resources():
    """Test that discoverGrafanaNamespaces ignores cluster-scoped Grafana resources.

    GIVEN a cluster with both namespaced and cluster-scoped Grafana resources
    WHEN discoverGrafanaNamespaces is called
    THEN only namespaced resources are included in the result.
    """
    grafana_namespaced = Mock()
    grafana_namespaced.metadata.namespace = "grafana"

    grafana_cluster_scoped = Mock()
    grafana_cluster_scoped.metadata.namespace = None

    dynClient = Mock()
    grafanaApi = Mock()
    grafanaApi.get.return_value = Mock(items=[grafana_namespaced, grafana_cluster_scoped])
    dynClient.resources.get.return_value = grafanaApi

    result = discoverGrafanaNamespaces(dynClient)

    assert result == {"grafana"}, f"Grafana discovery should ignore cluster-scoped resources and only return namespaced ones, but got: {result}"
