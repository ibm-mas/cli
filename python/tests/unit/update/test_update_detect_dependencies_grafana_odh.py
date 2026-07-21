# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Reverse-engineered tests for DependencyDetectionMixin.detectGrafana4 and detectODH.

All tests follow the GIVEN-WHEN-THEN convention.
"""

from unittest.mock import MagicMock

from kubernetes.dynamic.exceptions import NotFoundError, ResourceNotFoundError

from mas.cli.update.dependencies import DependencyDetectionMixin

# ---------------------------------------------------------------------------
# Minimal stub
# ---------------------------------------------------------------------------


def _makeStub():
    """Return a minimal DependencyDetectionMixin stub for Grafana/ODH tests."""

    class Stub(DependencyDetectionMixin):
        def __init__(self):
            self._params = {}
            self.dynamicClient = MagicMock()

        def isSNO(self):
            return False

        def getParam(self, key):
            return self._params.get(key, "")

        def setParam(self, key, value):
            self._params[key] = value

    return Stub()


def _mockApi(stub, items):
    """Wire stub.dynamicClient to return *items* for any resources.get call."""
    mockApi = MagicMock()
    stub.dynamicClient.resources.get.return_value = mockApi
    mockApi.get.return_value.to_dict.return_value = {"items": items}
    return mockApi


def _crdNotFound(stub):
    """Wire stub to raise ResourceNotFoundError on resources.get."""
    stub.dynamicClient.resources.get.side_effect = ResourceNotFoundError(MagicMock())


# ---------------------------------------------------------------------------
# detectGrafana4
# ---------------------------------------------------------------------------


def test_detectGrafana4_not_installed_returns_ok_true_no_param():
    """Test detectGrafana4 when the Grafana CRD is absent.

    GIVEN resources.get raises ResourceNotFoundError for the Grafana CRD
    WHEN detectGrafana4 is called
    THEN ok=True, message contains "not installed", grafana_v5_upgrade is not set.
    """
    stub = _makeStub()
    _crdNotFound(stub)

    result = stub.detectGrafana4()

    assert result.ok is True
    assert "not installed" in result.message
    assert stub.getParam("grafana_v5_upgrade") == ""


def test_detectGrafana4_zero_instances_returns_ok_true_no_param():
    """Test detectGrafana4 when CRD is installed but no v4 instances exist.

    GIVEN the Grafana CRD exists but items list is empty
    WHEN detectGrafana4 is called
    THEN ok=True, grafana_v5_upgrade is not set.
    """
    stub = _makeStub()
    _mockApi(stub, [])

    result = stub.detectGrafana4()

    assert result.ok is True
    assert stub.getParam("grafana_v5_upgrade") == ""


def test_detectGrafana4_installed_sets_param_and_returns_ok_true():
    """Test detectGrafana4 when a Grafana v4 instance is found.

    GIVEN one Grafana v4 instance in the items list
    WHEN detectGrafana4 is called
    THEN ok=True, message contains "will be migrated to v5",
         grafana_v5_upgrade param is set to "true".
    """
    stub = _makeStub()
    _mockApi(stub, [{"metadata": {"name": "grafana-1"}}])

    result = stub.detectGrafana4()

    assert result.ok is True
    assert "migrated to v5" in result.message
    assert stub.getParam("grafana_v5_upgrade") == "true"


def test_detectGrafana4_not_found_error_returns_ok_true():
    """Test detectGrafana4 treats NotFoundError the same as ResourceNotFoundError.

    GIVEN resources.get raises NotFoundError
    WHEN detectGrafana4 is called
    THEN ok=True and grafana_v5_upgrade is not set.
    """
    stub = _makeStub()
    stub.dynamicClient.resources.get.side_effect = NotFoundError(MagicMock())

    result = stub.detectGrafana4()

    assert result.ok is True
    assert stub.getParam("grafana_v5_upgrade") == ""


# ---------------------------------------------------------------------------
# detectODH
# ---------------------------------------------------------------------------


def test_detectODH_crd_not_installed_returns_ok_true_no_param():
    """Test detectODH when the Subscription CRD is absent.

    GIVEN resources.get raises ResourceNotFoundError for the Subscription CRD
    WHEN detectODH is called
    THEN ok=True, message contains "not installed", odh_to_rhoai_migration is not set.
    """
    stub = _makeStub()
    _crdNotFound(stub)

    result = stub.detectODH()

    assert result.ok is True
    assert "not installed" in result.message
    assert stub.getParam("odh_to_rhoai_migration") == ""


def test_detectODH_no_opendatahub_subscription_returns_not_installed():
    """Test detectODH when no opendatahub-operator subscription is found.

    GIVEN subscriptions list contains no opendatahub-operator entry
    WHEN detectODH is called
    THEN ok=True, odh_to_rhoai_migration is not set.
    """
    stub = _makeStub()
    _mockApi(stub, [{"spec": {"name": "some-other-operator"}}])

    result = stub.detectODH()

    assert result.ok is True
    assert stub.getParam("odh_to_rhoai_migration") == ""


def test_detectODH_opendatahub_subscription_sets_param():
    """Test detectODH when the opendatahub-operator subscription is found.

    GIVEN one Subscription with spec.name="opendatahub-operator"
    WHEN detectODH is called
    THEN ok=True, message contains "will be migrated to RHOAI",
         odh_to_rhoai_migration param is set to "true".
    """
    stub = _makeStub()
    _mockApi(stub, [{"spec": {"name": "opendatahub-operator"}}])

    result = stub.detectODH()

    assert result.ok is True
    assert "RHOAI" in result.message
    assert stub.getParam("odh_to_rhoai_migration") == "true"


def test_detectODH_not_found_error_returns_ok_true():
    """Test detectODH treats NotFoundError the same as ResourceNotFoundError.

    GIVEN resources.get raises NotFoundError
    WHEN detectODH is called
    THEN ok=True and odh_to_rhoai_migration is not set.
    """
    stub = _makeStub()
    stub.dynamicClient.resources.get.side_effect = NotFoundError(MagicMock())

    result = stub.detectODH()

    assert result.ok is True
    assert stub.getParam("odh_to_rhoai_migration") == ""
