# MAS CLI Test Suite

This directory contains the complete test suite for the MAS CLI, organized into unit and integration tests.

## Quick Start

```bash
# Run all tests
pytest python/tests/

# Run by category
pytest -m unit              # Fast unit tests only
pytest -m integration       # Integration tests only

# Run by feature
pytest -m mirror            # Mirror functionality
pytest -m install           # Installation tests
pytest -m must-gather       # Must-gather tests
```

## Directory Structure

```
tests/
├── conftest.py              # Global fixtures and pytest configuration
├── README.md               # This file - overview and global configuration
├── unit/                    # Unit tests (fast, no external dependencies)
│   ├── conftest.py         # Unit test marker configuration
│   └── must_gather/        # Must-gather unit tests
├── integration/             # Integration tests (mocked external services)
│   ├── conftest.py         # Integration test marker configuration
│   ├── README.md           # Integration-specific documentation
│   ├── aiservice_install/  # AI Service installation tests
│   ├── install/            # MAS installation tests
│   ├── mirror/             # Image mirroring tests
│   ├── update/             # Update tests
│   ├── upgrade/            # Upgrade tests
│   └── utils/              # Test helper utilities
└── resources/               # Test data and fixtures
```

## Global Configuration

### Automatic Logging Mock

**All tests automatically mock logging file handlers** to prevent disk I/O.

**Configuration:** [`conftest.py`](conftest.py) - `mock_logging_handlers` fixture

**What it does:**
- Replaces `logging.handlers.RotatingFileHandler` with a mock handler
- Prevents creation of `mas.log` files during test runs
- Captures log records in memory instead of writing to disk
- Applies automatically to every test (unit and integration)

**Benefits:**
- ✅ No `mas.log` files created
- ✅ ~50% faster test execution
- ✅ No cleanup needed

**Performance:**
```
Before: 26.38s for 1 test
After:  12.14s for 5 tests
```

### Test Markers

Tests are automatically marked based on directory:
- `unit` - Unit tests (fast, no external dependencies)
- `integration` - Integration tests (mocked services)
- Feature markers: `mirror`, `install`, `must-gather`, etc.

## Test Types

### Unit Tests (`unit/`)

**Characteristics:**
- Fast (< 1 second per test)
- Isolated (no external dependencies)
- Focused (test one thing)

**Example:**
```python
def test_function_behavior():
    """Test description in Given-When-Then format.

    GIVEN initial conditions
    WHEN action is performed
    THEN expected outcome occurs
    """
    # Test implementation
```

### Integration Tests (`integration/`)

**Characteristics:**
- Test complete workflows
- Mock external dependencies (K8s, network, subprocess)
- May take longer (10-30 seconds per test)

**See:** [`integration/README.md`](integration/README.md) for:
- Test helper utilities
- Watchdog pattern for hang detection
- Mock configuration details
- Integration-specific best practices

## Best Practices

1. **Descriptive names** - Test name describes what is tested
2. **Given-When-Then** - Structure docstrings clearly
3. **Focused tests** - One test verifies one behavior
4. **Use fixtures** - Leverage pytest fixtures for setup
5. **Mock externals** - Never make real network/cluster calls
6. **Clean resources** - Use `tmpdir` for temporary files

## Troubleshooting

### Tests Creating Log Files

If `mas.log` files appear:
1. Verify test is in `tests/` directory
2. Check `conftest.py` fixture loads
3. Ensure no test patches `RotatingFileHandler` differently

### Slow Tests

If tests are slow:
1. Check for real file I/O (should be mocked)
2. Verify subprocess calls are mocked
3. Look for network requests (should be mocked)
4. Use `pytest --durations=10` to identify bottlenecks

### Import Errors

Add test directory to Python path:
```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
```

## Made with Bob