# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Reverse-engineered tests for DependencyDetectionMixin.detectMongoDb.

All tests follow the GIVEN-WHEN-THEN convention.
"""

from unittest.mock import MagicMock

from kubernetes.dynamic.exceptions import NotFoundError, ResourceNotFoundError

from mas.cli.update.dependencies import DependencyDetectionMixin

# ---------------------------------------------------------------------------
# Minimal stub
# ---------------------------------------------------------------------------


def _makeStub(sno=False, mongoNamespacePreset="", catalogMongoVersion="7.0.14"):
    """Return a minimal DependencyDetectionMixin stub for MongoDB tests."""

    class Stub(DependencyDetectionMixin):
        def __init__(self):
            self._params = {}
            self.mongoCurrentVersion = None
            self.mongoTargetVersion = None
            self.noConfirm = False
            self.chosenCatalog = {
                "mongo_extras_version_default": catalogMongoVersion,
                "db2_channel_default": "v12.1.0",
                "cpd_product_version_default": "5.2.0",
            }
            self.args = MagicMock()
            self.args.cpd_product_version = None
            self.dynamicClient = MagicMock()

        def isSNO(self):
            return sno

        def getParam(self, key):
            return self._params.get(key, "")

        def setParam(self, key, value):
            self._params[key] = value

    stub = Stub()
    if mongoNamespacePreset:
        stub.setParam("mongodb_namespace", mongoNamespacePreset)
    return stub


def _mockApi(stub, items):
    """Wire stub.dynamicClient to return *items* for any resources.get call."""
    mockApi = MagicMock()
    stub.dynamicClient.resources.get.return_value = mockApi
    mockApi.get.return_value.to_dict.return_value = {"items": items}
    return mockApi


def _crdNotFound(stub):
    """Wire stub.dynamicClient to raise ResourceNotFoundError on resources.get."""
    stub.dynamicClient.resources.get.side_effect = ResourceNotFoundError(MagicMock())


def _mongoItem(namespace, version):
    """Build a minimal MongoDBCommunity item dict."""
    return {"metadata": {"namespace": namespace}, "status": {"version": version}}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_detectMongoDb_crd_not_installed_returns_not_installed():
    """Test detectMongoDb when the MongoDBCommunity CRD is not installed.

    GIVEN the MongoDBCommunity CRD does not exist (ResourceNotFoundError)
    WHEN detectMongoDb is called
    THEN ok=True and message contains "not installed".
    """
    stub = _makeStub()
    _crdNotFound(stub)

    result = stub.detectMongoDb()

    assert result.ok is True
    assert "not installed" in result.message


def test_detectMongoDb_zero_instances_returns_not_installed():
    """Test detectMongoDb when the CRD exists but no instances are found.

    GIVEN the MongoDBCommunity CRD is installed but the items list is empty
    WHEN detectMongoDb is called
    THEN ok=True and message contains "not installed".
    """
    stub = _makeStub()
    _mockApi(stub, [])

    result = stub.detectMongoDb()

    assert result.ok is True
    assert "not installed" in result.message


def test_detectMongoDb_major_version_bump_returns_ok_and_sets_action():
    """Test detectMongoDb when a major version upgrade is required (e.g. v6→v7).

    GIVEN one MongoDBCommunity instance at v6.0.5 and catalog target v7.0.14
    WHEN detectMongoDb is called
    THEN ok=True, message mentions "will be updated", mongodb_action="install",
         mongoCurrentVersion and mongoTargetVersion are set.
    """
    stub = _makeStub(catalogMongoVersion="7.0.14")
    _mockApi(stub, [_mongoItem("mongo-ns", "6.0.5")])

    result = stub.detectMongoDb()

    assert result.ok is True
    assert "will be updated" in result.message
    assert stub.getParam("mongodb_action") == "install"
    assert stub.mongoCurrentVersion == "6.0.5"
    assert stub.mongoTargetVersion == "7.0.14"
    assert stub.getParam("mongodb_namespace") == "mongo-ns"
    assert stub.getParam("mongodb_version") == "7.0.14"


def test_detectMongoDb_minor_upgrade_same_major_returns_already_at_target():
    """Test detectMongoDb when current is lexicographically lower than the target (same major).

    The version comparison used is plain string comparison, so the "already at target"
    branch is reached when the target string is >= the current string.
    e.g. current="7.0.1", target="7.0.8": "7.0.8" >= "7.0.1" → else branch.

    GIVEN one instance at v7.0.1 and catalog target v7.0.8 (same major, target > current lexicographically)
    WHEN detectMongoDb is called
    THEN ok=True and message contains "already at the target version".
    """
    stub = _makeStub(catalogMongoVersion="7.0.8")
    _mockApi(stub, [_mongoItem("mongo-ns", "7.0.1")])

    result = stub.detectMongoDb()

    assert result.ok is True
    assert "already at the target version" in result.message


def test_detectMongoDb_already_at_exact_version_returns_already_at_target():
    """Test detectMongoDb when current version equals the catalog target.

    GIVEN one instance at v7.0.14 and catalog target v7.0.14 (no change)
    WHEN detectMongoDb is called
    THEN ok=True and message contains "already at the target version".
    """
    stub = _makeStub(catalogMongoVersion="7.0.14")
    _mockApi(stub, [_mongoItem("mongo-ns", "7.0.14")])

    result = stub.detectMongoDb()

    assert result.ok is True
    assert "already at the target version" in result.message


def test_detectMongoDb_downgrade_returns_ok_false():
    """Test detectMongoDb when the catalog target is lower than installed version.

    GIVEN one instance at v7.0.14 and catalog target v6.0.5 (downgrade)
    WHEN detectMongoDb is called
    THEN ok=False and message contains "cannot be downgraded".
    """
    stub = _makeStub(catalogMongoVersion="6.0.5")
    _mockApi(stub, [_mongoItem("mongo-ns", "7.0.14")])

    result = stub.detectMongoDb()

    assert result.ok is False
    assert "cannot be downgraded" in result.message


def test_detectMongoDb_preset_namespace_is_used_for_scoped_lookup():
    """Test detectMongoDb uses the pre-set mongodb_namespace param for scoped lookup.

    GIVEN mongodb_namespace is already set to "custom-mongo-ns"
    WHEN detectMongoDb is called
    THEN the API get() is called with namespace="custom-mongo-ns".
    """
    stub = _makeStub(mongoNamespacePreset="custom-mongo-ns", catalogMongoVersion="7.0.14")
    mockApi = MagicMock()
    stub.dynamicClient.resources.get.return_value = mockApi
    mockApi.get.return_value.to_dict.return_value = {"items": [_mongoItem("custom-mongo-ns", "7.0.14")]}

    stub.detectMongoDb()

    mockApi.get.assert_called_once_with(namespace="custom-mongo-ns")


def test_detectMongoDb_sets_replicas_3_for_multi_node():
    """Test detectMongoDb sets mongodb_replicas=3 when not SNO.

    GIVEN isSNO() returns False
    WHEN detectMongoDb is called
    THEN mongodb_replicas param is set to "3".
    """
    stub = _makeStub(sno=False)
    _crdNotFound(stub)

    stub.detectMongoDb()

    assert stub.getParam("mongodb_replicas") == "3"


def test_detectMongoDb_sets_replicas_1_for_sno():
    """Test detectMongoDb sets mongodb_replicas=1 when running on SNO.

    GIVEN isSNO() returns True
    WHEN detectMongoDb is called
    THEN mongodb_replicas param is set to "1".
    """
    stub = _makeStub(sno=True)
    _crdNotFound(stub)

    stub.detectMongoDb()

    assert stub.getParam("mongodb_replicas") == "1"


def test_detectMongoDb_not_found_error_returns_not_installed():
    """Test detectMongoDb treats NotFoundError identically to ResourceNotFoundError.

    GIVEN resources.get raises NotFoundError (namespace not found)
    WHEN detectMongoDb is called
    THEN ok=True and message contains "not installed".
    """
    stub = _makeStub()
    stub.dynamicClient.resources.get.side_effect = NotFoundError(MagicMock())

    result = stub.detectMongoDb()

    assert result.ok is True
    assert "not installed" in result.message
