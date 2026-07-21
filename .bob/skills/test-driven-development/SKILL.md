---
name: test-driven-development
description: Comprehensive TDD approach with abilities for both test-first development and reverse-engineering tests for existing code
---

# Test-Driven Development Skills

This skill provides a comprehensive approach to Test-Driven Development with two distinct abilities for different scenarios.

## Context
- `{SKILL_ROOT}` is the root directory of this skill
- `{WORKSPACE_ROOT}` is the root directory of the workspace

## Ability: Write Tests First (Traditional TDD)

Use this ability when implementing new features or fixing bugs: `{SKILL_ROOT}/abilities/write-tests-first.md`

**When to use:**
- New features
- Bug fixes
- Refactoring with behavior changes
- Any new production code

**Core principle:** Write the test first, watch it fail, then implement.

## Ability: Reverse Engineer Tests

Use this ability when adding tests to existing untested code: `{SKILL_ROOT}/abilities/reverse-engineer-tests.md`

**When to use:**
- Adding tests to existing untested code
- Refactoring test suites that violate TDD principles
- Improving "tests-after" code with proper test coverage
- Documenting existing behavior through tests
- Legacy code modernization

**Core principle:** Write focused, behavior-driven tests "as if" they were written before implementation.

## Shared Resources

### Testing Anti-Patterns

Both abilities reference common testing anti-patterns to avoid: `{SKILL_ROOT}/testing-anti-patterns.md`

**Key anti-patterns:**
- Testing mock behavior instead of real behavior
- Adding test-only methods to production classes
- Mocking without understanding dependencies
- Incomplete mocks that hide structural assumptions
- Integration tests as afterthought

## Choosing the Right Ability

| Situation | Ability to Use |
|-----------|----------------|
| Implementing new feature | Write Tests First |
| Fixing a bug | Write Tests First |
| Adding tests to existing code | Reverse Engineer Tests |
| Refactoring without tests | Reverse Engineer Tests |
| Legacy code modernization | Reverse Engineer Tests |

## General Principles

Both abilities share these core principles:

1. **One test, one behavior** - Each test should verify a single, specific behavior
2. **Clear test names** - Test names should describe what behavior is being tested
3. **Minimal mocking** - Mock at system boundaries only, test real behavior
4. **Fast tests** - Tests should run quickly (< 2 seconds average)
5. **High coverage** - Aim for 80%+ coverage on production code

## Integration with Development Workflow

### For New Code (Write Tests First)
```
1. Write failing test
2. Watch it fail
3. Write minimal code to pass
4. Watch it pass
5. Refactor
6. Repeat
```

### For Existing Code (Reverse Engineer Tests)
```
1. Analyze implementation
2. Write test as if it were first
3. Verify test passes
4. Refactor for clarity
5. Repeat for each behavior
```

## Final Note

**For all new code, always use the Write Tests First ability.** The Reverse Engineer Tests ability is specifically for adding tests to existing code that was written without tests.

Following TDD principles from the start prevents the need for reverse engineering tests later.
