# Fix: `mas_icr_cpopen` Not Forwarded in `mas update --dev-mode`

## Objective
When running `mas update --dev-mode`, the `update-catalog` Tekton task (which runs the `ibm_catalogs` Ansible role) must receive `MAS_ICR_CPOPEN` pointing to the Artifactory registry, so the catalog source pod pulls from `docker-na-public.artifactory.swg-devops.com/wiotp-docker-local/cpopen/...` instead of `icr.io/cpopen/...`.

---

## Design Decisions

### Root Cause
Three distinct gaps exist in the update flow (each must be fixed independently):

1. **Python CLI (`update/app.py`)** — `UpdateApp.update()` never calls an equivalent of `InstallApp.configICR()`. In non-interactive mode it only passes args from `optionalParams` straight through; `mas_icr_cpopen` is never set.

2. **Tekton task (`tekton/src/tasks/dependencies/ibm-catalogs.yml.j2`)** — The `mas-devops-ibm-catalogs` task has no `mas_icr_cpopen` param and no `MAS_ICR_CPOPEN` env var. `ARTIFACTORY_USERNAME`/`ARTIFACTORY_TOKEN` exist but the ICR registry override does not.

3. **Tekton pipeline (`tekton/src/pipelines/mas-update.yml.j2`)** — The `mas-update` pipeline has no `mas_icr_cpopen` pipeline param, so there is nothing to forward to `update-catalog`.

4. **Tekton taskdef (`tekton/src/pipelines/taskdefs/cluster-setup/ibm-catalogs.yml.j2`)** — The cluster-setup taskdef (used by the install pipeline) has `artifactory_username`/`artifactory_token` but not `mas_icr_cpopen`. The install pipeline already has `mas_icr_cpopen` in `tekton/src/params/install.yml.j2`, so only the forwarding in the taskdef is missing.

### Design Choice: Mirror `configICR()` in Update Flow
Rather than adding a full `configICR()` method to `UpdateApp`, the minimal fix is:
- After `self.devMode = self.args.dev_mode`, add an inline block that calls `self.setParam("mas_icr_cpopen", ...)` using the same `getenv()` defaults as `InstallApp.configICR()`.
- Only `mas_icr_cpopen` is needed (not `mas_icr_cp` or `sls_icr_cpopen`) because only `ibm_catalogs` is invoked during update. This keeps the change minimal.
- The value is set unconditionally when `devMode` is True, else the default Ansible role value (`icr.io/cpopen`) applies — no param override is needed for the non-dev path.
- `mas_icr_cpopen` does **not** need to be in `optionalParams` because it is set explicitly and not derived from `self.args`; the loop over `optionalParams` handles arg-sourced values only.

### Pattern Reference
- `InstallApp.configICR()`: `python/src/mas/cli/install/app.py` lines 206–214
- `suite-install.yml.j2` param+env pattern: lines 81–83 (param) and line 213 (env)
- `mas-update.yml.j2` dev-mode params block: lines 30–39

---

## Critical Rules
- Introduce **no functional changes** beyond the four targeted edits below.
- Do **not** add `mas_icr_cp` or `sls_icr_cpopen` to the update flow — `ibm_catalogs` role does not use them.
- Preserve all existing params, env vars, and task structure in Jinja2 templates.
- Track progress ONLY in this plan document, NOT in chat todo lists.

---

## Execution Plan

### Phase 1 — Python CLI fix

**Intent**: When `UpdateApp.update()` runs with `devMode=True`, set `mas_icr_cpopen` to the Artifactory registry path (or the value of the `MAS_ICR_CPOPEN` env var if overridden).

**Expected Outcomes**:
- The non-interactive update path adds a `mas_icr_cpopen` pipeline parameter to the PipelineRun when `--dev-mode` is passed.
- Without `--dev-mode` nothing changes.

**Todo List**:
- [x] **1.1** In `python/src/mas/cli/update/app.py`, inside the `if self.args.mas_catalog_version:` block, after `self.devMode = self.args.dev_mode` (line 162) add:
  ```python
  from os import getenv  # (if not already imported at top)
  ...
  if self.devMode:
      self.setParam("mas_icr_cpopen", getenv("MAS_ICR_CPOPEN", "docker-na-public.artifactory.swg-devops.com/wiotp-docker-local/cpopen"))
  ```
  Place this block **after** the `optionalParams` loop (after line 207) so that `devMode` is fully resolved before the param is set, and the explicit `setParam` call is not overridden by the loop.
- [x] **1.2** Verify `getenv` is already imported in `update/app.py` (check top-level imports); add `from os import getenv` only if missing.

**Relevant Context**:
- `python/src/mas/cli/update/app.py` — `update()` method, lines 156–221
- `python/src/mas/cli/install/app.py` — `configICR()` lines 206–214 for the exact pattern to mirror

**Status**: `[x] complete`

---

### Phase 2 — Tekton task: add `mas_icr_cpopen` to `ibm-catalogs`

**Intent**: The `mas-devops-ibm-catalogs` Tekton task must declare `mas_icr_cpopen` as a parameter and expose it as the `MAS_ICR_CPOPEN` environment variable so the Ansible role receives the registry override.

**Expected Outcomes**:
- `tekton/src/tasks/dependencies/ibm-catalogs.yml.j2` has a `mas_icr_cpopen` param (default `""`) and a `MAS_ICR_CPOPEN` env var mapped to it.

**Todo List**:
- [x] **2.1** In `tekton/src/tasks/dependencies/ibm-catalogs.yml.j2`, add after the `mas_catalog_digest` param block (after line 25):
  ```yaml
      - name: mas_icr_cpopen
        type: string
        description: Override the ICR cpopen registry (used in dev mode)
        default: ""
  ```
- [x] **2.2** In the same file, add after the `MAS_CATALOG_DIGEST` env var (after line 52):
  ```yaml
        - name: MAS_ICR_CPOPEN
          value: $(params.mas_icr_cpopen)
  ```

**Relevant Context**:
- `tekton/src/tasks/dependencies/ibm-catalogs.yml.j2` — full file (76 lines)
- `tekton/src/tasks/suite-install.yml.j2` lines 81–83 and 213 — exact pattern to mirror

**Status**: `[x] complete`

---

### Phase 3 — Tekton pipeline: add `mas_icr_cpopen` to `mas-update`

**Intent**: The `mas-update` pipeline needs a `mas_icr_cpopen` pipeline-level parameter so the Python CLI can inject it into the PipelineRun, and the `update-catalog` task step can forward it.

**Expected Outcomes**:
- `tekton/src/pipelines/mas-update.yml.j2` declares a `mas_icr_cpopen` param (default `""`).
- The `update-catalog` task in the same file forwards `mas_icr_cpopen` to its params list.

**Todo List**:
- [x] **3.1** In `tekton/src/pipelines/mas-update.yml.j2`, in the `# Development Build Support` params block (around lines 30–39), add after `artifactory_token`:
  ```yaml
      - name: mas_icr_cpopen
        default: ""
        type: string
        description: Override the ICR cpopen registry (used in dev mode)
  ```
- [x] **3.2** In the same file, in the `update-catalog` task params (lines 250–254), add after the `artifactory_token` param:
  ```yaml
          # ICR registry override for dev mode
          - name: mas_icr_cpopen
            value: $(params.mas_icr_cpopen)
  ```

**Relevant Context**:
- `tekton/src/pipelines/mas-update.yml.j2` lines 30–39 (dev build params) and lines 240–255 (update-catalog task params)

**Status**: `[x] complete`

---

### Phase 4 — Tekton taskdef: forward `mas_icr_cpopen` in `cluster-setup/ibm-catalogs.yml.j2`

**Intent**: The `ibm-catalogs` taskdef (used by the install pipeline) must forward `mas_icr_cpopen` from the pipeline params to the task. The install pipeline already has `mas_icr_cpopen` defined in `tekton/src/params/install.yml.j2`; only the taskdef forwarding is missing.

**Expected Outcomes**:
- `tekton/src/pipelines/taskdefs/cluster-setup/ibm-catalogs.yml.j2` passes `mas_icr_cpopen: $(params.mas_icr_cpopen)` to the task.

**Todo List**:
- [x] **4.1** In `tekton/src/pipelines/taskdefs/cluster-setup/ibm-catalogs.yml.j2`, after the `mas_catalog_digest` param forward (line 16), add:
  ```yaml
      - name: mas_icr_cpopen
        value: $(params.mas_icr_cpopen)
  ```

**Relevant Context**:
- `tekton/src/pipelines/taskdefs/cluster-setup/ibm-catalogs.yml.j2` — full file (19 lines)
- `tekton/src/params/install.yml.j2` lines 437–439 — confirms `mas_icr_cpopen` is already a pipeline param

**Status**: `[x] complete`

---

## Final Validation

After all phases are complete:

1. **Regenerate Tekton artefacts**:
   ```bash
   ansible-playbook tekton/generate-tekton-tasks.yml
   ansible-playbook tekton/generate-tekton-pipelines.yml
   ```
2. **Inspect generated files**:
   - `target/tasks/ibm-catalogs.yaml` — must contain `mas_icr_cpopen` param and `MAS_ICR_CPOPEN` env var.
   - `target/pipelines/mas-update.yaml` — must contain `mas_icr_cpopen` at pipeline level and forwarded in `update-catalog` task.
   - `target/pipelines/mas-install.yaml` — must contain `mas_icr_cpopen` forwarded in `ibm-catalogs` task.
3. **Python unit tests**: Run existing update tests to confirm no regressions.
4. **Manual smoke test** (if environment available): Run `mas update --dev-mode --mas-catalog-version v9-master-amd64 ...` and confirm the PipelineRun's `update-catalog` TaskRun has `MAS_ICR_CPOPEN=docker-na-public.artifactory.swg-devops.com/wiotp-docker-local/cpopen`.
