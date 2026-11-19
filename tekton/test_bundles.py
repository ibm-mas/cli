#!/usr/bin/env python3

# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/v10.html
#
# *****************************************************************************

"""Pytest-based validation of the Tekton bundle partition.

The build (build/bin/build-tekton.sh) concatenates the generated Tekton
definitions into three bundles:

- ibm-mas-tekton.yaml        main (suite, dependencies, OCP, framework, AI Service)
- ibm-mas-tekton-fvt.yaml    FVT/IVT
- ibm-mas-tekton-gitops.yaml all gitops- prefixed tasks and pipelines

This test suite validates that:

1. Every generated task/pipeline lands in exactly one of the three bundles
2. No gitops- prefixed resource remains in the main or FVT bundles
3. The gitops bundle contains exactly the gitops- prefixed resources,
   including the gitops-*-fvt-preparer resources that were previously routed
   to the FVT bundle
4. Every taskRef in a bundle's pipelines resolves to a Task in that same
   bundle or in the main bundle (gitops/FVT bundles are layered on top of the
   main bundle)

Note: the deprovision-aiservice-deps pipeline templates under
src/pipelines/gitops have filenames without the gitops- prefix, so
build-tekton.sh routes them to the gitops bundle with an explicit case match;
the Pipeline resources they generate are named with the gitops- prefix and are
therefore covered by the prefix-based assertions below.

The gitops bundle is additive over the main bundle: gitops pipelines reference
mas-devops-* framework tasks from the main bundle, so consumers must apply the
main bundle before the gitops bundle.

Run with: pytest tekton/test_bundles.py -v
"""

from pathlib import Path
from typing import Dict, List, Set, Tuple

import pytest
import yaml

# Get paths relative to this file
SCRIPT_DIR = Path(__file__).parent
TARGET_DIR = SCRIPT_DIR / "target"
TASKS_DIR = TARGET_DIR / "tasks"
PIPELINES_DIR = TARGET_DIR / "pipelines"

MAIN_BUNDLE = TARGET_DIR / "ibm-mas-tekton.yaml"
FVT_BUNDLE = TARGET_DIR / "ibm-mas-tekton-fvt.yaml"
GITOPS_BUNDLE = TARGET_DIR / "ibm-mas-tekton-gitops.yaml"

# Resources containing 'fvt-' that are nevertheless gitops resources and must
# be routed to the gitops bundle (the gitops- prefix takes priority over the
# fvt- pattern in build-tekton.sh).  Note that the gitops-aiservice-fvt-preparer
# task/pipeline templates exist under src/ but are not currently included in
# the generation playbooks, so they are not asserted here.
FVT_PREPARER_RESOURCES = {
    "gitops-mas-fvt-preparer",
    "gitops-mas-fvt-preparer-pipeline",
}


def load_bundle_resources(file_path: Path) -> List[Tuple[str, str]]:
    """Load all (kind, name) resource pairs from a multi-document bundle."""
    resources: List[Tuple[str, str]] = []
    with open(file_path, "r") as f:
        # The bundles start with an empty line, which yields None documents
        for doc in yaml.safe_load_all(f):
            if not isinstance(doc, dict):
                continue
            kind = doc.get("kind")
            name = doc.get("metadata", {}).get("name")
            if kind and name:
                resources.append((kind, name))
    return resources


def load_generated_resources(directory: Path) -> Set[Tuple[str, str]]:
    """Load all (kind, name) resource pairs from generated definition files."""
    resources: Set[Tuple[str, str]] = set()
    if not directory.exists():
        return resources
    for file_path in sorted(directory.glob("*.yaml")):
        with open(file_path, "r") as f:
            doc = yaml.safe_load(f)
        if isinstance(doc, dict):
            kind = doc.get("kind")
            name = doc.get("metadata", {}).get("name")
            if kind and name:
                resources.add((kind, name))
    return resources


def get_task_refs(resource: Dict) -> Set[str]:
    """Extract all taskRef names referenced by a Pipeline resource."""
    refs: Set[str] = set()
    spec = resource.get("spec", {})
    for task in spec.get("tasks", []) + spec.get("finally", []):
        task_ref = task.get("taskRef", {})
        name = task_ref.get("name")
        if name:
            refs.add(name)
    return refs


def bundles_exist() -> bool:
    """Check whether the bundles have been built."""
    return MAIN_BUNDLE.exists() and FVT_BUNDLE.exists() and GITOPS_BUNDLE.exists()


pytestmark = pytest.mark.skipif(
    not bundles_exist(),
    reason="Tekton bundles not built (run: make tekton)",
)


@pytest.fixture(scope="module")
def bundle_resources() -> Dict[str, List[Tuple[str, str]]]:
    """Load the (kind, name) resources from each of the three bundles."""
    return {
        "main": load_bundle_resources(MAIN_BUNDLE),
        "fvt": load_bundle_resources(FVT_BUNDLE),
        "gitops": load_bundle_resources(GITOPS_BUNDLE),
    }


@pytest.fixture(scope="module")
def generated_tasks() -> Set[Tuple[str, str]]:
    return load_generated_resources(TASKS_DIR)


@pytest.fixture(scope="module")
def generated_pipelines() -> Set[Tuple[str, str]]:
    return load_generated_resources(PIPELINES_DIR)


def test_every_resource_in_exactly_one_bundle(bundle_resources, generated_tasks, generated_pipelines):
    """Every generated task/pipeline must appear in exactly one bundle."""
    expected = generated_tasks | generated_pipelines
    assert expected, "No generated resources found in tekton/target"

    # Locate each resource across the three bundles
    placement: Dict[Tuple[str, str], List[str]] = {}
    for bundle, resources in bundle_resources.items():
        for resource in resources:
            placement.setdefault(resource, []).append(bundle)

    missing = expected - set(placement.keys())
    assert not missing, f"Generated resources missing from all bundles: {sorted(missing)}"

    unexpected = set(placement.keys()) - expected
    assert not unexpected, f"Resources in bundles but not generated: {sorted(unexpected)}"

    duplicated = {r: b for r, b in placement.items() if len(b) > 1}
    assert not duplicated, f"Resources present in multiple bundles: {duplicated}"


def test_no_gitops_resources_in_main_or_fvt_bundle(bundle_resources):
    """No gitops- prefixed resource may remain in the main or FVT bundles."""
    for bundle in ("main", "fvt"):
        gitops_resources = [name for (kind, name) in bundle_resources[bundle] if name.startswith("gitops-")]
        assert not gitops_resources, f"gitops- prefixed resources found in the {bundle} bundle: {gitops_resources}"


def test_gitops_bundle_contents(bundle_resources, generated_tasks, generated_pipelines):
    """The gitops bundle must contain exactly the gitops- prefixed resources."""
    expected = {(kind, name) for (kind, name) in generated_tasks | generated_pipelines if name.startswith("gitops-")}
    actual = set(bundle_resources["gitops"])
    assert actual == expected, f"gitops bundle mismatch: missing={sorted(expected - actual)} " f"unexpected={sorted(actual - expected)}"


def test_fvt_preparers_in_gitops_bundle(bundle_resources):
    """The gitops-*-fvt-preparer resources belong to the gitops bundle, not FVT."""
    gitops_names = {name for (kind, name) in bundle_resources["gitops"]}
    fvt_names = {name for (kind, name) in bundle_resources["fvt"]}

    for resource in FVT_PREPARER_RESOURCES:
        assert resource in gitops_names, f"{resource} not found in gitops bundle"
        assert resource not in fvt_names, f"{resource} still present in FVT bundle"


@pytest.mark.parametrize(
    "bundle_file,bundle_key",
    [
        (MAIN_BUNDLE, "main"),
        (FVT_BUNDLE, "fvt"),
        (GITOPS_BUNDLE, "gitops"),
    ],
)
def test_pipeline_taskrefs_resolvable(bundle_file, bundle_key, bundle_resources):
    """Every taskRef in a bundle's pipelines must resolve to a Task in that
    bundle or in the main bundle."""
    main_tasks = {name for (kind, name) in bundle_resources["main"] if kind == "Task"}
    own_tasks = {name for (kind, name) in bundle_resources[bundle_key] if kind == "Task"}
    available_tasks = main_tasks | own_tasks

    with open(bundle_file, "r") as f:
        for doc in yaml.safe_load_all(f):
            if not isinstance(doc, dict) or doc.get("kind") != "Pipeline":
                continue
            pipeline_name = doc.get("metadata", {}).get("name")
            for ref in get_task_refs(doc):
                assert ref in available_tasks, (
                    f"Pipeline {pipeline_name} in {bundle_file.name} references " f"task {ref} which is not available in this bundle or the main bundle"
                )


if __name__ == "__main__":
    # Allow running directly for quick validation
    import sys

    if not bundles_exist():
        print(f"❌ Error: Tekton bundles not found in {TARGET_DIR}")
        sys.exit(1)

    pytest.main([__file__, "-v", "--tb=short"])
