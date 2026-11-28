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


def _role_steps(task_spec: Dict) -> List[Dict]:
    """Return the steps of a task spec that invoke run-role.sh (the ansible role runner)."""
    return [step for step in task_spec.get("steps", []) if any("run-role.sh" in part for part in step.get("command", []) or [])]


def _load_yaml(path: Path) -> Dict:
    with open(path, "r") as f:
        doc = yaml.safe_load(f)
    assert isinstance(doc, dict), f"{path} did not parse as a single YAML document"
    return doc


def _task_param(task: Dict, name: str):
    """Return the value of a pipeline task's param, or None when not set."""
    for param in task.get("params", []) or []:
        if param.get("name") == name:
            return param.get("value")
    return None


def test_ocp_verify_tasks_declare_approval_gate_param():
    """Both ocp-verify tasks declare verify_subscription_approvals, defaulting to False.

    The OLM approval gate (the cluster-wide wait for manual install plan
    approvals) must be off in every verification-only context: pre-flight and
    final checks must not invite an approval workflow. The gate reaches the
    ocp_verify role through the VERIFY_SUBSCRIPTION_APPROVALS env var, bound
    to this task param.
    """
    task_files = sorted(TASKS_DIR.glob("ocp-verify*.yaml"))
    assert task_files, "No ocp-verify* tasks found in tekton/target — did the build run?"

    for task_file in task_files:
        doc = _load_yaml(task_file)
        task_name = doc.get("metadata", {}).get("name")
        params = {p.get("name"): p for p in doc.get("spec", {}).get("params", [])}

        gate = params.get("verify_subscription_approvals")
        assert gate is not None, f"{task_name}: missing the verify_subscription_approvals param"
        assert gate.get("default") == "False", f"{task_name}: verify_subscription_approvals must default to False (found {gate.get('default')})"

        # The env binding must exist wherever VERIFY_SUBSCRIPTIONS is bound
        # (the ocp-verify-all task binds it per-step; ocp-verify in the
        # stepTemplate)
        doc_text = task_file.read_text()
        assert "VERIFY_SUBSCRIPTION_APPROVALS" in doc_text, f"{task_name}: VERIFY_SUBSCRIPTION_APPROVALS env is not bound to the param"


def test_approval_gate_enabled_only_in_update_post_verify():
    """The approval gate is enabled in exactly one place: mas-update's post-update-verify.

    The catalog digest update rolls every subscription on the cluster
    implicitly, so post-update-verify is the one context where waiting for
    the manual approvals is the job. Every other ocp-verify usage (pre and
    post checks in install, update and upgrade pipelines) must leave the
    gate off.
    """
    enabled = []
    for pipeline_file in sorted(PIPELINES_DIR.glob("*.yaml")):
        doc = _load_yaml(pipeline_file)
        if doc.get("kind") != "Pipeline":
            continue
        pipeline_name = doc.get("metadata", {}).get("name")
        for task in doc.get("spec", {}).get("tasks", []) or []:
            value = _task_param(task, "verify_subscription_approvals")
            if value is not None and str(value).lower() == "true":
                enabled.append(f"{pipeline_name}/{task.get('name')}")

    assert enabled == ["mas-update/post-update-verify"], f"The approval gate must be enabled only in mas-update's post-update-verify, found: {enabled}"

    # And within mas-update, the other two ocp-verify-all usages are off
    update = _load_yaml(PIPELINES_DIR / "mas-update.yaml")
    tasks = {task["name"]: task for task in update["spec"]["tasks"]}
    for task_name in ("pre-update-check", "post-deps-update-verify"):
        value = _task_param(tasks[task_name], "verify_subscription_approvals")
        assert value == "False", f"mas-update/{task_name}: the approval gate must be off (found {value})"
    assert _task_param(tasks["post-update-verify"], "verify_subscription_approvals") == "True"


def test_run_role_tasks_declare_olm_approval_env():
    """Every task whose steps invoke run-role.sh must plumb the OLM approval params.

    The OLM install plan approval mode reaches the ansible collection via the
    OLM_APPROVAL_MODE / OLM_APPROVAL_TIMEOUT environment variables, which are
    bound to the olm_approval_mode / olm_approval_timeout task params (either
    in the stepTemplate or per-step). Tasks that run roles but miss this
    plumbing silently ignore the approval mode, so this test prevents new
    tasks (or refactors that drop the common cli-env partials) from
    regressing the coverage.
    """
    expected_env = {
        "OLM_APPROVAL_MODE": "$(params.olm_approval_mode)",
        "OLM_APPROVAL_TIMEOUT": "$(params.olm_approval_timeout)",
    }
    checked = 0
    failures: List[str] = []

    for task_file in sorted(TASKS_DIR.glob("*.yaml")):
        with open(task_file, "r") as f:
            doc = yaml.safe_load(f)
        if not isinstance(doc, dict) or doc.get("kind") != "Task":
            continue

        spec = doc.get("spec", {})
        role_steps = _role_steps(spec)
        if not role_steps:
            continue
        checked += 1
        task_name = doc.get("metadata", {}).get("name")

        # The task must declare the params the env entries bind to
        declared_params = {p.get("name") for p in spec.get("params", [])}
        for param in ("olm_approval_mode", "olm_approval_timeout"):
            if param not in declared_params:
                failures.append(f"{task_name}: task does not declare the {param} param")

        # Every role-running step must see the env entries (from its own env
        # block or the task's stepTemplate), bound to the params
        template_env = {e.get("name"): e.get("value") for e in (spec.get("stepTemplate", {}) or {}).get("env", []) or []}
        for step in role_steps:
            step_env = {e.get("name"): e.get("value") for e in step.get("env", []) or []}
            effective = {**template_env, **step_env}
            for env_name, expected_value in expected_env.items():
                if env_name not in effective:
                    failures.append(f"{task_name} / step {step.get('name')}: missing the {env_name} env entry")
                elif effective[env_name] != expected_value:
                    failures.append(f"{task_name} / step {step.get('name')}: {env_name} is not bound to {expected_value} (found {effective[env_name]})")

    assert checked, "No run-role.sh tasks found in tekton/target — did the build run?"
    assert not failures, "Tasks running ansible roles without the OLM approval plumbing:\n  " + "\n  ".join(sorted(set(failures)))


if __name__ == "__main__":
    # Allow running directly for quick validation
    import sys

    if not bundles_exist():
        print(f"❌ Error: Tekton bundles not found in {TARGET_DIR}")
        sys.exit(1)

    pytest.main([__file__, "-v", "--tb=short"])
