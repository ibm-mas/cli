# MCPI Install Cleanup Plan

## Objective

Remove the over-engineered standalone `mcpi-install` command and pipeline across three repos, and replace with the minimal correct approach: a `--mcpi-channel` flag on the existing `mas-cli install` command that includes the `McpiCfg` CR via `additional-configs`, applied by the already-present `suite-config` Tekton task.

---

## Design Decisions

### Why the standalone approach was wrong

The over-built implementation treated MCPI like a standalone product (AI Service pattern) with its own:
- CLI command (`mas-cli mcpi-install`)
- Tekton pipeline (`mcpi-install.yml.j2`)
- Custom Tekton task (`mas-devops-mcpi`) running `gencfg_mcpicfg` + `suite_config`
- Ansible role (`gencfg_mcpicfg`) generating a `McpiCfg` CR
- python-devops namespace provisioning (`prepareMcpiPipelinesNamespace`, separate RBAC/PVC templates)

### The McpiCfg CR is trivially simple

`ibm/mas_devops/roles/gencfg_mcpicfg/templates/mcpicfg.yml.j2`:

```yaml
apiVersion: config.mas.ibm.com/v1
kind: McpiCfg
metadata:
  name: "{{ mas_instance_id }}-mcpi-system"
  namespace: "mas-{{ mas_instance_id }}-core"
  labels:
    mas.ibm.com/configScope: system
    mas.ibm.com/instanceId: "{{ mas_instance_id }}"
spec:
  displayName: "Maximo Cluster Performance Insights"
  config:
    enabled: true
```

There is no subscription channel, no database, no S3. The `mcpi_channel` param was never used in the CR template or anywhere in the `gencfg_mcpicfg` role — it was vestigial.

### How suite_config handles additional-configs

`run-role.sh` (line 3-5) copies `additional-configs/*` → `configs/` **before every role invocation**. The existing `suite-config` Tekton task calls `run-role.sh suite_config`. Therefore:

- If a `McpiCfg` YAML is placed in the `additional-configs` workspace, `suite_config` will automatically apply it
- The `McpiCfg` CR uses `{{ mas_instance_id }}` in name/namespace which `suite_config` resolves via `kubernetes.core.k8s template:`

### Decision: No new Tekton task needed, no `mcpi_channel` Tekton param needed

The existing `suite-config` step in `mas-install.yml.j2` is sufficient to apply the McpiCfg, as long as the CR YAML is present in `additional-configs`. No separate Tekton step, no new params file, no `mcpi_channel` pipeline parameter.

The `--mcpi-channel` CLI flag in `mas-cli install` serves as the user-facing gate. When set, the CLI:
1. Sets `self.installMcpi = True`
2. Sets `mcpi_channel` in params (for display in summary/argBuilder — the channel value itself isn't used functionally)
3. The McpiCfg YAML is bundled into the generated `additional-configs` secret when the `python-devops` `launchInstallPipeline` builds the PipelineRun

**Important**: Because `mcpi_channel` is not used in the CR, passing it as a Tekton pipeline param serves no purpose. The `--mcpi-channel` flag is needed only to:
- Signal that MCPI should be installed (gate)
- Display in the install summary
- Be reproducible via `buildCommand()`

---

## Critical Rules

- Track progress only by updating checkboxes in this plan file — do NOT use chat todo lists
- Delete files entirely rather than commenting them out
- Each phase must be independently validatable before proceeding to the next
- Do NOT add error handling or abstractions beyond the minimal patterns already used by other apps (e.g., `facilities_channel`)
- Preserve all unrelated content in files being partially edited
- When removing lines from `__main__.py`, `mascli/mas`, `.bashrc`, `pytest.ini` — verify surrounding context before editing

---

## Execution Plan

### Phase 1 — Delete over-built files

**Objective**: Remove all files that belong exclusively to the standalone mcpi-install implementation.

[ ] **1.1** Delete `python/src/mas/cli/mcpi/` (entire directory — 7 files)

[ ] **1.2** Delete `python/tests/integration/mcpi_install/` (entire directory — 3 files)

[ ] **1.3** Delete `tekton/src/pipelines/mcpi-install.yml.j2`

[ ] **1.4** Delete `tekton/src/tasks/mcpi/mcpi.yml.j2` and the `mcpi/` directory

[ ] **1.5** Delete `tekton/src/pipelines/taskdefs/mcpi/mcpi.yml.j2` and the `mcpi/` directory

[ ] **1.6** Delete `tekton/src/params/install-mcpi.yml.j2`

[ ] **1.7** Delete `ibm/mas_devops/roles/gencfg_mcpicfg/` (entire directory — 4 files across 4 subdirectories) in `ansible-devops` repo

[ ] **1.8** Delete `src/mas/devops/templates/mcpi-pipelines-pvc.yml.j2` in `python-devops` repo

[ ] **1.9** Delete `src/mas/devops/templates/mcpi-pipelines-rbac.yml.j2` in `python-devops` repo

[ ] **1.10** Delete `src/mas/devops/templates/pipelinerun-mcpi-install.yml.j2` in `python-devops` repo

[ ] **1.11** Delete `test/src/test_tekton_mcpi.py` in `python-devops` repo

**Validation**: Confirm none of the deleted paths exist. No build or test run needed yet.

---

### Phase 2 — Undo file modifications in `cli` repo

**Objective**: Revert all partial changes to shared files that were modified to support the standalone approach.

**Relevant files and what to undo:**

#### `tekton/src/params/install.yml.j2`
Remove the MCPI Configuration section (lines ~862-864):
```
#  MCPI Configuration
{{ lookup('template', params_src_dir ~ '/install-mcpi.yml.j2') }}
```

#### `tekton/src/pipelines/mas-install.yml.j2`
- Remove section 15 "Install and configure MCPI" block (~lines 464-468):
  ```
      # 15. Install and configure MCPI (Maximo Cluster Performance Insights)
      # -------------------------------------------------------------------------
      {{ lookup('template', pipeline_src_dir ~ '/taskdefs/mcpi/mcpi.yml.j2') | indent(4) }}
        runAfter:
          - suite-config
  ```
- Remove `- mcpi` from `post-install-verify` `runAfter` list (~line 484)
- Renumber section "16. Verify health..." back to "15." if sections were renumbered

#### `tekton/generate-tekton-tasks.yml`
Remove the MCPI block (~lines 45-52):
```yaml
    # 3. Generate Tasks (MCPI)
    # -------------------------------------------------------------------------
    - name: Generate Tasks (MCPI)
      ansible.builtin.template:
        src: "{{ task_src_dir }}/mcpi/{{ item }}.yml.j2"
        dest: "{{ task_target_dir }}/{{ item }}.yaml"
      with_items:
        - mcpi
```
Also renumber subsequent sections (AI Service was originally section 3, not 4).

#### `tekton/generate-tekton-pipelines.yml`
Remove the MCPI pipelines entry (~lines 46-47):
```yaml
      # MCPI Pipelines
      - mcpi-install
```

#### `python/src/mas/cli/__main__.py`
Remove:
- The usage text line: `" - <ForestGreen>mas-cli mcpi-install</ForestGreen> Install Maximo Cluster Performance Insights\n"`
- The dispatcher block (~lines 78-82):
  ```python
  if function == "mcpi-install":
      from mas.cli.mcpi.install.app import McpiInstallApp
      app = McpiInstallApp()
      raise SystemExit(app.install(argv[2:]))
  ```

#### `pytest.ini`
Remove the two MCPI markers (~lines 12-13):
```
    mcpi-install: MCPI installation tests (mas-cli mcpi-install)
    mcpi_install: MCPI installation tests (mas-cli mcpi-install)
```

#### `image/cli/mascli/mas`
Remove the `mcpi-install` case block (~lines 290-298):
```bash
  mcpi-install)
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" >> $LOGFILE
    echo "!! mcpi-install                                                              !!" >> $LOGFILE
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" >> $LOGFILE
    # Take the first parameter off (it will be "mcpi-install")
    shift
    # Run the new Python-based mcpi-install
    mas-cli mcpi-install "$@"
    ;;
```

#### `image/cli/app-root/src/.bashrc`
Remove the MCPI Management section (~lines 51-52):
```
echo "MCPI Management:"
echo "  - ${TEXT_BOLD}${COLOR_GREEN}mas mcpi-install${TEXT_RESET} to install MCPI into an existing MAS instance"
```

#### `python-devops` repo: `src/mas/devops/tekton.py`
Remove:
- `prepareMcpiPipelinesNamespace()` function (~lines 846-920)
- `launchMcpiInstallPipeline()` function (~lines 1610-1628)

**Validation**: After all edits, run a grep to confirm no remaining `mcpi-install` or `mcpi_channel` references in shared files. Tekton generation playbooks should parse cleanly (no missing template references).

---

### Phase 3 — Add `--mcpi-channel` to `mas-cli install`

**Objective**: Implement MCPI as a standard MAS app option in the existing install command, following the same pattern as `facilities_channel`.

#### `python/src/mas/cli/install/argParser.py`
In the "MAS Applications" argument group (after `--aiservice-channel`, before the `# Arcgis` section), add:
```python
masAppsArgGroup.add_argument(
    "--mcpi-channel",
    required=False,
    help="Subscription channel for Maximo Cluster Performance Insights",
)
```

#### `python/src/mas/cli/install/app.py` — `nonInteractiveMode()` init block
At lines ~2204-2216, `nonInteractiveMode()` initializes all install booleans to `False`. Add `self.installMcpi = False` to this block alongside the other flags.

#### `python/src/mas/cli/install/app.py` — `nonInteractiveMode()` key dispatch
After the `elif key == "aiservice_channel":` block (around line 2414), add:
```python
elif key == "mcpi_channel":
    if value is not None and value != "":
        self.setParam("mcpi_channel", value)
        self.installMcpi = True
```

#### `python/src/mas/cli/install/app.py` — `configApps()`
After the AI Service block (end of method, around line 1356), add a simple unconditional prompt:
```python
self.installMcpi = self.yesOrNo("Install Maximo Cluster Performance Insights (MCPI)")
if self.installMcpi:
    self.configAppChannel("mcpi")  # OR: self.promptForString(...)
```

> **Note**: `McpiCfg` has no subscription channel field in the CR, but we still prompt for a channel to match the install pattern and for future use. If `configAppChannel` requires an entry in the compatibility matrix, use `promptForString("MCPI subscription channel", "mcpi_channel")` instead.

#### `python/src/mas/cli/install/params.py`
Add `"mcpi_channel"` to `optionalParams` list (near the app channels section).

#### `python/src/mas/cli/install/argBuilder.py` — `buildCommand()`
After the `if self.installAIService:` block (~line 285), add:
```python
if self.installMcpi:
    command += f"  --mcpi-channel \"{self.getParam('mcpi_channel')}\"{newline}"
```

#### `python/src/mas/cli/install/summarizer.py`
Add an `mcpiSummary()` method following the pattern of `facilitiesSummary()` or `assistSummary()`:
```python
def mcpiSummary(self) -> None:
    if self.installMcpi:
        self.printSummary("MCPI", self.getParam("mcpi_channel"))
    else:
        self.printSummary("MCPI", "Do Not Install")
```
Call `self.mcpiSummary()` in the appropriate place in the summary output method.

**Validation**: Run `python -m pytest python/tests -m unit -k install` to confirm existing install tests pass. Verify `--help` output for `mas-cli install` shows `--mcpi-channel`.

---

### Phase 4 — Final validation

**Objective**: Confirm the full state of all three repos is clean and correct.

[ ] **4.1** In `cli` repo: run `grep -r "mcpi-install\|McpiInstall\|mcpi_channel\|gencfg_mcpicfg\|launchMcpiInstall\|prepareMcpiPipelines" python/ tekton/ image/ pytest.ini` — expect zero results (except `mcpi_channel` in the new optionalParams and argParser additions)

[ ] **4.2** In `cli` repo: run `ansible-playbook tekton/generate-tekton-tasks.yml --check` — expect success (no missing template errors)

[ ] **4.3** In `cli` repo: run `ansible-playbook tekton/generate-tekton-pipelines.yml --check` — expect success

[ ] **4.4** In `cli` repo: run `.venv/bin/pytest python/tests -m unit` — all unit tests pass

[ ] **4.5** In `ansible-devops` repo: confirm `ibm/mas_devops/roles/gencfg_mcpicfg/` directory is gone

[ ] **4.6** In `python-devops` repo: run `.venv/bin/pytest test/` — all tests pass (mcpi test file removed, no broken imports)

---

## Final Validation

### Success criteria

1. `grep -r "mcpi-install" cli/python/ cli/tekton/ cli/image/` returns zero matches
2. `ansible-playbook tekton/generate-tekton-tasks.yml` completes without errors
3. `ansible-playbook tekton/generate-tekton-pipelines.yml` completes without errors
4. `mas-cli install --help` shows `--mcpi-channel` in the MAS Applications group
5. `mas-cli mcpi-install` returns "command not found" or usage error (no longer a valid subcommand)
6. All unit tests in `cli` repo pass
7. All tests in `python-devops` pass
8. `gencfg_mcpicfg` role no longer exists in `ansible-devops`

### Troubleshooting

- If `generate-tekton-tasks.yml` fails: check that `tekton/src/tasks/mcpi/` directory was fully removed and no `with_items: - mcpi` block remains
- If `generate-tekton-pipelines.yml` fails: check that `tekton/src/pipelines/mcpi-install.yml.j2` was removed and `all_pipelines` list no longer contains `mcpi-install`
- If Python import fails: ensure `python/src/mas/cli/mcpi/` directory was fully removed and `__main__.py` dispatcher was cleaned up
- If `installMcpi` attribute error: ensure `self.installMcpi = False` default is set in `InstallApp.__init__()` alongside other `self.installXxx = False` defaults
