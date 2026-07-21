# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Reverse-engineered tests for DependencyDetectionMixin.detectDb2u.

All tests follow the GIVEN-WHEN-THEN convention.
"""

from unittest.mock import MagicMock

from kubernetes.dynamic.exceptions import NotFoundError, ResourceNotFoundError

from mas.cli.update.dependencies import DependencyDetectionMixin

# ---------------------------------------------------------------------------
# Minimal stub
# ---------------------------------------------------------------------------


def _makeStub(noConfirm=False, db2NamespacePreset="", db2Channel="v12.1.0"):
    """Return a minimal DependencyDetectionMixin stub for Db2 tests."""

    class Stub(DependencyDetectionMixin):
        def __init__(self):
            self._params = {}
            self.db2CurrentMajorVersion = None
            self.db2TargetMajorVersion = None
            self.noConfirm = noConfirm
            self.chosenCatalog = {
                "mongo_extras_version_default": "7.0.14",
                "db2_channel_default": db2Channel,
                "cpd_product_version_default": "5.2.0",
            }
            self.args = MagicMock()
            self.args.cpd_product_version = None
            self.dynamicClient = MagicMock()

        def isSNO(self):
            return False

        def getParam(self, key):
            return self._params.get(key, "")

        def setParam(self, key, value):
            self._params[key] = value

    stub = Stub()
    if db2NamespacePreset:
        stub.setParam("db2_namespace", db2NamespacePreset)
    return stub


def _db2Item(namespace, name, version=None):
    """Build a minimal Db2uCluster/Db2uInstance item dict."""
    item = {"metadata": {"namespace": namespace, "name": name}, "spec": {}}
    if version is not None:
        item["spec"]["version"] = version
    return item


def _mockTwoKinds(stub, clusterItems, instanceItems):
    """Wire two sequential resources.get calls (Db2uCluster then Db2uInstance)."""
    mockClusterApi = MagicMock()
    mockInstanceApi = MagicMock()
    mockClusterApi.get.return_value.to_dict.return_value = {"items": clusterItems}
    mockInstanceApi.get.return_value.to_dict.return_value = {"items": instanceItems}
    stub.dynamicClient.resources.get.side_effect = [mockClusterApi, mockInstanceApi]


def _crdNotFound(stub):
    """Wire stub to raise ResourceNotFoundError on the first resources.get call."""
    stub.dynamicClient.resources.get.side_effect = ResourceNotFoundError(MagicMock())


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_detectDb2u_crd_not_installed_returns_not_installed():
    """Test detectDb2u when the Db2u CRD is not present on the cluster.

    GIVEN the Db2u CRD does not exist (ResourceNotFoundError)
    WHEN detectDb2u is called
    THEN ok=True and message contains "not installed".
    """
    stub = _makeStub()
    _crdNotFound(stub)

    result = stub.detectDb2u()

    assert result.ok is True
    assert "not installed" in result.message


def test_detectDb2u_zero_instances_returns_none_found():
    """Test detectDb2u when no Db2uCluster or Db2uInstance resources exist.

    GIVEN both Db2uCluster and Db2uInstance item lists are empty
    WHEN detectDb2u is called
    THEN ok=True and message contains "No Db2uCluster or Db2uInstance instances found".
    """
    stub = _makeStub()
    _mockTwoKinds(stub, [], [])

    result = stub.detectDb2u()

    assert result.ok is True
    assert "No Db2uCluster or Db2uInstance instances found" in result.message


def test_detectDb2u_single_namespace_sets_param():
    """Test detectDb2u sets db2_namespace when all instances are in one namespace.

    GIVEN one Db2uCluster instance in namespace "db2u-ns"
    WHEN detectDb2u is called
    THEN db2_namespace param is set to "db2u-ns" and ok=True.
    """
    stub = _makeStub(db2Channel="v12.1.0")
    _mockTwoKinds(stub, [_db2Item("db2u-ns", "db2u-1", "12.1.0.0")], [])

    result = stub.detectDb2u()

    assert result.ok is True
    assert stub.getParam("db2_namespace") == "db2u-ns"


def test_detectDb2u_multiple_namespaces_interactive_picks_first_sorted():
    """Test detectDb2u with instances in multiple namespaces in interactive mode.

    GIVEN instances in namespaces "z-ns" and "a-ns" with noConfirm=False
    WHEN detectDb2u is called
    THEN ok=True and db2_namespace is set to "a-ns" (first sorted).
    """
    stub = _makeStub(noConfirm=False, db2Channel="v12.1.0")
    _mockTwoKinds(
        stub,
        [_db2Item("z-ns", "db2u-1", "12.1.0.0"), _db2Item("a-ns", "db2u-2", "12.1.0.0")],
        [],
    )

    result = stub.detectDb2u()

    assert result.ok is True
    assert stub.getParam("db2_namespace") == "a-ns"


def test_detectDb2u_multiple_namespaces_no_confirm_returns_ok_false():
    """Test detectDb2u returns ok=False with multiple namespaces in --no-confirm mode.

    GIVEN instances in two distinct namespaces with noConfirm=True
         and no db2_namespace preset
    WHEN detectDb2u is called
    THEN ok=False and message mentions "multiple namespaces".
    """
    stub = _makeStub(noConfirm=True, db2Channel="v12.1.0")
    _mockTwoKinds(
        stub,
        [_db2Item("ns-a", "db2u-1", "11.5.0.0"), _db2Item("ns-b", "db2u-2", "11.5.0.0")],
        [],
    )

    result = stub.detectDb2u()

    assert result.ok is False
    assert "multiple namespaces" in result.message


def test_detectDb2u_major_version_upgrade_sets_current_and_target():
    """Test detectDb2u detects a major version upgrade (v11→v12).

    GIVEN one instance at version "11.5.0.0" and db2_channel_default "v12.1.0"
    WHEN detectDb2u is called
    THEN ok=True, message mentions "will be updated",
         db2CurrentMajorVersion=11, db2TargetMajorVersion=12.
    """
    stub = _makeStub(db2Channel="v12.1.0")
    _mockTwoKinds(stub, [_db2Item("db2-ns", "db2u-1", "11.5.0.0")], [])

    result = stub.detectDb2u()

    assert result.ok is True
    assert "will be updated" in result.message
    assert stub.db2CurrentMajorVersion == 11
    assert stub.db2TargetMajorVersion == 12


def test_detectDb2u_already_at_target_major_sets_upgrade_flag_false():
    """Test detectDb2u when all instances are already at the target major version.

    GIVEN one instance at "12.1.0.0" and db2_channel_default "v12.1.0"
    WHEN detectDb2u is called
    THEN ok=True, message mentions "already at the target version",
         db2_v12_upgrade param is set to "false".
    """
    stub = _makeStub(db2Channel="v12.1.0")
    _mockTwoKinds(stub, [_db2Item("db2-ns", "db2u-1", "12.1.0.0")], [])

    result = stub.detectDb2u()

    assert result.ok is True
    assert "already at the target version" in result.message
    assert stub.getParam("db2_v12_upgrade") == "false"


def test_detectDb2u_no_version_in_spec_returns_unavailable():
    """Test detectDb2u when instance spec has no version field.

    GIVEN one instance with no "version" key in spec
    WHEN detectDb2u is called
    THEN ok=True and message contains "version information unavailable".
    """
    stub = _makeStub(db2Channel="v12.1.0")
    _mockTwoKinds(stub, [_db2Item("db2-ns", "db2u-1", version=None)], [])

    result = stub.detectDb2u()

    assert result.ok is True
    assert "version information unavailable" in result.message


def test_detectDb2u_sets_db2_channel_param():
    """Test detectDb2u sets the db2_channel param from the catalog.

    GIVEN db2_channel_default is "v12.1.0" and one instance exists
    WHEN detectDb2u is called
    THEN db2_channel param is set to "v12.1.0".
    """
    stub = _makeStub(db2Channel="v12.1.0")
    _mockTwoKinds(stub, [_db2Item("db2-ns", "db2u-1", "12.1.0.0")], [])

    stub.detectDb2u()

    assert stub.getParam("db2_channel") == "v12.1.0"


def test_detectDb2u_preset_namespace_is_respected():
    """Test detectDb2u skips namespace detection when db2_namespace is already set.

    GIVEN db2_namespace is pre-set to "preset-ns" and instances exist in another ns
    WHEN detectDb2u is called
    THEN db2_namespace remains "preset-ns".
    """
    stub = _makeStub(db2NamespacePreset="preset-ns", db2Channel="v12.1.0")
    _mockTwoKinds(stub, [_db2Item("other-ns", "db2u-1", "12.1.0.0")], [])

    stub.detectDb2u()

    assert stub.getParam("db2_namespace") == "preset-ns"


def test_detectDb2u_not_found_error_returns_not_installed():
    """Test detectDb2u treats NotFoundError the same as ResourceNotFoundError.

    GIVEN resources.get raises NotFoundError
    WHEN detectDb2u is called
    THEN ok=True and message contains "not installed".
    """
    stub = _makeStub()
    stub.dynamicClient.resources.get.side_effect = NotFoundError(MagicMock())

    result = stub.detectDb2u()

    assert result.ok is True
    assert "not installed" in result.message
