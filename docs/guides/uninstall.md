Uninstall
===============================================================================

Overview
-------------------------------------------------------------------------------
The MAS CLI provides automated uninstallation of Maximo Application Suite from OpenShift clusters. The uninstall process removes MAS instances, applications, and optionally their dependencies, providing a clean removal or preparation for reinstallation.

!!! tip
    For production environments, always test the uninstall process in a non-production environment first to identify potential issues and estimate timing.

This guide covers the complete uninstallation process, including MAS instances, applications, and dependency management.

!!! warning "Data Loss"
    Uninstalling MAS will permanently delete all MAS data, configurations, and applications. Ensure you have backups before proceeding. Consider using the [backup functionality](backup.md) before uninstalling.


Understanding MAS Uninstallation
-------------------------------------------------------------------------------

### What Gets Uninstalled
The uninstall process removes:

- **MAS Core** - Suite operator and core services
- **MAS Applications** - All installed applications (Manage, Monitor, IoT, etc.)
- **Application Data** - Persistent volumes and databases
- **Configurations** - Custom resources and configurations
- **Namespaces** - MAS instance namespaces

### Optional Dependency Removal
You can optionally remove shared dependencies:

- **Certificate Manager** - TLS certificate management
- **IBM Common Services** - Shared IBM services
- **Grafana** - Monitoring and dashboards
- **MongoDB** - MAS configuration database
- **Suite License Service (SLS)** - License management
- **Data Reporter Operator (DRO)** - Usage reporting
- **IBM Operator Catalog** - IBM operator catalog source

!!! warning "Shared Dependencies"
    Be cautious when removing dependencies in multi-instance or shared cluster environments. Removing shared dependencies can impact other applications and MAS instances.


Uninstallation Process
-------------------------------------------------------------------------------

### How Uninstall Works
The `mas uninstall` command performs the following steps:

1. **Detects MAS Instances** - Identifies installed MAS instances
2. **Validates Selection** - Confirms instance to uninstall
3. **Removes Applications** - Uninstalls all MAS applications
4. **Removes Core** - Uninstalls MAS core operator
5. **Cleans Namespaces** - Deletes MAS namespaces
6. **Removes Dependencies** - Optionally removes shared dependencies
7. **Cleans Resources** - Removes cluster-scoped resources


### Interactive Mode
Interactive mode guides you through the uninstallation process with prompts for all options.

```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas uninstall
```

The interactive session will:

1. Prompt for OpenShift cluster connection (if not connected)
2. Display detected MAS instances
3. Request instance selection for uninstallation
4. Ask whether to remove dependencies
5. Display uninstallation summary
6. Request confirmation before proceeding

### Non-Interactive Mode
Non-interactive mode is ideal for automation and scripting. All required parameters must be provided via command-line arguments.

```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas uninstall \
  --mas-instance-id inst1 \
  --no-confirm
```


Command Reference
-------------------------------------------------------------------------------

### MAS Instance Selection
- `--mas-instance-id MAS_INSTANCE_ID` - MAS instance ID to uninstall (required in non-interactive mode)

### Dependency Removal Options
- `--uninstall-all-deps` - Remove all MAS-related dependencies
- `--uninstall-cert-manager` - Remove Certificate Manager
- `--uninstall-common-services` - Remove IBM Common Services
- `--uninstall-grafana` - Remove Grafana
- `--uninstall-ibm-catalog` - Remove IBM Operator Catalog (ibm-operator-catalog)
- `--uninstall-mongodb` - Remove MongoDB
- `--uninstall-sls` - Remove Suite License Service
- `--uninstall-dro` - Remove Data Reporter Operator

### Other Options
- `--no-confirm` - Skip confirmation prompt
- `-h, --help` - Display help message
