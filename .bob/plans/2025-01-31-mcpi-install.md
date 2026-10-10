# Plan: Add `mcpi-install` Command to MAS CLI

## Objective

Add a new `mcpi-install` CLI command that installs the **Maximo Cluster Performance Insights (MCPI)** add-on operator (`ibm-mas-cfg-mcpi`) via a Tekton pipeline. The implementation follows the exact same 4-layer architecture used by `aiservice-install`.

---

## Repos Involved

| Repo | What changes |
|------|-------------|
| **`cli`** (this repo) | Python CLI module + Tekton templates — Phases 1 & 2 of this plan |
| **`ansible-devops`** | Add `mcpicfg` role to the `ibm.mas_devops` collection so `run-role.sh mcpicfg` works in the CLI image |
| **`python-devops`** (local path: `/Users/tahamadou/Source/MAS/python-devops/`) | Add `launchMcpiInstallPipeline()` + `prepareMcpiPipelinesNamespace()` + 3 new templates (see Design Decisions) |
| **`ibm-mas`** | `mcpicfg` role source already exists at `operator/ibm-mas-cfg-mcpi/roles/mcpicfg/` — no changes needed here, role is copied to `ansible-devops` |

---

## Design Decisions

### Architecture Layers

| Layer | Responsibility |
|-------|---------------|
| **Layer 1 — Dispatcher** | `__main__.py` routes `mcpi-install` → `McpiInstallApp().install()` |
| **Layer 2 — Python App** | `python/src/mas/cli/mcpi/install/` — interactive/non-interactive CLI |
| **Layer 3 — Tekton** | Task CRD + pipeline fragment + standalone pipeline + param files |
| **Layer 4 — Ansible** | `mcpicfg` role already exists in `ibm-mas`; invoked via `run-role.sh mcpicfg` |

### CLI Parameters

MCPI has no database, no S3, no ODH/RHOAI, no workspace sync. Its parameter set is minimal compared to AI Service:

| CLI Flag | `dest` / param name | Required | Notes |
|----------|---------------------|----------|-------|
| `-c, --mas-catalog-version` | `mas_catalog_version` | Yes | Catalog selection |
| `--mas-catalog-digest` | `mas_catalog_digest` | No | Dev/airgap catalog |
| `--ibm-entitlement-key` | `ibm_entitlement_key` | Yes | Image pull secret |
| `--mas-instance-id` | `mas_instance_id` | Yes | MAS instance ID (triggers non-interactive) |
| `--mcpi-channel` | `mcpi_channel` | Yes (in non-interactive) | Subscription channel; acts as sentinel guard in pipeline |
| `--routing-mode` | `routing_mode` | No | `subdomain` or `path`; default `subdomain` |
| `--manual-route-mgmt` | `manual_route_mgmt` | No | Default `false` |
| `--license-file` | `license_file` | Yes (non-interactive) | SLS license file path |
| `--sls-namespace` | `sls_namespace` | No | Default `ibm-sls` |
| `--dedicated-sls` | `dedicated_sls` | No | Flag — set SLS ns to `mas-<id>-sls` |
| `--contact-email` | `dro_contact_email` | Yes (non-interactive) | DRO contact |
| `--contact-firstname` | `dro_contact_firstname` | Yes (non-interactive) | DRO contact |
| `--contact-lastname` | `dro_contact_lastname` | Yes (non-interactive) | DRO contact |
| `--dro-namespace` | `dro_namespace` | No | DRO namespace |
| `--mongodb-namespace` | `mongodb_namespace` | No | BYO MongoDB namespace |
| `--storage-class-rwo` | `storage_class_rwo` | Yes | Pipeline storage |
| `--storage-class-rwx` | `storage_class_rwx` | Yes | Pipeline storage |
| `--storage-pipeline` | `storage_pipeline` | Yes (non-interactive) | Pipeline PVC class |
| `--storage-accessmode` | `storage_accessmode` | Yes (non-interactive) | ReadWriteMany / ReadWriteOnce |
| `--additional-configs` | `additional_configs` | No | Extra config dir |
| `--artifactory-username` | `artifactory_username` | No | Dev mode only |
| `--artifactory-token` | `artifactory_token` | No | Dev mode only |
| `--image-pull-policy` | `image_pull_policy` | No | Tekton image pull policy |
| `--service-account` | `service_account_name` | No | Custom SA |
| `--slack-token` | `slack_token` | No | Slack integration |
| `--slack-channel` | `slack_channel` | No | Slack integration |
| `--advanced` | `advanced` | No | Show advanced prompts in interactive mode |
| `--simplified` | `simplified` | No | Hide advanced prompts in interactive mode |
| `--accept-license` | `accept_license` | No | Pre-accept license |
| `--dev-mode` | `dev_mode` | No | Dev mode |
| `--skip-pre-check` | `skip_pre_check` | No | Skip pre-install healthcheck |
| `--no-confirm` | `no_confirm` | No | Skip confirmation prompt |
| `-h, --help` | help | No | |

> **Reason for SLS/DRO params**: Even though MCPI has no per-app entitlement, the pipeline still requires SLS and DRO to be installed as MAS core dependencies. This follows the same pattern as `aiservice-install`.

> **`routing_mode` and `manual_route_mgmt`**: MCPI-specific params beyond the standard MAS set. These map directly to `ROUTING_MODE` and `MANUAL_ROUTE_MGMT` env vars consumed by the `mcpicfg` Ansible role.

### requiredParams and optionalParams

**`requiredParams`:**
```python
[
    "mas_catalog_version",
    "mas_instance_id",
    "storage_class_rwo",
    "storage_class_rwx",
    "ibm_entitlement_key",
    "mcpi_channel",
    "dro_contact_email",
    "dro_contact_firstname",
    "dro_contact_lastname",
]
```

**`optionalParams`:**
```python
[
    "image_pull_policy",
    "service_account_name",
    "mas_catalog_digest",
    "sls_namespace",
    "dro_namespace",
    "mongodb_namespace",
    "routing_mode",
    "manual_route_mgmt",
    "artifactory_username",
    "artifactory_token",
    "slack_token",
    "slack_channel",
]
```

### Pipelines Namespace

Follows the AI Service pattern exactly: dedicated namespace `mcpi-{mas_instance_id}-pipelines`.

**A new `prepareMcpiPipelinesNamespace()` function is needed in `python-devops`** (analogous to `prepareAiServicePipelinesNamespace()` at line 731). It requires:
- New template: `mcpi-pipelines-rbac.yml.j2` (clone of `aiservice-pipelines-rbac.yml.j2`, replace `aiservice` with `mcpi`)
- New template: `mcpi-pipelines-pvc.yml.j2` (clone of `aiservice-pipelines-pvc.yml.j2`, replace `aiservice` with `mcpi`)
- Same signature: `prepareMcpiPipelinesNamespace(dynClient, instanceId, storageClass, accessMode, waitForBind=True, configureRBAC=True)`

### `launchInstallPipeline()` — Confirmed Blocker

`launchInstallPipeline()` in `python-devops/src/mas/devops/tekton.py` (line 1285) has two hardcoded branches:
- If `mas_instance_id` in params → launches `mas-install` pipeline, namespace `mas-{id}-pipelines`
- Otherwise → launches AI Service install, namespace `aiservice-{id}-pipelines`

**MCPI needs a new function `launchMcpiInstallPipeline()` in `python-devops`** plus a new Jinja2 template `pipelinerun-mcpi-install.yml.j2`. This is a **Phase 0 prerequisite** that must be done in the `python-devops` repo before Phase 1 of this CLI plan.

The new function uses `launchPipelineRun()` (generic, line 1247) with:
- `namespace = f"mcpi-{params['mas_instance_id']}-pipelines"`
- `templateName = "pipelinerun-mcpi-install"`
- PipelineRun URL: `f"{getConsoleURL(dynClient)}/k8s/ns/mcpi-{instanceId}-pipelines/tekton.dev~v1beta1~PipelineRun/{instanceId}-install-{timestamp}"`

The `pipelinerun-mcpi-install.yml.j2` template (in `src/mas/devops/templates/`) includes only MCPI-relevant params: `ibm_entitlement_key`, `mas_instance_id`, `mas_catalog_version`, `mcpi_channel`, `routing_mode`, `manual_route_mgmt`, plus SLS/DRO params and storage class params (trim `pipelinerun-install.yml.j2` to remove Db2/Kafka/CP4D/MAS app sections).

### Class Hierarchy

```python
class McpiInstallApp(
    BaseApp,
    McpiInstallArgBuilderMixin,    # from argBuilder.py
    McpiInstallSummarizerMixin,    # from summarizer.py
    InstallSettingsMixin,           # reused from install/settings.py
    ConfigGeneratorMixin            # reused from gencfg.py
)
```

### `mcpicfg` Role in `ansible-devops` — Confirmed Blocker

`run-role.sh mcpicfg` inside the Tekton task calls `ansible-playbook ibm.mas_devops.run_role` which dynamically loads the `ibm.mas_devops.mcpicfg` role. The `mcpicfg` role currently exists **only in the `ibm-mas` operator repo** at `operator/ibm-mas-cfg-mcpi/roles/mcpicfg/`. It is **not present** in `ansible-devops/ibm/mas_devops/roles/`.

**The `mcpicfg` role must be added to `ansible-devops`** (Phase 0 prerequisite) so it gets bundled into the CLI Docker image. The role must be placed at `ansible-devops/ibm/mas_devops/roles/mcpicfg/` with the same structure as `operator/ibm-mas-cfg-mcpi/roles/mcpicfg/` (tasks/, defaults/, vars/, templates/).

### Interactive Mode — Trigger

Presence of `--mas-instance-id` triggers **non-interactive** mode (omitting it triggers interactive mode prompts). This follows the same sentinel pattern as `aiservice-install` where the presence of `--aiservice-instance-id` (mapped to `args.aiservice_instance_id`) determines mode.

### Tekton Task Env Vars

The `mcpicfg` role reads these env vars:

| Env Var | Role Variable | Default |
|---------|--------------|---------|
| `IBM_ENTITLEMENT_KEY` | image pull secret | — |
| `MAS_INSTANCE_ID` | pipeline context | — |
| `MCPI_CHANNEL` | subscription channel | — |
| `ROUTING_MODE` | `routingMode` | `subdomain` |
| `MANUAL_ROUTE_MGMT` | `manualRouteMgmt` | `false` |

### No gencfg Step

MCPI has no post-install config generation. The McpiCfg CR is created and managed by the operator itself. No `gencfg-mcpi` task is needed.

### Standalone vs. `mas-install` Pipeline

MCPI gets both:
1. A **standalone `mcpi-install` pipeline** for independent MCPI installs
2. The **`mas-install` pipeline** is modified to include MCPI as an optional task guarded by `when: mcpi_channel != ""`

---

## Critical Rules

- Track progress in this plan file only, not in chat todo lists
- Follow existing code style exactly — look at `aiservice/install/` files as the canonical reference for every structural decision
- Copyright header `# Copyright (c) 2026 IBM Corporation` required in all new Python files
- All new Python files need Google-style docstrings
- Preserve all existing tests — add new tests, do not modify existing ones
- Validate at end of each phase: run `black`, `flake8`, and `pytest` before marking a phase done
- **Phase 0 (`ansible-devops` + `python-devops`) must be complete before Phase 1 begins** — the CLI cannot be completed without `launchMcpiInstallPipeline()` and the `mcpicfg` role in the collection

---

## Execution Plan

### Phase 0 — Cross-Repo Prerequisites
[x] **Status:** complete

**Intent:** Two changes in external repos are required before the CLI code can be completed. These must be opened as PRs in their respective repos and merged (or at least available as dev branches) before Phase 1 can be validated end-to-end.

**Expected Outcomes:**
- `ansible-devops` has a `mcpicfg` role under `ibm/mas_devops/roles/mcpicfg/`
- `python-devops` exposes `launchMcpiInstallPipeline()`, `prepareMcpiPipelinesNamespace()`, `pipelinerun-mcpi-install.yml.j2`, `mcpi-pipelines-rbac.yml.j2`, `mcpi-pipelines-pvc.yml.j2`

**Todo:**

- [x] **0.1** In the **`ansible-devops`** repo: Copy the `mcpicfg` role from `ibm-mas`:
  - Source: `/Users/tahamadou/Source/MAS/ibm-mas/operator/ibm-mas-cfg-mcpi/roles/mcpicfg/`
  - Destination: `/Users/tahamadou/Source/MAS/ansible-devops/ibm/mas_devops/roles/mcpicfg/`
  - Copy all subdirectories: `tasks/`, `defaults/`, `vars/`, `templates/`
  - Verify the role loads: `ansible-galaxy collection build` should succeed

- [x] **0.2** In **`python-devops`** (`/Users/tahamadou/Source/MAS/python-devops/`): Add MCPI namespace templates:
  - `src/mas/devops/templates/mcpi-pipelines-rbac.yml.j2` — clone of `aiservice-pipelines-rbac.yml.j2` with `aiservice` → `mcpi`
  - `src/mas/devops/templates/mcpi-pipelines-pvc.yml.j2` — clone of `aiservice-pipelines-pvc.yml.j2` with `aiservice` → `mcpi`

- [x] **0.3** In **`python-devops`**: Add `prepareMcpiPipelinesNamespace()` to `src/mas/devops/tekton.py`:
  - After `prepareAiServicePipelinesNamespace()` (line 731)
  - Same signature: `prepareMcpiPipelinesNamespace(dynClient, instanceId, storageClass, accessMode, waitForBind=True, configureRBAC=True)`
  - Uses `namespace = f"mcpi-{instanceId}-pipelines"`
  - Uses templates `mcpi-pipelines-rbac.yml.j2` and `mcpi-pipelines-pvc.yml.j2`
  - Renders with `mcpi_instance_id=instanceId` (not `aiservice_instance_id`)

- [x] **0.4** In **`python-devops`**: Add `pipelinerun-mcpi-install.yml.j2` to `src/mas/devops/templates/`:
  - Based on `pipelinerun-install.yml.j2` trimmed to MCPI scope:
    - `metadata.name: "{{mas_instance_id}}-install-{{ timestamp }}"`
    - `labels.tekton.dev/pipeline: mcpi-install`
    - `spec.pipelineRef.name: mcpi-install`
  - Params: `ibm_entitlement_key`, `storage_class_rwx`, `storage_class_rwo`, SLS params, DRO params, `mas_catalog_version` (+conditional `mas_catalog_digest`), `mas_instance_id`, `mcpi_channel`, conditional `routing_mode`, conditional `manual_route_mgmt`, conditional `artifactory_username/token`, conditional `image_pull_policy`, conditional `skip_pre_check`
  - Workspaces: `shared-configs`, `shared-entitlement`, `shared-pod-templates`, `shared-additional-configs`, `shared-certificates` (same as `pipelinerun-install.yml.j2`, no `shared-db2` or `shared-aiservice-config`)

- [x] **0.5** In **`python-devops`**: Add `launchMcpiInstallPipeline()` to `src/mas/devops/tekton.py`:
  - After `launchInstallPipeline()` (line 1285)
  - Signature: `launchMcpiInstallPipeline(dynClient: DynamicClient, params: dict) -> str`
  - Body:
    ```python
    instanceId = params["mas_instance_id"]
    namespace = f"mcpi-{instanceId}-pipelines"
    timestamp = launchPipelineRun(dynClient, namespace, "pipelinerun-mcpi-install", params)
    return f"{getConsoleURL(dynClient)}/k8s/ns/mcpi-{instanceId}-pipelines/tekton.dev~v1beta1~PipelineRun/{instanceId}-install-{timestamp}"
    ```

**Relevant Context:**
- `launchInstallPipeline` source: `python-devops/src/mas/devops/tekton.py:1285`
- `prepareAiServicePipelinesNamespace` source: `python-devops/src/mas/devops/tekton.py:731`
- `launchPipelineRun` generic: `python-devops/src/mas/devops/tekton.py:1247`
- `pipelinerun-install.yml.j2` (trim for mcpi): `python-devops/src/mas/devops/templates/pipelinerun-install.yml.j2`
- `aiservice-pipelines-rbac.yml.j2` (clone): `python-devops/src/mas/devops/templates/aiservice-pipelines-rbac.yml.j2`
- `aiservice-pipelines-pvc.yml.j2` (clone): `python-devops/src/mas/devops/templates/aiservice-pipelines-pvc.yml.j2`
- `mcpicfg` role source: `/Users/tahamadou/Source/MAS/ibm-mas/operator/ibm-mas-cfg-mcpi/roles/mcpicfg/`
- `ansible-devops` roles dir: `/Users/tahamadou/Source/MAS/ansible-devops/ibm/mas_devops/roles/`

---

### Phase 1 — Python CLI Module
[x] **Status:** complete

**Intent:** Create the `python/src/mas/cli/mcpi/install/` module with all 6 files and wire it into the dispatcher. This is the UI layer that collects user input, validates it, builds the pipeline command, and launches the Tekton pipeline.

**Expected Outcomes:**
- `mas-cli mcpi-install --help` works and shows all flags
- Non-interactive mode runs end-to-end with mocked Tekton calls
- All files are lint-clean and tested

**Todo:**

- [ ] **1.1** Create `python/src/mas/cli/mcpi/__init__.py`:
  ```python
  # Copyright header (2026)
  # Empty — package marker
  ```

- [ ] **1.2** Create `python/src/mas/cli/mcpi/install/__init__.py`:
  - Mirror `python/src/mas/cli/aiservice/install/__init__.py` exactly:
    ```python
    from ...cli import BaseApp  # noqa: F401
    ```

- [ ] **1.4** Create `python/src/mas/cli/mcpi/install/params.py`:
  - `requiredParams` and `optionalParams` as defined in Design Decisions above

- [ ] **1.5** Create `python/src/mas/cli/mcpi/install/argParser.py`:
  - Module-level `argparse.ArgumentParser` instance named `mcpiInstallArgParser`
  - Program: `"mas mcpi-install"`
  - Argument groups (in order):
    1. `MAS Catalog Selection & Entitlement` — `--mas-catalog-version`, `--mas-catalog-digest`, `--ibm-entitlement-key`
    2. `MCPI Basic Configuration` — `-i, --mas-instance-id`
    3. `MCPI Advanced Configuration` — `--routing-mode`, `--manual-route-mgmt`
    4. `MAS Advanced Configuration` — `--additional-configs`
    5. `Storage` — `--storage-class-rwo`, `--storage-class-rwx`, `--storage-pipeline`, `--storage-accessmode`
    6. `IBM Suite License Service` — `--license-file`, `--sls-namespace`, `--dedicated-sls`
    7. `IBM Data Reporting Operator (DRO)` — `--contact-email`, `--contact-firstname`, `--contact-lastname`, `--dro-namespace`
    8. `MongoDb Community Operator` — `--mongodb-namespace`
    9. `MAS Applications` — `--mcpi-channel`
    10. `Development Mode` — `--artifactory-username`, `--artifactory-token`
    11. `More` — `--advanced`, `--simplified`, `--accept-license`, `--dev-mode`, `--skip-pre-check`, `--no-confirm`, `--image-pull-policy`, `--service-account`, `--slack-token`, `--slack-channel`, `-h/--help`
  - `isValidFile()` helper for `--license-file` validation (mirror aiservice pattern)

- [ ] **1.6** Create `python/src/mas/cli/mcpi/install/argBuilder.py`:
  - Class `McpiInstallArgBuilderMixin` with `buildCommand(self) -> str`
  - Build a re-runnable shell command starting with `export IBM_ENTITLEMENT_KEY=x`
  - Command: `mas mcpi-install --mas-catalog-version ... --ibm-entitlement-key $IBM_ENTITLEMENT_KEY ...`
  - Include all set params in the same style as `aiServiceInstallArgBuilderMixin.buildCommand()`
  - End with `--accept-license --no-confirm`

- [ ] **1.7** Create `python/src/mas/cli/mcpi/install/summarizer.py`:
  - Class `McpiInstallSummarizerMixin`
  - Methods:
    - `ocpSummary()` — pipeline config, OCP architecture, storage classes
    - `mcpiSummary()` — catalog version, MAS instance ID, MCPI channel, routing mode, manual route mgmt
    - `droSummary()` — DRO email, first/last name, namespace
    - `slsSummary()` — SLS namespace, license file
    - `mongoSummary()` — MongoDB namespace (BYO vs. install)
    - `slackSummary()` — Slack channel
    - `displayInstallSummary()` — orchestrates all summaries; logs `yaml.dump(self.params)` at DEBUG; calls `getConsoleURL(self.dynamicClient)` for connected cluster line

- [ ] **1.8** Create `python/src/mas/cli/mcpi/install/app.py`:
  - Class `McpiInstallApp(BaseApp, McpiInstallArgBuilderMixin, McpiInstallSummarizerMixin, InstallSettingsMixin, ConfigGeneratorMixin)`
  - Import `mcpiInstallArgParser` from `.argParser`
  - Import `requiredParams, optionalParams` from `.params`
  - Import `McpiInstallArgBuilderMixin` from `.argBuilder`
  - Import `McpiInstallSummarizerMixin` from `.summarizer`
  - Import from `mas.devops.tekton`: `installOpenShiftPipelines`, `updateTektonDefinitions`, `prepareMcpiPipelinesNamespace`, `prepareInstallSecrets`, `testCLI`, `launchMcpiInstallPipeline` (added in Phase 0)
  - `logMethodCall` decorator (mirror aiservice pattern)
  - Key methods:
    - `configMcpi(self)` — prompts for MAS instance ID (using `InstanceIDFormatValidator`), MCPI channel, routing mode; mirrors `configAibroker()` from aiservice
    - `interactiveMode(self, simplified: bool, advanced: bool) -> None` — catalog, storage, SLS, DRO, ICR credentials, cert manager, MCPI config
    - `nonInteractiveMode(self) -> None` — iterates over `vars(self.args)`, handles `requiredParams`, `optionalParams`, `license_file`, `dedicated_sls`, `storage_pipeline`, `storage_accessmode`, `mongodb_namespace`, `additional_configs`, `mcpi_channel`, `approval_*`, and ignore-list keys (`accept_license`, `dev_mode`, etc.)
    - `install(self, argv: list) -> int` — main entry: parses args, detects interactive vs non-interactive via `args.mas_instance_id`, connects, runs mode, calls `slsLicenseFile()`, calls `buildCommand()` + `displayInstallSummary()`, confirms, prepares namespace and launches pipeline
  - Pipelines namespace: `mcpi-{self.getParam('mas_instance_id')}-pipelines`
  - Namespace prep: `prepareMcpiPipelinesNamespace(dynClient=..., instanceId=self.getParam('mas_instance_id'), ...)`

- [ ] **1.9** Modify `python/src/mas/cli/__main__.py`:
  - After line 76 (the `aiservice-install` block), add:
    ```python
    if function == "mcpi-install":
        from mas.cli.mcpi.install.app import McpiInstallApp

        app = McpiInstallApp()
        raise SystemExit(app.install(argv[2:]))
    ```
  - In `usage()`, add to the MAS Management Actions string (after the `aiservice-install` line if it exists, otherwise after the last install-like command):
    ```python
    + " - <ForestGreen>mas-cli mcpi-install</ForestGreen> Install Maximo Cluster Performance Insights\n"
    ```

- [ ] **1.10** Write integration tests in `python/tests/integration/mcpi_install/`:
  - Create `__init__.py` (empty with copyright header)
  - Create `conftest.py` — mirrors `aiservice_install/conftest.py`, auto-applies `mcpi-install` marker
  - Create `test_mcpi_install_app.py`:
    - `test_install_noninteractive(tmpdir)` — full non-interactive happy path:
      - Mocks: `DynamicClient`, `getNodes`, `isAirgapInstall`, `getCurrentCatalog`, `installOpenShiftPipelines`, `updateTektonDefinitions`, `prepareAiServicePipelinesNamespace`, `launchMcpiInstallPipeline`, `prepareInstallSecrets`, `testCLI`
      - Passes all required flags: `--mas-catalog-version`, `--ibm-entitlement-key`, `--mas-instance-id`, `--storage-class-rwo`, `--storage-class-rwx`, `--storage-pipeline`, `--storage-accessmode`, `--license-file`, `--contact-email`, `--contact-firstname`, `--contact-lastname`, `--mcpi-channel`, `--accept-license`, `--no-confirm`
      - Asserts `launchInstallPipeline` (or equivalent) was called once

- [ ] **1.11** Validate Phase 1:
  ```
  black python/src/mas/cli/mcpi/ python/tests/integration/mcpi_install/ --line-length 160 --check
  flake8 python/src/mas/cli/mcpi/ python/tests/integration/mcpi_install/ --max-line-length 160
  .venv/bin/pytest python/tests/integration/mcpi_install/ -v
  ```

**Relevant Context:**
- Reference app: [`python/src/mas/cli/aiservice/install/app.py`](python/src/mas/cli/aiservice/install/app.py:70)
- Reference argParser: [`python/src/mas/cli/aiservice/install/argParser.py`](python/src/mas/cli/aiservice/install/argParser.py:25)
- Reference argBuilder: [`python/src/mas/cli/aiservice/install/argBuilder.py`](python/src/mas/cli/aiservice/install/argBuilder.py:16)
- Reference summarizer: [`python/src/mas/cli/aiservice/install/summarizer.py`](python/src/mas/cli/aiservice/install/summarizer.py:18)
- Reference params: [`python/src/mas/cli/aiservice/install/params.py`](python/src/mas/cli/aiservice/install/params.py)
- Reference __init__: [`python/src/mas/cli/aiservice/install/__init__.py`](python/src/mas/cli/aiservice/install/__init__.py)
- Dispatcher: [`python/src/mas/cli/__main__.py`](python/src/mas/cli/__main__.py:72)
- Test pattern: [`python/tests/integration/aiservice_install/test_app.py`](python/tests/integration/aiservice_install/test_app.py:26)
- Test conftest: [`python/tests/integration/aiservice_install/conftest.py`](python/tests/integration/aiservice_install/conftest.py)
- `prepareAiServicePipelinesNamespace` call: [`python/src/mas/cli/aiservice/install/app.py`](python/src/mas/cli/aiservice/install/app.py:579)

---

### Phase 2 — Tekton Definitions
[x] **Status:** complete

**Intent:** Create all Tekton Jinja2 template sources needed to deploy and run the MCPI install pipeline.

**Expected Outcomes:**
- `ansible-playbook tekton/generate-tekton-tasks.yml` produces `target/tasks/mcpi.yaml`
- `ansible-playbook tekton/generate-tekton-pipelines.yml` produces `target/pipelines/mcpi-install.yaml`
- `target/pipelines/mas-install.yaml` includes the MCPI task, guarded by `when: mcpi_channel != ""`
- All generated YAML is valid Tekton syntax

**Todo:**

- [ ] **2.1** Create `tekton/src/tasks/mcpi/mcpi.yml.j2`:
  - `apiVersion: tekton.dev/v1`, `kind: Task`, `metadata.name: mas-devops-mcpi`
  - `spec.params`:
    - `{{ lookup('template', task_src_dir ~ '/common/cli-params.yml.j2') | indent(4) }}`
    - `artifactory_username`, `artifactory_token` (pre-release, empty defaults)
    - `ibm_entitlement_key` (type: string)
    - `mas_instance_id` (type: string)
    - `mcpi_channel` (type: string, description: "Catalog channel for the MCPI operator subscription")
    - `routing_mode` (type: string, default: "", description: "Routing mode for MCPI: subdomain or path")
    - `manual_route_mgmt` (type: string, default: "", description: "Disable automatic route management")
    - `mas_icr_cp` (type: string, default: "")
    - `mas_icr_cpopen` (type: string, default: "")
    - `custom_labels` (type: string, default: "", description: "Optional MAS custom labels, comma separated list of key=value pairs")
  - `spec.stepTemplate.env`:
    - `{{ lookup('template', task_src_dir ~ '/common/cli-env.yml.j2') | indent(4) }}`
    - `IBM_ENTITLEMENT_KEY: $(params.ibm_entitlement_key)`
    - `MAS_INSTANCE_ID: $(params.mas_instance_id)`
    - `MCPI_CHANNEL: $(params.mcpi_channel)`
    - `ROUTING_MODE: $(params.routing_mode)`
    - `MANUAL_ROUTE_MGMT: $(params.manual_route_mgmt)`
    - `MAS_ICR_CP: $(params.mas_icr_cp)`
    - `MAS_ICR_CPOPEN: $(params.mas_icr_cpopen)`
    - `CUSTOM_LABELS: $(params.custom_labels)`
    - `ARTIFACTORY_USERNAME: $(params.artifactory_username)`
    - `ARTIFACTORY_TOKEN: $(params.artifactory_token)`
  - `spec.steps` — single step named `mcpi`:
    - `image: quay.io/ibmmas/cli:latest`
    - `command: ["/opt/app-root/src/run-role.sh", "mcpicfg"]`
    - `workingDir: /workspace/configs`
  - `spec.workspaces`: `- name: configs` (optional: true)

- [ ] **2.2** Create `tekton/src/pipelines/taskdefs/mcpi/mcpi.yml.j2`:
  - Task fragment used in both `mas-install.yml.j2` and `mcpi-install.yml.j2`
  - `- name: mcpi`, `timeout: "0"`
  - `params`:
    - `{{ lookup('template', 'taskdefs/common/cli-params.yml.j2') | indent(4) }}`
    - `- name: devops_suite_name`, `value: mcpi`
    - `- name: artifactory_username`, `value: $(params.artifactory_username)`
    - `- name: artifactory_token`, `value: $(params.artifactory_token)`
    - `- name: ibm_entitlement_key`, `value: $(params.ibm_entitlement_key)`
    - `- name: custom_labels`, `value: $(params.custom_labels)`
    - `- name: mas_instance_id`, `value: $(params.mas_instance_id)`
    - `- name: mcpi_channel`, `value: "$(params.mcpi_channel)"`
    - `- name: routing_mode`, `value: $(params.routing_mode)`
    - `- name: manual_route_mgmt`, `value: $(params.manual_route_mgmt)`
  - `taskRef`: `name: mas-devops-mcpi`, `kind: Task`
  - `when`: `input: "$(params.mcpi_channel)"`, `operator: notin`, `values: [""]`
  - `workspaces`: `- name: configs`, `workspace: shared-configs`

- [ ] **2.3** Create `tekton/src/params/install-mcpi.yml.j2`:
  ```yaml
  # MAS Add-on Configuration - Maximo Cluster Performance Insights (MCPI)
  # -----------------------------------------------------------------------------
  - name: mcpi_channel
    type: string
    description: Default channel for IBM Maximo Cluster Performance Insights operator subscription
    default: ""
  - name: routing_mode
    type: string
    description: "Routing mode for MCPI: subdomain or path"
    default: ""
  - name: manual_route_mgmt
    type: string
    description: Disable automatic route management for MCPI
    default: ""
  ```

- [ ] **2.4** Modify `tekton/src/params/install.yml.j2`:
  - After line 844 (the end of the AI Service section: `{{ lookup('template', params_src_dir ~ '/install-aiservice.yml.j2') }}`), add:
  ```yaml

  #  MCPI Configuration
  # -----------------------------------------------------------------------------
  {{ lookup('template', params_src_dir ~ '/install-mcpi.yml.j2') }}
  ```

- [ ] **2.5** Create `tekton/src/pipelines/mcpi-install.yml.j2`:
  - Standalone install pipeline for MCPI-only installs
  - Mirror the structure of `aiservice-upgrade.yml.j2` adapted for a fresh install
  - `metadata.name: mcpi-install`
  - Workspaces: `shared-configs`, `shared-pod-templates`
  - Params:
    - `{{ lookup('template', params_src_dir ~ '/common.yml.j2') | indent(4) }}`
    - `- name: mas_instance_id` (type: string)
    - `- name: ibm_entitlement_key` (type: string)
    - `{{ lookup('template', params_src_dir ~ '/install-mcpi.yml.j2') | indent(4) }}`
  - Tasks:
    1. `pipeline-start` — `mas-devops-update-pipeline-status` (started)
    2. `ibm-catalogs` — runs after `pipeline-start`
    3. `cert-manager` — runs after `ibm-catalogs`
    4. `sls` — runs after `cert-manager`
    5. `dro` — runs after `sls`
    6. `mcpi` (via `{{ lookup('template', pipeline_src_dir ~ '/taskdefs/mcpi/mcpi.yml.j2') | indent(4) }}`) — runs after `sls`, `dro`
    7. `post-install-verify` (via `ocp-verify.yml.j2` taskdef) — runs after `mcpi`
  - `finally`: `sync-install` (`mas-devops-update-configmap`) + `pipeline-finish` (`mas-devops-update-pipeline-status`)

- [ ] **2.6** Modify `tekton/src/pipelines/mas-install.yml.j2`:
  - After the aiservice section (after the `gencfg-aiservice` block, which ends around line 464), add a numbered section:
    ```
    # 15. Install and configure MCPI (Maximo Cluster Performance Insights)
    # -------------------------------------------------------------------------
    {{ lookup('template', pipeline_src_dir ~ '/taskdefs/mcpi/mcpi.yml.j2') | indent(4) }}
      runAfter:
        - suite-config
    ```
  - Add `- mcpi` to the `post-install-verify` task's `runAfter` list (currently ends at line 479 with `- aiservice`)

- [ ] **2.7** Modify `tekton/generate-tekton-tasks.yml`:
  - Add a new block after the AI Service tasks section (after line 57):
    ```yaml
    # 3b. Generate Tasks (MCPI)
    # -------------------------------------------------------------------------
    - name: Generate Tasks (MCPI)
      ansible.builtin.template:
        src: "{{ task_src_dir }}/mcpi/{{ item }}.yml.j2"
        dest: "{{ task_target_dir }}/{{ item }}.yaml"
      with_items:
        - mcpi
    ```

- [ ] **2.8** Modify `tekton/generate-tekton-pipelines.yml`:
  - Add after `# AI Service Pipelines` block (after line 47):
    ```yaml
    # MCPI Pipelines
    - mcpi-install
    ```

- [ ] **2.9** Validate Phase 2:
  ```bash
  cd tekton
  ansible-playbook generate-tekton-tasks.yml
  ansible-playbook generate-tekton-pipelines.yml
  ```
  - Confirm `target/tasks/mcpi.yaml` generated and syntactically valid YAML
  - Confirm `target/pipelines/mcpi-install.yaml` generated
  - Confirm `target/pipelines/mas-install.yaml` contains the `mcpi` task block

**Relevant Context:**
- Task template reference: [`tekton/src/tasks/aiservice/aiservice.yml.j2`](tekton/src/tasks/aiservice/aiservice.yml.j2)
- Pipeline fragment reference: [`tekton/src/pipelines/taskdefs/aiservice/aiservice.yml.j2`](tekton/src/pipelines/taskdefs/aiservice/aiservice.yml.j2)
- Params reference: [`tekton/src/params/install-aiservice.yml.j2`](tekton/src/params/install-aiservice.yml.j2)
- Standalone pipeline reference: [`tekton/src/pipelines/aiservice-upgrade.yml.j2`](tekton/src/pipelines/aiservice-upgrade.yml.j2)
- Install pipeline: [`tekton/src/pipelines/mas-install.yml.j2`](tekton/src/pipelines/mas-install.yml.j2:436)
- Params file: [`tekton/src/params/install.yml.j2`](tekton/src/params/install.yml.j2:842)
- Generate tasks: [`tekton/generate-tekton-tasks.yml`](tekton/generate-tekton-tasks.yml:45)
- Generate pipelines: [`tekton/generate-tekton-pipelines.yml`](tekton/generate-tekton-pipelines.yml:46)

---

## Final Validation

After both phases are complete:

1. **Lint & format:**
   ```
   black python/src/mas/cli/mcpi/ python/tests/integration/mcpi_install/ --line-length 160 --check
   flake8 python/src/mas/cli/mcpi/ python/tests/integration/mcpi_install/ --max-line-length 160
   ```

2. **Tests (no regressions):**
   ```
   .venv/bin/pytest python/tests/integration/mcpi_install/ -v
   .venv/bin/pytest python/tests/ -v
   ```

3. **CLI smoke test:**
   ```
   mas-cli mcpi-install --help
   ```
   Confirm all flags display correctly.

4. **Tekton generation:**
   ```
   cd tekton
   ansible-playbook generate-tekton-tasks.yml
   ansible-playbook generate-tekton-pipelines.yml
   ```
   Confirm `target/tasks/mcpi.yaml`, `target/pipelines/mcpi-install.yaml` are generated and `target/pipelines/mas-install.yaml` includes the MCPI task.

**Success Criteria:**
- `mas-cli mcpi-install` appears in usage output
- All integration tests pass
- Tekton YAML contains `mas-devops-mcpi` task and `mcpi-install` pipeline
- MCPI task appears in `mas-install` pipeline guarded by `when: mcpi_channel != ""`
- No regressions in existing test suite
