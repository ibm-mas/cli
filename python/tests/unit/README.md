# Unit Tests

Unit tests validate individual functions and classes in isolation with no external dependencies.

**See also:** [`../README.md`](../README.md) for global test configuration and general guidelines.

## Test Organization

Unit tests are organized by functional area:

- **must_gather/** - Core must-gather functionality (app, CLI, output, upload)
- **must_gather/aiservice/** - AI Service instance and tenant collection
- **must_gather/argo/** - Argo application resource collection
- **must_gather/common/** - Shared utilities (resources, pods, secrets, parallel processing)
- **must_gather/dependencies/** - Dependency collection (Common Services, CP4D, DB2, SLS)
- **must_gather/mas/** - MAS-specific collection (apps, core, pipelines, summaries)
- **must_gather/ocp/** - OpenShift platform collection (cluster, nodes, operators, marketplace)
- **must_gather/summarizer/** - Summary generation and formatting

## Running Unit Tests

```bash
# All unit tests
pytest python/tests/unit/

# Specific category
pytest python/tests/unit/must_gather/aiservice/
pytest python/tests/unit/must_gather/common/

# By marker
pytest -m unit
pytest -m must-gather
```

## Test Characteristics

Unit tests should be:
- **Fast** - Complete in < 1 second per test
- **Isolated** - No external dependencies (network, filesystem, cluster)
- **Focused** - Test one function/method behavior
- **Deterministic** - Same input always produces same output

## Test Structure

### Class-Based Tests (unittest.TestCase)

```python
import unittest
from unittest.mock import MagicMock

class TestMyFeature(unittest.TestCase):
    """Test my feature functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mockClient = MagicMock()

    def test_feature_behavior(self):
        """Test specific behavior.

        GIVEN initial conditions
        WHEN action is performed
        THEN expected outcome occurs
        """
        # Test implementation
```

### Function-Based Tests (pytest style)

```python
from unittest.mock import Mock

class TestMyFeature:
    """Test my feature functionality."""

    def setup_method(self):
        """Set up test fixtures.

        GIVEN a test environment
        WHEN tests are run
        THEN create necessary mocks.
        """
        self.mockClient = Mock()

    def teardown_method(self):
        """Clean up test fixtures."""
        # Cleanup if needed

    def test_feature_behavior(self):
        """Test specific behavior.

        GIVEN initial conditions
        WHEN action is performed
        THEN expected outcome occurs
        """
        # Test implementation
```

## Common Patterns

### Mocking Kubernetes Resources

```python
from unittest.mock import MagicMock
from kubernetes.dynamic import DynamicClient

def test_with_k8s_mock():
    """Test with mocked Kubernetes client."""
    mockClient = MagicMock(spec=DynamicClient)
    mockApi = MagicMock()
    mockApi.get.return_value = mockResources
    mockClient.resources.get.return_value = mockApi
```

### Temporary Directories

```python
import tempfile
import shutil

def setup_method(self):
    """Create temporary directory."""
    self.testDir = tempfile.mkdtemp()

def teardown_method(self):
    """Clean up temporary directory."""
    if self.testDir:
        shutil.rmtree(self.testDir, ignore_errors=True)
```

### Patching Functions

```python
from unittest.mock import patch

@patch("mas.cli.must_gather.ocp.collectClusterResources")
def test_with_patch(self, mockCollect):
    """Test with patched function."""
    mockCollect.return_value = []
    # Test implementation
```

## Best Practices

1. **Mock External Dependencies**
   - Mock Kubernetes API calls
   - Mock file system operations
   - Mock network requests

2. **Use Given-When-Then**
   - Structure docstrings clearly
   - Makes test intent obvious

3. **Test One Thing**
   - Each test validates one behavior
   - Makes failures easy to diagnose

4. **Clean Up Resources**
   - Use `teardown_method()` or `tearDown()`
   - Remove temporary files/directories

5. **Descriptive Names**
   - Test name describes what is tested
   - Example: `test_discover_instances_from_crs`

## Common Assertions

```python
# Equality
self.assertEqual(actual, expected)
assert actual == expected

# Truth
self.assertTrue(condition)
assert condition

# Exceptions
with self.assertRaises(ValueError):
    function_that_raises()

# Mock calls
mockFunction.assert_called_once()
mockFunction.assert_called_with(arg1, arg2)
```

## Troubleshooting

### Tests Are Slow

Unit tests should be fast. If slow:
1. Check for real file I/O (should be mocked)
2. Verify no network calls
3. Ensure no subprocess execution
4. Use `pytest --durations=10` to find slow tests

### Mock Not Working

If mocks aren't being applied:
1. Verify patch path matches where function is used
2. Check mock is created before code under test runs
3. Ensure spec matches the object being mocked

### Import Errors

Add parent directory to path:
```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
```

## Made with Bob