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
mas uninstall
```

### Non-Interactive Uninstall
```bash
mas uninstall -i inst1 --no-confirm
```

Note: If you are not already connected to an OpenShift cluster you will be prompted to provide the server URL & token, and whether to verify the server certificate or not,  If you are already connected to a cluster you will be given the option to change to another cluster.