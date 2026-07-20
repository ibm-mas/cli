# Plan: Diagnose and Fix `NoSuchCatalogError` for `v9-master-amd64` in `mas update`

## Objective

Diagnose why `mas update` fails with `NoSuchCatalogError` when `v9-master-amd64` is used and
implement the correct fix, mirroring the pattern that already works correctly in `mas install`.

---

## Design Decisions

### Root Cause (Confirmed)

The `NoSuchCatalogError` is raised by `getCatalog()` from the external `mas.devops.data` package.
`v9-master-amd64` is a development/master catalog tag that does **not** exist in the static catalog
data embedded in `mas.devops` — it is only valid when the package itself is built from the `master`
branch of `ansible-devops`.

The bug has two distinct paths:

| Path | Condition | What happens |
|---|---|---|
| **Interactive mode, no `--dev-mode`** | User opens interactive session and chooses `v9-master-amd64` | Not possible via `chooseCatalog()` — only production tags are offered. Not a risk. |
| **Non-interactive mode, no `--dev-mode`** | `--catalog v9-master-amd64` passed without `--dev-mode` | `validateCatalog()` calls `getCatalog()`; `NoSuchCatalogError` propagates unhandled → crash. |
| **Dev mode, any mode** | `--dev-mode` flag set | `getCatalog(catalogVersion)` called at line 248 of `update/app.py`; `NoSuchCatalogError` still propagates unhandled if `v9-master-amd64` not in the installed `mas.devops` package. |

### What `mas install` does correctly

`python/src/mas/cli/install/app.py` line 2391–2395 wraps `getCatalog()` in a `try/except NoSuchCatalogError: pass` block. This silently tolerates the missing catalog entry in non-production builds.

### The fix required for `mas update`

Two locations in [`python/src/mas/cli/update/app.py`](python/src/mas/cli/update/app.py):

1. **`validateCatalog()` (line 468)** — wrap `getCatalog()` call in `try/except NoSuchCatalogError: return`
   so that a missing catalog does not crash in non-interactive non-dev-mode (defensive fix, low risk).

2. **Dev mode branch (line 248)** — wrap `getCatalog(catalogVersion)` in `try/except NoSuchCatalogError: pass`
   so that running with `--dev-mode --catalog v9-master-amd64` against a production `mas.devops` package
   does not crash (same pattern as install).

The import of `NoSuchCatalogError` must be added to [`update/app.py`](python/src/mas/cli/update/app.py) line 23.

### ansible-devops interaction

`getCatalog`, `getNewestCatalogTag`, and `NoSuchCatalogError` all live in the `mas.devops.data`
module, which is shipped as part of the `ibm-mas-devops` Python package (declared as a dependency in
`pyproject.toml`). This repo does **not** contain that package's source — it is an external dependency.
The catalog data baked into `mas.devops.data` determines which tags are "valid". `v9-master-amd64`
only exists in master-branch builds of that package.

---

## Critical Rules

- Track progress ONLY in this plan document; do NOT use chat todo lists.
- Do NOT change `chooseCatalog()` — the production catalog list it presents is correct.
- Do NOT change `validateCatalog()` OCP version or downgrade checks — only the `getCatalog()` call needs guarding.
- Introduce no functional changes beyond guarding the two `getCatalog()` calls.
- After every code change, run the integration test suite for `update` to confirm nothing regresses.
- Mirror the exact exception-handling pattern used in `install/app.py` line 2391–2395.

---

## Execution Plan

### Phase 1 — Code Fix

**Objective:** Add `NoSuchCatalogError` import and guard both `getCatalog()` call sites in `update/app.py`.

Spawn a new subtask to complete this phase. The subtask must read this plan file for full context.

- [ ] **1.1** In [`python/src/mas/cli/update/app.py`](python/src/mas/cli/update/app.py) line 23, extend the
  `from mas.devops.data import ...` statement to also import `NoSuchCatalogError`.
- [ ] **1.2** In `validateCatalog()` (line 468), wrap the `getCatalog()` call:
  ```python
  try:
      self.chosenCatalog = getCatalog(self.getParam("mas_catalog_version"))
  except NoSuchCatalogError:
      return
  ```
- [ ] **1.3** In the dev-mode branch (line 248), wrap the `getCatalog()` call:
  ```python
  try:
      self.chosenCatalog = getCatalog(catalogVersion)
  except NoSuchCatalogError:
      pass
  ```
- [ ] **1.4** Validate: run `flake8 python/src/mas/cli/update/app.py` — zero errors.

### Phase 2 — Integration Tests

**Objective:** Add integration tests that cover `NoSuchCatalogError` scenarios for `mas update`,
mirroring the pattern in [`python/tests/integration/install/test_dev_mode.py`](python/tests/integration/install/test_dev_mode.py).

Spawn a new subtask to complete this phase. The subtask must read this plan file for full context.

- [ ] **2.1** Create `python/tests/integration/update/test_dev_mode.py` with two test functions:
  - `test_update_master_no_dev_mode` — passes `--catalog v9-master-amd64` without `--dev-mode`;
    configures `getCatalog` mock to raise `NoSuchCatalogError`; asserts the update completes
    gracefully (no unhandled exception).
  - `test_update_master_dev_mode` — passes `--catalog v9-master-amd64` with `--dev-mode`;
    configures `getCatalog` mock to raise `NoSuchCatalogError`; asserts the update proceeds
    past catalog selection (no crash).
- [ ] **2.2** Use `UpdateTestConfig` / `run_update_test` from
  [`python/tests/integration/utils/update_test_helper.py`](python/tests/integration/utils/update_test_helper.py)
  — `expect_exception` field is available to assert specific exceptions are raised if needed;
  otherwise leave it `None` to assert no exception.
- [ ] **2.3** Note: `UpdateTestHelper.setup_mocks()` already patches `getCatalog` at
  `mas.cli.update.app.getCatalog` (line 425 of test helper) — override that mock's `side_effect`
  to `NoSuchCatalogError()` per test.
- [ ] **2.4** Validate: run `python -m pytest python/tests/integration/update/test_dev_mode.py -v`
  — all tests pass.

---

## Final Validation

Run the full update integration test suite to confirm no regressions:

```bash
.venv/bin/python -m pytest python/tests/integration/update/ -v
```

**Success criteria:**
- All pre-existing update tests pass.
- Both new `test_dev_mode.py` tests pass.
- `flake8 python/src/mas/cli/update/app.py` reports zero issues.

**Troubleshooting:**
- If `NoSuchCatalogError` is not importable, verify the installed `mas.devops` version via
  `.venv/bin/pip show ibm-mas-devops` — the class is confirmed present in `mas.devops.data`
  (see `install/app.py` line 64 for the same import).
- If the `validateCatalog()` guard causes OCP/downgrade checks to be skipped, add
  `self.chosenCatalog = {}` as a fallback default before the try/except so downstream
  `.get()` calls on `chosenCatalog` still work.
