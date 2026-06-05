Contributing
===============================================================================

Development Tips
-------------------------------------------------------------------------------

```bash
uv venv
uv pip install --editable ./python[dev]
uv pip install --editable ../python-devops[dev]
.venv/bin/activate

# Run help command
python python/src/mas-cli --help

# Run tests
pytest python/tests/
```

This will be running using the code in your workspace, when you make a change you don't need to rebuild anything, just restart the cli application.


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
