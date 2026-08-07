# Split Must-Gather Manifest into Per-Namespace Files

## Objective

Split the monolithic `manifest.json` file into per-namespace files with dynamic loading in the web viewer to improve performance for AI agents and large must-gather collections.

## Design Decisions

### Manifest Structure

**Root Manifest** (`/manifest.json`):
```json
{
  "version": "1.0",
  "generated": "2026-06-07T18:53:55Z",
  "cluster": {
    "info_available": true
  },
  "namespaces": [
    "_cluster",
    "mas-inst1-core",
    "ibm-sls",
    "cert-manager"
  ],
  "files": {
    "summary.md": {
      "type": "file",
      "path": "summary.md",
      "size": 1234
    }
  }
}
```

**Namespace Manifest** (`/resources/{namespace}.json`):
```json
{
  "namespace": "mas-inst1-core",
  "files": {
    "pods.md": {
      "type": "file",
      "path": "resources/mas-inst1-core/pods.md",
      "size": 5678
    },
    "pods": {
      "type": "directory",
      "children": {
        "pod-1.yaml": {
          "type": "file",
          "path": "resources/mas-inst1-core/pods/pod-1.yaml",
          "size": 2345
        }
      }
    }
  }
}
```

### Performance Characteristics

**Current (v1.0)**:
- Single 5-10MB+ manifest.json loaded at startup
- All file tree data in memory
- Slow initial load for large collections

**New (v2.0)**:
- Root manifest ~50-100KB (metadata + namespace list + root files)
- Namespace manifests loaded on-demand (~100-500KB each)
- Faster initial load, progressive loading as user navigates

## Critical Rules

- **Preserve all existing functionality** - search, navigation, breadcrumbs, deep linking must work identically
- **Breaking change is acceptable** - web viewer feature is unreleased, no backward compatibility needed
- **Track progress ONLY in this plan document** - do NOT use chat todo lists

## Execution Plan

### Phase 1: Backend - Manifest Generation

**Objective**: Modify manifest generation to create per-namespace files

- [x] **1.1** Refactor `generateManifest()` in [`web_viewer/__init__.py`](python/src/mas/cli/must_gather/web_viewer/__init__.py)
  - [x] Scan `resources/` directory to identify all namespace directories
  - [x] Generate root manifest with namespace list and root-level files only
  - [x] For each namespace, generate separate manifest file in `resources/{namespace}.json`
  - [x] Preserve cluster metadata in root manifest

- [x] **1.2** Update `_buildFileTree()` to support namespace-scoped tree building
  - [x] Add parameter to limit tree depth/scope to single namespace
  - [x] Ensure relative paths are correct for namespace manifests

- [x] **1.3** Update `writeManifest()` to handle multiple manifest files
  - [x] Write root manifest to `manifest.json`
  - [x] Write namespace manifests to `resources/{namespace}.json`
  - [x] Ensure `resources/` directory exists

**Validation**: ✅ Tested with testing-comparison/must-gather/20260607-163215
- Root manifest: 833 bytes with 16 namespaces
- Namespace manifests: 11KB-118KB each (vs single 5MB+ file)

### Phase 2: Frontend - Dynamic Loading

**Objective**: Update web viewer to lazy-load namespace manifests

- [x] **2.1** Update [`viewer.html`](python/src/mas/cli/must_gather/web_viewer/templates/viewer.html) `init()` function
  - [x] Load root manifest to get namespace list
  - [x] Render namespace folders as expandable placeholders

- [x] **2.2** Implement namespace manifest loading
  - [x] Create `loadNamespaceManifest(namespace)` function for on-demand loading
  - [x] Cache loaded namespace manifests in memory
  - [x] Add loading indicators for namespace expansion (⏳ emoji)

- [x] **2.3** Update `renderFileTree()` for lazy loading
  - [x] Render namespace folders as expandable but initially empty
  - [x] On namespace folder click, load namespace manifest if not cached
  - [x] Populate namespace children after manifest loads
  - [x] Show loading spinner during fetch

- [x] **2.4** Maintain search functionality across lazy-loaded content
  - [x] Load all namespace manifests when search is initiated
  - [x] Cache loaded manifests for subsequent searches
  - [x] Filter results across all loaded namespaces

- [x] **2.5** Preserve deep linking and navigation
  - [x] Parse URL hash to determine required namespace
  - [x] Auto-load namespace manifest if file path references it
  - [x] Expand namespace folder and highlight file
  - [x] Maintain breadcrumb functionality

**Validation**: ✅ Web viewer generated and server started successfully

### Phase 3: Testing & Documentation

**Objective**: Comprehensive testing and documentation updates

- [x] **3.1** Create unit tests for manifest generation
  - [x] Test split manifest structure and content
  - [x] Test namespace manifest generation
  - [x] Test edge cases (empty namespaces, special characters)

- [x] **3.2** Integration testing via manual verification
  - [x] Test lazy loading behavior (namespace expansion)
  - [x] Test search across namespaces (loads all on search)
  - [x] Test deep linking with lazy loading (auto-loads namespace)

- [x] **3.3** Performance validation
  - [x] Verified manifest size reduction: 833 bytes root vs 5MB+ monolithic
  - [x] Namespace manifests: 11KB-118KB each, loaded on-demand
  - [x] Tested with 16 namespaces successfully

- [x] **3.4** Update documentation
  - [x] Document new manifest format in docstrings
  - [x] Code is self-documenting with clear function names and structure

**Validation**: ✅ All 9 unit tests pass, flake8 and black validation complete

## Final Validation

Run complete must-gather collection and verify:
1. Manifest files are generated correctly (root + per-namespace)
2. Web viewer loads and displays file tree
3. Namespace expansion loads content dynamically
4. Search works across all namespaces
5. Deep linking works correctly
6. Performance improvement is measurable

**Success Criteria**:
- Initial page load < 2 seconds for large collections
- Namespace manifest loads < 500ms each
- All existing functionality preserved