---
name: reverse-engineer-tdd-tests
description: Apply TDD principles retrospectively to existing code by writing tests "as if" they were written first
---

# Reverse Engineering TDD Tests

## Overview

When implementation already exists, you cannot follow strict Red-Green-Refactor TDD. However, you can apply TDD principles retrospectively by writing tests "as if" they were written before implementation.

**Core principle:** Write focused, behavior-driven tests that would have guided the implementation if written first.

**Language-agnostic:** This approach works for any language (Python, TypeScript, Java, Go, etc.)

## When to Use

- Adding tests to existing untested code
- Refactoring test suites that violate TDD principles
- Improving "tests-after" code with proper test coverage
- Documenting existing behavior through tests
- Legacy code modernization

## Key Differences from True TDD

| Aspect | True TDD | Reverse Engineering TDD |
|--------|----------|------------------------|
| **Order** | Test → Implementation | Implementation → Test |
| **Red Phase** | Watch test fail | Verify test passes (implementation exists) |
| **Discovery** | Tests drive design | Tests document design |
| **Confidence** | High (saw it fail) | Medium (must verify thoroughly) |

## The Reverse Engineering Cycle

```
1. ANALYZE → 2. WRITE → 3. VERIFY → 4. REFACTOR → Repeat
```

### 1. ANALYZE - Understand Behavior

Read implementation to identify discrete, testable behaviors.

**Good Analysis:**
```
# Analyzing processPayment():
# 1. Returns error when payment gateway unavailable
# 2. Returns error when validation fails
# 3. Returns error when exception raised
# 4. Returns success and stores transaction on success
# 5. Skips notification when --silent flag set
# 6. Logs retry message when retry attempted
```

**Bad Analysis:**
```
# Analyzing processPayment():
# 1. Tests the function works
# 2. Tests error handling
# 3. Tests success case
```
Too vague, not actionable

### 2. WRITE - Create Focused Test

Write one test for one behavior, as if you were writing it before implementation.

**Requirements:**
- Test ONE specific behavior
- Use Given-When-Then docstring format
- Mock at system boundaries only (see Mocking Strategy below)
- Use real operations where possible (file I/O, data transformations)
- Clear, descriptive test name

**Good Test (Python):**
```python
def test_gateway_unavailable_returns_error():
    """Test that unavailable payment gateway returns error.

    GIVEN payment gateway is unavailable
    WHEN processPayment executes
    THEN returns error code and logs failure.
    """
    with patch("payment.gateway.connect") as mock_connect:
        mock_connect.return_value = None

        result = processPayment(amount=100, currency="USD")

        assert result.status == "error"
        assert "gateway unavailable" in result.message
```

**Good Test (TypeScript):**
```typescript
test('gateway unavailable returns error', async () => {
  // GIVEN payment gateway is unavailable
  const mockGateway = jest.fn().mockResolvedValue(null);

  // WHEN processPayment executes
  const result = await processPayment({
    amount: 100,
    currency: 'USD',
    gateway: mockGateway
  });

  // THEN returns error
  expect(result.status).toBe('error');
  expect(result.message).toContain('gateway unavailable');
});
```

**Bad Test:**
```python
def test_payment():
    """Test payment processing."""
    # Tests multiple behaviors at once
    # Vague name and docstring
    # Over-mocked
```

### 3. VERIFY - Confirm Test Passes

Run the test and verify it passes because implementation exists.

**Python:**
```bash
pytest tests/test_payment.py::test_gateway_unavailable_returns_error -v
```

**TypeScript:**
```bash
npm test -- payment.test.ts -t "gateway unavailable"
```

**Java:**
```bash
mvn test -Dtest=PaymentTest#testGatewayUnavailableReturnsError
```

**Confirm:**
- Test passes (implementation handles this case)
- Test is fast (< 2 seconds per test average)
- No warnings or errors
- Coverage increases

**Test fails?** Determine the cause:

1. **Bug in Implementation** ✅ Fix it
   - Test reveals existing code doesn't handle edge case correctly
   - Example: Function returns wrong error code, missing null check, incorrect validation
   - **Action:** Fix the bug - this is part of reverse engineering work

2. **Missing Feature** ❌ Don't implement it
   - Test expects behavior that was never implemented
   - Example: Function doesn't support optional parameter, missing entire code path
   - **Action:** Remove the test or mark as TODO - implementing new features is NOT part of reverse engineering
   - **Rationale:** Reverse engineering documents existing behavior, not desired behavior

3. **Test is Wrong** ✅ Fix the test
   - Test has incorrect expectations or setup
   - Example: Wrong assertion, incorrect mock setup, typo in test
   - **Action:** Fix the test to match actual implementation behavior

4. **Mocking is Incorrect** ✅ Fix the mocks
   - Mocks don't reflect real behavior or are over-mocked
   - Example: Mock returns wrong type, mocking internal functions
   - **Action:** Review mocking strategy and fix

**Critical Distinction:**

| Scenario | Action | Reason |
|----------|--------|--------|
| **Bug:** Code crashes on null input | ✅ Fix bug | Existing code should handle this |
| **Bug:** Returns wrong error code | ✅ Fix bug | Existing code has incorrect behavior |
| **Missing:** No support for new format | ❌ Don't add feature | Not part of existing behavior |
| **Missing:** Entire code path doesn't exist | ❌ Don't implement | New feature, not reverse engineering |

**When in doubt:** Ask yourself "Did the original developer intend this behavior?" If yes, it's a bug to fix. If no, it's a feature to skip.

### 4. REFACTOR - Improve Clarity

After test passes, refactor for clarity:
- Improve test name if needed
- Simplify setup code
- Extract common fixtures
- Add clarifying comments

**Keep test passing throughout refactoring.**

## Mocking Strategy

**Core Principle:** Mock at system boundaries, test real behavior including file operations and data transformations.

### What TO Mock (External Boundaries)

Mock external dependencies that are:
- Slow (network calls, database operations)
- Require external services (APIs, databases, message queues)
- Non-deterministic (random values, timestamps, external state)
- Already tested elsewhere (third-party libraries, other modules)

**Examples by Category:**

**1. External APIs / Services**
```python
# Python
@patch("module.api_client.fetch_data")
@patch("module.payment_gateway.process")
```
```typescript
// TypeScript
jest.mock('./apiClient', () => ({
  fetchData: jest.fn(),
  processPayment: jest.fn()
}));
```

**2. Database Operations**
```python
# Python
@patch("module.database.save")
@patch("module.database.query")
```
```java
// Java
@Mock
private DatabaseRepository repository;
```

**3. Network Operations**
```python
# Python
@patch("module.http_client.get")
@patch("module.download_file")
```
```typescript
// TypeScript
jest.mock('axios');
```

**4. Time-Dependent Operations**
```python
# Python
@patch("module.datetime.now")
@patch("module.time.sleep")
```
```typescript
// TypeScript
jest.useFakeTimers();
```

**Why:** External dependencies are slow, require services, and are tested elsewhere.

### What NOT to Mock (Internal Logic)

**NEVER mock these:**

**1. File Read/Write Operations** ✅
```python
# Python - DON'T mock file operations
# DO use temporary directories
def test_create_report_success(tmp_path):
    output_file = tmp_path / "report.md"
    create_report(output_file)
    assert output_file.exists()
    assert "expected content" in output_file.read_text()
```
```typescript
// TypeScript - DON'T mock fs
// DO use temporary directories
test('creates report file', () => {
  const tmpDir = fs.mkdtempSync('/tmp/test-');
  const outputFile = path.join(tmpDir, 'report.md');
  createReport(outputFile);
  expect(fs.existsSync(outputFile)).toBe(true);
});
```

**2. Argument Processing** ✅
```python
# DON'T mock argument objects
# DO create real objects with test data
args = {"instance_id": "test", "build_id": "123"}
```

**3. Data Transformation** ✅
```python
# DON'T mock transformation functions
# DO let them run and verify output
result = formatData(input_data)
assert result == expected_output
```

**4. Logging** ✅
```python
# DON'T mock logger
# DO let it log (fast, part of observable behavior)
# Optionally capture logs to verify messages
```

**5. Business Logic** ✅
```python
# DON'T mock calculation or validation functions
# DO test them directly with real inputs
result = calculateTotal(items)
assert result == expected_total
```

### Mock Pattern for File Operations

When mocking functions that interact with files, **create real files** in temporary locations:

**Python Example:**
```python
def test_process_with_real_files(tmp_path):
    """Test processing with real file operations."""

    # Setup: Create real directory structure
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)

    with patch("module.download_data") as mock_download:
        # Mock returns path to real temp directory
        mock_download.return_value = data_dir / "data.json"

        # Mock creates real file with test data
        def create_file(*args):
            file_path = data_dir / "result.txt"
            file_path.write_text("Test results")
            return {"success": True}

        with patch("module.external_process") as mock_process:
            mock_process.side_effect = create_file

            # Execute - performs real file I/O
            result = process_data(data_dir)

            # Verify real file was created
            assert result == 0
            assert (data_dir / "result.txt").exists()
```

**TypeScript Example:**
```typescript
test('processes with real files', () => {
  const tmpDir = fs.mkdtempSync('/tmp/test-');

  // Mock external download but create real file
  const mockDownload = jest.fn().mockImplementation(() => {
    const filePath = path.join(tmpDir, 'data.json');
    fs.writeFileSync(filePath, JSON.stringify({test: 'data'}));
    return filePath;
  });

  const result = processData(tmpDir, mockDownload);

  expect(result.success).toBe(true);
  expect(fs.existsSync(path.join(tmpDir, 'result.txt'))).toBe(true);
});
```

## Performance Targets

- **< 2 seconds per test** on average
- **< 5 seconds per test** maximum for complex scenarios
- **80%+ coverage** on command handlers

Slow tests indicate over-mocking or testing wrong things.

## Test Organization

### File Naming
```
tests/cli/test_<module>.py
```

### Test Naming Convention

**Pattern:** `test_<behavior>_<condition>_<expected_result>`

**Examples across languages:**

**Python:**
```python
def test_gateway_unavailable_returns_error():
def test_cache_hit_skips_download():
def test_successful_payment_stores_transaction():
```

**TypeScript:**
```typescript
test('gateway unavailable returns error', ...)
test('cache hit skips download', ...)
test('successful payment stores transaction', ...)
```

**Java:**
```java
@Test
public void testGatewayUnavailableReturnsError() { ... }
@Test
public void testCacheHitSkipsDownload() { ... }
```

**Go:**
```go
func TestGatewayUnavailableReturnsError(t *testing.T) { ... }
func TestCacheHitSkipsDownload(t *testing.T) { ... }
```

### Test Structure (Arrange-Act-Assert)

**Python:**
```python
def test_behavior():
    """Test description.

    GIVEN preconditions
    WHEN action occurs
    THEN expected result.
    """
    # Arrange: Setup mocks and test data
    with patch("module.external_function") as mock:
        mock.return_value = test_value
        test_input = {"key": "value"}

        # Act: Execute the behavior
        result = function_under_test(test_input)

        # Assert: Verify expected outcome
        assert result == expected
        mock.assert_called_once()
```

**TypeScript:**
```typescript
test('behavior description', () => {
  // Arrange
  const mockFunction = jest.fn().mockResolvedValue(testValue);
  const testInput = { key: 'value' };

  // Act
  const result = functionUnderTest(testInput, mockFunction);

  // Assert
  expect(result).toBe(expected);
  expect(mockFunction).toHaveBeenCalledTimes(1);
});
```

**Java:**
```java
@Test
public void testBehavior() {
    // Arrange
    when(mockService.externalFunction()).thenReturn(testValue);
    TestInput input = new TestInput("value");

    // Act
    Result result = functionUnderTest(input);

    // Assert
    assertEquals(expected, result);
    verify(mockService, times(1)).externalFunction();
}
```

## Common Pitfalls

### ❌ Testing Implementation Details
```
# BAD: Tests how code works internally
def test_uses_correct_algorithm():
    with mock("module.internal_helper") as mock:
        function()
        verify(mock).called_with(specific_args)
```

### ✅ Testing Behavior
```
# GOOD: Tests what code does
def test_returns_sorted_results():
    result = function(unsorted_data)
    assert result == sorted_data
```

### ❌ Over-Mocking
```
# BAD: Mocks everything including file operations
with mock("file_system.open"), \
     mock("file_system.exists"), \
     mock("file_system.mkdir"):
    # Test doesn't verify real file handling
```

### ✅ Minimal Mocking
```
# GOOD: Only mocks external boundaries
def test_with_real_files(tmp_dir):
    with mock("module.download_from_api") as mock:
        mock.return_value = tmp_dir / "file.dat"
        # Real file operations happen
```

### ❌ Multiple Behaviors in One Test
```
# BAD: Tests multiple things
def test_function_works():
    # Tests success, error handling, and caching
    assert result1 == success
    assert result2 == error
    assert cache_used
```

### ✅ One Behavior Per Test
```
# GOOD: Focused tests
def test_success_case():
    assert result == success

def test_error_case():
    assert result == error

def test_cache_hit_skips_operation():
    assert not operation_called
```

## Verification Checklist

Before marking reverse engineering complete:

- [ ] Every behavior has a focused test
- [ ] Each test has Given-When-Then docstring
- [ ] Tests use minimal mocking (boundaries only)
- [ ] File operations use real files with tmp_path
- [ ] Test names clearly describe behavior
- [ ] All tests pass
- [ ] Tests are fast (< 2s average)
- [ ] Coverage is 80%+ on target module
- [ ] No flake8 or black violations

## Example: Complete Reverse Engineering

**Implementation to Test:**
```python
def generate_report(data_source, output_dir, format="markdown"):
    """Generate report from data source."""
    try:
        # Fetch data from external source
        data = fetch_data(data_source)

        if not data:
            logger.warning("No data found")
            return 0

        # Transform data to desired format
        content = format_data(data, format)

        # Write to file
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        output_file = output_path / f"report.{format}"
        with open(output_file, "w") as f:
            f.write(content)

        logger.info(f"Report created: {output_file}")
        return 0

    except ValueError as e:
        logger.error(f"Error: {e}")
        return 1
```

**Step 1: ANALYZE Behaviors**
1. Success: Fetches data, formats it, writes file
2. No data: Logs warning, returns 0
3. ValueError: Logs error, returns 1

**Step 2: WRITE Tests**
```python
def test_generate_report_success(tmp_path):
    """Test successful report generation.

    GIVEN fetch_data returns valid data
    WHEN generate_report executes
    THEN report file is created and function returns 0.
    """
    with patch("module.fetch_data") as mock_fetch, \
         patch("module.format_data") as mock_format:

        mock_fetch.return_value = {"key": "value"}
        mock_format.return_value = "# Report\n\nContent..."

        result = generate_report(
            data_source="test_source",
            output_dir=str(tmp_path),
            format="markdown"
        )

        assert result == 0
        output_file = tmp_path / "report.markdown"
        assert output_file.exists()
        assert "# Report" in output_file.read_text()


def test_generate_report_no_data(tmp_path):
    """Test report generation with no data.

    GIVEN fetch_data returns empty result
    WHEN generate_report executes
    THEN warning is logged and function returns 0.
    """
    with patch("module.fetch_data") as mock_fetch:
        mock_fetch.return_value = None

        result = generate_report(
            data_source="test_source",
            output_dir=str(tmp_path)
        )

        assert result == 0


def test_generate_report_value_error(tmp_path):
    """Test report generation handles ValueError.

    GIVEN fetch_data raises ValueError
    WHEN generate_report executes
    THEN error is logged and function returns 1.
    """
    with patch("module.fetch_data") as mock_fetch:
        mock_fetch.side_effect = ValueError("Test error")

        result = generate_report(
            data_source="test_source",
            output_dir=str(tmp_path)
        )

        assert result == 1
```

**Step 3: VERIFY**
```bash
pytest tests/test_report.py::test_generate_report_success -v
pytest tests/test_report.py::test_generate_report_no_data -v
pytest tests/test_report.py::test_generate_report_value_error -v
```

All pass ✅

**Step 4: REFACTOR**
Tests are clear and focused. No refactoring needed.

## Comparison with True TDD

### True TDD (Ideal)
```
1. Write failing test
2. Watch it fail (proves test works)
3. Write minimal code to pass
4. Watch it pass
5. Refactor
```
**Confidence:** High - saw test fail and pass

### Reverse Engineering TDD (Pragmatic)
```
1. Analyze existing implementation
2. Write test as if it were first
3. Verify test passes (implementation exists)
4. Refactor test for clarity
```
**Confidence:** Medium - must verify thoroughly

## When to Use Each Approach

| Situation | Approach |
|-----------|----------|
| New feature | True TDD (test-first) |
| Bug fix | True TDD (test-first) |
| Existing untested code | Reverse Engineering TDD |
| Refactoring tests | Reverse Engineering TDD |
| Legacy code | Reverse Engineering TDD |

## Final Notes

Reverse Engineering TDD is **not** an excuse to skip true TDD. It's a pragmatic approach for:
- Adding tests to existing code
- Improving poor test suites
- Learning TDD principles on existing code

**For new code, always use true TDD (test-first).**

The goal is to write tests that would have guided the implementation if written first, even though they weren't.