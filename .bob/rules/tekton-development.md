a# Tekton Development Guide

## Overview

This guide covers the development workflow for Tekton pipelines and tasks in the MAS CLI project. The Tekton definitions use Jinja2 templating to generate reusable, parameterized CI/CD pipelines for IBM Maximo Application Suite (MAS) installation, configuration, and testing.

## Architecture

### Directory Structure

```
tekton/
├── generate-tekton-tasks.yml       # Ansible playbook to generate tasks
├── generate-tekton-pipelines.yml   # Ansible playbook to generate pipelines
├── src/                            # Source templates (Jinja2)
│   ├── params/                     # Parameter definitions
│   │   ├── common.yml.j2          # Common parameters (image_pull_policy, etc.)
│   │   ├── install-common.yml.j2  # Storage classes, entitlement
│   │   ├── install.yml.j2         # Main install parameters
│   │   └── install-*.yml.j2       # Component-specific parameters
│   ├── pipelines/                  # Pipeline templates
│   │   ├── mas-install.yml.j2     # Main installation pipeline
│   │   ├── mas-upgrade.yml.j2     # Upgrade pipeline
│   │   └── taskdefs/              # Task definitions used in pipelines
│   │       ├── core/              # Core MAS tasks
│   │       ├── apps/              # Application-specific tasks
│   │       ├── dependencies/      # Dependency installation tasks
│   │       └── common/            # Common task definitions
│   └── tasks/                      # Standalone task templates
│       ├── suite-config.yml.j2    # Suite configuration task
│       ├── suite-install.yml.j2   # Suite installation task
│       ├── common/                # Common task components
│       │   ├── cli-params.yml.j2  # Common CLI parameters
│       │   └── cli-env.yml.j2     # Common environment variables
│       └── dependencies/          # Dependency tasks
└── target/                         # Generated YAML files (not in git)
    ├── tasks/                      # Generated task definitions
    └── pipelines/                  # Generated pipeline definitions
```

### Key Concepts

1. **Jinja2 Templates**: All `.yml.j2` files are Jinja2 templates that generate Tekton YAML
2. **Parameter Composition**: Parameters are composed from multiple template files using `lookup('template', ...)`
3. **Task Definitions**: Reusable task definitions in `src/pipelines/taskdefs/` are included in pipelines
4. **Generation Process**: Ansible playbooks process templates and output to `target/` directory

## Development Workflow

### 1. Modifying Existing Tasks

When modifying a task (e.g., `suite-config`):

1. **Locate the task template**: `tekton/src/tasks/suite-config.yml.j2`
2. **Understand parameter sources**:
   - Common parameters: `src/tasks/common/cli-params.yml.j2`
   - Environment variables: `src/tasks/common/cli-env.yml.j2`
   - Task-specific parameters: Defined directly in the task
3. **Make changes** to the template
4. **Regenerate** the task using the generation playbook

### 2. Adding New Parameters

#### To a Task

1. **Add parameter definition** in the task's `spec.params` section:
   ```yaml
   - name: new_parameter
     type: string
     description: Description of the parameter
     default: ""
   ```

2. **Add environment variable** in the task's `stepTemplate.env` section:
   ```yaml
   - name: NEW_PARAMETER
     value: $(params.new_parameter)
   ```

3. **Update pipeline taskdefs** that use this task to pass the parameter

#### To a Pipeline

1. **Add to parameter file** (e.g., `src/params/install.yml.j2`):
   ```yaml
   - name: new_parameter
     type: string
     description: Description
     default: ""
   ```

2. **Pass to tasks** in pipeline taskdefs (e.g., `src/pipelines/taskdefs/core/suite-config.yml.j2`):
   ```yaml
   - name: suite-config
     params:
       - name: new_parameter
         value: $(params.new_parameter)
   ```

### 3. Parameter Composition Pattern

Parameters are composed using Jinja2 `lookup` function:

```yaml
params:
  {{ lookup('template', params_src_dir ~ '/common.yml.j2') | indent(4) }}
  {{ lookup('template', params_src_dir ~ '/install-common.yml.j2') | indent(4) }}
  {{ lookup('template', params_src_dir ~ '/install.yml.j2') | indent(4) }}
```

This pattern:
- Includes common parameters from multiple files
- Uses `indent(4)` to maintain proper YAML indentation
- Allows parameter reuse across pipelines

### 4. Task Reference Pattern

Pipeline task definitions use a two-file pattern:

1. **Task definition file** (e.g., `taskdefs/core/suite-config.yml.j2`):
   ```yaml
   - name: suite-config
     timeout: "0"
     params:
       {{ lookup('template', pipeline_src_dir ~ '/taskdefs/common/cli-params.yml.j2') | indent(4) }}
       - name: mas_instance_id
         value: $(params.mas_instance_id)
     taskRef:
       kind: Task
       name: mas-devops-suite-config
     workspaces:
       - name: configs
         workspace: shared-configs
   ```

2. **Pipeline includes the taskdef**:
   ```yaml
   tasks:
     {{ lookup('template', pipeline_src_dir ~ '/taskdefs/core/suite-config.yml.j2') | indent(4) }}
       runAfter:
         - suite-install
   ```

### 5. Storage Class Parameters

Storage class parameters follow a standard pattern:

- **RWO (ReadWriteOnce)**: `storage_class_rwo` - for single-node access
- **RWX (ReadWriteMany)**: `storage_class_rwx` - for multi-node access

Defined in `src/params/install-common.yml.j2`:
```yaml
- name: storage_class_rwo
  type: string
  default: ""
  description: ReadWriteOnce storage class
- name: storage_class_rwx
  type: string
  default: ""
  description: ReadWriteMany storage class
```

Usage pattern in tasks:
```yaml
- name: STORAGE_CLASS
  value: $(params.storage_class_rwx)
```

### 6. Environment Variable Mapping

Environment variables in tasks map to Ansible role variables:

**Task Parameter** → **Environment Variable** → **Ansible Role Variable**

Example:
```yaml
# Pipeline parameter
- name: mas_app_settings_jms_queue_pvc_storage_class
  type: string
  default: ""

# Task receives parameter
params:
  - name: mas_app_settings_jms_queue_pvc_storage_class
    value: $(params.mas_app_settings_jms_queue_pvc_storage_class)

# Task sets environment variable
env:
  - name: MAS_APP_SETTINGS_JMS_QUEUE_PVC_STORAGE_CLASS
    value: $(params.mas_app_settings_jms_queue_pvc_storage_class)

# Ansible role uses variable
# In ansible-devops role: mas_app_settings_jms_queue_pvc_storage_class
```

**Naming Convention**:
- Pipeline parameters: lowercase with underscores
- Environment variables: UPPERCASE with underscores
- Ansible variables: lowercase with underscores (same as pipeline params)

## Generation Process

### Generating Tasks

```bash
ansible-playbook tekton/generate-tekton-tasks.yml
```

This processes all task templates in `src/tasks/` and outputs to `target/tasks/`.

### Generating Pipelines

```bash
ansible-playbook tekton/generate-tekton-pipelines.yml
```

This processes all pipeline templates in `src/pipelines/` and outputs to `target/pipelines/`.

### Variables Available in Templates

- `task_src_dir`: Path to task source directory (`src/tasks`)
- `params_src_dir`: Path to params source directory (`src/params`)
- `pipeline_src_dir`: Path to pipeline source directory (`src/pipelines`)
- `mas_tekton_version`: Version tag for generated resources

## Testing Changes

1. **Generate the updated definitions**:
   ```bash
   ansible-playbook tekton/generate-tekton-tasks.yml
   ansible-playbook tekton/generate-tekton-pipelines.yml
   ```

2. **Review generated YAML** in `target/` directory

3. **Apply to cluster** (if testing):
   ```bash
   oc apply -f target/tasks/suite-config.yaml
   oc apply -f target/pipelines/mas-install.yaml
   ```

4. **Run pipeline** to validate changes

## Common Patterns

### Adding Storage Configuration

When adding storage-related parameters:

1. **Use existing storage class parameters** when possible:
   - `$(params.storage_class_rwx)` for shared storage
   - `$(params.storage_class_rwo)` for single-node storage

2. **Add size parameter** with empty default:
   ```yaml
   - name: component_pvc_size
     type: string
     description: PVC size for component
     default: ""
   ```

3. **Map to environment variables**:
   ```yaml
   - name: COMPONENT_PVC_SIZE
     value: $(params.component_pvc_size)
   - name: COMPONENT_PVC_STORAGECLASS
     value: $(params.storage_class_rwx)
   ```

### Conditional Task Execution

Use `when` clauses for conditional execution:

```yaml
- name: optional-task
  when:
    - input: "$(params.enable_feature)"
      operator: in
      values: ["true", "True"]
```

### Task Dependencies

Use `runAfter` to define task execution order:

```yaml
- name: dependent-task
  runAfter:
    - prerequisite-task-1
    - prerequisite-task-2
```

## Best Practices

1. **Parameter Defaults**: Use empty string `""` for optional parameters
2. **Documentation**: Always include `description` for parameters
3. **Indentation**: Use `indent(N)` filter when including templates
4. **Naming**: Follow existing naming conventions (lowercase_with_underscores)
5. **Reuse**: Leverage existing parameter files and taskdefs
6. **Testing**: Always regenerate and test after changes
7. **Storage Classes**: Reuse `storage_class_rwx` and `storage_class_rwo` parameters

## Troubleshooting

### Template Syntax Errors

If generation fails with Jinja2 errors:
- Check template syntax in `.yml.j2` files
- Verify `lookup()` paths are correct
- Ensure proper indentation in YAML

### Missing Parameters

If tasks fail with missing parameter errors:
- Verify parameter is defined in appropriate params file
- Check parameter is passed from pipeline to task
- Ensure environment variable mapping is correct

### Task Not Found

If pipeline fails with task not found:
- Verify task was generated in `target/tasks/`
- Check task name matches `taskRef.name` in pipeline
- Ensure task was applied to cluster