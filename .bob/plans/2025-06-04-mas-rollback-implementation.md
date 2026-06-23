# MAS Rollback Command — Implementation Plan

**Date:** 2025-06-04  
**Branch:** `masrollback`

---

## Objective

Wire up the existing `mas rollback` Python command so it is accessible through the CLI dispatcher, fix the missing `chooseCatalog()` method on `RollbackApp`, add rollback to the CLI usage display, and ensure the Tekton pipeline template is correct. The majority of the implementation (argParser, app logic, Tekton pipeline) already exists; the work is completing the integration gaps.

---

## Design Decisions

### What Already Exists (Do Not Recreate)
| Component | File | Status |
|-----------|------|--------|
| Python app class `RollbackApp` | `python/src/mas/cli/rollback/app.py` | ✅ Complete |
| Argument parser `rollbackArgParser` | `python/src/mas/cli/rollback/argParser.py` | ✅ Complete |
| `__init__.py` | `python/src/mas/cli/rollback/__init__.py` | ✅ Complete |
| Tekton pipeline template | `tekton/src/pipelines/rollback.yml.j2` | ✅ Complete |
| Bash wrapper `mas rollback` dispatch | `image/cli/mascli/mas` (lines 317–325) | ✅ Complete |
| External task references (`mas-devops-suite-rollback`, etc.) | `mas-devops` library | ✅ Provided by dependency |

### What Is Missing / Broken
1. **CLI dispatcher registration** — `python/src/mas/cli/__main__.py` has no `if function == "rollback":` block. Running `mas-cli rollback` hits the "Unknown action" error path.
2. **Usage display** — `usage()` in `__main__.py` does not list `rollback` in the printed help text.
3. **`chooseCatalog()` method missing from `RollbackApp`** — `RollbackApp` inherits only from `BaseApp`. `chooseCatalog()` is defined only in `UpdateApp`, not in `BaseApp`. The interactive code path (`self.chooseCatalog()` at line 90 of `app.py`) will raise `AttributeError` at runtime. `RollbackApp` needs its own `chooseCatalog()` implementation offering a list of catalog versions to roll back *to* (older catalogs).

### `chooseCatalog()` Design for Rollback
- The rollback `chooseCatalog()` must present a list of **older** catalog versions (the inverse of the update list).
- Follow the same pattern as `UpdateApp.chooseCatalog()` in `python/src/mas/cli/update/app.py` (lines 446–462): show named options with `promptForListSelect`.
- Catalog list should match the set of catalogs currently supported — the same versions listed in `UpdateApp.chooseCatalog()` can be reused here; the user will be picking a *previous* one. The `validateCatalog()` method (already implemented) will guard against selecting a newer catalog.

### Parameter Defaults in `rollback.yml.j2`
- `mas_core_version`, `mas_app_manage_version`, `mas_app_iot_version` currently have no `default:` value in the pipeline params. They should default to `""` (empty string) so the conditional `when: notin [""]` guards work correctly when a version is omitted.

---

## Critical Rules

- **Introduce no functional changes** to `app.py`, `argParser.py`, or `rollback.yml.j2` beyond what is required to fix the identified gaps.
- **Follow the existing dispatcher pattern** in `__main__.py` exactly — add a `if function == "rollback":` block matching the style of `backup`/`restore`.
- **Track progress only in this plan document**, not in chat todo lists.
- Do NOT rename or restructure any existing files.
- Do NOT add error handling for scenarios not identified here.
- After every phase, run the specified validation before marking the phase complete.

---

## Execution Plan

### Phase 1 — Fix CLI Dispatcher Registration

**Intent:** Make `mas-cli rollback` callable without triggering the "Unknown action" error.

- [x] **1.1** Open `python/src/mas/cli/__main__.py`
- [x] **1.2** After the `if function == "restore":` block (ends at line 109), add:
  ```python
  if function == "rollback":
      from mas.cli.rollback.app import RollbackApp

      app = RollbackApp()
      app.rollback(argv[2:])
      return
  ```
- [x] **1.3** In the `usage()` function HTML string (lines 41–54), add `rollback` to the MAS Management Actions list:
  ```
  " - <ForestGreen>mas-cli rollback</ForestGreen>   Rollback the IBM Maximo Operator Catalog\n"
  ```
  Insert this line after the `upgrade` line and before the `backup` line.
- [x] **1.4** Validate: `ast.parse()` confirms `__main__.py` syntax is clean.

---

### Phase 2 — Implement `chooseCatalog()` on `RollbackApp`

**Intent:** Fix the `AttributeError` that would occur in interactive mode when `self.chooseCatalog()` is called on a `RollbackApp` instance.

- [x] **2.1** Open `python/src/mas/cli/rollback/app.py`
- [x] **2.2** No `getCatalog` import needed — the method only uses `promptForListSelect` with a hardcoded list, matching `UpdateApp.chooseCatalog()` which also does not import `getCatalog`.
- [x] **2.3** Added `chooseCatalog()` to `RollbackApp` (before `validateCatalog()`), catalog list matches `UpdateApp.chooseCatalog()` exactly.
- [x] **2.4** Validate: `ast.parse()` confirms `rollback/app.py` syntax is clean.

---

### Phase 3 — Fix Pipeline Parameter Defaults

**Intent:** Ensure that `mas_core_version`, `mas_app_manage_version`, and `mas_app_iot_version` pipeline parameters have `default: ""` so the `when: notin [""]` conditional guards work when those params are omitted by a caller.

- [x] **3.1** Open `tekton/src/pipelines/rollback.yml.j2`
- [x] **3.2** Added `default: ""` to `mas_core_version`, `mas_app_manage_version`, and `mas_app_iot_version`.
- [x] **3.3** Validated via `grep -n "default:"` — all three params now have `default: ""`.

---

### Phase 4 — Fix Minor Comment Bug in Pipeline

**Intent:** The comment at line 146 in `rollback.yml.j2` reads `"# Manage App Rollback"` but it describes the IoT rollback task (`iot-rollback`). Fix the comment to avoid confusion.

- [x] **4.1** Fixed comment above `iot-rollback` task: `# 3. Rollback App (IoT)` / `# IoT App Rollback`.
- [x] **4.2** Validated via visual review — change is a comment-only edit with no structural impact.

---

## Final Validation

After all phases are complete:

1. **Import check:**
   ```bash
   python -c "from mas.cli.rollback.app import RollbackApp; print('Import OK')"
   python -c "import mas.cli.__main__; print('Dispatcher OK')"
   ```

2. **Help text check:**
   ```bash
   mas-cli --help
   ```
   Expected: `rollback` appears in the printed MAS Management Actions list.

3. **Arg parser smoke test:**
   ```bash
   mas-cli rollback --help
   ```
   Expected: shows the `mas rollback` usage from `rollbackArgParser`.

4. **Pipeline template review:**
   - Confirm `rollback.yml.j2` has `default: ""` on all three version params.
   - Confirm the IoT task comment is corrected.

5. **Success criteria:**
   - `mas-cli rollback --help` exits 0 and shows correct usage.
   - `mas-cli --help` lists `rollback` in the action list.
   - No `AttributeError` on `chooseCatalog` in the interactive path (verified by code review).
   - Pipeline YAML has correct defaults.
