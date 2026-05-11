# Add Kafka Image Processor Storage Configuration

**Date**: 2026-05-10

## Objective

Add support for configuring Kafka Image Processor PVC size and storage class in the Manage application configuration through Tekton pipelines.

## Critical Rules

- Follow existing parameter naming conventions (lowercase with underscores)
- Use empty string `""` as default for optional parameters
- Reuse existing `storage_class_rwx` parameter for storage class
- Add size parameter with empty default (Ansible role has its own default)
- Maintain proper YAML indentation when using Jinja2 templates
- Regenerate both tasks and pipelines after making changes

## Execution Plan

### Phase 1: Add Pipeline Parameters

**Objective**: Add new parameters to the install pipeline parameter definitions

- [x] **1.1** Add `mas_manage_kafkaimageprocessor_pvc_size` parameter to [`tekton/src/params/install.yml.j2`](/tekton/src/params/install.yml.j2)

Insert after line 684 (after `mas_appws_upgrade_type`):

```yaml
- name: mas_manage_kafkaimageprocessor_pvc_size
  type: string
  description: PVC size for Manage Kafka Image Processor
  default: ""
```

### Phase 2: Update Suite App Install Task

**Objective**: Add parameters and environment variables to the suite-app-install task

- [x] **2.1** Add `mas_manage_kafkaimageprocessor_pvc_size` parameter to [`tekton/src/tasks/suite-app-install.yml.j2`](/tekton/src/tasks/suite-app-install.yml.j2)

Insert after line 269 (after `mas_appws_upgrade_type`):

```yaml
    - name: mas_manage_kafkaimageprocessor_pvc_size
      type: string
      description: PVC size for Manage Kafka Image Processor
      default: ""
```

- [x] **2.2** Add `storage_class_rwx` parameter to [`tekton/src/tasks/suite-app-install.yml.j2`](/tekton/src/tasks/suite-app-install.yml.j2)

Insert after the `manage_kafkaimageprocessor_pvc_size` parameter:

```yaml
    - name: storage_class_rwx
      type: string
      description: ReadWriteMany storage class
      default: ""
```

- [x] **2.3** Add `MAS_MANAGE_KAFKAIMAGEPROCESSOR_PVC_SIZE` environment variable to [`tekton/src/tasks/suite-app-install.yml.j2`](/tekton/src/tasks/suite-app-install.yml.j2)

Insert in the `app-config` step's `env` section after line 514 (after `MAS_APPWS_UPGRADE_TYPE`):

```yaml
        - name: MAS_MANAGE_KAFKAIMAGEPROCESSOR_PVC_SIZE
          value: $(params.mas_manage_kafkaimageprocessor_pvc_size)
```

- [x] **2.4** Add `MAS_MANAGE_KAFKAIMAGEPROCESSOR_PVC_STORAGECLASS` environment variable to [`tekton/src/tasks/suite-app-install.yml.j2`](/tekton/src/tasks/suite-app-install.yml.j2)

Insert after the `MAS_MANAGE_KAFKAIMAGEPROCESSOR_PVC_SIZE` variable:

```yaml
        - name: MAS_MANAGE_KAFKAIMAGEPROCESSOR_PVC_STORAGECLASS
          value: $(params.storage_class_rwx)
```

### Phase 3: Update Manage App Pipeline Task Definition

**Objective**: Pass parameters from pipeline to suite-app-install task for Manage application

- [x] **3.1** Add parameter mappings to [`tekton/src/pipelines/taskdefs/apps/manage-app.yml.j2`](/tekton/src/pipelines/taskdefs/apps/manage-app.yml.j2)

Insert after line 114 (after `mas_appws_upgrade_type`):

```yaml
    - name: mas_manage_kafkaimageprocessor_pvc_size
      value: $(params.mas_manage_kafkaimageprocessor_pvc_size)
    - name: storage_class_rwx
      value: $(params.storage_class_rwx)
```

### Phase 4: Generate and Validate

**Objective**: Generate updated Tekton definitions and validate syntax

- [x] **4.1** Generate tasks
  ```bash
  ansible-playbook tekton/generate-tekton-tasks.yml
  ```

- [x] **4.2** Generate pipelines
  ```bash
  ansible-playbook tekton/generate-tekton-pipelines.yml
  ```

- [x] **4.3** Verify generated files
  - Check `target/tasks/suite-app-install.yaml` for new parameters and environment variables
  - Check `target/pipelines/mas-install.yaml` for new parameter
  - Validate YAML syntax is correct

## Validation

### Success Criteria

1. **Parameter Definition**: `mas_manage_kafkaimageprocessor_pvc_size` parameter exists in install pipeline with empty default
2. **Task Parameters**: Both `mas_manage_kafkaimageprocessor_pvc_size` and `storage_class_rwx` parameters are defined in suite-app-install task
3. **Environment Variables**: Both `MAS_MANAGE_KAFKAIMAGEPROCESSOR_PVC_SIZE` and `MAS_MANAGE_KAFKAIMAGEPROCESSOR_PVC_STORAGECLASS` are defined in suite-app-install task's app-config step
4. **Pipeline Mapping**: Manage app taskdef passes both parameters to suite-app-install task correctly
5. **Storage Class Reuse**: `MAS_MANAGE_KAFKAIMAGEPROCESSOR_PVC_STORAGECLASS` uses `$(params.storage_class_rwx)`
6. **Generation Success**: Both Ansible playbooks complete without errors
7. **YAML Validity**: Generated files are valid YAML with proper indentation

### Validation Commands

```bash
# Generate definitions
ansible-playbook tekton/generate-tekton-tasks.yml
ansible-playbook tekton/generate-tekton-pipelines.yml

# Verify parameter in pipeline
grep -A 2 "mas_manage_kafkaimageprocessor_pvc_size" target/pipelines/mas-install.yaml

# Verify task parameters
grep -A 2 "mas_manage_kafkaimageprocessor_pvc_size" target/tasks/suite-app-install.yaml
grep -A 2 "storage_class_rwx" target/tasks/suite-app-install.yaml

# Verify environment variables in task
grep "MAS_APP_SETTINGS_KAFKAIMAGEPROCESSOR" target/tasks/suite-app-install.yaml

# Validate YAML syntax
yamllint target/tasks/suite-app-install.yaml
yamllint target/pipelines/mas-install.yaml
```

## Implementation Notes

### Parameter Naming

Following the established pattern for Manage application settings:
- Pipeline parameter: `mas_manage_kafkaimageprocessor_pvc_size` (lowercase with underscores)
- Environment variable: `MAS_MANAGE_KAFKAIMAGEPROCESSOR_PVC_SIZE` (uppercase with underscores)
- Ansible variable: `mas_manage_kafkaimageprocessor_pvc_size` (same as pipeline parameter)

### Storage Class Strategy

Reusing `storage_class_rwx` because:
- Kafka Image Processor requires shared storage (ReadWriteMany)
- Consistent with other Manage storage configurations (see line 98 in manage-app.yml.j2: `mas_manage_imagestitching_storage_class`)
- Avoids parameter proliferation
- Follows existing patterns in the codebase

### Default Values

- Size parameter defaults to `""` (empty string)
- Ansible role `suite_app_config` provides its own default value
- This allows Tekton to be non-opinionated about sizing
- Users can override by setting the pipeline parameter

## Code Change Summary

### Files to Modify

1. **`tekton/src/params/install.yml.j2`** - Add pipeline parameter
2. **`tekton/src/tasks/suite-app-install.yml.j2`** - Add task parameters and environment variables
3. **`tekton/src/pipelines/taskdefs/apps/manage-app.yml.j2`** - Pass parameters to task

### Expected Changes

**Total lines added**: ~12 lines across 3 files
**Total lines modified**: 0 (only additions)

## References

- [Tekton Development Guide](/.bob/rules/tekton-development.md)
- [Suite App Install Task](/tekton/src/tasks/suite-app-install.yml.j2)
- [Install Parameters](/tekton/src/params/install.yml.j2)
- [Manage App Task Definition](/tekton/src/pipelines/taskdefs/apps/manage-app.yml.j2)