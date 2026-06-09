# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for MongoDB discovery functions."""

from unittest.mock import Mock
from mas.cli.must_gather.dependencies.mongodb import discoverMongoDBNamespaces


def test_discoverMongoDBNamespaces_returns_empty_set_when_no_mongodb_found():
    """Test that discoverMongoDBNamespaces returns empty set when no MongoDB CRs exist.

    GIVEN a cluster with no MongoDBCommunity custom resources
    WHEN discoverMongoDBNamespaces is called
    THEN an empty set is returned.
    """
    # Create mock client that returns no MongoDB resources
    dynClient = Mock()
    mongoApi = Mock()
    mongoApi.get.return_value = Mock(items=[])
    dynClient.resources.get.return_value = mongoApi

    result = discoverMongoDBNamespaces(dynClient)

    assert result == set(), f"MongoDB discovery should return empty set when no MongoDBCommunity CRs exist, but got: {result}"
    dynClient.resources.get.assert_called_once_with(kind="MongoDBCommunity")


def test_discoverMongoDBNamespaces_returns_namespaces_from_mongodb_crs():
    """Test that discoverMongoDBNamespaces returns namespaces where MongoDB CRs exist.

    GIVEN a cluster with MongoDBCommunity CRs in multiple namespaces
    WHEN discoverMongoDBNamespaces is called
    THEN a set of those namespace names is returned.
    """
    # Create mock MongoDB resources in different namespaces
    mongo1 = Mock()
    mongo1.metadata.namespace = "mongoce"

    mongo2 = Mock()
    mongo2.metadata.namespace = "mongodb-prod"

    mongo3 = Mock()
    mongo3.metadata.namespace = "mongoce"  # Duplicate namespace

    dynClient = Mock()
    mongoApi = Mock()
    mongoApi.get.return_value = Mock(items=[mongo1, mongo2, mongo3])
    dynClient.resources.get.return_value = mongoApi

    result = discoverMongoDBNamespaces(dynClient)

    assert result == {"mongoce", "mongodb-prod"}, f"MongoDB discovery should return namespaces where MongoDBCommunity CRs exist, but got: {result}"
    dynClient.resources.get.assert_called_once_with(kind="MongoDBCommunity")


def test_discoverMongoDBNamespaces_handles_api_exception():
    """Test that discoverMongoDBNamespaces handles API exceptions gracefully.

    GIVEN a cluster where the MongoDB API call fails
    WHEN discoverMongoDBNamespaces is called
    THEN an empty set is returned without raising an exception.
    """
    dynClient = Mock()
    dynClient.resources.get.side_effect = Exception("API error")

    result = discoverMongoDBNamespaces(dynClient)

    assert result == set(), f"MongoDB discovery should handle API exceptions gracefully and return empty set, but got: {result}"


def test_discoverMongoDBNamespaces_ignores_cluster_scoped_resources():
    """Test that discoverMongoDBNamespaces ignores cluster-scoped MongoDB resources.

    GIVEN a cluster with both namespaced and cluster-scoped MongoDB resources
    WHEN discoverMongoDBNamespaces is called
    THEN only namespaced resources are included in the result.
    """
    # Create mock MongoDB resources
    mongo_namespaced = Mock()
    mongo_namespaced.metadata.namespace = "mongoce"

    mongo_cluster_scoped = Mock()
    mongo_cluster_scoped.metadata.namespace = None

    dynClient = Mock()
    mongoApi = Mock()
    mongoApi.get.return_value = Mock(items=[mongo_namespaced, mongo_cluster_scoped])
    dynClient.resources.get.return_value = mongoApi

    result = discoverMongoDBNamespaces(dynClient)

    assert result == {"mongoce"}, f"MongoDB discovery should ignore cluster-scoped resources and only return namespaced ones, but got: {result}"
