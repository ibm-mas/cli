# Objective

Update the pipeline-start Slack notification so the first Slack message sent when a Tekton pipeline begins includes the real OpenShift console URL (e.g. `https://console-openshift-console.apps.*.cp.fyre.ibm.com`).

# Design Decisions

- **`--cluster-url` is a no-op today.** `update-pipeline-status.py` already passes `--cluster-url` to `mas-devops-notify-slack`, but the notifier uses `parse_known_args` and silently ignores unknown arguments. The cluster URL never reaches the Slack message.

- **The message is built in `python-devops`.** `notifyPipelineStart()` in [`python-devops/bin/mas-devops-notify-slack:100-162`](../python-devops/bin/mas-devops-notify-slack) builds the message from `instanceId`, `pipelineName`, and `toolchainLink` only. To show the cluster URL it must be added to the message block here.

- **The right env var pattern is `OCP_CONSOLE_URL`.** This is already the pattern used by `notifyProvisionFyre` and `notifyProvisionRoks` in the same file (lines 42, 76). Adding `OCP_CONSOLE_URL` support to `notifyPipelineStart` is consistent and requires no new CLI args.

- **The URL is resolved via `oc` in `update-pipeline-status.py`.** The `quay.io/ibmmas/cli` image has `oc` available and the task pod runs with an in-cluster service account token. `subprocess` is already imported and used in the script. The existing bash infrastructure in [`image/cli/mascli/functions/internal/connect`](image/cli/mascli/functions/internal/connect) uses this exact command three times:
  ```bash
  oc -n openshift-console get route console -o=jsonpath='{.spec.host}'
  ```

- **RBAC gap.** The pipeline service account (`mas-{id}-install-pipeline`) does not currently have `GET routes` in `openshift-console`. A new RBAC file is needed following the pattern of all other per-namespace pipeline RBAC files (e.g. [`rbac/install/pipeline/openshift-monitoring.yaml`](rbac/install/pipeline/openshift-monitoring.yaml)).

- **Scope.** Only `pipeline-start` message is changed. Completion, failure, and MongoDB paths are untouched.

# Critical Rules

- Do not add new CLI arguments to `mas-devops-notify-slack` — use `OCP_CONSOLE_URL` env var consistent with existing pattern.
- Do not add new Tekton pipeline parameters or secrets.
- The RBAC file must follow the exact naming and structure pattern of existing files under `rbac/install/pipeline/`.
- Every changed line must directly support adding the real console URL to the start notification.
- Track progress only in this plan document, not in chat todo lists.

# Execution Plan

## Phase 1: Add cluster URL to the pipeline-start Slack message (python-devops)

Launch a subtask in implementation mode to complete this phase, instructing it to read this plan file first.

- [ ] **1.1** In `notifyPipelineStart()` in `python-devops/bin/mas-devops-notify-slack` (around line 127):
  - Read `OCP_CONSOLE_URL` from the environment (`os.getenv("OCP_CONSOLE_URL", "")`).
  - If non-empty, append it as a line in the existing section block alongside `instanceInfo` and `toolchainLink`.
- [ ] **1.2** Confirm no other actions (`pipeline-complete`, `ansible-start`, etc.) are changed.
- [ ] **1.3** Run the python-devops test suite: `pytest test/ -v` in the python-devops repo.

## Phase 2: Add RBAC for pipeline service account to read the console route (cli)

Launch a subtask in implementation mode to complete this phase, instructing it to read this plan file first.

- [ ] **2.1** Create `rbac/install/pipeline/openshift-console.yaml` in the cli repo.
  - Grant `GET` on `routes` in `openshift-console` namespace to `mas-{{ mas_instance_id }}-install-pipeline`.
  - Mirror the structure of [`rbac/install/pipeline/openshift-monitoring.yaml`](rbac/install/pipeline/openshift-monitoring.yaml).
- [ ] **2.2** Register the new file in [`rbac/install/kustomization.yaml`](rbac/install/kustomization.yaml) under the pipeline RBAC block, in alphabetical order between `openshift-config.yaml` and `openshift-ingress-operator.yaml`.
- [ ] **2.3** Validate YAML syntax: `python3 -c "import yaml; yaml.safe_load(open('rbac/install/pipeline/openshift-console.yaml'))"`.

## Phase 3: Resolve the console URL and pass it to the notifier (cli)

Launch a subtask in implementation mode to complete this phase, instructing it to read this plan file first.

- [ ] **3.1** In `send_slack_notification()` in [`update-pipeline-status.py`](image/cli/app-root/src/update-pipeline-status.py):
  - Add a `getConsoleURL()` helper function (before `send_slack_notification`) that:
    - Runs `oc -n openshift-console get route console -o=jsonpath='{.spec.host}'` via `subprocess.run()` (already imported).
    - Returns `f"https://{result.stdout.strip()}"` on success.
    - Returns `""` silently on any failure (non-zero rc, exception, or empty output).
  - In the `pipeline-start` branch, replace the existing `--cluster-url` / `cluster_url` args (lines 56-57) with setting `env["OCP_CONSOLE_URL"] = getConsoleURL()` on the `subprocess.run()` call, passing the enriched environment.
- [ ] **3.2** Remove the now-unused `CLUSTER_URL` env var from [`update-pipeline-status.yml.j2`](tekton/src/tasks/framework/update-pipeline-status.yml.j2) (lines 60-61).
- [ ] **3.3** Confirm `pipeline-complete` branch and MongoDB code paths are untouched.
- [ ] **3.4** Run: `flake8 image/cli/app-root/src/update-pipeline-status.py`.

## Phase 4: Final verification

Launch a subtask in implementation mode to complete this phase, instructing it to read this plan file first.

- [ ] **4.1** Review the final diff for minimality — only these files should change:
  - `python-devops/bin/mas-devops-notify-slack`
  - `cli/rbac/install/pipeline/openshift-console.yaml` (new)
  - `cli/rbac/install/kustomization.yaml`
  - `cli/image/cli/app-root/src/update-pipeline-status.py`
  - `cli/tekton/src/tasks/framework/update-pipeline-status.yml.j2`
- [ ] **4.2** Update this plan file — mark all completed items with `[x]`.

# Final Validation

- `flake8 image/cli/app-root/src/update-pipeline-status.py`
- `python3 -c "import yaml; yaml.safe_load(open('rbac/install/pipeline/openshift-console.yaml'))"`
- `pytest test/ -v` in python-devops repo

Success criteria:

- `notifyPipelineStart` renders `OCP_CONSOLE_URL` in the Slack message when the env var is set.
- `update-pipeline-status.py` resolves the console URL via `oc` and passes it as `OCP_CONSOLE_URL` in the subprocess environment.
- Pipeline SA has `GET routes` permission in `openshift-console`.
- No new Tekton parameters, CLI args, or secrets introduced.
- All validation passes.
