Upgrade
===============================================================================

:::mas-cli-usage
module: mas.cli.upgrade.argParser
parser: upgradeArgParser
ignore_description: true
ignore_epilog: true
:::

Overview
-------------------------------------------------------------------------------
Upgrade is the act of switching a MAS installation to a new subscription channel; it is distinct from an update, which is when new versions are delivered on existing subscription channels. New features are always delivered via new subscription channels, while updates within a channel will only deliver updates to existing functionality (including security updates) and bug fixes.

### Upgrade vs. Update
When you choose to upgrade to pick up a feature release, the upgrade is targeted at a specific MAS instance in the cluster. Upgrades must work within an n-1 range, i.e., we support MAS 8.10 and 8.9 on a cluster, or 8.9 and 8.8, but not 8.8 and 8.10.

!!! important
    You can only upgrade to a version of MAS already supported by the `ibm-maximo-operator-catalog` CatalogSource currently installed in the cluster.

    - If you are using the static catalog and have not already updated to a catalog that includes the version of MAS you wish to upgrade to, then you must first follow the [update process](update.md).
    - If you are using the dynamic catalog then no action is required here; the catalog source will automatically update to include new MAS releases.

### Rollback Considerations
The process to undo an upgrade varies depending on what version and which applications were being upgraded. For example, if there are database changes that need to be reversed it's more involved than if it's just a case of stateless runtime to be reverted to an older version.


Disconnected Upgrade Preparation
-------------------------------------------------------------------------------
Before you start the upgrade, you must mirror the images for the new catalog that you wish to upgrade to. Mirroring the images is a simple but time consuming process. Three modes are available for the mirror process:

- **m2m** - mirrors images directly from the source registry to your private registry
- **m2d** - mirrors images from the source registry to a local directory
- **d2m** - mirrors images from a local directory to your private registry

`mas mirror` does not have an interactive mode, all options must be provided as command line arguments. For full details refer to the [image mirroring](mirroring-v2.md) guide.

```bash
docker run -ti --rm -e IBM_ENTITLEMENT_KEY -e REGISTRY_USERNAME -e REGISTRY_PASSWORD \
  quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror \
  --catalog @@MAS_LATEST_CATALOG@@ --release @@MAS_LATEST_CHANNEL@@ \
  --mode m2m --target-registry myprivateregistry.com \
  --dir /mnt/local-mirror \
  --core --iot --manage \
  --sls --tsm --mongodb-ce --db2u-s11 --db2u-s12
```

!!! important
    Make sure to select the release of MAS you want to upgrade to, not the release of MAS you are currently on. For example, if you are upgrading from MAS 8.9 to MAS 8.10 you should set `-C 8.10.x`.


Upgrade Maximo Application Suite
-------------------------------------------------------------------------------
Run `mas upgrade` and choose the MAS instance to upgrade. The upgrade will automatically detect the installed release and perform an upgrade to the next available release.

### Interactive Upgrade
```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas upgrade
```

### Non-Interactive Upgrade
```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas upgrade --mas-instance-id inst1 --no-confirm
```
