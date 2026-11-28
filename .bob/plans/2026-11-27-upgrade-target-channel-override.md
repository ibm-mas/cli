# Upgrade target-channel override: re-run the current release's upgrade

(Save this plan to `.bob/plans/2026-11-27-upgrade-target-channel-override.md` as the first implementation step, per repo convention.)

## Context

A `mas upgrade` from 9.0.x → 9.1.x failed after MAS core had already reached 9.1.x, but before the rest of the upgrade completed (including the required Manage Foundation install — the instance had **only core installed, no app subscriptions**). Re-running `mas upgrade` then derived the target as core+1 (9.2.x), because the target derivation ([`upgrade/app.py:991-1020`](python/src/mas/cli/upgrade/app.py#L991-L1020)) only looks at core + app **subscription channels** — with no apps installed, `allChannels = ["9.1.x"]` → target 9.2.x.

The `--next-channel` flag already exists as an override, but it hits the same blind spot: the "No action required" early-exit at [`upgrade/app.py:1026-1033`](python/src/mas/cli/upgrade/app.py#L1026-L1033) fires for an explicit target equal to the current channel when all app subscriptions are on it (`all()` over an empty app list is vacuously true), so `mas upgrade --next-channel 9.1.x` on this cluster exits with "already fully upgraded" instead of re-running the 9.1 upgrade.

**Decision (from user):** make the explicit target a *complete override of all logic*. If the user is on 9.1 and chooses 9.1, it must behave exactly as if they were on 9.0 auto-detecting an upgrade to 9.1 — launch the 9.1 upgrade pipeline, trigger the Manage Foundation flow, etc. The upgrade pipeline (like install) is idempotent, so even re-running a fully-successful 9.1 instance to 9.1 simply results in no action at the pipeline level. The auto-derived path stays as-is. The TUI also needs a way to choose the explicit target (today the TUI has no target-channel input at all).

## Semantics of an explicit target (both `--next-channel` and the new TUI choice)

- The explicit target is used as the upgrade target, unconditionally — **no "No action required" early-exit, ever** (pipeline idempotency handles the no-op case).
- Validation retained: the target must be either the current core channel (retry/re-run) or `upgrade_path[currentChannel]` (next hop); anything else is a fatal "No upgrade path available from X to Y". App compatibility-matrix validation against the target still runs.
- When the target is 9.1.x and Manage is not installed, the existing Manage Foundation flow ([`upgrade/app.py:1091`](python/src/mas/cli/upgrade/app.py#L1091) classic / [`upgrade/app.py:251`](python/src/mas/cli/upgrade/app.py#L251) TUI) triggers — this is what completes the failed upgrade.

## Changes

### 1. `python/src/mas/cli/upgrade/app.py` — classic path (`upgrade()`)

- Delete the early-exit block at lines 1026-1033 (`if self.nextChannel == currentChannel and all(app["channel"] == ...)` → "No action required … return"). Analysis: in the auto-derived branch this condition can never be true (auto `nextChannel == currentChannel` only happens when apps are behind, which makes `all()` false), so the block only ever fires for explicit targets — exactly the case that must now proceed. Update the comments at 1022-1025 accordingly.
- The explicit-path validation at 976-990 (retry message for target == current, path check otherwise) is unchanged.

### 2. `python/src/mas/cli/upgrade/app.py` — TUI path (`prepareUpgrade()`)

- Read an explicit target from a new param `upgrade_target_channel` (written by the new target-selection step's select field): when present and non-empty, treat it as the explicit target — validate (current channel or next hop, else `RuntimeError`), set `self.nextChannel` to it, and **never** raise "No action required". When absent, auto-derive exactly as today and store the derived value on `self.autoNextChannel` (new attribute, initialised in `__init__`).
- Delete the explicit-branch early-exit at lines 172-173 (`if self.nextChannel == currentChannel and all(...)` → raise "No action required"). Keep the auto-branch "already fully upgraded / latest release" raises at 186-192 (an instance on the latest release with everything on it still has nothing to offer).
- Add a small wrapper used as the instance-selection validator so a stale choice is cleared when the user goes back and re-selects an instance:
  ```python
  def prepareUpgradeForInstanceSelection(self) -> None:
      self.setParam("upgrade_target_channel", "")
      self.prepareUpgrade()
  ```
- Add the options helper for the new step:
  ```python
  def targetChannelOptions(self) -> list:
      """Valid targets for the target-selection step: the auto-derived next
      hop and the current channel (idempotent re-run), deduplicated."""
  ```
  (built from `self.autoNextChannel` + `self.currentChannel`; empty list when the channel is unknown).
- Update the `prepareUpgrade` docstring (explicit-target semantics) and the `resolveMasChannelParam` docstring's retry bullet (now first-class, not an accident).

### 3. `python/src/mas/cli/upgrade/workflow.py` — new target-channel step

Insert a step between instance-selection and license-acceptance:

```python
targetChannelStep = WorkflowStep(
    id="target-channel",
    heading="Select Target Channel",
    description=[...current channel, what the auto-detected target is, and a note
                  that re-running the current channel's upgrade is safe — the
                  pipeline is idempotent and completes any unfinished components...],
    fields=[WorkflowField(
        id="upgrade_target_channel",
        label="Target MAS Channel",
        type="select",
        required=True,
        options=lambda: appInstance.targetChannelOptions(),
        default=lambda: appInstance.autoNextChannel,
    )],
    validator=appInstance.prepareUpgrade,   # re-runs with the chosen target
    validator_status="Validating target channel…",
    condition=lambda p: appInstance.currentChannel not in (None, "", "Unknown"),
)
```

- Point the instance-selection step's `validator=` at `prepareUpgradeForInstanceSelection`.
- `WorkflowField` already supports callable `options` and `default` (see [`tui/models.py:38-64`](python/src/mas/cli/tui/models.py#L38-L64)); verify the default is applied for plain `select` fields in `StepScreen` and adjust if it's dynamic-select-only.
- The license/manage-foundation step conditions already re-evaluate off `nextChannel`, so choosing a 9.1.x target correctly surfaces the license and Manage Foundation steps.
- Update the module docstring (now 7 steps) and `buildUpgradeWorkflow`'s step list.

### 4. Generated non-interactive command — no change needed

`upgradeArgBuilderMixin` already emits `--next-channel <nextChannel>` whenever it is a known channel ([`argBuilder.py:56`](python/src/mas/cli/upgrade/argBuilder.py#L56)), so a TUI override automatically round-trips into the equivalent command.

## Tests

Follow `python/AGENTS.md` placement rules (logic → `unit/`, full command vs mocked cluster → `integration/`).

- `python/tests/unit/upgrade/test_upgrade_app.py` (uses the existing `_patch_cluster` helper, which already has a `verifyAppInstance` knob):
  - Explicit retry via `params["upgrade_target_channel"] = "9.1.x"` on core 9.1.x, **no apps**, `verifyAppInstance=False` → no raise, `nextChannel == "9.1.x"`, `isManageFoundation is True`, `params["mas_channel"] == "9.1.x"`, `params["should_install_manage_foundation"]` handled by the manage-foundation step.
  - Same cluster state, no override (auto) → `nextChannel == "9.2.x"` (documents current behaviour).
  - Explicit target equal to current on a fully-upgraded instance (core + all apps on 9.2.x, override 9.2.x) → proceeds, does **not** raise "No action required".
  - Invalid explicit target (core 9.1.x, override 9.3.x-feature) → `RuntimeError` "No upgrade path available".
  - `targetChannelOptions()` returns the deduped auto + current list; empty for unknown channel.
  - `prepareUpgradeForInstanceSelection` clears a stale `upgrade_target_channel`.
- `python/tests/unit/upgrade/test_upgrade_workflow.py`: the new step is wired between instance-selection and license-acceptance, with the right field/condition/validator (instance-selection validator is now the wrapper).
- `python/tests/integration/upgrade/test_upgrade_channel.py`: parameterise `verifyAppInstance` in `_run_upgrade` (currently hardcoded `True`), then add:
  - `mas upgrade --next-channel 9.1.x` with core 9.1.x, no apps, Manage missing → PipelineRun launched with `mas_channel == "9.1.x"` and `should_install_manage_foundation == "true"` (the user's exact scenario, end-to-end).
  - `--next-channel` equal to current on a fully-upgraded instance → launches (no early "No action required" return).

## Verification

Run in WSL against the repo venv (per environment memory):

```
wsl bash -lc "cd /mnt/c/Users/097891866/Documents/GitHub/ibm-mas/cli/python && .venv/bin/pytest tests/unit/upgrade tests/integration/upgrade -q"
```

Also run black/flake8 on the touched files (pre-commit runs them on commit). Manual smoke (optional): `mas upgrade --mas-instance-id <id> --next-channel 9.1.x --no-confirm --accept-license` against a dev cluster in the failed-upgrade state and confirm the PipelineRun carries `mas_channel=9.1.x` with the Manage Foundation tasks.
