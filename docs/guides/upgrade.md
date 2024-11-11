Upgrade
===============================================================================

Upgrade Overview
-------------------------------------------------------------------------------
Upgrade is the act of switching a MAS installation to a new subscription channel; it is distinct from an update, which is when new versions are delivered on existing subscription channels.  New features are always delivered via new subscription channels, update within a channel will only deliver updates to existing functionality (including security updates) and bug fixes.

1. [Upgrade](#1-upgrade)
2. [Disconnected Upgrade Preparation](#1-disconnected-install-preparation)
3. [Update MAS](#2-update-maximo-application-suite)

When you choose to upgrade to pick up a feature release, the upgrade is targeted at a specific MAS instance in the cluster.  Upgrades must work within an n-1 range, ie. we support MAS 8.10 and 8.9 on a cluster, or 8.9 and 8.8, but not 8.8 and 8.10.

The process to undo an upgrade varies depending on what version and which applications were being upgraded, e.g. if there are database changes that need to be reversed it's more involved than if it's just a case of stateless runtime to be reverted to an older version.

!!! important
    You can only upgrade to a version of MAS already supported by the `ibm-maximo-operator-catalog` CatalogSource currently installed in the cluster.

    - If you are using the static catalog and have not already updated to a catalog that includes the version of MAS you wish to upgrade to then you must first follow the [update process](update.md).
    - If you are using the dynamic catalog then no action is required here, the catalog source will automatically update to include new MAS releases.


1 Disconnected Upgrade Preparation
-------------------------------------------------------------------------------
Before you start the upgrade, you must mirror the images for the new catalog that you wish to update to. Mirroring the images is a simple but time consuming process.  Three modes are available for the mirror process:

- **direct** mirrors images directly from the source registry to your private registry
- **to-filesystem** mirrors images from the source to a local directory
- **from-filesystem** mirrors images from a local directory to your private registry

```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas mirror-images
```

You will be prompted to set the target registry for the image mirroring and to [select the version of IBM Maximo Operator Catalog to mirror](../catalogs/index.md) and the subset of content that you wish to mirror.  You can choose to mirror everything from the catalog, or control exactly what is mirrored to your private registry to reduce the time and bandwidth used to mirror the images, as well reducing the storage requirements of the registry.

This command can also be ran non-interactive, for full details refer to the [mirror-images](../commands/mirror-images.md) command documentation.

```bash
mas mirror-images -m direct -d /mnt/local-mirror \
  -H myprivateregistry.com -P 5000 -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
  --mirror-catalog --mirror-core --mirror-iot --mirror-manage \
  --mirror-cfs --mirror-sls --mirror-tsm --mirror-mongo --mirror-db2 \
  --ibm-entitlement $IBM_ENTITLEMENT_KEY --redhat-username $REDHAT_USERNAME --redhat-password $REDHAT_PASSWORD \
  --no-confirm
```

!!! important
    Make sure to select the release of MAS you want to upgrade to, not the release of MAS you are currently on.  For example if you are upgrading from MAS 8.9 to MAS 8.10 you should set `-C 8.10.x`.


2 Upgrade Maximo Application Suite
-------------------------------------------------------------------------------
Run `mas upgrade` and choose the MAS instance to upgrade.  The upgrade will automatically detect the installed release, and perform an upgrade to the next available release.

```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas upgrade
```

The command can also be ran non-interactive.

```bash
mas upgrade -i inst1 --no-confirm
```
