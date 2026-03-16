# MkDocs MAS Plugins

Custom MkDocs plugins for IBM Maximo Application Suite documentation, eliminating duplication and ensuring documentation stays synchronized with code.

## Overview

This package provides two complementary plugins that dynamically generate documentation from authoritative sources:

1. **MAS Catalogs Plugin (`mas_catalogs`)** - Dynamically inject MAS catalog metadata from python-devops
2. **MAS CLI Plugin (`mas_cli`)** - Automatically generate CLI documentation from Python argparse configurations

Both plugins eliminate manual documentation maintenance and ensure content stays synchronized with code.

## Installation

### From CLI Project Root

```bash
cd mkdocs_plugins
pip uninstall mkdocs-mas-plugins -y  # Remove any old versions
pip install -e .
cd ..
```

### Package Information

**Package Name**: `mkdocs-mas-plugins`
**Version**: 0.2.0
**Plugins Included**: `mas_catalogs`, `mas_cli`

## Configuration

Add to `mkdocs.yml`:

```yaml
plugins:
  - search: {}
  - mas_catalogs  # Catalog documentation plugin
  - mas_cli       # CLI documentation plugin
  - redirects:
      ...
```

---

# MAS Catalogs Plugin

Dynamically inject MAS catalog metadata from python-devops, eliminating documentation duplication.

## Problem Solved

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

## Solution

Replace hardcoded tables with simple directives that pull metadata dynamically:

```markdown
:::mas-catalog-details
```

## Usage

The plugin provides four directives for catalog documentation:

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

### 4. OCP Compatibility Matrix
```markdown
:::mas-catalog-ocp-compatibility-matrix
```
Renders the OpenShift Container Platform compatibility matrix table with GA dates, Standard Support, and Extended Support information. This directive is only applicable to catalogs from v9-250109 onwards, as older catalogs don't have OCP compatibility metadata in python-devops.

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
For more information about the OCP lifecycle refer to the [Red Hat OpenShift Container Platform Life Cycle Policy](https://access.redhat.com/support/policy/updates/openshift/).

IBM Maximo Application Suite customers receive a standard Red Hat OpenShift Container Platform subscription as part of their purchase. This includes 18 months of maintenance support for each OpenShift minor release.  A further 6 months support is available to purchase as an Extended Update Support (EUS) Add-on to x86-64 versions of Red Hat OpenShift Kubernetes Engine, Red Hat OpenShift Container Platform, and Red Hat OpenShift Platform Plus Standard subscriptions.

:::mas-catalog-ocp-compatibility-matrix
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
- Replaces directives with rendered content
- Shows an error if the catalog metadata is not found

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

---

# MAS CLI Plugin

Automatically generate CLI documentation from Python argparse configurations, eliminating manual documentation maintenance and ensuring CLI help text stays synchronized with code.

## Problem Solved

Previously, CLI command documentation had to be manually written and maintained:

```markdown
Usage
-------------------------------------------------------------------------------
For full usage information run `mas install --help`
```

This created several issues:
- **Documentation drift**: Help text in code vs. documentation could become inconsistent
- **Maintenance burden**: Changes to CLI arguments required updating multiple locations
- **Duplication**: Same information existed in argparse and markdown files
- **No single source of truth**: The argparse configuration should be authoritative

## Solution

Replace manual documentation with a simple directive that generates comprehensive documentation from the argparse configuration:

```markdown
:::mas-cli-usage
module: mas.cli.install.argParser
parser: installArgParser
:::
```

## Usage

### Directive Syntax

```markdown
:::mas-cli-usage
module: mas.cli.install.argParser
parser: installArgParser
ignore_description: true
ignore_epilog: true
:::
```

**Parameters:**
- `module` (required): Python module path containing the ArgumentParser (e.g., `mas.cli.install.argParser`)
- `parser` (required): Variable name of the ArgumentParser instance (e.g., `installArgParser`)
- `ignore_description` (optional): If `true`, skip the description section (default: `false`)
- `ignore_epilog` (optional): If `true`, skip the epilog section (default: `false`)

### Example

In documentation files (e.g., `docs/guides/install.md`):

```markdown
Installation
===============================================================================

:::mas-cli-usage
module: mas.cli.install.argParser
parser: installArgParser
ignore_description: true
ignore_epilog: true
:::

Preparation
-------------------------------------------------------------------------------
...
```

**The plugin automatically:**
1. Imports the specified module
2. Extracts the ArgumentParser instance
3. Generates comprehensive markdown documentation with:
   - Usage synopsis
   - Description (unless ignored)
   - All argument groups as organized HTML tables
   - Type information, choices, and defaults
   - Help text for each option
   - Epilog (unless ignored)

## Generated Output

The plugin generates well-structured markdown documentation with HTML tables for precise formatting:

### Usage Section
```markdown
## Usage

```bash
mas install [OPTIONS]
```
```

### Description Section (Optional)
```markdown
### Description

IBM Maximo Application Suite Admin CLI v1.0.0
Install MAS by configuring and launching the MAS Install Tekton Pipeline.

Interactive Mode:
Omitting the --instance-id option will trigger an interactive prompt
```

### Argument Groups

Each argument group from the argparse configuration becomes a section with an HTML table:

```markdown
### MAS Catalog Selection & Entitlement

<table style="width: 100%; table-layout: fixed;">
  <colgroup>
    <col style="width: 25%;">
    <col style="width: 15%;">
    <col style="width: 15%;">
    <col style="width: 45%;">
  </colgroup>
  <thead>
    <tr>
      <th>Option</th>
      <th>Type</th>
      <th>Default</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>-c</code>, <code>--mas-catalog-version</code></td>
      <td><code>string</code></td>
      <td>-</td>
      <td>IBM Maximo Operator Catalog to install</td>
    </tr>
    ...
  </tbody>
</table>
```

### Table Columns

1. **Option**: Short and long flags (e.g., `-i`, `--mas-instance-id`)
2. **Type**:
   - `string` for string arguments
   - `{choice1,choice2}` for choice-based arguments
   - `flag` for boolean flags
   - `int` for integer arguments
3. **Default**: Default value or `-` if none
4. **Description**: Help text from argparse

## How It Works

The plugin:
1. Registers with MkDocs as `mas_cli`
2. Scans markdown files for `:::mas-cli-usage` directives
3. Parses directive parameters (module, parser name, and optional flags)
4. Dynamically imports the specified module
5. Extracts the ArgumentParser instance
6. Iterates through all argument groups
7. Generates HTML tables for each group with fixed column widths
8. Replaces the directive with formatted markdown
9. **Raises exceptions on errors to fail the build** (CI/CD friendly)

**Important**:
- The plugin tries to import from installed packages first
- Falls back to `../python/src/` for development
- **Build will fail** if the module cannot be imported or the parser is not found
- This ensures CI/CD pipelines catch documentation issues early

## Benefits

1. **Single Source of Truth**: Argparse configuration is the authoritative source
2. **Always Up-to-Date**: Documentation automatically reflects code changes
3. **Consistency**: All CLI commands documented with same format
4. **Reduced Maintenance**: No manual documentation updates needed
5. **Type Safety**: Actual types and choices from argparse
6. **Comprehensive**: All 200+ arguments automatically documented
7. **Extensibility**: Easy to add more CLI commands
8. **Precise Formatting**: HTML tables with fixed column widths for consistent appearance

## Implementation Results

**Plugin Created**: `mkdocs_mas_cli` package with 2 modules
**Lines of Code**: ~400 lines (plugin + formatter)
**Documentation Updated**: `docs/guides/install.md`
**Configuration Updated**: `mkdocs.yml`, `setup.py`

### Files Created

- `mkdocs_plugins/mkdocs_mas_cli/__init__.py` - Plugin implementation (~125 lines)
- `mkdocs_plugins/mkdocs_mas_cli/formatter.py` - Markdown/HTML formatter (~280 lines)

### Files Modified

- `mkdocs_plugins/setup.py` - Added mas_cli plugin entry point
- `mkdocs.yml` - Registered mas_cli plugin
- `docs/guides/install.md` - Replaced manual usage with directive

## Error Handling

The plugin provides clear error messages and **fails the build** for common issues:

### Module Not Found
```
ImportError: Could not import mas.cli.install.argParser.
Tried adding /path/to/python/src to sys.path.
Original error: No module named 'mas.cli'
```

### Parser Not Found
```
AttributeError: Module mas.cli.install.argParser does not have attribute 'installArgParser'
```

### Invalid Parser
```
TypeError: installArgParser is not an ArgumentParser instance
```

## Testing

### Manual Testing

1. **Install Plugin**
   ```bash
   cd mkdocs_plugins
   pip install -e .
   cd ..
   ```

2. **Build Documentation**
   ```bash
   mkdocs serve
   ```

3. **Verify Output**
   Visit http://localhost:8000/guides/install/ and verify:
   - [ ] Usage section displays correctly
   - [ ] Description is formatted properly (if not ignored)
   - [ ] All argument groups are present
   - [ ] HTML tables render with consistent column widths
   - [ ] Options are properly formatted
   - [ ] Choices display as inline code
   - [ ] Defaults show correctly
   - [ ] Help text is readable
   - [ ] Epilog appears (if not ignored)

## Extending the Plugin

### Support Multiple Commands

Document multiple CLI commands in one page:

```markdown
## Install Command
:::mas-cli-usage
module: mas.cli.install.argParser
parser: installArgParser
:::

## Update Command
:::mas-cli-usage
module: mas.cli.update.argParser
parser: updateArgParser
:::
```

### Custom Formatting Options

Use optional parameters to control output:

```markdown
:::mas-cli-usage
module: mas.cli.install.argParser
parser: installArgParser
ignore_description: true
ignore_epilog: true
:::
```

## Troubleshooting

### Issue: Plugin not registered

```bash
cd mkdocs_plugins
pip uninstall mkdocs-mas-plugins -y
pip install -e .
python -c "import mkdocs_mas_cli; print('OK')"
```

### Issue: Module dependencies missing

Ensure you're running in the correct virtual environment with all CLI dependencies installed.

### Issue: Table formatting broken

The plugin uses HTML tables with fixed column widths. If tables appear broken, check for:
- Unescaped HTML characters in help text (automatically escaped by the plugin)
- Very long option names or descriptions (may need CSS adjustments)

---

# Package Structure

```
mkdocs_plugins/
├── mkdocs_mas_cli/           # CLI documentation plugin
│   ├── __init__.py           # Plugin implementation
│   └── formatter.py          # Markdown/HTML formatting
├── mkdocs_mas_catalogs/      # Catalog documentation plugin
│   └── __init__.py           # Plugin implementation
├── setup.py                  # Package configuration
└── README.md                 # This file
```

## Requirements

**Production:**
- `mas.devops` package (for catalogs plugin)
- `mas.cli` package (for CLI plugin)
- `mkdocs >= 1.0`
- `pyyaml`

**Development:**
- python-devops project in `../python-devops/` (for catalogs plugin)
- CLI source code in `../python/src/` (for CLI plugin)

## Future Enhancements

### Catalogs Plugin
- `:::mas-catalog-whats-new` - Auto-generate from release notes
- `:::mas-catalog-known-issues` - Pull from metadata
- `:::mas-catalog-versions` - Show OCP/MAS app compatibility matrix
- `:::mas-catalog-packages` - Dynamic package tables

### CLI Plugin
- **Subcommand Documentation**: Handle argparse subparsers
- **Example Generation**: Auto-generate examples from test cases
- **Cross-References**: Link related arguments
- **Search Integration**: Enhanced search for CLI options
- **Version Tracking**: Show when options were added/deprecated
- **Validation**: Ensure all options are documented

## Contributing

When adding new content:

### For Catalog Documentation
1. Create the catalog YAML file
2. Add metadata to python-devops
3. Create markdown file with directives
4. Build and verify

### For CLI Documentation
1. Create the argparse configuration
2. Add a directive to the documentation markdown file
3. Build and verify the generated documentation
4. No manual documentation needed!

## Related Work

This is part of a broader code deduplication effort across the IBM MAS CLI project, eliminating thousands of lines of duplicated documentation and ensuring content stays synchronized with authoritative sources.

## License

These plugins are part of the IBM Maximo Application Suite CLI project and follow the same license (Eclipse Public License v1.0).

## Made with Bob

These plugins were designed and implemented with assistance from Bob, an AI coding assistant, following established MkDocs plugin patterns and best practices.