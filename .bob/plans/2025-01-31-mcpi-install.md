# Plan: MCPI Install — Architecture, Design & Implementation Record

## Objective

Enable users to install **Maximo Cluster Performance Insights (MCPI)** via the existing `mas-cli install` command by adding a `--install-mcpi` flag. No standalone command, no new pipeline, no new Ansible role.

---

## Repos Involved

| Repo | Status | What changed |
|------|--------|-------------|
| **`cli`** | ✅ Done | `--install-mcpi` flag added to `install` command, generates the McpiCfg CR |
| **`ansible-devops`** | ✅ No change needed | No MCPI-specific role required |
| **`python-devops`** | ✅ No change needed | `launchInstallPipeline()` already mounts the `pipeline-additional-configs` secret into `mas-install` |

---

## Architecture

### How MCPI fits into the MAS install model

MCPI is a MAS system-level add-on. Its runtime is managed entirely by the existing `ibm-mas` operator through a `McpiCfg` custom resource. There is no separate MCPI operator subscription to install — the `<instanceId>-entitymgr-mcpicfg` deployment is created by the Suite operator (owned by the `Suite` CR) and is already present in `mas-<instanceId>-core` after MAS core is installed (MAS 9.2.1+). The CLI never installs or checks for it.

```
mas-cli install --install-mcpi
       │  CLI adds mcpi-system.yaml (McpiCfg) to Secret/pipeline-additional-configs
       ▼
pipelinerun-install.yml.j2  →  mas-<instanceId>-pipelines
       │
       ▼  (mas-install Tekton pipeline)
  suite-install  →  suite-verify  →  suite-config
       │                                   │
       │  run-role.sh copies               │  suite_config role:
       │  additional-configs/* → configs/  │  applies all *.yml|*.yaml in /workspace/configs/
       │                                   ▼
       │                     McpiCfg CR applied to mas-<instanceId>-core
       │                                   │
       │                                   ▼
       │                     <id>-entitymgr-mcpicfg (already running) reconciles CR
       │                     → deploys MCPI viewer, scripts, routes, certs
```

### The McpiCfg CR

The CR that enables MCPI is trivially simple — it has no subscription channel, no database, no S3, no custom configuration:

```yaml
apiVersion: config.mas.ibm.com/v1
kind: McpiCfg
metadata:
  name: "<instanceId>-mcpi-system"
  namespace: "mas-<instanceId>-core"
  labels:
    mas.ibm.com/configScope: system
    mas.ibm.com/instanceId: "<instanceId>"
spec:
  displayName: "Maximo Cluster Performance Insights"
  config:
    enabled: true
```

The CLI generates this file (`mcpi-system.yaml`, constant `MCPI_CONFIG_TEMPLATE` in `additionalConfigs.py`) when MCPI is enabled. The existing `suite-config` Tekton task applies it via `kubernetes.core.k8s template:` which resolves `{{ mas_instance_id }}` at apply time.

### Why the `additional-configs` workspace and not a new Tekton task

`run-role.sh` (the entrypoint for every Tekton task step) copies `additional-configs/*` → `configs/` **before every role invocation**:

```bash
# image/cli/app-root/src/run-role.sh
if [ -e "/workspace/additional-configs" ]; then
  cp /workspace/additional-configs/* /workspace/configs/
fi
```

`suite-install` declares the `additional-configs` workspace, so its run copies the files into the shared `configs` workspace; `suite_config` then applies them. No new Tekton step is needed. (`suite-config` itself does not declare that workspace — this copy-through path is read from the code and still needs end-to-end verification, see Open Items.)

### What `--install-mcpi` does

`--install-mcpi` is a plain on/off flag (`store_true`, like `--skip-grafana-install`). When set, or when the user answers "yes" to the interactive prompt, `self.installMcpi = True` and the CLI injects the `McpiCfg` resource into the `pipeline-additional-configs` secret (see [`additionalConfigs.py`](python/src/mas/cli/install/settings/additionalConfigs.py)). `suite-install` copies it into the shared configs workspace and `suite-config` applies it. A user-supplied `mcpi-system.yaml` in `--additional-configs` takes precedence.

MCPI requires MAS 9.2+. Non-interactive mode fails fast if `--install-mcpi` is combined with an older `--mas-channel`; interactive mode only offers the prompt for 9.2+.

### Why no new Ansible role (`gencfg_mcpicfg` removed)

The originally-added `gencfg_mcpicfg` role in `ansible-devops` generated the `McpiCfg` YAML from a Jinja template. This was unnecessary because:

- The CR is static, so the CLI embeds it as a template string
- `suite_config` already applies Jinja-templated YAML files from the workspace using `kubernetes.core.k8s template:`
- No new Ansible collection build or CLI image rebuild is required

---

## Design Decisions

### Why not a standalone `mcpi-install` command (like `aiservice-install`)?

AI Service is a genuinely separate product with its own operator, namespace, Db2, S3 and pipeline namespace. MCPI has none of that. It is a config-scope CR applied to the existing MAS core namespace, handled by the entity manager (`<id>-entitymgr-mcpicfg`) that the `ibm-mas` operator already deploys as part of the Suite. The CLI never installs the entity manager.

### Why a boolean flag and not `--mcpi-channel`?

`McpiCfg` has no channel field and there is no MCPI subscription, so a channel value would be meaningless. A boolean follows `--skip-grafana-install` / `--install-minio`.

### Pipeline wiring

No Tekton or python-devops change. The CR travels via the existing `pipeline-additional-configs` secret.

---

## Implementation — What Changed

All in the `cli` repo:

| File | Change |
|------|--------|
| [`argParser.py`](python/src/mas/cli/install/argParser.py) | `--install-mcpi` (`store_true`) in the MAS Applications group |
| [`app.py`](python/src/mas/cli/install/app.py) | `installMcpi` default; `install_mcpi` dispatch; interactive yes/no prompt (9.2+ only); fatal error for MAS < 9.2 |
| [`argBuilder.py`](python/src/mas/cli/install/argBuilder.py) | Emits `--install-mcpi` in the generated command |
| [`summarizer.py`](python/src/mas/cli/install/summarizer.py) | MCPI line in the install summary |
| [`additionalConfigs.py`](python/src/mas/cli/install/settings/additionalConfigs.py) | Injects `mcpi-system.yaml` (`McpiCfg`) into the secret |
| `python/tests/unit/test_install_mcpi_*.py` | Unit tests for the flag and the injection |

---

## What Was Removed (Cleanup)

The initial implementation built a full standalone command following the AI Service pattern. Everything below was removed:

### `cli` repo

| Removed | Reason |
|---------|--------|
| `python/src/mas/cli/mcpi/` (entire module) | Standalone `mcpi-install` command — wrong pattern |
| `python/tests/integration/mcpi_install/` | Tests for the removed standalone command |
| `tekton/src/pipelines/mcpi-install.yml.j2` | Standalone pipeline — not needed |
| `tekton/src/tasks/mcpi/mcpi.yml.j2` | Custom task running `gencfg_mcpicfg` + `suite_config` |
| `tekton/src/pipelines/taskdefs/mcpi/mcpi.yml.j2` | Pipeline fragment for the removed task |
| `tekton/src/params/install-mcpi.yml.j2` | Params file included in `install.yml.j2` |
| `mcpi-install` block in `tekton/generate-tekton-tasks.yml` | No task to generate |
| `mcpi-install` entry in `tekton/generate-tekton-pipelines.yml` | No standalone pipeline to generate |
| MCPI include in `tekton/src/params/install.yml.j2` | Removed MCPI params from pipeline |
| MCPI task + `runAfter` in `tekton/src/pipelines/mas-install.yml.j2` | Suite-config handles it |
| `mcpi-install` case in `image/cli/mascli/mas` | No standalone command |
| MCPI entry in `image/cli/app-root/src/.bashrc` | No standalone command |
| `mcpi-install` dispatcher in `python/src/mas/cli/__main__.py` | No standalone command |
| `mcpi-install` usage line in `python/src/mas/cli/__main__.py` | No standalone command |
| `mcpi-install` / `mcpi_install` markers in `pytest.ini` | No standalone tests |

### `ansible-devops` repo

| Removed | Reason |
|---------|--------|
| `ibm/mas_devops/roles/gencfg_mcpicfg/` (4 files) | CR is static — no dynamic generation needed |

### `python-devops` repo

| Removed | Reason |
|---------|--------|
| `src/mas/devops/templates/mcpi-pipelines-pvc.yml.j2` | No MCPI-specific pipeline namespace |
| `src/mas/devops/templates/mcpi-pipelines-rbac.yml.j2` | No MCPI-specific pipeline namespace |
| `src/mas/devops/templates/pipelinerun-mcpi-install.yml.j2` | No standalone MCPI pipeline |
| `prepareMcpiPipelinesNamespace()` in `tekton.py` | No MCPI-specific pipeline namespace |
| `launchMcpiInstallPipeline()` in `tekton.py` | `launchInstallPipeline()` drives `mas-install` |
| `test/src/test_tekton_mcpi.py` | Tests for the removed functions |

---

## How to Install MCPI

### Non-interactive

```bash
mas-cli install ... --mas-channel 9.2.x --install-mcpi
```

### Interactive

Answer `Yes` to "Install Maximo Cluster Performance Insights (MCPI)" in the Application Selection step (only shown for MAS 9.2+).

---

## Open Items

- End-to-end verification on a fresh instance ID (not `visionary`, which already has a manually applied `visionary-mcpi-system`) using `--install-mcpi`: confirm `suite-install` copies `mcpi-system.yaml` into the shared configs workspace and `suite-config` applies it (`oc get mcpicfg -n mas-<id>-core`).
- `configCatalog()` crashes when the installed catalog ID cannot be parsed from its display name (unrelated to MCPI).
