# Plan: Delete `sync-install` ConfigMap Before Install Pipeline Launch

## Objective

Before `launchInstallPipeline` is called in `InstallApp`, delete the `sync-install` ConfigMap from the pipelines namespace so that a re-run of a previously failed install does not inherit a stale `INSTALL_STATUS: Failed` that causes parallel pipelines (e.g. FVT) to abort immediately.

---

## Design Decisions

### Where to make the change
The call to `launchInstallPipeline` lives in `python/src/mas/cli/install/app.py` at line 3171, inside the `continueWithInstall` block. The deletion will be inserted immediately before the `with Halo(... "Submitting PipelineRun ...")` block at line 3167.

### ConfigMap name
No Python constant for `"sync-install"` exists anywhere in the codebase (it only appears in Tekton YAML templates). A new inline string literal `"sync-install"` will be used.

### Kubernetes client pattern
Use the same pattern already established in `cli.py::initializeApprovalConfigMap` (lines 549–553):
```python
cmAPI = self.dynamicClient.resources.get(api_version="v1", kind="ConfigMap")
try:
    cmAPI.delete(name="sync-install", namespace=pipelinesNamespace)
except NotFoundError:
    pass
```

### Namespace
`pipelinesNamespace` is already resolved at line 3059 (`f"mas-{self.getParam('mas_instance_id')}-pipelines"`) and is in scope at the insertion point.

### Imports
`NotFoundError` is already imported in `app.py` at line 20. No new imports are needed.

### Logging style
The surrounding code uses a `Halo` spinner for user-visible steps and `logger.debug()` for internal tracing. The deletion will follow the same Halo spinner pattern used for all other pre-pipeline steps, with a `logger.debug()` for the "not found, skipping" branch (consistent with the `initializeApprovalConfigMap` pattern).

---

## Critical Rules

- Modify only `python/src/mas/cli/install/app.py` — do not touch pipeline definitions, Tekton templates, or any other file unless strictly necessary.
- The deletion must be idempotent: a `NotFoundError` must be caught and silently ignored.
- No new imports or dependencies may be introduced.
- Track progress only in this plan document, not in chat todo lists.

---

## Execution Plan

### Phase 1 — Implement deletion logic

**Intent**: Insert the `sync-install` ConfigMap deletion block immediately before the `launchInstallPipeline` call.

**Expected Outcomes**:
- On a re-run, the stale `sync-install` ConfigMap is deleted before the pipeline starts.
- If the ConfigMap does not exist (first run), the deletion attempt is silently skipped and a `logger.debug` note is recorded.
- The user sees a Halo spinner step confirming the cleanup attempt.
- No imports are added; no other files are changed.

**Todo List**:
- [ ] **1.1** Open `python/src/mas/cli/install/app.py` and locate the `with Halo(text=f"Submitting PipelineRun..."` block (around line 3167).
- [ ] **1.2** Insert the following block immediately before that `with Halo(...)` block:

```python
with Halo(text=f"Clearing stale sync-install ConfigMap in {pipelinesNamespace}", spinner=self.spinner) as h:
    cmAPI = self.dynamicClient.resources.get(api_version="v1", kind="ConfigMap")
    try:
        logger.debug(f"Deleting sync-install ConfigMap in namespace {pipelinesNamespace} before launching install pipeline")
        cmAPI.delete(name="sync-install", namespace=pipelinesNamespace)
        h.stop_and_persist(symbol=self.successIcon, text=f"Deleted stale sync-install ConfigMap in {pipelinesNamespace}")
    except NotFoundError:
        logger.debug(f"sync-install ConfigMap not found in {pipelinesNamespace}, nothing to delete")
        h.stop_and_persist(symbol=self.successIcon, text=f"No stale sync-install ConfigMap found in {pipelinesNamespace}")
```

- [ ] **1.3** Verify the indentation and surrounding structure are correct.

**Relevant Context**:
- File: `python/src/mas/cli/install/app.py`
- Insertion point: between line 3165 (`h.stop_and_persist(... "Latest Tekton definitions..."`)  and line 3167 (`with Halo(... "Submitting PipelineRun..."`)
- `NotFoundError` already imported at line 20
- `logger` already defined at line 78
- `pipelinesNamespace` already in scope (line 3059)
- `self.dynamicClient` already in scope throughout this method

**Status**: `[x] done`

---

## Final Validation

1. Run flake8 on the modified file: `flake8 python/src/mas/cli/install/app.py`
2. Run black format check: `black --line-length 160 --check python/src/mas/cli/install/app.py`
3. Confirm no new imports were added.
4. Confirm the modified region looks correct by re-reading lines 3160–3185 of the file.
