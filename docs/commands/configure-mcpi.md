Configure MCPI
===============================================================================

Usage
-------------------------------------------------------------------------------
Usage information can be obtained using `mas configure-mcpi --help`

```
usage: mas configure-mcpi [-i MAS_INSTANCE_ID] [--no-confirm] [-h]

IBM Maximo Application Suite Admin CLI v@@CLI_LATEST_VERSION@@
Configure Maximo Cluster Performance Insights (MCPI) on an existing MAS instance.

Target MAS Instance Arguments:
Specify the target MAS instance for which to configure MCPI.

  -i, --mas-instance-id MAS_INSTANCE_ID
                        The MAS Instance ID to configure MCPI for (prompted if omitted)

More:
Additional options for configure-mcpi.

  --no-confirm          Proceed without prompting for confirmation
  -h, --help            Show this help message and exit
```

Examples
-------------------------------------------------------------------------------

### Interactive Configuration
Launch an interactive session that prompts for the MAS instance ID:

```bash
mas configure-mcpi
```

### Non-Interactive Configuration
Configure MCPI for a specific MAS instance without interactive prompts:

```bash
mas configure-mcpi \
  --mas-instance-id prod1 \
  --no-confirm
```

### Using uvx (Standalone)
Run `configure-mcpi` ephemerally using `uvx`:

```bash
uvx mas-cli configure-mcpi --mas-instance-id prod1 --no-confirm
```

Overview
-------------------------------------------------------------------------------

Maximo Cluster Performance Insights (MCPI) collects and provides performance metrics and telemetry insights for Maximo Application Suite clusters and workloads.

The `mas configure-mcpi` command enables MCPI on an existing MAS instance by creating or updating the `McpiCfg` custom resource in the instance's core namespace (`mas-<instance_id>-core`).

### How It Works

1. **Cluster Connection & Validation**: Connects to the target OpenShift cluster and verifies that the core namespace `mas-<instance_id>-core` exists.
2. **Version Verification**: Checks the installed MAS channel to confirm the instance is running MAS 9.2 or later.
3. **Resource Application**: Applies (creates or patches) the `McpiCfg` custom resource (`<instance_id>-mcpi-system`) with `spec.config.enabled: true` in the core namespace:

```yaml
apiVersion: config.mas.ibm.com/v1
kind: McpiCfg
metadata:
  name: <instance_id>-mcpi-system
  namespace: mas-<instance_id>-core
  labels:
    mas.ibm.com/configScope: system
    mas.ibm.com/instanceId: <instance_id>
spec:
  displayName: Maximo Cluster Performance Insights
  config:
    enabled: true
```

4. **Reconciliation**: The MAS entity manager operator detects the `McpiCfg` resource and automatically reconciles and deploys the necessary MCPI components.

### Verification

After running `mas configure-mcpi`, you can verify the status of the configuration using the OpenShift CLI:

```bash
oc get mcpicfg -n mas-<instance_id>-core
```

### Requirements

- Access to the target OpenShift cluster with permissions to manage `McpiCfg` resources in the MAS core namespace
- MAS instance running channel **9.2.x** or later
- Target namespace `mas-<instance_id>-core` must already exist on the cluster

!!! warning "Version Requirement"
    Maximo Cluster Performance Insights (MCPI) is only supported on **MAS 9.2 or later**. Attempting to configure MCPI on earlier MAS versions will result in an error.
