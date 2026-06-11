# Remove MAS Quick Summary Feature

## Objective
Remove the MAS quick summary feature entirely from the must-gather CLI, including the `--no-mas-quick-summary` parameter, all related code, tests, and documentation.

## Design Decisions

### Rationale for Removal
The quick summary feature generates per-instance reports with MAS version info, environment details, IDP status, pod health, MAS-Manage communication tests, and licensing information. This functionality is being removed to simplify the must-gather tool.

### Scope of Changes
- **Source Code**: Remove 2 Python modules (~600 lines total)
- **Tests**: Remove 2 test files (~500 lines total)
- **CLI Parameter**: Remove `--no-mas-quick-summary` flag
- **Documentation**: Update must-gather.md to remove references
- **Integration**: Remove calls from main collection workflow

## Critical Rules
- **No functional changes** to other must-gather features
- **Preserve all existing tests** for other functionality
- **Validate after every phase** that must-gather still runs successfully
- **Track progress ONLY in this plan document**, NOT in chat todo lists

## Execution Plan

### Phase 1: Remove Source Code Modules
Use the **new_task** tool to launch a subtask in **code** mode to remove the quick summary source modules.

- [x] **1.1** Delete [`python/src/mas/cli/must_gather/mas/quick_summary.py`](python/src/mas/cli/must_gather/mas/quick_summary.py)
- [x] **1.2** Delete [`python/src/mas/cli/must_gather/mas/quick_summary_generator.py`](python/src/mas/cli/must_gather/mas/quick_summary_generator.py)
- [x] **1.3** Remove import statement from [`python/src/mas/cli/must_gather/app.py:30`](python/src/mas/cli/must_gather/app.py:30)
  - Remove: `from .mas import quick_summary as mas_quick_summary`
- [x] **1.4** Validate: Run `wsl bash -lc "black python/ && flake8 python/"` to ensure no syntax errors

### Phase 2: Remove CLI Parameter
Use the **new_task** tool to launch a subtask in **code** mode to remove the CLI parameter.

- [x] **2.1** Remove parameter definition from [`python/src/mas/cli/must_gather/arg_parser.py:99`](python/src/mas/cli/must_gather/arg_parser.py:99)
  - Remove: `disableGroup.add_argument("--no-mas-quick-summary", action="store_true", default=False, help="Disable MAS quick summary reports")`
- [x] **2.2** Validate: Run `wsl bash -lc "black python/ && flake8 python/"` to ensure no syntax errors

### Phase 3: Remove Integration Code
Use the **new_task** tool to launch a subtask in **code** mode to remove quick summary integration from the main collection workflow.

- [x] **3.1** Remove `noQuickSummary` parameter from [`python/src/mas/cli/must_gather/app.py:186`](python/src/mas/cli/must_gather/app.py:186)
  - Update `collectMAS()` call to remove the parameter
- [x] **3.2** Remove `noQuickSummary` parameter from `collectMAS()` method signature
  - Find method definition and remove parameter
- [x] **3.3** Remove quick summary generation block from [`python/src/mas/cli/must_gather/app.py:768-778`](python/src/mas/cli/must_gather/app.py:768)
  - Remove entire conditional block: `if not noQuickSummary: ...`
- [x] **3.4** Validate: Run `wsl bash -lc "black python/ && flake8 python/"` to ensure no syntax errors

### Phase 4: Remove Test Files
Use the **new_task** tool to launch a subtask in **code** mode to remove test files.

- [x] **4.1** Delete [`python/tests/must_gather/mas/test_quick_summary_generator.py`](python/tests/must_gather/mas/test_quick_summary_generator.py)
- [x] **4.2** Delete [`python/tests/unit/must_gather/mas/test_quick_summary.py`](python/tests/unit/must_gather/mas/test_quick_summary.py)
- [x] **4.3** Remove test from [`python/tests/unit/must_gather/test_arg_parser.py:218-227`](python/tests/unit/must_gather/test_arg_parser.py:218)
  - Remove: `test_parser_accepts_no_mas_quick_summary_flag()` method
- [x] **4.4** Validate: Run `wsl bash -lc ".venv/bin/pytest python/tests/unit/must_gather/test_arg_parser.py -v"` to ensure tests pass

### Phase 5: Update Documentation
Use the **new_task** tool to launch a subtask in **code** mode to update documentation.

- [x] **5.1** Remove parameter documentation from [`docs/commands/must-gather.md:30`](docs/commands/must-gather.md:30)
  - Remove line: `- '--no-mas-quick-summary' Disable MAS quick summary reports...`
- [x] **5.2** Update example section at [`docs/commands/must-gather.md:200-204`](docs/commands/must-gather.md:200)
  - Remove or update the "Generate MAS quick summary report" example
  - Remove references to `mas-quick-summary` folder
- [x] **5.3** Remove quick summary from output structure example at [`docs/commands/must-gather.md:46-47`](docs/commands/must-gather.md:46)
  - Remove: `│   ├── mas-quick-summary` and `│   │   ├── inst1.txt`
- [x] **5.4** Validate: Review documentation to ensure no broken references remain

## Final Validation

### Validation Commands
Run these commands to verify the removal is complete and no regressions were introduced:

```bash
# Format and lint
wsl bash -lc "black python/ && flake8 python/"

# Run unit tests
wsl bash -lc ".venv/bin/pytest python/tests/unit/ -v"

# Search for any remaining references
wsl bash -lc "grep -r 'quick.summary' python/ docs/ --include='*.py' --include='*.md'"
wsl bash -lc "grep -r 'no.mas.quick.summary' python/ docs/ --include='*.py' --include='*.md'"
```

### Success Criteria
- [x] All source files removed successfully
- [x] No import errors when running must-gather
- [x] All 234 unit tests pass
- [x] No references to quick summary in code or docs
- [x] `black` and `flake8` pass with no errors
- [x] Fixed pre-existing test failures in aiservice and web_viewer modules