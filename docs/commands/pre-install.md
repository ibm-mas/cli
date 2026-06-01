Pre-Install
===============================================================================

Usage
-------------------------------------------------------------------------------
Usage information can be obtained using `mas pre-install --help`

```
usage: mas pre-install [-i MAS_INSTANCE_ID] [--mas-channel MAS_CHANNEL]
                       [--admin-mode {cluster,namespaced,minimal}]
                       [--apps APPS] [--no-confirm] [-h]

IBM Maximo Application Suite Admin CLI v21.3.0
Set up pre-install RBAC for MAS.
Available only for MAS channel 9.2.x and later.

Interactive Mode:
Omitting required options will trigger an interactive prompt

Target Cluster Arguments:
Specify the target cluster and MAS instance for which pre-install RBAC should be set up.

  -i, --mas-instance-id MAS_INSTANCE_ID
                        The MAS instance ID for which pre-install RBAC will be set up
  --mas-channel MAS_CHANNEL
                        The MAS channel used to select pre-install RBAC manifests, for example 9.2.x
  --admin-mode {cluster,namespaced,minimal}
                        The admin mode used to determine which pre-install RBAC manifests are set up (minimal mode does not require pre-install)
  --apps APPS           Comma-separated list of apps used to filter which pre-install RBAC manifests are set up (required for namespaced mode), for example core,manage,iot

More:
Additional options for pre-install.

  --no-confirm          Proceed without prompting for cluster confirmation
  -h, --help            Show this help message and exit
```

Examples
-------------------------------------------------------------------------------

### Interactive Pre-Install
Launch an interactive pre-install session that will prompt you for all required configuration:

```bash
mas pre-install
```

### Non-Interactive Pre-Install for Namespaced Mode
Set up pre-install RBAC for a MAS instance using namespaced admin mode (apps are required):

```bash
mas pre-install \
  --mas-instance-id prod1 \
  --mas-channel 9.2.x \
  --admin-mode namespaced \
  --apps core,manage,iot \
  --no-confirm
```

### Pre-Install for Cluster Mode
Set up pre-install RBAC for cluster admin mode (apps are not required - automatically uses ibm-mas operator):

```bash
mas pre-install \
  --mas-instance-id test1 \
  --mas-channel 9.2.x \
  --admin-mode cluster \
  --no-confirm
```

### Pre-Install with Multiple Applications
Set up pre-install RBAC for multiple MAS applications:

```bash
mas pre-install \
  --mas-instance-id prod1 \
  --mas-channel 9.2.x \
  --admin-mode namespaced \
  --apps core,manage,monitor,iot,predict,visualinspection \
  --no-confirm
```

### Minimal Mode (No Pre-Install Required)
If you specify minimal mode, the command will inform you that pre-install is not required:

```bash
mas pre-install \
  --mas-instance-id prod1 \
  --mas-channel 9.2.x \
  --admin-mode minimal \
  --no-confirm
```

This will display a message explaining that minimal mode does not require pre-install RBAC setup.

Understanding MAS 9.2 Permission Model Changes
-------------------------------------------------------------------------------

Starting with MAS 9.2, there are significant changes to the permissions model used by Maximo Application Suite related to the ability of the Core Platform to act as a delegated OpenShift administrator.

**By default, MAS operator packages operate in minimal permissions mode.** Compared to previous MAS releases, this means the MAS Core Platform has:

- **No ClusterRoles** - No cluster-wide permissions to access resources across all namespaces
- **No permissions to create namespaces** - Cannot create new application namespaces
- **No permissions in openshift-marketplace** - Cannot list PackageManifests, CatalogSources, or manage Subscriptions
- **No permissions in cert-manager namespace** - Cannot manage Certificates or Issuers outside the core namespace
- **Limited cross-namespace access** - Only essential namespace-scoped roles for specific operations (e.g., reading Secrets and ConfigMaps in application namespaces for binding)

In this minimal permission mode, when you install Maximo Application Suite applications, each application operator will grant the core platform only the **essential namespace-scoped permissions** required for basic operation (such as binding configuration). This means that the **non-essential** capabilities (installing new applications, managing application lifecycle, and viewing application status outside the core namespace) of the Core Platform's administrative API and UI that were previously enabled by default are now **disabled by default**.

**To enable these administrative capabilities**, you must explicitly configure one of the elevated admin modes (**cluster** or **namespaced**). If you have cluster administrator permissions, you can specify `--admin-mode cluster` or `--admin-mode namespaced` when running `mas install` and the necessary RBAC will be applied automatically. If you do not have cluster administrator permissions, a cluster administrator must first run `mas pre-install` to set up the required RBAC, then you can proceed with `mas install`.


### Admin Modes

MAS 9.2 and later supports three admin modes that control the level of permissions granted to the MAS:

| Admin Mode | Description | Application Lifecycle Management |
|----------------|-------------|---------------------------|
| **cluster** | ClusterRoles containing all non-essential permissions are created via MAS CLI. Functionally same as previous MAS releases. | Full - MAS Admin can manage application lifecycle across the cluster |
| **namespaced** | Namespace-scoped Roles containing all non-essential permissions are created via MAS CLI in pre-created application namespaces. No ClusterRoles are installed. | Scoped - MAS Admin can manage application lifecycle within bounds of pre-created namespaces |
| **minimal** | Only essential Roles and namespace-scoped Roles are created by operators. No ClusterRoles or non-essential namespace-scoped Roles are installed. | None - MAS Admin cannot manage application lifecycle; must be handled by OpenShift Administrator |

### When to Use Pre-Install

The `mas pre-install` command is used to grant elevated RBAC permissions to the MAS Core Platform, enabling administrative capabilities.

**If you want to use minimal mode:**
- Skip `mas pre-install` entirely
- Run `mas install` with `--admin-mode minimal` - essential roles will be created automatically during installation
- Note: You will not be able to install or upgrade applications through the MAS UI or API

**If you want to use cluster or namespaced mode:**
- **With cluster administrator permissions:** Run `mas install` directly with `--admin-mode cluster` or `--admin-mode namespaced` - it will automatically handle the pre-install RBAC setup
- **Without cluster administrator permissions:** A cluster administrator must first run `mas pre-install` to grant the necessary permissions, then you can run `mas install` to proceed with installation

### Pre-Install Process

The pre-install command performs the following operations:

1. **Validates cluster administrator permissions** - Ensures you have the required permissions to create RBAC resources
2. **Validates MAS channel** - Confirms the channel is 9.2.x or later
3. **Validates application selection** - Ensures all specified applications are supported (only in namespaced mode)
4. **Applies RBAC manifests** - Creates ClusterRoles, ClusterRoleBindings, Roles and RoleBindings based on admin mode and selected applications

!!! note "Minimal Mode and Pre-Install"
    If the cluster is intended to run in **minimal** mode, `mas pre-install` is not required as essential roles are installed by each operator during installation. The `mas pre-install` command only supports **cluster** and **namespaced** modes.

### Supported Applications

The following applications are supported for pre-install RBAC setup:

- `core` - MAS Core
- `aiservice` - AI Service
- `arcgis` - ArcGIS
- `facilities` - Maximo Facilities
- `iot` - Maximo IoT
- `manage` - Maximo Manage
- `monitor` - Maximo Monitor
- `optimizer` - Maximo Optimizer
- `predict` - Maximo Predict
- `visualinspection` - Maximo Visual Inspection

You can specify multiple applications as a comma-separated list (e.g., `core,manage,iot`).

### Integration with MAS Install

After running `mas pre-install`, proceed with the MAS installation using the `--no-confirm` flag to avoid re-applying the RBAC resources. Use the same admin mode that was used during pre-install for issuerKind selection:

```bash
mas install \
  --mas-instance-id prod1 \
  --admin-mode namespaced \
  --no-confirm \
  ... other install parameters ...
```

### Workflow Example

**Step 1: Cluster Administrator runs `mas pre-install`**
```bash
mas pre-install \
  --mas-instance-id prod1 \
  --mas-channel 9.2.x \
  --admin-mode namespaced \
  --apps core,manage,iot \
  --no-confirm
```

**Step 2: MAS Installer (with limited permissions) runs `mas install`**
```bash
mas install \
  --mas-instance-id prod1 \
  --admin-mode namespaced \
  --no-confirm \
  ... other parameters ...
```

### Requirements

- OpenShift cluster administrator permissions
- MAS channel 9.2.x or later
- Access to the target OpenShift cluster

!!! warning "Administrator Permissions Required"
    The `mas pre-install` command requires cluster administrator permissions. If you do not have these permissions, the command will fail with an error message. Only a cluster administrator can set up pre-install RBAC for MAS.

### Interactive Mode

When running without all required options, the command enters interactive mode and will prompt for:

1. Target OpenShift cluster connection
2. MAS instance ID
3. MAS channel (for example 9.2.x)
4. Admin mode (cluster or namespaced)
5. Applications to include (comma-separated list) - **only for namespaced mode**

The command will display a summary of your selections and ask for confirmation before applying the RBAC resources.

**Note:** In cluster mode, applications are not prompted as the ibm-mas operator is automatically used.

### Version Compatibility

!!! important
    This command is only supported for MAS version 9.2 and later. If you specify an earlier mas version, the command will fail with an error message.