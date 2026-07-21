# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Reverse-engineered tests for DependencyDetectionMixin fatal pre-condition checks.

Covers:
- isWatsonDiscoveryInstalled
- isWatsonOpenscaleInstalled
- isIBMCertManagerInstalled

All tests follow the GIVEN-WHEN-THEN convention.
"""

from unittest.mock import MagicMock

from kubernetes.dynamic.exceptions import NotFoundError, ResourceNotFoundError

from mas.cli.update.dependencies import DependencyDetectionMixin

# ---------------------------------------------------------------------------
# Minimal stub
# ---------------------------------------------------------------------------


def _makeStub():
    """Return a minimal DependencyDetectionMixin stub for fatal-check tests."""

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
# isWatsonDiscoveryInstalled
# ---------------------------------------------------------------------------


def test_isWatsonDiscovery_crd_not_installed_returns_ok_true():
    """Test isWatsonDiscoveryInstalled when the WatsonDiscovery CRD is absent.

    GIVEN resources.get raises ResourceNotFoundError for WatsonDiscovery
    WHEN isWatsonDiscoveryInstalled is called
    THEN ok=True and message contains "not installed".
    """
    stub = _makeStub()
    _crdNotFound(stub)

    result = stub.isWatsonDiscoveryInstalled()

    assert result.ok is True
    assert "not installed" in result.message


def test_isWatsonDiscovery_installed_returns_ok_false():
    """Test isWatsonDiscoveryInstalled when a WatsonDiscovery instance is found.

    GIVEN the WatsonDiscovery CRD is installed and one instance exists
    WHEN isWatsonDiscoveryInstalled is called
    THEN ok=False and message contains "update cannot proceed".
    """
    stub = _makeStub()
    _mockApi(stub, [{"metadata": {"name": "wd-1"}}])

    result = stub.isWatsonDiscoveryInstalled()

    assert result.ok is False
    assert "update cannot proceed" in result.message


def test_isWatsonDiscovery_zero_instances_returns_ok_true():
    """Test isWatsonDiscoveryInstalled when CRD exists but no instances are found.

    GIVEN WatsonDiscovery CRD is present but the items list is empty
    WHEN isWatsonDiscoveryInstalled is called
    THEN ok=True.
    """
    stub = _makeStub()
    _mockApi(stub, [])

    result = stub.isWatsonDiscoveryInstalled()

    assert result.ok is True


# ---------------------------------------------------------------------------
# isWatsonOpenscaleInstalled
# ---------------------------------------------------------------------------


def test_isWatsonOpenscale_crd_not_installed_returns_ok_true():
    """Test isWatsonOpenscaleInstalled when the WOService CRD is absent.

    GIVEN resources.get raises ResourceNotFoundError for WOService
    WHEN isWatsonOpenscaleInstalled is called
    THEN ok=True and message contains "not installed".
    """
    stub = _makeStub()
    _crdNotFound(stub)

    result = stub.isWatsonOpenscaleInstalled()

    assert result.ok is True
    assert "not installed" in result.message


def test_isWatsonOpenscale_installed_returns_ok_false():
    """Test isWatsonOpenscaleInstalled when a WOService instance is found.

    GIVEN the WOService CRD is installed and one instance exists
    WHEN isWatsonOpenscaleInstalled is called
    THEN ok=False and message contains "update cannot proceed".
    """
    stub = _makeStub()
    _mockApi(stub, [{"metadata": {"name": "wos-1"}}])

    result = stub.isWatsonOpenscaleInstalled()

    assert result.ok is False
    assert "update cannot proceed" in result.message


def test_isWatsonOpenscale_zero_instances_returns_ok_true():
    """Test isWatsonOpenscaleInstalled when CRD exists but no instances are found.

    GIVEN WOService CRD is present but the items list is empty
    WHEN isWatsonOpenscaleInstalled is called
    THEN ok=True.
    """
    stub = _makeStub()
    _mockApi(stub, [])

    result = stub.isWatsonOpenscaleInstalled()

    assert result.ok is True


# ---------------------------------------------------------------------------
# isIBMCertManagerInstalled
# ---------------------------------------------------------------------------


def _mockCertManager(stub, namespaceFound=True, podNames=None):
    """Wire the two-step namespace+pods lookup for isIBMCertManagerInstalled.

    Args:
        stub: The mixin stub instance.
        namespaceFound (bool): If False, raise NotFoundError on namespace lookup.
        podNames (list): Pod metadata.name values to return when namespace found.
    """
    if not namespaceFound:
        stub.dynamicClient.resources.get.side_effect = NotFoundError(MagicMock())
        return

    podNames = podNames or []
    pods = []
    for n in podNames:
        pod = MagicMock()
        pod.metadata.name = n
        pods.append(pod)

    mockNsApi = MagicMock()
    mockPodsApi = MagicMock()

    # First call: Namespace API
    mockNsApi.get.return_value = MagicMock()  # namespace exists — no exception
    # Second call: Pod API
    mockPodsApi.get.return_value.items = pods

    stub.dynamicClient.resources.get.side_effect = [mockNsApi, mockPodsApi]


def test_isIBMCertManager_namespace_not_found_returns_ok_true():
    """Test isIBMCertManagerInstalled when ibm-common-services namespace doesn't exist.

    GIVEN resources.get raises NotFoundError for the Namespace lookup
    WHEN isIBMCertManagerInstalled is called
    THEN ok=True and message contains "not installed".
    """
    stub = _makeStub()
    _mockCertManager(stub, namespaceFound=False)

    result = stub.isIBMCertManagerInstalled()

    assert result.ok is True
    assert "not installed" in result.message


def test_isIBMCertManager_namespace_exists_no_cainjector_returns_ok_true():
    """Test isIBMCertManagerInstalled when namespace exists but no cainjector pod.

    GIVEN ibm-common-services namespace exists, pods list has no cert-manager-cainjector pod
    WHEN isIBMCertManagerInstalled is called
    THEN ok=True and message contains "not installed".
    """
    stub = _makeStub()
    _mockCertManager(stub, namespaceFound=True, podNames=["some-other-pod-abc"])

    result = stub.isIBMCertManagerInstalled()

    assert result.ok is True
    assert "not installed" in result.message


def test_isIBMCertManager_cainjector_pod_present_returns_ok_false():
    """Test isIBMCertManagerInstalled when a cert-manager-cainjector pod is found.

    GIVEN ibm-common-services namespace exists and a pod named
         "cert-manager-cainjector-xyz" is present
    WHEN isIBMCertManagerInstalled is called
    THEN ok=False and message contains "update cannot proceed".
    """
    stub = _makeStub()
    _mockCertManager(stub, namespaceFound=True, podNames=["cert-manager-cainjector-xyz"])

    result = stub.isIBMCertManagerInstalled()

    assert result.ok is False
    assert "update cannot proceed" in result.message
