Uninstall
===============================================================================

Usage
-------------------------------------------------------------------------------
`mas uninstall [options]`

### MAS Instance Selection
- `-i|--id MAS_INSTANCE_ID` MAS Instance ID to uninstall

### Other Options
- `--no-confirm` Launch the upgrade without prompting for confirmation
- `-h|--help` Show help message


Examples
-------------------------------------------------------------------------------
### Interactive Uninstall
```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas uninstall
```

### Non-Interactive Uninstall
```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas uninstall -i inst1 --no-confirm
```
