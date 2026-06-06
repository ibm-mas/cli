# Must-Gather Migration Bug Fixes

## Objective

Fix two bugs in the Python must-gather migration:

1. **SLS Collector Output Path Bug**: Files are being written to `testing/.../resources/resources/sls-fvtcore` instead of `testing/.../resources/sls-fvtcore` (double "resources" issue)

2. **Index Generation Format Bug**: Pod and secret indexes are being generated as `.txt` files instead of `.md` (markdown) files, and the pods index needs special handling to include both pod YAML files and pod log files

## Design Decisions

### Root Cause Analysis

**Bug 1: SLS Double Resources Path**
- In [`dependencies/utils.py:93`](python/src/mas/cli/must_gather/dependencies/utils.py:93), `collectFromNamespaces()` passes `outputDir` directly to `genericMustGather()`
- In [`dependencies/sls.py:43`](python/src/mas/cli/must_gather/dependencies/sls.py:43), `collectSLS()` calls `collectFromNamespaces()` with `outputDir` parameter
- The `genericMustGather()` function in [`app.py:312`](python/src/mas/cli/must_gather/app.py:312) appends `/resources` to the outputDir
- This creates the path: `{outputDir}/resources/{namespace}` where outputDir already contains `/resources`
- Result: `testing/.../resources/resources/sls-fvtcore`

**Bug 2: Index File Extensions**
- In [`common/pods.py:69`](python/src/mas/cli/must_gather/common/pods.py:69), pods summary is written as `pods.txt`
- In [`common/secrets.py:73`](python/src/mas/cli/must_gather/common/secrets.py:73), secrets summary is written as `secrets.txt`
- The new Python implementation uses markdown tables (via [`common/resources.py:125`](python/src/mas/cli/must_gather/common/resources.py:125) `_writeMarkdownIndex()`)
- Pods and secrets should follow the same pattern as other resources and use `.md` extension
- The pods index needs to include links to both pod YAML files AND pod log files (when logs are collected)

### Solution Design

**Bug 1 Solution:**
- Modify [`dependencies/sls.py`](python/src/mas/cli/must_gather/dependencies/sls.py) `collectSLS()` to NOT use `collectFromNamespaces()` utility
- Instead, directly call `collectSLSNamespace()` for each discovered namespace
- This matches the pattern used in [`app.py:612-623`](python/src/mas/cli/must_gather/app.py:612-623) where SLS collection is already handled correctly

**Bug 2 Solution:**
- Change [`common/pods.py:69`](python/src/mas/cli/must_gather/common/pods.py:69) from `pods.txt` to `pods.md`
- Change [`common/secrets.py:73`](python/src/mas/cli/must_gather/common/secrets.py:73) from `secrets.txt` to `secrets.md`
- Refactor `_writeSummary()` functions to use markdown table format (similar to `_writeMarkdownIndex()`)
- For pods: Create a special markdown index that includes:
  - Links to pod YAML files in the `pods/{app}/` subdirectories
  - Links to pod log files in the `pods/{app}/logs/` subdirectories (when logs exist)
  - Use a table format with columns: NAME, READY, STATUS, RESTARTS, AGE, YAML, LOGS

## Critical Rules

1. **Preserve all existing functionality** - No changes to collection logic, only output paths and file formats
2. **Maintain backward compatibility** - Ensure web viewer can still read the new markdown format
3. **Follow existing patterns** - Use `_writeMarkdownIndex()` style for consistency with other resources
4. **Test thoroughly** - Validate both bugs are fixed and no regressions introduced
5. **Track progress ONLY in this plan document** - Do NOT use chat todo lists or `update_todo_list` tool

## Execution Plan

### Phase 1: Fix SLS Double Resources Path Bug

**Objective:** Eliminate the double "resources" directory in SLS output paths

[ ] **1.1** Read and analyze current SLS collection flow
  - [ ] Review [`dependencies/sls.py`](python/src/mas/cli/must_gather/dependencies/sls.py) `collectSLS()` function
  - [ ] Review [`dependencies/utils.py`](python/src/mas/cli/must_gather/dependencies/utils.py) `collectFromNamespaces()` function
  - [ ] Review how [`app.py`](python/src/mas/cli/must_gather/app.py) calls `collectSLS()`

[ ] **1.2** Modify [`dependencies/sls.py`](python/src/mas/cli/must_gather/dependencies/sls.py)
  - [ ] Remove the `collectSLS()` function that uses `collectFromNamespaces()`
  - [ ] The function is already correctly implemented in [`app.py:578-624`](python/src/mas/cli/must_gather/app.py:578-624)
  - [ ] Verify that `collectSLSNamespace()` is called directly for each namespace

[ ] **1.3** Validate the fix
  - [ ] Run must-gather collection with SLS
  - [ ] Verify output path is `testing/.../resources/sls-{namespace}` (single "resources")
  - [ ] Confirm no "resources/resources" double directory

### Phase 2: Fix Index Generation Format Bug

**Objective:** Convert pods and secrets indexes from `.txt` to `.md` with markdown table format

[ ] **2.1** Update secrets index generation
  - [ ] Modify [`common/secrets.py:73`](python/src/mas/cli/must_gather/common/secrets.py:73) to use `secrets.md` instead of `secrets.txt`
  - [ ] Refactor `_writeSummary()` to `_writeMarkdownIndex()` using markdown table format
  - [ ] Include columns: NAME, NAMESPACE, TYPE
  - [ ] Add markdown link in NAME column pointing to `secrets/{name}.yaml`

[ ] **2.2** Update pods index generation
  - [ ] Modify [`common/pods.py:69`](python/src/mas/cli/must_gather/common/pods.py:69) to use `pods.md` instead of `pods.txt`
  - [ ] Refactor `_writeSummary()` to `_writeMarkdownIndex()` using markdown table format
  - [ ] Include columns: NAME, READY, STATUS, RESTARTS, AGE, YAML, LOGS
  - [ ] Add markdown link in YAML column pointing to `pods/{app}/{name}.yaml`
  - [ ] Add markdown link in LOGS column pointing to `pods/{app}/logs/` (only if logs exist)
  - [ ] Handle cases where logs don't exist (show empty or "N/A")

[ ] **2.3** Validate the fix
  - [ ] Run must-gather collection with pods and secrets
  - [ ] Verify `pods.md` and `secrets.md` files are created (not `.txt`)
  - [ ] Verify markdown table format is correct
  - [ ] Verify links work correctly in web viewer
  - [ ] Test with and without pod logs collection

### Phase 3: Final Validation

**Objective:** Comprehensive testing to ensure both bugs are fixed and no regressions

[ ] **3.1** Run full must-gather collection
  - [ ] Execute: `mas-cli must-gather --directory testing`
  - [ ] Verify SLS resources are in correct path (single "resources")
  - [ ] Verify all namespace indexes use `.md` format
  - [ ] Check pods.md includes both YAML and log links

[ ] **3.2** Test web viewer compatibility
  - [ ] Launch web viewer: `mas-cli must-gather serve --dir testing/must-gather/{timestamp}`
  - [ ] Navigate to SLS namespace and verify resources display correctly
  - [ ] Navigate to pods.md and verify links work
  - [ ] Navigate to secrets.md and verify links work
  - [ ] Verify markdown rendering is correct

[ ] **3.3** Run Python tests
  - [ ] Execute: `.venv/bin/pytest python/tests/must_gather/`
  - [ ] Verify all tests pass
  - [ ] Add new tests if needed for the fixes

[ ] **3.4** Code quality checks
  - [ ] Run: `black python/src/mas/cli/must_gather/`
  - [ ] Run: `flake8 python/src/mas/cli/must_gather/`
  - [ ] Fix any formatting or linting issues

## Final Validation

**Success Criteria:**
1. SLS resources are collected to `testing/.../resources/sls-{namespace}` (no double "resources")
2. All namespace indexes use `.md` extension (pods.md, secrets.md)
3. Markdown tables render correctly with working links
4. Pods index includes both YAML and log file links
5. Web viewer displays all content correctly
6. All existing tests pass
7. Code passes black and flake8 checks

**Commands to Run:**
```bash
# Test collection
mas-cli must-gather --directory testing

# Verify paths
ls -la testing/must-gather/*/resources/
ls -la testing/must-gather/*/resources/sls-*/

# Check file extensions
find testing/must-gather/*/resources -name "*.txt" -o -name "*.md" | grep -E "(pods|secrets)"

# Test web viewer
mas-cli must-gather serve --dir testing/must-gather/{timestamp}

# Run tests
.venv/bin/pytest python/tests/must_gather/

# Code quality
black python/src/mas/cli/must_gather/
flake8 python/src/mas/cli/must_gather/