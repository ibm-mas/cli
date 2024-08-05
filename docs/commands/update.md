Update
===============================================================================

Usage
-------------------------------------------------------------------------------
Usage information can be obtained using `mas update --help`

```
usage: mas update [-c MAS_CATALOG_VERSION] [--db2-namespace DB2_NAMESPACE] [--mongodb-namespace MONGODB_NAMESPACE] [--mongodb-v5-upgrade] [--mongodb-v6-upgrade]
                  [--kafka-namespace KAFKA_NAMESPACE] [--kafka-provider {redhat,strimzi}] [--dro-migration DRO_MIGRATION]
                  [--dro-storage-class DRO_STORAGE_CLASS] [--dro-namespace DRO_NAMESPACE] [--no-confirm] [--skip-pre-check] [-h]

IBM Maximo Application Suite Admin CLI v100.0.0
Update the IBM Maximo Operator Catalog, and related MAS dependencies by configuring and launching the MAS Update Tekton Pipeline.

Interactive Mode:
Omitting the --catalog option will trigger an interactive prompt

Catalog Selection:
  -c MAS_CATALOG_VERSION, --catalog MAS_CATALOG_VERSION
                                                  Maximo Operator Catalog Version (e.g. @@MAS_LATEST_CATALOG@@)

Update Dependencies:
  --db2-namespace DB2_NAMESPACE                   Namespace where Db2u operator and instances will be updated
  --mongodb-namespace MONGODB_NAMESPACE           Namespace where MongoCE operator and instances will be updated
  --mongodb-v5-upgrade                            Required to confirm a major version update for MongoDb to version 5
  --mongodb-v6-upgrade                            Required to confirm a major version update for MongoDb to version 6
  --kafka-namespace KAFKA_NAMESPACE               Namespace where Kafka operator and instances will be updated
  --kafka-provider {redhat,strimzi}               The type of Kakfa operator installed in the target namespace for updte

UDS to DRO Migration:
  --dro-migration DRO_MIGRATION                   Required to confirm the migration from IBM User Data Services (UDS) to IBM Data Reporter Operator (DRO)
  --dro-storage-class DRO_STORAGE_CLASS           Set Custom RWO Storage Class name for DRO as part of the update
  --dro-namespace DRO_NAMESPACE                   Set Custom Namespace for DRO(Default: redhat-marketplace)

More:
  --no-confirm                                    Launch the upgrade without prompting for confirmation
  --skip-pre-check                                Skips the 'pre-update-check' and 'post-update-verify' tasks in the update pipeline
  -h, --help                                      Show this help message and exit
```

Overview
-------------------------------------------------------------------------------
The `mas update` function is the primary tool for applying security updates and bug fixes to Maximo Application Suite running on OpenShift.  During an update the [IBM Maximo Operator Catalog](/catalogs/) will be updated to the chosen version, this will trigger an automatic update to all IBM operators installed from this catalog.

!!! note
    Note that `mas update` will not update any other operator catalogs installed on the OpenShift cluster, including the Red Hat Operator Catalogs.

### Dependency Management
In addition to it's primary role to update the IBM Maximo Operator Catalog (and verify the successfull rollout of updated operators) the update command will also perform updates to a number of MAS dependencies controlled outside of the IBM Operator Catalog.

The update function will automatically search for and detect all of these dependencies and present a summary report that will describe the action it will take for the user to review before they launch the update (unless `--no-confirm` is set, in which case the update will start without prompt).

#### MongoDb & Kafka
Each version of the IBM Maximo Operator Catalog is certified against a specific version of MongoDb and Apache Kafka, although other versions of both are supported, the goal of `mas update` is to ensure customers' are running MongoDb & Kafka with the same latest bug fixes and security patches that we test the catalog with internally.

To this end `mas update` will perform updates to both the installed MongoCE Operator and the MongoDbCommunity operand to align the version of the operator and the MongoDb cluster with the same version we have tested with.  When a major version update is required users will be prompted to approve the major version update and recommended to take a database backup, all other updates will be automatically applied.

For Kafka things work pretty much the same; although the version of the operator is out of our control because it is determined by the version of the Red Hat Operator Catalogs that are installed on the cluster.  MAS update will however perform necessary updates to the Kafka operand to update the version of the Kafka instance at appropriate times.

#### IBM Cloud Pak for Data
Each version of the IBM Maximo Operator Catalog is certified compatible with a specific version of IBM Cloud Pak for Data (CP4D), it is not recommended to diverge from this captible version because CP4D versioning is very brittle and even a small patch update to one of it's services can create incompatibilities elsewhere.


### Automatic Migrations
Sometimes MAS dependencies go out of support and there is a need to migrate to an alternative, the MAS update function is designed to handle these migrations automatically, giving customers the benefit of a fully automated, well-testing, migration path that they can rely on because it's the same migration path used by IBM internally and all other MAS customers.

#### UDS to DRO Migration
In November 2023 it was announced that IBM User Data Services (UDS) was being sunset, to be replaced by IBM Data Reporter Operator (DRO).  MAS customers updating from a catalog older than **February 2024** will see UDS uninstalled, DRO installed, and all MAS instances in the cluster automatically migrated to use the new DRO instance.

#### IBM Certificate Manager
IBM Certificate-Manager is deprecated, it's replacement is Red Hat Certificate-Manager.  MAS customers updating from catalogs prior to **January 2024** will see IBM Certificate-Manager uninstalled, Red Hat Certificate-Manager installed, and all MAS instances automatically reconfigured to use the latter.

#### Grafana Operator v4
In December 2024 is was announced that support for the Grafana v4 Operator would cease later that month, MAS customers updating from a catalog older than **February 2024** will see their Grafana installation automatically migrated to the Grafana v5 Operator.

Examples
-------------------------------------------------------------------------------
### Interactive Update
```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas update
```

### Non-Interactive Update
```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas update -c @@MAS_LATEST_CATALOG@@ --no-confirm
```
