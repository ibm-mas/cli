# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Reverse-engineered tests for DependencyDetectionMixin.detectCP4D.

All tests follow the GIVEN-WHEN-THEN convention.
"""

from unittest.mock import MagicMock

from kubernetes.dynamic.exceptions import NotFoundError, ResourceNotFoundError

from mas.cli.update.dependencies import DependencyDetectionMixin

# ---------------------------------------------------------------------------
# Minimal stub
# ---------------------------------------------------------------------------


def _makeStub(catalogCpdVersion="5.2.0", argsCpdVersion=None):
    """Return a minimal DependencyDetectionMixin stub for CP4D tests."""

    class Stub(DependencyDetectionMixin):
        def __init__(self):
            self._params = {}
            self.noConfirm = False
            self.chosenCatalog = {
                "mongo_extras_version_default": "7.0.14",
                "db2_channel_default": "v12.1.0",
                "cpd_product_version_default": catalogCpdVersion,
            }
            self.args = MagicMock()
            self.args.cpd_product_version = argsCpdVersion
            self.dynamicClient = MagicMock()

        def isSNO(self):
            return False

        def getParam(self, key):
            return self._params.get(key, "")

        def setParam(self, key, value):
            self._params[key] = value

    return Stub()


def _cpdItem(namespace, version, fileStorage="ocs-storagecluster-cephfs", blockStorage="ocs-storagecluster-ceph-rbd"):
    """Build a minimal Ibmcpd item dict."""
    return {
        "metadata": {"namespace": namespace},
        "spec": {
            "version": version,
            "storageClass": fileStorage,
            "zenCoreMetadbStorageClass": blockStorage,
        },
    }


def _mockCpdApi(stub, items):
    """Wire stub.dynamicClient to return *items* for any resources.get call."""
    mockApi = MagicMock()
    stub.dynamicClient.resources.get.return_value = mockApi
    mockApi.get.return_value.to_dict.return_value = {"items": items}
    return mockApi


def _crdNotFound(stub):
    """Wire stub to raise ResourceNotFoundError on resources.get."""
    stub.dynamicClient.resources.get.side_effect = ResourceNotFoundError(MagicMock())


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_detectCP4D_crd_not_installed_returns_not_installed():
    """Test detectCP4D when the Ibmcpd CRD is not present.

    GIVEN resources.get raises ResourceNotFoundError for the Ibmcpd CRD
    WHEN detectCP4D is called
    THEN ok=True and message contains "not installed".
    """
    stub = _makeStub()
    _crdNotFound(stub)

    result = stub.detectCP4D()

    assert result.ok is True
    assert "not installed" in result.message


def test_detectCP4D_zero_instances_returns_not_installed():
    """Test detectCP4D when no Ibmcpd instances exist.

    GIVEN items list is empty
    WHEN detectCP4D is called
    THEN ok=True and message contains "not installed".
    """
    stub = _makeStub()
    _mockCpdApi(stub, [])

    result = stub.detectCP4D()

    assert result.ok is True
    assert "not installed" in result.message


def test_detectCP4D_multiple_instances_returns_none_will_be_updated():
    """Test detectCP4D when more than one Ibmcpd instance exists.

    GIVEN two Ibmcpd instances in different namespaces
    WHEN detectCP4D is called
    THEN ok=True and message contains "none will be updated".
    """
    stub = _makeStub()
    _mockCpdApi(
        stub,
        [_cpdItem("ibm-cpd", "5.1.3"), _cpdItem("ibm-cpd-2", "5.0.0")],
    )

    result = stub.detectCP4D()

    assert result.ok is True
    assert "none will be updated" in result.message


def test_detectCP4D_non_ibm_cpd_namespace_is_not_managed():
    """Test detectCP4D when the instance is outside the ibm-cpd namespace.

    GIVEN one instance in namespace "custom-cpd" (not "ibm-cpd")
    WHEN detectCP4D is called
    THEN ok=True and message contains "not managed by MAS".
    """
    stub = _makeStub()
    _mockCpdApi(stub, [_cpdItem("custom-cpd", "5.1.3")])

    result = stub.detectCP4D()

    assert result.ok is True
    assert "not managed by MAS" in result.message


def test_detectCP4D_unsupported_version_returns_ok_false():
    """Test detectCP4D when current version is not in the upgrade path.

    GIVEN one instance at version "4.8.0" (not in cpdUpgradePath)
    WHEN detectCP4D is called
    THEN ok=False and message contains "Skipping intermediate".
    """
    stub = _makeStub(catalogCpdVersion="5.2.0")
    _mockCpdApi(stub, [_cpdItem("ibm-cpd", "4.8.0")])

    result = stub.detectCP4D()

    assert result.ok is False
    assert "Skipping intermediate" in result.message


def test_detectCP4D_skipped_intermediate_version_returns_ok_false():
    """Test detectCP4D when catalog target does not match the required next step.

    GIVEN instance at "5.0.0" (maps to "5.1.3") but catalog target is "5.2.0"
    WHEN detectCP4D is called
    THEN ok=False and message contains "Skipping intermediate".
    """
    stub = _makeStub(catalogCpdVersion="5.2.0")
    _mockCpdApi(stub, [_cpdItem("ibm-cpd", "5.0.0")])

    result = stub.detectCP4D()

    assert result.ok is False
    assert "Skipping intermediate" in result.message


def test_detectCP4D_valid_upgrade_path_sets_params_and_returns_will_be_updated():
    """Test detectCP4D for a valid upgrade: 5.1.3 → 5.2.0.

    GIVEN instance at "5.1.3" and catalog target "5.2.0"
    WHEN detectCP4D is called
    THEN ok=True, message contains "will be updated",
         cp4d_update="true", cpd_product_version="5.2.0",
         storage_class_rwx and storage_class_rwo set.
    """
    stub = _makeStub(catalogCpdVersion="5.2.0")
    _mockCpdApi(stub, [_cpdItem("ibm-cpd", "5.1.3", fileStorage="nfs-sc", blockStorage="rwo-sc")])

    result = stub.detectCP4D()

    assert result.ok is True
    assert "will be updated" in result.message
    assert stub.getParam("cp4d_update") == "true"
    assert stub.getParam("cpd_product_version") == "5.2.0"
    assert stub.getParam("storage_class_rwx") == "nfs-sc"
    assert stub.getParam("storage_class_rwo") == "rwo-sc"


def test_detectCP4D_already_at_target_returns_already_at_target():
    """Test detectCP4D when the instance is already at the target version.

    GIVEN instance at "5.2.0" and catalog target "5.2.0"
    WHEN detectCP4D is called
    THEN ok=True and message contains "already at the target version".
    """
    stub = _makeStub(catalogCpdVersion="5.2.0")
    _mockCpdApi(stub, [_cpdItem("ibm-cpd", "5.2.0")])

    result = stub.detectCP4D()

    assert result.ok is True
    assert "already at the target version" in result.message


def test_detectCP4D_args_cpd_version_overrides_catalog():
    """Test detectCP4D uses the --cpd-product-version arg when provided.

    GIVEN instance at "5.1.3" and args.cpd_product_version is truthy (simulating CLI flag),
         with cpd_product_version param already set to "5.2.0"
    WHEN detectCP4D is called
    THEN the target version read comes from getParam("cpd_product_version").
    """
    stub = _makeStub(catalogCpdVersion="5.0.0", argsCpdVersion="5.2.0")
    stub.setParam("cpd_product_version", "5.2.0")
    _mockCpdApi(stub, [_cpdItem("ibm-cpd", "5.1.3")])

    result = stub.detectCP4D()

    # 5.1.3 → 5.2.0 is a valid upgrade path, so should succeed
    assert result.ok is True
    assert "will be updated" in result.message


def test_detectCP4D_not_found_error_returns_not_installed():
    """Test detectCP4D treats NotFoundError as CRD not installed.

    GIVEN resources.get raises NotFoundError
    WHEN detectCP4D is called
    THEN ok=True and message contains "not installed".
    """
    stub = _makeStub()
    stub.dynamicClient.resources.get.side_effect = NotFoundError(MagicMock())

    result = stub.detectCP4D()

    assert result.ok is True
    assert "not installed" in result.message
