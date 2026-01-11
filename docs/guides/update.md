Update
===============================================================================

:::mas-cli-usage
module: mas.cli.update.argParser
parser: updateArgParser
ignore_description: true
ignore_epilog: true
:::

Overview
-------------------------------------------------------------------------------
The `mas update` function is the primary tool for applying security updates and bug fixes to Maximo Application Suite running on OpenShift. During an update the [IBM Maximo Operator Catalog](../catalogs/index.md) will be updated to the chosen version, which triggers an automatic update to all IBM operators installed from this catalog.

!!! note
    `mas update` will not update any other operator catalogs installed on the OpenShift cluster, including the Red Hat Operator Catalogs.

### Update vs. Upgrade
This guide is specifically for environments using **static catalogs**. If you are using the **dynamic catalog** then updates are automatically applied as soon as they are released.

The catalog update is applied at a cluster level. When we update, we don't update a specific operator running on the cluster, but rather the cluster as a whole. Everything in the cluster should be running at the latest version available in the catalog that is currently installed.

When applying a catalog update it will apply all the latest fixes for everything in the cluster (all MAS instances and all dependencies), ensuring that you're on a tested combination of patch levels across the board. There's no option to mix patch levels (e.g. keep one MAS instance on 8.9.4 and another on 8.9.5).

!!! important
    You must select a newer catalog than what is already in use. Updating to an older static catalog is not supported.

### Dependency Management
In addition to its primary role to update the IBM Maximo Operator Catalog (and verify the successful rollout of updated operators), the update command will also perform updates to a number of MAS dependencies controlled outside of the IBM Operator Catalog.

The update function will automatically search for and detect all of these dependencies and present a summary report that will describe the action it will take for the user to review before they launch the update (unless `--no-confirm` is set, in which case the update will start without prompt).

#### MongoDb & Kafka
Each version of the IBM Maximo Operator Catalog is certified against a specific version of MongoDb and Apache Kafka. Although other versions of both are supported, the goal of `mas update` is to ensure customers are running MongoDb & Kafka with the same latest bug fixes and security patches that we test the catalog with internally.

To this end, `mas update` will perform updates to both the installed MongoCE Operator and the MongoDbCommunity operand to align the version of the operator and the MongoDb cluster with the same version we have tested with. When a major version update is required, users will be prompted to approve the major version update and recommended to take a database backup. All other updates will be automatically applied.

For Kafka things work pretty much the same, although the version of the operator is out of our control because it is determined by the version of the Red Hat Operator Catalogs that are installed on the cluster. MAS update will however perform necessary updates to the Kafka operand to update the version of the Kafka instance at appropriate times.

#### IBM Cloud Pak for Data
Each version of the IBM Maximo Operator Catalog is certified compatible with a specific version of IBM Cloud Pak for Data (CP4D). It is not recommended to diverge from this compatible version because CP4D versioning is very brittle and even a small patch update to one of its services can create incompatibilities elsewhere.

### Automatic Migrations
Sometimes MAS dependencies go out of support and there is a need to migrate to an alternative. The MAS update function is designed to handle these migrations automatically, giving customers the benefit of a fully automated, well-tested migration path that they can rely on because it's the same migration path used by IBM internally and all other MAS customers.

#### IBM Certificate Manager
IBM Certificate-Manager is deprecated, its replacement is Red Hat Certificate-Manager. MAS customers updating from catalogs prior to **January 2024** will see IBM Certificate-Manager uninstalled, Red Hat Certificate-Manager installed, and all MAS instances automatically reconfigured to use the latter.

#### Grafana Operator v4
In December 2024 it was announced that support for the Grafana v4 Operator would cease later that month. MAS customers updating from a catalog older than **February 2024** will see their Grafana installation automatically migrated to the Grafana v5 Operator.

### Rollback Considerations
Undoing an update is a lot of work as it's reversing a lot of changes throughout the cluster. Generally it shouldn't be needed as updates are just bringing security and bug fixes. Think of it like applying a Windows update; there's no easy "undo" and if something slipped through we would fast track a new update so that rather than needing to revert from 8.9.5 to 8.9.4 there would be an 8.9.6 provided in double quick time that either reverted whatever caused the regression in 8.9.5 or addressed whatever the issue was.


Disconnected Update Preparation
-------------------------------------------------------------------------------
Before you start the update, you must mirror the images for the new catalog that you wish to update to. Mirroring the images is a simple but time consuming process. Three modes are available for the mirror process:

- **direct** - mirrors images directly from the source registry to your private registry
- **to-filesystem** - mirrors images from the source to a local directory
- **from-filesystem** - mirrors images from a local directory to your private registry

```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas mirror-images
```

You will be prompted to set the target registry for the image mirroring, to select the version of IBM Maximo Operator Catalog to mirror, and the subset of content that you wish to mirror. You can choose to mirror everything from the catalog, or control exactly what is mirrored to your private registry to reduce the time and bandwidth used to mirror the images, as well as reducing the storage requirements of the registry.

This command can also be run non-interactively. For full details refer to the [image mirroring](image-mirroring.md) guide.

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
    Make sure to select the release of MAS you currently have installed in the cluster. If you have multiple instances of MAS in the cluster running different releases then you must run the mirror command multiple times to ensure that you have mirrored the content for all releases of MAS that are in use in the cluster.


Update Maximo Application Suite
-------------------------------------------------------------------------------
Run `mas update` and choose the catalog to update to. This will update the operator catalog installed in your cluster, and the Operator Lifecycle Manager (OLM) will automatically update all installed operators to the newest version available on the current subscription channel.

### Interactive Update
```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas update
```

### Non-Interactive Update
```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas update -c @@MAS_LATEST_CATALOG@@ --no-confirm
```
