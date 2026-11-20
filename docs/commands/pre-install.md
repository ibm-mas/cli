Pre-Install
===============================================================================

Usage
-------------------------------------------------------------------------------
Usage information can be obtained using `mas pre-install --help`

```
usage: mas pre-install [-i MAS_INSTANCE_ID] [--mas-channel MAS_CHANNEL]
                       [--admin-mode {cluster,namespaced}]
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
  --admin-mode {cluster,namespaced}
                        The admin mode used to determine which pre-install RBAC manifests are set up
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


Understanding MAS 9.2 Permission Model Changes
-------------------------------------------------------------------------------

Starting with MAS 9.2, there are significant changes to the permissions model used by Maximo Application Suite related to the ability of MAS to act as a delegated OpenShift administrator.

**By default, MAS operator packages operate in minimal permissions mode.** Compared to previous MAS releases, this means MAS has:

- **No ClusterRoles** - No cluster-wide permissions to access resources across all namespaces
- **No permissions to create namespaces** - Cannot create new application namespaces
- **No permissions in openshift-marketplace** - Cannot list PackageManifests, CatalogSources, or manage Subscriptions
- **Limited cross-namespace access** - Only essential namespace-scoped roles for specific operations (e.g., reading Secrets and ConfigMaps in application namespaces for binding)

In this minimal permission mode, when you install Maximo Application Suite applications, each application operator will grant MAS only the **essential namespace-scoped permissions** required for basic operation (such as binding configuration). This means that the **non-essential** capabilities (installing new applications, managing application lifecycle, and viewing application status outside the core namespace) of the MAS administrative API and UI that were previously enabled by default are now **disabled by default**.

**To enable these administrative capabilities**, you must explicitly configure one of the elevated admin modes (**cluster** or **namespaced**). If you have cluster administrator permissions, you can specify `--admin-mode cluster` or `--admin-mode namespaced` when running `mas install` and the necessary RBAC will be applied automatically. If you do not have cluster administrator permissions, a cluster administrator must first run `mas pre-install` to set up the required RBAC, then you can proceed with `mas install`.


### Admin Modes

MAS 9.2 and later supports three admin modes that control the level of permissions granted to the MAS:

| Admin Mode | Description | Apps Required |
|----------------|-------------|---------------|
| **cluster** | MAS has cluster-level access to manage its applications and resources across the cluster. ClusterRoles are installed for the ibm-mas operator only. | No - automatically uses ibm-mas operator |
| **namespaced** | No ClusterRoles are installed. MAS can manage resources only in namespaces prepared by the OpenShift admin. Roles are created for selected applications. | Yes - must specify apps |

**Note:** If the cluster is intended to run in minimal mode, `mas pre-install` is not required as essential roles are installed by each operator during installation.

### When to Use Pre-Install

The `mas pre-install` command sets up RBAC (Role-Based Access Control) permissions for your MAS instance by creating ClusterRoles, Roles, and RoleBindings based on the selected admin mode and applications. This is required when you do not have cluster administrator permissions and want to use **cluster** or **namespaced** mode.

When you run `mas install` with **cluster** or **namespaced** mode and you don't have cluster administrator permissions, `mas install` cannot create the required RBAC for these modes. A cluster administrator must first run `mas pre-install` to set up these permissions, then you can proceed with `mas install`.

If you have cluster administrator permissions, you can skip `mas pre-install` and run `mas install` directly - it will automatically handle the RBAC setup for **cluster** or **namespaced** mode. For **minimal** mode, `mas pre-install` is not required as essential roles are installed by operators during installation.


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

### Requirements

- OpenShift cluster administrator permissions
- MAS channel 9.2.x or later
- Access to the target OpenShift cluster

### Running with uvx
`mas pre-install` is available in both the container image and the standalone CLI:

```bash
uvx mas-cli pre-install \
  --mas-instance-id prod1 \
  --mas-channel 9.2.x \
  --admin-mode cluster \
  --no-confirm
```

The RBAC manifests are applied from the [ibm-mas/pre-install](https://github.com/ibm-mas/pre-install) repository. They are located in the following order:

1. The directory named by the `MAS_PREINSTALL_RBAC_DIR` environment variable, if set. The directory must contain `maximo-operator-catalog/operators` and/or `openshift-platform/operators`. If it is set but is not a directory the command fails rather than falling back.
2. `/opt/app-root/rbac`, which is populated when the container image is built.
3. The copy bundled inside the `mas-cli` package, which is what `uvx` and `uv tool install` use.

The bundled copy is fixed at the time the `mas-cli` release was built.  Use `MAS_PREINSTALL_RBAC_DIR` to apply newer or customised manifests.

To find out which `ibm-mas/pre-install` commit a release ships, read `SOURCE.json` from the installed package. The location of the directory that was used is also written to `mas.log` each time the command runs.

```bash
uvx --from mas-cli python -c "import json, mas.cli.rbac_utils as r, os; print(open(os.path.join(r.PACKAGED_PREINSTALL_RBAC_DIR, 'SOURCE.json')).read())"
```

!!! warning "Administrator Permissions Required"
    The `mas pre-install` command requires cluster administrator permissions. If you do not have these permissions, the command will fail with an error message.