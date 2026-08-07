# Suite Summary Conversion Plan

## Objective
Convert the bash script `tmp/suite-summary.sh` into a Python module that generates MAS suite summaries from must-gather files (not live cluster queries). Integrate this into the must-gather CLI with a new `summarize` command.

## Design Decisions

### Architecture
- **Summarizer Pattern**: Follow the existing `subscriptions.py` pattern - read YAML files from must-gather directory structure
- **Output Format**: Generate markdown instead of plain text for better readability in web viewer
- **Data Sources**: All information must come from collected must-gather files:
  - Suite CR: `resources/mas-{instance}-core/suite/{instance}.yaml`
  - Pods: `resources/mas-{instance}-core/pods/*/` (YAML files and pod status)
  - ConfigMaps: `resources/mas-{instance}-core/configmaps/`
  - App Workspace CRs: `resources/mas-{instance}-{app}/` directories
  - SCIM configs: `resources/mas-{instance}-core/scimcfg/` (if exists)

### Key Differences from Bash Script
1. **No cluster queries**: All data from must-gather files
2. **Markdown output**: Use markdown headers, tables, and formatting
3. **Version detection**: Parse from Suite CR status instead of live queries
4. **Pod status**: Read from collected pod YAML files
5. **Communication tests**: Skip (requires live cluster access)

### Summary Sections (Markdown)
1. **MAS Environment Overview**
   - MAS Core Version
   - Seamless login status (8.11+)
   - User self-registration config (9.0+)

2. **User Registry Synchronization**
   - SCIM sync reports (if configured)

3. **Pod Health and Status**
   - Core services pods (coreapi, internalapi, usersync-coordinator, scimsync)
   - Table format with pod name, state, reason

4. **Activated Applications**
   - List of installed apps (detect from workspace CRs)

5. **Manage Application Details** (if installed)
   - Version
   - Deployment type (Full/Foundation)
   - Bundle configuration
   - Pod status
   - PodTemplates configuration

6. **Identity Provider Status** (8.11+)
   - Note: Cannot retrieve from must-gather (requires API calls)
   - Document limitation

7. **Licensing Information** (9.1+)
   - Note: Cannot retrieve from must-gather (requires API calls)
   - Document limitation

## Critical Rules
- **No cluster access**: All data must come from must-gather files
- **Handle missing data gracefully**: Not all must-gather versions have all resources
- **Version-aware**: Check MAS version to determine which sections to include
- **Markdown formatting**: Use proper markdown syntax for headers, lists, tables
- **Error handling**: Continue processing even if some data is missing

## Execution Plan

### Phase 1: Create Suite Summarizer Module
**Objective**: Implement `python/src/mas/cli/must_gather/summarizer/suite.py`

- [x] **1.1** Create `suite.py` with module docstring and copyright header
- [x] **1.2** Implement helper function `_parseVersion(versionStr: str) -> tuple[int, int, int]`
- [x] **1.3** Implement helper function `_findMASInstances(resourcesDir: str) -> list[str]`
- [x] **1.4** Implement helper function `_loadSuiteCR(outputDir: str, instanceId: str) -> Optional[dict]`
- [x] **1.5** Implement helper function `_getPodStatus(outputDir: str, namespace: str) -> list[dict]`
- [x] **1.6** Implement helper function `_getActivatedApps(outputDir: str, instanceId: str) -> list[str]`
- [x] **1.7** Implement helper function `_loadManageWorkspaceCR(outputDir: str, instanceId: str) -> Optional[dict]`
- [x] **1.8** Implement helper function `_getSCIMConfig(outputDir: str, instanceId: str) -> Optional[dict]`
- [x] **1.9** Implement main function `summarize(outputDir: str) -> None`
- [x] **1.10** Add comprehensive docstrings to all functions (Google style)
- [x] **1.11** Validate with black and flake8

### Phase 2: Refactor Summary Generation
**Objective**: Create generic `generateSummary()` function in `app.py`

- [x] **2.1** Rename `generateSubscriptionsSummary()` to `_generateSubscriptionsSummary()`
- [x] **2.2** Create new `generateSummary(outputDir: str) -> bool` method
- [x] **2.3** Update `_collectMustGather()` to call `generateSummary()` instead
- [x] **2.4** Add logging for each summarizer execution
- [x] **2.5** Validate changes don't break existing functionality

### Phase 3: Add Summarize CLI Command
**Objective**: Add `mas-cli must-gather summarize` command

- [x] **3.1** Update `arg_parser.py` to add `summarize` subcommand
- [x] **3.2** Update `app.py` `mustGather()` method
- [x] **3.3** Add validation that directory exists and contains must-gather data
- [x] **3.4** Add success/error messages with proper formatting
- [x] **3.5** Update help text and documentation

### Phase 4: Testing and Validation
**Objective**: Ensure all functionality works correctly

- [x] **4.1** Test suite summarizer with sample must-gather
- [x] **4.2** Test `summarize` command
- [ ] **4.3** Test full must-gather collection (requires live cluster)
- [ ] **4.4** Test error handling (requires additional test cases)
- [x] **4.5** Run black and flake8 on all modified files
- [ ] **4.6** Update any relevant documentation (if needed)

## Final Validation
- [ ] All summarizers run successfully during must-gather collection
- [ ] `summarize` command works independently on existing must-gather
- [ ] Markdown output is properly formatted and readable
- [ ] No cluster access is required (all data from files)
- [ ] Error handling is robust
- [ ] Code follows project style guidelines
