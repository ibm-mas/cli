Upgrade
===============================================================================

Usage
-------------------------------------------------------------------------------
`mas upgrade [options]`

### MAS Instance Selection
- `-i|--id MAS_INSTANCE_ID` MAS Instance ID to upgrade

### Other Options
- `--no-confirm` Mirror images without prompting for confirmation
- `-h|--help` Show help message


Examples
-------------------------------------------------------------------------------
### Interactive Upgrade
```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas upgrade
```

### Non-Interactive Upgrade
```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas upgrade -i inst1 --no-confirm
```
