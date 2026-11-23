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


OLM Install Plan Approval
-------------------------------------------------------------------------------
The OLM install plan approval mode is not chosen at update time — it was chosen at install time and is a property of the cluster.  Because a catalog update rolls **every** subscription installed from the IBM Maximo Operator Catalog, `mas update` detects the aggregate approval mode across the whole cluster before launching the pipeline, reports it in the review settings, and passes it to the pipeline so the update behaves consistently with how you set things up:

- **Automatic** — every subscription in the cluster is Automatic: install plans generated by the update are applied without pausing.
- **Manual** — every subscription in the cluster is Manual: install plans generated by the update wait for your approval.  The task logs display what is pending and the `oc patch` command to grant approval (or use the OpenShift Console), and the update resumes automatically once the approval is given.
- **Mixed** — both modes are present (for example OLM auto-created dependency subscriptions in a Manual namespace): reported with counts, and treated as Manual — the Manual subscriptions gate on approval while the Automatic ones roll freely.

A wait budget is an operational choice rather than a setup choice, so `--olm-approval-timeout` (seconds, budgeting **each individual** approval wait; default 7200 = 2 hours) is available on the update command, along with the `OLM_APPROVAL_TIMEOUT` environment variable.  There is deliberately no `--olm-approval-mode` flag on `mas update`:

```bash
mas update -c @@MAS_LATEST_CATALOG@@ --olm-approval-timeout 7200 --no-confirm
```

| Variable               | Description                                 |
| ---------------------- | ------------------------------------------- |
| `OLM_APPROVAL_TIMEOUT` | Seconds to wait for each individual install plan approval when the cluster uses manual approval |

!!! note
    Just like on install, an Automatic-mode update **fails fast** when it encounters install plans that are already waiting for approval (for example after a previous Manual-mode run) — with the approve commands and the remedy in the error message, rather than hanging the subscription/workload verification tasks.  Approve the pending install plans (or re-run after they are approved) to proceed.

For the full details see the [ansible-devops OLM manual approvals documentation](https://ibm-mas.github.io/ansible-devops/olm-manual-approvals/).
