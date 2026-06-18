# Add --arch Parameter to mas mirror-images Command

## Status: ✅ IMPLEMENTATION COMPLETE

See [Implementation Summary](2026-06-18-implementation-summary.md) for detailed documentation.

## Objective

Add `--arch` / `-a` parameter to `mas mirror-images` command to allow users to explicitly specify target architecture (amd64, ppc64le, s390x) instead of downloading images for all architectures. This provides more control and reduces download size/time when users know their target architecture.

## Design Decisions

### Architecture Resolution Logic

The implementation will use a **flexible approach** that supports multiple scenarios:

1. **Catalog version with arch + no --arch**: Extract arch from catalog version (current behavior)
2. **Catalog version with arch + --arch specified**: Use --arch value, show warning if mismatch
3. **Catalog version without arch + --arch specified**: Use --arch value
4. **No catalog arch + no --arch**: Error (cannot determine architecture)

### Parameter Flow

```
User Input (--arch or interactive prompt)
    ↓
MIRROR_ARCH environment variable
    ↓
set_target_arch() function
    ↓
MIRROR_SINGLE_ARCH environment variable
    ↓
ansible-devops (mirror_single_arch variable)
```

### Interactive Mode Architecture Selection

When in interactive mode and no `--arch` is provided, prompt user to select architecture:
- Show numbered list: 1. amd64, 2. ppc64le, 3. s390x
- Default to architecture from catalog version if present
- If catalog has no arch suffix, require user selection

## Critical Rules

- **Preserve backward compatibility**: Existing scripts using catalog version with arch suffix must continue to work
- **No functional changes to ansible-devops**: The backend already supports `mirror_single_arch` variable
- **Validate architecture values**: Only accept amd64, ppc64le, s390x
- **Clear user feedback**: Show warnings when --arch overrides catalog version architecture
- **Track progress ONLY in this plan document**, NOT in chat todo lists

## Execution Plan

### Phase 1: Modify Argument Parser and Add Interactive Prompt

**Objective**: Add `--arch` parameter to CLI and interactive architecture selection

[x] **1.1** Add `--arch` / `-a` case to argument parser in `mirror_images_noninteractive()`
  - [x] Add case statement for `-a|--arch` around line 79-229
  - [x] Store value in `MIRROR_ARCH` variable
  - [x] Validate architecture value (amd64, ppc64le, s390x)
  - [x] Show error and exit if invalid architecture provided

[x] **1.2** Add interactive architecture prompt in `mirror_images_interactive()`
  - [x] Add prompt after catalog version selection (after line 37 in mirror_images_common)
  - [x] Show numbered options: 1. amd64, 2. ppc64le, 3. s390x
  - [x] Set default based on catalog version if arch suffix present
  - [x] Store selection in `MIRROR_ARCH` variable

[x] **1.3** Export `MIRROR_ARCH` variable in `mirror_to_registry_common()`
  - [x] Add `export MIRROR_ARCH` around line 94 in mirror_images_common

[ ] **1.4** Validation: Run interactive mode and verify architecture prompt appears

### Phase 2: Modify set_target_arch() Function

**Objective**: Update architecture detection logic to support explicit --arch parameter

[x] **2.1** Modify `set_target_arch()` function in `mirror_images_common`
  - [x] Check if `MIRROR_ARCH` is set (from --arch or interactive prompt)
  - [x] If `MIRROR_ARCH` is set:
    - [x] Extract arch from catalog version if present
    - [x] If catalog arch exists and differs from `MIRROR_ARCH`, show warning
    - [x] Use `MIRROR_ARCH` value for `MIRROR_SINGLE_ARCH`
  - [x] If `MIRROR_ARCH` is not set:
    - [x] Use existing logic to extract from catalog version
    - [x] Error if cannot determine architecture
  - [x] Ensure `MIRROR_SINGLE_ARCH` is exported

[x] **2.2** Update architecture display in review settings (line 140)
  - [x] Architecture display already exists and will show MIRROR_SINGLE_ARCH correctly

[ ] **2.3** Validation: Test all scenarios:
  - [ ] Catalog with arch + no --arch (should use catalog arch)
  - [ ] Catalog with arch + matching --arch (should proceed without warning)
  - [ ] Catalog with arch + different --arch (should show warning, use --arch)
  - [ ] Catalog without arch + --arch (should use --arch)

### Phase 3: Update Help Documentation

**Objective**: Document the new --arch parameter in help text

[x] **3.1** Add `--arch` parameter to help header in `mirror_images_help`
  - [x] Add entry in "Maximo Operator Catalog Selection" section (after line 34)
  - [x] Format: `-a, --arch ${COLOR_YELLOW}MIRROR_ARCH${TEXT_RESET}  Target architecture (amd64, ppc64le, s390x)`
  - [x] Add description explaining it overrides catalog version architecture

[x] **3.2** Add usage examples in help text
  - [x] Example with --arch parameter
  - [x] Example showing override behavior

[ ] **3.3** Validation: Run `mas mirror-images --help` and verify documentation

### Phase 4: Integration Testing

**Objective**: Comprehensive testing of all scenarios

**Note**: Manual testing required - see [Implementation Summary](2026-06-18-implementation-summary.md) for test scenarios

[ ] **4.1** Test non-interactive mode with --arch parameter
  - [ ] Test: `mas mirror-images --arch amd64 --catalog v9-260527-amd64 ...`
  - [ ] Test: `mas mirror-images --arch ppc64le --catalog v9-260527-amd64 ...` (should warn)
  - [ ] Test: `mas mirror-images --arch s390x --catalog v9-260527 ...`
  - [ ] Verify `MIRROR_SINGLE_ARCH` is set correctly in each case

[ ] **4.2** Test interactive mode
  - [ ] Run without --arch, verify architecture prompt appears
  - [ ] Test selecting each architecture option
  - [ ] Verify selection is reflected in review settings

[ ] **4.3** Test backward compatibility
  - [ ] Run existing command without --arch parameter
  - [ ] Verify architecture is extracted from catalog version
  - [ ] Confirm no regression in existing functionality

[ ] **4.4** Test error handling
  - [ ] Test invalid architecture value: `--arch invalid`
  - [ ] Test catalog without arch and no --arch parameter
  - [ ] Verify appropriate error messages

## Final Validation

After completing all phases:

1. **Run help command**: `mas mirror-images --help`
   - Verify --arch parameter is documented
   - Check formatting and clarity

2. **Test non-interactive mode**:
   ```bash
   mas mirror-images \
     --mode direct \
     --dir /tmp/mirror \
     --arch amd64 \
     --catalog v9-260527-amd64 \
     --channel 9.0.x \
     --host registry.example.com \
     --username admin \
     --password secret \
     --ibm-entitlement KEY \
     --mirror-core \
     --no-confirm
   ```
   - Verify architecture is set correctly
   - Check for any warnings if catalog arch differs

3. **Test interactive mode**:
   ```bash
   mas mirror-images
   ```
   - Verify architecture prompt appears
   - Test selecting different architectures
   - Confirm selection is used in mirror process

4. **Test backward compatibility**:
   ```bash
   mas mirror-images \
     --mode direct \
     --dir /tmp/mirror \
     --catalog v9-260527-ppc64le \
     --channel 9.0.x \
     --host registry.example.com \
     --username admin \
     --password secret \
     --ibm-entitlement KEY \
     --mirror-core \
     --no-confirm
   ```
   - Verify architecture is extracted from catalog version
   - Confirm no errors or unexpected behavior

**Success Criteria**:
- All tests pass without errors
- Architecture selection works in both interactive and non-interactive modes
- Backward compatibility maintained
- Help documentation is clear and accurate
- Warning messages appear when --arch overrides catalog architecture