Pre-Install
===============================================================================

Usage
-------------------------------------------------------------------------------
Usage information can be obtained using `mas pre-install --help`

```
usage: mas pre-install [-i MAS_INSTANCE_ID] [--mas-version MAS_VERSION]
                       [--permission-mode {cluster,namespaced,minimal}]
                       [--apps APPS] [--no-confirm] [-h]

IBM Maximo Application Suite Admin CLI v21.3.0
Set up pre-install RBAC for MAS.
Available only for MAS version 9.2.0 and later.

Interactive Mode:
Omitting required options will trigger an interactive prompt

Target Cluster Arguments:
Specify the target cluster and MAS instance for which pre-install RBAC should be set up.

  -i, --mas-instance-id MAS_INSTANCE_ID
                        The MAS instance ID for which pre-install RBAC will be set up
  --mas-version MAS_VERSION
                        The MAS version in x.y.z format used to select pre-install RBAC manifests, for example 9.2.0
  --permission-mode {cluster,namespaced,minimal}
                        The permission mode used to determine which pre-install RBAC manifests are set up
  --apps APPS           Comma-separated list of apps used to filter which pre-install RBAC manifests are set up, for example core,manage,iot

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
Set up pre-install RBAC for a MAS instance using namespaced permission mode:

```bash
mas pre-install \
  --mas-instance-id prod1 \
  --mas-version 9.2.0 \
  --permission-mode namespaced \
  --apps core,manage,iot \
  --no-confirm
```

### Pre-Install for Minimal Mode
Set up pre-install RBAC for minimal permission mode:

```bash
mas pre-install \
  --mas-instance-id dev1 \
  --mas-version 9.2.0 \
  --permission-mode minimal \
  --apps core \
  --no-confirm
```

### Pre-Install for Cluster Mode
Set up pre-install RBAC for cluster permission mode (optional, as cluster mode can apply RBAC during installation):

```bash
mas pre-install \
  --mas-instance-id test1 \
  --mas-version 9.2.0 \
  --permission-mode cluster \
  --apps core,manage,monitor,iot \
  --no-confirm
```

### Pre-Install with Multiple Applications
Set up pre-install RBAC for multiple MAS applications:

```bash
mas pre-install \
  --mas-instance-id prod1 \
  --mas-version 9.2.0 \
  --permission-mode namespaced \
  --apps core,manage,monitor,iot,predict,visualinspection \
  --no-confirm
```

Notes
-------------------------------------------------------------------------------

### Pre-Install Process
The pre-install command performs the following operations:

1. **Validates cluster administrator permissions** - Ensures you have the required permissions to create RBAC resources
2. **Validates MAS version** - Confirms the version is 9.2.0 or later
3. **Validates application selection** - Ensures all specified applications are supported
4. **Applies RBAC manifests** - Creates ClusterRoles, Roles, RoleBindings, and ServiceAccounts based on permission mode and selected applications

### When to Use Pre-Install

The `mas pre-install` command is used to grant necessary RBAC permissions.

**If you have cluster administrator permissions:**
- Run `mas install` directly - it will automatically handle the pre-install RBAC setup

**If you do NOT have cluster administrator permissions:**
- A cluster administrator must run `mas pre-install` to grant the necessary permissions
- Then you can run `mas install --skip-preinstall-rbac` to proceed with installation

### Permission Modes

All permission modes work with `mas pre-install`:

| Permission Mode | Description |
|----------------|-------------|
| **cluster** | MAS has cluster-level access to manage its applications and resources across the cluster. ClusterRoles are installed. |
| **namespaced** | No ClusterRoles are installed. MAS can manage resources only in namespaces prepared by the OpenShift admin. |
| **minimal** | Minimal permissions with essential RBAC requirements |

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

After running `mas pre-install`, proceed with the MAS installation using the `--skip-preinstall-rbac` flag to avoid re-applying the RBAC resources:

```bash
mas install \
  --mas-instance-id prod1 \
  --permission-mode namespaced \
  --skip-preinstall-rbac \
  ... other install parameters ...
```

### Workflow Example

**Step 1: Cluster Administrator runs `mas pre-install`**
```bash
mas pre-install \
  --mas-instance-id prod1 \
  --mas-version 9.2.0 \
  --permission-mode namespaced \
  --apps core,manage,iot \
  --no-confirm
```

**Step 2: MAS Installer (with limited permissions) runs `mas install`**
```bash
mas install \
  --mas-instance-id prod1 \
  --permission-mode namespaced \
  --skip-preinstall-rbac \
  ... other parameters ...
```

### Requirements

- OpenShift cluster administrator permissions
- MAS version 9.2.0 or later
- Access to the target OpenShift cluster

!!! warning "Administrator Permissions Required"
    The `mas pre-install` command requires cluster administrator permissions. If you do not have these permissions, the command will fail with an error message. Only a cluster administrator can set up pre-install RBAC for MAS.

### Interactive Mode

When running without all required options, the command enters interactive mode and will prompt for:

1. Target OpenShift cluster connection
2. MAS instance ID
3. MAS version (in x.y.z format)
4. Permission mode (cluster, namespaced, or minimal)
5. Applications to include (comma-separated list)

The command will display a summary of your selections and ask for confirmation before applying the RBAC resources.

### Version Compatibility

!!! important
    This command is only supported for MAS version 9.2.0 and later. If you specify an earlier version, the command will fail with an error message.