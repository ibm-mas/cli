# Mirror Command Unit Tests

This directory contains unit tests for the `mas mirror` command, following the patterns established by the install test helper.

## Overview

The mirror test framework provides a structured way to test the mirror command functionality without requiring actual container registries, oc-mirror binary execution, or network access. All external dependencies are mocked.

## Test File Organization

The test suite is organized into modular files by category for better maintainability:

### Test Files (23 tests total)

1. **test_mirror_basic.py** (5 tests)
   - Basic mirror operations across different modes (m2d, m2m, d2m)
   - Custom auth file usage
   - Config file download from GitHub

2. **test_mirror_errors.py** (7 tests)
   - Missing oc-mirror binary
   - Invalid catalog version
   - Missing credentials (IBM entitlement key, registry credentials)
   - Command failures and partial failures
   - Timeout handling

3. **test_mirror_auth.py** (3 tests)
   - Authentication file generation for m2d mode
   - Authentication file generation for m2m mode
   - Authentication file generation for d2m mode

4. **test_mirror_config.py** (3 tests)
   - Successful config download from GitHub
   - Config download failure handling
   - Invalid YAML config handling

5. **test_mirror_packages.py** (3 tests)
   - Mirroring all available packages
   - Selective package mirroring
   - DB2 package special handling (db2u-s11, db2u-s12)

6. **test_mirror_advanced.py** (2 tests)
   - TLS verification disabled
   - Custom image timeout

## Architecture

### Test Helper Components

1. **MirrorTestConfig** (`test/utils/mirror_test_helper.py`)
   - Dataclass that defines test scenario configuration
   - Specifies mirror mode, catalog version, packages, and expected behavior
   - Automatically builds command line arguments from configuration

2. **MirrorTestHelper** (`test/utils/mirror_test_helper.py`)
   - Main test execution class
   - Sets up all necessary mocks (subprocess, file I/O, network)
   - Includes watchdog thread to detect hanging tests
   - Validates command construction and execution

3. **run_mirror_test()** (`test/utils/mirror_test_helper.py`)
   - Convenience function to run a test with minimal code
   - Takes tmpdir and MirrorTestConfig as parameters

## Running Tests

Run all mirror tests:
```bash
pytest test/mirror/
```

Run specific test file:
```bash
pytest test/mirror/test_mirror_basic.py
pytest test/mirror/test_mirror_errors.py
pytest test/mirror/test_mirror_auth.py
pytest test/mirror/test_mirror_config.py
pytest test/mirror/test_mirror_packages.py
pytest test/mirror/test_mirror_advanced.py
```

Run specific test:
```bash
pytest test/mirror/test_mirror_basic.py::test_mirror_m2d_catalog_only
```

## Test Scenarios

### test_mirror_m2d_catalog_only
**Purpose**: Test basic mirror-to-disk mode with catalog only

**Configuration**:
- Mode: m2d (mirror to disk)
- Catalog: v9-260129-amd64
- Release: 9.1.x
- Packages: None (catalog only)

**What it tests**:
- Basic m2d mode execution
- Catalog mirroring without packages
- Success result parsing
- Command argument construction

### test_mirror_m2m_with_packages
**Purpose**: Test mirror-to-mirror mode with packages

**Configuration**:
- Mode: m2m (mirror to mirror)
- Catalog: v9-260129-amd64
- Release: 9.1.x
- Packages: SLS, Core
- Target registry: registry.example.com/mas

**What it tests**:
- m2m mode with target registry
- Multiple package mirroring
- Authentication file generation
- Registry credentials handling

### test_mirror_d2m_resume
**Purpose**: Test disk-to-mirror mode for resuming

**Configuration**:
- Mode: d2m (disk to mirror)
- Catalog: v9-260129-amd64
- Release: 9.1.x
- Target registry: registry.example.com/mas

**What it tests**:
- d2m mode execution
- Resuming from disk storage
- Registry-only authentication (no IBM entitlement needed)

### test_mirror_with_custom_authfile
**Purpose**: Test using a pre-existing authentication file

**Configuration**:
- Mode: m2d
- Custom authfile path provided

**What it tests**:
- Custom auth file usage
- Skipping auth file generation
- Auth file validation

### test_mirror_with_config_download
**Purpose**: Test config file download from GitHub

**Configuration**:
- Mode: m2d
- Config file doesn't exist locally

**What it tests**:
- GitHub config file download
- Network mock handling
- Fallback to remote config

## Writing New Tests

### Basic Pattern

```python
def test_my_scenario(tmpdir):
    """Test description."""

    # Create test configuration
    config = MirrorTestConfig(
        mode='m2d',
        catalog_version='v9-260129-amd64',
        release='9.1.x',
        root_dir=str(tmpdir),
        packages={'sls': True},  # Enable packages as needed
        mock_oc_mirror_output=[
            '2026/02/09 17:00:15  [INFO]   : 10 / 10 additional images mirrored successfully',
        ],
        mock_image_count=10,
        expect_success=True,
        timeout_seconds=30,
        env_vars={
            'IBM_ENTITLEMENT_KEY': 'test-key',
            'HOME': str(tmpdir),
        },
        config_exists_locally=True,
    )

    # Run the test
    run_mirror_test(tmpdir, config)
```

### Configuration Options

#### Required Parameters
- `mode`: Mirror mode ('m2m', 'm2d', or 'd2m')
- `catalog_version`: Catalog version string (e.g., 'v9-260129-amd64')
- `release`: MAS release version (e.g., '9.1.x')

#### Optional Parameters
- `target_registry`: Target registry for m2m/d2m modes
- `root_dir`: Root directory for mirror operations (default: '/tmp/mirror')
- `packages`: Dict of package flags (e.g., `{'sls': True, 'core': True}`)
- `mock_oc_mirror_output`: List of output lines to simulate
- `mock_image_count`: Number of images in config (default: 10)
- `expect_success`: Whether operation should succeed (default: True)
- `timeout_seconds`: Test timeout in seconds (default: 30)
- `argv`: Custom command line arguments (auto-generated if not provided)
- `authfile`: Path to custom auth file
- `dest_tls_verify`: TLS verification flag (default: True)
- `image_timeout`: Image operation timeout (default: '20m')
- `env_vars`: Environment variables dict
- `mock_catalog_data`: Custom catalog data dict
- `config_exists_locally`: Whether config file exists locally (default: True)

## Mock Behavior

### Subprocess (oc-mirror)
- Mocked via `subprocess.Popen`
- Returns configured output lines
- Simulates success/failure based on `expect_success`
- Validates command arguments

### File System
- `path.exists()`: Returns True for local configs or custom authfile
- `makedirs()`: No-op, doesn't create actual directories
- `open()`: Returns mock file with YAML content

### Network
- `urllib.request.urlopen()`: Returns mock YAML content for GitHub downloads
- Only used when `config_exists_locally=False`

### Catalog Data
- `getCatalog()`: Returns mock catalog with version information
- Can be customized via `mock_catalog_data` parameter

## Running Tests

### Run all mirror tests
```bash
cd ../cli/python
pytest test/mirror/
```

### Run specific test
```bash
pytest test/mirror/test_mirror.py::test_mirror_m2d_catalog_only
```

### Run with verbose output
```bash
pytest test/mirror/ -v
```

### Run with debug logging
```bash
pytest test/mirror/ -v --log-cli-level=DEBUG
```

## Troubleshooting

### Test Timeout
If a test times out, check:
- `timeout_seconds` is sufficient for the test
- Mocks are properly configured
- No actual subprocess execution is occurring

### Import Errors
Ensure the test directory is in the Python path:
```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
```

### Mock Not Working
Verify the mock patch path matches the actual import in the code:
- Use `mas.cli.mirror.app.subprocess.Popen` not just `subprocess.Popen`
- Check the module where the function is used, not where it's defined

## Comparison with Install Test Helper

| Feature | Install Helper | Mirror Helper |
|---------|---------------|---------------|
| **User Interaction** | Yes (prompt tracking) | No (non-interactive) |
| **External Deps** | Kubernetes API | oc-mirror, file system |
| **Async Operations** | Pipeline launch | Subprocess execution |
| **Watchdog** | Yes | Yes |
| **Mock Complexity** | High (K8s resources) | Medium (subprocess, I/O) |

## Future Enhancements

Potential areas for expansion:
- Error scenario tests (network failures, invalid configs)
- Performance tests (large image counts)
- Partial failure scenarios (some images fail)
- Resume/retry logic testing
- Multi-architecture testing
- Custom timeout validation

## Made with Bob