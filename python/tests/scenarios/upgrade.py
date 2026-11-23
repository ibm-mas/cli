# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
# *****************************************************************************

"""Named UpgradeApp states shared by unit and pilot tests.

Each scenario is a snapshot of the state ``UpgradeApp`` holds at a
particular point in the TUI workflow: right after the connect step's
``post_connect`` (the instance list) or right after ``prepareUpgrade``
(the channel and storage class state the review screen renders).  Building
a real ``UpgradeApp`` (rather than a MagicMock) means the arg-builder
command rendering computes exactly as production code does.

The error paths of the workflow (no instances on the cluster, incompatible
apps, license not accepted, already on the latest channel) are cluster
behaviours rather than app states, so they are covered by the
``prepareUpgrade`` / ``fetchInstalledInstanceIds`` unit tests with a mocked
dynamic client (see tests/unit/upgrade/test_upgrade_app.py) instead of
scenario entries.
"""

from mas.cli.upgrade.app import UpgradeApp

# Scenario registry. ``params`` are written into app.params; ``attrs`` are
# set directly on the app instance (state populated by post_connect /
# prepareUpgrade).
UPGRADE_SCENARIOS = {
    # Connected to a cluster with a single MAS instance — the state the
    # instance-selection step renders its select from.
    "single-instance": {
        "params": {},
        "attrs": {"_installedInstanceIds": ["inst1"]},
    },
    # Connected to a cluster with two MAS instances — select ordering.
    "multiple-instances": {
        "params": {},
        "attrs": {"_installedInstanceIds": ["dev", "prod"]},
    },
    # Happy path after prepareUpgrade: 9.1.x -> 9.2.x with the pipeline
    # storage class read from the existing config-pvc — the state the
    # review step renders.
    "upgrade-9-1-to-9-2": {
        "params": {"mas_instance_id": "inst1"},
        "attrs": {
            "masInstanceId": "inst1",
            "currentChannel": "9.1.x",
            "nextChannel": "9.2.x",
            "effectiveCurrentChannel": "9.1.x",
            "pipelineStorageClass": "ocs-storagecluster-cephfs",
            "pipelineStorageAccessMode": "ReadWriteMany",
        },
    },
    # Channel could not be detected from the cluster (e.g. upgrade queued
    # to run after install) — the review screen renders placeholders.
    "unknown-channel": {
        "params": {"mas_instance_id": "inst1"},
        "attrs": {
            "masInstanceId": "inst1",
            "currentChannel": "Unknown",
            "nextChannel": "Unknown",
        },
    },
    # 9.0.x to 9.1.x without Manage installed: the upgrade installs Manage
    # Foundation — the state after prepareUpgrade detects it, before the
    # manage-foundation step has collected its inputs.
    "manage-foundation": {
        "params": {"mas_instance_id": "inst1"},
        "attrs": {
            "masInstanceId": "inst1",
            "currentChannel": "9.0.x",
            "nextChannel": "9.1.x",
            "effectiveCurrentChannel": "9.0.x",
            "isManageFoundation": True,
        },
    },
    # The same upgrade with the manage-foundation step completed: inputs
    # collected and params configured (the state the review step renders).
    "manage-foundation-configured": {
        "params": {
            "mas_instance_id": "inst1",
            "should_install_manage_foundation": "true",
            "mas_app_channel_manage": "9.1.x",
            "storage_class_rwo": "ocs-storagecluster-ceph-rbd",
            "storage_class_rwx": "ocs-storagecluster-cephfs",
            "db2_action_manage": "install",
        },
        "attrs": {
            "masInstanceId": "inst1",
            "currentChannel": "9.0.x",
            "nextChannel": "9.1.x",
            "effectiveCurrentChannel": "9.0.x",
            "isManageFoundation": True,
            "pipelineStorageClass": "ocs-storagecluster-cephfs",
            "pipelineStorageAccessMode": "ReadWriteMany",
        },
    },
    # Instance already on the latest channel — nothing to upgrade.
    "already-on-latest-channel": {
        "params": {"mas_instance_id": "inst1"},
        "attrs": {
            "masInstanceId": "inst1",
            "currentChannel": "9.3.x-feature",
            "nextChannel": "",
        },
    },
}


def upgrade_scenario(name: str) -> UpgradeApp:
    """Return a real UpgradeApp instance in the named scenario state.

    Args:
        name (str): Scenario name (a key of UPGRADE_SCENARIOS).

    Returns:
        UpgradeApp: App in tuiMode with the scenario's params and state
            applied.
    """
    scenario = UPGRADE_SCENARIOS[name]
    app = UpgradeApp()
    app.tuiMode = True
    app.params.update(scenario["params"])
    for key, value in scenario["attrs"].items():
        setattr(app, key, value)
    return app
