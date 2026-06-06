Contributing
===============================================================================

Development Tips
-------------------------------------------------------------------------------
Set up your development environment with an editable install of the package and the mas-devops dependency.

```bash
uv venv
uv pip install --editable .[dev]
uv pip install --editable ../python-devops[dev]
.venv/bin/activate

# Run help command
python mas-cli --help

# Run tests
pytest python/test python/tests
```

### Must-Gather

```bash
# Generate must-gather
rm mas.log; mas-cli must-gather --keep-files -d testing/must-gather

# The following commands are useful for quick development cycles on the
# post-processing to avoid needing to run the must-gather collectors again

# 1. Re-generate web viewer
python -m mas.cli.must_gather.web_viewer generate --dir testing/must-gather/20260606-085110

# 2. Serve web viewer
python -m mas.cli.must_gather.web_viewer serve --dir testing/must-gather/20260606-085110

```

Useful Commands
-------------------------------------------------------------------------------
### Print the usage information
```bash
python mas-cli --help
```

### Simple commands for manual tests
```bash
python mas-cli mirror --help

# Check simple m2d mirroring
python mas-cli mirror --mode m2d --dir /tmp/mirror --catalog v9-260326-amd64 --release  9.1.x --tsm --image-timeout 10m

# Check old catalog exception handling
python mas-cli mirror --mode m2d --dir /tmp/mirror --catalog v9-251224-amd64 --release  9.1.x --amlen --image-timeout 10m

# Check invalid catalog exception handling
python mas-cli mirror --mode m2d --dir /tmp/mirror --catalog v9-260101-amd64 --release  9.1.x --amlen --image-timeout 10m
```
