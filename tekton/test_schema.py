#!/usr/bin/env python3
"""Pytest-based validation for Tekton Pipeline and Task definitions.

This test suite validates generated Tekton YAML files against JSON schemas
without requiring a Kubernetes cluster.

Run with: pytest tekton/test_schema.py -v
"""

import json
from pathlib import Path
from typing import Dict, Optional, Tuple

import pytest
import yaml
from jsonschema import Draft4Validator

# Get paths relative to this file
SCRIPT_DIR = Path(__file__).parent
SCHEMAS_DIR = SCRIPT_DIR / "schemas"
TARGET_DIR = SCRIPT_DIR / "target"
TASKS_DIR = TARGET_DIR / "tasks"
PIPELINES_DIR = TARGET_DIR / "pipelines"


def load_schema(schema_path: Path) -> Dict:
    """Load JSON schema from file."""
    with open(schema_path, "r") as f:
        return json.load(f)


def load_yaml_file(file_path: Path) -> Dict:
    """Load and parse a YAML file."""
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def get_schema_for_resource(resource: Dict, schemas_dir: Path) -> Tuple[Optional[Dict], Optional[str]]:
    """Determine which schema to use for a resource."""
    api_version = resource.get("apiVersion", "")
    kind = resource.get("kind", "")

    # Determine version (v1 or v1beta1)
    if "v1beta1" in api_version:
        version = "v1beta1"
    elif "v1" in api_version:
        version = "v1"
    else:
        return None, f"Unsupported apiVersion: {api_version}"

    # Determine kind
    if kind not in ["Task", "Pipeline"]:
        return None, f"Unsupported kind: {kind}"

    # Load appropriate schema
    schema_file = schemas_dir / f"{version}_{kind}.json"
    if not schema_file.exists():
        return None, f"Schema file not found: {schema_file}"

    try:
        schema = load_schema(schema_file)
        return schema, None
    except Exception as e:
        return None, f"Failed to load schema: {str(e)}"


def validate_resource(resource: Dict, schema: Dict) -> Tuple[bool, str]:
    """Validate a Tekton resource against its schema."""
    validator = Draft4Validator(schema)
    errors = []

    for error in validator.iter_errors(resource):
        # Format error message with path
        path = ".".join(str(p) for p in error.path) if error.path else "root"
        errors.append(f"{path}: {error.message}")

    if errors:
        return False, "\n  ".join([""] + errors)
    return True, ""


def validate_file(file_path: Path, schemas_dir: Path) -> Tuple[bool, str]:
    """Validate a single Tekton YAML file."""
    try:
        resource = load_yaml_file(file_path)

        if not isinstance(resource, dict):
            return False, "File does not contain a valid YAML object"

        schema, error = get_schema_for_resource(resource, schemas_dir)
        if error or schema is None:
            return False, error or "Failed to load schema"

        is_valid, error_msg = validate_resource(resource, schema)
        return is_valid, error_msg

    except yaml.YAMLError as e:
        return False, f"YAML parsing error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


# Collect all task files
def get_task_files():
    """Get all task YAML files."""
    if not TASKS_DIR.exists():
        return []
    return sorted(TASKS_DIR.glob("*.yaml"))


def get_pipeline_files():
    """Get all pipeline YAML files."""
    if not PIPELINES_DIR.exists():
        return []
    return sorted(PIPELINES_DIR.glob("*.yaml"))


# Generate test IDs for better pytest output
def task_id(file_path):
    """Generate test ID for task file."""
    return file_path.name


def pipeline_id(file_path):
    """Generate test ID for pipeline file."""
    return file_path.name


# Parametrized tests
@pytest.mark.parametrize("task_file", get_task_files(), ids=task_id)
def test_task_schema(task_file):
    """Validate a Tekton Task against its JSON schema."""
    is_valid, error_msg = validate_file(task_file, SCHEMAS_DIR)
    assert is_valid, f"Schema validation failed:{error_msg}"


@pytest.mark.parametrize("pipeline_file", get_pipeline_files(), ids=pipeline_id)
def test_pipeline_schema(pipeline_file):
    """Validate a Tekton Pipeline against its JSON schema."""
    is_valid, error_msg = validate_file(pipeline_file, SCHEMAS_DIR)
    assert is_valid, f"Schema validation failed:{error_msg}"


if __name__ == "__main__":
    # Allow running directly for quick validation
    import sys

    # Check if directories exist
    if not TARGET_DIR.exists():
        print(f"❌ Error: Target directory not found: {TARGET_DIR}")
        sys.exit(1)

    if not SCHEMAS_DIR.exists():
        print(f"❌ Error: Schemas directory not found: {SCHEMAS_DIR}")
        sys.exit(1)

    # Run pytest programmatically
    pytest.main([__file__, "-v", "--tb=short"])

# Made with Bob
