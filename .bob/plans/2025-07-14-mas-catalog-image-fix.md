# MAS Catalog Image Fix Plan

## Objective

The `mas update` command ignores `MAS_CATALOG_DIGEST` (and by extension, development/pre-release catalog image digest pinning), causing the OLM CatalogSource pod to pull from the tag-based reference at `icr.io` rather than the pinned digest. This plan traces every layer where `mas_catalog_digest` support is missing from the update path and adds it to match the existing install path.

---

## Background & Design Decisions

### `MAS_CATALOG_IMAGE` vs `mas_catalog_digest`

- **`MAS_CATALOG_IMAGE`** is a GitOps-only concept consumed by `gitops_cluster` shell function → ArgoCD ApplicationSet YAML. It has no presence in the standard CLI `install`/`update` Tekton path and no corresponding variable in the `ibm_catalogs` Ansible role.
- **`mas_catalog_digest`** is the correct variable for controlling image pinning in the standard `install`/`update` path. It sets the digest portion of the CatalogSource image spec: `<registry>/<image>@<digest>` (immutable). Without it, OLM resolves a mutable `:tag` reference at runtime, which pulls whatever `icr.io` (or the dev registry) currently serves for that tag.

### Why the CatalogSource pod pulls from `icr.io`

The `ibm_catalogs` Ansible role selects a CatalogSource template based on `mas_catalog_version` and `mas_catalog_digest`. When `mas_catalog_digest` is empty (the update path today), it falls back to the `online-catalog.yml.j2` or `development-catalog.yml.j2` template, both of which hardcode the registry and use only `:tag`. The CatalogSource pod is then scheduled by OLM using that tag reference, resolving against `icr.io` at pull time.

### Responsible party

The **CLI `mas update` path** is responsible — not external OLM behavior. The `ibm_catalogs` Ansible role and its CatalogSource templates are correct; they just never receive a non-empty `mas_catalog_digest` from the update pipeline.

### Install path (working — use as reference)

| Layer | File | What it does |
|---|---|---|
| ArgParser | `python/src/mas/cli/install/argParser.py:80-83` | Adds `--mas-catalog-digest` argument |
| Params | `python/src/mas/cli/install/params.py:36` | Lists `mas_catalog_digest` in `optionalParams` |
| Summarizer | `python/src/mas/cli/install/summarizer.py:170-171` | Displays digest in summary |
| ArgBuilder | `python/src/mas/cli/install/argBuilder.py:53-54` | Appends `--mas-catalog-digest` to non-interactive command |
| Pipeline params | `tekton/src/params/install-ibmcatalogs.yml.j2:9-12` | Defines `mas_catalog_digest` Tekton param |
| Pipeline install.yml.j2 | `tekton/src/params/install.yml.j2:416` | Includes `install-ibmcatalogs.yml.j2` |
| Taskdef | `tekton/src/pipelines/taskdefs/cluster-setup/ibm-catalogs.yml.j2:15-16` | Passes `mas_catalog_digest` to task |
| Task | `tekton/src/tasks/dependencies/ibm-catalogs.yml.j2:22-25,51-52` | Task param → `MAS_CATALOG_DIGEST` env var |

### Update path (broken — gaps to fix)

| Layer | File | Gap |
|---|---|---|
| ArgParser | `python/src/mas/cli/update/argParser.py` | No `--mas-catalog-digest` argument |
| App | `python/src/mas/cli/update/app.py` | No `mas_catalog_digest` handling in summary or param list |
| Pipeline params | `tekton/src/pipelines/mas-update.yml.j2:21-35` | No `mas_catalog_digest` param |
| Pipeline task call | `tekton/src/pipelines/mas-update.yml.j2:229-247` | `update-catalog` task not passed `mas_catalog_digest` |

---

## Critical Rules

- Mirror the install path exactly — do not invent new patterns.
- `mas_catalog_digest` is optional with default `""` at every layer.
- The Tekton task definition (`tekton/src/tasks/dependencies/ibm-catalogs.yml.j2`) and Ansible role already support `mas_catalog_digest` — do not touch them.
- After any Tekton template change, regenerate using `ansible-playbook tekton/generate-tekton-pipelines.yml` and verify the generated `target/pipelines/mas-update.yaml` contains the digest param.
- Track progress in this plan file only — do not use chat todo lists.

---

## Execution Plan

### Phase 1 — Python CLI: add `mas_catalog_digest` to update flow

**Status:** `[x] done`

- [x] **1.1** In [`python/src/mas/cli/update/argParser.py`](python/src/mas/cli/update/argParser.py:98-99), add `--mas-catalog-digest` argument to `masArgGroup` (mirror [`install/argParser.py:79-83`](python/src/mas/cli/install/argParser.py:79-83)).
- [x] **1.2** In [`python/src/mas/cli/update/app.py`](python/src/mas/cli/update/app.py), add `mas_catalog_digest` to `optionalParams` list (line 173 area).
- [x] **1.3** In the update summary method (around line 299), display the digest when non-empty, mirroring [`install/summarizer.py:170-171`](python/src/mas/cli/install/summarizer.py:170-171).
- [x] **1.4** Validate: 64 tests pass, 3 pre-existing failures in test_dev_mode.py (use `--mas-catalog-version` which has always been unrecognized by update argparser — unrelated to this change).

### Phase 2 — Tekton pipeline: add `mas_catalog_digest` param to `mas-update.yml.j2`

**Status:** `[x] done`

- [x] **2.1** In [`tekton/src/pipelines/mas-update.yml.j2`](tekton/src/pipelines/mas-update.yml.j2:21-35), added `mas_catalog_digest` parameter definition after `mas_catalog_version`.
- [x] **2.2** In the `update-catalog` task invocation, added `- name: mas_catalog_digest` / `value: $(params.mas_catalog_digest)` after `mas_catalog_version`.
- [x] **2.3** Regenerated the pipeline: `ansible-playbook tekton/generate-tekton-pipelines.yml` — successful.
- [x] **2.4** `tekton/target/pipelines/mas-update.yaml` confirmed to contain `mas_catalog_digest` in both pipeline params spec and `update-catalog` task params.

---

## Final Validation

### Commands

```bash
# Unit tests for update CLI
python/.venv/bin/pytest python/test/update/ -v

# Regenerate Tekton definitions
ansible-playbook tekton/generate-tekton-pipelines.yml

# Verify generated pipeline
grep -A3 "mas_catalog_digest" target/pipelines/mas-update.yaml
```

### Success Criteria

1. `python test/update/` passes with no new failures.
2. `target/pipelines/mas-update.yaml` contains `mas_catalog_digest` as a top-level pipeline parameter with `default: ""`.
3. `target/pipelines/mas-update.yaml` contains `mas_catalog_digest` passed to the `update-catalog` task.
4. Running `mas update --catalog v9-XXXXXX-amd64 --mas-catalog-digest sha256:...` no longer raises `unrecognized argument`.
5. The Tekton PipelineRun for `mas-update` receives a non-empty `MAS_CATALOG_DIGEST` env var in the `mas-devops-ibm-catalogs` step, causing the Ansible role to select the digest-based CatalogSource template.

### Troubleshooting

- If `ansible-playbook` fails with template errors, check indentation around the new param block in `mas-update.yml.j2`.
- If the update `app.py` does not pass the digest through, check that `mas_catalog_digest` is included in the dict passed as `params=self.params` to `launchUpdatePipeline()` — the `self.params` dict is populated from all declared params so adding the arg and handling it should be sufficient.
