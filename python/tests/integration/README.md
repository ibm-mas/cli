# Integration Tests

Integration tests validate end-to-end functionality by testing complete command workflows with mocked external dependencies.

**See also:** [`../README.md`](../README.md) for global test configuration and general guidelines.

## Test Categories

Integration tests are organized by command functionality:

- **aiservice_install/** - AI Service installation workflows
- **install/** - MAS installation workflows (catalog, dev mode, routing)
- **mirror/** - Image mirroring operations (m2d, m2m, d2m modes)
- **update/** - MAS update workflows
- **upgrade/** - MAS upgrade workflows
- **utils/** - Test helper utilities and shared fixtures

## Running Integration Tests

```bash
# All integration tests
pytest python/tests/integration/

# Specific category
pytest python/tests/integration/mirror/
pytest python/tests/integration/install/

# By marker
pytest -m mirror
pytest -m install
```

## Mocked Components

Integration tests mock all external dependencies:

1. **Kubernetes API** - All cluster operations
2. **Subprocess execution** - Commands like `oc-mirror`, `helm`
3. **Network requests** - GitHub downloads, registry operations
4. **File system** - Most file operations (except test fixtures)
5. **Logging** - Automatic via global fixture (see [`../README.md`](../README.md))

## Watchdog Pattern for Hang Detection

### What is the Watchdog?

The watchdog is an **activity-based timeout mechanism** used in test helpers. Unlike simple timeouts, it:
- Resets its timer when progress is detected
- Only triggers if the test hangs without activity
- Allows variable test duration based on complexity

### When to Use Watchdog

**Use watchdog when:**
- ✅ Tests have interactive prompts (install, update tests)
- ✅ Tests have subprocess calls that should show progress (mirror tests)
- ✅ Test duration varies based on number of operations
- ✅ You need to detect actual hangs vs slow-but-progressing tests

**Don't use watchdog when:**
- ❌ Test has fixed, predictable duration
- ❌ No interactive or progressive operations
- ❌ Simple unit tests with no external interactions

### Watchdog Implementations

#### 1. Install/Update Tests: Prompt-Based Activity
```python
def start_watchdog(self):
    """Start watchdog thread to detect hanging prompts."""
    def watchdog():
        while not self.test_failed["failed"]:
            time.sleep(1)
            elapsed = time.time() - self.last_prompt_time["time"]
            if elapsed > self.config.timeout_seconds:
                self.test_failed["failed"] = True
                self.test_failed["message"] = f"Test hung: No prompt received for {self.config.timeout_seconds}s"
                break

    self.watchdog_thread = threading.Thread(target=watchdog, daemon=True)
    self.watchdog_thread.start()

# Timer resets on each prompt
def wrapped_prompt_handler(*args, **kwargs):
    self.last_prompt_time["time"] = time.time()  # Reset timer
    return prompt_handler(*args, **kwargs)
```

**Behavior:**
- Timer resets every time a prompt is handled
- Test with 10 prompts (5s each) = 50s total, but watchdog won't trigger
- Only triggers if a single prompt hangs for 30s+ without response

#### 2. Mirror Tests: Subprocess Activity
```python
def start_watchdog(self):
    """Start watchdog thread to detect hanging tests."""
    def watchdog():
        while not self.test_failed["failed"]:
            time.sleep(1)
            elapsed = time.time() - self.last_activity_time["time"]
            if elapsed > self.config.timeout_seconds:
                self.test_failed["failed"] = True
                self.test_failed["message"] = f"Test hung: No activity for {self.config.timeout_seconds}s"
                break

# Timer resets on subprocess calls
def popen_side_effect(*args, **kwargs):
    self.update_activity()  # Reset timer
    return self.create_mock_subprocess()
```

**Behavior:**
- Timer resets on each subprocess call
- Allows long operations as long as they show progress
- Detects if subprocess mock stops responding

### Watchdog vs pytest.mark.timeout

| Scenario | Watchdog (30s) | pytest.mark.timeout(60s) |
|----------|----------------|--------------------------|
| 10 prompts × 5s each | ✅ Pass (50s, resets 10×) | ✅ Pass (50s < 60s) |
| Hangs after 9 prompts | ✅ Fail at 45s+30s=75s | ❌ Pass (45s < 60s) |
| Single slow prompt (40s) | ❌ Fail (40s > 30s) | ✅ Pass (40s < 60s) |
| Actual hang (no activity) | ✅ Fail at 30s | ✅ Fail at 60s |

**Key difference:** Watchdog detects **lack of progress**, not just total duration.

### Configuration

Set timeout in test config:
```python
config = MirrorTestConfig(
    # ... other config
    timeout_seconds=30,  # Watchdog triggers after 30s of inactivity
)
```

**Recommended values:**
- Fast tests (few operations): 15-30 seconds
- Medium tests (multiple prompts): 30-60 seconds
- Complex tests (many operations): 60-120 seconds

## Writing New Tests

### Basic Structure

```python
def test_my_feature(tmpdir):
    """Test description in Given-When-Then format.

    GIVEN initial conditions
    WHEN action is performed
    THEN expected outcome occurs
    """
    # Test implementation
```

### Using Test Helpers

Each test category has a helper class to reduce boilerplate:

```python
from utils import MirrorTestHelper, MirrorTestConfig

def test_mirror_scenario(tmpdir):
    config = MirrorTestConfig(
        mode='m2d',
        catalog_version='v9-260129-amd64',
        timeout_seconds=30,  # Watchdog timeout
        # ... other config
    )
    helper = MirrorTestHelper(tmpdir, config)
    helper.run_mirror_test()
```

### Logging in Tests

The logging mock is automatic, but you can access it if needed:

```python
def test_with_log_verification(tmpdir, mock_logging_handlers):
    """Test that verifies log output."""
    # Your test code
    # mock_logging_handlers contains the mock handler
    # You can verify calls if needed
```

## Troubleshooting

### Tests Creating Real Log Files

If you see `mas.log` files being created:
1. Verify the test is in the `integration/` directory
2. Check that `conftest.py` fixture is being loaded
3. Ensure no test is patching `RotatingFileHandler` differently

### Slow Test Execution

If tests are slow:
1. Check for real file I/O (should be mocked)
2. Verify subprocess calls are mocked
3. Look for network requests (should be mocked)
4. Use `pytest --durations=10` to identify slow tests

### Mock Not Working

If mocks aren't being applied:
1. Verify import paths match where functions are used (not defined)
2. Check mock is patched before the code under test runs
3. Ensure fixture scope is appropriate

## Best Practices

1. **Use descriptive test names** - Name should describe what is being tested
2. **Follow Given-When-Then** - Structure docstrings clearly
3. **Keep tests focused** - One test should verify one behavior
4. **Use fixtures** - Leverage pytest fixtures for common setup
5. **Mock external dependencies** - Never make real network/cluster calls
6. **Clean up resources** - Use `tmpdir` for temporary files
7. **Document complex scenarios** - Add comments for non-obvious logic

## Made with Bob