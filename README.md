IBM Maximo Application Suite CLI Utility
===============================================================================
[![Code Style: Black](https://img.shields.io/badge/Code%20Style-Black-000000.svg)](https://github.com/psf/black)
[![Flake8: Checked](https://img.shields.io/badge/Flake8-Checked-blueviolet)](https://flake8.pycqa.org/en/latest/)
![PyPI - Version](https://img.shields.io/pypi/v/mas.cli)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/mas.cli)

[![Build CLI](https://github.com/ibm-mas/cli/actions/workflows/build-cli.yml/badge.svg)](https://github.com/ibm-mas/cli/actions/workflows/build-cli.yml)
[![Build Docs](https://github.com/ibm-mas/cli/actions/workflows/docs.yml/badge.svg)](https://github.com/ibm-mas/cli/actions/workflows/build-cli.yml)
[![GitHub release](https://img.shields.io/github/v/release/ibm-mas/cli)](https://github.com/ibm-mas/cli/releases/latest)


Documentation
-------------------------------------------------------------------------------
[https://ibm-mas.github.io/cli/](https://ibm-mas.github.io/cli/)


Dependency Switchover Breakpoints
-------------------------------------------------------------------------------
The Maximo Operator Catalogs pin default versions for the major dependencies, and
`mas update` compares the installed version against the target catalog's defaults
(see the `DetectResult` registry in `python/src/mas/cli/update/dependencies.py` and
the detectors in `python/src/mas/cli/update/app.py`).  The catalog metadata itself
lives in the [ansible-devops](https://github.com/ibm-mas/ansible-devops) catalog
registry (`mas/devops/data/catalogs/*.yaml`); the generated per-catalog package
manifests in [docs/catalogs/](docs/catalogs/) are derived from it.

### MongoDB (`mongo_extras_version_default`)

| Breakpoint | Catalog | Default Version |
|------------|---------|-----------------|
| First catalog with the field | v8-231004 (Oct 2023) | 4.4.21 |
| v4.4 → v5.0 | v8-231128 (28 Nov 2023) | 5.0.21 |
| v5.0 → v6.0 | v9-240625 (25 Jun 2024) | 6.0.12 |
| v6.0 → v7.0 | v9-241003 (3 Oct 2024) | 7.0.12 |
| v7.0 → v8.0 | v9-251127 (27 Nov 2025) | 8.0.13 |

### IBM Db2 (`db2_channel_default`)

| Breakpoint | Catalog | Default db2u Channel |
|------------|---------|----------------------|
| Long-standing default (field absent pre-v9-260129, CLI falls back to `v110509.0`) | ≤ v9-260527 | v110509.0 (Db2 11.5.9) |
| Db2 v11 → v12 | v9-260625 (25 Jun 2026) | v120104.0 (Db2 12.1) — triggers `db2_v12_upgrade` and requires `--db2-license-file` |
| v120104.0 → v120105.0 | v9-260827 (27 Aug 2026) | v120105.0 |

Db2 12 channels (v120100.0 – v120104.0) were already present as options in earlier
catalogs; v9-260625 is where the **default** flipped.

### Open Data Hub → RHOAI v2

RHOAI is not part of the catalog registry — this switchover is driven by CLI and
ansible-devops code, so the breakpoints are the first catalogs published after each
code change:

- **New installs**: ansible-devops #2091 / cli #2027 (merged 6 Feb 2026, "Replace ODH
  with RHOAI - New Install", `rhoai_channel` default `stable` = v2) → first catalog
  **v9-260216 (16 Feb 2026)**.
- **`mas update` migration** (`odh_to_rhoai_migration`): ansible-devops #2153 /
  cli #2133 (merged 10 Apr 2026) → first catalog **v9-260430 (30 Apr 2026)**.
- ODH support was fully dropped in **AI Service 9.1.18** (RHOAI 2.25.10+ required).

### RHOAI v2 → v3

- ansible-devops #2494 / cli #2686 (both 3 Nov 2026): `rhoai_channel` default changed
  from `stable` to `stable-3.x`.  There is no in-place upgrade path — RHOAI v2 is
  uninstalled and v3 installed (DSCInitialization and DataScienceCluster are recreated).
- First catalog: **v9-261105 (5 Nov 2026)**.  v9-261029 (29 Oct 2026) still installs
  RHOAI v2, so updating to v9-261105 is what triggers the v2 → v3 replacement.

### IBM Cloud Pak for Data (`cpd_product_version_default`)

| Default | First Catalog |
|---------|---------------|
| 4.8.0 | v9-240625 |
| 5.0.0 | v9-241205 |
| 5.1.3 | v9-250624 |
| 5.2.0 | v9-251224 |
| 5.3.1 | v9-260827 |
| 5.4.0 | v9-261029 |

`mas update` enforces a hop-by-hop path through these versions (no skipping
intermediates) via `cpdUpgradePath` in `python/src/mas/cli/update/app.py`.

### How the RHOAI/ODH choice is actually made

Unlike the dependencies above, RHOAI is not shipped in the IBM Maximo Operator
Catalog — it is a Red Hat operator (`rhods-operator` from `redhat-operators`) —
so the catalog registry has no field that pins it.  The platform choice is
decided entirely by the CLI version:

- The install pipeline contains both an `aiservice-odh` and an `aiservice-rhoai`
  task; the only selection gate is the `rhoai` boolean param
  (`tekton/src/pipelines/taskdefs/aiservice/odh.yml.j2` and `rhoai.yml.j2`).
- The current CLI sets `rhoai=true` unconditionally
  (`python/src/mas/cli/aiservice/install/app.py`), without consulting the catalog
  or the AI Service channel.  Before cli #2027 (6 Feb 2026) the `rhoai` param did
  not exist and the ODH task always ran.
- On update, `detectODH`/`detectRHOAIv2` key off the live cluster state (ODH
  subscription present, or `rhods-operator` CSV major version), not the target
  catalog, and the role installs whatever `rhoai_channel` says (role default
  `stable-3.x` today).

**Consequence:** the same catalog tag installs a different data-science platform
depending on which CLI image runs it — e.g. catalog v9-260129 (AI Service 9.1.11)
plus a CLI from January 2026 installs ODH, while the same catalog plus a current
CLI installs RHOAI v3.  Likewise, updating an ODH cluster to *any* target catalog
with a current CLI migrates ODH → RHOAI v3 in one hop.

This is fragile because the AI Service operator version (catalog-driven) ↔ RHOAI
version (CLI-driven) compatibility matrix is not encoded anywhere
machine-readable: nothing prevents an old catalog's AI Service from being
installed on top of a RHOAI version it was never tested with.  The only guard is
the advisory in `python/src/mas/cli/install/app.py` recommending that the CLI
version align with the catalog release date.  A clean fix would encode the
minimum AI Service version per RHOAI major in the catalog registry (alongside
the other `*_default` fields) and fail fast on unsupported pairings.


Want to contribute to MAS Command Line Interface?
--------------------------------------------------------------------------------
We welcome every Maximo Application Suite users, developers and enthusiasts to contribute to the MAS Command Line Interface while fixing code issues and implementing new automated functionalities.

You can contribute to this collection by raising [a new issue](https://github.com/ibm-mas/cli/issues) with suggestions on how to make our MAS automation engine even better, or if you want to become a new code contributor, please refer to the [Contributing Guidelines](CONTRIBUTING.md) and learn more about how to get started.

