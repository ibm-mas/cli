# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for Kafka discovery functions."""

from unittest.mock import Mock
from mas.cli.must_gather.dependencies.kafka import discoverKafkaNamespaces


def test_discoverKafkaNamespaces_returns_empty_set_when_no_kafka_found():
    """Test that discoverKafkaNamespaces returns empty set when no Kafka CRs exist.

    GIVEN a cluster with no Kafka custom resources
    WHEN discoverKafkaNamespaces is called
    THEN an empty set is returned.
    """
    # Create mock client that returns no Kafka resources
    dynClient = Mock()
    kafkaApi = Mock()
    kafkaApi.get.return_value = Mock(items=[])
    dynClient.resources.get.return_value = kafkaApi

    result = discoverKafkaNamespaces(dynClient)

    assert result == set()
    dynClient.resources.get.assert_called_once_with(kind="Kafka")


def test_discoverKafkaNamespaces_returns_namespaces_from_kafka_crs():
    """Test that discoverKafkaNamespaces returns namespaces where Kafka CRs exist.

    GIVEN a cluster with Kafka CRs in multiple namespaces
    WHEN discoverKafkaNamespaces is called
    THEN a set of those namespace names is returned.
    """
    # Create mock Kafka resources in different namespaces
    kafka1 = Mock()
    kafka1.metadata.namespace = "strimzi"

    kafka2 = Mock()
    kafka2.metadata.namespace = "kafka-prod"

    kafka3 = Mock()
    kafka3.metadata.namespace = "strimzi"  # Duplicate namespace

    dynClient = Mock()
    kafkaApi = Mock()
    kafkaApi.get.return_value = Mock(items=[kafka1, kafka2, kafka3])
    dynClient.resources.get.return_value = kafkaApi

    result = discoverKafkaNamespaces(dynClient)

    assert result == {"strimzi", "kafka-prod"}
    dynClient.resources.get.assert_called_once_with(kind="Kafka")


def test_discoverKafkaNamespaces_handles_api_exception():
    """Test that discoverKafkaNamespaces handles API exceptions gracefully.

    GIVEN a cluster where the Kafka API call fails
    WHEN discoverKafkaNamespaces is called
    THEN an empty set is returned without raising an exception.
    """
    dynClient = Mock()
    dynClient.resources.get.side_effect = Exception("API error")

    result = discoverKafkaNamespaces(dynClient)

    assert result == set()


def test_discoverKafkaNamespaces_ignores_cluster_scoped_resources():
    """Test that discoverKafkaNamespaces ignores cluster-scoped Kafka resources.

    GIVEN a cluster with both namespaced and cluster-scoped Kafka resources
    WHEN discoverKafkaNamespaces is called
    THEN only namespaced resources are included in the result.
    """
    # Create mock Kafka resources
    kafka_namespaced = Mock()
    kafka_namespaced.metadata.namespace = "strimzi"

    kafka_cluster_scoped = Mock()
    kafka_cluster_scoped.metadata.namespace = None

    dynClient = Mock()
    kafkaApi = Mock()
    kafkaApi.get.return_value = Mock(items=[kafka_namespaced, kafka_cluster_scoped])
    dynClient.resources.get.return_value = kafkaApi

    result = discoverKafkaNamespaces(dynClient)

    assert result == {"strimzi"}
