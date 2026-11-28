# OLM Approvals — Full-Scope Cluster Gate + ocp_verify Mode Separation

> On approval, copy this plan to `cli/.bob/plans/2026-11-24-cluster-wide-approval-gate-full-scope.md` per the plans convention (a local file write only).

## Context

Two problems with the cluster-wide approval gate as it stands on `manualsubs`:

1. **Disclosure is serial.** The cluster-wide branch of `wait_for_subscription_approval` discovers all namespaces with pending plans, then waits on them one at a time — the user only sees namespace N's approvals once namespaces 1..N-1 have converged. Controlling rollout order is a main reason Manual approval exists; hiding the full scope defeats it.
2. **The gate piggybacks on `verify_subscriptions`.** The `ocp_verify` role runs `wait_for_subscription_approval` under `when: verify_subscriptions`, and that flag is on in **every** `ocp_verify` invocation: `pre-update-check`, `post-update-verify`, `post-deps-update-verify` (mas-update), `pre-install-check`/`post-install-verify` (mas-install), and both checks in the upgrade pipelines. Since the CLI sets `OLM_APPROVAL_MODE=Manual` pipeline-wide on manual-approval clusters, all of those would *wait and invite approval*. A pre-flight check should not offer to start an approval workflow seconds before the catalog changes; a final post-install check finding pending approvals means something went wrong.

**Changes (decided with the user):**

- **A. Full-scope unified wait** — after discovery, print every pending install plan across every namespace up front (grouped by namespace, with `oc patch` commands), then one multi-namespace poll loop; each poll re-checks all in-scope namespaces and re-runs pending-plan discovery. Gate returns when all in-scope namespaces converge. Per-namespace timeout budget, clock starting when the namespace is first observed (gate start for discovered namespaces).
- **B. `ocp_verify` mode separation** — new role variable `verify_subscription_approvals` (default **False**), gating the approval wait, ordered **before** `verify_subscriptions`. Enabled in exactly one place: mas-update's `post-update-verify` — the one context where subscriptions roll implicitly and waiting is the job.

**Descoped (user decision):** `verify_subscriptions` keeps its current behavior unchanged — no channel-head ("expected CSV") assertions, no pending-plan fail-fast. With the gate off, the verify tasks do exactly what they did before the manual-approvals work. (Consequence: a verify context with a leftover pending plan under Manual passes as today — `UpgradePending`+Manual is accepted. If we later want verify contexts to *fail* on pending approvals, that's a follow-up.)

Scope: **ansible-devops** (role, action plugin, module_utils) + **cli tekton wiring** (task params, taskdefs, mas-update enablement). No python-devops changes (existing `olm.py` primitives reused as-is); no CLI python changes (fire-and-forget).

## Design

### 1. ansible-devops `roles/ocp_verify` — new flag

**`defaults/main.yml`** — add:

```yaml
verify_subscription_approvals: "{{ lookup('env', 'VERIFY_SUBSCRIPTION_APPROVALS') | default('False', True) | bool }}"
```

**`tasks/main.yml`** — the "Wait for install plan approval" task keeps its position above "Check Subscription Status" but its `when:` changes from `verify_subscriptions` to `verify_subscription_approvals`. Rewrite the comment: the gate is the update's convergence point, enabled only where waiting is the job (`post-update-verify`); everywhere else it does not run. `verify_subscriptions` is untouched.

### 2. ansible-devops `plugins/module_utils/olm_approvals.py` — new `waitForClusterApproval`

`waitForClusterApproval(dynClient, display, timeout=None, pollInterval=30, approvalMode=None) -> dict`

1. **Settle** — `waitForSubscriptionResolution(dynClient, None)` (unchanged; stale-manifest protection after catalog digest updates).
2. **Initial discovery** — `getPendingInstallPlans(dynClient, None)` → initial scope. Nothing pending → early return `{waited: False, namespaces: [], statuses: {}}`.
3. **Mode handling on the initial snapshot:**
   - Non-Manual context (including unset) with pending plans → `ValueError` listing the approve commands from **all** namespaces at once (today only the first namespace's error surfaces), plus the `OLM_APPROVAL_MODE=Manual` remedy.
   - Manual context → print the **up-front full-scope report**: header ("N install plan(s) awaiting manual approval across M namespaces — approve them in any order"), then per namespace (sorted) the `formatApprovalNotice` lines for each pending plan. Seed `seenPlanNames` with every (namespace, installPlan) pair.
   - Mixed-mode namespaces: existing notice + treated as Manual (unchanged).
4. **Unified poll loop** (local `while` loop; reuses the same snapshot functions, not the single-namespace `waitForSubscriptionConvergence`):
   - Each poll: re-run `getPendingInstallPlans(None)` — a namespace with a newly-pending plan joins the scope and gets its deadline assigned then; then `getNamespaceConvergenceStatus(dynClient, ns)` for every in-scope namespace.
   - **Late mode-mismatch**: pending plans in a non-Manual context appearing mid-wait → same `ValueError`.
   - **New-plan notices** (Manual): diff each namespace's `pendingApprovals` against `seenPlanNames`; print `formatApprovalNotice` for new ones, including new plans in already-scoped namespaces (multi-step upgrade paths).
   - **Fail-fast**: any `resolutionError` or `failedInstallPlans` in an in-scope namespace → `OLMException` naming namespace, subscription/plan.
   - **Scope removal only on convergence** (`status["converged"]` is True) — never remove a namespace just because pending-plan discovery no longer lists it (an approved plan can still be rolling out).
   - **Heartbeat** every `STATUS_INTERVAL`: "Waiting for install plan approval since X — outstanding: ns1 (2 plans, deadline 16:02), ns2 (1 plan, deadline 15:47)".
   - **Deadline expiry** (any in-scope namespace past its deadline) → `OLMTimeoutError` listing every still-outstanding namespace, each with its non-converged subscriptions (`installedCSV -> targetCSV`) and, under Manual, the repeated approve commands.
5. **Return** — `{waited: bool, namespaces: [all ever in scope], statuses: {ns: final convergence status}}`.

Reuse: `formatApprovalNotice`, `approveCommand`, `STATUS_INTERVAL`, `_formatTimestamp`. No new constants. Timeout resolution stays with the caller (`resolveApprovalTimeout`); the per-namespace budget equals the resolved timeout.

### 3. ansible-devops `plugins/action/wait_for_subscription_approval.py`

- **Namespace mode: unchanged** (single `waitForSubscriptionApproval` call — the per-namespace waits used by individual roles are not touched).
- **Cluster-wide mode**: single call to `waitForClusterApproval`. Keep the `OLMTimeoutError`/`OLMException`/`ValueError` → `AnsibleError` translation and the honest `waited`-based final message ("All install plan approvals have been granted in: …" / "No install plans are waiting for approval"), extended with "and all subscriptions are at their channel head".
- Update docstring/usage: cluster-wide mode shows the full scope up front; approvals may be granted in any order.

### 4. cli tekton wiring

| File | Change |
|---|---|
| `tekton/src/tasks/ocp/ocp-verify-all.yml.j2` | New task param `verify_subscription_approvals` (string, default `"False"`); add `VERIFY_SUBSCRIPTION_APPROVALS: $(params.verify_subscription_approvals)` env to the **ocp-verify-subscriptions** step only (the role orders gate-before-verify internally, in the same step/pod) |
| `tekton/src/tasks/ocp/ocp-verify.yml.j2` | Same new param (default `"False"`) + env in `stepTemplate` (symmetry; install pipeline never enables it) |
| `tekton/src/pipelines/taskdefs/cluster-setup/ocp-verify-all.yml.j2` | Pass `verify_subscription_approvals: "{{ verify_subscription_approvals | default('False') }}"` |
| `tekton/src/pipelines/taskdefs/cluster-setup/ocp-verify.yml.j2` | Same passthrough |
| `tekton/src/pipelines/mas-update.yml.j2` | `post-update-verify` invocation adds `'verify_subscription_approvals': 'True'` to the taskdef `template_vars` — the **only** enablement. `pre-update-check` and `post-deps-update-verify` stay default-False |

Enablement matrix (all other `ocp_verify` uses run gate-off, restoring their pre-manualsubs verify-only behavior):

| Pipeline task | verify_subscription_approvals |
|---|---|
| mas-update `post-update-verify` | **True** |
| mas-update `pre-update-check`, `post-deps-update-verify` | False |
| mas-install `pre-install-check`, `post-install-verify` | False |
| mas-upgrade / aiservice-upgrade pre & post checks | False |

### 5. Tests

**ansible-devops `ibm/mas_devops/tests/unit/plugins/module_utils/test_olm_approvals.py`** — new `TestWaitForClusterApproval` (existing harness mocks `mas.devops.olm` at module_utils level; extend `makeStatus`/`makeSubscriptionEntry` usage, don't replace):
- Nothing pending after settle → immediate success, `waited=False`, no notices.
- Up-front report: notices for **all** namespaces' plans printed exactly once, before any waiting.
- Any-order convergence: namespaces converge out of order — gate returns only when all converge; no serial blocking.
- Late entrant: discovery returns a new namespace on poll 2 → joins scope, notices, deadline from first observation.
- New plan mid-wait in an already-scoped namespace → notice fires (seenPlanNames diff).
- Mode mismatch at discovery (Automatic context) → `ValueError` with commands from all namespaces; late mismatch mid-wait → same.
- Mixed-mode namespace → notice, treated as Manual.
- `resolutionError`/`failedInstallPlans` fail-fast names the namespace.
- Deadline expiry → `OLMTimeoutError` listing every outstanding namespace with subs + commands.
- Heartbeat names all outstanding namespaces; settle-before-discover ordering (`["settle", "discover"]`) asserted here (moved from the action-level test).

**`tests/unit/plugins/action/test_wait_for_subscription_approval.py`**: cluster-wide tests updated for the single `waitForClusterApproval` call shape; no-op test unchanged in spirit.

**cli `tekton/test_bundles.py`**: assert the new param exists on both ocp-verify tasks, defaults False, and that only mas-update's post-update-verify sets it True.

### 6. Docs

ansible-devops `docs/olm-manual-approvals.md`: cluster-wide gate section rewritten — full-scope up-front report, any-order approvals, per-namespace budgets from first observation, mid-wait re-discovery; new `verify_subscription_approvals` role variable and the verify-vs-wait separation (the gate runs only where waiting is the job).

## Verification

1. **Unit tests** (WSL, explicit `/mnt/c` paths):
   - `wsl bash -lc 'cd /mnt/c/Users/097891866/Documents/GitHub/ibm-mas/ansible-devops/ibm/mas_devops/tests && python -m pytest unit/plugins -v'` (2 pre-existing `aiservice_upgrade` subprocess-timeout failures are baseline)
   - cli tekton bundle tests — match the existing CI invocation for `tekton/test_bundles.py`
2. **Rendered-pipeline check**: regenerate the tekton bundle and inspect the rendered `mas-update` pipeline — `post-update-verify` carries `verify_subscription_approvals: "True"`, the other two ocp-verify-all usages carry `"False"`.
3. **Cluster E2E** (rebuild the `manualsubs` CLI image bundling collection + mas-devops): multi-MAS-installation cluster under Manual approval —
   - `pre-update-check` with a leftover pending plan → no approval waiting is initiated (gate does not run; verify behaves as it did pre-manualsubs).
   - `post-update-verify` → full-scope report (every namespace, every plan) at once; approve namespaces in reverse order; gate converges only when all done; dependency tasks start only after.
   - Automatic cluster: `post-update-verify` gate still fail-fasts on pending plans (mode-mismatch), as today.
4. Copy this plan to `cli/.bob/plans/2026-11-24-cluster-wide-approval-gate-full-scope.md`.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Concurrent budgets burn while the user favours one namespace | Accepted: per-namespace deadline from first observation; timeout error names everything outstanding. |
| Verify contexts no longer surface pending approvals at all (descoped brains) | Accepted descope: identical to pre-manualsubs behavior. Follow-up candidate if it bites. |
| Re-discovery each poll adds API churn | One cluster-wide install-plan list + one snapshot per in-scope namespace per 30s poll — same order as today's serial loop, interleaved. |
| A converged namespace regresses (new plan appears) | Re-discovery re-adds it to scope; notice fires via the seenPlanNames diff. |
| Unrelated stuck sub in a shared namespace blocks the gate | Unchanged: scope is pending-plan-based (never convergence-based), bounded by the per-namespace deadline, fail-fast on ResolutionFailed/Failed plans. |

## Non-goals

- `verify_subscriptions` changes of any kind (descoped by user decision — no channel-head assertions, no pending-plan fail-fast).
- Changing the gate's pending-plan-based scope rule (unrelated converged subscriptions in `openshift-operators` and friends never enter scope).
- Namespace-mode waits used by individual roles (`suite_upgrade`, `dro`, `cp4d`, …) — unchanged.
- Any CLI-side waiting, reporting, or log streaming.
