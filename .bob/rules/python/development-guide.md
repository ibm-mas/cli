# Python Code Development Guide

## Key Rules
- **Modern Python:** Python 3.12 with type hints and dataclasses
- Use a **virtual environment** in `.venv`
- **Formatting:** Black with 160 character width
- **No Code Smells:** Flake8
- **Modular:** Break implmentation into small, reusable modules - limiting files to no more than **600** lines of code
- **Test-Driven Development:** Write tests **before** the implementation using the [test-driven-development](.bob/skills/test-driven-development) skill
- **pytest** with **pytest-coverage** is mandatory
- Test code **must also be documentated**: Each test function must have a docstring in the Given-When-Then format

## Virtual Environments
**CRITICAL:** Most Python commands (pytest, pip, python, etc.) MUST be run from within the project's virtual environment. **Exceptions:** black and flake8 are installed globally and do NOT require venv.

### Command Format
- **For commands requiring venv (pytest, pip, python):** `.venv/bin/<COMMAND>`
- **For black and flake8 (no venv needed):** `<COMMAND>`

**Why this matters:** Most Python packages (pytest, etc.) are installed in the venv, not globally. Black and flake8 are exceptions - they're installed globally for consistency across projects.


## Style Guide
### Naming Conventions
- Use `snake_case` for file names
- Use `snake_case` for module names
- Use `camelCase` for variable and function names
- Use `PascalCase` for class names.

### Import Organization
Organize imports in three groups:

```python
# 1. Standard library
import logging
import os
from datetime import datetime
from typing import Optional, Dict, List

# 2. Third-party packages
import requests
from kubernetes import client
from pymongo import MongoClient

# 3. Local imports
from mas.utils import exceptions
from mas.utils import violations
```

**Do not use inline imports**, all imports must be listed at the top of the file.

### Multiline Strings
For simple concatenation, use parentheses with implicit string joining:

```python
def function():
    message = (
        "This is a long message that spans multiple lines. "
        "Use parentheses for implicit string concatenation "
        "following PEP-8 style guidelines."
    )
```

Use `textwrap.dedent()` for multiline strings to maintain newlines, while preserving indentation:

```python
import textwrap

def function():
    configContent = textwrap.dedent(
        """\
        maximoappsuite:
          test-repo:
            branches:
              - main
              - develop
            rulesets:
              - python
        """
    )
```

### Copyright Headers
If `.copyright.yml` contains `validate: true` refer to the instructions in [copyright-statements.md](copyright-statements.md) to properly maintain copyright headers in all Python source files.

### Validation
After completing any significant unit of work use the [black-and-flake8](.bob/skills/black-and-flake8) skill command to format and lint the code

### Test Organization
- Name test files `tests/src/<module>/test_<module>_<feature>.py` (pytest requires unique file names across all directories)
- Limit individual test files to a maximum of **600** lines of code
- Place test data in `tests/resources/<module>`
- Use `conftest.py` for shared fixtures
- Use `pytest.mark` decorators for to denote tests requiring external dependencies that are not mocked, e.g. `mongodb`, `kafka`, `db2`
