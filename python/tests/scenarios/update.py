# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Named UpdateApp states shared by unit and pilot tests.

Each scenario is a snapshot of the state ``UpdateApp`` holds after the
dependency checks have run against a particular kind of cluster: the params
the detectors populate plus the transient detector attributes. Building a
real ``UpdateApp`` (rather than a MagicMock) means the pending-confirmation
helpers (``upgradeConfirmationsPending`` etc.) compute their answers exactly
as production code does, so tests exercise real behaviour rather than
stubbed return values.

Scenarios are also the intended states for the future manual testing
harness, keeping automated and manual testing on identical fixtures.
"""

from mas.cli.update.app import UpdateApp

# Scenario registry. ``params`` are written into app.params; ``attrs`` are
# set directly on the app instance (detector state). ``license_path``
# optionally pre-provides a Db2 license file path (as --db2-license-file
# or a prior TUI entry would).
UPDATE_SCENARIOS = {
    # Nothing detected: no dependencies, no pending confirmations. The
    # confirm-upgrades step is skipped and review shows "No action required".
    "clean": {
        "params": {},
        "attrs": {},
    },
    # Db2 11 detected in a single namespace, target catalog moves to 12 —
    # the v11 to v12 upgrade requiring a license file.
    "db2-v11-to-v12": {
        "params": {"db2_namespace": "db2u"},
        "attrs": {"db2CurrentMajorVersion": 11, "db2TargetMajorVersion": 12},
    },
    # Db2 upgrade already confirmed (e.g. --db2-v12-upgrade) but the license
    # file has not been provided yet.
    "db2-license-only": {
        "params": {"db2_namespace": "db2u", "db2_v12_upgrade": "true"},
        "attrs": {"db2CurrentMajorVersion": 11, "db2TargetMajorVersion": 12},
    },
    # Major-version bump that does not require a license file (future
    # v12 to v13 style): confirmation is a checkbox, not a path input.
    "db2-major-no-license": {
        "params": {"db2_namespace": "db2u"},
        "attrs": {"db2CurrentMajorVersion": 12, "db2TargetMajorVersion": 13},
    },
    # Db2 already at the target version: nothing pending.
    "db2-current-at-target": {
        "params": {"db2_namespace": "db2u", "db2_v12_upgrade": "false"},
        "attrs": {"db2CurrentMajorVersion": 12, "db2TargetMajorVersion": 12},
    },
    # MongoDB Community major-version update pending (7 -> 8).
    "mongo-major": {
        "params": {"mongodb_namespace": "mongo-ns", "mongodb_action": "install"},
        "attrs": {"mongoCurrentVersion": "7.0.5", "mongoTargetVersion": "8.0.14"},
    },
    # Both a MongoDB major update and the Db2 v11 to v12 upgrade pending.
    "mongo-and-db2-v12": {
        "params": {"db2_namespace": "db2u", "mongodb_namespace": "mongo-ns", "mongodb_action": "install"},
        "attrs": {
            "db2CurrentMajorVersion": 11,
            "db2TargetMajorVersion": 12,
            "mongoCurrentVersion": "7.0.5",
            "mongoTargetVersion": "8.0.14",
        },
    },
    # All supported dependencies detected: review rendering variety.
    "dependencies-detected": {
        "params": {
            "db2_namespace": "db2u",
            "mongodb_namespace": "mongo-ns",
            "kafka_namespace": "kafka-ns",
            "cp4d_update": "true",
            "grafana_v5_upgrade": "true",
            "odh_to_rhoai_migration": "true",
        },
        "attrs": {},
    },
    # ODH to RHOAI migration with RHOAI v2 already detected.
    "rhoai-v2-detected": {
        "params": {"odh_to_rhoai_migration": "true"},
        "attrs": {"rhoaiV2Detected": True},
    },
}


def update_scenario(name: str, license_path: str | None = None) -> UpdateApp:
    """Return a real UpdateApp instance in the named scenario state.

    Args:
        name (str): Scenario name (a key of UPDATE_SCENARIOS).
        license_path (str, optional): Db2 license file path to pre-provide,
            as ``--db2-license-file`` or a prior TUI entry would.

    Returns:
        UpdateApp: App in tuiMode with the scenario's params and detector
            state applied.
    """
    scenario = UPDATE_SCENARIOS[name]
    app = UpdateApp()
    app.tuiMode = True
    app.params.update(scenario["params"])
    for key, value in scenario["attrs"].items():
        setattr(app, key, value)
    if license_path is not None:
        app.db2LicenseFileLocal = license_path
    return app
