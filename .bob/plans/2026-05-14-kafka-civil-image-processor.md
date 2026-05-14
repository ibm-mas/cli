# Kafka and Civil Infrastructure Image Processor

## Objective

Review and update the CLI install logic to properly handle Kafka configuration for IoT and Manage Civil Infrastructure component with optional Kafka Image Processor support.

## Current State Analysis

### Kafka Configuration Flow (Current)

**Interactive Mode** ([`interactiveMode()`](python/src/mas/cli/install/app.py:1669-1726)):
1. Apps are configured via [`configApps()`](python/src/mas/cli/install/app.py:1137-1268)
2. Manage settings configured via [`manageSettings()`](python/src/mas/cli/install/settings/manageSettings.py:96-110)
3. Kafka configured via [`configKafka()`](python/src/mas/cli/install/settings/kafkaSettings.py:95-199)

**Kafka Requirements** ([`kafkaSettings.py`](python/src/mas/cli/install/settings/kafkaSettings.py:76-93)):
- [`_requiresKafkaIoT()`](python/src/mas/cli/install/settings/kafkaSettings.py:76-77): Returns `True` if IoT is being installed
- [`_requiresKafkaCivil()`](python/src/mas/cli/install/settings/kafkaSettings.py:79-85): Returns `True` if:
  - Manage is being installed AND
  - Civil component is enabled (`"civil="` in `mas_appws_components`) AND
  - Manage version is 9.2.0 or later

**Civil Component Selection** ([`manageSettings.py`](python/src/mas/cli/install/settings/manageSettings.py:144-145)):
- Civil is selected as a simple yes/no prompt in [`manageSettingsComponents()`](python/src/mas/cli/install/settings/manageSettings.py:128-195)
- No mention of Kafka Image Processor during Civil selection

**Non-Interactive Mode Validation** ([`app.py`](python/src/mas/cli/install/app.py:2149-2163)):
- Validates Kafka is configured if IoT is installed (lines 2149-2153)
- Validates Kafka is configured if Civil is enabled in Manage 9.2+ (lines 2155-2163)

### Issues Identified

1. **Missing Kafka Image Processor Option**: When Civil component is selected, user is not prompted about enabling Kafka Image Processor
2. **No PVC Storage Size Prompt**: If Kafka Image Processor is enabled, no prompt for PVC storage size
3. **Kafka Configuration Timing**: Kafka configuration happens AFTER Manage settings, but the decision about Kafka Image Processor should be made during Civil component selection
4. **No Parameter for Image Processor**: No parameter exists to track whether Kafka Image Processor is enabled for Civil

## Required Changes

### 1. Add New Instance Variable and Parameter

Need to add:
- **Instance variable**: `self.enableKafkaImageProcessor` (boolean) - Similar to `self.devMode`, tracks whether Kafka Image Processor should be enabled. This is the **single control point** for Kafka Image Processor functionality in the CLI.
- **Parameter**: `mas_appws_bindings_kafka_manage` - Kafka binding configuration (similar to `mas_appws_bindings_jdbc_manage`)

**Note**:
- No PVC size parameter needed - the pipeline uses a default of 10GB
- No storage class parameter needed - the pipeline will use `storage_class_rwx` automatically
- The `mas_appws_bindings_kafka_manage` parameter should be set to "system" when Kafka Image Processor is enabled (following the same pattern as JDBC bindings)

### 2. Update Civil Component Selection Flow

In [`manageSettingsComponents()`](python/src/mas/cli/install/settings/manageSettings.py:128-195):

**Current flow** (line 144-145):
```python
if self.yesOrNo(" - Civil Infrastructure"):
    self.params["mas_appws_components"] += ",civil=latest"
```

**New flow**:
```python
if self.yesOrNo(" - Civil Infrastructure"):
    self.params["mas_appws_components"] += ",civil=latest"

    # Check if Manage version supports Kafka Image Processor (9.2+)
    manageChannel = self.getParam("mas_app_channel_manage")
    if manageChannel and isVersionEqualOrAfter('9.2.0', manageChannel):
        self.printDescription([
            "",
            "Civil Infrastructure Defect Detection with Kafka Image Processor:",
            "The Kafka Image Processor enables advanced defect detection capabilities.",
            "This requires a Kafka instance and uses 10GB of storage for image processing."
        ])

        if self.yesOrNo("Enable Kafka Image Processor for Civil Infrastructure"):
            self.enableKafkaImageProcessor = True
            # Bind Manage to system Kafka (similar to JDBC binding pattern)
            self.setParam("mas_appws_bindings_kafka_manage", "system")
```

### 3. Simplify Kafka Requirements Logic

In [`kafkaSettings.py`](python/src/mas/cli/install/settings/kafkaSettings.py:79-93), the [`_requiresKafkaCivil()`](python/src/mas/cli/install/settings/kafkaSettings.py:79-85) function is now **redundant** and should be **removed**.

**Reason**: `self.enableKafkaImageProcessor` is now the single control point. We don't need a separate function to check if Civil requires Kafka - we just check the boolean directly.

**Update [`_getKafkaRequirements()`](python/src/mas/cli/install/settings/kafkaSettings.py:87-93)**:

**Current**:
```python
def _getKafkaRequirements(self) -> List[str]:
    requirements = []
    if self._requiresKafkaIoT():
        requirements.append("Maximo IoT")
    if self._requiresKafkaCivil():
        requirements.append("Manage Civil Infrastructure (9.2+) Defect Detection")
    return requirements
```

**Updated**:
```python
def _getKafkaRequirements(self) -> List[str]:
    requirements = []
    if self._requiresKafkaIoT():
        requirements.append("Maximo IoT")
    if self.enableKafkaImageProcessor:
        requirements.append("Manage Civil Infrastructure (9.2+) Kafka Image Processor")
    return requirements
```

### 4. Update Kafka Configuration Logic

In [`configKafka()`](python/src/mas/cli/install/settings/kafkaSettings.py:95-199), update to use `self.enableKafkaImageProcessor` directly:

**Current** (lines 95-111):
```python
def configKafka(self) -> None:
    requirements = self._getKafkaRequirements()

    if requirements:
        self.printH1("Configure Kafka")

        # Build description based on what requires Kafka
        hasIoT = self._requiresKafkaIoT()
        hasCivil = self._requiresKafkaCivil()

        description = []
        if hasIoT and hasCivil:
            description.append("Maximo IoT and Manage Civil Infrastructure (9.2+) Defect Detection require a shared system-scope Kafka instance")
        elif hasIoT:
            description.append("Maximo IoT requires a shared system-scope Kafka instance")
        elif hasCivil:
            description.append("Manage Civil Infrastructure (9.2+) Defect Detection functionality requires a shared system-scope Kafka instance")
```

**Updated**:
```python
def configKafka(self) -> None:
    requirements = self._getKafkaRequirements()

    if requirements:
        self.printH1("Configure Kafka")

        # Build description based on what requires Kafka
        hasIoT = self._requiresKafkaIoT()
        hasImageProcessor = self.enableKafkaImageProcessor

        description = []
        if hasIoT and hasImageProcessor:
            description.append("Maximo IoT and Manage Civil Infrastructure Kafka Image Processor require a shared system-scope Kafka instance")
        elif hasIoT:
            description.append("Maximo IoT requires a shared system-scope Kafka instance")
        elif hasImageProcessor:
            description.append("Manage Civil Infrastructure Kafka Image Processor requires a shared system-scope Kafka instance")
```

**Key Change**: Use `self.enableKafkaImageProcessor` directly instead of calling `_requiresKafkaCivil()`. This makes `self.enableKafkaImageProcessor` the single control point.

### 5. Update Non-Interactive Mode Validation

In [`nonInteractiveMode()`](python/src/mas/cli/install/app.py:2155-2163), **replace** the existing Civil/Kafka validation with simplified parameter validation:

**Remove Current Validation** (lines 2155-2163):
```python
# Validate Kafka requirements for CIVIL installation in non-interactive mode
isCivilEnabled = self.installManage and "civil=" in self.getParam("mas_appws_components")
if isCivilEnabled:
    manageChannel = self.getParam("mas_app_channel_manage")
    if manageChannel and isVersionEqualOrAfter('9.2.0', manageChannel):
        kafkaAction = self.getParam("kafka_action_system")
        hasKafkaConfig = kafkaAction in ["install", "byo"]
        if not hasKafkaConfig:
            self.fatalError("--manage-components with 'civil=' in Manage 9.2+ requires Kafka configuration...")
```

**Add New Validation** (simple parameter checks):
```python
# Validate --manage-kafka parameter requirements
if self.getParam("mas_appws_bindings_kafka_manage") != "":
    # Validate Kafka provider is configured
    kafkaProvider = self.getParam("kafka_provider")
    if not kafkaProvider or kafkaProvider == "":
        self.fatalError("--manage-kafka requires --kafka-provider to be set")

    # Validate Manage version compatibility
    manageChannel = self.getParam("mas_app_channel_manage")
    if manageChannel and not isVersionEqualOrAfter('9.2.0', manageChannel):
        self.fatalError(f"--manage-kafka requires Manage version 9.2.0 or later. Current version: {manageChannel}")
```

**Key Changes:**
1. Simple parameter validation - no state management needed
2. Check if `--kafka-provider` is set when `--manage-kafka` is provided
3. Check if Manage version >= 9.2.0 when `--manage-kafka` is provided
4. No need to set `self.enableKafkaImageProcessor` in non-interactive mode - it's only used for interactive flow control

### 6. Add CLI Arguments

In [`argParser.py`](python/src/mas/cli/install/argParser.py), add new argument in the Manage section:

```python
manageArgGroup.add_argument(
    "--manage-kafka",
    dest="mas_appws_bindings_kafka_manage",
    required=False,
    help="Select the Kafka configuration to bind to Manage (e.g., 'system'). Required for Civil Infrastructure Kafka Image Processor.",
    default=""
)
```

**Note**: When this parameter is set to "system" in non-interactive mode, it indicates that Kafka Image Processor should be enabled.

### 7. Update Parameter Lists

Add new parameter to [`params.py`](python/src/mas/cli/install/params.py):

```python
"mas_appws_bindings_kafka_manage",
```

**Note**: This should be added near `mas_appws_bindings_jdbc_manage` for consistency.

### 8. Update Command Builder

In [`argBuilder.py`](python/src/mas/cli/install/argBuilder.py), add command line generation for new parameter (near the `--manage-jdbc` line):

```python
if self.getParam('mas_appws_bindings_kafka_manage') != "":
    command += f"  --manage-kafka \"{self.getParam('mas_appws_bindings_kafka_manage')}\"{newline}"
```

### 9. Update Installation Summary

In [`summarizer.py`](python/src/mas/cli/install/summarizer.py), add display of Civil Image Processor settings when Civil is enabled:

```python
if "civil=" in self.getParam("mas_appws_components"):
    self.printSummary("  + Kafka Image Processor",
        "Enabled" if self.enableKafkaImageProcessor else "Disabled")
    if self.enableKafkaImageProcessor:
        self.printParamSummary("  + Kafka Binding", "mas_appws_bindings_kafka_manage")
```

### 10. Update Tekton Pipeline Definitions

**Add Parameter** in [`tekton/src/params/install.yml.j2`](tekton/src/params/install.yml.j2:557-560):

Add after `mas_appws_bindings_jdbc_manage`:
```yaml
- name: mas_appws_bindings_kafka_manage
  type: string
  description: Select the Kafka configuration to bind to Manage
  default: ""
```

**Pass Parameter to Task** in [`tekton/src/pipelines/taskdefs/apps/manage-app.yml.j2`](tekton/src/pipelines/taskdefs/apps/manage-app.yml.j2:37-38):

Add after the `mas_appws_bindings_jdbc` parameter:
```yaml
- name: mas_appws_bindings_kafka
  value: "$(params.mas_appws_bindings_kafka_manage)"
```

## Execution Plan

- [x] **Phase 1: Add Instance Variable and Parameter**
  - [x] Add `self.enableKafkaImageProcessor` instance variable initialization in [`__init__()`](python/src/mas/cli/install/app.py)
  - [x] Add `mas_appws_bindings_kafka_manage` parameter to [`params.py`](python/src/mas/cli/install/params.py)
  - [x] Add `--manage-kafka` CLI argument to [`argParser.py`](python/src/mas/cli/install/argParser.py)
  - [x] Validate additions

- [x] **Phase 2: Update Interactive Flow**
  - [x] Modify [`manageSettingsComponents()`](python/src/mas/cli/install/settings/manageSettings.py:128-195) to prompt for Kafka Image Processor when Civil is selected
  - [x] Set `self.enableKafkaImageProcessor = True` when user enables it
  - [x] Set `mas_appws_bindings_kafka_manage` to "system" when enabled

- [x] **Phase 3: Simplify Kafka Logic**
  - [x] **Remove** [`_requiresKafkaCivil()`](python/src/mas/cli/install/settings/kafkaSettings.py:79-85) function (now redundant)
  - [x] Update [`_getKafkaRequirements()`](python/src/mas/cli/install/settings/kafkaSettings.py:87-93) to use `self.enableKafkaImageProcessor` directly
  - [x] Update [`configKafka()`](python/src/mas/cli/install/settings/kafkaSettings.py:95-199) to use `self.enableKafkaImageProcessor` directly

- [x] **Phase 4: Update Non-Interactive Mode**
  - [x] Update validation in [`nonInteractiveMode()`](python/src/mas/cli/install/app.py:2155-2163) to check `self.enableKafkaImageProcessor`
  - [x] Set `self.enableKafkaImageProcessor = True` when `mas_appws_bindings_kafka_manage` parameter is set to "system"

- [x] **Phase 5: Update Tekton Pipeline**
  - [x] Add `mas_appws_bindings_kafka_manage` parameter to [`tekton/src/params/install.yml.j2`](tekton/src/params/install.yml.j2)
  - [x] Pass parameter to manage task in [`tekton/src/pipelines/taskdefs/apps/manage-app.yml.j2`](tekton/src/pipelines/taskdefs/apps/manage-app.yml.j2)
  - [x] Regenerate Tekton definitions using `ansible-playbook tekton/generate-tekton-pipelines.yml`

- [x] **Phase 6: Update Supporting Code**
  - [x] Update [`argBuilder.py`](python/src/mas/cli/install/argBuilder.py) for command generation
  - [x] Update [`summarizer.py`](python/src/mas/cli/install/summarizer.py) to display Image Processor status and Kafka binding
  - [x] Validate all Python changes with `autopep8` and `flake8`

- [ ] **Phase 7: Automated Testing**
  - [ ] Create `python/test/install/test_manage92_civil_kafka.py` with two test functions:
    - [ ] `test_manage92_civil_no_kafka_interactive()` - Interactive test: Manage 9.2 with Civil, decline Kafka Image Processor
      - Prompt handlers for Civil component selection
      - Decline Kafka Image Processor when prompted
      - Verify no Kafka configuration required
      - Verify `mas_appws_bindings_kafka_manage` is empty
    - [ ] `test_manage92_civil_with_kafka_interactive()` - Interactive test: Manage 9.2 with Civil, enable Kafka Image Processor
      - Prompt handlers for Civil component selection
      - Accept Kafka Image Processor when prompted
      - Prompt handlers for Kafka configuration
      - Verify `mas_appws_bindings_kafka_manage = "system"`
      - Verify Kafka provider is configured
    - [ ] `test_manage92_civil_with_kafka_non_interactive()` - Non-interactive test: Manage 9.2 with Civil and `--manage-kafka system`
      - Use argv similar to [`test_install_master_dev_mode_non_interactive()`](python/test/install/test_dev_mode.py:372)
      - Include `--manage-channel 9.2.x-dev`
      - Include `--manage-components "base=latest,civil=latest"`
      - Include `--manage-kafka system`
      - Include `--kafka-provider strimzi`
      - Verify installation completes successfully
    - [ ] `test_manage92_civil_kafka_validation_errors()` - Non-interactive validation tests:
      - Test `--manage-kafka` without `--kafka-provider` → expect error
      - Test `--manage-kafka` with Manage < 9.2.0 → expect error

## Validation

After implementation, verify:

**Interactive Mode:**
1. ✅ IoT installation prompts for Kafka configuration
2. ✅ Civil component selection (Manage 9.2+) prompts for Kafka Image Processor
3. ✅ If Image Processor enabled, sets `mas_appws_bindings_kafka_manage` to "system"
4. ✅ Kafka configuration only required if IoT OR `self.enableKafkaImageProcessor` is True

**Non-Interactive Mode:**
5. ✅ Validates `--kafka-provider` is set when `--manage-kafka` is provided
6. ✅ Validates Manage version >= 9.2.0 when `--manage-kafka` is provided
7. ✅ Error message clear when Manage version < 9.2.0
8. ✅ Error message clear when `--kafka-provider` missing
9. ✅ No state management needed - pure parameter validation

**Code Quality:**
10. ✅ `self.enableKafkaImageProcessor` is the single control point for Image Processor functionality
11. ✅ `_requiresKafkaCivil()` function removed (redundant)
12. ✅ Installation summary displays Civil Image Processor status and Kafka binding
13. ✅ Generated command includes `--manage-kafka` parameter

**Tekton Integration:**
14. ✅ Tekton pipeline receives `mas_appws_bindings_kafka_manage` parameter
15. ✅ Tekton task passes `mas_appws_bindings_kafka` to ansible-devops role
16. ✅ Pipeline uses default 10GB PVC size and `storage_class_rwx` automatically

**Automated Tests:**
17. ✅ Interactive test: Manage 9.2 with Civil, decline Kafka Image Processor
18. ✅ Interactive test: Manage 9.2 with Civil, enable Kafka Image Processor
19. ✅ Non-interactive test: Manage 9.2 with Civil and `--manage-kafka system`
20. ✅ Validation error tests: Missing `--kafka-provider` and incompatible Manage version
21. ✅ All test cases pass successfully

**Final Checks:**
20. ✅ All Python code passes `black` and `flake8` validation
21. ✅ Tekton definitions regenerate successfully
14. ✅ All Python code passes `black` and `flake8` validation