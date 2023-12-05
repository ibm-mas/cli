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
You can execute the must gather from the cli image or in non-interactive mode.
To execute the must-gather from the cli image, start a mas cli container using docker or podman 
```bash
docker run -ti --rm -v /~:/mnt/home --pull always quay.io/ibmmas/cli
```

```bash
podman run -ti --rm -v /data:/mnt/home:z --pull always quay.io/ibmmas/cli
```

Before running the must-gather command, you must authenticate to OCP with oc login command
for more details you can refer to https://www.ibm.com/support/pages/node/6998647

For non-interactive mode, you need to provide the oc login command before the mas must gather command as shown in the example below:
```bash
podman run --rm -v /data:/mnt/home:z quay.io/ibmmas/cli /bin/bash -c "oc login --token=sha256~XFnSk...fc8U --server=https://api.<openshift domain>:6443/ --insecure-skip-tls-verify; mas must-gather -d /mnt/home/must-gather"
```

Examples
-------------------------------------------------------------------------------
### Complete Must-Gather
Running this command will save the must-gather file to a must-gather directory in your home directory.

```bash
mas must-gather -d /mnt/home/must-gather
```

### Quick Must-Gather
Running this command will save the must-gather file to a must-gather directory in your home directory.

```bash
mas must-gather -d /mnt/home/must-gather --summary-only
```

### Must-Gather for one MAS instance
```bash
mas must-gather -d /mnt/home/must-gather --mas-instance-ids inst1
```

### Must-Gather that includes the data of the secrets
```bash
mas must-gather -d /mnt/home/must-gather --secret-data
```

### Must-Gather that collects everything, including data for db2 and ibm-common-services namespaces and data for all secrets
```bash
mas must-gather -d /mnt/home/must-gather --secret-data --extra-namespaces "db2u,ibm-common-services"
```

### Must-Gather that collects only data for mas core for MAS instance "inst1"
```bash
mas must-gather -d /mnt/home/must-gather --no-ocp --no-dependencies --no-sls --mas-instance-ids "inst1" --mas-app-ids "core"
```

### Must-Gather that collects only data for mas core and mas manage for MAS instance "inst1"
```bash
mas must-gather -d /mnt/home/must-gather --no-ocp --no-dependencies --no-sls --mas-instance-ids "inst1" --mas-app-ids "core,manage"
```

### Execute the Must-Gather in non-interactive mode
```bash
docker run --rm -v /~:/mnt/home:z quay.io/ibmmas/cli /bin/bash -c "oc login --token=sha256~XFnSk...fc8U --server=https://api.<openshift domain>:6443/ --insecure-skip-tls-verify; mas must-gather -d /mnt/home/must-gather"
```

### Execute the Must-Gather in non-interactive mode using podman
```bash
podman run --rm -v /data:/mnt/home:z quay.io/ibmmas/cli /bin/bash -c "oc login --token=sha256~XFnSk...fc8U --server=https://api.<openshift domain>:6443/ --insecure-skip-tls-verify; mas must-gather -d /mnt/home/must-gather"
```