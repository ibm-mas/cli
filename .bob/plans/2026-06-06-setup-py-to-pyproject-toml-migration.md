# Migration Plan: setup.py to pyproject.toml

## Objective

Migrate the mas-cli Python package from legacy [`setup.py`](python/setup.py) to modern [`pyproject.toml`](https://peps.python.org/pep-0621/) configuration, following PEP 621 standards while maintaining full backward compatibility with existing build processes and workflows.

## Design Decisions

### Repository Structure - CONSOLIDATION APPROACH
- **Single pyproject.toml at root**: Consolidate package metadata into existing root [`pyproject.toml`](pyproject.toml)
- **Rationale**:
  - Avoids duplication between root and `python/` pyproject.toml files
  - Single source of truth for both tool configuration and package metadata
  - Simpler maintenance and less confusion
  - The `python/` directory structure is preserved via `package-dir = {"": "python/src"}`
- **UV workspace member**: Remove `tool.uv.workspace.members = ["python"]` since package is now defined at root
- **Build context**: Update workflow to build from root instead of `cd python`

### Build Backend Selection
- **Use `setuptools` with `pyproject.toml`** - Maintains compatibility with existing build infrastructure
- **Leverage `setuptools.build_meta`** as the build backend (PEP 517)
- **Keep dynamic versioning** using `setuptools-scm` or custom version extraction
- **Preserve namespace package structure** (`mas.cli`) using `setuptools` configuration

### Version Management Strategy
- **Current approach**: Version stored in [`python/src/mas/cli/__init__.py`](python/src/mas/cli/__init__.py) as `__version__ = "100.0.0"`
- **Build-time injection**: [`build-cli.yml`](.github/workflows/build-cli.yml) lines 102-107 replace version strings using `sed`
- **Two version locations**:
  1. `__init__.py`: `__version__ = "100.0.0"` → replaced with `VERSION_NOPREREL`
  2. `cli.py`: `self.version: str = "100.0.0-pre.local"` → replaced with `VERSION`
- **Migration approach**: Use `dynamic = ["version"]` with custom version provider that reads from `__init__.py`

### File Inclusion Strategy
- **Current**: [`MANIFEST.in`](python/MANIFEST.in) includes template files
- **Migration**: Convert to `tool.setuptools.package-data` in `pyproject.toml`
- **Preserve**: All template file patterns from MANIFEST.in

### Dependency Management
- **Runtime dependencies**: Move from `install_requires` to `dependencies`
- **Development dependencies**: Move from `extras_require["dev"]` to `optional-dependencies.dev`
- **Pin kubernetes==33.1.0**: Preserve version lock with comment explaining issue #2460

## Critical Rules

1. **Preserve all existing functionality** - No functional changes to the package
2. **Maintain version injection mechanism** - Build workflow must continue to work with sed replacements
3. **Keep MANIFEST.in temporarily** - Remove only after confirming package-data works correctly
4. **Validate package contents** - Ensure all templates and data files are included in built package
5. **Test both editable and wheel installs** - Verify `-e .` and `pip install dist/*.whl` work correctly
6. **Preserve namespace package structure** - `mas.cli` must remain a namespace package
7. **Track progress ONLY in this plan document** - Do NOT use chat todo lists

## Execution Plan

### Phase 1: Consolidate into Root pyproject.toml

Use the **new_task** tool to launch a subtask in **code** mode to complete this phase:

```
Consolidate mas-cli package configuration into root pyproject.toml
```

- [x] **1.1** Update root [`pyproject.toml`](pyproject.toml) with package metadata
  - [x] Set `[build-system]` with setuptools backend
  - [x] Configure `[project]` metadata from setup.py
  - [x] Set `dynamic = ["version"]` for version management
  - [x] Add all dependencies from `install_requires`
  - [x] Add dev dependencies from `extras_require["dev"]`
  - [x] Configure classifiers
  - [x] Set `requires-python = ">=3.12"`
- [x] **1.2** Configure `[tool.setuptools]` section
  - [x] Set `package-dir = {"": "python/src"}` to reflect python subdirectory
  - [x] Configure namespace packages discovery with `where = "python/src"`
  - [x] Add package-data for template files (from MANIFEST.in)
- [x] **1.3** Add `[tool.setuptools.dynamic]` for version extraction
  - [x] Configure version to read from `python/src/mas/cli/__init__.py`
  - [x] Use `attr: mas.cli.__version__` pattern
- [x] **1.4** Add `[project.scripts]` for CLI entry point
  - [x] Configure `mas-cli` script via entry point
- [x] **1.5** Remove `[tool.uv.workspace]` section
  - [x] Package is now defined at root, not as a workspace member
- [-] **1.6** Validate pyproject.toml syntax
  - [ ] Run `python -m build --check` or equivalent validation

**Validation**: Confirm root pyproject.toml is syntactically correct and contains all metadata from python/setup.py

### Phase 2: Update Build Configuration and Workflow

Use the **new_task** tool to launch a subtask in **code** mode to complete this phase:

```
Update Makefile and build workflow to work from repository root
```

- [x] **2.1** Update [`python/Makefile`](python/Makefile)
  - [x] Update paths to work from python/ subdirectory but reference root pyproject.toml
  - [x] Test editable install: `pip install -e .[dev]` from root
  - [x] Ensure all targets (install, build, test, lint) function correctly
- [x] **2.2** Update [`.github/workflows/build-cli.yml`](.github/workflows/build-cli.yml)
  - [x] **CRITICAL**: Change `cd $GITHUB_WORKSPACE/python` to work from root (line 101)
  - [x] Update version injection sed commands (lines 102-107) to use `python/src/` paths
  - [x] Update pip install command to work from root: `pip install .[dev]` (line 111)
  - [x] Update build command to work from root: `python -m build` (line 152)
  - [x] Update artifact path: `dist/mas_cli-${{ env.VERSION_NOPREREL }}.tar.gz` (line 153)
- [x] **2.3** Update download artifact paths in container build jobs
  - [x] Update Python package download path (artifact consumption remains `${{ github.workspace }}/image/cli/install/`)
  - [x] Verify artifact is sourced from `dist/` not `python/dist/`
- [x] **2.4** Document consolidation approach
  - [x] Add comment in root pyproject.toml explaining structure
  - [x] Document that python/setup.py will be deprecated but kept temporarily

**Validation**: Run `python -m build` from root and verify package builds successfully

### Phase 3: Parallel Testing

Use the **new_task** tool to launch a subtask in **code** mode to complete this phase:

```
Test root pyproject.toml build alongside python/setup.py to ensure compatibility
```

- [x] **3.1** Build package with root pyproject.toml
  - [x] Run `python -m build` from repository root
  - [x] Verify wheel and sdist are created in `dist/`
  - [x] Extract and inspect wheel contents
  - [x] Compare with python/setup.py-built package
- [x] **3.2** Verify package contents
  - [x] Check `mas.cli` module is present (from python/src/)
  - [x] Verify all template files are included
  - [x] Confirm `mas-cli` script is in wheel
  - [x] Verify package structure matches python/setup.py build
- [x] **3.3** Test installation scenarios
  - [x] Fresh venv: `pip install dist/mas_cli-*.whl`
  - [x] Editable install from root: `pip install -e .[dev]`
  - [x] Verify `mas-cli --help` works
  - [x] Run existing tests: `pytest`
- [x] **3.4** Test version injection mechanism
  - [x] Manually run sed commands with updated paths (python/src/)
  - [x] Build package after version injection
  - [x] Verify version appears correctly in built package
  - [x] Check both `__version__` and `self.version` are updated

**Validation**: Package installs and functions identically to python/setup.py-built version

### Phase 4: Deprecate setup.py

Use the **new_task** tool to launch a subtask in **code** mode to complete this phase:

```
Deprecate setup.py while maintaining backward compatibility
```

- [x] **4.1** Add deprecation notice to [`python/setup.py`](python/setup.py)
  - [x] Add comment at top: "DEPRECATED: This file is maintained for backward compatibility only. Use pyproject.toml."
  - [x] Keep file functional for now
- [x] **4.2** Update [`python/CONTRIBUTING.md`](python/CONTRIBUTING.md)
  - [x] Document pyproject.toml as primary configuration
  - [x] Update build instructions if needed
- [x] **4.3** Update [`python/README.md`](python/README.md)
  - [x] Add note about modern packaging approach
  - [x] Update any build/install instructions

**Validation**: Documentation clearly indicates pyproject.toml is the primary configuration

### Phase 5: CI/CD Integration Testing

Use the **new_task** tool to launch a subtask in **code** mode to complete this phase:

```
Test complete build workflow with pyproject.toml in CI/CD pipeline
```

- [x] **5.1** Create test branch with changes
  - [x] Push pyproject.toml and updated files
  - [x] Trigger build-cli.yml workflow
- [x] **5.2** Monitor build-python job
  - [x] Verify version injection (lines 102-107)
  - [x] Check pip install succeeds (line 111)
  - [X] Confirm linting passes (lines 136-140)
  - [x] Verify tests pass (lines 143-146)
  - [x] Check build succeeds (lines 149-153)
- [X] **5.3** Verify artifact creation
  - [x] Check `mas_cli.tar.gz` artifact is uploaded
  - [x] Download and inspect artifact
  - [x] Verify version in filename matches `VERSION_NOPREREL`
- [x] **5.4** Test container builds
  - [x] Verify all architecture builds succeed
  - [x] Check Python package is correctly installed in containers
  - [x] Confirm CLI functionality in container

**Validation**: Complete CI/CD pipeline succeeds with pyproject.toml

### Phase 6: Remove setup.py (Future)

**Note**: This phase should be executed in a separate task after Phase 5 is validated in production

Use the **new_task** tool to launch a subtask in **code** mode to complete this phase:

```
Remove deprecated setup.py after pyproject.toml is proven stable
```

- [x] **6.1** Remove [`python/setup.py`](python/setup.py)
- [x] **6.2** Remove [`python/MANIFEST.in`](python/MANIFEST.in) if no longer needed
- [x] **6.3** Update any remaining documentation references
- [x] **6.4** Test complete build pipeline one final time

**Validation**: Package builds and deploys successfully without setup.py

## Final Validation

After completing all phases:

1. **Build the package**: `python -m build` (from repository root)
2. **Install in clean venv**: `python -m venv test-venv && source test-venv/bin/activate && pip install dist/mas_cli-*.whl`
3. **Run CLI**: `mas-cli --help`
4. **Run tests**: `pytest`
5. **Check version**: `python -c "import mas.cli; print(mas.cli.__version__)"`
6. **Verify templates**: Check that template files are accessible in installed package
7. **Test editable install**: `pip install -e .[dev]`
8. **Run full CI/CD pipeline**: Trigger workflow and verify all jobs pass
9. **Compare package contents**: Use `unzip -l dist/*.whl` to compare with setup.py-built package

### Success Criteria

- ✅ Package builds successfully with `python -m build`
- ✅ All template files are included in built package
- ✅ Version injection mechanism works in CI/CD
- ✅ CLI script is executable and functional
- ✅ All tests pass
- ✅ Editable install works for development
- ✅ Container builds succeed with new package
- ✅ PyPI publishing works (on release)
- ✅ No functional changes to package behavior

### Troubleshooting

**Issue**: Templates not included in package
- **Solution**: Verify `tool.setuptools.package-data` configuration matches MANIFEST.in patterns
- **Check**: Use `unzip -l dist/*.whl` to inspect wheel contents

**Issue**: Version not injected correctly
- **Solution**: Ensure `dynamic = ["version"]` and `tool.setuptools.dynamic.version` are configured
- **Check**: Verify sed commands in workflow target correct files

**Issue**: Namespace package not working
- **Solution**: Confirm `tool.setuptools.packages.find` includes `where = "src"` and `namespaces = true`
- **Check**: Test import: `python -c "import mas.cli"`

**Issue**: CLI script not found
- **Solution**: Verify `[project.scripts]` entry point is correct
- **Check**: Look for `mas-cli` in wheel's `*.dist-info/entry_points.txt`

**Issue**: Dependencies not installed
- **Solution**: Check `dependencies` list matches `install_requires` from setup.py
- **Check**: Run `pip show mas-cli` and verify dependencies
