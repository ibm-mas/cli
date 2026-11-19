# AGENTS.md — Test Structure Guide

Guidance for AI coding agents (and humans) on how the MAS CLI test suite
is organised and where new tests go. See `tests/README.md` for the user
facing overview and `.bob/plans/2026-11-15-tui-pilot-test-plan.md` for the
design rationale.

## The three test categories

Tests are split by **what they drive**:

| Category | Drives | Requires | Location |
|---|---|---|---|
| **integration** | the real `mas-cli` process end-to-end | mocked OCP cluster fixtures | `tests/integration/` |
| **unit** | business logic in the app, with the UI mocked away | nothing | `tests/unit/` |
| **pilot** | the Textual UI sitting in front of the app, via a live pilot | nothing (stubbed app) | `tests/pilot/` |

Within `unit/` and `pilot/` there is a second axis — **framework vs
command**:

- `tui/` — the generic TUI framework the command UIs are built on (shell,
  models, messages, generic screens)
- `update/` — update-command-specific logic and screens

```
tests/
├── scenarios/               # Shared named app states (see below)
│   └── update.py
├── unit/                    # Business logic, mocked — drives the app under the UI
│   ├── tui/                 #   framework: shell, models, generic screens
│   └── update/              #   update command: app logic + update-specific screens
├── pilot/                   # Live Textual pilot — drives the UI in front of the app
│   ├── conftest.py          #   auto-applies the `pilot` marker to every test here
│   ├── harness.py           #   ScreenPilotApp + click_button/wait_for helpers
│   ├── tui/                 #   framework screens
│   └── update/              #   update screens (confirm-upgrades, auto-run, connect, launch)
└── integration/             # End-to-end, needs the OCP test fixtures
```

A screen's tests therefore live in two trees with paired filenames (e.g.
`unit/update/test_update_confirm_upgrades_screen.py` and
`pilot/update/test_confirm_upgrades_screen.py`) — the logic assertions in
`unit/`, the UI-driving tests in `pilot/`.

## Where does a new test go?

1. **Logic only** (pure functions, params write-back, validation rules,
   no rendering/events): `tests/unit/<command-or-tui>/`, mock the widgets.
2. **Anything involving rendering, events, focus, or compose structure**:
   `tests/pilot/<command-or-tui>/`, drive the real screen with a pilot.
   Pilot tests catch the bug class mocks cannot — the first pilot test run
   found a Db2 license path pointing at a non-existent file being accepted
   because only the launch path ever opened it.
3. **Screen is generic** (works for any command, lives in
   `mas/cli/tui/screens/`): `tui/` subtree. **Screen reads
   command-specific app state** (e.g. imports from `mas/cli/update/`):
   `<command>/` subtree.
4. **Full command behaviour against mocked cluster fixtures**:
   `tests/integration/`.

## Scenario module (`tests/scenarios/`)

Named app states as plain data (params + detector attributes), returned as
**real app instances** (e.g. `UpdateApp` in `tuiMode`), not MagicMocks — so
derived helpers like `upgradeConfirmationsPending()` compute exactly as
production code does. Use them in both unit and pilot tests:

```python
from scenarios.update import update_scenario

mas_app = update_scenario("db2-v11-to-v12")   # see UPDATE_SCENARIOS registry
```

When you need a new cluster/app state, add it to the registry rather than
building a one-off mock — the planned manual testing harness
(`dev.py --screen X --scenario Y`) will consume the same registry.

## Pilot test conventions

Use the helpers in `tests/pilot/harness.py`; they encode three Textual
gotchas that cost real debugging time:

- **`run_screen_pilot(screen, drive)`** mounts one screen in a bare app
  (with the production stylesheet), calls `start_dynamic_loaders()` as the
  shell does, and records posted workflow messages on `app.posted`. Assert
  on messages and written params — step *advancement* is the shell's job
  and is covered by the shell tests in `tests/unit/tui/`.
- **Widget assertions must run inside `drive`** — the DOM is torn down
  after `run_test()` exits; post-shutdown queries raise `NoMatches`.
- **Use `click_button(pilot, selector)`, not `pilot.click`**, for buttons:
  Textual's Button swallows a Click while its `-active` press-animation
  class is present, so back-to-back pilot clicks on the same button
  silently lose the second press. `click_button` waits out the animation.
- **Use `wait_for_widget(pilot, selector)`** when waiting for lazily
  mounted panels: plain `asyncio.sleep` does not drive Textual's refresh
  cycle — `pilot.pause()` does. (`wait_for(predicate)` is for worker-thread
  state that updates via `call_from_thread`.)
- Async pattern: `asyncio.run(...)` inside a sync test function — the repo
  does not use pytest-asyncio.

## Markers and CI

- The `pilot` marker is auto-applied by `tests/pilot/conftest.py` (never
  add it per-file); `tui` marks Textual-related tests in `unit/`.
- CI runs plain `pytest python/tests` — every category runs in the unit
  gate; there is no marker-based selection to opt into.
- `-m "not pilot"` gives a fast local loop without the live-UI tests.
- Docstrings follow GIVEN/WHEN/THEN; black and flake8 must pass (see
  pre-commit config).
