Uninstall
===============================================================================

Usage
-------------------------------------------------------------------------------
`mas uninstall [options]`

### MAS Instance Selection
- `-i|--id MAS_INSTANCE_ID` MAS Instance ID to uninstall

### MAS Dependencies Uninstall Options
- `--uninstall-cert-manager` Uninstalls Certificate Manager from the target cluster. **Important**: Certificate Manager is a cluster-wide dependency, therefore be really careful when uninstalling it as this might be used by other applications and dependencies installed in the cluster.
- `--uninstall-common-services` Uninstalls IBM Common Services from the target cluster. **Important**: IBM Common Services is a shared dependency under `ibm-common-services` namespace, therefore be really careful when uninstalling it as this might be used by other applications and dependencies installed in the cluster.
- `--uninstall-cluster-monitoring` Uninstalls Cluster Monitoring from the target cluster, including OpenTelemetry, Graphana and User Workload Monitoring.
- `--uninstall-ibm-catalog` Uninstalls IBM Maximo Operator Catalog Source (`ibm-operator-catalog`) from the target cluster. **Important**: Catalog Sources are cluster-wide dependencies, therefore be really careful when uninstalling it as this might be used by several applications and dependencies installed in the cluster.
- `--uninstall-mongodb` Uninstalls MongoDB from the target cluster. **Important**: MongoDB could be a shared dependency, therefore be really careful when uninstalling it as this might be used by several applications and dependencies installed in the cluster.
- `--uninstall-sls` Uninstalls Suite License Service from the target cluster. **Important**: SLS could be a shared dependency, therefore be really careful when uninstalling it as this might be used by other MAS instances and dependencies installed in the cluster.
- `--uninstall-all-deps` Uninstalls **all** MAS related dependencies including:
    - Certificate Manager
    - IBM Common Services
    - Cluster Monitoring
    - IBM Operator Catalog
    - MongoDB
    - Suite License Service

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