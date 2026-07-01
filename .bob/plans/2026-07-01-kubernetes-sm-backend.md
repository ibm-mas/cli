# Objective

Extend the GitOps secrets-manager abstraction so [`gitops_utils`](image/cli/mascli/functions/gitops_utils) and its consumers can support a new `kubernetes` backend alongside the existing AWS backend, while removing any remaining direct AWS Secrets Manager assumptions from the MAS CLI functions and GitOps workspace.

# Design Decisions

- Treat [`sm_login()`](image/cli/mascli/functions/gitops_utils:245) and the other [`sm_`](image/cli/mascli/functions/gitops_utils:245) helpers in [`gitops_utils`](image/cli/mascli/functions/gitops_utils) as the single abstraction layer for secret CRUD and lookup behavior.
- Preserve the current AWS behavior as the default path; add `kubernetes` branches rather than refactoring unrelated call sites.
- For the new backend, model secret CRUD with `oc` or `kubectl` against Kubernetes `Secret` objects and keep authentication minimal: [`sm_login()`](image/cli/mascli/functions/gitops_utils:245) should validate cluster access only, not perform cloud credential setup.
- Align Kubernetes secret naming with AVP’s Kubernetes path format used by templates such as [`ibm-dro.yaml.j2`](image/cli/mascli/templates/gitops/appset-configs/cluster/ibm-dro.yaml.j2:18): `<path:namespace:secret-name#key>`. Under `kubernetes`, `SECRETS_PATH` should represent the namespace and the `SECRET_KEY_*` values should remain `secret-name#key` references.
- When `AVP_TYPE=kubernetes`, ensure secret resource names are Kubernetes-safe by defaulting the secret-name separator to `_` instead of `/`, while keeping the existing AWS separator behavior unchanged.
- Update CLI function consumers that currently hard-code `AVP_TYPE=aws` so they can pass through or default the backend type without bypassing the shared abstraction.
- In the GitOps repo, keep the existing pattern demonstrated by [`sm_login`](../gitops/sls-applications/100-ibm-sls/templates/08-postsync-update-sm_Job.yaml) usage in the referenced SLS postsync job: source [`gitops_utils`](image/cli/mascli/functions/gitops_utils) and call the shared `sm_*` helpers instead of invoking AWS CLI directly.
- Because the GitOps workspace is outside the current sandbox, implementation must explicitly validate and update that repo during execution using the same abstraction-focused rules.

# Critical Rules

- Introduce no functional changes for the existing AWS backend beyond what is required to add `kubernetes` support.
- Keep all direct secret-provider interactions inside [`gitops_utils`](image/cli/mascli/functions/gitops_utils); do not add new direct `aws secretsmanager` calls elsewhere.
- Use the existing helper names and calling conventions so current scripts and templates continue to work.
- Prefer the smallest possible updates to consumer files: only replace hard-coded backend assumptions or direct AWS calls.
- Validate both the CLI repo and the GitOps repo after edits.
- Track progress only in this plan document; do not create chat todo lists.

# Execution Plan

## Phase 1: Finalize the backend contract in [`gitops_utils`](image/cli/mascli/functions/gitops_utils) ✅ COMPLETE

- [x] **1.1** Audited all sm_* helpers; defined `kubernetes` behavior for all nine functions.
  - [x] `SECRETS_PATH` = namespace; `SECRET_KEY_*` = `secret-name#key` (unchanged from AWS shape).
  - [x] Secret names keep `_` separator (consumers already set keys with `_` e.g. `account_cluster_secretname`).
  - [x] JSON payload: each top-level key becomes a Kubernetes Secret data field; `sm_get_secret*` reconstructs JSON from data fields via jq.
  - [x] `sm_get_secret_arn()` for `kubernetes`: returns the secret name as-is (no ARN concept).
- [x] **1.2** Implemented `kubernetes` branches in all nine `sm_*` helpers using `oc`.
- [x] **1.3** Changed global default from `AVP_TYPE="aws"` to `AVP_TYPE="${AVP_TYPE:-aws}"` so callers can override.
- [x] **1.4** `bash -n gitops_utils` passes. All consumer files syntax-checked cleanly.

## Phase 2: Remove AWS-only assumptions from MAS CLI function consumers ✅ COMPLETE

- [x] **2.1** Changed all 35 bare `AVP_TYPE=aws` assignments across 35 consumer files to `AVP_TYPE="${AVP_TYPE:-aws}"` using `sed`. `gitops_efs_csi_driver` was already in the correct conditional form and was left untouched.
- [x] **2.2** `grep -rn 'aws secretsmanager' image/cli/mascli/functions/` confirms zero matches outside `gitops_utils`.
- [x] **2.3** `bash -n` syntax check passed on all modified files.

## Phase 3: Remove AWS-only assumptions from the GitOps workspace ✅ COMPLETE

- [x] **3.1** Searched all YAML templates in the GitOps repo for `aws secretsmanager` calls. All four occurrences found were already commented-out (legacy documentation lines — no active calls). No replacements needed.
- [x] **3.2** Replaced all 16 hard-coded `value: "aws"` for `AVP_TYPE` env vars with `value: "{{ .Values.sm_backend | default "aws" }}"` across the following templates:
  - `sls-applications/100-ibm-sls/templates/08-postsync-update-sm_Job.yaml`
  - `sls-applications/100-ibm-sls/templates/07-ibm-sls-dns_job.yaml`
  - `cluster-applications/030-ibm-dro/templates/12-2-dro-dns_job.yaml`
  - `cluster-applications/030-ibm-dro/templates/14-postsync-update-sm_Job.yaml`
  - `cluster-applications/060-custom-sa/templates/04-postsync-update-sm_Job.yaml`
  - `cluster-applications/010-redhat-cert-manager/templates/04-postsync-update-sm_Job.yaml`
  - `cluster-applications/055-instana-agent-operator/templates/08-CronJob.yaml`
  - `instance-applications/100-ibm-sls/templates/07-postsync-update-sm_Job.yaml`
  - `instance-applications/130-ibm-jdbc-config/templates/postdelete-delete-db2-user_Job.yaml`
  - `instance-applications/120-ibm-wsl/templates/02-ibm-wsl-post-verify.yaml`
  - `instance-applications/120-ibm-db2u-database/templates/07-postsync-setup-db2_Job.yaml`
  - `instance-applications/510-550-ibm-mas-suite-app-config/templates/700-702-postsync-db2-manage.yaml`
  - `instance-applications/600-ibm-post-sync-jobs/templates/001-ibm-create-initial-users.yaml`
  - `instance-applications/115-ibm-aiservice-tenant/templates/08-aiservice-postsyncjob.yaml`
  - `instance-applications/101-ibm-sync-jobs-cp4d/templates/02-ibm-cp4d-presync.yaml`
  - `instance-applications/010-ibm-sync-jobs/templates/01-ibm-mas_suite_dns_Job.yaml`
  - `instance-applications/010-ibm-sync-jobs/templates/01-ibm-mas_suite_certs_Job.yaml`
- [x] **3.3** Verified `sls-applications/100-ibm-sls/templates/08-postsync-update-sm_Job.yaml` (reference pattern): already sources `gitops_utils` and calls `sm_login` / `sm_update_secret` correctly. No changes required.
- [x] **3.4** `helm lint` passed on all 14 affected charts with 0 failures.

## Phase 4: End-to-end verification ✅ COMPLETE

- [x] **4.1** CLI repo: `grep -rn 'aws secretsmanager' image/cli/mascli/functions/` → 0 matches outside `gitops_utils`. `grep -rn 'AVP_TYPE=aws' image/cli/mascli/functions/` → 0 matches. ✅
- [x] **4.2** GitOps workspace: `grep -rn 'value: "aws"' --include="*.yaml"` → 0 matches. `grep -rn "aws secretsmanager" --include="*.yaml" | grep -v "# aws secretsmanager"` → 0 matches. `grep -rn 'sm_backend' --include="*.yaml"` → 17 parameterized references. ✅
- [x] **4.3** All 14 affected Helm charts pass `helm lint` with 0 failures. Pre-existing warnings (missing `junitreporter` sub-chart, icon recommendation) are unrelated to these changes. ✅

# Final Validation

- In the CLI repo, run the applicable shell validation for changed files, at minimum a syntax pass for edited function files and any project-standard lint or test command available for shell assets.
- Re-run content searches in [`image/cli/mascli/functions/`](image/cli/mascli/functions) for `aws secretsmanager` and `AVP_TYPE=aws` to verify only intentional compatibility defaults remain.
- In the GitOps repo, run content searches and any available YAML or Helm template validation against changed templates and scripts.
- Success criteria:
  - `kubernetes` is supported through the shared [`sm_*`](image/cli/mascli/functions/gitops_utils:245) abstraction.
  - Existing AWS call paths still work.
  - No consumer outside [`gitops_utils`](image/cli/mascli/functions/gitops_utils) calls AWS Secrets Manager directly.
  - GitOps templates and scripts use the abstraction layer rather than provider-specific commands.
- If validation fails, fix the relevant phase first, update this plan file with progress, and re-run validation before completion.
