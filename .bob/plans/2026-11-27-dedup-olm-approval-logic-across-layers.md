# Deduplicate OLM Approval Logic Across the Layers

> After approval, copy this plan to `cli/.bob/plans/2026-11-27-dedup-olm-approval-logic-across-layers.md` (step 0 of implementation).

## Context

The intended architecture (stated in `ansible-devops ibm/mas_devops/tests/unit/plugins/README.md:23`): python-devops implements each capability once; ansible-devops action plugins are thin wrappers (task args + `get_api_client` + package call + `AnsibleError` translation); progress flows through python-devops `onPending` callbacks with the collection owning display.

This broke down in the OLM manual-approvals gate. The 2026-11-27 bug fix (transient `ResolutionFailed` suppression via `transitionInFlight`) had to be made identically in **two files** — python-devops `waitForSubscriptionConvergence` and a near-verbatim copy of the same fail-fast inside the collection's `waitForClusterApproval` — and tested twice. The user wants that "1 fix = 2 files" pattern structurally eliminated.

Where it works (preserve as the model): `plugins/action/wait_for_subscription_approval.py` (103 lines, thin) and `waitForSubscriptionApproval` (delegates to PD via `onPending`).

Where it broke:
- `waitForClusterApproval` (`olm_approvals.py:288-517`, ~230 lines) re-implements PD's fail-fast policy verbatim, the poll-loop skeleton, per-namespace deadline bookkeeping (`firstSeen`/`scope`), and timeout message construction — because PD has no cluster-scoped convergence wait, no late-entrant scope, no per-namespace deadlines, and no mismatch policy, so the logic had nowhere else to live.
- Internal drift in `olm_approvals.py`: mismatch `ValueError` text ×4 (wording already diverging), Mixed notice ×2, heartbeat ×2, approve-command join ×5.
- Pure-presentation helpers with no ansible dependency live in the collection: `approveCommand`, `formatApprovalNotice`, `_formatTimestamp`.
- Env-var resolution (`OLM_APPROVAL_MODE`/`OLM_APPROVAL_TIMEOUT` precedence) exists in the collection **and is mirrored a third time** in the CLI (`cli/python/src/mas/cli/common/olmApprovals.py`).
- AD tests hand-build PD status dicts (`makeStatus`/`makeSubscriptionEntry` replicate the `getNamespaceConvergenceStatus` contract) and re-test PD policy through `waitForClusterApproval`.

**User decisions:** full dedup (cluster wait + fail-fast + notice formatting + env resolution move to PD); CLI repo included; `apply_subscription.py`'s inline approval-mode-change logic is a follow-up, out of scope.

**Branches:** `manualsubs` in all three repos. Changes stay local — no commits/pushes.

## Design

New python-devops API (all in `src/mas/devops/olm.py` unless noted). Everything below is policy/formatting owned by PD once; the collection keeps only task-arg reading, `display` calls, and exception translation.

### 1. Shared fail-fast (the root fix)

`_raiseIfNamespaceUnresolvable(status: dict, namespace: str) -> None` — extracted verbatim from `waitForSubscriptionConvergence`'s fail-fast block (olm.py ~1024-1036): raises `OLMException` on `resolutionError` not suppressed by pendingSubscriptions/`transitionInFlight`, and on `failedInstallPlans`. Called by `waitForSubscriptionConvergence` **and** the new cluster wait. PD error wording wins (names the subscription, `oc get subscription ... -o yaml` remedy). This is the change that makes the next transient-handling bug a one-file fix.

### 2. Presentation of domain data (moved from `olm_approvals.py`)

- `formatInstallPlanApprovalCommand(approval) -> str` (was `approveCommand`) — beside `approveInstallPlan` (olm.py:450-488) so the merge-patch shape is defined once.
- `formatInstallPlanApprovalNotice(approval) -> list[str]` (was `formatApprovalNotice`) — renders the `_describePendingInstallPlan` contract.
- `formatApproveCommands(pending) -> str` — the join pattern currently duplicated ×5, used by mismatch/timeout messages and the collection's timeout re-raise.
- `formatUtcTimestamp(epoch) -> str` (was `_formatTimestamp`) — needed by PD's deadline messages; collection heartbeats reuse it.
- `VALID_APPROVAL_MODES = ("Automatic", "Manual")`, `DEFAULT_APPROVAL_TIMEOUT = 7200` — module constants.

### 3. Env resolution (moved; collapses three copies)

```python
def resolveApprovalMode(explicit: Optional[str] = None, getenv: Callable = os.environ.get) -> Optional[str]
def resolveApprovalTimeout(explicit: Optional[int] = None, getenv: Callable = os.environ.get) -> Optional[int]
```
Precedence: `explicit` > env var > `None`. `explicit` passes through unvalidated (callers validate their own task args/flags — collection today, argparse `choices` in the CLI). Env values are validated with `ValueError` naming the variable; **adopt the CLI's stricter timeout validation** ("OLM_APPROVAL_TIMEOUT must be an integer number of seconds (found 'x')") — the collection's bare `int()` today raises an unnamed ValueError. Injectable `getenv` for tests (CLI's pattern).

### 4. Mismatch policy (one implementation)

`raiseIfApprovalModeMismatch(pending: list, approvalMode: Optional[str], namespaces: Optional[list] = None) -> None` — raises `OLMException` when `pending` is non-empty and `approvalMode != "Manual"` (unset counts as Automatic, as today), message = approve commands + `OLM_APPROVAL_MODE=Manual` remedy, unified wording (single builder replaces the 4 drifting copies). Note the exception-type change: today the collection raises `ValueError`; the action plugin (wait_for_subscription_approval.py:87-92) already translates `OLMException` identically, so ansible-level behavior is preserved.

### 5. Cluster-wide convergence wait (the big move)

```python
def waitForClusterConvergence(dynClient, timeout=None, pollInterval=30, approvalMode=None, onPending=None) -> dict
```
Owns everything `waitForClusterApproval`'s loop does today, mechanics unchanged:
1. Settle: `waitForSubscriptionResolution(dynClient, None)` (moves inside; the collection no longer calls it separately).
2. Discovery: `getPendingInstallPlans(dynClient, None)`; empty → return `{"waited": False, "namespaces": [], "statuses": {}}`.
3. Mismatch: `raiseIfApprovalModeMismatch(pending, approvalMode, all discovered namespaces)`.
4. Loop: per-poll re-discovery (late entrants join scope, `firstSeen` starts their clock, never reset on regression), per-namespace `getNamespaceConvergenceStatus`, per-namespace `_raiseIfNamespaceUnresolvable`, converged namespaces leave scope, `raiseIfApprovalModeMismatch` re-checked for plans that appear mid-wait, per-namespace deadline expiry raises `OLMTimeoutError` listing each namespace's non-converged subscriptions (`installedCSV -> targetCSV (state)`) + approve commands (reuses `_formatConvergenceTimeoutMessage`-style listing).
5. `onPending(clusterStatus, pollCount)` invoked every poll while outstanding; `clusterStatus` = `{"pendingApprovals": [...cluster-wide], "statuses": {ns: convergence status}, "outstanding": [ns...]}` — enough for the collection to diff new plans for notices, print heartbeats, and detect Mixed namespaces. (Same exception-propagation-through-callback contract as today.)
6. Returns `{"waited", "namespaces" (sorted, ever in scope), "statuses"}` — the exact contract `waitForClusterApproval` returns today, so the action plugin's result handling is unchanged.

## Files to modify

| Repo | File | Change |
|---|---|---|
| python-devops | `src/mas/devops/olm.py` | Additions 1-5 above; `waitForSubscriptionConvergence` fail-fast becomes a call to `_raiseIfNamespaceUnresolvable` (behavior identical) |
| python-devops | `src/mas/devops/__init__.py` | Version `100.0.0` → `100.1.0` |
| python-devops | `test/src/test_olm_approvals.py` | New tests (below); existing single-namespace tests unchanged |
| ansible-devops | `ibm/mas_devops/plugins/module_utils/olm_approvals.py` | Shrink to the thin layer (below); imports move to PD |
| ansible-devops | `ibm/mas_devops/plugins/action/wait_for_subscription_approval.py` | Unchanged except: verify `ValueError` branch still needed (task-arg/env validation still raises it; mismatch now arrives as `OLMException`) |
| ansible-devops | `requirements.txt` | `mas-devops >= 5.2.0` → `mas-devops >= 100.1.0` (collection now imports new PD symbols) |
| ansible-devops | `tests/unit/plugins/module_utils/test_olm_approvals.py`, `tests/unit/plugins/action/test_wait_for_subscription_approval.py` | Test migration (below) |
| ansible-devops | `docs/olm-manual-approvals.md` | Note the layering: gate logic lives in `mas.devops.olm`; the collection displays and translates. Update resolution-helper home. |
| cli | `python/src/mas/cli/common/olmApprovals.py` | `resolveOlmApprovalMode`/`resolveOlmApprovalTimeout` become delegates to PD (`resolveApprovalMode(explicit=flagValue, getenv=getenv)`); delete `VALID_OLM_APPROVAL_MODES`/`DEFAULT_OLM_APPROVAL_TIMEOUT` if unused after (import from PD where still referenced); update the "mirrors the collection" docstring to point at PD |
| cli | `pyproject.toml` | `mas-devops >= 9.0.0` → `>= 100.1.0` (CLI now imports the new PD symbols) |
| cli | `python/tests/unit/common/test_olm_approvals.py` | Should pass unchanged (public behavior identical); adjust only if the delegate changes injectable-getenv plumbing |

### The collection layer after the refactor (`olm_approvals.py`)

- `resolveApprovalMode(taskArg)` / `resolveApprovalTimeout(taskArg)`: keep as pass-throughs (task-arg validation with the existing `install_plan_approval must be one of:` message stays; env part delegates to PD). Kept because `plugins/action/apply_subscription.py` imports them.
- `waitForSubscriptionApproval`: unchanged shape; internals now call `raiseIfApprovalModeMismatch` (entry + inside `onPending` for late plans), `formatInstallPlanApprovalNotice`, `formatApproveCommands` (timeout re-raise). Heartbeat/STATUS_INTERVAL display stays here.
- `waitForClusterApproval(dynClient, display, timeout, pollInterval, approvalMode)`: becomes ~40 lines — an `onPending` closure doing display (first-call full-scope report, new-plan notices via its own `seenPlanNames` diff, heartbeat every STATUS_INTERVAL, first-seen Mixed notice) around one `waitForClusterConvergence` call. Delete the local loop, `firstSeen`/`scope`/`enterScope`, fail-fast copies, mismatch texts, `_formatTimestamp`, `approveCommand`, `formatApprovalNotice`, `DEFAULT_APPROVAL_TIMEOUT`.

## Test migration

**python-devops** (`test/src/test_olm_approvals.py`) gains:
- `TestResolveApprovalMode` / `TestResolveApprovalTimeout` — explicit precedence, env validation `ValueError`s, injectable `getenv`, `None` default (ported from the collection/CLI tests).
- `TestApprovalNotices` — command format (merge-patch string), notice lines, no-current-CSV case (ported from AD `TestFormatApprovalNotice`).
- `TestWaitForClusterConvergence` — no-op when nothing pending; initial + mid-wait mismatch raises; late entrant joins scope; per-namespace deadline expiry (message lists subscriptions + commands); fail-fast resolution error naming the namespace; Failed plan fail-fast; transient suppression after approval (port of the AD test that mirrored the bug fix — via the cluster entry point); Mixed not fatal; any-order convergence; return contract. Mocks: reuse `ResourceList`/`ResponseSequence`/`makeSubscription`/`makeInstallPlan`/`makeGetHandler`/`buildDynClient`; cluster-wide `getPendingInstallPlans` hits the kwargs-free `allResponse` branch of `makeGetHandler` with per-namespace Subscription listings — items already carry `metadata.namespace`.

**ansible-devops**:
- DELETE the PD-policy tests under `TestWaitForClusterApproval` (`test_resolution_failed_fails_fast_naming_the_namespace`, both transient tests, `test_failed_install_plan_fails_fast_naming_the_plan`) and `TestFormatApprovalNotice` — policy now tested once in PD.
- REWRITE `TestWaitForClusterApproval` with `waitForClusterConvergence` mocked: up-front full-scope report on first `onPending`, new-plan notice dedupe, heartbeat cadence, Mixed notice, no-op honest success (`waited=False`).
- KEEP: `TestResolveApprovalMode`/`TestResolveApprovalTimeout` (now pass-through + task-arg validation), `waitForSubscriptionApproval` display tests, timeout re-raise wrapper test.
- `test_wait_for_subscription_approval.py`: update the mismatch test if it asserts `ValueError` from the cluster path (now `OLMException`); translation-to-`AnsibleError` tests unchanged.

**cli**: `python/tests/unit/common/test_olm_approvals.py` passes unchanged (delegates preserve signatures and behavior).

## Verification (WSL, per environment conventions)

1. `wsl bash -lc 'cd /mnt/c/Users/097891866/Documents/GitHub/ibm-mas/python-devops && .venv/bin/pytest test/src/test_olm_approvals.py'`
2. ansible-devops `.venv` must have local PD installed editable (`.venv/bin/pip install -e /mnt/c/.../python-devops` — per AGENT_INSTRUCTIONS.md; new symbols then resolve automatically): `.venv/bin/pytest ibm/mas_devops/tests/unit/plugins/module_utils/test_olm_approvals.py ibm/mas_devops/tests/unit/plugins/action/test_wait_for_subscription_approval.py`
3. cli: `.venv/bin/pytest python/tests/unit` (or the common subset plus `-m "not pilot"` fast loop).
4. `black --check` on all changed files (both devops repos' `.venv/bin/black`).
5. Import sanity for the collection: `.venv/bin/python -c "from ansible_collections.ibm.mas_devops.plugins.module_utils import olm_approvals"` (mirrors the CI test job's import path in `.github/workflows/test.yml`).
6. Behavior parity is unit-tested (same notices, same fail-fast semantics, same deadline behavior); a cluster E2E Manual-mode upgrade re-run is optional confirmation, not required for this refactor.

## Non-goals / follow-ups

- `apply_subscription.py`'s inline approval-mode-change logic (asymmetric explicit/resolved-mode rules) — same disease, different policy; extract to PD (e.g. `checkApprovalModeChange`) as a follow-up.
- No new configuration surface; no message contract changes beyond unifying the 4 drifted mismatch wordings (PD wording wins).
- No logger-to-display bridge — the `onPending` callback pattern stays the progress mechanism.
