# Pre-Approval Action Preview for mas install/update/upgrade

**Status:** Not started — plan only, no changes made
**Date:** 2026-11-21

## Context

Today the CLI shows a **settings review** (chosen params) before the final `yesOrNo("Proceed with these settings")` confirm, but never tells the user **what will actually be done to their cluster**. The OLM-level actions (CatalogSource roll, Subscription channel changes, Suite CR creation, Db2/Mongo/Kafka upgrades...) happen inside Ansible roles in Tekton tasks, invisible to the user until they watch the pipeline run.

Objective: before the confirm prompt, present a concrete, cluster-state-aware list of planned actions, e.g.

```
*openshift-marketplace*
 - Update CatalogSource/ibm-operator-catalog to v9-261105-amd64 -> v9-261214-amd64

*mas-inst1-core*
 - Update Subscription/ibm-mas on channel 9.0.x -> 9.1.x
 - Create Suite/inst1
```

Decisions made with the user:

- **First vertical slice: `mas update`** (smallest pipeline, detectors already exist). install and upgrade follow.
- **`--dry-run` flag**: shows the full review + action preview, then exits as if the confirm was answered "no" — nothing applied, no pipeline launched. Not a separate preview pathway.
- **Placement**: a new "Actions To Be Performed" section *after* the existing Review Settings; existing sections untouched.

### Related work: OLM manual install plan approvals

The ansible-devops collection (`manualsubs` branch) now supports manual OLM install plan approvals: with `OLM_APPROVAL_MODE=Manual` (and `OLM_APPROVAL_TIMEOUT`, default 7200s), roles pause with human-facing instructions whenever an install plan awaits approval, wait for the out-of-band approval (5-minute status lines showing the deadline), then resume — or fail when the timeout expires. The collection never approves on the user's behalf. Support covers the `apply_subscription` path (~20 roles), the template-based dependency roles, the update/upgrade channel-change flows, and a cluster-wide approval gate in `ocp_verify` (this is where `mas update`'s implicit catalog-digest subscription rolls are waited on).

This plan is complementary: the manual-approvals work gives the user control *during* the run (pausing at each install plan), while the action preview tells them *before* the run what the pipeline is about to do to their cluster. See `.bob/plans/2026-11-21-olm-manual-approvals-cli-tekton.md` for the CLI/Tekton wiring of the approval-mode flags.

## Architecture (recommended)

**Action metadata lives in the Tekton Task sources; the CLI derives the preview at runtime from the shipped bundle.** The Python side contains zero per-task knowledge — only the engine (bundle parsing, guard evaluation, substitution, probing, rendering).

Rationale: the annotations are rendered by `make tekton` into the same `ibm-mas-tekton.yaml` bundle the CLI ships and applies, so gating, ordering and actions are derived from *exactly* the Pipeline document about to be submitted — no cross-artifact drift. A bundle coverage test converts annotation drift into a build failure. (A pure Python catalog was rejected: it would rot the same way `install/summarizer.py` already does.)

Established facts that make this tractable (verified against the sources):

- The three target pipelines use **only** `when:` guards with `operator: in` / `notin` and inputs of the form `$(params.X)` — evaluation is trivial. (Task-result inputs exist only in `mas-fvt-launcher`.)
- `BaseApp.getParam()` returns `""` for unset params while Tekton applies the **pipeline default** (e.g. `mas_monitor_install_order`) — the planner must merge pipeline defaults from the bundle *under* `self.params`.
- Tasks are the reuse unit (`mas-devops-db2` is bound 3 ways in mas-install via taskdef suffixes), so annotations go on **Task templates**, with per-binding differences expressed through param substitution and `if` conditions.

## Annotation schema

The metadata declares only **which key resources a task works with**. It does NOT encode verbs — in the collection the verb is almost universally "apply", and what we actually want to tell the user is the verb *in the context of this cluster*, which only the CLI can determine at runtime (probe the cluster: absent → Create, present → Update; namespace absent → "Create Namespace" and everything in it is a Create). Same pipeline + same params on two different clusters yields two different previews — that's the point.

One annotation per Task, in `tekton/src/tasks/**.yml.j2` `metadata.annotations` (JSON block scalar — toolable, testable):

```yaml
# tekton/src/tasks/dependencies/ibm-catalogs.yml.j2
metadata:
  name: mas-devops-ibm-catalogs
  annotations:
    mas.devops/action-preview: |
      [
        {"namespace": "openshift-marketplace", "kind": "CatalogSource",
         "name": "ibm-operator-catalog", "detail": "$(params.mas_catalog_version)"}
      ]
```

```yaml
# tekton/src/tasks/suite-install.yml.j2
metadata:
  name: mas-devops-suite-install
  annotations:
    mas.devops/action-preview: |
      [
        {"namespace": "mas-$(params.mas_instance_id)-core", "kind": "Subscription",
         "name": "ibm-mas", "detail": "channel $(params.mas_channel)"},
        {"namespace": "mas-$(params.mas_instance_id)-core", "kind": "Suite",
         "name": "$(params.mas_instance_id)"}
      ]
```

Fields (deliberately minimal — "a set of 'I'm going to create/update this resource' statements" is already a huge step forward for the user):

- `namespace` / `kind` / `name`: the resource identity. Literal or containing `$(params.X)` **task-level** tokens (plain `str.replace`, substrings supported: `mas-$(params.mas_instance_id)-core`).
- `detail` (optional): trailing text, param-templated (e.g. the target channel or catalog version). The renderer combines it with the probed current state (e.g. "channel 9.0.x -> 9.1.x").
- `if` (optional, per entry): `{"param": "db2_action", "in": ["install"]}` — same in/notin semantics as when-guards. This is how one Task serves multiple pipelines (install `db2_action: install` vs update `db2_action: upgrade`).

**Curation happens at authoring time**: annotate only the *key* resources — user-visible top-level objects (Namespace, CatalogSource, Subscription, OperatorGroup, CR instances: Suite, `*Application`, Db2uCluster, MongoDbCommunity, Kafka, Grafana, IbmSls, AiCfg, CP4D). Secrets, ConfigMaps, RBAC, Deployments are not annotated. Framework tasks that touch no key resources are annotation-exempt (whitelist for the coverage test): `mas-devops-update-pipeline-status`, `mas-devops-update-configmap`, `mas-devops-wait-for-configmap-v2`, `mas-devops-ocp-verify*`.

**CLI-created infrastructure** (pipelines namespace, RBAC, secrets, Tekton defs, PipelineRun itself — applied by the CLI, not tasks) renders as a short fixed preamble in the renderer (hardcoded list; the CLI code is the source, so no drift risk).

## New modules

```
python/src/mas/cli/plan/
  __init__.py
  model.py       # ResourceRef dataclass (namespace, kind, name, detail, taskName)
                 #  + PlannedAction (ResourceRef + verb computed from cluster
                 #  state: Create | Update) + PlannedActionPreview
  bundle.py      # parse shipped ibm-mas-tekton.yaml (yaml.safe_load_all,
                 #  module-level cache, parse once per process); index Pipeline
                 #  and Task docs by metadata.name. Uses
                 #  BaseApp.tektonDefsWithoutDigestPath (pipelines identical in
                 #  both bundle variants)
  evaluate.py    # merge pipeline spec.params defaults under self.params;
                 #  evaluate when-guards (in/notin over $(params.X)); build
                 #  per-task param bindings from the pipeline task's params
                 #  list; substitute tokens in annotation fields; evaluate `if`
  probe.py       # cluster-state probing to compute the verb:
                 #  1. probe each distinct namespace once (cached) — missing
                 #     namespace => emit "Create Namespace/<ns>" and mark all
                 #     resources in it Create (no per-resource probe needed)
                 #  2. namespace exists => probe the resource (generic
                 #     dynamic-client get) — absent => Create, present => Update
                 #  3. where richer helpers exist, reuse them for the current-
                 #     state detail: mas.devops.mas (getCurrentCatalog,
                 #     getMasChannel, listMasInstances), mas.devops.mas.apps
                 #     (getAppsSubscriptionChannel, getInstalledApps)
                 #  4. probe error => fall back to "Create or Update <resource>"
                 #     rather than guessing
  render.py      # CLI renderer (printH2 namespace headers + printSummary-style
                 #  lines) and buildPreviewMarkdown() for the TUI
  preview.py     # orchestrator: buildPreview(pipelineName, params, dynClient)
                 #  -> PlannedActionPreview
```

Pattern to follow: `update/dependencies.py` — pure dataclasses, no cluster imports outside `probe.py`, so unit tests need no connection.

## CLI integration

All three flows, between the existing review and the confirm:

- **update** — `python/src/mas/cli/update/app.py` after the "Required Migrations" block (~line 397), before the `yesOrNo` at :399-402: `printH2("Actions To Be Performed")` + preview for pipeline `mas-update`.
- **install** — `python/src/mas/cli/install/app.py:3112-3118`, after `displayInstallSummary()`, before the `yesOrNo`: pipeline `mas-install`.
- **upgrade** — `python/src/mas/cli/upgrade/app.py` after the review block (:1174-1180), before `yesOrNo` (:1182-1184): pipeline `mas-upgrade`.

Skip the preview section when `self.noConfirm` (nothing is being confirmed).

### `--dry-run` flag

New flag on install, update, upgrade (`argParser.py` + `CommandArg` entries in `argBuilder.py` so the echoed command carries it). Semantics: show the full review **and** the action preview, then exit cleanly as if the confirm was answered "no" — print a clear "dry run complete, nothing was applied" message.

Implementation notes:

- In update/app.py:404 the launch gate is `if self.noConfirm or continueWithUpdate:` — `--dry-run` must **not** take the `noConfirm` path; it forces `continueWithX = False` and returns before `launchUpdate()`.
- `--dry-run` still connects to the cluster (read-only — state detection needs it) but applies nothing: all mutations (`createTektonFileWithDigest`, namespace/RBAC/secrets/tekton-defs, PipelineRun) happen only after the confirm, so exiting at the confirm is naturally side-effect-free.
- If combined with `--no-confirm`, `--dry-run` wins (show and exit).
- Help text must distinguish it from `--no-confirm`.

### TUI integration

`ReviewScreen._build_markdown()` (python/src/mas/cli/tui/screens/review.py:98) prefers a `review_builder(mas_app)` callable. Extend `buildUpdateReview` (python/src/mas/cli/update/workflow.py) and the upgrade equivalent to append an `## Actions To Be Performed` section from `buildPreviewMarkdown(...)`. Install has no TUI today. `start_dynamic_loaders()` re-invokes the builder when the user goes back, so the preview stays correct after param changes.

## Phased execution

**Phase 0 — bookkeeping**: create the feature branch.

**Phase 1 — engine + `mas update` slice + `--dry-run` (update)**

- Build `mas/cli/plan/` (model, bundle, evaluate, probe, render, preview).
- Annotate the ~12 tasks reachable from mas-update: `ibm-catalogs`, `ocs`, `grafana`, `rhoai-migration`, `db2`, `mongodb`, `kafka`, `cp4d*`, `aiservice-migration`.
- `make tekton` (regenerates both `python/src/mas/cli/templates/` and `image/cli/mascli/templates/` copies — never hand-edit the bundle; see `.bob/rules/tekton-development.md`).
- Integrate preview + `--dry-run` in update/app.py + update/argParser.py + update/argBuilder.py.

**Phase 2 — `mas install`**

- Annotate the ~40 remaining tasks reachable from mas-install (suite, apps, dependencies, cp4d, aiservice). `mas-devops-db2` demonstrates three-way binding + `if` conditions; add the infrastructure preamble.
- Integrate preview + `--dry-run` in install/app.py + argParser + argBuilder.

**Phase 3 — `mas upgrade` + TUI**

- Annotate tasks reachable from mas-upgrade; integrate in upgrade/app.py.
- TUI markdown sections in update/upgrade workflows.

Each phase: branch work on a feature branch (repo convention: same branch name across repos if ansible-devops ever needs touching); commit `[minor]`.

## Testing

1. `tekton/test_action_annotations.py` (sibling of `test_bundles.py`, runs on `tekton/target` after `make tekton`): every taskRef reachable from mas-install/mas-update/mas-upgrade (minus the framework whitelist) carries a parseable `mas.devops/action-preview`; JSON fields valid; every `$(params.X)` in an annotation names a param the Task declares; `if.in` values are strings.
2. `python/tests/unit/plan/`: guard evaluation (in/notin; unset param falls back to bundle default — the `mas_monitor_install_order` case), task param binding and substring substitution, `if` conditions, probe with a fake dynamic client (extend `tests/scenarios/` registry), renderer string snapshots. The bundle is checked in, so `bundle.py` tests load it directly — no cluster, no generation step.
3. `--dry-run` behaviour: unit tests asserting the launch gate is not taken (e.g. `launchUpdate` never called) and exit is clean.
4. TUI: markdown assertions in `tests/unit/update/`; no new widgets → no pilot tests needed (per python/AGENTS.md).

## Verification

1. `make pytest` (python/tests) and `pytest-tekton` (tekton/test_schema.py, test_bundles.py + new test_action_annotations.py) in WSL (`wsl bash -lc`, `.venv`).
2. `make tekton` then confirm the generated bundle carries the annotations (grep `mas.devops/action-preview`).
3. Manual: `mas update --dry-run` against a dev cluster — review + "Actions To Be Performed" render with correct Create/Update verbs reflecting actual cluster state (e.g. CatalogSource present → "Update ... v9-current -> v9-target"), then exits without applying anything; `oc get pipelineruns` confirms nothing was launched. Repeat for install and upgrade in later phases; exercise the TUI (`mas update` bare invocation) review screen.

## Risks / future work

- **Cross-repo truth**: annotations in this repo describe roles in ansible-devops; coverage tests verify presence/validity, not semantics. Mitigation: review convention (task/role PRs touch annotations in the same commit). Mirroring annotations into ansible-devops is possible future work.
- **Bundle parse cost**: 760KB YAML parsed once per process, lazily only when the preview is shown; measure and confirm negligible.
- Future: Delete verbs (for the uninstall pipeline), and extending to uninstall/backup/restore pipelines.
