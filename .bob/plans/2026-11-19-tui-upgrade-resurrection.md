# TUI Upgrade Resurrection Plan

**Status:** complete (branch `textual-upgrade`, commit `e9cd7a4ac2`) · **Target branch:** `textual-upgrade` (created from `origin/master` after PR #2715 merged) · **Source branch:** `origin/textual` · **Date:** November 2026

> Goal: resurrect the `mas upgrade` Textual TUI work stranded on the old
> `textual` branch, port it onto the polished TUI framework that landed
> via the `textual-update` PR (#2715), and finish the vertical slice so
> it is ready to merge. Written while the full context of the
> `textual-update` work is fresh.

## Background

The original `textual` branch (8 commits, tip `7411d86a62`) contained TUI
work for both `update` and `upgrade`. The `update` half was rebuilt on
`textual-update` — greatly evolved along the way (shared widgets, theme,
layout contract, pilot-test infrastructure, command generator) — and is
in PR #2715. The `upgrade` half was never ported and is now stranded
against an old framework generation.

**The stranded work is also incomplete.** The old branch's
`buildUpgradeWorkflow` returns only two steps (connect-cluster and
instance-selection) whose docstring promises "on success the workflow
goes directly to the review screen" — but no review or launch step
exists in the definition. So this is a port *and finish* job, not a
cherry-pick.

Meanwhile master has moved: PR #2713 ("Refactor command builder, and
enable for update and upgrade") landed `upgradeArgBuilderMixin.buildCommand`
with round-trip tests (`tests/unit/upgrade/test_upgrade_arg_builder.py`)
— the review screen's equivalent-command panel for upgrade is therefore
nearly free.

## Source inventory (what to mine from `origin/textual`)

Everything below is recoverable with `git show origin/textual:<path>`
or `git diff origin/master origin/textual -- <path>`:

| Piece | Location on `origin/textual` | State |
|---|---|---|
| Workflow builder skeleton | `python/src/mas/cli/upgrade/workflow.py` (75 lines) | Good skeleton; needs review + launch steps added and API check against current models |
| `prepareUpgrade()` | `python/src/mas/cli/upgrade/app.py` (~line 51, ~116 lines) | Channel detection, compatibility matrix, license, Manage Foundation, Monitor order, Civil Kafka, RBAC — reuses non-interactive logic |
| `fetchInstalledInstanceIds()` | same file (~line 167) | post_connect hook; raises "No MAS instances were found" so the error surfaces on the connect screen |
| Storage-class / order helpers | same file (`configPipelineStorageClass`, `configStorageClasses`, `computeMonitorInstallOrderForUpgrade`, `validateKafkaForCivilUpgrade`) | Extracted from the old monolithic `upgrade()` — port as needed by `prepareUpgrade` |
| `__main__.py` dispatch | bare `mas upgrade` (no `--mas-instance-id`/`--help`/`-h`) → `serveTuiMode("upgrade")` | Port, but align with update's dispatch style (see phase 3) |
| Unit tests | `python/tests/unit/upgrade/test_upgrade_workflow.py` (137 lines), `test_upgrade_main.py` (112 lines) | Port to current conventions (GIVEN/WHEN/THEN docstrings, `pytestmark`) |

**Do NOT port:**

- The old branch's own `mas.cli.tui` framework — superseded by the
  version in PR #2715.
- The old branch's wholesale `update/app.py` split (`catalog.py`,
  `rbac.py`) — `textual-update` took a different path (`dependencies.py`
  only) and it merged; following it would create merge conflicts for no
  gain.
- The old branch's dropping of `upgradeArgBuilderMixin` from the
  `UpgradeApp` bases — master's command-builder refactor (#2713) now
  depends on that mixin; keep it and call `buildCommand()` from the TUI
  instead.
- Commit `4b3080f949` ("Doc updates" — deletes dependency diagram docs):
  unrelated to the TUI; separate decision if anyone wants it.

## Target shape

`mas upgrade` with no flags launches the TUI (any flag falls through to
the classic CLI, matching `mas update`). Workflow definition:

1. **connect-cluster** — the shared `connectClusterStep` from
   `mas.cli.common.workflow`, with
   `post_connect=appInstance.fetchInstalledInstanceIds`.
2. **instance-selection** — generic `StepScreen`; `mas_instance_id`
   select field with `options=lambda: appInstance._installedInstanceIds`
   (current `WorkflowField.options` still accepts a zero-argument
   callable — verified against the models on `textual-update`);
   `validator=appInstance.prepareUpgrade`; summary items for instance
   ID, current/next channel, skip-pre-check.
3. **review** — `ReviewScreen` with
   `command_builder=lambda app: app.buildCommand()` (the round-trip
   tests already guarantee the generated command parses), plus a
   `script_filename_builder` (e.g. `mas-upgrade-<instance>.sh`).
4. **launch** — `LaunchScreen` submitting the upgrade pipeline, mirroring
   the update launch step (`screen_kwargs={"command_builder": ...}`).

Everything visual comes for free from the merged framework (theme,
action bars, chrome, layout contract).

## Phased plan

### Phase 0 — Branch setup

After PR #2715 merges:

```
git fetch origin
git checkout --no-track -b textual-upgrade origin/master
```

(`--no-track` so the branch carries no upstream wiring until it is
actually pushed with `git push -u origin textual-upgrade`.)

### Phase 1 — Port the `UpgradeApp` methods (~half day)

Method-by-method onto current master's `upgrade/app.py` — not
file-by-file, the surrounding file has diverged:

- `fetchInstalledInstanceIds` — port as-is.
- `prepareUpgrade` — port with its TUI-mode flag guards
  (`noConfirm = True`, `skipPreCheck`, `licenseAccepted`, `devMode`,
  `nextChannel`, RBAC attrs defaulted when argparse has not run). Check
  each `mas.devops` import still exists at current master's versions;
  the old code was written against an older devops API surface.
- Keep `upgradeArgBuilderMixin` in the class bases; add `tuiMode`
  handling only if `fatalError`/print suppression is not already
  inherited from `BaseApp` (update's app already does this — copy its
  pattern).

### Phase 2 — Write `upgrade/workflow.py` against the current framework

Use `update/workflow.py` as the reference for idioms
(`screen_class`, `screen_kwargs`, `heading_level`, summary items,
`_nonInteractiveCommand` helper). Start from the old branch's 75-line
skeleton, add the review and launch steps it never had. Check
`WorkflowStep`/`WorkflowField` signatures against
`mas/cli/tui/models.py` — the skeleton predates `dynamic_select` and
the current validator protocol; `options` as a callable is still valid.

### Phase 3 — `__main__.py` dispatch

Mirror the update pattern exactly:

```python
if function == "upgrade":
    if not any(arg.startswith("-") for arg in argv[2:]):
        from mas.cli.tui.shell import serveTuiMode
        serveTuiMode("upgrade", argv[2:])
        return
```

The old branch special-cased `--mas-instance-id not in argv`; the
update-style any-flag check gives the same behaviour for that flag and
is one consistent rule across commands. (`--help`/`-h` start with `-`
and fall through to the classic parser, which handles them.)

### Phase 4 — Tests

- **Unit** (`tests/unit/upgrade/`): port `test_upgrade_workflow.py`
  (step ids/order, field wiring, validator binding, command builder
  wiring) and `test_upgrade_main.py` (dispatch) to current conventions —
  GIVEN/WHEN/THEN docstrings, `pytestmark = pytest.mark.tui` where
  Textual is imported. `test_upgrade_app.py`-style tests for
  `prepareUpgrade` / `fetchInstalledInstanceIds` with mocked
  `dynamicClient` (see update's `test_update_app.py` for the mocking
  pattern).
- **Scenarios** (`tests/scenarios/`): add an upgrade registry —
  single-instance, no-instances (post_connect error), incompatible-apps,
  license-not-accepted, already-on-latest-channel. Real `UpgradeApp`
  instances per the scenario-module convention, so both unit and pilot
  tests share them.
- **Pilot** (`tests/pilot/upgrade/`): the generic screens are already
  covered by `tests/pilot/tui/`; add only upgrade-specific flows —
  instance selection populated from post_connect state, validator
  failure shown in the reserved status row, review command panel
  rendering the `buildCommand()` output.

### Phase 5 — Polish and verification

- `tui/dev.py`: switch `COMMAND = "upgrade"` temporarily to eyeball the
  flow end-to-end (no screenshots in chat — the pilot tests and the
  user's own eyeballing are the verification).
- Full TUI unit + pilot suites green; black and flake8 clean; the wider
  repo suite has the known `must_gather/test_timer.py` load flake.
- `AGENTS.md` tree comment already covers `tests/unit/upgrade/` and
  `tests/pilot/upgrade/` by convention — no doc change needed beyond
  any new scenario registry entry.

## Verification

- `tests/unit/upgrade/` + `tests/pilot/upgrade/` green via
  `wsl bash -lc` (repo convention; see memory notes on the WSL venv).
- Manual: `mas upgrade` bare → TUI; `mas upgrade --mas-instance-id inst`
  → classic path; `mas upgrade --help` → classic help.
- The review screen's command panel must survive the
  `test_upgrade_arg_builder.py` round-trip contract (it builds the same
  string the parser must accept).

## Rollback / branch hygiene

- `textual-upgrade` is a fresh branch off merged master — nothing from
  the old `textual` branch is merged, only mined, so no stray history
  comes along.
- The old `textual` branch can be deleted once this lands (it has no
  other unique work: its update half is superseded, its doc deletion is
  out of scope).
