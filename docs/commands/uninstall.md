Uninstall
===============================================================================

Usage
-------------------------------------------------------------------------------
Usage information can be obtained using `mas uninstall --help`

```
usage: mas uninstall [--mas-instance-id MAS_INSTANCE_ID] [--uninstall-all-deps] [--uninstall-cert-manager] [--uninstall-common-services] [--uninstall-grafana]
                     [--uninstall-ibm-catalog] [--uninstall-mongodb] [--uninstall-sls] [--uninstall-uds] [--no-confirm] [-h]

IBM Maximo Application Suite Admin CLI v100.0.0
Uninstall MAS by configuring and launching the MAS Uninstall Tekton Pipeline.

Interactive Mode:
Omitting the --instance-id option will trigger an interactive prompt

MAS Instance Selection:
  --mas-instance-id MAS_INSTANCE_ID  The MAS instance ID to be uninstalled

MAS Dependencies Selection:
  --uninstall-all-deps               Uninstall all MAS-related dependencies from the target cluster
  --uninstall-cert-manager           Uninstall Certificate Manager from the target cluster
  --uninstall-common-services        Uninstall IBM Common Services from the target cluster
  --uninstall-grafana                Uninstall Grafana from the target cluster
  --uninstall-ibm-catalog            Uninstall the IBM Maximo Operator Catalog Source (ibm-operator-catalog) from the target cluster
  --uninstall-mongodb                Uninstall MongoDb from the target cluster
  --uninstall-sls                    Uninstall IBM Suite License Service from the target cluster
  --uninstall-uds                    Uninstall IBM User Data Services from the target cluster

More:
  --no-confirm                       Launch the upgrade without prompting for confirmation
  -h, --help                         Show this help message and exit
```

Examples
-------------------------------------------------------------------------------
### Interactive Uninstall
```bash
mas uninstall
```

### Non-Interactive Uninstall
```bash
mas uninstall --mas-instance-id inst1 --no-confirm
```
