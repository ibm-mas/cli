# Code Deduplication Plan for IBM MAS CLI Project

## Executive Summary

This document outlines a comprehensive plan to address code duplication across the IBM MAS CLI project. The analysis identified duplication in multiple areas: Tekton pipelines/tasks, catalog documentation, RBAC configurations, and Python CLI code.

**Current Status**: Catalog documentation deduplication is **IN PROGRESS** with significant achievements:
- ✅ Phase 1: Details tables (72 files, 554 lines removed)
- ✅ Phase 2: Install commands & CatalogSource YAML (74 files, 1,736 net lines removed)
- 🔄 Phase 3: OCP compatibility matrix (pending)

---

## 1. Catalog Documentation Deduplication

### Status: IN PROGRESS (75% Complete)

### Problem
74 catalog documentation files (`docs/catalogs/*.md`) contained hardcoded metadata that duplicated information from the sibling `python-devops` project:
- Details tables (digest, versions, dependencies)
- Installation commands
- CatalogSource YAML configurations
- OCP compatibility matrices

### Solution Implemented
Created custom MkDocs plugin (`mkdocs-mas-catalogs`) that dynamically injects catalog metadata at documentation build time using directive-based syntax.

### Completed Work

#### Phase 1: Details Tables ✅
- **Directive**: `:::mas-catalog-details`
- **Impact**: 72 files updated, 554 lines removed
- **Benefit**: Catalog metadata (digest, versions, dependencies) now pulled from single source

#### Phase 2: Installation & Source ✅
- **Directives**:
  - `:::mas-catalog-install` - Replaces installation commands
  - `:::mas-catalog-source` - Replaces CatalogSource YAML
- **Impact**: 74 files updated, 1,956 lines removed, 220 lines added (net: -1,736 lines)
- **Benefit**: Installation procedures and YAML configs centrally managed

### Remaining Work

#### Phase 3: OCP Compatibility Matrix 🔄
- **Directive**: `:::mas-catalog-ocp-compatibility-matrix`
- **Scope**: Catalogs from v9-250109 onwards (older catalogs lack metadata)
- **Requirements**:
  1. Create `../python-devops/src/mas/devops/data/ocp.yaml` with OCP lifecycle data:
     ```yaml
     ocp_versions:
       "4.19":
         ga_date: "June 17, 2025"
         standard_support: "December 17, 2026"
         extended_support: "N/A"
       "4.18":
         ga_date: "February 25, 2025"
         standard_support: "GA of 4.19 + 3 Months"
         extended_support: "August 25, 2026"
       # ... etc
     ```
  2. Update plugin to load OCP lifecycle data and render matrix table
  3. Create selective update script (only v9-250109+)
  4. Update documentation

- **Estimated Impact**: ~30 files, ~900 lines removed
- **Priority**: HIGH (completes catalog deduplication initiative)

### Benefits Achieved
- **Maintainability**: Single source of truth for catalog metadata
- **Consistency**: Automated generation prevents documentation drift
- **Efficiency**: Updates to python-devops automatically reflect in docs
- **Reduced Errors**: No manual synchronization needed

### Files Modified
- `mkdocs_plugins/mkdocs_mas_catalogs/__init__.py` - Plugin implementation
- `mkdocs_plugins/setup.py` - Package configuration
- `mkdocs_plugins/README.md` - Documentation
- `mkdocs.yml` - Plugin registration
- `scripts/update_catalog_details.py` - Phase 1 automation
- `scripts/update_catalog_directives.py` - Phase 2 automation
- `docs/catalogs/*.md` - 74 catalog files updated

---

## 2. Tekton Pipeline & Task Duplication

### Status: NOT STARTED

### Problem
Extensive duplication in Tekton YAML files generated from Jinja2 templates:

#### 2.1 Parameter Definitions
**Location**: `tekton/src/params/*.yml.j2`

**Duplication Pattern**: Common parameters repeated across multiple templates:
- `mas_instance_id`, `mas_workspace_id`, `mas_workspace_name`
- `mas_config_dir`, `mas_app_channel`, `mas_app_id`
- Git-related parameters (repo, branch, credentials)
- Catalog parameters (source, digest, tag)

**Example Files**:
- `install-common.yml.j2` - 50+ common parameters
- `install-workspace.yml.j2` - Workspace-specific parameters
- `gitops-common.yml.j2` - GitOps parameters
- Multiple app-specific files repeating similar patterns

**Proposed Solution**:
1. Create parameter fragment templates:
   - `params/fragments/mas-instance.yml.j2`
   - `params/fragments/mas-workspace.yml.j2`
   - `params/fragments/git-config.yml.j2`
   - `params/fragments/catalog-config.yml.j2`
2. Use Jinja2 `{% include %}` to compose parameter lists
3. Maintain app-specific parameters in individual files

**Estimated Impact**:
- Reduce ~2,000 lines of duplicated parameter definitions
- Improve consistency across 30+ parameter files

#### 2.2 Task Definitions
**Location**: `tekton/src/tasks/**/*.yml.j2`

**Duplication Pattern**: Common task structures repeated:
- CLI environment setup tasks (`cli-env.yml.j2`, `cli-env-nosuitename.yml.j2`)
- Wait/polling tasks (`wait-for-configmap.yml.j2`, `wait-for-tekton.yml.j2`)
- Update tasks (`update-configmap.yml.j2`, `update-pipeline-status.yml.j2`)

**Proposed Solution**:
1. Create base task templates with configurable sections
2. Use Jinja2 macros for common task patterns:
   ```jinja2
   {% macro cli_setup(suite_name_required=true) %}
   # Common CLI setup steps
   {% endmacro %}
   ```
3. Consolidate similar tasks where appropriate

**Estimated Impact**:
- Reduce ~1,500 lines across 100+ task files
- Standardize task structure

#### 2.3 Pipeline Structures
**Location**: `tekton/src/pipelines/**/*.yml.j2`

**Duplication Pattern**: Similar pipeline structures for different apps:
- FVT pipelines (`mas-fvt-*.yml.j2`) - 15+ files with similar structure
- GitOps pipelines (`gitops/gitops-*.yml.j2`) - 20+ files
- Install/upgrade/rollback patterns repeated

**Proposed Solution**:
1. Create pipeline template macros for common patterns:
   - FVT pipeline structure
   - GitOps pipeline structure
   - Install/upgrade/rollback patterns
2. Use Jinja2 inheritance for pipeline families
3. Keep app-specific logic in dedicated sections

**Estimated Impact**:
- Reduce ~3,000 lines across 50+ pipeline files
- Improve pipeline consistency

### Priority: MEDIUM
**Rationale**: While significant duplication exists, the Jinja2 template system already provides some abstraction. Focus on catalog documentation first (higher ROI), then tackle Tekton refactoring.

---

## 3. RBAC Configuration Duplication

### Status: NOT STARTED

### Problem
**Location**: `rbac/install/pipeline/*.yaml`

**Duplication Pattern**: Similar ClusterRole definitions with slight variations:
- `clusterrole.yaml` - Base permissions
- `clusterrole-dro.yaml` - DRO-specific permissions
- `clusterrole-grafana5.yaml` - Grafana permissions
- `clusterrole-mas-x-core.yaml` - MAS core permissions
- `clusterrole-mongoce.yaml` - MongoDB permissions

Each file contains:
- Similar rule structures
- Overlapping API groups
- Repeated resource types

**Proposed Solution**:

#### Option A: Kustomize Composition (Recommended)
1. Create base ClusterRole with common permissions
2. Use Kustomize patches for component-specific additions
3. Structure:
   ```
   rbac/install/pipeline/
   ├── base/
   │   ├── kustomization.yaml
   │   └── clusterrole-base.yaml
   ├── overlays/
   │   ├── dro/
   │   ├── grafana/
   │   ├── mas-core/
   │   └── mongoce/
   ```

#### Option B: Template Generation
1. Create YAML template with common structure
2. Use Python/Jinja2 to generate specific ClusterRoles
3. Maintain component-specific rules in data files

**Estimated Impact**:
- Reduce ~500 lines of duplicated RBAC rules
- Improve maintainability of permission sets
- Easier security auditing

**Priority**: LOW
**Rationale**: RBAC files are relatively stable and duplication is manageable. Focus on higher-impact areas first.

---

## 4. Python CLI Code Duplication

### Status: NOT STARTED

### Problem
**Location**: `python/src/` (CLI scripts)

**Duplication Pattern**: Common patterns in CLI scripts:
- Argument parsing setup
- Logging configuration
- Error handling
- Environment variable loading
- Configuration file reading

**Analysis Needed**: Detailed code review required to identify specific duplication patterns.

**Proposed Solution**:
1. Create shared utility modules:
   - `cli_utils.py` - Common CLI setup functions
   - `config_loader.py` - Configuration management
   - `error_handlers.py` - Standardized error handling
2. Refactor CLI scripts to use shared utilities
3. Maintain script-specific logic separately

**Estimated Impact**: TBD (requires detailed analysis)

**Priority**: LOW
**Rationale**: Python code is more maintainable than YAML/documentation. Focus on documentation and configuration duplication first.

---

## 5. Implementation Roadmap

### Phase 1: Complete Catalog Documentation ✅ (Mostly Done)
**Timeline**: 1-2 days
**Status**: 75% complete

- [x] Implement Details directive
- [x] Implement Install directive
- [x] Implement Source directive
- [ ] Create OCP lifecycle data file in python-devops
- [ ] Implement OCP matrix directive
- [ ] Create selective update script
- [ ] Update documentation
- [ ] Test and validate

**Deliverables**:
- Complete catalog documentation deduplication
- ~2,700 total lines removed
- Single source of truth for all catalog metadata

### Phase 2: Tekton Parameter Consolidation
**Timeline**: 1-2 weeks
**Status**: Not started

1. Analyze parameter usage across all templates
2. Design fragment structure
3. Create parameter fragment templates
4. Update parameter files to use fragments
5. Regenerate Tekton YAML files
6. Test pipeline functionality
7. Document new structure

**Deliverables**:
- Consolidated parameter definitions
- ~2,000 lines reduced
- Improved parameter consistency

### Phase 3: Tekton Task Refactoring
**Timeline**: 2-3 weeks
**Status**: Not started

1. Identify common task patterns
2. Create task macros and base templates
3. Refactor task definitions
4. Test task execution
5. Update documentation

**Deliverables**:
- Standardized task structure
- ~1,500 lines reduced
- Reusable task components

### Phase 4: Tekton Pipeline Refactoring
**Timeline**: 2-3 weeks
**Status**: Not started

1. Analyze pipeline families
2. Design pipeline template hierarchy
3. Create pipeline macros
4. Refactor pipeline definitions
5. Test end-to-end pipelines
6. Update documentation

**Deliverables**:
- Consistent pipeline structure
- ~3,000 lines reduced
- Maintainable pipeline families

### Phase 5: RBAC Consolidation (Optional)
**Timeline**: 1 week
**Status**: Not started

1. Analyze RBAC requirements
2. Design Kustomize structure
3. Create base and overlays
4. Test RBAC functionality
5. Update documentation

**Deliverables**:
- Consolidated RBAC definitions
- ~500 lines reduced
- Easier permission management

### Phase 6: Python CLI Refactoring (Optional)
**Timeline**: 2-3 weeks
**Status**: Not started

1. Detailed code analysis
2. Design utility module structure
3. Create shared utilities
4. Refactor CLI scripts
5. Test CLI functionality
6. Update documentation

**Deliverables**:
- Reusable CLI utilities
- Improved code maintainability
- Standardized error handling

---

## 6. Success Metrics

### Quantitative Metrics
- **Lines of Code Reduced**: Target 8,000+ lines across all phases
- **File Count Reduced**: Consolidate where appropriate
- **Duplication Ratio**: Measure with tools like `jscpd` or `duplo`
- **Build Time**: Should remain stable or improve
- **Test Coverage**: Maintain or improve current coverage

### Qualitative Metrics
- **Maintainability**: Easier to update common patterns
- **Consistency**: Reduced drift between similar components
- **Documentation**: Clearer structure and relationships
- **Developer Experience**: Faster onboarding, easier contributions
- **Error Reduction**: Fewer synchronization errors

---

## 7. Risk Assessment

### Low Risk
- **Catalog Documentation** (Phase 1): Isolated changes, automated testing possible
- **RBAC Consolidation** (Phase 5): Well-defined scope, easy to validate

### Medium Risk
- **Tekton Parameters** (Phase 2): Affects many files but changes are mechanical
- **Python CLI** (Phase 6): Requires careful refactoring but has test coverage

### High Risk
- **Tekton Tasks** (Phase 3): Core functionality, extensive testing required
- **Tekton Pipelines** (Phase 4): Complex dependencies, end-to-end testing critical

### Mitigation Strategies
1. **Incremental Changes**: Complete one phase before starting next
2. **Automated Testing**: Expand test coverage before refactoring
3. **Validation Scripts**: Create scripts to verify generated YAML
4. **Rollback Plan**: Maintain ability to revert changes
5. **Documentation**: Document all changes and new patterns
6. **Code Review**: Require thorough review of all changes

---

## 8. Recommendations

### Immediate Actions (Next 2 Weeks)
1. ✅ **Complete Phase 1**: Finish OCP compatibility matrix directive
2. **Document Success**: Create case study of catalog deduplication
3. **Plan Phase 2**: Detailed analysis of Tekton parameter duplication

### Short-term (1-3 Months)
1. **Execute Phase 2**: Tekton parameter consolidation
2. **Execute Phase 3**: Tekton task refactoring
3. **Establish Patterns**: Document best practices for avoiding duplication

### Long-term (3-6 Months)
1. **Execute Phase 4**: Tekton pipeline refactoring
2. **Consider Phase 5**: RBAC consolidation if time permits
3. **Consider Phase 6**: Python CLI refactoring if needed
4. **Continuous Improvement**: Regular duplication audits

### Best Practices Going Forward
1. **Single Source of Truth**: Always prefer data-driven generation
2. **Template Reuse**: Use Jinja2 includes/macros for common patterns
3. **Code Review**: Check for duplication in all PRs
4. **Documentation**: Document why patterns exist and how to use them
5. **Automation**: Create tools to detect and prevent duplication

---

## 9. Conclusion

The IBM MAS CLI project has significant code duplication, particularly in:
1. **Catalog documentation** (75% resolved, high impact)
2. **Tekton configurations** (not started, high volume)
3. **RBAC definitions** (not started, low priority)
4. **Python CLI code** (not started, needs analysis)

The catalog documentation deduplication initiative demonstrates the value of this work:
- **2,290 lines removed** so far (with 900 more pending)
- **Single source of truth** established
- **Automated generation** prevents future drift
- **Improved maintainability** for 74 files

Continuing this effort across Tekton configurations could yield similar benefits, with an estimated **6,500+ additional lines** of duplication that could be eliminated.

**Recommended Priority**:
1. **HIGH**: Complete catalog documentation (Phase 1)
2. **MEDIUM**: Tekton parameter consolidation (Phase 2)
3. **MEDIUM**: Tekton task refactoring (Phase 3)
4. **MEDIUM**: Tekton pipeline refactoring (Phase 4)
5. **LOW**: RBAC consolidation (Phase 5)
6. **LOW**: Python CLI refactoring (Phase 6)

The phased approach allows for incremental progress with measurable results at each stage, while managing risk through careful testing and validation.