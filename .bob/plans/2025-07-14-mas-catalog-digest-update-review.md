# MAS Catalog Digest — Update Pipeline Fix

**Branch:** `fix-dev-channel-upgrade`  
**Repos affected:** `ibm-mas/cli` · `ibm-mas/python-devops`  
**Author:** Parveen Kumar  
**Reviewer:** David Parker

---

## 1. The Problem

### Observed behaviour

Setting `MAS_CATALOG_IMAGE` in `~/Github/dev-env/mas.env` and running `mas update` had no effect — the OLM CatalogSource pod continued to pull from `icr.io` using a tag-based image reference rather than the intended pinned image.

### Root-cause investigation

`MAS_CATALOG_IMAGE` is a **GitOps-only** variable. It is consumed by the `gitops_cluster` shell function and rendered into ArgoCD ApplicationSet YAML. It has no presence in the standard `mas install` / `mas update` Tekton pipeline path, and the `ibm_catalogs` Ansible role has no `mas_catalog_image` variable — the registry hostname is hardcoded per CatalogSource Jinja2 template.

The correct variable for controlling which image the CatalogSource uses in the standard path is **`mas_catalog_digest`**. The `ibm_catalogs` Ansible role uses this to select between two template families:

| Template | Image reference style | When used |
|---|---|---|
| `online-catalog.yml.j2` | `icr.io/cpopen/ibm-maximo-operator-catalog:{{ mas_catalog_version }}` | No digest supplied |
| `development-catalog.yml.j2` | `docker-na-public.artifactory.../ibm-maximo-operator-catalog:{{ mas_catalog_version }}` | Artifactory credentials supplied, no digest |
| `development-catalog-with-digest.yml.j2` | `docker-na-public.artifactory.../ibm-maximo-operator-catalog@{{ mas_catalog_digest }}` | Digest supplied (immutable) |
| `offline-catalog.yml.j2` | `icr.io/cpopen/ibm-maximo-operator-catalog@{{ mas_catalog_metadata.catalog_digest }}` | Offline/airgap |

When `mas_catalog_digest` is empty, OLM resolves a **mutable tag** at runtime — it always pulls whatever `icr.io` currently serves for that tag, ignoring any local override. With a digest, OLM pins to a specific immutable image layer.

### Why install works but update does not

`mas install` has full end-to-end support for `mas_catalog_digest`. The `mas update` path was added later and the parameter was simply never wired through.

| Layer | `mas install` | `mas update` |
|---|---|---|
| CLI argument | ✅ `--mas-catalog-digest` in `install/argParser.py` | ❌ Missing |
| Python params | ✅ `optionalParams` in `install/params.py` | ❌ Missing |
| PipelineRun template | ✅ Conditional block in `pipelinerun-install.yml.j2` | ❌ Missing from `pipelinerun-update.yml.j2` |
| Tekton Pipeline spec | ✅ `install-ibmcatalogs.yml.j2` included | ❌ Not in `mas-update.yml.j2` |
| Tekton task invocation | ✅ Passed in `cluster-setup/ibm-catalogs.yml.j2` | ❌ Not passed in update task call |
| Tekton task definition | ✅ `mas-devops-ibm-catalogs` receives it | ✅ Same task — already correct |
| Ansible role | ✅ Reads `MAS_CATALOG_DIGEST` env var | ✅ Same role — already correct |

The Ansible role and the Tekton task definition required **no changes** — they already handle `mas_catalog_digest` correctly. The gap was entirely in the update path above them.

---

## 2. Changes Made

### 2.1 `ibm-mas/cli` — `fix-dev-channel-upgrade` branch

#### `python/src/mas/cli/update/argParser.py`

Added `--mas-catalog-digest` to the `Catalog Selection` argument group, matching the install argParser:

```python
masArgGroup.add_argument(
    "--mas-catalog-digest",
    required=False,
    help="IBM Maximo Operator Catalog Digest, only required when installing development catalog sources"
)
```

Without this, argparse raises `unrecognized arguments` and exits with code 2 before any other logic runs.

#### `python/src/mas/cli/update/app.py`

Added `"mas_catalog_digest"` to `optionalParams` in the non-interactive branch of `update()`. This causes the value parsed from `--mas-catalog-digest` to be stored via `self.setParam()` and included in `self.params`, which is the dict passed directly to `launchUpdatePipeline()`.

Also added a summary display line (consistent with `install/summarizer.py`):

```python
if self.getParam("mas_catalog_digest") not in (None, ""):
    self.printSummary("Catalog Digest", self.getParam("mas_catalog_digest"))
```

#### `tekton/src/pipelines/mas-update.yml.j2`

Added `mas_catalog_digest` as an optional pipeline parameter (mirroring `tekton/src/params/install-ibmcatalogs.yml.j2`):

```yaml
- name: mas_catalog_digest
  type: string
  description: Set when using dev or pre-release catalog in airgap
  default: ""
```

Added the parameter to the `update-catalog` task invocation (mirroring `tekton/src/pipelines/taskdefs/cluster-setup/ibm-catalogs.yml.j2`):

```yaml
- name: mas_catalog_digest
  value: $(params.mas_catalog_digest)
```

The generated output at `tekton/target/pipelines/mas-update.yaml` was verified to contain both additions.

#### `python/tests/integration/update/test_catalog_digest.py` (new file)

Three integration tests written TDD-style (test written and confirmed failing before implementation):

- `test_mas_catalog_digest_arg_is_accepted` — verifies argparse no longer raises on `--mas-catalog-digest`
- `test_mas_catalog_digest_passed_to_pipeline` — verifies the digest value reaches `app.params`
- `test_mas_catalog_digest_omitted_defaults_empty` — verifies omitting the flag leaves the param absent/empty

---

### 2.2 `ibm-mas/python-devops` — `fix-dev-channel-upgrade` branch

#### `src/mas/devops/templates/pipelinerun-update.yml.j2`

Added the conditional `mas_catalog_digest` block immediately after `mas_catalog_version`, matching the existing pattern in `pipelinerun-install.yml.j2`:

```jinja
{%- if mas_catalog_digest is defined and mas_catalog_digest != "" %}
    - name: mas_catalog_digest
      value: "{{ mas_catalog_digest }}"
{%- endif %}
```

Without this, even though `mas_catalog_digest` is now carried in `self.params` by the CLI and declared in the Tekton Pipeline spec, the `PipelineRun` resource created by `launchUpdatePipeline()` would still not include the parameter — the `mas-update` Tekton Pipeline would receive an empty string for `mas_catalog_digest`, and the Ansible role would fall back to a tag-based CatalogSource.

---

## 3. End-to-end flow after the fix

```
mas update --catalog v9-260625-amd64 --mas-catalog-digest sha256:028ecfe...
    │
    ├─ update/argParser.py          parses --mas-catalog-digest → args.mas_catalog_digest
    ├─ update/app.py                setParam("mas_catalog_digest", "sha256:028ecfe...")
    │                               → included in self.params dict
    │
    ├─ pipelinerun-update.yml.j2    renders mas_catalog_digest into PipelineRun YAML
    │   (python-devops)             → PipelineRun param: mas_catalog_digest = sha256:028ecfe...
    │
    ├─ mas-update Tekton Pipeline   receives mas_catalog_digest pipeline param
    │   (tekton/src/pipelines/)     passes it to update-catalog task
    │
    ├─ mas-devops-ibm-catalogs Task sets MAS_CATALOG_DIGEST env var (unchanged)
    │
    └─ ibm_catalogs Ansible Role    MAS_CATALOG_DIGEST non-empty → selects
        (ansible-devops)            development-catalog-with-digest.yml.j2
                                    CatalogSource image: <registry>@sha256:028ecfe...  ✅
```

---

## 4. What was NOT changed

- `ibm_catalogs` Ansible role — already correct, not touched
- `mas-devops-ibm-catalogs` Tekton task definition — already correct, not touched
- `mas install` path — already working, not touched
- GitOps path (`gitops_cluster` / ArgoCD) — separate concern, not touched
- `MAS_CATALOG_IMAGE` — remains GitOps-only; documented as out of scope for standard install/update

---

## 5. Test results

```
python3 -m pytest python/tests/integration/update/ -q

64 passed, 3 failed (pre-existing — test_dev_mode.py uses --mas-catalog-version
which has never been a valid flag for mas update; unrelated to this change)
```

All 3 new tests pass. No regressions in the 61 previously passing tests.

---

## 6. CI behaviour

The `build-cli.yml` GitHub Actions workflow uses branch-name matching to install python-devops:

```bash
python3 -m pip install "git+https://github.com/ibm-mas/python-devops.git@${GITHUB_REF_NAME}"
```

When this PR runs on `fix-dev-channel-upgrade`, it installs python-devops from the same-named branch automatically — no workflow changes required.
