mas.cli
-------------------------------------------------------------------------------
Introduced in 2026, replacing the standalone binary previously built with PyInstaller, `mas-cli` is now compatible with [uv](https://docs.astral.sh/uv/) and is the simplest way run the CLI.

- [Install uv](https://docs.astral.sh/uv/getting-started/installation/)

### Ephemeral Execution
Run the MAS CLI without an install:

```bash
uvx mas-cli --help
```

### Persistent Installation
Install the MAS CLI globally:

```bash
# Install the latest version of mas-cli
uv tool install mas-cli

# The 'mas-cli' command is available in your PATH
mas-cli --help

# Upgrade or uninstall the mas-cli
uv tool upgrade mas-cli
uv tool uninstall mas-cli
```

!!! tip "Choosing a specific version"
    You can use a specific version of mas-cli by with ephemeral execution or installation using `mas-cli@@@CLI_LATEST_VERSION@@`
