# Must-Gather Collectors Flag Refactoring Plan

## Objective

Refactor the must-gather CLI to replace multiple boolean disable flags (`--summary-only`, `--pods-only`, `--no-ocp`, `--no-dependencies`, `--no-sls`) with a single `--collectors` flag that provides granular control over which collectors are enabled.

## Design Decisions

### New `--collectors` Flag Design

**Accepted collectors:**
- `ocp` - OpenShift Container Platform resources
- `db2` - Db2 database instances
- `kafka` - Kafka/Strimzi instances
- `mongodb` - MongoDB instances (part of dependencies)
- `cp4d` - Cloud Pak for Data
- `cert-manager` - Certificate Manager
- `grafana` - Grafana instances
- `sls` - IBM Suite License Service
- `mas` - MAS instances (core + apps + pipelines)
- `aiservice` - AI Service instances

**Behavior:**
- Default: All collectors enabled when flag not specified
- Format: Comma-separated list (e.g., `--collectors ocp,mas,sls`)
- Validation: Error if invalid collector name provided
- Case-insensitive matching

### Mapping Old Flags to New Behavior

| Old Flag | Action |
|----------|--------|
| `--no-ocp` | Replace with `--collectors` (omit `ocp` from list) |
| `--no-dependencies` | Replace with `--collectors` (omit `db2,kafka,mongodb,cp4d,cert-manager,grafana`) |
| `--no-sls` | Replace with `--collectors` (omit `sls` from list) |
| `--summary-only` | **Remove completely** - redundant due to performance improvements |
| `--pods-only` | **Remove completely** - redundant due to performance improvements |

### Implementation Strategy

1. **Argument Parser Changes** ([`arg_parser.py`](python/src/mas/cli/must_gather/arg_parser.py))
   - Remove `--no-ocp`, `--no-dependencies`, `--no-sls`, `--summary-only`, `--pods-only` arguments
   - Add `--collectors` argument with default value of all collectors
   - Add validation function for collector names

2. **Collection Plan Logic** ([`app.py`](python/src/mas/cli/must_gather/app.py))
   - Replace `if not parsedArgs.no_dependencies:` checks with collector membership tests
   - Replace `if not parsedArgs.no_ocp:` checks with collector membership tests
   - Remove all `parsedArgs.summary_only` and `parsedArgs.pods_only` logic
   - Create helper function to check if collector is enabled

3. **Backward Compatibility**
   - No backward compatibility needed (breaking change is acceptable for CLI refactoring)
   - Update all documentation to reflect new flag

## Critical Rules

- **TDD Approach**: Write tests BEFORE implementation for each component
- **Remove All Five Flags**: Must remove `--summary-only`, `--pods-only`, `--no-ocp`, `--no-dependencies`, `--no-sls`
- **No Functional Changes for Collectors**: The `--collectors` flag must not change what data is collected, only how collectors are selected
- **Simplification**: Removing `--summary-only` and `--pods-only` simplifies the codebase (no replacement needed)
- **Preserve Existing Tests**: All existing tests must continue to pass (with argument updates)
- **Virtual Environment**: All pytest commands must use `.venv/bin/pytest` wrapped in WSL
- **Track Progress**: Update this plan document with `[x]` after completing each step - do NOT use chat todo lists

## Execution Plan

### Phase 1: Test Infrastructure Setup ✅

Use **new_task** tool with mode "code" to complete this phase.

- [x] **1.1** Create test file [`python/tests/unit/must_gather/test_arg_parser.py`](python/tests/unit/must_gather/test_arg_parser.py)
  - [x] Test default collectors (all enabled)
  - [x] Test custom collectors list parsing
  - [x] Test invalid collector name validation
  - [x] Test case-insensitive collector names
  - [x] Test empty collectors list handling
  - [x] Test whitespace handling in collector names

- [x] **1.2** Create test file [`python/tests/unit/must_gather/test_collectors_integration.py`](python/tests/unit/must_gather/test_collectors_integration.py)
  - [x] Test OCP collector enabled/disabled
  - [x] Test dependencies collectors (db2, kafka, mongodb, cp4d, cert-manager, grafana)
  - [x] Test SLS collector enabled/disabled
  - [x] Test MAS collector enabled/disabled
  - [x] Test AIService collector enabled/disabled
  - [x] Test multiple collectors combination

- [x] **1.3** Run tests to verify they fail (TDD red phase)
  ```bash
  wsl bash -lc ".venv/bin/pytest python/tests/unit/must_gather/test_arg_parser.py::TestCollectorsFlag -v"
  wsl bash -lc ".venv/bin/pytest python/tests/unit/must_gather/test_collectors_integration.py -v"
  ```

**Validation:** ✅ All new tests failed as expected (11 failed in test_arg_parser.py, 23 failed in test_collectors_integration.py)

### Phase 2: Argument Parser Implementation ✅

Use **new_task** tool with mode "code" to complete this phase.

- [x] **2.1** Update [`python/src/mas/cli/must_gather/arg_parser.py`](python/src/mas/cli/must_gather/arg_parser.py)
  - [x] Remove lines 96-98 (`--no-ocp`, `--no-dependencies`, `--no-sls`)
  - [x] Remove `--summary-only` and `--pods-only` arguments
  - [x] Add `--collectors` argument in "General Controls" group
    - Default: `"ocp,db2,kafka,mongodb,cp4d,cert-manager,grafana,sls,mas,aiservice"`
    - Type: `str`
    - Help text explaining comma-separated list and available collectors
  - [x] Create `validateCollectors()` function
    - Parse comma-separated string
    - Strip whitespace
    - Convert to lowercase
    - Validate against allowed collectors
    - Return comma-separated string (preserving spacing pattern)
    - Raise `argparse.ArgumentTypeError` for invalid names

- [x] **2.2** Run argument parser tests
  ```bash
  wsl bash -lc ".venv/bin/pytest python/tests/unit/must_gather/test_arg_parser.py::TestCollectorsFlag -v"
  ```
  ✅ All 13 tests passed

**Validation:** ✅ All argument parser tests pass (Completed 2026-06-09)

**Note:** Integration tests (`test_collectors_integration.py`) are expected to fail at this stage because they test integration with `planCollection()`, which will be updated in Phase 3.

### Phase 3: Collection Plan Logic Implementation ✅

Use **new_task** tool with mode "code" to complete this phase.

- [x] **3.1** Update [`python/src/mas/cli/must_gather/app.py`](python/src/mas/cli/must_gather/app.py)
  - [x] Add helper method `_parseCollectors(collectorsStr: str) -> set` to `MustGatherApp` class
    - Parse comma-separated string
    - Strip whitespace, convert to lowercase
    - Return set of enabled collectors
  - [x] Update `planCollection()` method (lines 223-423)
    - [x] Parse collectors at start: `enabledCollectors = self._parseCollectors(parsedArgs.collectors)`
    - [x] Replace OCP check: `if "ocp" in enabledCollectors:`
    - [x] Add individual collector checks (no grouping):
      - `if "kafka" in enabledCollectors:` for Kafka
      - `if "mongodb" in enabledCollectors:` for MongoDB
      - `if "grafana" in enabledCollectors:` for Grafana
      - `if "cert-manager" in enabledCollectors:` for cert-manager
      - `if "db2" in enabledCollectors:` for DB2
      - `if "cp4d" in enabledCollectors:` for CP4D
    - [x] Replace SLS check: `if "sls" in enabledCollectors:`
    - [x] Add MAS check: `if "mas" in enabledCollectors:`
    - [x] Add AIService check: `if "aiservice" in enabledCollectors:`
  - [x] Update `_collectMustGather()` method (line 173)
    - [x] Replace `if not parsedArgs.no_ocp:` with `if "ocp" in self._parseCollectors(parsedArgs.collectors):`
  - [x] Remove all references to `parsedArgs.summary_only` and `parsedArgs.pods_only` (replaced with `False`)

- [x] **3.2** Run integration tests
  ```bash
  wsl bash -lc ".venv/bin/pytest python/tests/unit/must_gather/test_collectors_integration.py -v"
  ```
  ✅ All 23 integration tests passed

**Validation:** ✅ All integration tests pass (Completed 2026-06-09)

**Note:** 9 tests in `test_arg_parser.py` and `test_app_plan_collection.py` are expected to fail because they still reference the old removed flags. These will be fixed in Phase 4.

### Phase 4: Update Existing Tests ✅

Use **new_task** tool with mode "code" to complete this phase.

- [x] **4.1** Update [`python/tests/unit/must_gather/test_arg_parser.py`](python/tests/unit/must_gather/test_arg_parser.py)
  - [x] Removed `test_parser_accepts_summary_only_flag` (line 85-94)
  - [x] Removed `test_parser_accepts_pods_only_flag` (line 107-116)
  - [x] Removed `test_parser_accepts_no_ocp_flag` (line 173-183)
  - [x] Removed `test_parser_accepts_no_dependencies_flag` (line 185-195)
  - [x] Removed `test_parser_accepts_no_sls_flag` (line 197-207)
  - [x] Updated `test_parser_accepts_multiple_flags_together` to use `--collectors` instead of old flags

- [x] **4.2** Update [`python/tests/unit/must_gather/test_app_plan_collection.py`](python/tests/unit/must_gather/test_app_plan_collection.py)
  - [x] Updated `test_planCollection_creates_collection_plan` to use `collectors` attribute
  - [x] Updated `test_planCollection_discovers_dependencies` to use `collectors` attribute
  - [x] Renamed and updated `test_planCollection_respects_no_dependencies_flag` to `test_planCollection_respects_collectors_without_dependencies`
  - [x] Replaced all Mock object attributes (`no_ocp`, `no_dependencies`, `no_sls`, `summary_only`) with `collectors`

- [x] **4.3** Run full must-gather test suite
  ```bash
  wsl bash -lc ".venv/bin/pytest python/tests/unit/must_gather/ -v"
  ```
  ✅ All 196 tests passed

**Validation:** ✅ All must-gather tests pass (Completed 2026-06-09)

### Phase 5: Documentation Updates

Use **new_task** tool with mode "code" to complete this phase.

- [x] **5.1** Restructure and move must-gather documentation
  - [x] Created new `docs/guides/must-gather.md` using `:::mas-cli-usage` directive
  - [x] Updated examples to use `--collectors` flag instead of old flags
  - [x] Removed old `docs/commands/must-gather.md`
  - [x] Updated `mkdocs.yml` navigation to point to new location
  - [x] Added redirect mapping from old to new location

- [x] **5.2** Search for other documentation references
  - Found references in `docs/commands/must-gather.md` (now moved) and `python/src/mas/cli/must_gather/README.md`

- [x] **5.3** Update module README
  - [x] Updated `python/src/mas/cli/must_gather/README.md` to use `--collectors` flag in examples

- [x] **5.4** Refactor arg_parser to follow standard pattern
  - [x] Removed all helper functions (`createArgumentParser`, `_addCollectArguments`, `_addServeSubparser`)
  - [x] Declared `mustGatherArgParser` directly at module level with all arguments and serve subcommand
  - [x] Updated `app.py` to use `mustGatherArgParser` directly
  - [x] Updated all test files to use `mustGatherArgParser` instead of `createArgumentParser()`
  - [x] Verified all 30 arg_parser tests pass

**Validation:** ✅ Documentation restructured, arg_parser simplified to follow install module pattern, all tests pass (Completed 2026-06-09)

### Phase 6: Code Quality & Validation ✅

Use **new_task** tool with mode "code" to complete this phase.

- [x] **6.1** Run black formatter
  ```bash
  wsl bash -lc "black python/src/mas/cli/must_gather/ python/tests/unit/must_gather/"
  ```
  ✅ 3 files reformatted, 83 files left unchanged

- [x] **6.2** Run flake8 linter
  ```bash
  wsl bash -lc "flake8 python/src/mas/cli/must_gather/ python/tests/unit/must_gather/"
  ```
  ✅ All flake8 violations fixed, clean output

- [x] **6.3** Run complete test suite
  ```bash
  wsl bash -lc ".venv/bin/pytest python/tests/unit/must_gather/ -v"
  ```
  ✅ All 196 tests passed in 28.79s

- [x] **6.4** Manual smoke test
  - [x] Test help output: `wsl bash -lc ".venv/bin/mas-cli must-gather --help"` ✅
  - [x] Test with collectors flag: `wsl bash -lc ".venv/bin/mas-cli must-gather --collectors ocp,mas --help"` ✅
  - Verified `--collectors` flag appears in help with all available collectors listed

**Validation:** ✅ All tests pass, code is formatted and linted, command works correctly (Completed 2026-06-09)

## Final Validation

Before marking this plan complete:

1. **All tests pass**: Run `wsl bash -lc ".venv/bin/pytest python/tests/unit/must_gather/ -v"`
2. **Code quality**: Black and flake8 report no issues
3. **Documentation updated**: All references to old flags removed
4. **Functional equivalence**: New flag provides same functionality as old flags
5. **No regressions**: Existing functionality preserved

## Success Criteria

- [ ] All old flags (`--no-ocp`, `--no-dependencies`, `--no-sls`) removed from code
- [ ] New `--collectors` flag implemented with validation
- [ ] All tests pass (existing + new)
- [ ] Documentation updated with examples
- [ ] Code formatted with black (160 char width)
- [ ] No flake8 violations
- [ ] Test coverage maintained or improved