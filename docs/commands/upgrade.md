Upgrade
===============================================================================

Usage
-------------------------------------------------------------------------------
`mas upgrade [options]`

### MAS Instance Selection
- `-i|--id MAS_INSTANCE_ID` MAS Instance ID to upgrade

### Other Options
- `--no-confirm`        Launch the upgrade without prompting for confirmation
- `--skip-pre-check`    Skips the 'pre-upgrade-check' and 'post-upgrade-verify' tasks in the upgrade pipeline
- `-h|--help`           Show help message


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
