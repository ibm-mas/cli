# Implementation Summary: --arch Parameter for mas mirror-images

## Overview

Successfully implemented the `--arch` / `-a` parameter for the `mas mirror-images` command, allowing users to explicitly specify target architecture (amd64, ppc64le, s390x) instead of downloading images for all architectures.

## Changes Made

### 1. Argument Parser (image/cli/mascli/functions/mirror_images)

**Added**: New `-a|--arch` case in the argument parser (lines 131-141)
- Accepts architecture value and stores in `MIRROR_ARCH` variable
- Validates that architecture is one of: amd64, ppc64le, s390x
- Shows error and exits if invalid architecture provided

### 2. Interactive Mode (image/cli/mascli/functions/mirror_images_common)

**Added**: Interactive architecture selection prompt (lines 45-84)
- Displays numbered menu: 1. amd64, 2. ppc64le, 3. s390x
- Auto-detects default from catalog version if architecture suffix present
- Stores selection in `MIRROR_ARCH` variable
- Validates user input

**Modified**: Export MIRROR_ARCH variable (line 138)
- Added `export MIRROR_ARCH` to make variable available to ansible-playbook

### 3. Architecture Resolution Logic (image/cli/mascli/functions/mirror_images_common)

**Completely rewrote**: `set_target_arch()` function (lines 205-240)

New logic flow:
1. Extract architecture from catalog version if present (CATALOG_ARCH)
2. If MIRROR_ARCH is set (from --arch or interactive):
   - Check for mismatch with catalog version
   - Show warning if architectures differ
   - Use MIRROR_ARCH value
3. If MIRROR_ARCH not set:
   - Use CATALOG_ARCH from catalog version
   - Error if cannot determine architecture
4. Export MIRROR_SINGLE_ARCH for ansible-devops

### 4. Help Documentation (image/cli/mascli/functions/help/mirror_images_help)

**Added**: Documentation for --arch parameter (line 35)
- Parameter description with color formatting
- Explanation that it overrides catalog version architecture

**Added**: Usage examples (lines 81-90)
- Example with explicit architecture
- Example showing override behavior with warning
- Example with catalog version without architecture suffix

## Behavior

### Non-Interactive Mode

```bash
# Specify architecture explicitly
mas mirror-images --arch amd64 --catalog v9-260527-amd64 ...

# Override catalog architecture (shows warning)
mas mirror-images --arch ppc64le --catalog v9-260527-amd64 ...

# Use with catalog without arch suffix
mas mirror-images --arch s390x --catalog v9-260527 ...
```

### Interactive Mode

When running `mas mirror-images` without parameters:
1. Prompts for catalog version
2. **NEW**: Prompts for target architecture with smart defaults
3. Continues with existing prompts (mirror mode, registry, etc.)

### Architecture Resolution

| Scenario | Catalog Version | --arch Parameter | Result | Warning |
|----------|----------------|------------------|--------|---------|
| 1 | v9-260527-amd64 | (not set) | amd64 | No |
| 2 | v9-260527-amd64 | amd64 | amd64 | No |
| 3 | v9-260527-amd64 | ppc64le | ppc64le | Yes |
| 4 | v9-260527 | amd64 | amd64 | No |
| 5 | v9-260527 | (not set) | Error | N/A |

## Backward Compatibility

✅ **Fully backward compatible**
- Existing scripts using catalog version with arch suffix continue to work
- No changes required to existing workflows
- Architecture is still extracted from catalog version when --arch not specified

## Integration with ansible-devops

The implementation leverages existing ansible-devops support:
- `MIRROR_SINGLE_ARCH` environment variable is already supported
- No changes needed in ansible-devops repository
- The `mirror_single_arch` variable in ansible roles handles the filtering

## Testing Recommendations

### Manual Testing

1. **Test help documentation**:
   ```bash
   mas mirror-images --help
   ```

2. **Test non-interactive with --arch**:
   ```bash
   mas mirror-images --mode direct --arch amd64 --catalog v9-260527-amd64 \
     --dir /tmp/mirror --channel 9.0.x --host registry.example.com \
     --username admin --password secret --ibm-entitlement KEY \
     --mirror-core --no-confirm
   ```

3. **Test architecture override (should show warning)**:
   ```bash
   mas mirror-images --mode direct --arch ppc64le --catalog v9-260527-amd64 \
     --dir /tmp/mirror --channel 9.0.x --host registry.example.com \
     --username admin --password secret --ibm-entitlement KEY \
     --mirror-core --no-confirm
   ```

4. **Test interactive mode**:
   ```bash
   mas mirror-images
   # Verify architecture prompt appears with correct defaults
   ```

5. **Test backward compatibility**:
   ```bash
   mas mirror-images --mode direct --catalog v9-260527-ppc64le \
     --dir /tmp/mirror --channel 9.0.x --host registry.example.com \
     --username admin --password secret --ibm-entitlement KEY \
     --mirror-core --no-confirm
   # Should work without --arch parameter
   ```

6. **Test error handling**:
   ```bash
   # Invalid architecture
   mas mirror-images --arch invalid ...
   
   # No architecture determinable
   mas mirror-images --catalog v9-260527 ...  # without --arch
   ```

## Files Modified

1. `image/cli/mascli/functions/mirror_images` - Added --arch argument parsing
2. `image/cli/mascli/functions/mirror_images_common` - Added interactive prompt, export, and modified set_target_arch()
3. `image/cli/mascli/functions/help/mirror_images_help` - Added documentation and examples

## Benefits

1. **Reduced Download Size**: Users only download images for their target architecture
2. **Faster Mirror Process**: Less data to transfer means faster completion
3. **Explicit Control**: Users can override catalog version architecture if needed
4. **Better UX**: Interactive mode guides users through architecture selection
5. **Backward Compatible**: Existing workflows continue to work unchanged

## Future Considerations

- Consider adding architecture validation against available catalog versions
- Could add auto-detection of system architecture as default
- May want to add architecture to the review settings display for clarity