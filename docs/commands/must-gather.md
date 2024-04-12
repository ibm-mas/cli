Must gather
===============================================================================

Usage
-------------------------------------------------------------------------------
`mas must-gather [options]`

### Destination
- `-d|--directory MG_DIR` Directory where the must-gather will be saved, defaults to `/tmp/must-gather` (or `/must-gather` if the directory exists)
- `-k|--keep-files` Do not delete individual files after creating the must-gather compressed tar archive

### General Controls
- `--summary-only` Perform a much faster must-gather that only gathers high level summary information
- `--no-logs` Skip collection of pod logs, greatly speeds up must-gather collection time when pod logs are not required
- `--secret-data` Include secrets content in the must-gather

### MAS Content Controls:
- `--mas-instance-ids` Limit must-gather to a list of MAS instance IDs (comma-seperated list)
- `--mas-app-ids` Limit must-gather to a subset of MAS namespaces (comma-seperated list)

### Disable Collectors:
- `--no-ocp` Disable must-gather for the OCP cluster itself
- `--no-dependencies` Disable must-gather for in-cluster dependencies (Db2, Cloud Pak for Data, Cloud Pak Foundational Services, Mongo)
- `--no-sls` Disable must-gather for IBM Suite License Service

### Additional Collectors:
- `--extra-namespaces` Enable must-gather in custom namespaces (comma-seperated list)

### Artifactory Upload:
- `--artifactory-token ARTIFACTORY_TOKEN` Provide a token for Artifactory to automatically upload the file to `ARTIFACTORY_UPLOAD_DIRECTORY`
- `--artifactory-upload-directory ARTIFACTORY_UPLOAD_DIRECTORY` Working URL to the root directory in Artifactory where the must-gather file should be uploaded


Content
-------------------------------------------------------------------------------

```
/must-gather/
├── 20230423-204411
│   ├── reconcile-logs
│   │   └── mas-inst1-core
│   │   |   ├── Suite
│   │   |   │   └── 20230423-172432.log
│   │   |   │   └── 20230423-204010.log
│   │   |   ├── Workspace
│   │   |   │   └── 20230423-113224.log
│   │   |   └── MongoCfg
│   │   |       └── 20230423-130043.log
│   ├── resources
│   │   ├── _cluster
│   |   │   ├── clusterversions.txt
│   |   │   ├── namespaces.txt
│   |   │   ├── operatorconditions.txt
│   |   │   ├── packagemanifests.txt
│   |   │   └── storageclasses.txt
│   │   ├── mas-inst1-core
│   │   |   ├── clusterserviceversions
│   │   |   │   └── <contain definition of every ClusterServiceVersion in the namespace>
│   │   |   ├── configmaps
│   │   |   │   ├── ibm-cpp-config.yaml
│   │   |   │   └── ibm-licensing-upload-config.yaml
│   │   |   ├── deployments
│   │   |   │   ├── inst1-coreapi.yaml
│   │   |   │   └── isnt2-internalapi.yaml
│   │   |   ├── installplans
│   │   |   │   └── <contain definition of every InstallPlan in the namespace>
│   │   |   ├── jobs
│   │   |   │   └── <contain definition of every Job in the namespace>
│   │   |   ├── operatorconditions
│   │   |   │   └── <contain definition of every OperatorCondition in the namespace>
│   │   |   ├── pods
│   │   |   │   ├── app1
│   │   |   │   |   ├── logs
│   │   |   │   |   |   └── inst1-coreapi-28037940-njx4_coreapi.log
│   │   |   │   |   ├── inst1-coreapi-28037940-njx4.txt
│   │   |   │   |   └── inst1-coreapi-28037940-njx4.yaml
│   │   |   │   ├── app2
│   │   |   │   └── app3
│   │   |   ├── pvc
│   │   |   │   └── <contain definition of every PVC in the namespace>
│   │   |   ├── roles
│   │   |   │   └── <contain definition of every Role in the namespace>
│   │   |   ├── rolebindings
│   │   |   │   └── <contain definition of every RoleBinding in the namespace>
│   │   |   ├── routes
│   │   |   │   └── <contain definition of every Route in the namespace>
│   │   |   ├── secrets
│   │   |   │   └── <contain definition of every Secret in the namespace>
│   │   |   ├── serviceaccounts
│   │   |   │   └── <contain definition of every ServiceAccount in the namespace>
│   │   |   ├── services
│   │   |   │   └── <contain definition of every Service in the namespace>
│   │   |   ├── statefulsets
│   │   |   │   └── <contain definition of every StatefulSet in the namespace>
│   │   |   ├── subscriptions
│   │   |   │   └── <contain definition of every Subscription in the namespace>
│   │   |   ├── clusterserviceversions.txt
│   │   |   ├── configmaps.txt
│   │   |   ├── deployments.txt
│   │   |   ├── installplans.txt
│   │   |   ├── jobs.txt
│   │   |   ├── operatorconditions.txt
│   |   │   ├── pods.txt
│   |   │   ├── pvc.txt
│   |   │   ├── roles.txt
│   |   │   ├── rolebindings.txt
│   |   │   ├── routes.txt
│   |   │   ├── secrets.txt
│   |   │   ├── serviceaccounts.txt
│   |   │   ├── services.txt
│   |   │   ├── statefulsets.txt
│   │   |   └── subscriptions.txt
│   │   └── mas-inst1-appId
│   │   |   └── <contain must-gather from mas-inst1-appId>
│   │   ├── mas-inst2-core
│   │   |   └── <contain must-gather from mas-inst2-core>
│   │   └── mas-inst2-appId
│   │       └── <contain must-gather from mas-inst2-appId>
│   ├── cp4d.txt
│   ├── db2u.txt
│   ├── ibm-common-services.txt
│   ├── mas-inst1-core.txt
│   ├── mas-inst1-appId.txt
│   ├── mas-inst2-core.txt
│   ├── mas-inst2-appId.txt
└── must-gather-20230423-204411.tgz
```


Usage
-------------------------------------------------------------------------------
As with other CLI functions, the must-gather will run against the currently connected cluster, use `oc login` to connect to a cluster before running `mas must-gather`.

```bash
# Start the container in docker
docker run -ti --rm -v /~:/mnt/home --pull always quay.io/ibmmas/cli
# Login to the cluster and run the must-gather, which will be available in the home directory on the local system
oc login --token=xxx --server=https://xxx:xxx
mas must-gather -d /mnt/home/must-gather
```

```bash
# Start the container in podman
podman run -ti --rm -v /~:/mnt/home:z --pull always quay.io/ibmmas/cli
# Login to the cluster and run the must-gather, which will be available in the home directory on the local system
oc login --token=xxx --server=https://xxx:xxx
mas must-gather -d /mnt/home/must-gather
```


Examples
-------------------------------------------------------------------------------

**Cluster-scoped must-gather:** Collect data for all MAS instances, critical cluster resources, and most MAS dependencies (Db2, Cloud Pak Foundational Services, Cloud Pak for Data, etc).

```bash
mas must-gather -d /mnt/home/must-gather
```

**Include secret data:** By default secret data is not included in the must-gather archive, only the existence of the secret is recorded and how many fields it contains.  Adding the `--secret-data` flag will trigger the inclusion of the secret data as well.

```bash
mas must-gather -d /mnt/home/must-gather --secret-data
```

**Quick must-gather:** This must-gather will omit pod logs and details of standard Kubernetes resources, it runs incredibly fast but it's usage is situational.

```bash
mas must-gather -d /mnt/home/must-gather --summary-only
```

**Target a specific MAS instance:** By setting `---mas-instance-ids` to a comma-separated list of instance IDs you can instruct the must-gather to focus on specific instances only.

```bash
mas must-gather -d /mnt/home/must-gather --mas-instance-ids inst1
```

**Target specific applications:**  Setting `--mas-app-ids` to a comma-separated list of MAS application IDs will restict the MAS-specific must-gather to those applications only, which can be combined with `--no-ocp`, `--no-dependencies`, `--no-sls`, & `--mas-instance-ids` to focus the collection to a specific namespace/MAS application.

```bash
# Target Core in inst1
mas must-gather -d /mnt/home/must-gather --no-ocp --no-dependencies --no-sls --mas-instance-ids "inst1" --mas-app-ids "core"

# Target Core + Manage in inst2
mas must-gather -d /mnt/home/must-gather --no-ocp --no-dependencies --no-sls --mas-instance-ids "inst2" --mas-app-ids "core,manage"
```

### Execute the Must-Gather in non-interactive mode
```bash
docker run --rm -v /~:/mnt/home:z quay.io/ibmmas/cli /bin/bash -c "oc login --token=sha256~XFnSk...fc8U --server=https://api.<openshift domain>:6443/ --insecure-skip-tls-verify; mas must-gather -d /mnt/home/must-gather"
```

### Execute the Must-Gather in non-interactive mode using podman
```bash
podman run --rm -v /data:/mnt/home:z quay.io/ibmmas/cli /bin/bash -c "oc login --token=sha256~XFnSk...fc8U --server=https://api.<openshift domain>:6443/ --insecure-skip-tls-verify; mas must-gather -d /mnt/home/must-gather"
```