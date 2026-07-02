# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for Certificate Manager discovery functions."""

from unittest.mock import Mock
from mas.cli.must_gather.dependencies.cert_manager import (
    _discoverCertManagerNamespaces,
)


def test_discoverCertManagerNamespaces_returns_both_namespaces_when_exist():
    """Test that discoverCertManagerNamespaces returns both namespaces when they exist.

    GIVEN a cluster with both cert-manager-operator and cert-manager namespaces
    WHEN discoverCertManagerNamespaces is called
    THEN both namespace names are returned in a set.
    """
    dynClient = Mock()
    namespaceApi = Mock()

    def mockGet(name):
        # Simulate both namespaces exist
        return Mock()

    namespaceApi.get.side_effect = mockGet
    dynClient.resources.get.return_value = namespaceApi

    result = _discoverCertManagerNamespaces(dynClient)

    assert result == {
        "cert-manager-operator",
        "cert-manager",
    }, f"Certificate Manager discovery should find both cert-manager-operator and cert-manager namespaces when they exist, but got: {result}"


def test_discoverCertManagerNamespaces_returns_only_operator_namespace():
    """Test that discoverCertManagerNamespaces returns only operator namespace when it exists.

    GIVEN a cluster with only cert-manager-operator namespace
    WHEN discoverCertManagerNamespaces is called
    THEN only cert-manager-operator is returned.
    """
    dynClient = Mock()
    namespaceApi = Mock()

    def mockGet(name):
        if name == "cert-manager-operator":
            return Mock()
        else:
            from kubernetes.client.exceptions import ApiException

            raise ApiException(status=404)

    namespaceApi.get.side_effect = mockGet
    dynClient.resources.get.return_value = namespaceApi

    result = _discoverCertManagerNamespaces(dynClient)

    assert result == {
        "cert-manager-operator"
    }, f"Certificate Manager discovery should find only cert-manager-operator namespace when cert-manager namespace does not exist, but got: {result}"


def test_discoverCertManagerNamespaces_returns_only_cert_manager_namespace():
    """Test that discoverCertManagerNamespaces returns only cert-manager namespace when it exists.

    GIVEN a cluster with only cert-manager namespace
    WHEN discoverCertManagerNamespaces is called
    THEN only cert-manager is returned.
    """
    dynClient = Mock()
    namespaceApi = Mock()

    def mockGet(name):
        if name == "cert-manager":
            return Mock()
        else:
            from kubernetes.client.exceptions import ApiException

            raise ApiException(status=404)

    namespaceApi.get.side_effect = mockGet
    dynClient.resources.get.return_value = namespaceApi

    result = _discoverCertManagerNamespaces(dynClient)

    assert result == {
        "cert-manager"
    }, f"Certificate Manager discovery should find only cert-manager namespace when cert-manager-operator namespace does not exist, but got: {result}"


def test_discoverCertManagerNamespaces_returns_empty_when_none_exist():
    """Test that discoverCertManagerNamespaces returns empty set when no namespaces exist.

    GIVEN a cluster with no cert-manager namespaces
    WHEN discoverCertManagerNamespaces is called
    THEN an empty set is returned.
    """
    dynClient = Mock()
    namespaceApi = Mock()

    def mockGet(name):
        from kubernetes.client.exceptions import ApiException

        raise ApiException(status=404)

    namespaceApi.get.side_effect = mockGet
    dynClient.resources.get.return_value = namespaceApi

    result = _discoverCertManagerNamespaces(dynClient)

    assert result == set(), f"Certificate Manager discovery should return empty set when no cert-manager namespaces exist, but got: {result}"


def test_discoverCertManagerNamespaces_handles_api_exception():
    """Test that discoverCertManagerNamespaces handles API exceptions gracefully.

    GIVEN a cluster where namespace API calls fail
    WHEN discoverCertManagerNamespaces is called
    THEN an empty set is returned without raising an exception.
    """
    dynClient = Mock()
    dynClient.resources.get.side_effect = Exception("API error")

    result = _discoverCertManagerNamespaces(dynClient)

    assert result == set(), f"Certificate Manager discovery should handle API exceptions gracefully and return empty set, but got: {result}"
