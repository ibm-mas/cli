# OLM Approvals — Deterministic Target-State (Subscription Convergence) Wait

> Step 0 (before any code): add the no-commit/no-push rule to the user's global `~/.claude/CLAUDE.md`. The agent never commits or pushes; the user handles everything that exposes work publicly.
>
> On completion, copy this plan to `cli/.bob/plans/2026-11-24-olm-subscription-convergence-wait.md` per the plans convention (a local file write only).

## Context

The manual-approvals work on the `manualsubs` branches (python-devops, ansible-devops, cli — all unmerged) currently closes the install-plan generation race with **timing-window waits**: `waitForSubscriptionInstallPlans` (fresh subscriptions) and `waitForSubscriptionResolution` (a quiet-poll settle over subscription status, ~1 min, for patched subscriptions and the cluster-wide gate). The upgrade roles additionally hedge with blind 5-minute pauses and generation-bump state checks after the gate.

This change replaces the timing windows with a **deterministic target-state wait**:

1. Read a Subscription's `status.installedCSV` (current state).
2. Read the target CSV for that subscription's channel from the PackageManifest (`status.channels[<sub.spec.channel>].currentCSV`).
3. Wait until **every subscription in the namespace** reports `installedCSV == target` — InstallPlans are namespace-scoped, so just because the subscription we're working with hasn't bumped doesn't mean another in the namespace didn't.
   - **Automatic**: wait for the subscription(s) to reach the expected version.
   - **Manual**: exactly the same wait, plus messaging that we are waiting for a manual approval (notices with the `oc patch` command).

This unifies Manual and Automatic into one convergence wait and eliminates the generation/settle pre-gate, the post-approval settle block, and the upgrade roles' blind pauses.

**Decisions made with the user:**
- **Upgrade-role simplification is in scope** — the post-gate state checks and blind pauses guard against a condition that can no longer occur once the gate is convergence-based.
- **`OLM_APPROVAL_TIMEOUT` is the single timeout for both modes** — it is a timeout for *the approval*, regardless of how the approval is issued (human under Manual, OLM under Automatic). Same default (7200s), same resolution (task arg > env > default), fatal on expiry in both modes. Documentation updated accordingly. No new constant.
- The **cluster-wide gate keeps its settle** — after a catalog digest update the PackageManifest itself lags, and there is no deterministic catalog→manifest signal. This is the one timing window that genuinely cannot be removed.
- CLI is fire-and-forget: **no functional CLI changes**; only test fixes and doc-text updates.

**Branches:** `manualsubs` in all three repos.

**Workflow constraint (standing, from the user):** never create commits or push — the user handles all commits and pushes personally. All work stays local in the working tree; my job ends once the changes are local. (This rule is also being added to the user's global `~/.claude/CLAUDE.md` as the first implementation step.)

## Design

### 1. python-devops — `src/mas/devops/olm.py`

**New:**

- `getChannelHeadCSV(dynClient, packageName, channel, catalogSourceNamespace="openshift-marketplace") -> Optional[str]` — reads the PackageManifest `status.channels[]` entry with `name == channel`, returns its `currentCSV`; `None` when manifest or channel entry is absent. (First Python reader of channel data; mirrors the Jinja idiom in ansible-devops `common_tasks/get_version_from_channel.yml`. Built on existing `getPackageManifest`, olm.py:48.)
- `_subscriptionChannelHead(dynClient, subscription, manifestCache) -> tuple[Optional[str], Optional[str]]` (internal) — resolves one subscription's target: package = `spec.name`, channel = `spec.channel`, catalog namespace = `spec.sourceNamespace` or `openshift-marketplace`. `manifestCache` is a per-poll dict keyed `(package, sourceNamespace)` so each poll costs at most one manifest GET per package. Returns `(targetCSV, skipReason)`.
- `getNamespaceConvergenceStatus(dynClient, namespace) -> dict` — non-blocking snapshot: one subscription list + cached manifest lookups, composed with the existing `getNamespaceApprovalStatus` (reuse its InstallPlan listing / `_describePendingInstallPlan`; the approval-info dict shape is test-pinned and unchanged). Returns:
  ```python
  {
    "namespace", "approvalMode", "pendingApprovals", "blocking",   # unchanged semantics
    "subscriptions": [ {"name", "package", "channel", "state", "installedCSV",
                        "targetCSV", "installPlanRef",
                        "converged": bool|None,      # None when skipped
                        "skipped": bool, "skipReason": str|None,
                        "resolutionError": str|None} ],   # ResolutionFailed condition message
    "failedInstallPlans": [names],   # phase Failed plans referenced by non-converged subs
    "converged": bool,               # every non-skipped sub has installedCSV == targetCSV
  }
  ```
  Subscriptions with no PackageManifest / no channel entry: **warn + skip** (never block — nothing can be approved for them; a removed catalog must not wedge installs).
- `waitForSubscriptionConvergence(dynClient, namespace, timeout=None, pollInterval=30, onPending=None) -> dict` — the mode-agnostic poll loop:
  1. Snapshot via `getNamespaceConvergenceStatus`.
  2. **Fail fast:** any `resolutionError` (Subscription `status.conditions` type `ResolutionFailed`, status True, manifest present) → raise `OLMException` naming the subscription, the condition message, and `oc get subscription -n <ns>` / catalog-health pointers. Any `failedInstallPlans` → raise `OLMException` naming the plan and owning sub. (Note ordering: missing manifest → skip; manifest present + ResolutionFailed → raise.)
  3. `converged` → return status.
  4. Invoke `onPending(status, pollCount)`; returning `False` aborts and returns current status (same contract as `waitForNamespaceApprovals`).
  5. Timeout → `OLMTimeoutError` listing each non-converged sub as `name: installedCSV -> targetCSV (state)`; skipped subs listed as warnings.

**Removed** (subsumed — a fresh subscription is simply not-yet-converged; its plan appears and the notice fires on a later poll):
- `waitForSubscriptionInstallPlans` (olm.py:743), `getSubscriptionInstallPlanRefs` (olm.py:717), `INSTALL_PLAN_GENERATION_TIMEOUT` constant.

**Kept unchanged:** `waitForSubscriptionResolution` + `SUBSCRIPTION_RESOLUTION_*` (still used by the cluster-wide gate only), `waitForSubscriptionStable`, `waitForInstallPlanComplete`, `waitForNamespaceApprovals`, and `applySubscription` in full (its internal waits have intentional `startingCSV` pinning semantics under Manual auto-approve-initial-install — non-goal).

### 2. ansible-devops — `plugins/module_utils/olm_approvals.py`

`waitForSubscriptionApproval(dynClient, display, namespace, packageName=None, timeout=None, pollInterval=30, approvalMode=None)` — **`targetCSV` parameter dropped** (its only use, the post-approval settle, is deleted). New flow:

1. Initial `getNamespaceApprovalStatus` snapshot; keep the mode-mismatch `ValueError` verbatim (blocking + `approvalMode != "Manual"` → approve commands + `OLM_APPROVAL_MODE=Manual` remedy); keep the Mixed-mode notice.
2. Run `waitForSubscriptionConvergence` with **`timeout` = the resolved approval timeout in both modes** (`resolveApprovalTimeout`: task arg > `OLM_APPROVAL_TIMEOUT` > 7200) and an `onPending` callback that:
   - **Diffs pending plans** against previously-seen install-plan names (closure state) and prints `formatApprovalNotice` lines for each *new* plan — an improvement over today, where a second plan appearing mid-wait never got a notice. Manual mode only.
   - **Late mismatch:** in a non-Manual context, any discovered pending approval raises the same `ValueError` as step 1 (closes the creation race the old pre-gate handled).
   - Emits the periodic status line every `STATUS_INTERVAL` (300s): Manual keeps "Waiting for install plan approval since X, approval deadline Y"; Automatic gets an equivalent line ("Waiting for N subscription(s) in <ns> to reach their channel head ... deadline Y") — the approval deadline applies in both modes per the user's decision.
3. Catch `OLMTimeoutError`: Manual → re-raise with the approve commands repeated (existing pattern); Automatic → re-raise with the non-converged subscription list (message already names `installedCSV -> targetCSV` per sub).
4. Return the final convergence status plus `waited` (True only when pending approvals were observed at any point — the action plugin's honest success message depends on it). `packageName` is retained to highlight that subscription's final state in the returned status and to avoid churning the role call sites; it does not narrow the wait.

**Deleted:** the race pre-gate (L159-168), the post-approval `waitForInstallPlanComplete`/`waitForSubscriptionStable` block (L226-231 — convergence already implies the plan completed and the CSV installed: OLM only promotes `installedCSV` after the CSV reaches Succeeded), and the now-unused imports.

### 3. ansible-devops — `plugins/action/wait_for_subscription_approval.py`

Structurally unchanged (preserves the test-pinned `["settle", "discover"]` cluster-wide ordering):
- Namespace mode: single `waitForSubscriptionApproval` call.
- Cluster-wide mode: `waitForSubscriptionResolution(None)` settle (stale-manifest protection after catalog digest updates) → `getPendingInstallPlans(None)` → per-namespace `waitForSubscriptionApproval` without `packageName`. **Discovery stays pending-plan-based** — do NOT discover "namespaces with non-converged subscriptions": `openshift-operators` and friends contain unrelated operators, and one broken unrelated subscription must not wedge `mas update`/`ocp_verify`.
- Update docstring/usage; optionally extend the waited message to "... and all subscriptions are at their channel head".

### 4. ansible-devops — upgrade-role simplification (user-approved scope)

When the convergence gate returns, the subscription is definitionally at its channel head, so the post-gate hedging is dead weight. CR-level waits (Suite/App/AIServiceApp reconciled versions, OperatorCondition, deployment readiness) **stay** — convergence does not cover workload reconciliation.

| Role | Remove | Keep |
|---|---|---|
| `suite_upgrade/tasks/upgrade.yml` | generation-bump/state-check task + debug (L26-42), 5-min pause (L47-49) | OperatorCondition lookup w/ 10×60s retries; Suite CR reconciled-version check |
| `suite_app_upgrade/tasks/upgrade.yml` | 5-min pause (L24-26) | OperatorCondition 10×120s retries; App/Workspace CR checks |
| `aiservice_upgrade/tasks/upgrade_aiservice.yml` | state-check task + debug (L26-42), 5-min pause (L47-49) | "Read subscription" task L83-90 (its `installedCSV` feeds the version comparison at L102) |
| `kafka/.../run-kafka-subscription-upgrade.yml` | 30s pause (L20-22), the whole `currentCSV == installedCSV` poll (L24-39 — exactly the wait the gate now performs), trailing 30s pause (L64-66) | deployment-ready wait |
| `ocs/tasks/upgrade/main.yml` | 1-min pauses after source patches (L76-78, L91-93), 2-min pause (L138-140) | 5-min pause at L113-115 only if the following StorageCluster tasks lack their own retries/until — verify first |

Check `tests/unit/roles/<role>/` for coverage of the removed tasks (e.g. `aiservice_upgrade` tests set `currentCSV` in their subscription mocks) and update accordingly.

### 5. cli — test fixes + doc text only (no functional changes)

- `python/tests/unit/install/test_install_olm_approvals.py`: the `TestInstallOlmApprovalPrompt` tests mock a nonexistent `promptForSelect` — the shipped `configOLMApprovals` (install/app.py:499-505) uses `promptForString` + `WordCompleter` + `ListOptionValidator`. Replace `app.promptForSelect = MagicMock(...)` with `app.promptForString = MagicMock(...)` (fake signature `(message, param=None, default="", **kwargs)`; assert on `call_args.kwargs["default"]`). Delete `test_cancelled_dialog_aborts_the_install` (no cancel-returns-None path on `promptForString`).
- `python/tests/integration/utils/install_test_helper.py`: remove the `@mock.patch("mas.cli.displayMixins.radiolist_dialog")` decorator (attribute doesn't exist → `AttributeError` at decorator time), its parameter/side-effect, and the dead `answerSelectDialog` helper.
- `python/tests/integration/utils/prompt_tracker.py`: add `r".*Select the install plan approval mode.*": lambda message: "Automatic"` to `OPTIONAL_PROMPT_DEFAULTS`; fix the stale select-list comment (L18-19).
- Timeout-semantics text: update the install wizard description (install/app.py:508-512), summarizer, and `docs/guides/{install,update,upgrade}.md` — `OLM_APPROVAL_TIMEOUT` budgets each approval wait **in both modes** (human approval under Manual, OLM's own approval + rollout under Automatic).

### 6. Docs

- ansible-devops `docs/olm-manual-approvals.md`: replace the "Install plan generation" section with "Subscription convergence" — target = PackageManifest channel head; success = every non-skipped subscription's `installedCSV == target`; skipped manifests warn+skip; fail-fast on ResolutionFailed/Failed plans; `OLM_APPROVAL_TIMEOUT` applies to both modes (renamed framing: "a timeout for the approval, however it is issued"); cluster-wide settle retained and why; the upgrade-role simplifications.
- python-devops `docs/api/olm.md`: add `getChannelHeadCSV`, `getNamespaceConvergenceStatus`, `waitForSubscriptionConvergence`.

## Files to modify

| Repo | File | Change |
|---|---|---|
| python-devops | `src/mas/devops/olm.py` | new `getChannelHeadCSV`, `_subscriptionChannelHead`, `getNamespaceConvergenceStatus`, `waitForSubscriptionConvergence`; delete `waitForSubscriptionInstallPlans`, `getSubscriptionInstallPlanRefs`, `INSTALL_PLAN_GENERATION_TIMEOUT` |
| python-devops | `test/src/test_olm_approvals.py` | extend `buildDynClient` (PackageManifest mapping), new `makePackageManifest`/`makePackageManifestHandler` fakes, extend `makeSubscription` (`channel`, `sourceNamespace`, `conditions` — explicit, Mock auto-attrs are truthy); new `TestGetChannelHeadCSV`, `TestGetNamespaceConvergenceStatus`, `TestWaitForSubscriptionConvergence` (immediate success, `ResponseSequence` transitions, timeout message, ResolutionFailed fail-fast, Failed-plan fail-fast, skipped-don't-block, `onPending` contract); delete `TestGetSubscriptionInstallPlanRefs`, `TestWaitForSubscriptionInstallPlans` |
| ansible-devops | `plugins/module_utils/olm_approvals.py` | gate restructure per §2 |
| ansible-devops | `plugins/action/wait_for_subscription_approval.py` | docstring/message updates only |
| ansible-devops | `roles/{suite_upgrade,suite_app_upgrade,aiservice_upgrade,kafka,ocs}/tasks/...` | pause/state-check removals per §4 |
| ansible-devops | `ibm/mas_devops/tests/unit/plugins/module_utils/test_olm_approvals.py` | delete `TestWaitForSubscriptionApprovalGenerationRace`; rewrite `TestWaitForSubscriptionApproval` around patched `waitForSubscriptionConvergence` (both modes pass the resolved timeout; new-plan notice diff; late mismatch; timeout re-raise per mode; `waited` semantics) |
| ansible-devops | `tests/unit/roles/...` | update coverage of removed role tasks |
| ansible-devops | `docs/olm-manual-approvals.md` | convergence semantics |
| cli | `python/tests/unit/install/test_install_olm_approvals.py`, `python/tests/integration/utils/{install_test_helper,prompt_tracker}.py` | prompt-API test fixes |
| cli | `python/src/mas/cli/install/app.py` (wizard text), `docs/guides/{install,update,upgrade}.md` | timeout-semantics wording |

## Verification

1. **Unit tests** (WSL, explicit `/mnt/c` paths):
   - `wsl bash -lc 'cd /mnt/c/Users/097891866/Documents/GitHub/ibm-mas/python-devops && .venv/bin/pytest test/src/test_olm_approvals.py -v'`
   - `wsl bash -lc 'cd /mnt/c/Users/097891866/Documents/GitHub/ibm-mas/ansible-devops/ibm/mas_devops/tests && python -m pytest unit/ -v'` (note: 2 pre-existing `aiservice_upgrade` failures on subprocess timeouts are baseline, not regressions)
   - cli: `wsl bash -lc 'cd /mnt/c/Users/097891866/Documents/GitHub/ibm-mas/cli && .venv/bin/pytest python/tests'`
2. **Cluster E2E** (rebuild the `manualsubs` CLI image bundling collection + mas-devops):
   - Fresh install, Manual (the original dro failure scenario): notices for both operators within seconds of Subscription creation, `oc patch` approval out-of-band, gate returns at head, `marketplaceconfigs` CRD wait succeeds.
   - Fresh install, Automatic: gate performs the real convergence wait (seconds) — no regression vs the old no-op.
   - Channel upgrade, Manual (suite_upgrade): notices fire (including a *second* plan on multi-step upgrade paths — validates the notice-diff improvement), gate returns at head, removed state-check/pause tasks hide nothing (OperatorCondition retries suffice).
   - `mas update` / catalog digest update: cluster-wide gate settles → discovers → waits per namespace.
   - Broken subscription (bad channel): fails fast with ResolutionFailed naming the sub, in both modes.
   - Shared namespace (e.g. openshift-storage): convergence covers sibling subscriptions.
   - Removed catalog / missing manifest: warn + skip, gate passes.
   - **Checkpoint:** confirm on the real cluster that `installedCSV` only promotes after the CSV reaches Succeeded — justifies deleting the post-approval settle block. If it does not hold, reinstate a single `waitForInstallPlanComplete` for the packageName's last approved plan.
3. Copy this plan to `cli/.bob/plans/2026-11-24-olm-subscription-convergence-wait.md`.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Stale PackageManifest in cluster-wide mode → vacuous pass after digest update | Settle (`waitForSubscriptionResolution(None)`) retained before discovery. Residual race (manifest updates after settle) exists today too; documented, accepted. |
| Unrelated stuck sub in a shared namespace blocks the gate | Bounded by `OLM_APPROVAL_TIMEOUT`; fail-fast on ResolutionFailed/Failed plans; timeout message names each non-converged sub with `installedCSV -> targetCSV`. Today's gate already blocks on any pending plan in the namespace — same blast radius for the pending case. |
| Subs pinned via `startingCSV` under Manual never reach head | Not a regression: the un-approved upgrade plan already blocks today's gate. Documented. |
| 7200s Automatic ceiling turns very slow installs into failures | User's explicit decision (one knob, "timeout for the approval however issued"); fail-fast conditions catch genuinely-broken subs early, so the ceiling only bites truly stuck rollouts. |
| Manifest reads add API churn | Per-poll cache keyed `(package, sourceNamespace)`; negligible at 30s polls. |
| Upgrade-role pause removal hides a real settle need | OperatorCondition/StorageCluster lookups retry 10-20 min; E2E scenario 3 validates. |

## Non-goals

- `applySubscription` internal waits (startingCSV pinning semantics are intentional).
- Any new configurable constant — `OLM_APPROVAL_TIMEOUT` is the only timeout; the cluster-wide settle keeps its existing fixed 600s constants.
- CLI-side waiting/log-streaming (fire-and-forget by design).
