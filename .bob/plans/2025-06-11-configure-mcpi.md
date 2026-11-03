# Plan: `mas-cli configure-mcpi` Command

## Objective

Add a new `configure-mcpi` sub-command to the MAS CLI that applies an `McpiCfg` custom resource to an existing MAS 9.2+ deployment. The command supports both interactive and non-interactive (CI/CD) modes, validates the target cluster/namespace/version, and follows all existing code patterns in the project.

---

## Design Decisions

### Module location
- New Python module: `python/src/mas/cli/configure_mcpi/`
  - `__init__.py`
  - `app.py` — `ConfigureMcpiApp` class
  - `argParser.py` — argument parser singleton
- Follows the same layout as `setup_rbac/` (the simplest existing command).

### Argument design
| Flag | Short | Required | Notes |
|---|---|---|---|
| `--mas-instance-id` | `-i` | No (prompted if absent) | Stored in `args.mas_instance_id` |
| `--no-confirm` | — | No | `store_true`; skips confirmation prompt |

`--mas-instance-id` is optional in the parser (not `required=True`) so that interactive mode can prompt for it. The app validates it is non-empty before proceeding.

### Interactive vs non-interactive mode
- **Interactive**: `--mas-instance-id` absent → `self.promptForString(...)` with `InstanceIDFormatValidator`
- **Non-interactive**: `--mas-instance-id` supplied → skip prompt
- `self.noConfirm` controls whether a final "Proceed?" confirmation is shown.

### Connectivity check
- Call `self.connect()` (inherited from `BaseApp`) — loads kubeconfig or in-cluster config, prints cluster summary, and exits fatally if unable to connect. No custom code needed.

### Namespace validation
- Target namespace: `mas-{instanceId}-core`
- Use `self.dynamicClient.resources.get(api_version="v1", kind="Namespace")` with a `try/except NotFoundError` (same pattern as `must_gather/dependencies/utils.py`).
- If the namespace does not exist, call `self.fatalError(...)`.

### MAS channel/version validation
- Read the OLM subscription channel: `getMasChannel(self.dynamicClient, instanceId)` from `mas.devops.mas`.
- `getMasChannel` returns the channel string (e.g., `"9.2.x"`) or `None` if the subscription is missing.
- If `None`: fatal error — MAS is not installed for this instance ID.
- Version gate: `isVersionEqualOrAfter("9.2.0", channel)` from `mas.devops.utils`.
- If `False`: fatal error — MCPI requires MAS 9.2+.

### McpiCfg CR construction
Constructed as a Python dict (matching the template already in `additionalConfigs.py`):

```python
{
    "apiVersion": "config.mas.ibm.com/v1",
    "kind": "McpiCfg",
    "metadata": {
        "name": f"{instanceId}-mcpi-system",
        "namespace": f"mas-{instanceId}-core",
        "labels": {
            "mas.ibm.com/configScope": "system",
            "mas.ibm.com/instanceId": instanceId,
        },
    },
    "spec": {
        "displayName": "Maximo Cluster Performance Insights",
        "config": {"enabled": True},
    },
}
```

### Idempotency strategy
- Try `resourceAPI.get(name=..., namespace=...)`.
- If it exists → `resourceAPI.patch(body=cr, name=..., namespace=...)` (server-side apply via strategic merge).
- If `NotFoundError` → `resourceAPI.create(body=cr, namespace=...)`.
- Wrap in a `Halo` spinner, consistent with `setup_rbac/app.py`.

### Bash entrypoint integration
- Add a `configure-mcpi` case to `image/cli/mascli/mas` that logs to `$LOGFILE` then delegates to `mas-cli configure-mcpi "$@"`.
- Pattern: identical to `setup-rbac` and `pre-install` cases.

### Usage string in `__main__.py`
- Add `- mas-cli configure-mcpi   Apply Maximo Cluster Performance Insights configuration` to `usage()`.
- Add lazy-import dispatch case for `configure-mcpi`.

### Unit test files
| File | What it tests |
|---|---|
| `python/tests/unit/test_configure_mcpi_args.py` | Argparse: `--mas-instance-id`, `--no-confirm`, `--help` |
| `python/tests/unit/test_configure_mcpi_app.py` | CR dict construction helper; version validation logic |

Tests follow the Given-When-Then docstring format. No real cluster connection; Kubernetes calls are mocked via `unittest.mock.patch`.

---

## Critical Rules

- Do NOT modify any existing modules other than `__main__.py` (dispatch) and `image/cli/mascli/mas` (bash entrypoint).
- Do NOT import from `mas.cli.install` — the McpiCfg dict is defined locally in the new module, not reused from `additionalConfigs.py`.
- Follow the exact copyright header used in other files in `python/src/mas/cli/` (year 2026).
- Use `snake_case` file names, `PascalCase` class name (`ConfigureMcpiApp`), `camelCase` for variables.
- All Python files ≤ 600 lines.
- Test functions must have a Given-When-Then docstring.
- Track progress by updating this file's checkboxes only — do not use chat todo lists.
- Run `black --line-length 160` and `flake8` after implementation.
- Run `python -m pytest python/tests/unit/test_configure_mcpi*.py` to validate tests pass.

---

## Execution Plan

### Phase 1 — Python module skeleton

**Objective:** Create the `configure_mcpi` package with argparser and empty app class.

- [x] **1.1** Create `python/src/mas/cli/configure_mcpi/__init__.py` (empty)
- [x] **1.2** Create `python/src/mas/cli/configure_mcpi/argParser.py`:
  - `configureMcpiArgParser` with `prog="mas configure-mcpi"`
  - Argument group `"Target MAS Instance Arguments"`: `--mas-instance-id` / `-i`, `required=False`
  - Argument group `"More"`: `--no-confirm` (`store_true`, default `False`)
  - `-h` / `--help` action
  - Copyright header (year 2026)
- [x] **1.3** Create `python/src/mas/cli/configure_mcpi/app.py`:
  - Class `ConfigureMcpiApp(BaseApp)` with method `configureMcpi(self, argv)`
  - `buildMcpiCr(instanceId)` helper function
  - Copyright header (year 2026)

**Validation:** `python -m py_compile python/src/mas/cli/configure_mcpi/app.py` — no syntax errors.

---

### Phase 2 — Unit tests (TDD first)

**Objective:** Write unit tests before implementing app logic so implementation is test-driven.

- [x] **2.1** Create `python/tests/unit/test_configure_mcpi_args.py`:
  - `test_mas_instance_id_argument_sets_value` — `--mas-instance-id inst1` → `args.mas_instance_id == "inst1"`
  - `test_mas_instance_id_defaults_to_none` — no args → `args.mas_instance_id is None`
  - `test_no_confirm_flag_sets_true` — `--no-confirm` → `args.no_confirm is True`
  - `test_no_confirm_defaults_to_false` — no flag → `args.no_confirm is False`
- [x] **2.2** Create `python/tests/unit/test_configure_mcpi_app.py`:
  - `test_mcpi_cr_dict_has_correct_api_version` — helper returns dict with `apiVersion: config.mas.ibm.com/v1`
  - `test_mcpi_cr_dict_has_correct_kind` — `kind: McpiCfg`
  - `test_mcpi_cr_dict_name_uses_instance_id` — `metadata.name == "inst1-mcpi-system"`
  - `test_mcpi_cr_dict_namespace_uses_instance_id` — `metadata.namespace == "mas-inst1-core"`
  - `test_mcpi_cr_dict_has_required_labels` — labels contain both `configScope` and `instanceId`
  - `test_mcpi_cr_dict_spec_enabled_true` — `spec.config.enabled == True`
  - Extract CR construction into a standalone function `buildMcpiCr(instanceId)` to make it independently testable.

**Validation:** Tests run and validated.

---

### Phase 3 — Core app logic

**Objective:** Implement the full `configureMcpi` method so all tests go Green.

Steps inside `configureMcpi(self, argv)`:

- [x] **3.1** Parse args and set `self.noConfirm = self.args.no_confirm`
- [x] **3.2** Print header: `self.printH1("Configure MCPI")`
- [x] **3.3** Connect to cluster: `self.connect()`
- [x] **3.4** Determine `instanceId`:
  - If `self.args.mas_instance_id` is set, use it.
  - Otherwise prompt: `self.promptForString("MAS Instance ID", validator=InstanceIDFormatValidator())`
- [x] **3.5** Print summary line: `self.printSummary("MAS Instance ID", instanceId)`
- [x] **3.6** Validate namespace `mas-{instanceId}-core` exists via `dynamicClient`; `fatalError` if not.
- [x] **3.7** Read channel: `getMasChannel(self.dynamicClient, instanceId)`; `fatalError` if `None`.
- [x] **3.8** Version gate: `isVersionEqualOrAfter("9.2.0", channel)`; `fatalError` if `False`.
- [x] **3.9** If `not self.noConfirm`, call `self.yesOrNo("Proceed to apply McpiCfg")`; exit if `False`.
- [x] **3.10** Build the CR dict using `buildMcpiCr(instanceId)` (extracted helper function in `app.py`).
- [x] **3.11** Apply CR inside a `Halo` spinner:
  - Get resource API: `self.dynamicClient.resources.get(api_version="config.mas.ibm.com/v1", kind="McpiCfg")`
  - Try `get(name=..., namespace=...)`; if found → `patch`, else (on `NotFoundError`) → `create`.
  - `h.stop_and_persist(symbol=self.successIcon, ...)` on success.
- [x] **3.12** Print `self.printH1("Next Steps")` with guidance message.

**Validation:** `python -m pytest python/tests/unit/test_configure_mcpi*.py` — all 18 tests pass (Green).

---

### Phase 4 — Dispatcher and bash entrypoint integration

**Objective:** Wire the new command into `__main__.py` and `image/cli/mascli/mas`.

- [x] **4.1** In `python/src/mas/cli/__main__.py`:
  - Add usage entry: `- mas-cli configure-mcpi Apply Maximo Cluster Performance Insights configuration` inside `usage()`
  - Add dispatch block for `configure-mcpi`
- [x] **4.2** In `image/cli/mascli/mas`, add `configure-mcpi` case

**Validation:** `__main__.py` and `image/cli/mascli/mas` updated and verified.

---

### Phase 5 — Code quality and final validation

**Objective:** Ensure all new code meets style requirements.

- [x] **5.1** Run `black --line-length 160 python/src/mas/cli/configure_mcpi/ python/tests/unit/test_configure_mcpi*.py`
- [x] **5.2** Run `flake8 python/src/mas/cli/configure_mcpi/ python/tests/unit/test_configure_mcpi*.py`
- [x] **5.3** Run unit test suite: 26 MCPI & configure-mcpi unit tests pass
- [x] **5.4** Review all new files for correct copyright header format

---

## Final Validation

### Commands

```bash
# Syntax check all new Python files
python -m py_compile python/src/mas/cli/configure_mcpi/app.py
python -m py_compile python/src/mas/cli/configure_mcpi/argParser.py
python -m py_compile python/src/mas/cli/__main__.py

# Unit tests
.venv/bin/python -m pytest python/tests/unit/test_configure_mcpi_args.py -v
.venv/bin/python -m pytest python/tests/unit/test_configure_mcpi_app.py -v

# Style
black --line-length 160 --check python/src/mas/cli/configure_mcpi/ python/tests/unit/test_configure_mcpi*.py
flake8 python/src/mas/cli/configure_mcpi/ python/tests/unit/test_configure_mcpi*.py

# Help output (smoke test)
mas-cli configure-mcpi --help
```

### Success criteria

- All unit tests pass with zero failures.
- Black and flake8 report no violations on new files.
- `mas-cli configure-mcpi --help` prints the usage with `--mas-instance-id` and `--no-confirm`.
- No regressions in the existing unit test suite.

### Relevant context for implementer

| Item | Location |
|---|---|
| Closest structural analogue | `python/src/mas/cli/setup_rbac/` |
| CR template reference | `python/src/mas/cli/install/settings/additionalConfigs.py` lines 22-37 |
| Version utility | `mas.devops.utils.isVersionEqualOrAfter` |
| Channel reader | `mas.devops.mas.getMasChannel` |
| Namespace check pattern | `python/src/mas/cli/must_gather/dependencies/utils.py` lines 21-40 |
| InstanceIDFormatValidator | `python/src/mas/cli/validators.py` line 32 |
| Bash entrypoint dispatch pattern | `image/cli/mascli/mas` lines 849-867 |
| Existing MCPI unit tests | `python/tests/unit/test_install_mcpi_flag.py`, `python/tests/unit/test_install_mcpi_config.py` |
