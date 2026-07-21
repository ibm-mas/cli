# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Reverse-engineered tests for DependencyDetectionMixin.detectKafka.

All tests follow the GIVEN-WHEN-THEN convention.
"""

from unittest.mock import MagicMock

from kubernetes.dynamic.exceptions import NotFoundError, ResourceNotFoundError

from mas.cli.update.dependencies import DependencyDetectionMixin

# ---------------------------------------------------------------------------
# Minimal stub
# ---------------------------------------------------------------------------


def _makeStub(kafkaProviderPreset="", kafkaNamespacePreset=""):
    """Return a minimal DependencyDetectionMixin stub for Kafka tests."""

    class Stub(DependencyDetectionMixin):
        def __init__(self):
            self._params = {}
            self.noConfirm = False
            self.chosenCatalog = {
                "mongo_extras_version_default": "7.0.14",
                "db2_channel_default": "v12.1.0",
                "cpd_product_version_default": "5.2.0",
            }
            self.args = MagicMock()
            self.dynamicClient = MagicMock()

        def isSNO(self):
            return False

        def getParam(self, key):
            return self._params.get(key, "")

        def setParam(self, key, value):
            self._params[key] = value

    stub = Stub()
    if kafkaProviderPreset:
        stub.setParam("kafka_provider", kafkaProviderPreset)
    if kafkaNamespacePreset:
        stub.setParam("kafka_namespace", kafkaNamespacePreset)
    return stub


def _kafkaItem(namespace):
    """Build a minimal Kafka item dict."""
    return {"metadata": {"namespace": namespace}}


def _subItem(name):
    """Build a minimal Subscription item dict with the given spec.name."""
    return {"spec": {"name": name}}


def _mockKafkaAndSub(stub, kafkaItems, subItems):
    """Wire two sequential resources.get calls: Kafka API then Subscription API."""
    mockKafkaApi = MagicMock()
    mockSubApi = MagicMock()
    mockKafkaApi.get.return_value.to_dict.return_value = {"items": kafkaItems}
    mockSubApi.get.return_value.to_dict.return_value = {"items": subItems}
    stub.dynamicClient.resources.get.side_effect = [mockKafkaApi, mockSubApi]


def _crdNotFound(stub):
    """Wire stub to raise ResourceNotFoundError on the first resources.get call."""
    stub.dynamicClient.resources.get.side_effect = ResourceNotFoundError(MagicMock())


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_detectKafka_crd_not_installed_returns_not_installed():
    """Test detectKafka when the Kafka CRD is absent.

    GIVEN resources.get raises ResourceNotFoundError for the Kafka CRD
    WHEN detectKafka is called
    THEN ok=True and message contains "not installed".
    """
    stub = _makeStub()
    _crdNotFound(stub)

    result = stub.detectKafka()

    assert result.ok is True
    assert "not installed" in result.message


def test_detectKafka_zero_instances_returns_none_found():
    """Test detectKafka when the Kafka CRD exists but has no instances.

    GIVEN the Kafka items list is empty and no kafka_namespace is preset
    WHEN detectKafka is called
    THEN ok=True and message contains "No Apache Kafka instances found".
    """
    stub = _makeStub()
    mockKafkaApi = MagicMock()
    mockKafkaApi.get.return_value.to_dict.return_value = {"items": []}
    stub.dynamicClient.resources.get.return_value = mockKafkaApi

    result = stub.detectKafka()

    assert result.ok is True
    assert "No Apache Kafka instances found" in result.message


def test_detectKafka_amq_subscription_sets_redhat_provider():
    """Test detectKafka sets kafka_provider="redhat" for AMQ Streams subscription.

    GIVEN one Kafka instance and an AMQ Streams Subscription (spec.name="amq-streams")
    WHEN detectKafka is called
    THEN ok=True, kafka_provider="redhat", kafka_namespace set to the instance namespace.
    """
    stub = _makeStub()
    _mockKafkaAndSub(stub, [_kafkaItem("kafka-ns")], [_subItem("amq-streams")])

    result = stub.detectKafka()

    assert result.ok is True
    assert stub.getParam("kafka_provider") == "redhat"
    assert stub.getParam("kafka_namespace") == "kafka-ns"


def test_detectKafka_strimzi_subscription_sets_strimzi_provider():
    """Test detectKafka sets kafka_provider="strimzi" for Strimzi subscription.

    GIVEN one Kafka instance and a Strimzi Subscription (spec.name="strimzi-kafka-operator")
    WHEN detectKafka is called
    THEN ok=True, kafka_provider="strimzi".
    """
    stub = _makeStub()
    _mockKafkaAndSub(stub, [_kafkaItem("kafka-ns")], [_subItem("strimzi-kafka-operator")])

    result = stub.detectKafka()

    assert result.ok is True
    assert stub.getParam("kafka_provider") == "strimzi"


def test_detectKafka_no_subscription_match_returns_ok_false():
    """Test detectKafka returns ok=False when no known Subscription is found.

    GIVEN one Kafka instance but no amq-streams or strimzi subscription
    WHEN detectKafka is called
    THEN ok=False and message contains "Unable to determine".
    """
    stub = _makeStub()
    _mockKafkaAndSub(stub, [_kafkaItem("kafka-ns")], [_subItem("some-other-operator")])

    result = stub.detectKafka()

    assert result.ok is False
    assert "Unable to determine" in result.message


def test_detectKafka_multiple_namespaces_picks_first_sorted():
    """Test detectKafka with instances in multiple namespaces picks first sorted.

    GIVEN instances in namespaces "z-kafka" and "a-kafka"
    WHEN detectKafka is called
    THEN kafka_namespace is set to "a-kafka" (first alphabetically).
    """
    stub = _makeStub()
    _mockKafkaAndSub(
        stub,
        [_kafkaItem("z-kafka"), _kafkaItem("a-kafka")],
        [_subItem("amq-streams")],
    )

    stub.detectKafka()

    assert stub.getParam("kafka_namespace") == "a-kafka"


def test_detectKafka_preset_provider_skips_subscription_lookup():
    """Test detectKafka skips the Subscription API call when kafka_provider is preset.

    GIVEN kafka_provider is already set to "strimzi" and kafka_namespace is preset
    WHEN detectKafka is called
    THEN only one resources.get call is made (Kafka CRD), not a second for Subscriptions,
         and ok=True.
    """
    stub = _makeStub(kafkaProviderPreset="strimzi", kafkaNamespacePreset="kafka-ns")
    mockKafkaApi = MagicMock()
    mockKafkaApi.get.return_value.to_dict.return_value = {"items": [_kafkaItem("kafka-ns")]}
    stub.dynamicClient.resources.get.return_value = mockKafkaApi

    result = stub.detectKafka()

    assert result.ok is True
    # Only the Kafka CRD lookup should have been called once; no Subscription lookup
    assert stub.dynamicClient.resources.get.call_count == 1


def test_detectKafka_not_found_error_returns_not_installed():
    """Test detectKafka treats NotFoundError the same as ResourceNotFoundError.

    GIVEN resources.get raises NotFoundError for the Kafka CRD
    WHEN detectKafka is called
    THEN ok=True and message contains "not installed".
    """
    stub = _makeStub()
    stub.dynamicClient.resources.get.side_effect = NotFoundError(MagicMock())

    result = stub.detectKafka()

    assert result.ok is True
    assert "not installed" in result.message
