# OLM Manual Approvals — Close the Install Plan Generation Race

## Context

The cluster E2E verification of the manual-approvals work (`tmp/dro.log`, 2026-11-23) failed: the dro role created both Subscriptions (`ibm-metrics-operator` at 11:12:51, `ibm-data-reporter-operator` at 11:12:53) with `installPlanApproval: Manual`, then the "Wait for install plan approval" task returned success in ~0.09s claiming "All install plan approvals have been granted" — before OLM had generated the InstallPlans. No approval notice was ever shown, nothing was approved, and the run hung retrying on the `marketplaceconfigs` CRD wait.

Root cause — a snapshot race in the approval gate:

- Template-based roles (dro, eck, kafka, cp4d, ocs, nvidia_gpu, ocp_efs, turbonomic — 21 task files) create Subscriptions via `kubernetes.core.k8s` templates then immediately call `ibm.mas_devops.wait_for_subscription_approval`.
- `waitForSubscriptionApproval` (ansible-devops `plugins/module_utils/olm_approvals.py:105`) is a "cheap no-op when nothing is pending": one `getNamespaceApprovalStatus` snapshot, return when `blocking` is False.
- `getNamespaceApprovalStatus` (python-devops `src/mas/devops/olm.py:560`) computes `blocking` only from InstallPlans that already exist in `RequiresApproval` — a just-created Subscription with no InstallPlan yet reads as "nothing blocking".
- Contrast: `applySubscription` (olm.py:941-949) waits for InstallPlan creation first, so the ~20 `apply_subscription`-based roles are unaffected. In Automatic mode the race is harmless (OLM approves by itself), which is why it only surfaced now.

The cluster-wide mode of the gate (namespace omitted — the `ocp_verify` gate used by `mas update` after catalog digest updates) has the same race in principle: it discovers namespaces by listing already-existing pending InstallPlans.

A second instance of the same bug, surfaced during plan review: the upgrade/update flows (`suite_upgrade`, `suite_app_upgrade`, `aiservice_upgrade`, kafka upgrade) patch an existing Subscription's channel then immediately call the gate — the old `installPlanRef` (pointing at the already-Completed plan) is present throughout, so any presence-based wait passes instantly on the stale ref and the pending new plan can be missed. Their downstream `installPlanGeneration`-bump checks accept `UpgradePending` under Manual, so a vacuously-passed gate lets the flow march on with an unapproved plan. Note OLM never clears `installPlanRef` on patch — it replaces it atomically and bumps `installPlanGeneration` (suite_upgrade's before/after generation comparison relies on this), so there is no reverse race (no false wait on idempotent re-runs).

Decisions made with the user:
- Generation/settle waits get a **dedicated 600s ceiling** (not the 7200s human-approval budget), as fixed constants — no env var, no task argument, nothing configurable.
- **Fix both** the namespace-mode and cluster-wide gates, covering both the fresh-Subscription and patched-Subscription cases.

No CLI changes are needed — the CLI already passes `OLM_APPROVAL_MODE`/`OLM_APPROVAL_TIMEOUT` through; the gap is entirely in python-devops + ansible-devops.

**Branches:** `manualsubs` in python-devops and ansible-devops (cross-repo rule from CONTRIBUTING.md / the 2026-11-21 plan).

## Design

### 1. python-devops — two new helpers in `src/mas/devops/olm.py`

Follow the existing poll-loop style of `waitForNamespaceApprovals` (olm.py:640).

**`waitForSubscriptionInstallPlans(dynClient, namespace, timeout=600, pollInterval=15)`** — the fresh-Subscription fix:
- Poll Subscriptions in the namespace until every one has `status.installPlanRef` (OLM's signal that it generated the plan). A settled Subscription already has it, so this only waits on genuinely fresh ones (normally seconds).
- On timeout raise `OLMTimeoutError` naming the Subscriptions still missing refs, with a remedy hint (`oc get subscription -n <ns>` and check catalog/operator-lifecycle-manager health). Fatal — a just-created Subscription must produce a plan.

**`waitForSubscriptionResolution(dynClient, namespace=None, timeout=600, pollInterval=15, quietPolls=4)`** — the settle poll, used for both the patched-Subscription and cluster-wide cases:
- Snapshot each Subscription's `(status.state, status.installPlanRef, status.installedCSV, status.installPlanGeneration, status.currentCSV)`; return once `quietPolls` consecutive snapshots are identical (~1 min of quiet ⇒ no change is coming). Ignore `catalogHealth`-style noise — only the resolution fields count.
- Timeout is **non-fatal**: log a warning and return (no change coming is a legitimate outcome; the caller proceeds with whatever is visible, matching today's behavior).

### 2. ansible-devops — `plugins/module_utils/olm_approvals.py`

- `waitForSubscriptionApproval` (namespace mode), when `status["approvalMode"]` is `"Manual"` or `"Mixed"`:
  1. If any Subscription lacks `installPlanRef` → `waitForSubscriptionInstallPlans` (fatal at 600s). If **all** Subscriptions were fresh (no ref at entry), the ref's appearance is the resolution event — skip the settle and go straight to the blocking check (dro-style installs pay seconds, not a minute).
  2. If any Subscription already had a ref at entry (untouched or just-patched — indistinguishable) → `waitForSubscriptionResolution` settle poll before the blocking check (upgrade-style flows: ~1 min; catches the new plan a channel change generates).
  3. Re-snapshot and run the blocking check as today. This also makes the Automatic-mode mismatch fail-fast reliable (pending plans are seen instead of raced past).
  Automatic/None-mode namespaces keep today's instant no-op. The 600s budgets are plain constants in python-devops — no task argument, no env var, nothing to configure.
- Add `waited` (bool) to the returned status dict — True only when the human wait path actually ran — so the plugin can stop claiming "approvals have been granted" when nothing was ever pending.

### 3. ansible-devops — `plugins/action/wait_for_subscription_approval.py`

- Cluster-wide branch: call `waitForSubscriptionResolution(dynClient, None, ...)` before `getPendingInstallPlans` (no refactor — the discovery/per-namespace logic stays where it is).
- Fix the success message: `"All install plan approvals have been granted in: ..."` only when something was actually waited on (`waited`); otherwise `"No install plans are waiting for approval"`.

### 4. Docs — ansible-devops `docs/olm-manual-approvals.md`

New "Install plan generation" subsection under Timeout semantics: the gate first waits for OLM to generate install plans for just-created Subscriptions (fixed 600s budget, not configurable), and the cluster-wide gate settles on subscription status stability before concluding nothing is pending. Support matrix: note the template-based dependency roles' creation→generation race is closed.

## Files to modify

| Repo | File | Change |
|---|---|---|
| python-devops | `src/mas/devops/olm.py` | `waitForSubscriptionInstallPlans`, `waitForSubscriptionResolution` |
| python-devops | `test/src/test_olm_approvals.py` | tests for both helpers (reuse `ResourceList`, `ResponseSequence`, `makeSubscription` — extend it with `installPlanRef`/`installPlanGeneration` params) |
| ansible-devops | `plugins/module_utils/olm_approvals.py` | generation wait in `waitForSubscriptionApproval`, `waited` flag |
| ansible-devops | `plugins/action/wait_for_subscription_approval.py` | settle call in cluster-wide branch, honest success message |
| ansible-devops | `tests/unit/plugins/module_utils/test_olm_approvals.py` | Manual/Mixed namespace with un-generated plans → waits then notices; all-fresh namespace skips the settle; pre-existing refs trigger the settle; Automatic unchanged; timeout → error; `waited` semantics |
| ansible-devops | `tests/unit/plugins/action/test_wait_for_subscription_approval.py` | message assertions, cluster-wide settle ordering |
| ansible-devops | `docs/olm-manual-approvals.md` | generation/settle semantics |

## Non-goals

- No new configuration surface: the 600s generation budget is a fixed constant — no env var, no task argument, no CLI/Tekton flag. If a need to tune it emerges later it can be added then.
- No changes to the 21 role task files — the fix is entirely inside the gate module both modes call.

## Verification

1. **Unit tests** (WSL, per environment conventions): `wsl bash -lc 'cd /mnt/c/Users/097891866/Documents/GitHub/ibm-mas/python-devops && .venv/bin/pytest test/src/test_olm_approvals.py'` and the ansible-devops equivalents for the module_utils and action plugin tests.
2. **Cluster E2E re-run** (the failing scenario): rebuild the `manualsubs` branch CLI image (which bundles the collection + mas-devops), re-run the dro install with `--olm-approval-mode Manual`. Expected: within seconds of Subscription creation the run displays "Waiting for manual approval of install plan ... in redhat-marketplace" notices for both operators with the `oc patch installplan/...` commands; after approving out-of-band, the `marketplaceconfigs` CRD wait succeeds and the run completes. Also confirm an Automatic-mode install behaves exactly as before (no added delay), and exercise a Manual-mode upgrade (channel change) to confirm the settle poll surfaces the approval notice before the `installPlanGeneration` check.
3. After approval, copy this plan to `cli/.bob/plans/2026-11-23-olm-manual-approval-installplan-generation-race.md` per the plans convention.
