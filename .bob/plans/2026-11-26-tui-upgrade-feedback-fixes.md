# TUI upgrade feedback: colour consistency, license confirmation, shared storage class selection

## Context

Feedback on the new interactive `mas upgrade` Textual flow (branch `manualsubs`), three items — the third expanded per review into a **shared** storage-class selection implementation used by both install and upgrade, so the upcoming install TUI doesn't re-implement it:

1. **Colours differ between container and local runs.** Root cause found: [theme.py](python/src/mas/cli/tui/theme.py) sets *explicit* Carbon hex colours via a registered Textual `Theme` — not hints. Textual renders internally at truecolour, but the output console (rich) downsamples ANSI to the terminal's **detected** colour system (`textual.constants.COLOR_SYSTEM`, default `auto`, detected from `TERM`/`COLORTERM`). In a container session (`oc rsh` / `docker exec -it`) `COLORTERM` is dropped and `TERM` is often plain `xterm`, so detection drops to 256-colour and quantizes the palette to the xterm cube. The escape sequences pass through the pty untouched, so the *outer* terminal's capability is what matters and we can force truecolour safely.

2. **The license-acceptance step has a redundant checkbox.** [license_acceptance.py](python/src/mas/cli/tui/screens/license_acceptance.py) blocks "Confirm & Continue" until an "I accept…" checkbox is checked. Clicking the button is itself the confirmation.

3. **Storage class selection must be implemented once, shared.** Today `InstallApp.configStorageClasses` ([install/app.py:1427](python/src/mas/cli/install/app.py#L1427)) and `UpgradeApp.configStorageClasses` ([upgrade/app.py:697](python/src/mas/cli/upgrade/app.py#L697)) are near-duplicate prompt flows (provider detection → yesOrNo override → list classes → prompt RWO/RWX with `StorageClassValidator`), and the upgrade TUI's manage-foundation step collects them as free-text `Input`s. Build one shared selection implementation covering TUI and non-TUI, consumed by upgrade now and install's future TUI later.

On execution, first save a copy of this plan to `.bob/plans/2026-11-26-tui-upgrade-feedback-fixes.md` per repo convention.

---

## Part 1 — Force truecolour for the TUI

Textual reads `TEXTUAL_COLOR_SYSTEM` from the environment at import of `textual.constants` (verified: textual 8.2.8, `constants.py:149`), and `App.__init__` reads the module attribute at construction time — so both an env var and a module-attribute patch are effective.

**Changes** (helper in [theme.py](python/src/mas/cli/tui/theme.py), called from [shell.py](python/src/mas/cli/tui/shell.py)):

- Add `forceColorConsistency()` to `theme.py`:
  - `os.environ.setdefault("TEXTUAL_COLOR_SYSTEM", "truecolor")`
  - If `textual.constants.COLOR_SYSTEM` is still `"auto"` (textual was imported before the env var was set — the normal case, since `shell.py` imports textual at module top), patch the module attribute to `"truecolor"`.
  - User escape hatch honoured both ways: an explicit `TEXTUAL_COLOR_SYSTEM=256` (or `NO_COLOR`) set by the user is never overridden.
- Call it at the top of `serveTuiMode()` **before** the lazy workflow-module imports, and in `TextualShell.__init__` before `super().__init__()` (covers `dev.py` and direct construction). Extend `theme.py`'s docstring/rollback note.

**Tests** — extend [test_tui_theme.py](python/tests/unit/tui/test_tui_theme.py): env unset → sets env var + patches `textual.constants.COLOR_SYSTEM` to `"truecolor"` (save/restore module attr and env in the test); env preset to `"256"` → respected, no patch; `COLOR_SYSTEM` already non-auto → not overwritten.

## Part 2 — Remove the license-acceptance checkbox

**Changes** in [license_acceptance.py](python/src/mas/cli/tui/screens/license_acceptance.py):
- Remove the `Checkbox` widget from `compose()`, the `on_checkbox_changed` handler, and the checkbox gate in `on_button_pressed` — clicking "Confirm & Continue" directly sets `self._mas_app.licenseAccepted = True` and posts `StepCompleted`.
- Adjust the license-acceptance step description in [upgrade/workflow.py](python/src/mas/cli/upgrade/workflow.py) to state that selecting Confirm & Continue constitutes acceptance. Update both files' docstrings.

**Tests** — update [test_license_acceptance_screen.py](python/tests/pilot/upgrade/test_license_acceptance_screen.py):
- Drop checkbox assertions from `test_license_screen_shows_target_channel_terms`.
- Replace the blocked/checked pair with one test: clicking Confirm & Continue records `licenseAccepted = True` and posts `("step_completed", 2)`, with no inline error.

## Part 3 — Shared storage class selection (install + upgrade, TUI + non-TUI)

### 3a. Framework: real `dynamic_select` support in `StepScreen`

`WorkflowField.options_loader` is **documented** to run in a worker thread ([models.py:50-51](python/src/mas/cli/tui/models.py#L50-L51)) but never implemented — `dynamic_select` currently renders identically to `select` with synchronous options. A cluster API call can't run in `compose()` on the UI thread, so implement it:

**Changes** in [step.py](python/src/mas/cli/tui/screens/step.py):
- `start_dynamic_loaders()` (currently a no-op): for each field with `options_loader`, run the loader in a worker thread (`self.run_worker(..., thread=True)`, same pattern as `_run_validator`), passing `self._mas_app.params` (the documented contract). On completion, via `call_from_thread`:
  - set the `Select`'s options to `[(opt, opt) for opt in result]`;
  - apply the field's `default` — allow `default` to be a **callable** (evaluated at load-completion, reading state the loader cached on the app); if the value is in the options, set it as the Select value;
  - refresh the step's `context` rows (re-resolve each `WorkflowSummaryItem` against the app and update the `.context-value` labels) so rows populated by the load appear.
- While a dynamic load is in flight: disable the Next button and show "Looking up storage classes…" via `ActionBar.set_status`; re-enable on completion, clear on success / `set_error` on loader failure (mirrors the connect screen's busy pattern).
- `Select` stays `allow_blank=True` — blank keeps its "auto-detect" meaning where the step allows it.
- Update [models.py](python/src/mas/cli/tui/models.py) `WorkflowField` docstrings: `options_loader` behaviour now real; `default` may be a zero-arg callable.

### 3b. Shared app logic: `StorageClassMixin`

**New module** `python/src/mas/cli/common/storageClasses.py` — follows the existing shared-mixin precedent ([common/olmApprovals.py](python/src/mas/cli/common/olmApprovals.py), `OlmApprovalDetectionMixin`), no Textual dependency:

- `lookupStorageClasses()` — memoized (one TUI session = one cluster): sorted storage class names via `getStorageClasses(self.dynamicClient)`, plus `getDefaultStorageClasses(self.dynamicClient)` provider detection cached on the app (`self.detectedStorageClasses`, `self.detectedStorageProviderName`, `self.storageClassProvider`). This single lookup feeds the TUI dropdowns, the non-TUI prompt flows, and the review summary.
- `promptForStorageClasses(allowRwxNone=False)` — the shared non-TUI prompt pair: print the class list, prompt RWO/RWX with `StorageClassValidator` ([validators.py](python/src/mas/cli/validators.py)), optionally note that `"none"` is valid for RWX.
- `configStorageClasses(...)` — shared orchestration with small knobs for the two commands' policy differences:
  1. validate any params already set (CLI flags / TUI dropdown selections) against the cluster;
  2. provider detection + display (non-TUI), accept detected (interactive `yesOrNo`; auto-accept under `noConfirm`);
  3. fall back to prompt (non-TUI) / `fatalError` naming the step's inputs (TUI, as upgrade does today);
  - `cliArgsWin: bool` — upgrade passes `True` (CLI flags take precedence over detection, current upgrade behaviour); install passes `False` (detection is offered as the default and the user confirms/overrides, current install behaviour).
  - `allowRwxNone: bool` — install `True`, upgrade `False`.

**Command integration** (thin wrappers, behaviour-preserving):
- [UpgradeApp](python/src/mas/cli/upgrade/app.py) adds `StorageClassMixin` to its bases; its `configStorageClasses` is replaced by the mixin's (with upgrade's knobs and TUI error message). `prepareManageFoundation` (the step validator) is unchanged — it already calls `self.configStorageClasses()`.
- [InstallApp](python/src/mas/cli/install/app.py) adds `StorageClassMixin`; its `configStorageClasses` reduces to the shared call with `allowRwxNone=True, cliArgsWin=False` plus its command-specific tail (pipeline PVC class derivation from the chosen RWO/RWX, [install/app.py:1476-1483](python/src/mas/cli/install/app.py#L1476-L1483)). Install's existing H1/description text and `storageClassProvider` bookkeeping move into the shared method (parameterized where the texts differ).
- The facilities-specific storage prompts ([install/app.py:1664+](python/src/mas/cli/install/app.py#L1664)) are **not** touched — different params, out of scope.

### 3c. Shared TUI step builder: `storageClassStep()`

**Add to** [common/workflow.py](python/src/mas/cli/common/workflow.py), beside `connectClusterStep`:

```python
def storageClassStep(appInstance, *, id, heading, description,
                     validator=None, condition=None,
                     required=False, allowRwxNone=False) -> WorkflowStep
```

- Fields: `storage_class_rwo` and `storage_class_rwx` as `dynamic_select` — `options_loader=lambda params: appInstance.lookupStorageClasses()`, `default=lambda: <detected rwo/rwx from appInstance.detectedStorageClasses>` (so the detected provider's classes are pre-selected), `required` per the knob, `"none"` appended to the RWX options when `allowRwxNone`.
- Context row: `WorkflowSummaryItem(label="Detected storage provider", attr="detectedStorageProviderName")` — "—" at compose, filled by the post-load context refresh.
- **Upgrade's manage-foundation step** ([upgrade/workflow.py](python/src/mas/cli/upgrade/workflow.py)) becomes a call to this builder with its heading/description/validator (`prepareManageFoundation`)/condition (`manageFoundationPending`), `required=False` (blank = auto-detect at validation), `allowRwxNone=False`; its description is updated for dropdown semantics.
- The future install TUI reuses the same builder with `required=True, allowRwxNone=True` — no second implementation.

### 3d. Tests

- **Pilot, framework** — extend [tests/pilot/tui/test_step_screen.py](python/tests/pilot/tui/test_step_screen.py): `options_loader` runs and populates the Select (harness already calls `start_dynamic_loaders()` after mount); callable `default` pre-selects; failing loader shows the inline error and re-enables Next; context row refreshes post-load.
- **Pilot, upgrade** — update [test_manage_foundation_screen.py](python/tests/pilot/upgrade/test_manage_foundation_screen.py): fields are now `Select`s; patch `mas.cli.common.storageClasses.getStorageClasses` / `getDefaultStorageClasses` (existing patch pattern in [test_upgrade_app.py:387,432](python/tests/unit/upgrade/test_upgrade_app.py#L387)) so the real lookup runs against a fake OCS-style cluster; assert dropdown populated, provider defaults pre-selected, provider name in the context row; blank-select path still advances to the validator.
- **Unit, mixin** — new `tests/unit/common/test_storage_class_mixin.py` (new dir with `__init__.py`, following the per-area convention in [AGENTS.md](python/AGENTS.md)): lookup caching, provider attrs, param validation failure, `cliArgsWin` both ways, `allowRwxNone`, noConfirm/tuiMode error paths.
- **Unit, upgrade** — [test_upgrade_app.py](python/tests/unit/upgrade/test_upgrade_app.py): existing `prepareManageFoundation` tests keep passing against the mixin-backed `configStorageClasses` (they patch `getDefaultStorageClasses` at the upgrade-app import site — retarget the patch to the new common module).

---

## Verification

- Targeted: `wsl bash -lc "cd /mnt/c/Users/097891866/Documents/GitHub/ibm-mas/cli/python && pytest tests/pilot/tui tests/pilot/upgrade tests/unit/tui tests/unit/upgrade tests/unit/common tests/unit/install -q"` (WSL `.venv`).
- Full gate (integration tests with mocked OCP fixtures run here too — they cover install's non-TUI `configStorageClasses` paths via `--storage-class-rwo/rwx` flags and will catch behaviour drift from the mixin refactor): `pytest tests` from `python/`, as CI runs it.
- `black` / `flake8` on touched files.
- Colour fix: unit tests prove the forcing and the escape hatch; optionally run `mas upgrade` in the container image with `TERM=xterm` (previously downsampling) — colours should match a local run, and `TEXTUAL_COLOR_SYSTEM=256 mas upgrade` should reproduce the old dull palette.
- No changes to non-TUI code paths outside the storage-class mixin refactor: `serveTuiMode` colour forcing only touches the env when the TUI launches.

## Out of scope (noted, not done)

- The **pipeline** storage class on upgrade (`configPipelineStorageClass`) stays auto-resolved from the existing config-pvc / provider detection; no selection UI today. A dropdown for the "no config-pvc found" case is a follow-up (it could reuse `storageClassStep`'s lookup).
- The update command's `ConfirmUpgradesScreen` checkboxes are untouched — those confirm *breaking changes* (Mongo/Db2 major upgrades), a different intent from license acceptance.
- Install TUI workflow itself — the shared pieces land now; wiring them into an install workflow is the upcoming task.

## Implementation notes (deviations from the plan above)

- **`Select.BLANK` → `Select.NULL`** (latent bug fix, `tui/screens/step.py`): in textual 8.2.8 `Select.BLANK` is a deprecated alias literally equal to `False`, while the no-selection sentinel is `Select.NULL`. The old `Select.BLANK` usages meant an empty-options Select crashed at mount, blank required selects passed validation, and blank-value comparisons never matched. All three usages now use `Select.NULL`.
- **Blank optional select writes `""`** in `StepScreen._write_params` (previously a blank select left any previously-written param untouched) — this is what gives blank dropdowns the "auto-detect" meaning.
- **`promptForStorageClasses(onlyMissing=...)`**: added a flag so the upgrade flavour preserves the old behaviour of prompting only for a *missing* class when partial CLI args were given; the install override path prompts for both, as before.
- **Install gains early validation** of provided storage classes (previously install only validated prompted values) — a strictly-better change caught by the same `StorageClassValidator` semantics, with `"none"` exempt via `allowRwxNone`.
- **`tests/unit/common/` already existed** (command builder, OLM approvals, progress tests) — the mixin tests slot in beside them rather than creating the directory.
- The dynamic-load status row text is generic ("Looking up available options…") since `StepScreen` is command-agnostic; the storage-specific signal is the "Detected storage provider" context row.
- **Colour-system guard**: `forceColorConsistency` patches `textual.constants.COLOR_SYSTEM` only when it is still `"auto"` *and* the effective env value is the truecolour default — a user-set `TEXTUAL_COLOR_SYSTEM=256` survives even when textual was imported before the env var was set (a test caught the first draft overriding it).
- **Colour fix reworked after review** (final approach): the app-side forcing was removed entirely. The container image's Dockerfile now sets `ENV TEXTUAL_COLOR_SYSTEM=truecolor` (alongside the existing `MAS_CLIPBOARD` env, with the same override note) — setting the environment up correctly rather than forcing from the app. Local runs keep pure terminal detection, textual reads the env var cleanly at import (no module-attribute patch needed), and `docker run -e`/`oc set env` provides the override. The `forceColorConsistency` helper, its two call sites in `shell.py`, and its three unit tests are gone; `theme.py`'s docstring points at the Dockerfile.
