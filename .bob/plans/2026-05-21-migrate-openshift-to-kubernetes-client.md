# Migrate from openshift to Kubernetes Python Client

## Objective

Replace the `openshift` package with the official `kubernetes` Python client's `DynamicClient` in the MAS CLI codebase to ensure better maintenance, broader community support, and eliminate dependency on the OpenShift-specific client library.

## Critical Rules

- Maintain backward compatibility - all function signatures must remain unchanged
- All existing tests must pass without modification
- No `.apply()` method usage found in CLI codebase (simpler migration than python-devops)
- Validate with `black` and `flake8` after each code change
- Update copyright headers to 2026 where files are modified
- Test incrementally - validate each file after refactoring
- The CLI depends on `mas-devops >= 5.2.0` which must be migrated first

## Execution Plan

### Phase 1: Analysis and Preparation

- [ ] **1.1** Document all usage patterns of `openshift.dynamic`
  - [ ] `DynamicClient` instantiation (4 files: cli.py, validators.py, 2 test helpers)
  - [ ] Exception types: `NotFoundError`, `ResourceNotFoundError`
  - [ ] No `.apply()` calls found (unlike python-devops)
  - [ ] Import in validators.py has comment about needing apply (line 16-17)

- [ ] **1.2** Verify mas-devops dependency status
  - [ ] Confirm mas-devops has completed openshift → kubernetes migration
  - [ ] Update mas-devops version requirement if needed

- [ ] **1.3** Validate Phase 1
  - [ ] All openshift usage patterns documented
  - [ ] Dependency chain understood

### Phase 2: Update Dependencies

- [ ] **2.1** Update [`python/setup.py`](python/setup.py:60) dependencies
  - [ ] Remove `'openshift'` from install_requires (line 60)
  - [ ] Ensure `'kubernetes == 33.1.0'` remains (line 61)
  - [ ] Update mas-devops version if needed (line 56)

- [ ] **2.2** Update copyright header in setup.py
  - [ ] Change copyright year from 2024 to 2024, 2026

- [ ] **2.3** Validate Phase 2
  - [ ] Run `python setup.py check`
  - [ ] Verify no syntax errors

### Phase 3: Update Source Code Imports

- [ ] **3.1** Update [`python/src/mas/cli/validators.py`](python/src/mas/cli/validators.py:17)
  - [ ] Replace `from openshift import dynamic` with `from kubernetes import dynamic`
  - [ ] Remove or update comment about needing apply (line 16)
  - [ ] Update copyright header to include 2026

- [ ] **3.2** Update [`python/src/mas/cli/cli.py`](python/src/mas/cli/cli.py:28-29)
  - [ ] Replace `from openshift.dynamic import DynamicClient` with `from kubernetes.dynamic import DynamicClient`
  - [ ] Replace `from openshift.dynamic.exceptions import NotFoundError` with `from kubernetes.dynamic.exceptions import NotFoundError`
  - [ ] Update copyright header to include 2026

- [ ] **3.3** Update [`python/src/mas/cli/install/app.py`](python/src/mas/cli/install/app.py:20)
  - [ ] Replace `from openshift.dynamic.exceptions import NotFoundError` with `from kubernetes.dynamic.exceptions import NotFoundError`
  - [ ] Update copyright header to include 2026

- [ ] **3.4** Update [`python/src/mas/cli/install/settings/manageSettings.py`](python/src/mas/cli/install/settings/manageSettings.py:15,26)
  - [ ] Replace `from openshift.dynamic.exceptions import ResourceNotFoundError` with `from kubernetes.dynamic.exceptions import ResourceNotFoundError`
  - [ ] Replace `from openshift.dynamic import DynamicClient` (TYPE_CHECKING block) with `from kubernetes.dynamic import DynamicClient`
  - [ ] Update copyright header to include 2026

- [ ] **3.5** Update [`python/src/mas/cli/install/summarizer.py`](python/src/mas/cli/install/summarizer.py:26)
  - [ ] Replace `from openshift.dynamic import DynamicClient` (TYPE_CHECKING block) with `from kubernetes.dynamic import DynamicClient`
  - [ ] Update copyright header to include 2026

- [ ] **3.6** Update [`python/src/mas/cli/update/app.py`](python/src/mas/cli/update/app.py:19)
  - [ ] Replace `from openshift.dynamic.exceptions import NotFoundError, ResourceNotFoundError` with `from kubernetes.dynamic.exceptions import NotFoundError, ResourceNotFoundError`
  - [ ] Update copyright header to include 2026

- [ ] **3.7** Update [`python/src/mas/cli/uninstall/app.py`](python/src/mas/cli/uninstall/app.py:18)
  - [ ] Replace `from openshift.dynamic.exceptions import NotFoundError, ResourceNotFoundError` with `from kubernetes.dynamic.exceptions import NotFoundError, ResourceNotFoundError`
  - [ ] Update copyright header to include 2026

- [ ] **3.8** Update [`python/src/mas/cli/backup/app.py`](python/src/mas/cli/backup/app.py:18)
  - [ ] Replace `from openshift.dynamic.exceptions import ResourceNotFoundError` with `from kubernetes.dynamic.exceptions import ResourceNotFoundError`
  - [ ] Update copyright header to include 2026

- [ ] **3.9** Update [`python/src/mas/cli/aiservice/install/app.py`](python/src/mas/cli/aiservice/install/app.py:20)
  - [ ] Replace `from openshift.dynamic.exceptions import NotFoundError` with `from kubernetes.dynamic.exceptions import NotFoundError`
  - [ ] Update copyright header to include 2026

- [ ] **3.10** Update [`python/src/mas/cli/aiservice/upgrade/app.py`](python/src/mas/cli/aiservice/upgrade/app.py:27)
  - [ ] Replace `from openshift.dynamic.exceptions import ResourceNotFoundError` with `from kubernetes.dynamic.exceptions import ResourceNotFoundError`
  - [ ] Update copyright header to include 2026

- [ ] **3.11** Validate Phase 3
  - [ ] Run `wsl bash -lc "black python/src/mas/cli/*.py python/src/mas/cli/**/*.py"`
  - [ ] Run `wsl bash -lc "flake8 python/src/mas/cli/*.py python/src/mas/cli/**/*.py"`
  - [ ] Verify no import errors

### Phase 4: Update Test Code Imports

- [ ] **4.1** Update [`python/test/utils/install_test_helper.py`](python/test/utils/install_test_helper.py:18-19)
  - [ ] Replace `from openshift.dynamic import DynamicClient` with `from kubernetes.dynamic import DynamicClient`
  - [ ] Replace `from openshift.dynamic.exceptions import NotFoundError` with `from kubernetes.dynamic.exceptions import NotFoundError`
  - [ ] Update copyright header to include 2026

- [ ] **4.2** Update [`python/test/utils/update_test_helper.py`](python/test/utils/update_test_helper.py:18)
  - [ ] Replace `from openshift.dynamic import DynamicClient` with `from kubernetes.dynamic import DynamicClient`
  - [ ] Update copyright header to include 2026

- [ ] **4.3** Update [`python/test/aiservice/install/test_app.py`](python/test/aiservice/install/test_app.py:16-17)
  - [ ] Replace `from openshift.dynamic import DynamicClient` with `from kubernetes.dynamic import DynamicClient`
  - [ ] Replace `from openshift.dynamic.exceptions import NotFoundError` with `from kubernetes.dynamic.exceptions import NotFoundError`
  - [ ] Update copyright header to include 2026

- [ ] **4.4** Validate Phase 4
  - [ ] Run `wsl bash -lc "black python/test/**/*.py"`
  - [ ] Run `wsl bash -lc "flake8 python/test/**/*.py"`
  - [ ] Verify no syntax errors

### Phase 5: Testing

- [ ] **5.1** Run existing test suite
  - [ ] Run `wsl bash -lc "cd python && pytest test/ -v"`
  - [ ] Document any failures and root cause
  - [ ] Fix any issues found

- [ ] **5.2** Validate Phase 5
  - [ ] All existing tests pass
  - [ ] No regressions detected

### Phase 6: Final Validation

- [ ] **6.1** Code quality checks
  - [ ] Run `wsl bash -lc "black python/src/mas/cli/*.py python/src/mas/cli/**/*.py python/test/**/*.py"`
  - [ ] Run `wsl bash -lc "flake8 python/src/mas/cli/*.py python/src/mas/cli/**/*.py python/test/**/*.py"`
  - [ ] Verify no violations

- [ ] **6.2** Dependency verification
  - [ ] Run `python python/setup.py check`
  - [ ] Verify `openshift` is not in dependencies
  - [ ] Verify `kubernetes` is in dependencies
  - [ ] Verify mas-devops version is correct

- [ ] **6.3** Documentation review
  - [ ] All copyright headers include 2026
  - [ ] No references to openshift package remain
  - [ ] Comment in validators.py about apply is updated/removed

## Implementation Details

### Files Requiring Changes

**Source Code (10 files):**
1. [`python/src/mas/cli/validators.py`](python/src/mas/cli/validators.py:17) - Main import + comment
2. [`python/src/mas/cli/cli.py`](python/src/mas/cli/cli.py:28-29) - DynamicClient + NotFoundError
3. [`python/src/mas/cli/install/app.py`](python/src/mas/cli/install/app.py:20) - NotFoundError
4. [`python/src/mas/cli/install/settings/manageSettings.py`](python/src/mas/cli/install/settings/manageSettings.py:15,26) - ResourceNotFoundError + TYPE_CHECKING
5. [`python/src/mas/cli/install/summarizer.py`](python/src/mas/cli/install/summarizer.py:26) - TYPE_CHECKING
6. [`python/src/mas/cli/update/app.py`](python/src/mas/cli/update/app.py:19) - Both exceptions
7. [`python/src/mas/cli/uninstall/app.py`](python/src/mas/cli/uninstall/app.py:18) - Both exceptions
8. [`python/src/mas/cli/backup/app.py`](python/src/mas/cli/backup/app.py:18) - ResourceNotFoundError
9. [`python/src/mas/cli/aiservice/install/app.py`](python/src/mas/cli/aiservice/install/app.py:20) - NotFoundError
10. [`python/src/mas/cli/aiservice/upgrade/app.py`](python/src/mas/cli/aiservice/upgrade/app.py:27) - ResourceNotFoundError

**Test Code (3 files):**
1. [`python/test/utils/install_test_helper.py`](python/test/utils/install_test_helper.py:18-19)
2. [`python/test/utils/update_test_helper.py`](python/test/utils/update_test_helper.py:18)
3. [`python/test/aiservice/install/test_app.py`](python/test/aiservice/install/test_app.py:16-17)

**Configuration (1 file):**
1. [`python/setup.py`](python/setup.py:60) - Remove openshift dependency

### Import Replacement Patterns

**Pattern 1: DynamicClient only**
```python
# Before
from openshift.dynamic import DynamicClient

# After
from kubernetes.dynamic import DynamicClient
```

**Pattern 2: NotFoundError only**
```python
# Before
from openshift.dynamic.exceptions import NotFoundError

# After
from kubernetes.dynamic.exceptions import NotFoundError
```

**Pattern 3: ResourceNotFoundError only**
```python
# Before
from openshift.dynamic.exceptions import ResourceNotFoundError

# After
from kubernetes.dynamic.exceptions import ResourceNotFoundError
```

**Pattern 4: Both exceptions**
```python
# Before
from openshift.dynamic.exceptions import NotFoundError, ResourceNotFoundError

# After
from kubernetes.dynamic.exceptions import NotFoundError, ResourceNotFoundError
```

**Pattern 5: Dynamic module (validators.py)**
```python
# Before
from openshift import dynamic

# After
from kubernetes import dynamic
```

### Special Considerations

1. **No apply() usage**: Unlike python-devops, the CLI codebase does not use `.apply()` method, making this migration simpler
2. **Comment in validators.py**: Line 16-17 mentions using openshift for apply access - this comment should be removed or updated
3. **Dependency on mas-devops**: The CLI requires `mas-devops >= 5.2.0` which must complete its migration first
4. **TYPE_CHECKING blocks**: Two files use TYPE_CHECKING imports that also need updating

## Validation

### Success Criteria

1. **Dependency removed**: `openshift` no longer in [`python/setup.py`](python/setup.py:60)
2. **Imports updated**: All 13 files use `kubernetes.dynamic` instead of `openshift.dynamic`
3. **Code quality**: All files pass `black` and `flake8` validation
4. **Tests pass**: All existing tests pass without modification
5. **Copyright updated**: Modified files have 2026 in copyright header
6. **Comment updated**: validators.py comment about apply is removed/updated

### Commands to Run

```bash
# Code formatting and linting
wsl bash -lc "black python/src/mas/cli/*.py python/src/mas/cli/**/*.py python/test/**/*.py"
wsl bash -lc "flake8 python/src/mas/cli/*.py python/src/mas/cli/**/*.py python/test/**/*.py"

# Run all tests
wsl bash -lc "cd python && pytest test/ -v"

# Verify setup.py
python python/setup.py check
```

### Expected Results

- Black: No files reformatted
- Flake8: No violations
- Pytest: All tests pass
- Setup.py: No errors, `openshift` not in dependencies