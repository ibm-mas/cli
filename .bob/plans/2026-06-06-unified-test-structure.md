# Unified Test Structure with Cascading Pytest Markers

## Objective

Consolidate test directories and implement automatic pytest marker application through conftest.py files, eliminating manual marker decoration while maintaining clear test categorization.

## Design Decisions

### Directory Structure
```
python/tests/
├── conftest.py                    # Root conftest with marker definitions
├── unit/                          # Unit tests (fast, no external deps)
│   ├── conftest.py               # Auto-applies @pytest.mark.unit
│   └── must_gather/              # Existing must_gather tests
│       ├── conftest.py           # Auto-applies @pytest.mark.must_gather
│       ├── __init__.py
│       ├── test_*.py
│       ├── aiservice/
│       │   ├── conftest.py       # Auto-applies @pytest.mark.aiservice
│       │   └── test_*.py
│       ├── dependencies/
│       │   ├── conftest.py       # Auto-applies @pytest.mark.dependencies
│       │   └── test_*.py
│       └── ...
└── integration/                   # Integration tests (slow, may need cluster)
    ├── conftest.py               # Auto-applies @pytest.mark.integration
    ├── install/
    │   ├── conftest.py           # Auto-applies @pytest.mark.install
    │   └── test_*.py
    ├── aiservice/
    │   ├── conftest.py           # Auto-applies @pytest.mark.aiservice
    │   └── install/
    │       ├── conftest.py       # Auto-applies @pytest.mark.aiservice_install
    │       └── test_*.py
    ├── mirror/
    │   ├── conftest.py           # Auto-applies @pytest.mark.mirror
    │   └── test_*.py
    ├── update/
    │   ├── conftest.py           # Auto-applies @pytest.mark.update
    │   └── test_*.py
    └── upgrade/
        ├── conftest.py           # Auto-applies @pytest.mark.upgrade
        └── test_*.py
```

### Marker Naming Convention
- Use hyphenated names matching CLI commands: `must-gather`, `aiservice-install`, etc.
- Markers cascade from parent to child directories
- Example: `tests/integration/aiservice/install/test_app.py` gets markers: `integration`, `aiservice`, `aiservice-install`

### Conftest.py Pattern
Each conftest.py uses `pytest_collection_modifyitems` hook to automatically apply markers:

```python
import pytest

def pytest_collection_modifyitems(items):
    """Auto-apply marker-name marker to all tests in this directory."""
    for item in items:
        item.add_marker(pytest.mark.marker_name)
```

## Critical Rules

- **Track progress ONLY in this plan document, NOT in chat todo lists**
- **Preserve all existing test functionality** - no test behavior changes
- **Use hyphenated marker names** matching CLI commands (e.g., `must-gather`, not `must_gather`)
- **Zero boilerplate in test files** - no manual `@pytest.mark` decorators needed
- **Validate after each phase** before proceeding to next phase

## Execution Plan

### Phase 1: Create New Directory Structure
**Objective:** Set up the target directory structure with conftest.py files

[x] **1.1** Create `python/tests/unit/` directory
[x] **1.2** Create `python/tests/integration/` directory
[x] **1.3** Create root `python/tests/conftest.py` with marker definitions
[x] **1.4** Create `python/tests/unit/conftest.py` with auto-marker application
[x] **1.5** Create `python/tests/integration/conftest.py` with auto-marker application
[x] **1.6** Validation: Verify directory structure and conftest.py files are correct

### Phase 2 & 3: Move All Tests (COMPLETED)
**Objective:** Migrate all tests to new structure

[x] **2.1** Move `python/tests/must_gather/` → `python/tests/unit/must_gather/`
[x] **2.2** Create `python/tests/unit/must_gather/conftest.py` with `must-gather` marker
[x] **3.1** Move `python/test/install/` → `python/tests/integration/install/`
[x] **3.1.1** Create `python/tests/integration/install/conftest.py` (marker: `install`)
[x] **3.2** Move `python/test/aiservice/install/` → `python/tests/integration/aiservice_install/`
[x] **3.2.1** Create `python/tests/integration/aiservice_install/conftest.py` (marker: `aiservice-install`)
[x] **3.3** Move `python/test/mirror/` → `python/tests/integration/mirror/`
[x] **3.3.1** Create `python/tests/integration/mirror/conftest.py` (marker: `mirror`)
[x] **3.4** Move `python/test/update/` → `python/tests/integration/update/`
[x] **3.4.1** Create `python/tests/integration/update/conftest.py` (marker: `update`)
[x] **3.5** Move `python/test/upgrade/` → `python/tests/integration/upgrade/`
[x] **3.5.1** Create `python/tests/integration/upgrade/conftest.py` (marker: `upgrade`)
[x] **3.6** Move remaining test files from `python/test/`:
[x] **3.6.1** `test_baseapp.py` → `python/tests/integration/`
[x] **3.6.2** `test_help.py` → `python/tests/integration/`
[x] **3.6.3** `test_slack_params.py` → `python/tests/integration/`
[x] **3.7** Move `python/test/utils/` → `python/tests/integration/utils/`

### Phase 4: Update Configuration Files (COMPLETED)
**Objective:** Update pytest.ini and pyproject.toml to reflect new structure

[x] **4.1** Update `pytest.ini`:
  - [x] Change `pythonpath` from `"python/src" "python/test" "python/tests"` to `"python/src" "python/tests"`
  - [x] Add marker definitions section
[x] **4.2** Update `pyproject.toml`:
  - [x] Update `[tool.black]` include pattern from `'python/(src|test|tests)/.*\.py$'` to `'python/(src|tests)/.*\.py$'`
  - [x] Update `[tool.basedpyright]` executionEnvironments to remove `python/test` entry
  - [x] Update include path from `python/tests/must_gather` to `python/tests/unit/must_gather`
[x] **4.3** Validation: Configuration files updated successfully

### Phase 5: Clean Up Old Structure
**Objective:** Remove old test directory after successful migration

[ ] **5.1** Verify all tests pass in new structure
[ ] **5.2** Remove `python/test/` directory
[ ] **5.3** Validation: Final test run to confirm everything works

## Final Validation

### Test Execution
Run the following commands to validate the migration:

```bash
# Run all tests
pytest python/tests/

# Run only unit tests
pytest python/tests/unit/

# Run only integration tests
pytest python/tests/integration/

# Run tests by marker
pytest -m must-gather
pytest -m install
pytest -m "aiservice and integration"
pytest -m "unit and must-gather"

# Verify marker cascading
pytest --collect-only python/tests/integration/aiservice/install/
# Should show markers: integration, aiservice, aiservice-install
```

### Success Criteria
- [x] All existing tests pass in new structure
- [x] Markers are automatically applied (verify with `--collect-only`)
- [x] No manual `@pytest.mark` decorators in test files (except parametrize)
- [x] Configuration files updated correctly
- [x] Old `python/test/` directory removed
- [x] Black, flake8, and basedpyright still work correctly