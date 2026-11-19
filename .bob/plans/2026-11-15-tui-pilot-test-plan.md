# TUI Pilot Test Plan

**Status:** implemented (phases 1–3, November 2026) · **Branch:** `textual-update` · **Date:** November 2026

> **Implementation notes (added after phases 1–3 landed):**
>
> - The first real-app pilot test run found the bug it was built to catch:
>   the confirm-upgrades screen accepted a Db2 license path pointing at a
>   non-existent file and advanced — the failure only surfaced when the
>   pipeline launch opened the file. Fixed by validating the path
>   (`isfile`, after `~` expansion) at confirmation time
>   (`tui/screens/confirm_upgrades.py`).
> - A second related bug: a workflow reset did not clear the collected
>   license path, so `db2LicenseFileNeeded()` (which only checks for None)
>   skipped the license input on the second pass, silently reusing a stale
>   path. Fixed with the `resetWorkflowState()` app hook, called by the
>   shell on `WorkflowReset`.
> - Two Textual pilot gotchas are documented in
>   `tests/pilot/harness.py`: (1) a Button swallows a Click while its
>   `-active` press-animation class is present, so back-to-back pilot
>   clicks on the same button lose the second press (`click_button` waits
>   out the animation); (2) lazily-mounted panels only appear once a
>   refresh cycle runs — plain `asyncio.sleep` does not drive Textual's
>   refresh, `pilot.pause()` does (`wait_for_widget`).
> - Widget assertions must run inside the pilot context — the DOM is torn
>   down after `run_test()` exits.

## Background

The first vertical slice of the Textual TUI (`mas-cli update`) shipped with
thorough mock-based unit coverage but almost no *live* coverage of the
screens themselves — the first bug reported against the confirm-upgrades
screen (entering the Db2 license path and clicking Confirm appeared to do
nothing) was a UI-flow defect that mocks could not catch, because the screen's
logic was correct in isolation and only its interaction contract was wrong.

This plan introduces **pilot tests** — live Textual
[`run_test()`](https://textual.textualize.io/guide/testing/) pilots that
mount a screen with a stubbed MAS app and drive it with real events — as a
first-class test category, alongside a shared **scenario module** that will
later also drive a manual testing harness.

## Test taxonomy

Three top-level categories, split by *what the test drives*:

| Category | Drives | Requires | Location |
|---|---|---|---|
| **integration** | the real `mas-cli` process against a real OCP cluster | cluster credentials | `tests/integration/` |
| **unit** | the business logic in the app, with the UI mocked away | nothing (mocked deps) | `tests/unit/` |
| **pilot** | the UI sitting in front of the app, via a live Textual pilot | nothing (stubbed app) | `tests/pilot/` |

Within `unit/` and `pilot/`, a second axis separates **framework** from
**command**:

- `tui/` — the TUI framework the command UIs are built on (shell, models,
  messages, generic screens)
- `update/` — update-command-specific logic and screens

```
tests/
├── integration/          # needs a real OCP cluster
├── unit/                 # business logic, mocked — drives the app under the UI
│   ├── tui/              #   framework: shell, models, messages, generic screens
│   └── update/           #   update command: app logic + update-specific screens
└── pilot/                # live Textual pilot — drives the UI in front of the app
    ├── tui/              #   framework screens (generic step, review, overlays)
    └── update/           #   update screens (confirm-upgrades, auto-run, connect, launch)
```

Rationale for the split:

- **Humans spot gaps.** `pilot/update/` reads as a coverage map: missing
  files are missing live coverage (today that glance would show the connect
  screen has none).
- **Zero CI wiring.** `build-cli.yml` runs `pytest python/tests`, so the new
  directory is picked up automatically and pilot tests run in the unit gate.
- **Cost accepted:** a screen's tests live in two trees (logic in
  `unit/`, UI in `pilot/`). Mitigated by identical base filenames across the
  pair — e.g. `unit/update/test_update_confirm_upgrades.py` and
  `pilot/update/test_update_confirm_upgrades.py` read as companions.

Rule of thumb going forward: logic-only assertions stay mock (fast);
anything involving **rendering, events, focus, or compose structure**
becomes pilot.

### Marker mechanics

- Add `pilot: Live Textual pilot tests` to the `markers` list in `pytest.ini`.
- Auto-apply the marker from `tests/pilot/conftest.py` via a
  `pytest_collection_modifyitems` hook — no per-file `pytestmark`, and the
  marker can never drift out of sync with the directory.
- `-m "not pilot"` then gives a fast local loop if suite time grows.
- Async pattern: keep the repo's existing `asyncio.run(...)` inside sync
  test functions — no `pytest-asyncio` dependency.

## Phases

### Phase 1 — Shared scenario module (~half day)

New module (neutral location importable from both `unit/` and `pilot/`,
e.g. `tests/scenarios/`): a base `make_mas_app()` builder (params dict wired
to `getParam`/`setParam`, `tuiMode=True`, detector-state attributes) plus a
declarative scenario registry with attribute/param overlays.

```python
def make_mas_app(**overlays) -> MagicMock: ...   # base builder

SCENARIOS = {
    "db2-v11-to-v12": {...},
    ...
}
def scenario(name: str) -> MagicMock: ...
```

This module is **the deliverable that the future manual testing harness
(consuming the same named states via `dev.py --screen X --scenario Y`) will
use verbatim**. Build it now, prove it against real assertions, and the
manual harness inherits tested fixtures instead of writing them blind.

#### Update-command scenarios

| Scenario | State | Exercises |
|---|---|---|
| `clean` | No dependencies, nothing pending | confirm-upgrades condition → skipped; review shows "No action required"; auto-run all-pass |
| `db2-v11-to-v12` | Db2 11 in `db2u` → 12, license needed | License path is the confirmation; Confirm advances straight to review |
| `db2-license-only` | `db2_v12_upgrade=true` already set, license still `None` | The `or` branch in compose; partial `_writeConfirmations` |
| `db2-major-no-license` | Major bump with no license requirement | Checkbox path (future v12→13 style) |
| `mongo-major` | Mongo 7→8 pending | Mongo checkbox + backup notice |
| `mongo-and-db2-v12` | Both pending | Multiple sections; both params written on Confirm |
| `multi-namespace-db2` | Detection blocked, CLI guidance shown | Auto-run blocked state (known TUI limitation) |
| `dependencies-detected` | db2/mongo/kafka/cp4d/grafana/odh params set | Review rendering variety |
| `odh-to-rhoai` / `rhoai-v2` | Migration variants | Review migration-text branches |
| `dep-check-failure` | A detector returns fatal | Auto-run error + Quit (silent-hang bug class from the original branch) |

Deliverables:

- Scenario module with the registry above.
- **Cleanup:** move update-specific screen tests out of `unit/tui/` into
  `unit/update/` (`test_tui_auto_run_screen.py` imports
  `mas.cli.update.dependencies`; `test_tui_confirm_upgrades_screen.py`
  exercises `UpdateApp` helpers — both are misfiled as framework tests).
- Migrate existing per-file stub builders (`conftest.make_app`,
  `_make_screen`/`_make_live_app` helpers) onto the shared module.
- No test-behavior change: all existing tests still pass.

### Phase 2 — Pilot harness (~2–3 hours)

In `tests/pilot/conftest.py`: a `pilot_screen(screen, mas_app)` helper — a
bare Textual `App` that:

1. Mounts one screen with the stub `mas_app`
2. Records posted messages (`StepCompleted`, `WorkflowReset`,
   `ActionComplete`) and params writes
3. Yields the pilot so the test drives it (`pilot.click`, `Input.value`, …)

Tests assert "screen posted `StepCompleted(3)` and wrote
`db2_v12_upgrade=true`" rather than "the shell advanced to review" — no
workflow mapping needed. The shell keeps its role as the *wiring* layer,
tested by the existing shell-level files unchanged.

Deliverables: harness helper, marker hook, one harness smoke test.

### Phase 3 — Per-screen pilot tests (~1 day)

| Screen | Action | Coverage added |
|---|---|---|
| `confirm_upgrades` | Migrate the three live tests added with the license-input fix onto the harness; extend with `mongo-major`, `mongo-and-db2-v12`, `db2-license-only` | Full confirm/abort/validation matrix per scenario |
| `connect` | **New** (no dedicated test file exists today) | Connect success → `StepCompleted`; error → inline, no advance |
| `auto_run` | Add pilot tests alongside existing mocks | All-pass → Next; failure → Quit visible |
| `launch` | Add pilot tests | Button flow, progress callbacks streaming into the log pane |
| `review`, `action_overlay`, `params_overlay`, generic `step` | Leave as-is (covered via shell tests); optionally migrate later | — |

Deliverables: pilot files under `tests/pilot/update/` (and `tests/pilot/tui/`
for anything genuinely framework-level), all green in CI.

## Deferred

- **Snapshot testing** (`pytest-textual-snapshot`): renders screens to SVG
  and diffs against committed snapshots — catches the "layout is a bit off"
  bug class that behavior tests miss. Revisit at ~4–5 screens.
- **Manual testing harness**: `dev.py --screen confirm-upgrades --scenario
  db2-v11-to-v12` boots the real shell with the shared scenario states and
  prior steps pre-completed, for hands-on testing without a cluster. Builds
  entirely on Phase 1; no rework of anything above.

## Budget

- Current unit suite: ~68s (472 tests). Estimate +20–40 pilot tests at
  ~0.5–1.5s each ≈ +20–50s. Acceptable; `-m "not pilot"` is the escape
  hatch before it ever becomes a problem.
