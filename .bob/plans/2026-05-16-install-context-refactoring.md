# InstallContext Refactoring Plan

## Objective

Introduce a centralized `InstallContext` object to eliminate 60-70% of TYPE_CHECKING boilerplate across install mixins by consolidating scattered state into a single, well-defined interface.

## Critical Rules

- Use `camelCase` for all variable and function names (per `.bob/rules/python/development-guide.md`)
- Use `PascalCase` for class names
- Maintain `params` dict as strings-only for Tekton pipeline parameters
- Introduce NO breaking changes - context works alongside existing attributes initially
- Validate with `black` and `flake8` after each file modification
- Test each mixin conversion independently before proceeding to next
- Update copyright year to 2026 in all modified files

## Execution Plan

### Phase 1: Create InstallContext Foundation ✅

**Objective**: Create context object with zero impact on existing code

- [x] **1.1** Create `python/src/mas/cli/install/context.py`
  - [x] Add copyright header (2026)
  - [x] Import required types (dataclass, field, Optional, Dict, Any, DynamicClient)
  - [x] Define `InstallContext` dataclass with camelCase attributes
  - [x] Include `params: Dict[str, str]` for Tekton parameters
  - [x] Add typed attributes for all CLI state (devMode, showAdvancedOptions, etc.)
  - [x] Implement `getParam(key: str, default: str = "") -> str` method
  - [x] Implement `setParam(key: str, value: str) -> None` method with type validation
  - [x] Implement `getSelectedApps() -> list[str]` helper method
  - [x] Add comprehensive docstrings

- [x] **1.2** Validate context.py
  - [x] Run: `wsl bash -lc "black python/src/mas/cli/install/context.py"`
  - [x] Run: `wsl bash -lc "flake8 python/src/mas/cli/install/context.py"`
  - [x] Verify no errors - Black reformatted, flake8 passed

### Phase 2: Integrate Context into InstallApp ✅

**Objective**: Add context to InstallApp without changing mixin behavior

- [x] **2.1** Modify `python/src/mas/cli/install/app.py`
  - [x] Update copyright year to 2026
  - [x] Import `InstallContext` from `.context`
  - [x] In `install()` method, create `self.context = InstallContext()`
  - [x] Map `self.context.params = self.params` (share same dict reference)
  - [x] Create `syncStateToContext()` helper method
  - [x] Map all boolean flags (devMode → context.devMode, etc.)
  - [x] Map all application flags (installManage → context.installManage, etc.)
  - [x] Map all file paths (localConfigDir → context.localConfigDir, etc.)
  - [x] Map all secrets (additionalConfigsSecret → context.additionalConfigsSecret, etc.)
  - [x] Call syncStateToContext() in interactiveMode() and nonInteractiveMode()
  - [x] Keep existing attributes unchanged (backward compatibility)

- [x] **2.2** Validate app.py changes
  - [x] Run: `wsl bash -lc "black python/src/mas/cli/install/app.py"` - Reformatted successfully
  - [x] Run: `wsl bash -lc "flake8 python/src/mas/cli/install/app.py"` - Only pre-existing W503 warnings
  - [x] Verify `mas install --help` still works - Confirmed working

### Phase 3: Convert First Mixin (additionalConfigs)

**Objective**: Prove the pattern with smallest mixin

- [ ] **3.1** Update `python/src/mas/cli/install/settings/additionalConfigs.py`
  - [ ] Update copyright year to 2026
  - [ ] In TYPE_CHECKING block, replace ~75 lines of stubs with:
    ```python
    from ..context import InstallContext
    context: InstallContext
    ```
  - [ ] Keep method stubs (printH1, yesOrNo, etc.) - only remove attribute stubs
  - [ ] Replace all `self.params` → `self.context.params`
  - [ ] Replace all `self.localConfigDir` → `self.context.localConfigDir`
  - [ ] Replace all `self.noConfirm` → `self.context.noConfirm`
  - [ ] Replace all `self.isInteractiveMode` → `self.context.isInteractiveMode`
  - [ ] Replace all `self.showAdvancedOptions` → `self.context.showAdvancedOptions`
  - [ ] Replace all secret attributes → `self.context.*Secret`
  - [ ] Replace `self.getParam()` → `self.context.getParam()`
  - [ ] Replace `self.setParam()` → `self.context.setParam()`

- [ ] **3.2** Validate additionalConfigs.py
  - [ ] Run: `wsl bash -lc "black python/src/mas/cli/install/settings/additionalConfigs.py"`
  - [ ] Run: `wsl bash -lc "flake8 python/src/mas/cli/install/settings/additionalConfigs.py"`
  - [ ] Test `mas install` with additional configs scenario
  - [ ] Verify no functional changes

### Phase 4: Convert Remaining Mixins

**Objective**: Apply same pattern to all other mixins

- [ ] **4.1** Convert `python/src/mas/cli/install/settings/manageSettings.py`
  - [ ] Update copyright year to 2026
  - [ ] Replace TYPE_CHECKING stubs with context import
  - [ ] Update all attribute references to use `self.context.*`
  - [ ] Run black and flake8
  - [ ] Test Manage installation scenario

- [ ] **4.2** Convert `python/src/mas/cli/install/settings/db2Settings.py`
  - [ ] Update copyright year to 2026
  - [ ] Replace TYPE_CHECKING stubs with context import
  - [ ] Update all attribute references to use `self.context.*`
  - [ ] Run black and flake8
  - [ ] Test Db2 installation scenario

- [ ] **4.3** Convert `python/src/mas/cli/install/settings/mongodbSettings.py`
  - [ ] Update copyright year to 2026
  - [ ] Replace TYPE_CHECKING stubs with context import
  - [ ] Update all attribute references to use `self.context.*`
  - [ ] Run black and flake8
  - [ ] Test MongoDB installation scenario

- [ ] **4.4** Convert `python/src/mas/cli/install/settings/kafkaSettings.py`
  - [ ] Update copyright year to 2026
  - [ ] Replace TYPE_CHECKING stubs with context import
  - [ ] Update all attribute references to use `self.context.*`
  - [ ] Run black and flake8
  - [ ] Test Kafka installation scenario

- [ ] **4.5** Convert `python/src/mas/cli/install/settings/aiSettings.py`
  - [ ] Update copyright year to 2026
  - [ ] Replace TYPE_CHECKING stubs with context import
  - [ ] Update all attribute references to use `self.context.*`
  - [ ] Run black and flake8
  - [ ] Test AI Service installation scenario

### Phase 5: Update Other Install Files

**Objective**: Ensure consistency across all install module files

- [ ] **5.1** Review `python/src/mas/cli/install/argBuilder.py`
  - [ ] Check if context usage would simplify this file
  - [ ] Update if beneficial, otherwise document why not needed

- [ ] **5.2** Review `python/src/mas/cli/install/summarizer.py`
  - [ ] Check if context usage would simplify this file
  - [ ] Update if beneficial, otherwise document why not needed

### Phase 6: Final Validation

**Objective**: Comprehensive testing and cleanup

- [ ] **6.1** Run full test suite
  - [ ] Execute all install-related tests
  - [ ] Verify all scenarios work (Manage, IoT, Predict, etc.)
  - [ ] Test with various combinations of apps and dependencies

- [ ] **6.2** Code quality validation
  - [ ] Run black on all modified files
  - [ ] Run flake8 on all modified files
  - [ ] Verify no type checking errors with pyright/mypy

- [ ] **6.3** Documentation
  - [ ] Add docstring to InstallContext explaining its purpose
  - [ ] Document the pattern for future mixin additions
  - [ ] Update any relevant developer documentation

## Validation

### Success Criteria

- All modified files pass `black` and `flake8` validation
- TYPE_CHECKING blocks reduced by 60-70% (from ~225 lines to ~70 lines)
- All existing tests pass without modification
- `mas install` command works identically to before
- No functional changes to installation behavior
- All copyright years updated to 2026

### Testing Commands

```bash
# Format and lint all modified files
wsl bash -lc "black python/src/mas/cli/install/context.py python/src/mas/cli/install/app.py python/src/mas/cli/install/settings/*.py"
wsl bash -lc "flake8 python/src/mas/cli/install/context.py python/src/mas/cli/install/app.py python/src/mas/cli/install/settings/*.py"

# Run install tests
wsl bash -lc "cd python && pytest tests/cli/install/"

# Manual smoke test
mas install --help
```

### Rollback Plan

If issues arise:
1. Revert changes to specific mixin file
2. Context object remains harmless if unused
3. Can proceed with remaining mixins independently
4. Each phase is independently reversible

## Notes

- Context object uses camelCase for all attributes (e.g., `devMode`, `installManage`)
- `params` dict remains string-only for Tekton compatibility
- Context is shared reference, not copied - changes propagate immediately
- Method stubs in TYPE_CHECKING blocks still needed (printH1, yesOrNo, etc.)
- Only attribute stubs are eliminated by context object