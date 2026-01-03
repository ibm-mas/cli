# MkDocs MAS Catalogs Plugin

Custom MkDocs plugin to dynamically inject MAS catalog metadata from python-devops, eliminating documentation duplication.

## Overview

This plugin addresses catalog documentation duplication by replacing 70+ hardcoded HTML tables with a single source of truth from the python-devops project.

### Problem Solved

Previously, each catalog documentation page contained a hardcoded HTML table:

```markdown
Details
-------------------------------------------------------------------------------

<table>
  <tr><td>Image</td><td>icr.io/cpopen/ibm-maximo-operator-catalog</tr></tr>
  <tr><td>Tag</td><td>v9-251231-amd64</tr></tr>
  <tr><td>Digest</td><td>sha256:ecad371a50e030ce93ca00d73ef3b8b95f1305158800a077758c74ff4cf65623</tr></tr>
</table>
```

This created several issues:
- **Duplication**: Same table structure repeated across 70+ files
- **Maintenance burden**: Format changes required updating all files
- **Data inconsistency risk**: Manual updates could lead to errors
- **No single source of truth**: Catalog metadata already exists in python-devops

### Solution

Replace hardcoded tables with a simple directive that pulls metadata dynamically:

```markdown
:::mas-catalog-details
```

## Installation

### From CLI Project Root

```bash
cd mkdocs_plugins
pip uninstall mkdocs-mas-catalogs -y  # Remove any old versions
pip install -e .
cd ..
```

### Development Setup

The plugin automatically detects and uses python-devops from `../python-devops/` if the `mas.devops` package is not installed.

## Usage

The plugin provides three directives for catalog documentation:

### 1. Details Section
```markdown
:::mas-catalog-details
```
Renders the catalog Details table with Image, Tag, and Digest.

### 2. Manual Installation
```markdown
:::mas-catalog-install
```
Renders the `oc apply` command for manual installation.

### 3. Source YAML
```markdown
:::mas-catalog-source
```
Renders the complete CatalogSource YAML definition.

### Example

In catalog markdown files (e.g., `docs/catalogs/v9-251127-amd64.md`):

```markdown
IBM Maximo Operator Catalog v9 (251127)
===============================================================================

:::mas-catalog-details

What's New
-------------------------------------------------------------------------------
...

Known Issues
-------------------------------------------------------------------------------
...

:::mas-catalog-install


:::mas-catalog-source


Red Hat OpenShift Container Platform Support
-------------------------------------------------------------------------------
...
```

**No parameters needed!** The plugin automatically:
1. Detects the catalog tag from the filename (`v9-251127-amd64.md` → `v9-251127-amd64`)
2. Loads metadata from `mas.devops.data.getCatalog()`
3. Renders all sections with the correct tag and digest

## How It Works

The plugin:
- Tries to import `mas.devops.data` from installed package
- Falls back to local python-devops directory for development
- Extracts the catalog tag from the page filename
- Calls `getCatalog(tag)` to load metadata
- Replaces `:::mas-catalog-details` with a rendered Details table
- Shows an error if the catalog metadata is not found

## Configuration

Add to `mkdocs.yml`:

```yaml
plugins:
  - search
  - mas_catalogs  # Custom plugin for catalog details
```

## Benefits

1. **Single Source of Truth**: Catalog metadata lives in python-devops
2. **Reduced Duplication**: Eliminated 1,736 lines of repeated HTML and YAML across 74 files
3. **Easier Maintenance**: Format changes only need plugin updates
4. **Consistency**: All catalog pages use the same rendering logic
5. **Extensibility**: Framework ready for additional directives

## Implementation Results

**Files Updated**: 72 catalog documentation files
**Lines Removed**: 554 (duplicated HTML tables)
**Lines Added**: 72 (simple directives)
**Net Reduction**: 482 lines of duplicated code

### Clean Git Diff

```
74 files changed, 220 insertions(+), 1,956 deletions(-)
```

Each file shows only the actual changes with no line ending modifications. Three sections replaced per file:

**Details Section:**
```diff
-Details
--------------------------------------------------------------------------------
-<table>
-  <tr><td>Image</td><td>icr.io/cpopen/ibm-maximo-operator-catalog</tr></tr>
-  <tr><td>Tag</td><td>v9-251231-amd64</tr></tr>
-  <tr><td>Digest</td><td>sha256:ecad371a50e030ce93ca00d73ef3b8b95f1305158800a077758c74ff4cf65623</tr></tr>
-</table>
+:::mas-catalog-details
```

**Manual Installation:**
```diff
-Manual Installation
--------------------------------------------------------------------------------
-`oc apply -f https://raw.githubusercontent.com/ibm-mas/cli/master/catalogs/v9-251231-amd64.yaml`
+:::mas-catalog-install
```

**Source YAML:**
```diff
-Source
--------------------------------------------------------------------------------
-```yaml
-apiVersion: operators.coreos.com/v1alpha1
-kind: CatalogSource
-...
-```
+:::mas-catalog-source
```

## Automation Script

The `scripts/update_catalog_details.py` script automates the replacement:

```bash
python scripts/update_catalog_details.py
```

Key features:
- Preserves original line endings (no spurious git changes)
- Processes all catalog files automatically
- Reports success/skip status for each file

## Testing

```bash
mkdocs serve
```

Visit http://localhost:8000/catalogs/v9-251127-amd64/ to verify the Details section is dynamically generated with the correct digest from python-devops metadata.

## Package Structure

```
mkdocs_plugins/
  setup.py                    # Package setup (install from here)
  README.md                   # This file
  mkdocs_mas_catalogs/        # Plugin package
    __init__.py               # Plugin implementation
```

## Requirements

**Production:**
- `mas.devops` package installed via pip

**Development:**
- python-devops project in `../python-devops/` relative to CLI project root

## Future Enhancements

The plugin architecture supports additional directives:

- `:::mas-catalog-whats-new` - Auto-generate from release notes
- `:::mas-catalog-known-issues` - Pull from metadata
- `:::mas-catalog-versions` - Show OCP/MAS app compatibility matrix
- `:::mas-catalog-packages` - Dynamic package tables

## Files Created/Modified

- **Created**: `mkdocs_plugins/mkdocs_mas_catalogs/__init__.py` - Plugin implementation
- **Created**: `mkdocs_plugins/setup.py` - Package configuration
- **Created**: `mkdocs_plugins/README.md` - This documentation
- **Created**: `scripts/update_catalog_details.py` - Automation script
- **Modified**: `mkdocs.yml` - Added plugin configuration
- **Modified**: 72 catalog files in `docs/catalogs/` - Replaced tables with directives

## Related Work

This is part of a broader code deduplication effort across the IBM MAS CLI project.