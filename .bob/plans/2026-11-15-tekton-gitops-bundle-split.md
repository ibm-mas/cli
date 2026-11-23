# Plan: Split GitOps Tekton resources into `ibm-mas-tekton-gitops.yaml`

**Date:** 2026-11-15
**Status:** Not started — plan only, no changes made
**Goal:** Produce a third Tekton bundle from the build so that main, FVT, and GitOps
Tekton resources are isolated from each other:

- `ibm-mas-tekton.yaml` — main (suite install/update/upgrade/backup/restore, dependencies, OCP, framework, AI Service)
- `ibm-mas-tekton-fvt.yaml` — FVT/IVT
- `ibm-mas-tekton-gitops.yaml` — **new** — all `gitops-` prefixed tasks and pipelines

---

## 1. Current state (how the build works today)

### Generation
- [tekton/generate-tekton-tasks.yml](../../tekton/generate-tekton-tasks.yml) renders
  `tekton/src/tasks/**/*.yml.j2` → `tekton/target/tasks/*.yaml`. Section 9 renders the
  ~78 gitops tasks from `tekton/src/tasks/gitops/`.
- [tekton/generate-tekton-pipelines.yml](../../tekton/generate-tekton-pipelines.yml) renders
  `tekton/src/pipelines/*.j2` → `tekton/target/pipelines/*.yaml`, plus the gitops
  pipelines from `tekton/src/pipelines/gitops/` (sections 3–5). Note it also generates
  `-after-provision` / `-after-deprovision` variants of some gitops pipelines.
- Pipeline taskdefs (`tekton/src/pipelines/taskdefs/**`) are **inlined** into the
  generated pipeline YAML at Jinja render time (`lookup('template', ...)`), so there is
  no runtime file dependency on taskdefs.

### Bundling
[build/bin/build-tekton.sh](../../build/bin/build-tekton.sh) concatenates the generated
files into two bundles:

- `TARGET_FILE` = `ibm-mas-tekton.yaml` — also copied into
  `image/cli/mascli/templates/` and `python/src/mas/cli/templates/` (shipped inside the
  CLI image and PyPI package)
- `TARGET_FILE_FVT` = `ibm-mas-tekton-fvt.yaml` — **not** shipped in the CLI; only
  uploaded as a GitHub artifact and released to Artifactory

The split is a `case` statement on the file basename (build-tekton.sh:86-108):

```bash
*fvt-*|*ivt-*|aiservice-fvt*|aiservice-launchfvt*)   → FVT bundle
*gitops-...                                          → (currently falls through to) main bundle
```

### Consumption
- CI: [.github/workflows/build-cli.yml](../../.github/workflows/build-cli.yml) runs
  `build-tekton.sh`, uploads both bundles as workflow artifacts, and releases both to
  Artifactory (lines 47-72). The `build-python` and `image-*` jobs download only
  `ibm-mas-tekton.yaml` into their template directories.
- CLI runtime: `python/src/mas/cli/cli.py:140` points `tektonDefsPath` at the shipped
  `templates/ibm-mas-tekton.yaml`; every CLI flow that touches Tekton
  (install, update, upgrade, uninstall, backup, restore, aiservice install/upgrade)
  calls `updateTektonDefinitions(...)` with it. **No CLI code launches any `gitops-*`
  pipeline** — the gitops consumers are external (MAS GitOps automation downloading
  from Artifactory / applying the bundle to the pipelines namespace).
- Because `updateTektonDefinitions` applies the *whole* main bundle today, every
  cluster touched by `mas install`/`mas update` etc. currently receives all gitops
  tasks and pipelines.

---

## 2. Design decisions

### D1 — Match by `gitops-` prefix, checked **before** the FVT patterns
The user-facing rule is "all `gitops-` prefixed tasks and pipelines". This is a prefix
match on the basename (`gitops-*`), not `*gitops-*`, because every gitops source file
starts with the prefix.

**Ordering matters:** `gitops-mas-fvt-preparer`, `gitops-aiservice-fvt-preparer` (tasks)
and `gitops-mas-fvt-preparer-pipeline`, `gitops-aiservice-fvt-preparer-pipeline`
(pipelines) contain `fvt-` and therefore land in the **FVT bundle today**. With the new
rule they move to the **gitops bundle**. The `gitops-*` case must be listed before the
`*fvt-*` case so the prefix wins. This is an intentional, visible behavior change —
see §5.

### D2 — `deprovision-aiservice-deps` goes into the gitops bundle
`tekton/src/pipelines/gitops/deprovision-aiservice-deps.yml.j2` (and its generated
`-after-deprovision` variant) is the one gitops-source pipeline **without** the
`gitops-` prefix. It references `gitops-deprovision-efs` and `gitops-deprovision-mongo`
tasks, so leaving it in the main bundle would create a dangling taskRef once the gitops
tasks leave. Handle it with an explicit basename special-case in the `case` statement
(renaming the pipeline itself would change the Pipeline resource name in clusters and
break external automation that launches it by name — do not rename in this change).

### D3 — Do not ship the gitops bundle inside the CLI
Mirror the FVT treatment: `ibm-mas-tekton-gitops.yaml` is uploaded as a workflow
artifact and released to Artifactory, but **not** copied into
`image/cli/mascli/templates/` or `python/src/mas/cli/templates/`. Nothing in the CLI
invokes gitops pipelines, so the CLI package doesn't need it. Consequence: external
gitops automation must apply the gitops bundle itself instead of relying on
`mas install` to have applied it — see §6 rollout.

### D4 — Generated `-after-provision` / `-after-deprovision` variants follow their parent
All of these are `gitops-*-after-*` and are caught by the same `gitops-*` prefix (plus
the `deprovision-aiservice-deps-after-deprovision` special case from D2). No extra
handling needed.

---

## 3. Changes

### 3.1 [build/bin/build-tekton.sh](../../build/bin/build-tekton.sh) (primary change)

1. **Declare the new target** in both the CI branch (lines 10-18) and the `DEV_MODE`
   branch (lines 20-44):
   ```bash
   TARGET_FILE_GITOPS=$GITHUB_WORKSPACE/tekton/target/ibm-mas-tekton-gitops.yaml
   # resp.
   TARGET_FILE_GITOPS=$DIR/../../tekton/target/ibm-mas-tekton-gitops.yaml
   ```

2. **Initialize it** next to the other two (build-tekton.sh:69-70):
   ```bash
   echo "" > $TARGET_FILE_GITOPS
   ```

3. **Add the gitops case to the task loop** (build-tekton.sh:86-96). New order —
   gitops first, then FVT, then default:
   ```bash
   for FILE in $TASK_FILES; do
     FILE_NAME=$(basename $FILE)
     case "$FILE_NAME" in
       gitops-*)
         addToFile $FILE $TARGET_FILE_GITOPS
         ;;
       *fvt-*|*ivt-*|aiservice-fvt*|aiservice-launchfvt*)
         addToFile $FILE $TARGET_FILE_FVT
         ;;
       *)
         addToFile $FILE $TARGET_FILE
         ;;
     esac
   done
   ```

4. **Add the gitops case to the pipeline loop** (build-tekton.sh:98-108), including the
   D2 special case:
   ```bash
   for FILE in $PIPELINE_FILES; do
     FILE_NAME=$(basename $FILE)
     case "$FILE_NAME" in
       gitops-*|deprovision-aiservice-deps*)
         addToFile $FILE $TARGET_FILE_GITOPS
         ;;
       *fvt-*|*ivt-*|aiservice-fvt*)
         addToFile $FILE $TARGET_FILE_FVT
         ;;
       *)
         addToFile $FILE $TARGET_FILE
         ;;
     esac
   done
   ```
   (`deprovision-aiservice-deps*` also catches the generated
   `deprovision-aiservice-deps-after-deprovision.yaml`.)

5. **Leave the copies to CLI templates unchanged** (build-tekton.sh:110-111) — only the
   main bundle is copied, per D3.

### 3.2 [.github/workflows/build-cli.yml](../../.github/workflows/build-cli.yml)

In the `build-tekton` job, after the existing FVT steps (lines 57-62):

1. Add an artifact upload:
   ```yaml
   - name: Upload the Tekton definitions (GitOps)
     uses: actions/upload-artifact@v4
     with:
       name: ibm-mas-tekton-gitops.yaml
       path: ${{ github.workspace }}/tekton/target/ibm-mas-tekton-gitops.yaml
       retention-days: 30
   ```

2. Add an Artifactory release next to the existing two (line 72):
   ```bash
   $GITHUB_WORKSPACE/build/bin/artifactory-release.sh $GITHUB_WORKSPACE/tekton/target/ibm-mas-tekton-gitops.yaml
   ```

No changes to the `build-python` / `image-*` jobs — they only consume
`ibm-mas-tekton.yaml`, which remains an artifact and remains copied to both template
directories by the build script.

### 3.3 No changes needed elsewhere

- [.gitignore](../../.gitignore) — `tekton/target` is already ignored; the new file
  lives there and is not copied into any templates directory (D3).
- [Makefile](../../Makefile) — `64-clean-tekton` and `tekton/target` targets work
  unchanged; `pytest-tekton` validates `tekton/target/**` per-file, not the bundles.
- [tekton/test_schema.py](../../tekton/test_schema.py) — schema-validates the
  individual generated files in `target/tasks` and `target/pipelines`, which are
  unchanged by the split. Optional hardening in §4.

---

## 4. Verification

1. **Regenerate locally** (WSL): `make tekton` (equivalently
   `DEV_MODE=true build/bin/build-tekton.sh` with ansible-playbook available).
2. **Bundle-partition assertions** — add a small validation (one-off script, or extend
   `tekton/test_schema.py` with a new test module so it runs in `make tekton`):
   - Every file in `tekton/target/tasks/*.yaml` and `tekton/target/pipelines/*.yaml`
     appears in **exactly one** of the three bundles (compare `# <path>` header
     comments the `addToFile` function writes, or count `kind: Task|Pipeline` docs by
     name across the three files).
   - `ibm-mas-tekton.yaml` and `ibm-mas-tekton-fvt.yaml` contain **zero** resources
     whose `metadata.name` starts with `gitops-`.
   - `ibm-mas-tekton-gitops.yaml` contains all `gitops-*` tasks/pipelines, including
     the `-after-provision` / `-after-deprovision` variants and
     `deprovision-aiservice-deps` (+ its `-after-deprovision` variant).
   - `gitops-mas-fvt-preparer*` and `gitops-aiservice-fvt-preparer*` are in the
     **gitops** bundle, no longer the FVT bundle (D1 behavior change).
   - Existing schema tests still pass: `.venv/bin/pytest tekton/test_schema.py -v`.
3. **Reference sanity check** (one-off, can be part of the same test): parse each
   bundle; collect `taskRef.name` values from every pipeline; assert each bundle's
   pipelines only reference tasks present in **that bundle or the main bundle**
   (gitops pipelines reference `mas-devops-wait-for-tekton` etc. from the framework
   tasks, so the gitops bundle is layered on top of the main bundle — that layering is
   expected and fine).
4. **CI dry run**: push to a branch, confirm the `build-tekton` job uploads three
   artifacts and the Artifactory release step pushes all three.

---

## 5. Behavior changes to flag in the PR description

1. **Main bundle shrinks.** Clusters where gitops tasks were applied via
   `mas install`/`mas update`/etc. stop receiving gitops definition updates. Existing
   applied gitops resources are **not deleted** (`updateTektonDefinitions` only
   applies/updates what's in the file) — they will drift stale until the gitops bundle
   is applied over them.
2. **FVT bundle loses the gitops fvt-preparer** tasks/pipelines
   (`gitops-mas-fvt-preparer*`, `gitops-aiservice-fvt-preparer*`). Any automation that
   applies only `ibm-mas-tekton-fvt.yaml` and uses the preparer must now also apply
   `ibm-mas-tekton-gitops.yaml`. If this turns out to be unwanted, the fallback is an
   explicit exception keeping those four in the FVT bundle — confirm with the FVT
   automation owners before merge.
3. **`deprovision-aiservice-deps` moves to the gitops bundle** despite lacking the
   prefix (D2).

---

## 6. Rollout / downstream coordination

- External MAS GitOps automation that currently relies on either (a) the monolithic
  `ibm-mas-tekton.yaml` from Artifactory containing gitops resources, or (b) `mas
  install` having applied them, must switch to applying `ibm-mas-tekton-gitops.yaml`
  (layered after the main bundle) — announce the new Artifactory path
  (`.../ibm-mas-tekton-gitops.yaml`) to the gitops repo owners.
- The gitops bundle is **additive-only over the main bundle**: gitops pipelines
  reference non-gitops tasks (e.g. `mas-devops-wait-for-tekton`, framework tasks), so
  consumers apply main first, then gitops. FVT remains independent of gitops (after
  change #2 above).
- Suggest a clean cross-check in one representative test cluster after the first
  release: apply main + gitops bundles, launch one `gitops-mas-deps`-style pipeline,
  confirm no missing-task errors.

## 7. Open questions (resolve before/at execution)

1. Confirm with FVT automation owners whether moving the `gitops-*-fvt-preparer*`
   resources out of the FVT bundle is acceptable (§5.2).
2. Confirm no external consumer applies `ibm-mas-tekton.yaml` from Artifactory
   expecting gitops resources to be included (vs. applying them from their own gitops
   repo) — if some do, consider a one-release transition where both old monolithic and
   new split bundles are published.
3. Decide whether the partition test from §4.2 should be permanent (extend
   `tekton/test_schema.py`) or a one-off verification — recommended: permanent, it is
   cheap and prevents future mis-filed tasks.
