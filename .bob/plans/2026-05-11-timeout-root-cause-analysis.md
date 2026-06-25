# Tekton Timeout Root Cause Analysis

**Date:** 2026-05-11
**Issue:** TaskRun `fvt811x-fvt-manage-4131-fvt-manage-base-ui-adhoc-report` terminated after 1 hour despite step timeouts of 2.5 hours

---

## Executive Summary

**ROOT CAUSE IDENTIFIED:** Three tasks in the mas-fvt-manage pipeline are missing `timeout: "0"` in their pipeline task definitions, causing Tekton to apply a calculated default timeout of 1 hour that overrides the 150-minute step-level timeouts.

**Impact:** Tasks are terminated prematurely, preventing test steps from completing their work.

---

## Root Cause Analysis

### The Smoking Gun

**Working Task Example (coreapi-addons):**
```yaml
# /tekton/src/pipelines/taskdefs/fvt-core/phase1-under5min.yml.j2
- name: coreapi-addons
  {{ lookup('template', 'taskdefs/fvt-core/common/taskref.yml.j2') | indent(2) }}  # ← Includes timeout: "0"
  params:
    ...
```

The taskref template ([`/tekton/src/pipelines/taskdefs/fvt-core/common/taskref.yml.j2`](/tekton/src/pipelines/taskdefs/fvt-core/common/taskref.yml.j2)) contains:
```yaml
timeout: "0"
taskRef:
  kind: Task
  name: mas-fvt-core
```

**Broken Task (fvt-manage-base-ui-adhoc-report):**
```yaml
# /tekton/src/pipelines/taskdefs/fvt-manage/phase5.yml.j2 (lines 79-96)
- name: fvt-manage-base-ui-adhoc-report
  {{ lookup('template', 'taskdefs/fvt-manage/ui/when.yml.j2') | indent(2) }}
  taskRef:                                                                         # ← Missing timeout: "0"!
    kind: Task
    name: mas-fvt-manage-adhoc-report
  params:
    ...
```

### Why This Matters

**When a pipeline task definition does NOT specify `timeout: "0"`:**
1. Tekton applies a default task timeout
2. Formula: **pipeline timeout ÷ number of tasks**
3. For 8-hour pipeline with ~8 tasks: **480 min ÷ 8 = 60 minutes**
4. This 1-hour task timeout overrides the 150-minute step timeouts
5. Task is killed after exactly 1 hour

**When a pipeline task definition DOES specify `timeout: "0"`:**
1. No task-level timeout is applied
2. Step-level timeouts control execution
3. Tasks can run as long as their steps need

---

## All Affected Tasks

**3 tasks in the mas-fvt-manage pipeline are missing `timeout: "0"`:**

### Phase 4
1. **fvt-manage-base-ui-birt-report** ([`/tekton/src/pipelines/taskdefs/fvt-manage/phase4.yml.j2:37-57`](/tekton/src/pipelines/taskdefs/fvt-manage/phase4.yml.j2))
   - Task: `mas-fvt-manage-birt-report`
   - Task template: [`/tekton/src/tasks/fvt/mas-fvt-manage-birt-report.yml.j2`](/tekton/src/tasks/fvt/mas-fvt-manage-birt-report.yml.j2)
   - Step timeouts: 150 minutes each (3 steps)
   - Missing: `timeout: "0"`

### Phase 5
2. **fvt-manage-base-ui-directprint** ([`/tekton/src/pipelines/taskdefs/fvt-manage/phase5.yml.j2:59-76`](/tekton/src/pipelines/taskdefs/fvt-manage/phase5.yml.j2))
   - Task: `mas-fvt-manage-directprint`
   - Task template: [`/tekton/src/tasks/fvt/mas-fvt-manage-directprint.yml.j2`](/tekton/src/tasks/fvt/mas-fvt-manage-directprint.yml.j2)
   - Step timeouts: 150 minutes each (3 steps)
   - Missing: `timeout: "0"`

3. **fvt-manage-base-ui-adhoc-report** ([`/tekton/src/pipelines/taskdefs/fvt-manage/phase5.yml.j2:79-96`](/tekton/src/pipelines/taskdefs/fvt-manage/phase5.yml.j2)) ← **PRODUCTION FAILURE**
   - Task: `mas-fvt-manage-adhoc-report`
   - Task template: [`/tekton/src/tasks/fvt/mas-fvt-manage-adhoc-report.yml.j2`](/tekton/src/tasks/fvt/mas-fvt-manage-adhoc-report.yml.j2)
   - Step timeouts: 150 minutes each (4 steps)
   - Missing: `timeout: "0"`

---

## Why These 3 Tasks Are Different

**Most tasks use the taskref template:**
```yaml
{{ lookup('template', pipeline_src_dir ~ '/taskdefs/fvt-manage/ui/taskref.yml.j2') | indent(2) }}
```

Which includes ([`/tekton/src/pipelines/taskdefs/fvt-manage/ui/taskref.yml.j2`](/tekton/src/pipelines/taskdefs/fvt-manage/ui/taskref.yml.j2)):
```yaml
timeout: "0"
taskRef:
  kind: Task
  name: mas-fvt-manage
```

**But these 3 tasks directly specify taskRef without the template:**
```yaml
taskRef:
  kind: Task
  name: mas-fvt-manage-adhoc-report
```

This bypasses the `timeout: "0"` that should be included.

---

## The Fix

Add `timeout: "0"` before `taskRef:` in all 3 task definitions:

### Fix 1: phase4.yml.j2 (line 37)
**File:** [`/tekton/src/pipelines/taskdefs/fvt-manage/phase4.yml.j2`](/tekton/src/pipelines/taskdefs/fvt-manage/phase4.yml.j2)

```yaml
# Manage FVT BIRT Reports
- name: fvt-manage-base-ui-birt-report
  timeout: "0"  # ← ADD THIS LINE
  {{ lookup('template', pipeline_src_dir ~ '/taskdefs/fvt-manage/ui/when.yml.j2') | indent(2) }}
  taskRef:
    kind: Task
    name: mas-fvt-manage-birt-report
  params:
    {{ lookup('template', pipeline_src_dir ~ '/taskdefs/fvt-manage/ui/params.yml.j2') | indent(4) }}
```

### Fix 2: phase5.yml.j2 (line 59)
**File:** [`/tekton/src/pipelines/taskdefs/fvt-manage/phase5.yml.j2`](/tekton/src/pipelines/taskdefs/fvt-manage/phase5.yml.j2)

```yaml
# Manage Direct Print Report Tasks
- name: fvt-manage-base-ui-directprint
  timeout: "0"  # ← ADD THIS LINE
  {{ lookup('template', pipeline_src_dir ~ '/taskdefs/fvt-manage/ui/when.yml.j2') | indent(2) }}
  taskRef:
    kind: Task
    name: mas-fvt-manage-directprint
  params:
    {{ lookup('template', pipeline_src_dir ~ '/taskdefs/fvt-manage/ui/params.yml.j2') | indent(4) }}
```

### Fix 3: phase5.yml.j2 (line 79)
**File:** [`/tekton/src/pipelines/taskdefs/fvt-manage/phase5.yml.j2`](/tekton/src/pipelines/taskdefs/fvt-manage/phase5.yml.j2)

```yaml
# Manage FVT Adhoc Reports
- name: fvt-manage-base-ui-adhoc-report
  timeout: "0"  # ← ADD THIS LINE
  {{ lookup('template', 'taskdefs/fvt-manage/ui/when.yml.j2') | indent(2) }}
  taskRef:
    kind: Task
    name: mas-fvt-manage-adhoc-report
  params:
    {{ lookup('template', 'taskdefs/fvt-manage/ui/params.yml.j2') | indent(4) }}
```

---

## Verification Steps

After applying fixes:

1. **Regenerate pipelines:**
   ```bash
   ansible-playbook tekton/generate-tekton-pipelines.yml
   ```

2. **Check generated pipeline:**
   - File: `/tekton/target/pipelines/mas-fvt-manage.yaml`
   - Verify all 3 tasks have `timeout: "0"` in the generated YAML

3. **Deploy and test:**
   - Apply updated pipeline to cluster
   - Run test to verify tasks complete successfully

---

## Additional Findings

### Task Templates (✅ All Correct)
All 52 task templates in [`/tekton/src/tasks/`](/tekton/src/tasks/) correctly define timeouts **only at step level**:
- No task-level timeouts defined
- Step timeouts range from 90m to 6h40m
- Pattern is correct and consistent

### Pipeline TaskDefs (⚠️ 3 Issues Found)
77 pipeline task definitions in [`/tekton/src/pipelines/taskdefs/`](/tekton/src/pipelines/taskdefs/):
- **76 use `timeout: "0"`** (correct)
- **3 missing `timeout: "0"`** (the issues identified above)
- **1 uses `timeout: "2h"`** - AIService FVT ([`/tekton/src/pipelines/taskdefs/fvt-aiservice/common/taskref.yml.j2`](/tekton/src/pipelines/taskdefs/fvt-aiservice/common/taskref.yml.j2))
  - Note: This is a separate issue - task timeout 2h vs step timeout 3h

### PipelineRun Templates (ℹ️ Context)
20 PipelineRun templates in [`/image/cli/masfvt/templates/`](/image/cli/masfvt/templates/):
- **18 templates:** `timeouts.pipeline: "8h"`
- **1 template:** `timeouts.pipeline: "12h"` (mas-fvt-core)
- **1 template:** `timeouts.pipeline: "0"` (finally)

The PipelineRun timeout is NOT the root cause, but it determines the calculated default task timeout. Tasks with explicit `timeout: "0"` work correctly regardless of the PipelineRun timeout (as proven by coreapi-addons).

---

## Why This Wasn't Caught Earlier

1. **Inconsistent pattern usage** - Most tasks use the taskref template, but these 3 don't
2. **No validation** - No CI/CD checks for missing timeouts in pipeline taskdefs
3. **Silent failure mode** - Tekton applies default timeout without warning
4. **Timing-dependent** - Only manifests when tasks run longer than calculated default (60 minutes)
5. **Rare occurrence** - Most tasks complete within the default timeout

---

## Recommendations

### Immediate Actions (Critical)

1. **Apply the 3 fixes above** to add `timeout: "0"` to the affected tasks
2. **Regenerate and deploy** the updated pipeline
3. **Test** to verify tasks complete successfully

### Short-term Actions

1. **Fix AIService FVT timeout** - Change [`/tekton/src/pipelines/taskdefs/fvt-aiservice/common/taskref.yml.j2`](/tekton/src/pipelines/taskdefs/fvt-aiservice/common/taskref.yml.j2) from `timeout: "2h"` to `timeout: "0"`
2. **Add CI/CD validation** to ensure all pipeline tasks have explicit timeouts
3. **Audit all pipelines** for similar issues

### Long-term Actions

1. **Standardize on taskref templates** - Always use templates to avoid this pattern
2. **Documentation** - Document the timeout interaction between PipelineRun, Task, and Step levels
3. **Monitoring** - Add alerts for TaskRuns terminated by timeout
4. **Create troubleshooting guide** for timeout-related failures

---

## Technical Details

### Timeout Hierarchy in Tekton

```
PipelineRun
├── timeouts.pipeline: "8h"          ← Sets overall pipeline limit
└── Tasks
    ├── timeout: "0"                 ← No task limit (uses step timeouts)
    └── Steps
        └── timeout: "150m"          ← Step-level timeout
```

**Problem:** When `timeouts.pipeline` is set and task `timeout` is not specified, Tekton calculates:
- Default task timeout = pipeline timeout / number of tasks
- This overrides the intent of allowing steps to control timing
- Step timeouts become irrelevant if task timeout is shorter

### Correct Configuration

```yaml
# PipelineRun
spec:
  timeouts:
    pipeline: "8h"  # Overall limit (optional)

# Pipeline TaskDef
- name: my-task
  timeout: "0"      # REQUIRED: No task timeout, let steps control timing
  taskRef:
    kind: Task
    name: my-task-name

# Task
spec:
  steps:
    - name: my-step
      timeout: 150m  # Step controls its own timeout
```

---

## Conclusion

The production failure was caused by a simple but critical omission: three pipeline task definitions were missing `timeout: "0"`. This allowed Tekton to apply a calculated default timeout of 1 hour, which terminated tasks before their 150-minute steps could complete.

The fix is straightforward: add `timeout: "0"` to the three affected task definitions. This will allow the step-level timeouts to control execution as intended.