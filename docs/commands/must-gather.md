Must gather
===============================================================================

Usage
-------------------------------------------------------------------------------
`mas must-gather [options]`

### Options
- `-d|--directory MG_DIR` Directory where the must-gather will be saved, defaults to `/tmp/must-gather` (or `/must-gather` if the directory exists)
- `-k|--keep-files` Do not delete individual files after creating the must-gather compressed tar archive
- `--summary-only` Perform a much faster must-gather that only gathers high level summary of resources in the cluster
- `--no-pod-logs` Skip collection of pod logs, greatly speeds up must-gather collection time when pod logs are not required
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

Examples
-------------------------------------------------------------------------------
### Complete Must-Gather
Running this command will save the must-gather file to a must-gather directory in your home directory.

```bash
docker run -ti --rm -v /~:/mnt/home --pull always quay.io/ibmmas/cli mas must-gather -d /mnt/home/must-gather
```

### Quick Must-Gather
Running this command will save the must-gather file to a must-gather directory in your home directory.

```bash
docker run -ti --rm -v /~:/mnt/home --pull always quay.io/ibmmas/cli mas must-gather -d /mnt/home/must-gather --summary-only
```

