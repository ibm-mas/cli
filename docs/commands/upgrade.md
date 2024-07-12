Upgrade
===============================================================================

Usage
-------------------------------------------------------------------------------
Usage information can be obtained using `mas upgrade --help`

```
sage: mas upgrade [--mas-instance-id MAS_INSTANCE_ID] [--skip-pre-check] [--no-confirm] [-h]

IBM Maximo Application Suite Admin CLI v100.0.0
Upgrade MAS by configuring and launching the MAS Upgrade Tekton Pipeline.

Interactive Mode:
Omitting the --instance-id option will trigger an interactive prompt

MAS Instance Selection:
  --mas-instance-id MAS_INSTANCE_ID  The MAS instance ID to be upgraded

More:
  --skip-pre-check                   Disable the 'pre-upgrade-check' and 'post-upgrade-verify' tasks in the upgrade pipeline
  --no-confirm                       Launch the upgrade without prompting for confirmation
  -h, --help                         Show this help message and exit
```


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
