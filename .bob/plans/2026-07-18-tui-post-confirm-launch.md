# MAS CLI TUI — Launch Step & Pipeline Execution (update command)

## Objective

Close the architectural gap in the `update` TUI path: the pipeline is never
launched after the user confirms. Implement this as a proper workflow step — a
**launch screen** that auto-runs the pipeline submission, streams progress, and
reveals a "Done" button when finished. The user flow becomes:

```
connect-cluster  →  choose-catalog  →  dependency-checks  →  review  →  launch  →  Done (exit 0)
```

Review is no longer the terminal screen. It becomes a normal step whose Confirm
button advances to the launch step. The launch step is the last step; its Done
button exits the application.

The `upgrade` command is deliberately out of scope. Once `update` is complete and
working it will serve as the reference implementation for applying the same pattern
to `upgrade`.

----
## Context — What Is Wrong Today

### The pipeline is never launched from the TUI path

`__main__.py` for `update`:

```python
if "--catalog" not in argv …:
    serveTuiMode("update", argv[2:])
    return          # ← pipeline is NEVER launched
```

`TextualShell.on_workflow_confirmed` calls `self.exit(0)`. `serveTuiMode` returns.
`main()` returns. The pipeline is never submitted.

### The launch block is only reachable from the non-interactive path

Lines 186–249 of `update/app.py` — the Halo-wrapped RBAC, namespace prep, Tekton
install, and `launchUpdatePipeline` call — are only reached when `--catalog` is passed.
The TUI path has no route to them.

### The review screen is defined twice

| Path | Where |
|---|---|
| CLI | `update/app.py` lines 146–179 (`printH1`/`printH2`/`printSummary`) |
| TUI | `update/workflow.py` `buildUpdateReview()` |

Both must be kept in sync. Any change requires edits in two places.

----
## Design Decision — LaunchScreen as a Proper WorkflowStep

The launch step follows the exact same pattern as `AutoRunScreen`:

- Auto-starts work when `start_dynamic_loaders()` is called (i.e. when the step
  becomes active, after the user clicks Confirm on review)
- Streams progress entries to a `RichLog` (one line per stage)
- Reveals a **Done** button when the launch completes successfully, or a
  **Dismiss** button and error text on failure
- **Done** calls `self.app.exit(0)` directly — it does not post `StepCompleted`,
  because there is no next step

This requires:

1. A new `LaunchScreen` widget in `tui/screens/launch.py` — analogous to
   `AutoRunScreen` but calls `launchUpdate(progressCallback)` on the app instance
2. A `launchUpdate(progressCallback)` method on `UpdateApp` — pure work, no Halo,
   no `printH1`; reports each stage via `progressCallback(label, ok, detail)`
3. A **launch step** appended to `buildUpdateWorkflow`
4. `ReviewScreen` Confirm advances to the launch step by posting `StepCompleted`
   instead of `WorkflowConfirmed`, and `TextualShell` routes normally

`WorkflowDefinition` remains `List[WorkflowStep]` — **no type change needed**.

The cleanest approach: **`ReviewScreen` posts `StepCompleted` instead of
`WorkflowConfirmed`**. The launch step follows as the last step in the definition.
`WorkflowConfirmed` and the special `_activate_review` path in `TextualShell` are
removed entirely. The sidebar shows all steps including review and launch.

----
## Scope

**In scope:**
- New `LaunchScreen` widget (`tui/screens/launch.py`)
- `launchUpdate(progressCallback)` extracted from `update/app.py`
- `ReviewScreen` converted to a normal `WorkflowStep` (posts `StepCompleted`)
- `TextualShell` simplified: remove `_activate_review`, `WorkflowConfirmed` handler,
  hardcoded "Review Settings" sidebar entry, and `review_builder` plumbing
- `buildUpdateReview()` deleted from `update/workflow.py` (replaced by
  `WorkflowSummaryItem` entries on the review step)
- Review and launch steps added to `buildUpdateWorkflow`

**Out of scope:**
- `upgrade`, `install`, `backup`, `restore`, `uninstall`, `aiservice` — later phases
- Removal of `printH1`/`yesOrNo` from `app.py` CLI path — Phase 7
- MongoDB lexicographic version comparison bug — tracked separately

----
## Revised User Flow

```
Sidebar           Content
──────────────────────────────────────────────
✓ connect          [ Connect to OpenShift ]
✓ choose-catalog   [ Choose Target Catalog ]
✓ dep-checks       [ Dependency Update Checks ]  ← AutoRunScreen
→ review           [ Review Settings ]           ← ReviewScreen (now a step)
  launch           [ Launch Update ]             ← LaunchScreen (new)
──────────────────────────────────────────────
```

After the user clicks **Confirm** on the review step, the shell advances to the
launch step. `LaunchScreen.start_dynamic_loaders()` fires immediately, streams
progress, and reveals a **Done** button. Done calls `app.exit(0)`.

On **Reset** from the review step, the workflow resets to step 0 as today.

----
## Implementation Plan

### Step 1 — Tests first: workflow shape

File: `python/tests/unit/update/test_update_workflow.py`

Add failing tests (RED):

- `test_build_update_workflow_has_review_step` — step with `id="review"` is present
- `test_build_update_workflow_has_launch_step` — step with `id="launch"` is the last step
- `test_review_step_uses_review_screen_class` — `step.screen_class is ReviewScreen`
- `test_launch_step_uses_launch_screen_class` — `step.screen_class is LaunchScreen`
- `test_build_update_workflow_step_order` — ids in order:
  `["connect-cluster", "choose-catalog", "dependency-checks", "review", "launch"]`
- `test_review_step_has_summary_items` — `review` step `.summary` is non-empty and
  includes entries for catalog, db2, mongodb, kafka, cp4d, grafana, odh

Run: confirm RED (`review` and `launch` steps do not exist yet).

### Step 2 — Create LaunchScreen

File: `python/src/mas/cli/tui/screens/launch.py`

```python
class LaunchScreen(VerticalScroll):
    """Content panel that submits the Tekton pipeline and streams progress.

    Auto-starts when start_dynamic_loaders() is called. Calls
    launchUpdate(progressCallback) on the app instance. Appends one log row
    per stage. Reveals a Done button on success, or an error row and Dismiss
    button on failure. Done calls app.exit(0).
    """
```

Constructor signature: `(mas_app, step, step_index)`
— `step_index` received from `step.screen_kwargs["step_index"]` or positional arg.

Progress callback contract: `(label: str, ok: bool, detail: str) -> None` — same
as `AutoRunScreen`. Appended to `RichLog` as `✓ label: detail` or `✗ label: detail`.

Buttons:
- `btn-done` — hidden initially (`display: none`); `on_button_pressed` calls
  `self.app.exit(0)`
- `btn-dismiss-error` — hidden initially; shown on failure; calls `self.app.exit(1)`

`start_dynamic_loaders()`: calls `self.run_worker(self._run_launch, thread=True)`.

`_run_launch()`: calls `self._mas_app.launchUpdate(progressCallback)` in a worker
thread. On success: `call_from_thread(self._enable_done)`. On exception:
`call_from_thread(self._append_error, exc)` then `call_from_thread(self._enable_dismiss)`.

`reset()` method: clear log, re-hide both buttons (for workflow reset).

Export `LaunchScreen` from `tui/screens/__init__.py`.

Add unit tests in `python/tests/unit/tui/test_tui_launch_screen.py`:

- `test_launch_screen_is_importable` — `from mas.cli.tui.screens import LaunchScreen`
  does not raise
- `test_launch_screen_calls_launch_update_on_app` — construct a stub app with a
  `launchUpdate` method that records calls; instantiate `LaunchScreen`; call
  `_run_launch()` directly; assert `launchUpdate` was called with a callable
- `test_launch_screen_progress_callback_appends_to_log` — not testable without
  Textual; document as requiring a manual smoke test

### Step 3 — Extract launchUpdate(progressCallback) from update/app.py

File: `python/src/mas/cli/update/app.py`

Extract lines 186–249 into a new method:

```python
def launchUpdate(self, progressCallback=None) -> None:
    """Submit the Tekton update pipeline, reporting stages via progressCallback.

    Pure-work method with no printH1, yesOrNo, or printDescription calls.
    Called from the TUI LaunchScreen (with a progressCallback that streams
    each stage to the RichLog) and from the non-interactive update() path
    (with progressCallback=None, where Halo spinners are used directly —
    keeping existing CLI behaviour completely unchanged).

    Args:
        progressCallback (Callable, optional): Called as
            (label: str, ok: bool, detail: str) -> None after each stage.
            When None, Halo spinners are used instead.
    """
```

When `progressCallback is not None` each stage calls the devops function directly
and posts one callback entry. When `progressCallback is None` the existing
`with Halo(...) as h:` blocks run exactly as today.

Concrete stages and their callback labels:

| Label | Devops call |
|---|---|
| `"Validate OpenShift Pipelines"` | `installOpenShiftPipelines(...)` |
| `"Apply pre-install RBAC: {instanceId}"` | `applyPreInstallMASRBAC(...)` (once per instance) |
| `"Prepare pipelines namespace"` | `createNamespace(...)`, `preparePipelinesNamespace(...)`, `prepareUpdateSecrets(...)` |
| `"Install Tekton definitions"` | `updateTektonDefinitions(...)` |
| `"Submit PipelineRun"` | `launchUpdatePipeline(...)` |

Replace the inline block in `update()` with `self.launchUpdate()` (no callback —
CLI behaviour unchanged).

The `if not self.noConfirm: … yesOrNo(…)` block (lines 181–184) is **not touched**.
The `printH1`/`printH2`/`printSummary` review block (lines 139–179) is **not
touched**. Both stay for the CLI path until Phase 7.

Add tests in `python/tests/unit/update/test_update_launch.py` (new file):

- `test_launchUpdate_calls_install_openshift_pipelines` — mock all devops functions;
  confirm `installOpenShiftPipelines` is called
- `test_launchUpdate_calls_launch_update_pipeline` — confirm `launchUpdatePipeline`
  called with `params=self.params`
- `test_launchUpdate_applies_rbac_when_flag_set` — set `applyPreInstallMASRBAC=True`
  with one entry in `instancesNeedingRBAC`; confirm `applyPreInstallMASRBAC` called
- `test_launchUpdate_skips_rbac_when_flag_false` — confirm not called when flag False
- `test_launchUpdate_with_progress_callback_calls_callback` — pass a
  list-collecting callback; confirm at least one `(label, ok, detail)` tuple appended

### Step 4 — Convert ReviewScreen to a normal WorkflowStep panel

Today `ReviewScreen` posts `WorkflowConfirmed` on Confirm. It must instead post
`StepCompleted(self._step_index)` so `TextualShell._complete_step` advances to the
launch step.

File: `python/src/mas/cli/tui/screens/review.py`

```python
# Before
from mas.cli.tui.messages import WorkflowConfirmed, WorkflowReset
…
if event.button.id == "btn-confirm":
    self.post_message(WorkflowConfirmed())

# After
from mas.cli.tui.messages import StepCompleted, WorkflowReset
…
if event.button.id == "btn-confirm":
    self.post_message(StepCompleted(self._step_index))
```

`ReviewScreen.__init__` gains `step_index: int` parameter (alongside `mas_app` and
`definition`). The `WorkflowStep` for review supplies it via
`screen_kwargs={"step_index": 3}`.

`WorkflowReset` still posts as today — `TextualShell.on_workflow_reset` handles it.

### Step 5 — Simplify TextualShell

File: `python/src/mas/cli/tui/shell.py`

**Remove the following** (all become dead code once ReviewScreen posts StepCompleted):

- `_activate_review()`, `_mount_and_activate_review()`, `_show_review()` — review
  is now mounted like any other step by the existing `_activate_step` path
- `on_workflow_confirmed()` — no longer fired
- The hardcoded `"Review Settings"` `ListItem` appended in `_populate_sidebar`
- `review_builder` constructor parameter and `self._review_builder` attribute
- The `review_builder_name` lookup, `builder_fn` construction, and `review_builder=`
  kwarg in `serveTuiMode`

`_populate_content`, `_complete_step`, `_find_next_active_index`, and
`on_workflow_reset` are **unchanged**.

`ReviewScreen` is now instantiated by the existing `_make_panel` path via
`step.screen_class`. No special-casing required.

File: `python/src/mas/cli/tui/messages.py`

Remove the `WorkflowConfirmed` class — nothing posts or handles it after this step.

### Step 6 — Update buildUpdateWorkflow

File: `python/src/mas/cli/update/workflow.py`

Replace the current three-step definition with five steps:

```python
from mas.cli.tui.screens import ReviewScreen, LaunchScreen

reviewStep = WorkflowStep(
    id="review",
    heading="Review Settings",
    heading_level="h1",
    description=["Please carefully review your choices below."],
    screen_class=ReviewScreen,
    screen_kwargs={"step_index": 3},
    summary=[
        WorkflowSummaryItem(label="Installed Catalog",      attr="installedCatalogId"),
        WorkflowSummaryItem(label="Target Catalog Version", param="mas_catalog_version"),
        WorkflowSummaryItem(label="IBM Db2",                param="db2_namespace"),
        WorkflowSummaryItem(label="MongoDB Community",      param="mongodb_namespace"),
        WorkflowSummaryItem(label="Apache Kafka",           param="kafka_namespace"),
        WorkflowSummaryItem(label="IBM Cloud Pak for Data", param="cp4d_update"),
        WorkflowSummaryItem(label="Grafana v4 Operator",    param="grafana_v5_upgrade"),
        WorkflowSummaryItem(label="Open Data Hub (ODH)",    param="odh_to_rhoai_migration"),
    ],
)

launchStep = WorkflowStep(
    id="launch",
    heading="Launch Update",
    heading_level="h1",
    description=["Submitting the Tekton pipeline for MAS update."],
    screen_class=LaunchScreen,
    screen_kwargs={"step_index": 4},
)

return [connectStep, chooseCatalogStep, dependencyChecksStep, reviewStep, launchStep]
```

Delete `buildUpdateReview()` entirely.

### Step 7 — Validate and lint

```bash
wsl bash -lc "cd /mnt/c/Users/097891866/Documents/GitHub/ibm-mas/cli && black . && flake8 python/ 2>&1 | tail -20"
wsl bash -lc "cd /mnt/c/Users/097891866/Documents/GitHub/ibm-mas/cli && .venv/bin/pytest python/tests/unit/ -v 2>&1 | tail -40"
```

All tests green. No new flake8 warnings.

Manual smoke test (requires cluster):
```bash
mas-cli update          # TUI: review → launch → pipeline submitted → Done exits 0
mas-cli update -c v9-… # CLI: unchanged — launchUpdate() called with no callback
```

----
## File Change Summary

| File | Change |
|---|---|
| `tui/screens/launch.py` | **New** — `LaunchScreen` auto-run panel |
| `tui/screens/__init__.py` | Export `LaunchScreen` |
| `tui/screens/review.py` | Post `StepCompleted` instead of `WorkflowConfirmed`; accept `step_index` |
| `tui/messages.py` | Remove `WorkflowConfirmed` class |
| `tui/shell.py` | Remove `_activate_review`, `on_workflow_confirmed`, hardcoded review sidebar entry, `review_builder` plumbing |
| `update/workflow.py` | Add `review` + `launch` steps; delete `buildUpdateReview()` |
| `update/app.py` | Extract `launchUpdate(progressCallback=None)`; replace inline block with `self.launchUpdate()` |
| `tests/unit/tui/test_tui_launch_screen.py` | **New** — `LaunchScreen` importability and wiring tests |
| `tests/unit/update/test_update_workflow.py` | Update step-id assertions; add review/launch step tests |
| `tests/unit/update/test_update_launch.py` | **New** — `launchUpdate` unit tests |

**Files not touched:** `__main__.py`, `common/workflow.py`, `upgrade/`, all mixin
files, all dependency-detection tests, `test_update_detect_result.py`.

----
## Key Invariants

- `WorkflowDefinition` remains `List[WorkflowStep]` — no type change.
- `WorkflowConfirmed` is removed entirely; `ReviewScreen` posts `StepCompleted`.
- `LaunchScreen.Done` calls `app.exit(0)` directly — no `StepCompleted` posted
  (there is no next step after launch).
- The `upgrade` command is **completely unaffected** by this change — its workflow
  still ends at `instance-selection` and still exits via `WorkflowConfirmed` until
  the upgrade reference implementation is tackled separately.

  > **Wait** — removing `WorkflowConfirmed` from `messages.py` and
  > `on_workflow_confirmed` from `shell.py` **will** break `upgrade` if its
  > `ReviewScreen` still posts `WorkflowConfirmed`. Since `upgrade` does not yet
  > have a review step (its workflow ends at `instance-selection` followed directly
  > by the existing `ReviewScreen` special path), **verify** whether `upgrade`'s
  > `ReviewScreen` is reachable before deleting `WorkflowConfirmed`. If it is,
  > retain the message class and handler as a no-op stub until the upgrade
  > reference implementation is done, then delete them together.

- The CLI path (`--catalog`) is **completely unchanged**: `app.update()` calls
  `self.launchUpdate()` with no callback; all Halo spinners and terminal output
  work exactly as before.
- At the end of every step, `pytest python/tests/unit/` must be fully green.

----
## Known Issues to Track (not in scope here)

- **MongoDB version comparison is lexicographic, not semver.**
  `detectMongoDb` uses plain string `<` comparison. `"7.0.14" < "7.0.8"` evaluates
  as `True`, incorrectly flagging a patch upgrade as a downgrade. Fix: use
  `packaging.version` or integer-tuple comparison. Documented in
  `test_update_detect_dependencies_mongo.py` test docstring.
