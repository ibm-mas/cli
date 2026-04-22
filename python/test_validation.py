#!/usr/bin/env python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from prompt_toolkit.document import Document
from prompt_toolkit.validation import ValidationError
from mas.cli.validators import CustomizationArchiveNameValidator

validator = CustomizationArchiveNameValidator()

# Test valid names
for name in ["CustomArchive", "test-123", "my_archive.zip"]:
    try:
        validator.validate(Document(text=name))
        print(f"✅ '{name}' passed")
    except ValidationError as e:
        print(f"❌ '{name}' failed: {e.message}")

# Test invalid names  
for name in ["Custom Archive", "-test", "_test"]:
    try:
        validator.validate(Document(text=name))
        print(f"❌ '{name}' should have failed")
    except ValidationError:
        print(f"✅ '{name}' correctly rejected")
