# Refactor Resource Collection to Generate Markdown Index Files

## Objective
Replace text-based resource summaries with markdown index files that provide structured, tabular views of collected resources with resource-specific columns.

## Design Decisions

### Markdown Format
- **Header**: `# {Kind} ({apiVersion})`
- **Table**: Markdown table with resource-specific columns
- **File Extension**: Change from `.txt` to `.md`

### Field Mapping System - CRD-Based Approach
**Use CRD `additionalPrinterColumns` specifications** to determine which fields to display, exactly like `kubectl` does.

#### Advantages:
1. **Consistency with kubectl**: Users see the same columns they're familiar with
2. **No manual maintenance**: Automatically works for all CRDs (IBM and third-party)
3. **Already available**: We already load CRDs via `getIBMCRDs()` function
4. **Accurate field paths**: CRDs specify exact JSONPath for each column
5. **Type information**: CRDs include data types (string, integer, date, etc.)

#### Implementation Strategy:
1. **Extend CRD loading** to capture `additionalPrinterColumns` from each CRD
2. **Cache printer columns** alongside kind/apiVersion in `getIBMCRDs()`
3. **Create fallback mappings** for built-in Kubernetes resources (Pod, Service, etc.) that don't have CRDs
4. **Extract field values** using JSONPath expressions from CRD specs

#### CRD Structure Example:
```yaml
spec:
  versions:
    - name: v1
      additionalPrinterColumns:
        - name: Status
          type: string
          jsonPath: .status.conditions[?(@.type=="Ready")].status
        - name: Age
          type: date
          jsonPath: .metadata.creationTimestamp
```

### Field Extraction Strategy
- **For CRDs**: Use JSONPath from `additionalPrinterColumns`
- **For built-in resources**: Hardcode common patterns (Pod, Service, Deployment, etc.)
- **Default**: Show only resource name when no columns defined

### Backward Compatibility
- Keep the same file naming convention (pluralized kind)
- Maintain the same directory structure
- Preserve all existing collection logic
- Only change the summary file format and remove `noDetail` parameter

## Critical Rules
- **No functional changes** to resource collection logic
- **Preserve all existing tests** - update only the assertions about file format
- **Maintain parallel collection** performance characteristics
- **Track progress** ONLY in this plan document, NOT in chat todo lists
- **Validate after every phase** before proceeding

## Execution Plan

### Phase 1: CRD Processing Infrastructure
**Objective**: Process ALL CRDs during OCP collection to extract printer columns and identify IBM CRDs

- [x] **1.1** Create `python/src/mas/cli/must_gather/common/crd_processor.py`
  - [x] Define `PrinterColumn` dataclass: name, type, jsonPath, description, priority
  - [x] Define `CRDInfo` dataclass: kind, apiVersion, group, printerColumns, isIBM
  - [x] Implement `processCRDs(dynClient: DynamicClient, outputDir: str) -> tuple[Dict, List]`
    - [x] Load ALL CRDs from cluster
    - [x] For each CRD extract:
      - [x] kind, apiVersion, group
      - [x] `additionalPrinterColumns` from spec
      - [x] Determine if IBM CRD (name contains "ibm")
    - [x] Write CRDs to `{outputDir}/_cluster/customresourcedefinitions.yaml`
    - [x] Return: (printerColumnsCache, ibmCRDsList)
  - [x] Implement `getPrinterColumns(kind: str, apiVersion: str) -> List[PrinterColumn]` lookup
  - [x] Create fallback mappings for built-in Kubernetes resources
  - [x] Implement JSONPath evaluator: `extractValueFromJsonPath(resource: dict, jsonPath: str) -> str`
  - [x] Add comprehensive docstrings

- [x] **1.2** Update `python/src/mas/cli/must_gather/ocp/cluster.py`
  - [x] Add CRD collection as first step in `collectClusterResources()`
  - [x] Call `processCRDs()` to get printer columns and IBM CRD list
  - [x] Store results in module-level variables for access by other collectors
  - [x] Return both printer columns cache and IBM CRD list

- [x] **1.3** Update `python/src/mas/cli/must_gather/app.py`
  - [x] Modify `collectOCP()` to capture CRD processing results
  - [x] Store printer columns cache and IBM CRD list as instance variables
  - [x] Handle `--no-ocp` flag: still process CRDs but skip other OCP collection
  - [x] Pass IBM CRD list to `genericMustGather()` for IBM resource discovery

- [x] **1.4** Update `python/src/mas/cli/must_gather/common/ibm_resources.py`
  - [x] Modify `getIBMCRDs()` to accept optional pre-computed IBM CRD list
  - [x] If list provided, use it instead of fetching from cluster
  - [x] Maintain backward compatibility for direct calls

- [x] **1.5** Add unit tests
  - [x] Create `tests/src/must_gather/common/test_crd_processor.py`
  - [x] Test CRD loading and parsing
  - [x] Test IBM CRD identification
  - [x] Test printer column extraction
  - [x] Test JSONPath extraction with various patterns
  - [x] Test fallback mappings for built-in resources
  - [x] Mock CRD structures (IBM, Strimzi, MongoDB, Cert-Manager)
  - [x] Test CRD YAML file generation

- [x] **1.6** Validation
  - [x] Run: `.venv/bin/pytest tests/src/must_gather/common/test_crd_processor.py -v`
  - [x] Verify CRDs are written to `_cluster/customresourcedefinitions.yaml`
  - [x] Verify IBM CRDs are correctly identified
  - [x] Verify printer columns are extracted for all CRDs

### Phase 2: Refactor Summary Writing to Markdown
**Objective**: Replace `_writeSummary()` with `_writeMarkdownIndex()` using printer columns

- [x] **2.1** Update `python/src/mas/cli/must_gather/common/resources.py`
  - [x] Import `getPrinterColumns` and `extractValueFromJsonPath` from printer_columns module
  - [x] Rename `_writeSummary()` to `_writeMarkdownIndex()`
  - [x] Update function signature to accept `kind` and `apiVersion` parameters
  - [x] Implement markdown table generation:
    - [x] Fetch printer columns for the resource type
    - [x] Generate markdown header: `# {Kind} ({apiVersion})`
    - [x] Generate table header row with column names
    - [x] Generate separator row with alignment
    - [x] Generate data rows by extracting values using JSONPath
  - [x] Handle empty resource lists gracefully
  - [x] Update docstrings

- [x] **2.2** Update `collectResources()` function
  - [x] Change summary file path from `{resourceType}.txt` to `{resourceType}.md`
  - [x] Pass `kind` and `apiVersion` to `_writeMarkdownIndex()`
  - [x] Update docstring to reflect markdown output

- [x] **2.3** Add unit tests for markdown generation
  - [x] Create `tests/src/must_gather/common/test_resources_markdown.py`
  - [x] Test markdown header generation
  - [x] Test table generation with CRD printer columns
  - [x] Test table generation with fallback columns
  - [x] Test default behavior (name only when no columns)
  - [x] Test empty resource lists
  - [x] Test various JSONPath patterns

- [x] **2.4** Validation
  - [x] Run: `.venv/bin/pytest tests/src/must_gather/common/test_resources_markdown.py -v`
  - [x] Manually inspect generated markdown files
  - [x] Compare with `kubectl get` output for consistency
  - [x] Ensure all tests pass before proceeding

### Phase 3: Remove `noDetail` Parameter
**Objective**: Remove the `noDetail` parameter from all functions

**Note**: We are skipping phase 3, 4, and 5 for now, and will make a final decision on whether to remove this parameter at a later date.

- [ ] **3.1** Update `python/src/mas/cli/must_gather/common/resources.py`
  - [ ] Remove `noDetail` parameter from `collectResources()` signature
  - [ ] Remove conditional logic based on `noDetail`
  - [ ] Always generate detailed YAML files
  - [ ] Update docstring

- [ ] **3.2** Update `python/src/mas/cli/must_gather/common/parallel.py`
  - [ ] Remove `noDetail` parameter from `collectResourcesParallel()`
  - [ ] Remove parameter passing to `collectResources()`
  - [ ] Update docstring

- [ ] **3.3** Update `python/src/mas/cli/must_gather/common/pods.py`
  - [ ] Remove `noDetail` parameter from `collectPods()`
  - [ ] Remove conditional logic based on `noDetail`
  - [ ] Always generate pod YAML and logs (if requested)
  - [ ] Update summary file to `.md` format
  - [ ] Update docstring

- [ ] **3.4** Validation
  - [ ] Run: `.venv/bin/pytest tests/src/must_gather/common/ -v`
  - [ ] Ensure all common module tests pass


### Phase 4: Update All Callers
**Objective**: Remove `noDetail` parameter from all function calls

- [ ] **4.1** Update `python/src/mas/cli/must_gather/app.py`
  - [ ] Remove `noDetail` parameter from all `collectResources()` calls
  - [ ] Remove `noDetail` parameter from all `genericMustGather()` calls
  - [ ] Remove `noDetail` parameter from all collector function calls
  - [ ] Update `genericMustGather()` signature
  - [ ] Update all method signatures that accept `noDetail`

- [ ] **4.2** Update OCP collectors
  - [ ] `python/src/mas/cli/must_gather/ocp/cluster.py`
  - [ ] `python/src/mas/cli/must_gather/ocp/nodes.py`
  - [ ] `python/src/mas/cli/must_gather/ocp/airgap.py`
  - [ ] `python/src/mas/cli/must_gather/ocp/marketplace.py`

- [ ] **4.3** Update dependency collectors
  - [ ] `python/src/mas/cli/must_gather/dependencies/utils.py`
  - [ ] `python/src/mas/cli/must_gather/dependencies/common_services.py`
  - [ ] `python/src/mas/cli/must_gather/dependencies/cp4d.py`
  - [ ] `python/src/mas/cli/must_gather/dependencies/db2.py`
  - [ ] `python/src/mas/cli/must_gather/dependencies/dro.py`
  - [ ] `python/src/mas/cli/must_gather/dependencies/cert_manager.py`
  - [ ] `python/src/mas/cli/must_gather/dependencies/kafka.py`
  - [ ] `python/src/mas/cli/must_gather/dependencies/grafana.py`
  - [ ] `python/src/mas/cli/must_gather/dependencies/mongodb.py`
  - [ ] `python/src/mas/cli/must_gather/dependencies/sls.py`

- [ ] **4.4** Update MAS collectors
  - [ ] `python/src/mas/cli/must_gather/mas/apps.py`
  - [ ] `python/src/mas/cli/must_gather/mas/pipelines.py`

- [ ] **4.5** Update other collectors
  - [ ] `python/src/mas/cli/must_gather/argo/applications.py`
  - [ ] `python/src/mas/cli/must_gather/aiservice/instance.py`
  - [ ] `python/src/mas/cli/must_gather/aiservice/pipelines.py`

- [ ] **4.6** Validation
  - [ ] Run: `.venv/bin/pytest tests/src/must_gather/ -v`
  - [ ] Fix any test failures related to parameter changes

### Phase 5: Update Command-Line Interface
**Objective**: Remove `--summary-only` flag and related logic

- [ ] **5.1** Update `python/src/mas/cli/must_gather/arg_parser.py`
  - [ ] Remove `--summary-only` argument definition
  - [ ] Update help text if needed

- [ ] **5.2** Update `python/src/mas/cli/must_gather/app.py`
  - [ ] Remove all references to `parsedArgs.summary_only`
  - [ ] Remove conditional logic based on summary_only flag

- [ ] **5.3** Validation
  - [ ] Run: `python -m mas.cli.must_gather --help`
  - [ ] Verify `--summary-only` is no longer listed

### Phase 6: Expand Fallback Printer Columns
**Objective**: Add comprehensive fallback printer columns for built-in Kubernetes resources

- [x] **6.1** Add fallback columns for all standard Kubernetes resources
  - [x] Pod: Ready, Status, Restarts, Age
  - [x] Deployment: Ready, Up-to-Date, Available, Age
  - [x] Service: Type, Cluster-IP, External-IP, Port(s), Age
  - [x] StatefulSet: Ready, Age
  - [x] DaemonSet: Desired, Current, Ready, Up-to-Date, Available, Age
  - [x] ReplicaSet: Desired, Current, Ready, Age
  - [x] Job: Completions, Duration, Age
  - [x] CronJob: Schedule, Suspend, Active, Last Schedule, Age
  - [x] PersistentVolumeClaim: Status, Volume, Capacity, Access Modes, Storage Class, Age
  - [x] ConfigMap, Secret: Data, Age
  - [x] ServiceAccount: Secrets, Age
  - [x] Ingress: Class, Hosts, Address, Ports, Age

- [x] **6.2** Add fallback columns for OCP-specific resources
  - [x] Node: Status, Roles, Age, Version
  - [x] ClusterVersion: Version, Available, Progressing, Since, Status
  - [x] StorageClass: Provisioner, Reclaim Policy, Volume Binding Mode, Age
  - [x] Namespace: Status, Age

- [x] **6.3** Add fallback columns for operator resources
  - [x] CatalogSource: Display, Type, Publisher, Age
  - [x] Subscription: Package, Source, Channel, Age
  - [x] InstallPlan: CSV, Approval, Approved
  - [x] ClusterServiceVersion: Display, Version, Replaces, Phase
  - [x] PackageManifest: Name, Catalog, Age

- [x] **6.4** Note on ALL custom resources
  - **ALL CRDs** (IBM, Strimzi, MongoDB, Cert-Manager, etc.) automatically use their `additionalPrinterColumns`
  - Examples that will work automatically:
    - IBM: Suite, WorkspaceConfig, BasCfg, JdbcCfg, SlsCfg, etc.
    - Strimzi: Kafka, KafkaTopic, KafkaUser, KafkaConnect, etc.
    - MongoDB: MongoDBCommunity
    - Cert-Manager: Certificate, Issuer, ClusterIssuer
    - Any other CRDs in the cluster
  - No manual mapping needed - this is the key advantage of the CRD-based approach

- [ ] **6.5** Validation
  - [ ] Run full must-gather collection on test cluster
  - [ ] Verify `_cluster/customresourcedefinitions.yaml` exists and contains all CRDs
  - [ ] Compare markdown tables with `kubectl get -o wide` output
  - [ ] Verify IBM CRD tables match `oc get <crd>` output
  - [ ] Verify tables are properly formatted and informative
  - [ ] Test with `--no-ocp` flag to ensure CRDs are still processed

### Phase 7: Fix Summary Generation (Added 2026-06-05)
**Objective**: Update summarizer to read markdown index files and adjust paths for summary.md

**Context**: After implementing markdown index generation, the summarizer was still trying to read `.txt` files that no longer exist. The solution is to read the generated `.md` files, convert H1 headers to H2, and adjust relative paths for inclusion in the root `summary.md`.

- [x] **7.1** Add markdown links to resource names in index files
  - [x] Modify `_writeMarkdownIndex()` in `resources.py` to convert first column (name) to markdown links
  - [x] Links format: `[name](pluralKind/name.yaml)` relative to the index file location
  - [x] Add tests in `test_resources_markdown_links.py` to verify link generation
  - [x] Verify links use plural form of kind (e.g., `pods/`, `suites/`, `catalogsources/`)
  - [x] Run tests and validate with black/flake8

- [x] **7.2** Update summarizer to read .md files instead of .txt files
  - [x] Create helper functions `_adjustMarkdownPaths()` and `_convertHeaderLevel()`
  - [x] Update `cluster.processClusterVersion()` to read `clusterversions.md`
  - [x] Update `catalogs.summarize()` to read `catalogsources.md`
  - [x] Remove obsolete functions that processed `.txt` files and built PrettyTables
  - [x] Add tests in `test_markdown_integration.py` to verify markdown reading

- [x] **7.3** Adjust relative paths when including markdown in summary.md
  - [x] Implement path adjustment in `_adjustMarkdownPaths()` using regex
  - [x] Convert paths like `[text](path/file.yaml)` to `[text](resources/_cluster/path/file.yaml)`
  - [x] Test path adjustment for both cluster and catalog resources
  - [x] Verify H1 to H2 header conversion works correctly

- [x] **7.4** Validation
  - [x] Run: `.venv/bin/pytest python/tests/must_gather/summarizer/ -v`
  - [x] Run: `.venv/bin/pytest python/tests/must_gather/common/test_resources_markdown*.py -v`
  - [x] Verify all 13 tests pass (5 summarizer + 8 resources)
  - [x] Run black and flake8 on modified files
  - [x] Update plan document with completion status

### Phase 8: Remove Redundant Summary Generation (Added 2026-06-05)
**Objective**: Remove the now-redundant summary.md generation since resource index files are already in markdown format

**Context**: With markdown index files generated for all resources, the summary.md aggregation is redundant. The subscriptions summary is still useful as a cluster-wide view, so we'll keep only that and write it directly to `resources/_cluster/subscriptions.md`.

- [x] **8.1** Remove summary.md generation from app.py
  - [x] Remove `generateSummary()` method from `MustGatherApp` class
  - [x] Add `generateSubscriptionsSummary()` method to generate only subscriptions summary
  - [x] Update main workflow to call new subscriptions-only method
  - [x] Remove unused imports (subprocess)

- [x] **8.2** Update subscriptions summarizer to write to resources/_cluster/subscriptions.md
  - [x] Modify `summarize()` in `subscriptions.py` to write directly to `resources/_cluster/subscriptions.md`
  - [x] Change return type from string to None (no longer used for aggregation)
  - [x] Generate unified table aggregating subscriptions from all namespaces

- [x] **8.3** Remove cluster and catalogs summarizers (no longer needed)
  - [x] Remove `generateSummary()` function from `summarizer/__init__.py`
  - [x] Remove imports for cluster, catalogs, and subscriptions modules
  - [x] Simplify to minimal module docstring

- [x] **8.4** Validation
  - [x] Run: `.venv/bin/pytest python/tests/must_gather/ -v`
  - [x] Verify subscriptions.md is generated correctly
  - [x] Verify summary.md is no longer created
  - [x] Run black and flake8 on modified files

### Phase 9: Fix CRD Storage Pattern (Added 2026-06-05)
**Objective**: Store CRDs in individual files with markdown index, matching the pattern used for other resources

**Context**: Currently all CRDs are written to a single massive file (`customresourcedefinitions.yaml` - 460k lines). This should follow the same pattern as other resources: individual files in `customresourcedefinitions/` directory with a markdown index file.

- [x] **9.1** Update CRD processor to write individual CRD files
  - [x] Modify `processCRDs()` in `crd_processor.py` to create `customresourcedefinitions/` directory
  - [x] Write each CRD to `customresourcedefinitions/{crd_name}.yaml`
  - [x] Remove old single-file YAML generation

- [x] **9.2** Generate customresourcedefinitions.md index file
  - [x] Create `_writeCRDMarkdownIndex()` function to generate markdown table
  - [x] Include columns: Name (as link), Group, Age
  - [x] Write to `resources/_cluster/customresourcedefinitions.md`

- [x] **9.3** Update tests and validate
  - [x] Create `test_crd_processor_individual_files.py` with 3 new tests
  - [x] Update existing test in `test_crd_processor.py` to expect new file structure
  - [x] Run: `.venv/bin/pytest python/tests/must_gather/common/test_crd_processor*.py -v`
  - [x] Verify all 13 tests pass (10 existing + 3 new)
  - [x] Run black and flake8 on modified files
  - [x] Remove unused imports

### Phase 10: Fix Resource Output Path Bugs (Added 2026-06-05)
**Objective**: Fix path inconsistencies causing resources to be written to wrong directories

**Context**: Two related bugs were discovered in resource collection:
1. **IBM resources path duplication**: IBM resources were being written to `resources/resources/namespace/` instead of `resources/namespace/` due to duplicate path concatenation in `collectResourcesParallel()`.
2. **Standard resources missing /resources prefix**: Standard Kubernetes resources (configmaps, deployments, etc.) were being written to `namespace/` instead of `resources/namespace/` due to inconsistent path handling in `genericMustGather()`.

#### Bug 1: IBM Resources Path Duplication

- [x] **10.1** Fix path duplication in parallel.py
  - [x] Remove duplicate `/resources` concatenation in `collectResourcesParallel()`
  - [x] Change line 58 from `resourcesOutputDir = f"{outputDir}/resources"` to use `outputDir` directly
  - [x] Update line 72 to pass `outputDir` instead of `resourcesOutputDir` to `collectResources()`

- [x] **10.2** Create regression tests
  - [x] Create `test_parallel_output_path.py` with 2 tests
  - [x] Test that resources are written to correct directory without path duplication
  - [x] Test that IBM resources specifically go to correct path
  - [x] Verify files do NOT exist in wrong location (with duplicate `/resources/`)

- [x] **10.3** Update existing tests
  - [x] Fix `test_parallel.py` tests that expected the buggy behavior
  - [x] Update `test_collectResourcesParallel_collects_multiple_resources_successfully`
  - [x] Update `test_collectResourcesParallel_with_noDetail_flag`
  - [x] Change expected `outputDir` from `f"{outputDir}/resources"` to `outputDir`

#### Bug 2: Standard Resources Missing /resources Prefix

- [x] **10.4** Fix inconsistent path handling in app.py
  - [x] Update `genericMustGather()` line 345 to add `/resources` prefix
  - [x] Change from `outputDir=outputDir` to `outputDir=f"{outputDir}/resources"`
  - [x] This makes standard resources consistent with IBM resources (line 295) and secrets (line 360)

- [x] **10.5** Validation
  - [x] Run: `.venv/bin/pytest python/tests/must_gather/common/test_parallel*.py -v`
  - [x] Verify all 8 tests pass (6 existing + 2 new)
  - [x] Run black and flake8 on modified files
  - [x] Verify both IBM and standard resources now appear in correct location: `resources/namespace/`

## Final Validation

- [ ] **Run complete test suite**
  - [ ] `.venv/bin/pytest tests/ -v`
  - [ ] All tests must pass

- [ ] **Run black and flake8**
  - [ ] `black python/src/mas/cli/must_gather/ --line-length 160`
  - [ ] `flake8 python/src/mas/cli/must_gather/`
  - [ ] Fix any formatting or linting issues

- [ ] **Integration test**
  - [ ] Run full must-gather on test cluster
  - [ ] Verify all `.md` files are generated correctly
  - [ ] Verify no `.txt` files are created
  - [ ] Verify detailed YAML files are still generated
  - [ ] Verify pod logs are still collected

- [ ] **Documentation update**
  - [ ] Update any documentation referencing `.txt` summary files
  - [ ] Update examples showing markdown format
  - [ ] Document the field mapping system for future maintainers
