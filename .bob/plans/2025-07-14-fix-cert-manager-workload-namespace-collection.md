# Fix cert-manager Resource Collection from Workload Namespaces

## Objective

Namespace-scoped cert-manager resources (`CertificateRequest`, `Certificate`, `Issuer`, `Order`, `Challenge`) are only being collected from the `cert-manager` and `cert-manager-operator` namespaces. They are actually created in workload namespaces (e.g. `mas-inst1-core`, `ibm-sls`). This plan fixes the collector to capture these resources across all namespaces using `allNamespaces=True`.

## Design Decisions

### Split CERT_MANAGER_RESOURCES into two lists

The current single `CERT_MANAGER_RESOURCES` list passes all resources to `generateNamespaceCollectionTasks`, which always collects them scoped to the operator namespace. We need two distinct lists:

**`CERT_MANAGER_NAMESPACE_RESOURCES`** — resources that exist only in the cert-manager operator namespaces (no workload footprint):
- `("operator.openshift.io/v1alpha1", "CertManager")`
- `("cert-manager.io/v1", "ClusterIssuer")`

**`CERT_MANAGER_ALL_NAMESPACE_RESOURCES`** — namespace-scoped resources that are created in workload namespaces and must be collected across all namespaces:
- `("cert-manager.io/v1", "CertificateRequest")`
- `("cert-manager.io/v1", "Certificate")`
- `("cert-manager.io/v1", "Issuer")`
- `("acme.cert-manager.io/v1", "Order")`
- `("acme.cert-manager.io/v1", "Challenge")`

### How `allNamespaces=True` works in `collectResources`

When `allNamespaces=True` is passed to [`collectResources`](python/src/mas/cli/must_gather/common/resources.py:66), it:
1. Calls `api.get()` with no namespace filter (all namespaces)
2. Writes output to `resources/_cluster/<resourceType>/all-namespaces.yaml`

This means all-namespace tasks must pass `None` as the namespace and `allNamespaces=True`. They are NOT compatible with `generateNamespaceCollectionTasks` (which always sets `allNamespaces=False`). The all-namespace tasks must be added directly to the plan.

### No changes needed in `app.py`, `task_generation.py`, or `resources.py`

The fix is entirely self-contained within `cert_manager.py` and its tests.

### Output structure

- Operator-namespace resources (namespace-scoped): `resources/cert-manager/<kind>s/<name>.yaml` (unchanged)
- All-namespace resources: `resources/_cluster/<kind>s/all-namespaces.yaml` (new)

## Critical Rules

- Do NOT modify `task_generation.py`, `resources.py`, or `app.py`
- Do NOT break the existing namespace-scoped collection for the operator namespaces
- The all-namespace collection group must be added once (not once per operator namespace)
- Track progress ONLY in this plan document, NOT in chat todo lists
- Run tests after every change

## Execution Plan

### Phase 1 — Update `cert_manager.py`

**Intent:** Split `CERT_MANAGER_RESOURCES` into two lists and add all-namespace collection tasks to the plan.

**Expected Outcomes:**
- `CERT_MANAGER_RESOURCES` is replaced by `CERT_MANAGER_NAMESPACE_RESOURCES` and `CERT_MANAGER_ALL_NAMESPACE_RESOURCES`
- `addCertManagerToCollectionPlan` adds a second group `"Certificate Manager (all namespaces)"` with tasks using `allNamespaces=True`
- Existing per-namespace groups for `cert-manager` and `cert-manager-operator` still collect `CertManager` and `ClusterIssuer`

**Todo List:**

- [x] **1.1** In [`cert_manager.py`](python/src/mas/cli/must_gather/dependencies/cert_manager.py), replace `CERT_MANAGER_RESOURCES` with two lists:
  - `CERT_MANAGER_NAMESPACE_RESOURCES` — `CertManager`, `ClusterIssuer`
  - `CERT_MANAGER_ALL_NAMESPACE_RESOURCES` — `CertificateRequest`, `Certificate`, `Issuer`, `Order`, `Challenge`
- [x] **1.2** Update `addCertManagerToCollectionPlan` to:
  - Pass `customResources=CERT_MANAGER_NAMESPACE_RESOURCES` to `generateNamespaceCollectionTasks` (replaces old `CERT_MANAGER_RESOURCES`)
  - After the per-namespace loop, add a new plan group `"Certificate Manager (all namespaces)"` with one task per resource in `CERT_MANAGER_ALL_NAMESPACE_RESOURCES`, each calling `collectResources(namespace=None, ..., allNamespaces=True)`
  - The all-namespace group should be added only when cert-manager namespaces are discovered (i.e. cert-manager is installed)
- [x] **1.3** Update the module docstring and function docstring to reflect the new behaviour
- [x] **1.4** Validate: run `flake8` and `black` on `cert_manager.py`

**Relevant Context:**
- [`cert_manager.py`](python/src/mas/cli/must_gather/dependencies/cert_manager.py) — file to modify
- [`resources.py:collectResources`](python/src/mas/cli/must_gather/common/resources.py:66) — accepts `namespace=None, allNamespaces=True`
- [`task_generation.py:generateNamespaceCollectionTasks`](python/src/mas/cli/must_gather/common/task_generation.py:24) — used for per-namespace tasks

**Status:** `[x] done`

---

### Phase 2 — Update existing tests and add new tests

**Intent:** Update `test_cert_manager_plan.py` to assert both the per-namespace groups AND the new all-namespace group. Add a focused new test confirming all-namespace task generation.

**Expected Outcomes:**
- All existing tests in `test_cert_manager_plan.py` and `test_cert_manager_discovery.py` continue to pass
- A new test asserts that `addCertManagerToCollectionPlan` adds the `"Certificate Manager (all namespaces)"` group when namespaces exist
- A new test confirms the all-namespace group is NOT added when no cert-manager namespaces exist
- A new test asserts that the all-namespace group tasks use `allNamespaces=True` (i.e. `collectResources` is called with `namespace=None` and `allNamespaces=True`)

**Todo List:**

- [x] **2.1** In [`test_cert_manager_plan.py`](python/tests/unit/must_gather/dependencies/test_cert_manager_plan.py), update `test_addCertManagerToCollectionPlan_adds_groups_for_discovered_namespaces`:
  - Changed assertion from `plan.total_groups == 2` to `plan.total_groups == 3` (2 namespace groups + 1 all-namespaces group)
- [x] **2.2** Added `test_addCertManagerToCollectionPlan_adds_all_namespace_group`
- [x] **2.3** Added `test_addCertManagerToCollectionPlan_no_all_namespace_group_when_no_cert_manager`
- [x] **2.4** Added `test_addCertManagerToCollectionPlan_all_namespace_tasks_use_allNamespaces_flag`
- [x] **2.5** Added `test_addCertManagerToCollectionPlan_namespace_groups_collect_clusterissuer_and_certmanager`
- [x] **2.6** Validate: 11/11 tests pass, flake8 clean, black formatted

**Relevant Context:**
- [`test_cert_manager_plan.py`](python/tests/unit/must_gather/dependencies/test_cert_manager_plan.py) — tests to update
- [`test_cert_manager_discovery.py`](python/tests/unit/must_gather/dependencies/test_cert_manager_discovery.py) — discovery tests (no changes expected)
- [`collection_plan.py`](python/src/mas/cli/must_gather/collection_plan.py) — use `plan.groups` to inspect group names

**Status:** `[x] done`

---

## Final Validation

```bash
.venv/bin/pytest python/tests/unit/must_gather/dependencies/test_cert_manager_plan.py python/tests/unit/must_gather/dependencies/test_cert_manager_discovery.py -v
```

**Success criteria:**
- All existing tests pass with no regressions
- New tests for all-namespace group pass
- `flake8 python/src/mas/cli/must_gather/dependencies/cert_manager.py` reports no issues
- `black --check --line-length 160 python/src/mas/cli/must_gather/dependencies/cert_manager.py` reports no issues
