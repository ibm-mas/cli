# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Unit tests for the shared StorageClassMixin (mas/cli/common/storageClasses.py).

Covers the memoized lookup (options + provider detection cached on the
app), and the configStorageClasses resolution flow's two flavours:
``cliArgsWin`` (upgrade — provided values win, detection auto-accepted
under --no-confirm) and the install flavour (detection offered as the
default, user confirms or overrides), plus the "none" RWX exemption and
the no-detection error paths (TUI vs --no-confirm messages).
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from mas.cli.common.storageClasses import StorageClassMixin

DETECTED = SimpleNamespace(
    provider="ocs",
    providerName="OpenShift Container Storage",
    rwo="ocs-storagecluster-ceph-rbd",
    rwx="ocs-storagecluster-cephfs",
)
NO_DETECTION = SimpleNamespace(provider=None, providerName=None, rwo=None, rwx=None)


class _Host(StorageClassMixin):
    """Minimal BaseApp stand-in exercising the mixin's host contract."""

    def __init__(self, params=None, noConfirm=False, tuiMode=False):
        self.params = params if params is not None else {}
        self.noConfirm = noConfirm
        self.tuiMode = tuiMode
        self.dynamicClient = MagicMock()
        self.yesOrNoResponse = True
        self.printed = []

    def printDescription(self, content):
        self.printed.append(("description", content))

    def yesOrNo(self, message):
        self.printed.append(("yesOrNo", message))
        return self.yesOrNoResponse

    def fatalError(self, message):
        raise RuntimeError(message)

    def getParam(self, param):
        return self.params.get(param, "")


def _storageClasses(names=("ocs-storagecluster-ceph-rbd", "ocs-storagecluster-cephfs", "custom-nfs")):
    """Return fake storage class objects shaped like the mas.devops API."""
    return [SimpleNamespace(metadata=SimpleNamespace(name=name)) for name in names]


def _patches(defaults=DETECTED, names=None):
    """Return patchers for the mixin module's cluster lookups.

    Args:
        defaults (SimpleNamespace): getDefaultStorageClasses return value.
        names (tuple, optional): Storage class names for getStorageClasses.

    Returns:
        tuple: (getStorageClasses, getDefaultStorageClasses, getStorageClass,
        prompt) patchers, all targeting mas.cli.common.storageClasses.
    """
    classes = _storageClasses() if names is None else _storageClasses(names)
    return (
        patch("mas.cli.common.storageClasses.getStorageClasses", return_value=classes),
        patch("mas.cli.common.storageClasses.getDefaultStorageClasses", return_value=defaults),
        patch("mas.cli.common.storageClasses.getStorageClass", return_value=object()),
        patch("mas.cli.common.storageClasses.prompt"),
    )


# ---------------------------------------------------------------------------
# lookupStorageClasses
# ---------------------------------------------------------------------------


def test_lookup_caches_options_and_detection():
    """Test that the lookup is memoized and caches the provider detection.

    GIVEN a host app on a cluster with three storage classes and a
        detectable provider
    WHEN lookupStorageClasses is called twice
    THEN both calls return the same sorted names, the cluster is only
        queried once, and the detection attributes are populated for the
        TUI dropdown defaults and context row.
    """
    host = _Host()
    getSc, getDefaults, _, _ = _patches()
    with getSc as mock_sc, getDefaults as mock_defaults:
        first = host.lookupStorageClasses()
        second = host.lookupStorageClasses()

    assert first == ["custom-nfs", "ocs-storagecluster-ceph-rbd", "ocs-storagecluster-cephfs"]
    assert first == second
    mock_sc.assert_called_once()
    mock_defaults.assert_called_once()
    assert host.detectedStorageProviderName == "OpenShift Container Storage"
    assert host.detectedStorageClasses.rwo == "ocs-storagecluster-ceph-rbd"


def test_lookup_without_detection_leaves_provider_attrs_none():
    """Test that an unrecognized cluster leaves the provider attrs unset.

    GIVEN a host app on a cluster with no known storage provider
    WHEN lookupStorageClasses is called
    THEN the class names are still returned (for the dropdowns) but
        detectedStorageProviderName is None, so no default is pre-selected.
    """
    host = _Host()
    getSc, getDefaults, _, _ = _patches(defaults=NO_DETECTION)
    with getSc, getDefaults:
        names = host.lookupStorageClasses()

    assert len(names) == 3
    assert host.detectedStorageProviderName is None


# ---------------------------------------------------------------------------
# configStorageClasses — cliArgsWin (upgrade flavour)
# ---------------------------------------------------------------------------


def test_cli_args_win_uses_provided_classes_without_detection():
    """Test that fully-provided values are validated and used as-is.

    GIVEN a host with both storage classes already in params (CLI flags or
        TUI dropdown selections) available on the cluster
    WHEN configStorageClasses runs with the upgrade flavour
    THEN the classes are validated against the cluster and no provider
        detection runs (mock_defaults not called).
    """
    host = _Host(params={"storage_class_rwo": "custom-nfs", "storage_class_rwx": "ocs-storagecluster-cephfs"})
    getSc, getDefaults, getOne, prompt = _patches()
    with getSc, getDefaults as mock_defaults, getOne as mock_get_one, prompt as mock_prompt:
        StorageClassMixin.configStorageClasses(host)

    mock_get_one.assert_any_call(host.dynamicClient, "custom-nfs")
    mock_get_one.assert_any_call(host.dynamicClient, "ocs-storagecluster-cephfs")
    mock_defaults.assert_not_called()
    mock_prompt.assert_not_called()
    assert host.params["storage_class_rwo"] == "custom-nfs"


def test_cli_args_win_invalid_class_raises():
    """Test that a provided class missing from the cluster fails fast.

    GIVEN a host with an RWO storage class that does not exist on the
        cluster
    WHEN configStorageClasses runs
    THEN RuntimeError names the class and the flag it came from.
    """
    host = _Host(params={"storage_class_rwo": "missing-sc"})
    getSc, getDefaults, getOne, prompt = _patches()
    with getSc, getDefaults, patch("mas.cli.common.storageClasses.getStorageClass", return_value=None), prompt:
        with pytest.raises(RuntimeError, match="missing-sc.*--storage-class-rwo"):
            StorageClassMixin.configStorageClasses(host)


def test_cli_args_win_auto_accepts_detection_under_no_confirm():
    """Test that detection is auto-accepted without prompting under --no-confirm.

    GIVEN a no-confirm host with no storage classes in params, on a
        cluster with a detectable provider
    WHEN configStorageClasses runs with the upgrade flavour
    THEN the detected classes are written to params without any yes/no
        prompt (the TUI dropdowns already pre-selected them).
    """
    host = _Host(noConfirm=True)
    getSc, getDefaults, getOne, prompt = _patches()
    with getSc, getDefaults, getOne, prompt as mock_prompt:
        StorageClassMixin.configStorageClasses(host)

    assert host.params["storage_class_rwo"] == "ocs-storagecluster-ceph-rbd"
    assert host.params["storage_class_rwx"] == "ocs-storagecluster-cephfs"
    mock_prompt.assert_not_called()
    # The yesOrNo confirmation is skipped entirely under --no-confirm
    assert not any(kind == "yesOrNo" for kind, _ in host.printed)


def test_cli_args_win_no_detection_tui_message():
    """Test the TUI no-detection error names the step's dropdowns.

    GIVEN a no-confirm TUI host on a cluster with no detectable provider
    WHEN configStorageClasses runs
    THEN RuntimeError carries the TUI message (the dropdowns are where the
        user must provide the classes), not the CLI flag message.
    """
    host = _Host(noConfirm=True, tuiMode=True)
    getSc, getDefaults, getOne, prompt = _patches(defaults=NO_DETECTION)
    with getSc, getDefaults, getOne, prompt:
        with pytest.raises(RuntimeError, match="on this step"):
            StorageClassMixin.configStorageClasses(host, noDetectionTuiMessage="No storage classes could be detected. Enter them on this step.")


def test_cli_args_win_no_detection_no_confirm_message():
    """Test the classic no-detection error names the CLI flags.

    GIVEN a no-confirm non-TUI host on a cluster with no detectable
        provider
    WHEN configStorageClasses runs
    THEN RuntimeError carries the --no-confirm message naming
        --storage-class-rwo and --storage-class-rwx.
    """
    host = _Host(noConfirm=True)
    getSc, getDefaults, getOne, prompt = _patches(defaults=NO_DETECTION)
    with getSc, getDefaults, getOne, prompt:
        with pytest.raises(RuntimeError, match="--no-confirm.*--storage-class-rwo"):
            StorageClassMixin.configStorageClasses(host)


def test_cli_args_win_interactive_falls_back_to_prompt():
    """Test that an interactive run with no detection prompts for both classes.

    GIVEN an interactive host with no storage classes in params on a
        cluster with no detectable provider
    WHEN configStorageClasses runs
    THEN the prompt pair collects both classes (prompting only for values
        not already in params) and marks the provider as custom.
    """
    host = _Host()
    getSc, getDefaults, getOne, prompt = _patches(defaults=NO_DETECTION)
    with getSc, getDefaults, getOne, prompt as mock_prompt:
        mock_prompt.side_effect = ["custom-nfs", "ocs-storagecluster-cephfs"]
        StorageClassMixin.configStorageClasses(host)

    assert host.params["storage_class_rwo"] == "custom-nfs"
    assert host.params["storage_class_rwx"] == "ocs-storagecluster-cephfs"
    assert mock_prompt.call_count == 2
    assert host.storageClassProvider == "custom"


# ---------------------------------------------------------------------------
# configStorageClasses — install flavour (cliArgsWin=False)
# ---------------------------------------------------------------------------


def test_install_flavour_detection_accepted():
    """Test that the install flavour offers detection and keeps it on yes.

    GIVEN an interactive install-flavour host on a cluster with a
        detectable provider
    WHEN the user accepts the auto-detected classes
    THEN the detected classes are written to params and no prompt pair
        runs.
    """
    host = _Host()
    host.yesOrNoResponse = True
    getSc, getDefaults, getOne, prompt = _patches()
    with getSc, getDefaults, getOne, prompt as mock_prompt:
        StorageClassMixin.configStorageClasses(host, cliArgsWin=False, allowRwxNone=True)

    assert host.params["storage_class_rwo"] == "ocs-storagecluster-ceph-rbd"
    assert host.params["storage_class_rwx"] == "ocs-storagecluster-cephfs"
    mock_prompt.assert_not_called()
    assert host.storageClassProvider == "ocs"


def test_install_flavour_detection_declined_prompts():
    """Test that declining the detected classes prompts for both.

    GIVEN an interactive install-flavour host with a detectable provider
    WHEN the user declines the auto-detected classes
    THEN both classes are prompted for (the install override prompts both,
        even values already in params) and the provider is custom.
    """
    host = _Host()
    host.yesOrNoResponse = False
    getSc, getDefaults, getOne, prompt = _patches()
    with getSc, getDefaults, getOne, prompt as mock_prompt:
        mock_prompt.side_effect = ["custom-nfs", "custom-nfs"]
        StorageClassMixin.configStorageClasses(host, cliArgsWin=False, allowRwxNone=True)

    assert host.params["storage_class_rwo"] == "custom-nfs"
    assert host.params["storage_class_rwx"] == "custom-nfs"
    assert mock_prompt.call_count == 2
    assert host.storageClassProvider == "custom"


def test_install_flavour_none_rwx_is_valid():
    """Test that "none" is an accepted RWX answer in the install flavour.

    GIVEN an install-flavour host with storage_class_rwx set to "none"
        (no suitable ReadWriteMany class on the cluster) on a cluster with
        no detectable provider
    WHEN configStorageClasses validates the provided values
    THEN "none" is exempt from cluster validation (no fatal error naming
        it) and the user keeps the provided pair.
    """
    host = _Host(params={"storage_class_rwo": "custom-nfs", "storage_class_rwx": "none"})
    host.yesOrNoResponse = True
    getSc, getDefaults, getOne, prompt = _patches(defaults=NO_DETECTION)
    with getSc, getDefaults, getOne as mock_get_one, prompt as mock_prompt:
        StorageClassMixin.configStorageClasses(host, cliArgsWin=False, allowRwxNone=True)

    # Only the RWO class is validated against the cluster
    mock_get_one.assert_called_once_with(host.dynamicClient, "custom-nfs")
    mock_prompt.assert_not_called()
    assert host.params["storage_class_rwx"] == "none"
