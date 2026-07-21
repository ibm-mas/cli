# MAS CLI Architecture Redesign — Textual TUI Shell

## Objective
Replace the MAS CLI interactive layer with a full-screen Textual TUI shell, delivered one command at a time so that each migrated command can be shipped independently without blocking untouched commands. Commands not yet migrated continue to work exactly as today throughout the entire delivery.

----
## Design Decisions

### Phased delivery model — vertical slices per command

```
Phase 1 — Foundation (one-time)
  tui/models.py, tui/shell.py, tui/__init__.py
  pyproject.toml gets [tui] extra
  No changes to any app.py or __main__.py

Phase 2 — Complete TUI shell (field widgets, review, async actions)
  Shell is fully functional; still no command dispatch wired

Phase 3 — update command (first slice)
  update/workflow.py, update/app.py stripped, __main__.py dispatch
  All other commands unchanged

Phase 4 — upgrade command
Phase 5 — install command (most complex)
Phase 6 — remaining commands (backup, restore, uninstall, aiservice)

Phase 7 — cleanup
  Delete workflow/ empty dir, displayMixins.py, prompt_toolkit hard dep
  CliRenderer is already gone; web/ is already gone
```

**Key invariant**: at the end of every phase, `pytest` passes, `black`/`flake8` pass, and every CLI command works correctly. A command is either fully on the old path or fully on the new path — no partial states.

### Co-existence during migration

While migration is in progress each command's `app.py` continues to use `printH1`/`promptFor*`/`Halo` until its dedicated phase. `__main__.py` gains one TUI dispatch block per command as each is migrated. `displayMixins.py` and the empty `workflow/` directory are not removed until Phase 7 after all commands are done.

### The migration pattern — separating input collection from logic

Many existing methods mix two concerns in one function: **collecting user input** (via `prompt_toolkit`/`Halo`) and **executing logic** (cluster API calls, validation, decisions). The TUI needs the logic without the prompts; the old interactive CLI needs both together until the command is fully migrated.

The strategy depends on whether a method is shared across commands or local to one command:

**Shared methods on `BaseApp` (e.g. `connect()`):**
Extend the existing method to accept an optional set of pre-supplied values. When values are supplied (TUI path), skip prompting and use them directly. When values are absent (old interactive CLI path), prompt as today. This preserves the old interactive path for commands not yet migrated while enabling the TUI path for migrated commands.

```python
# cli.py — extended connect() supports both paths
def connect(self, server_url: str = "", login_token: str = "", skip_tls_verify: bool = False) -> None:
    self.reloadDynamicClient()
    if self._dynClient is not None and not server_url:
        # Already connected — old interactive: ask user; TUI: silently proceed
        if not self.noConfirm:
            if not self.yesOrNo("Proceed with this cluster"):
                server_url = prompt(...)   # old interactive path only
        ...
    elif server_url:
        # Values supplied by TUI field widgets — connect directly, no prompts
        connect(server_url, login_token, skip_tls_verify)
        ...
    else:
        # No existing connection, no supplied values — prompt (old interactive path)
        server_url = prompt(...)
        ...
    self.lookupTargetArchitecture()
```

The `connect-cluster` step action in `common/workflow.py` passes values collected by the TUI widgets as arguments: `action=lambda: app.connect(server_url=app._tuiInputs["server_url"], ...)`. In Phase 7, once every command is migrated, the old prompting branches are removed.

**Note:** `_tuiInputs` is a transient dict on the app instance populated by the TUI shell's `_write_params()` step completion handler for non-Tekton fields (cluster connection details). It is distinct from `self.params` which holds only Tekton pipeline parameters.

**Single-command methods (e.g. `configDb2()` in `install/settings/db2Settings.py`):**
Same approach — the method gains optional parameters for the values the TUI would collect. When called with values (TUI path), skip prompts. When called without (old interactive path), prompt as today. After Phase 7, the prompting branches are deleted.

### What "migrating a command" means

A command is fully migrated when:
* `{command}/workflow.py` exists with `build{Command}Workflow(app)` returning a complete `WorkflowDefinition`
* All shared methods used by the command (e.g. `connect()`) have been extended to accept pre-supplied values
* `__main__.py` dispatches the interactive path to `serveTuiMode()`
* Non-interactive path (`--catalog`, `--instance-id`, etc.) is **untouched**
* Old interactive paths in `app.py` still work — `printH1`/`promptFor*`/`Halo` calls are not removed until Phase 7
* All tests pass

### Target directory structure (end state)

```
python/src/mas/cli/
├── tui/
│   ├── __init__.py
│   ├── shell.py          # TextualShell(App) + serveTuiMode()
│   └── models.py         # WorkflowStep, WorkflowField, WorkflowDefinition
├── common/
│   └── workflow.py       # Shared connectClusterStep() reused by all commands
├── install/
│   ├── workflow.py       # buildInstallWorkflow(app) — pure data
│   ├── app.py            # Old interactive path intact until Phase 7
│   └── ...
├── update/
│   ├── workflow.py       # buildUpdateWorkflow(app) — pure data
│   ├── app.py            # Old interactive path intact until Phase 7
│   └── ...
├── upgrade/
│   ├── workflow.py       # buildUpgradeWorkflow(app)
│   ├── app.py
│   └── ...
├── backup/ restore/ uninstall/ aiservice/
│   └── workflow.py       # one per command
├── cli.py                # BaseApp — shared methods extended, not replaced; displayMixins removed Phase 7
├── displayMixins.py      # DELETED in Phase 7 only
└── workflow/             # DELETED in Phase 7 (empty dir, clean up last)
```

### tui/models.py — the type system

Written fresh (no prior `workflow/types.py` to copy from). Defines the complete type system for the TUI workflow layer.

```python
FieldType = Literal[
    "string", "password", "int", "bool",
    "select",           # static options list
    "multi_select",     # checkbox group (e.g. Manage components)
    "dynamic_select",   # options fetched from cluster at step-mount time
    "file", "dir"
]

@dataclass
class WorkflowField:
    id: str
    label: str
    type: FieldType
    options: Optional[List[str]] = None
    options_loader: Optional[Callable] = None    # for dynamic_select
    default: Optional[str] = None
    validator: Optional[str] = None
    sensitive: bool = False
    required: bool = True

@dataclass
class WorkflowSummaryItem:
    label: str
    param: str
    sensitive: bool = False

@dataclass
class WorkflowStep:
    id: str
    heading: str
    heading_level: str = "h1"
    description: List[str] = field(default_factory=list)
    fields: List[WorkflowField] = field(default_factory=list)
    summary: List[WorkflowSummaryItem] = field(default_factory=list)
    action: Optional[Callable] = None
    condition: Optional[Callable[[dict], bool]] = None

WorkflowDefinition = List[WorkflowStep]
```

`condition(params: dict) -> bool` — the TUI shell passes current `params` at evaluation time so any step can inspect prior selections. All `condition` lambdas use `lambda p: ...` signature throughout.

### Static step graph with condition(params) — the install model

All steps declared upfront; conditions evaluated dynamically. The TUI sidebar shows all steps. Steps whose `condition(params)` is `False` are rendered greyed-out and automatically skipped. After each step completes, all subsequent step conditions are re-evaluated with the updated params.

```python
WorkflowStep(
    id="configure-kafka",
    heading="Configure Kafka",
    condition=lambda p: p.get("install_iot") == "true",
    action=app._configKafka,
)
```

### Two FieldTypes requiring special handling

* `multi_select` — checkbox group; write-back: `params[field.id] = ",".join(selected)`
* `dynamic_select` — `field.options` is `None` at definition time; `field.options_loader(params)` runs in a worker thread at step-mount; shows spinner while loading

### TUI shell layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  MAS CLI — Update                                         [ESC quit] │
├───────────────────────┬─────────────────────────────────────────────┤
│  STEPS                │  <heading>                                   │
│                       │  <description>                               │
│  ✓ connect-cluster    │                                              │
│  → choose-catalog     │  [field widgets]                             │
│    dependency-checks  │                                              │
│  ░ configure-kafka    │                   [  Next →  ]               │
│    review-settings    │  (greyed = condition currently False)        │
└───────────────────────┴─────────────────────────────────────────────┘
```

Sidebar legend: `✓` completed · `→` active · blank upcoming · `░` conditionally-skipped

### Async actions and dynamic_select loading

Both `step.action` and `field.options_loader` run via `run_worker(callable, thread=True)`. An `ActionOverlay(ModalScreen)` appears for step actions. A spinner within the field appears while `options_loader` resolves.

### TUI inputs vs Tekton params

The TUI shell writes field values to two different places depending on their purpose:

* **Tekton pipeline parameters** — written to `app.params` (the dict passed to the pipeline launcher). These are the values used in `{command}/workflow.py` `WorkflowField` definitions and `WorkflowSummaryItem` entries.
* **TUI-only operational inputs** — values needed to execute step actions during the TUI session but not passed to Tekton (e.g. `server_url`, `login_token`, `skip_tls_verify`). These are passed directly as arguments to the extended method (see migration pattern above) and are never stored in `app.params`.

### params write-back contract

After `TextualShell.run()` returns, `app_instance.params` is fully populated. The downstream pipeline launch code in `app.py` is unchanged.

```
bool field     → params[id] = "true" or "false"
multi_select   → params[id] = ",".join(selected_values)
all others     → params[id] = str(value)
```

### Non-interactive path — completely untouched

Every `app.py` has an `if args.some_sentinel:` block for the non-interactive path. That block is never touched during this migration.

### __main__.py dispatch pattern (per migrated command)

```python
if function == "update":
    cmdArgs = argv[2:]
    if "--catalog" not in cmdArgs:     # no non-interactive sentinel → TUI
        from mas.cli.tui.shell import serveTuiMode
        serveTuiMode("update", cmdArgs)
        return
    from mas.cli.update.app import UpdateApp
    app = UpdateApp()
    raise SystemExit(app.update(cmdArgs))
```

Non-interactive sentinel per command: `update` → `--catalog`; `upgrade` → `--mas-instance-id`; `install` → `--mas-instance-id`; `backup`/`restore`/`uninstall` → `--mas-instance-id`.

### pyproject.toml

`textual` added under `[tui]` optional extra in Phase 1.

----
## Implementation Plan

### Phase 1: Foundation — tui/models.py + tui/shell.py skeleton

Build the TUI type system and shell skeleton once. No command dispatch wired yet. The `workflow/` directory remains as an empty package placeholder.

* ✅ **1.1** Create `python/tests/unit/tui/__init__.py` (empty)

* ✅ **1.2** Write failing tests in `python/tests/unit/tui/test_tui_models.py`:
  * RED: `test_workflow_field_minimal_construction` — `WorkflowField(id="x", label="X", type="string")` does not raise
  * RED: `test_workflow_field_supports_multi_select_type` — `type="multi_select"` is accepted
  * RED: `test_workflow_field_supports_dynamic_select_type` — `type="dynamic_select"` accepted; `options_loader` stored
  * RED: `test_workflow_step_condition_receives_params_dict` — `condition=lambda p: p.get("x")=="y"`; calling `step.condition({"x": "y"})` returns `True`
  * RED: `test_workflow_summary_item_construction` — `WorkflowSummaryItem(label="L", param="p")` stores both fields
  * RED: `test_workflow_definition_is_list` — `WorkflowDefinition` accepted as a plain `list`
  * Confirmed RED: `ModuleNotFoundError: No module named 'mas.cli.tui'`

* ✅ **1.3** Create `python/src/mas/cli/tui/__init__.py` (empty)

* ✅ **1.4** Create `python/src/mas/cli/tui/models.py`:
  * `FieldType` literal with all 9 types
  * `WorkflowField`, `WorkflowSummaryItem`, `WorkflowStep` dataclasses with `field(default_factory=list)` defaults
  * `WorkflowDefinition = List[WorkflowStep]`
  * Google-style docstrings throughout

* ✅ **1.5** GREEN: 8/8 model tests pass

* ✅ **1.6** Write failing tests in `python/tests/unit/tui/test_tui_shell.py`:
  * Tests use `pytest.importorskip("textual")` — skip gracefully when textual absent
  * `pytestmark = pytest.mark.tui` applied to all tests
  * `test_import_error_without_textual`, `test_shell_instantiates`, `test_sidebar_has_one_item_per_step`, `test_condition_false_step_renders_greyed`, `test_active_step_heading_visible_in_content_area` written
  * These tests are currently SKIPPED (waiting for `textual` install); will be RED once textual is installed

* ✅ **1.7** Create `python/src/mas/cli/tui/shell.py`:
  * Guarded `textual` import — raises `ImportError` with `"pip install mas-cli[tui]"` hint when absent
  * `TextualShell(App)` skeleton with async `on_mount()`, sidebar + content layout
  * `DEFAULT_CSS` with sidebar 25%, `.step-active`, `.step-completed`, `.step-skipped` classes
  * async `_populate_sidebar()` (uses `await lv.append()`), async `_populate_content()` (uses `await sw.mount()`)
  * `_activate_step()`, `_is_skipped()` helpers; `serveTuiMode()` at module bottom
  * Textual 8.x API: `await list_view.append()`, `await switcher.mount()`, no `add_content()`

* ✅ **1.8** `textual` moved to hard dependency in `pyproject.toml` (user decision); `tui` marker added to `pytest.ini`
  * Note: the `[tui]` optional-dependencies section was not retained; `textual` is now in `dependencies`
  * Shell tests use `asyncio.run()` wrapper pattern (no pytest-asyncio needed for Textual 8.x)

* ✅ **1.9** GREEN + REFACTOR — black and flake8 clean

* ✅ **1.10** Phase 1 validation: 243 passed, 0 skipped, 0 failed

----

### Phase 2: Field widgets + params write-back (complete TUI shell)

Implement all field widget types, `Next →` button, params write-back, review screen, and `ActionOverlay`. After this phase the shell is fully functional — Phases 3+ only wire commands into it.

* ✅ **2.1** Write 25 failing tests — all confirmed RED before implementation

* ✅ **2.2** Implement `StepScreen(VerticalScroll)` in `shell.py`:
  * `_build_field_widget(field)` factory covering all 9 field types
  * `dynamic_select`: mounts `LoadingIndicator`; runs `options_loader(params)` in worker thread via `run_worker(thread=True)`; replaces indicator with `Select` via async `_replace_with_select` called from `call_from_thread`
  * Key finding: `_replace_with_select` must be `async def` so `call_from_thread` awaits it — prevents `WaitForScreenTimeout`
  * Key finding: `pilot.click()` requires `size=(200, 50)` for multi-step workflows — default test size clips the button off-screen
  * `on_button_pressed` → validate required fields → `_write_params()` → post `StepCompleted`
  * `_write_params()`: `bool` → `"true"/"false"`; `multi_select` → `",".join(selected)`; all others → `str(value)`

* ✅ **2.3** Implement `ReviewScreen(VerticalScroll)`:
  * `DataTable` populated from all steps' `summary` lists; sensitive values masked as `***`
  * `Button("Confirm", id="btn-confirm")` posts `WorkflowConfirmed` message to app

* ✅ **2.4** Implement `ActionOverlay(ModalScreen)`:
  * `ProgressBar` (indeterminate) + `RichLog` + hidden `Button("Dismiss")`
  * `run_worker(thread=True)` runs `step.action()`; on success calls `_on_success` via `call_from_thread`; on exception calls `_on_error`

* ✅ **2.5** Implement event handlers in `TextualShell`:
  * `on_step_completed()` — fires action overlay if step has action; else calls `_complete_step`
  * `_complete_step()` — marks step complete, refreshes conditions, advances to next non-skipped step or review
  * `on_workflow_confirmed()` — calls `self.exit(0)`

* ✅ **2.6** `shell.py` is 780 lines — under 800 limit; no extraction needed

* ✅ **2.7** GREEN + REFACTOR — `black` and `flake8` clean; removed unused `Scalar` import and `StepCompleted` stub

* ✅ **2.8** Restructure test files — replace `test_tui_shell.py` + `test_tui_shell_phase2.py` with semantically-named files:
  * `test_tui_shell_layout.py` — import guard, instantiation, sidebar, heading (5 tests)
  * `test_tui_shell_fields.py` — all 9 field widget types + defaults + dynamic_select (9 tests)
  * `test_tui_shell_navigation.py` — params write-back, Next, step advancement, condition re-evaluation (9 tests)
  * `test_tui_shell_review.py` — review screen, action overlay, confirm (7 tests)

* ✅ **2.9** Phase 2 validation: **38 passed, 0 failed** (`python/tests/unit/tui/` — all 38 tests GREEN)
  * Full suite: **268 passed, 0 skipped** — no regressions

----

### Phase 3: update command — first vertical slice

Wire `update` to the TUI shell. `upgrade`, `install`, and all others are completely unaffected.

* 📋 **3.1** Create `python/tests/unit/update/__init__.py` (empty)

* 📋 **3.2** Write failing tests in `python/tests/unit/update/test_update_workflow.py`:
  * RED: `test_build_update_workflow_returns_definition` — `buildUpdateWorkflow(app)` returns a list
  * RED: `test_build_update_workflow_step_ids` — ids `connect-cluster`, `choose-catalog`, `dependency-checks`, `review-settings` present in that order
  * RED: `test_connect_cluster_step_has_action` — `connect-cluster` step has a callable action
  * RED: `test_connect_cluster_action_is_connect_from_params` — action is `app._connectFromParams`
  * RED: `test_dependency_checks_step_has_action`
  * RED: `test_choose_catalog_field_is_select_type` — `mas_catalog_version` field has `type="select"` with non-empty options
  * RED: `test_review_settings_step_has_summary_items`
  * RED: `test_review_settings_summary_includes_catalog_version` — `mas_catalog_version` param referenced
  * RED: `test_all_conditions_accept_params_dict` — every step condition is either `None` or callable with `dict` arg without `TypeError`

* 📋 **3.3** Write failing tests in `python/tests/unit/update/test_update_main.py`:
  * RED: `test_main_update_no_catalog_calls_serve_tui_mode` — patch `serveTuiMode`; call `main()` with `["mas-cli", "update"]`; assert `serveTuiMode` called
  * RED: `test_main_update_with_catalog_does_not_call_tui` — `["mas-cli", "update", "--catalog", "v9-amd64"]`; assert `serveTuiMode` not called; `UpdateApp.update` called

* 📋 **3.4** Add `_connectFromParams(self) -> None` to `BaseApp` in `cli.py`:
  * Reads `server_url`, `login_token`, `skip_tls_verify` from `self.params`
  * If `self._dynClient` is already loaded and no connection params provided, calls `self.lookupTargetArchitecture()` and returns (already connected via kubeconfig)
  * Otherwise calls `connect(server_url, login_token, skip_tls)` from `mas.devops.ocp`, then `self.reloadDynamicClient()`, then `self.lookupTargetArchitecture()`
  * No `prompt_toolkit` calls — safe to run in a worker thread
  * Write the test first: `test_connect_from_params_uses_params_dict`, `test_connect_from_params_skips_when_already_connected`

* 📋 **3.5** Create `python/src/mas/cli/common/__init__.py` (empty) and `python/src/mas/cli/common/workflow.py`:
  * `connectClusterStep(app_instance) -> WorkflowStep` — returns the standard OCP connection step with `server_url`, `login_token`, `skip_tls_verify` fields and `action=app_instance._connectFromParams`

* 📋 **3.6** Create `python/src/mas/cli/update/workflow.py`:
  * `buildUpdateWorkflow(app_instance) -> WorkflowDefinition`
  * Uses `connectClusterStep(app_instance)` from `common/workflow.py`
  * All `condition` lambdas use `lambda p: ...` signature

* 📋 **3.7** Strip `update/app.py` interactive branch:
  * Remove all `printH1`/`printH2`/`printDescription`/`promptFor*`/`yesOrNo`/`Halo` calls from the `else:` interactive block in `update()`
  * The interactive block becomes empty (the `serveTuiMode` call is in `__main__.py`; `app.update()` is only called by `__main__` in non-interactive mode)
  * Non-interactive block (`if self.args.mas_catalog_version:`) is **untouched**

* 📋 **3.8** Wire `__main__.py` dispatch for `update`:
  * If `--catalog` absent → `serveTuiMode("update", cmdArgs)` then `return`
  * If `--catalog` present → `UpdateApp().update(cmdArgs)` as today

* 📋 **3.9** GREEN + REFACTOR
  * `wsl bash -lc "cd /mnt/c/Users/097891866/Documents/GitHub/ibm-mas/cli && black . && flake8 python/ 2>&1 | tail -20"`

* 📋 **3.10** Validate Phase 3
  * `wsl bash -lc "cd /mnt/c/Users/097891866/Documents/GitHub/ibm-mas/cli && .venv/bin/pytest python/tests/unit/ -v 2>&1 | tail -40"`
  * All upgrade/install/other command tests still green

----

### Phase 4: upgrade command — second vertical slice

Same pattern as Phase 3. All other commands unchanged.

* 📋 **4.1** Create `python/tests/unit/upgrade/__init__.py` (empty)

* 📋 **4.2** Write failing tests in `python/tests/unit/upgrade/test_upgrade_workflow.py`:
  * RED: `test_build_upgrade_workflow_returns_definition`
  * RED: `test_build_upgrade_workflow_step_ids` — expected step ids present in order
  * RED: `test_connect_cluster_step_has_action`
  * RED: `test_instance_selection_step_present`
  * RED: `test_all_conditions_accept_params_dict`

* 📋 **4.3** Write failing tests in `python/tests/unit/upgrade/test_upgrade_main.py`:
  * RED: `test_main_upgrade_no_instance_calls_serve_tui_mode`
  * RED: `test_main_upgrade_with_instance_does_not_call_tui`

* 📋 **4.4** Create `python/src/mas/cli/upgrade/workflow.py`:
  * `buildUpgradeWorkflow(app_instance) -> WorkflowDefinition`
  * Uses `connectClusterStep(app_instance)` from `common/workflow.py`
  * All conditions use `lambda p: ...` signature

* 📋 **4.5** Strip `upgrade/app.py` interactive branch (same approach as 3.6)

* 📋 **4.6** Wire `__main__.py` dispatch for `upgrade`:
  * If `--mas-instance-id` absent → `serveTuiMode("upgrade", cmdArgs)` then `return`
  * If `--mas-instance-id` present → `UpgradeApp().upgrade(cmdArgs)` as today

* 📋 **4.7** GREEN + REFACTOR
  * `wsl bash -lc "cd /mnt/c/Users/097891866/Documents/GitHub/ibm-mas/cli && black . && flake8 python/ 2>&1 | tail -20"`

* 📋 **4.8** Validate Phase 4
  * `wsl bash -lc "cd /mnt/c/Users/097891866/Documents/GitHub/ibm-mas/cli && .venv/bin/pytest python/tests/unit/ -v 2>&1 | tail -60"`

----

### Phase 5: install command — most complex vertical slice

`install` requires the most work: `install/settings/` mixins dismantled, `summarizer.py` replaced, full conditional step graph built. All other commands unaffected.

* 📋 **5.1** Create `python/tests/unit/install/__init__.py` (empty, if not present)

* 📋 **5.2** Write failing tests in `python/tests/unit/install/test_install_workflow.py`:
  * RED: `test_build_install_workflow_returns_definition`
  * RED: `test_all_top_level_steps_present` — full expected step id list verified
  * RED: `test_kafka_step_condition_false_when_no_iot` — `condition({"install_iot": "false"})` is `False`
  * RED: `test_kafka_step_condition_true_when_iot_selected` — `condition({"install_iot": "true"})` is `True`
  * RED: `test_manage_components_field_is_multi_select` — `mas_appws_components` field has `type="multi_select"`
  * RED: `test_storage_class_field_uses_dynamic_select` — storage class field has `type="dynamic_select"` and `options_loader` callable
  * RED: `test_dns_cloudflare_step_condition` — only active when `dns_provider == "cloudflare"`
  * RED: `test_dns_route53_step_condition` — only active when `dns_provider == "route53"`
  * RED: `test_db2_manage_step_condition_requires_install_manage` — condition requires `install_manage == "true"`
  * RED: `test_all_conditions_accept_params_dict`

* 📋 **5.3** Write failing tests in `python/tests/unit/install/test_install_main.py`:
  * RED: `test_main_install_no_instance_calls_serve_tui_mode`
  * RED: `test_main_install_with_instance_id_does_not_call_tui`

* 📋 **5.4** Create `python/src/mas/cli/install/workflow.py`:
  * `buildInstallWorkflow(app_instance) -> WorkflowDefinition`
  * Full static step list; all conditions use `lambda p: ...`
  * `multi_select` field for Manage components (`id="mas_appws_components"`)
  * `dynamic_select` fields for storage classes (`options_loader=app_instance._loadStorageClasses`)

* 📋 **5.5** Migrate settings mixins to `InstallApp` private methods:
  * For each mixin file (`db2Settings`, `mongodbSettings`, `kafkaSettings`, `manageSettings`, `additionalConfigs`, `aiSettings`):
    * Move cluster-logic to `InstallApp` as `_configDb2()`, `_configMongoDB()`, etc.
    * Remove all `printH1`/`promptFor*`/`yesOrNo`/`Halo` calls from each method
    * Delete mixin file once fully migrated
  * Replace `InstallSummarizerMixin` with `WorkflowSummaryItem` entries in `workflow.py`; delete `summarizer.py`

* 📋 **5.6** Add `_loadStorageClasses(params) -> List[str]` to `InstallApp`

* 📋 **5.7** Strip `install/app.py` interactive branch; non-interactive path untouched

* 📋 **5.8** Wire `__main__.py` dispatch for `install`

* 📋 **5.9** GREEN + REFACTOR; verify no `printH1`/`promptFor*` remain in `install/`:
  * `wsl bash -lc "cd /mnt/c/Users/097891866/Documents/GitHub/ibm-mas/cli && grep -rn 'printH1\\|promptFor\\|yesOrNo\\|Halo' python/src/mas/cli/install/ --include='*.py' | grep -v __pycache__ 2>&1"`

* 📋 **5.10** Validate Phase 5
  * `wsl bash -lc "cd /mnt/c/Users/097891866/Documents/GitHub/ibm-mas/cli && .venv/bin/pytest python/tests/unit/ -v 2>&1 | tail -60"`

----

### Phase 6: remaining commands (backup, restore, uninstall, aiservice)

Each command is an independent mini-slice. Apply the same pattern as Phase 3 for each.

* 📋 **6.1** For each command (`backup`, `restore`, `uninstall`, `aiservice-install`, `aiservice-upgrade`):
  * Create `python/tests/unit/{command}/__init__.py` (if not present)
  * Write failing tests: `test_build_{command}_workflow_returns_definition`, step ids, actions, conditions
  * Write failing dispatcher test: `test_main_{command}_no_instance_calls_serve_tui_mode`
  * Create `python/src/mas/cli/{command}/workflow.py` with `build{Command}Workflow(app_instance)`
  * Strip interactive calls from `{command}/app.py`
  * Wire `__main__.py` dispatch
  * GREEN + REFACTOR per command; validate full test suite green after each

* 📋 **6.2** Validate Phase 6
  * `wsl bash -lc "cd /mnt/c/Users/097891866/Documents/GitHub/ibm-mas/cli && .venv/bin/pytest python/tests/unit/ -v 2>&1 | tail -60"`

----

### Phase 7: cleanup — remove obsolete code

Only runs after **every** command has been migrated and verified. Removes all remaining dead code.

* 📋 **7.1** Verify no `printH1`/`promptFor*`/`yesOrNo`/`Halo` remain in any `app.py`:
  * `wsl bash -lc "cd /mnt/c/Users/097891866/Documents/GitHub/ibm-mas/cli && grep -r 'printH1\\|promptFor\\|yesOrNo\\|from halo' python/src/mas/cli --include='*.py' | grep -v displayMixins | grep -v __pycache__ 2>&1"` — must be empty

* 📋 **7.2** Delete `python/src/mas/cli/displayMixins.py`

* 📋 **7.3** Remove `PrintMixin, PromptMixin` from `BaseApp` inheritance in `cli.py`; remove `from .displayMixins import ...` import; remove `prompt_toolkit` imports from `cli.py`

* 📋 **7.4** Delete `connectWeb()` from `cli.py` — it has no callers; its role is now fulfilled by `_connectFromParams()` added in Phase 3

* 📋 **7.5** Remove `prompt_toolkit` and `halo` from hard dependencies in `pyproject.toml`

* 📋 **7.6** Delete `python/src/mas/cli/workflow/` directory (empty, just the `__pycache__/` shell remaining)

* 📋 **7.7** Delete `python/src/mas/cli/install/argBuilder.py` if no longer imported anywhere:
  * `wsl bash -lc "grep -r 'argBuilder' python/src/mas/cli --include='*.py' | grep -v __pycache__ 2>&1"`

* 📋 **7.8** GREEN + REFACTOR
  * `wsl bash -lc "cd /mnt/c/Users/097891866/Documents/GitHub/ibm-mas/cli && black . && flake8 python/ 2>&1 | tail -20"`

* 📋 **7.9** Validate Phase 7
  * `wsl bash -lc "cd /mnt/c/Users/097891866/Documents/GitHub/ibm-mas/cli && .venv/bin/pytest python/tests/unit/ -v 2>&1 | tail -60"`

----

## Final Validation

### Success Criteria
* `mas-cli update` (no flags) launches Textual TUI
* `mas-cli update --catalog v9-...` runs non-interactive unchanged
* `mas-cli upgrade`, `install`, `backup`, `restore`, `uninstall`, `aiservice-install`, `aiservice-upgrade` — TUI for interactive; non-interactive unchanged throughout
* `must-gather`, `mirror`, `setup-rbac`, `pre-install` — unaffected in all phases
* All conditional steps appear/disappear correctly based on prior selections
* `multi_select` Manage components write correct comma-joined param
* `dynamic_select` storage classes load from cluster in worker thread without freezing UI
* `textual` absent → clear `ImportError` with install hint; non-interactive CLI works without it
* Zero `printH1`/`promptFor*`/`yesOrNo`/`Halo` calls in any `app.py` after Phase 7
* All unit tests pass; zero `black`/`flake8 python/` findings
* Each production file ≤ 800 lines

### Validation Steps
* `wsl bash -lc "cd /mnt/c/Users/097891866/Documents/GitHub/ibm-mas/cli && .venv/bin/pytest python/tests/unit/ -v 2>&1 | tail -80"`
* `wsl bash -lc "cd /mnt/c/Users/097891866/Documents/GitHub/ibm-mas/cli && black . --check && flake8 python/ 2>&1 | tail -30"`
* `wsl bash -lc "cd /mnt/c/Users/097891866/Documents/GitHub/ibm-mas/cli && grep -rn 'printH1\\|promptFor\\|yesOrNo\\|from halo' python/src/mas/cli --include='*.py' | grep -v displayMixins | grep -v __pycache__ 2>&1"` — empty after Phase 7

----
## Agent Instructions

### Rules
* Use the plan document as the single source of truth during implementation
* Do NOT use `update_todo_list` tool
* Do NOT write any production code before writing a failing test — RED → GREEN → REFACTOR strictly
* Do NOT modify the non-interactive code path in any `app.py` — only the interactive branch changes
* `textual` is a hard dependency in `pyproject.toml` — do not move it back to an optional extra
* Do NOT delete `displayMixins.py` or the `workflow/` directory until Phase 7
* After every phase, ALL tests must pass and `black`/`flake8 python/` must be clean before marking the phase done
* All shell commands use `wsl bash -lc "..."` wrapper
* `bool` fields write `"true"` / `"false"` strings — match the prior `yesOrNo` convention
* `multi_select` fields write `","` joined strings — e.g. `"base=latest,health=latest"`
* `condition` callables always accept a single `params: dict` argument — no zero-arg conditions
* Settings mixin files (`install/settings/`) are deleted only after all methods have been migrated to `InstallApp`
* Commands not yet migrated must still pass all their existing tests unchanged
* Use `flake8 python/` not `flake8 .` — avoids false positives from `.venv/` and `web/node_modules/`
