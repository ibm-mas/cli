# Plan: Fix `mas update` failures with `v9-master-amd64` catalog

## Objective

`mas update --dev-mode -c v9-master-amd64` has two crash paths that must be fixed:

1. `AttributeError: 'UpdateApp' object has no attribute 'chosenCatalog'` — `self.chosenCatalog` is never initialised to a safe default, so downstream detect methods crash after `getCatalog()` raises `NoSuchCatalogError`.
2. `AssertionError: Catalog ID is not set` — when the installed catalog image tag is non-standard (dev/master builds), `getCurrentCatalog()` returns `catalogId=None`, and a hard `assert` fires in the Review Settings section despite the warning-and-continue path being intentional.

---

## Design Decisions

### Root Cause

In [`python/src/mas/cli/update/app.py`](python/src/mas/cli/update/app.py):

- `self.chosenCatalog` is **never assigned a default value** in `update()`.
- Two call sites already guard `getCatalog()` with `except NoSuchCatalogError`:
  - Dev-mode branch (line 248–251): `pass` after catching the error.
  - `validateCatalog()` (line 472–474): `return` after catching the error.
- After either guard fires, `self.chosenCatalog` is undefined. Subsequent methods read it unconditionally:

  | Method | Access | Line |
  |--------|--------|------|
  | `detectDb2u()` | `self.chosenCatalog["db2_channel_default"]` | 849 |
  | `detectMongoDb()` | `self.chosenCatalog["mongo_extras_version_default"]` | 615 |
  | `detectCP4D()` | `self.chosenCatalog["cpd_product_version_default"]` | 731 |
  | `shouldApplyRBACForInstance()` | `targetCatalog.get(...)` | 106 |

### Fix Strategy

**Minimal, safe approach:**

1. Initialise `self.chosenCatalog = None` at the top of `update()`, alongside the other instance attribute initializations (line 163–165).
2. Guard each downstream `self.chosenCatalog` dict access with an early-return / skip when `self.chosenCatalog is None`:
   - `detectDb2u()`: skip the `targetDb2uVersion` assignment; skip version comparison logic.
   - `detectMongoDb()`: skip `targetMongoVersion` assignment and the entire version comparison block.
   - `detectCP4D()`: skip the `cpdTargetVersion` assignment from catalog; fall through to the `--cpd-product-version` arg path only.
   - `shouldApplyRBACForInstance()` already receives `targetCatalog` as a parameter and checks `if not targetCatalog:` at line 56 — this guard is already safe if `self.chosenCatalog` is `None`.

**What must NOT change:**
- The existing `NoSuchCatalogError` guards themselves — they are correct.
- `chooseCatalog()` — production catalog list is correct.
- OCP version and downgrade checks in `validateCatalog()` — only active when `getCatalog()` succeeds.
- Any logic not downstream of `self.chosenCatalog`.

### Behaviour When `chosenCatalog` is None

- `detectDb2u()`: Db2u instances are detected and namespace is set, but channel (`db2_channel`) is not set. The Ansible role handles the missing value gracefully.
- `detectMongoDb()`: MongoDB instances are detected and namespace is set, but `mongodb_version` is not set and no major-version upgrade check occurs. Same Ansible-role fallback applies.
- `detectCP4D()`: CPD instances are detected; if `--cpd-product-version` was passed via CLI, it is used; otherwise CPD update is not triggered (safest default).
- RBAC: `shouldApplyRBACForInstance()` receives `None` as `targetCatalog` and returns `False` immediately at the existing `if not targetCatalog: return False` guard (line 56). No RBAC is applied — correct for dev-mode master builds.

---

## Critical Rules

- Track progress ONLY in this plan document; do NOT use chat todo lists.
- Initialise `self.chosenCatalog = None` — do not use `{}` as a default; `None` is a clearer sentinel that prevents silent key-access on an empty dict.
- Do NOT add new try/except blocks. Only add `if self.chosenCatalog is None:` guards at the read sites.
- Introduce no functional changes beyond the `None` initialisation and the four guard additions.
- All existing integration tests must continue to pass (they mock `getCatalog` to return a real dict, so `self.chosenCatalog` will not be `None` in those tests).
- After every code change run `flake8 python/src/mas/cli/update/app.py` — zero errors.

---

## Execution Plan

### Phase 1 — Code Fix

**Objective:** Initialise `self.chosenCatalog = None` and add `None` guards at every downstream read site.

Spawn a new subtask to complete this phase. The subtask must read this plan file for full context.

- [ ] **1.1** In [`python/src/mas/cli/update/app.py`](python/src/mas/cli/update/app.py) `update()` method, add `self.chosenCatalog = None` after the existing initializations at line 165 (alongside `self.applyPreInstallMASRBAC = False`).
- [ ] **1.2** In `detectDb2u()` (line 849), guard the `targetDb2uVersion` read:
  ```python
  targetDb2uVersion = self.chosenCatalog["db2_channel_default"] if self.chosenCatalog else None
  ```
  Then wrap the `if targetDb2uVersion:` check around `self.setParam("db2_channel", targetDb2uVersion)` (this `if` already exists at line 862 — verify it covers the assignment correctly).
- [ ] **1.3** In `detectMongoDb()` (line 615), guard the `targetMongoVersion` read and the entire version comparison block:
  ```python
  if self.chosenCatalog:
      targetMongoVersion = self.chosenCatalog["mongo_extras_version_default"]
      # ... existing version comparison logic ...
  else:
      h.stop_and_persist(symbol=self.successIcon, text=f"MongoDb CE is installed (catalog not available in dev mode)")
  ```
- [ ] **1.4** In `detectCP4D()` (line 731), guard the `cpdTargetVersion` catalog read:
  ```python
  if self.args.cpd_product_version:
      cpdTargetVersion = self.getParam("cpd_product_version")
  elif self.chosenCatalog:
      cpdTargetVersion = self.chosenCatalog["cpd_product_version_default"]
  else:
      h.stop_and_persist(symbol=self.successIcon, text=f"IBM Cloud Pak for Data ({cpdInstanceNamespace}) detected (catalog not available in dev mode)")
      return
  ```
- [ ] **1.5** Remove the `assert self.installedCatalogId is not None` on line 298 and replace with `self.installedCatalogId or "Unknown"` so that dev/master catalog images (whose tag is not a standard `v9-YYMMDD-amd64` string) do not crash the Review Settings summary.
- [ ] **1.6** Validate: run `flake8 python/src/mas/cli/update/app.py` — zero errors.

### Phase 2 — Integration Tests

**Objective:** Add integration tests covering the `NoSuchCatalogError` / `chosenCatalog = None` path in `mas update` for both dev-mode and non-dev-mode with the master catalog tag.

Spawn a new subtask to complete this phase. The subtask must read this plan file for full context.

- [ ] **2.1** Create [`python/tests/integration/update/test_dev_mode.py`](python/tests/integration/update/test_dev_mode.py) with copyright header matching other files in the directory.
- [ ] **2.2** Write `test_update_master_dev_mode`:
  - `argv`: `["--dev-mode", "--mas-catalog-version", "v9-master-amd64", "--no-confirm"]`
  - Override `mocks["get_catalog"]` `side_effect` to `NoSuchCatalogError()` so `self.chosenCatalog` remains `None`.
  - No Db2u / MongoDB / CP4D resources in the config (keep dependencies absent to isolate the test).
  - Assert update completes without exception (`expect_exception=None`).
  - Use `UpdateTestConfig` + `run_update_test` from [`python/tests/integration/utils/update_test_helper.py`](python/tests/integration/utils/update_test_helper.py).
- [ ] **2.3** Write `test_update_master_no_dev_mode`:
  - `argv`: `["--mas-catalog-version", "v9-master-amd64", "--no-confirm"]`
  - Override `mocks["get_catalog"]` `side_effect` to `NoSuchCatalogError()`.
  - Assert update completes without exception.
- [ ] **2.4** Note: `UpdateTestHelper.run_update_test()` does not expose `mocks` directly — the `side_effect` override must be applied inside the test via a custom helper or by subclassing `UpdateTestHelper`. Check whether `run_update_test` accepts a `mocks_override` hook; if not, test by patching `mas.cli.update.app.getCatalog` again with `mock.patch` around the `run_update_test` call.
- [ ] **2.5** Add a third test `test_update_unknown_installed_catalog` that sets `installed_catalog_id=None` (simulating `getCurrentCatalog` returning `catalogId=None`) and asserts no `AssertionError` is raised.
- [ ] **2.6** Validate: run `.venv/bin/python -m pytest python/tests/integration/update/test_dev_mode.py -v` — all tests pass.

---

## Final Validation

Run the full update integration test suite to confirm no regressions:

```bash
.venv/bin/python -m pytest python/tests/integration/update/ -v
```

**Success criteria:**
- All pre-existing update integration tests pass.
- Both new `test_dev_mode.py` tests pass.
- `flake8 python/src/mas/cli/update/app.py` reports zero issues.

**Troubleshooting:**
- If any of `detectDb2u`, `detectMongoDb`, or `detectCP4D` still fail with `AttributeError`, re-check that the guard was placed **before** the dict access, not inside the block that already assumed the key exists.
- If `shouldApplyRBACForInstance()` crashes on `None`, verify the existing `if not targetCatalog: return False` guard at line 56 is still in place (it is — do not remove it).
- If the `getCatalog` mock override in tests is not taking effect, ensure the `mock.patch` for the override is applied after `UpdateTestHelper.setup_mocks()` but before `app.update()` is called (stack ordering matters in `ExitStack`).
