Must gather
===============================================================================

Usage
-------------------------------------------------------------------------------
`mas must-gather [options]`

### Options
- `-d|--directory MG_DIR` Directory where the must-gather will be saved, defaults to `/tmp/must-gather`
- `--summary-only` Perform a much faster must-gather that only gathers high level summary of resources in the cluster
- `--no-pod-logs` Skip collection of pod logs, greatly speeds up must-gather collection time when pod logs are not required
- `--artifactory-token ARTIFACTORY_TOKEN` Provide a token for Artifactory to automatically upload the file to `ARTIFACTORY_UPLOAD_DIRECTORY`
- `--artifactory-upload-directory ARTIFACTORY_UPLOAD_DIRECTORY` Working URL to the root directory in Artifactory where the must-gather file should be uploaded

Content
-------------------------------------------------------------------------------

```
tmp/must-gather/
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
│   │   └── mas-inst1-core
│   │   |   ├── configmaps
│   │   |   │   ├── ibm-cpp-config.yaml
│   │   |   │   └── ibm-licensing-upload-config.yaml
│   │   |   ├── deployments
│   │   |   │   ├── inst1-coreapi.yaml
│   │   |   │   └── isnt2-internalapi.yaml
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
│   │   |   ├── routes
│   │   |   │   └── <contain definition of every Route in the namespace>
│   │   |   ├── secrets
│   │   |   │   └── <contain definition of every Secret in the namespace>
│   │   |   ├── services
│   │   |   │   └── <contain definition of every Service in the namespace>
│   │   |   ├── statefulsets
│   │   |   │   └── <contain definition of every StatefulSet in the namespace>
│   │   |   ├── configmaps.txt
│   │   |   ├── deployments.txt
│   |   │   ├── pods.txt
│   |   │   ├── pvc.txt
│   |   │   ├── routes.txt
│   |   │   ├── secrets.txt
│   |   │   ├── services.txt
│   |   │   └── statefulsets.txt
│   │   └── mas-inst1-appId
│   │       ├── configmaps
│   │       │   └── <contain definition of every ConfigMap in the namespace>
│   │       ├── deployments
│   │       │   └── <contain definition of every Deployment in the namespace>
│   │       ├── pods
│   │       │   └── <contain definition of every Pod in the namespace>
│   │       ├── pvc
│   │       │   └── <contain definition of every PVC in the namespace>
│   │       ├── routes
│   │       │   └── <contain definition of every Route in the namespace>
│   │       ├── secrets
│   │       │   └── <contain definition of every Secret in the namespace>
│   │       ├── services
│   │       │   └── <contain definition of every Service in the namespace>
│   │       ├── statefulsets
│   │       │   └── <contain definition of every StatefulSet in the namespace>
│   │       ├── configmaps.txt
│   │       ├── deployments.txt
│   |       ├── pods.txt
│   |       ├── pvc.txt
│   |       ├── routes.txt
│   |       ├── secrets.txt
│   |       ├── services.txt
│   |       └── statefulsets.txt
│   ├── cp4d.txt
│   ├── db2u.txt
│   ├── ibm-common-services.txt
│   ├── mas-inst1-core.txt
│   ├── mas-inst1-appId.txt
│   ├── mas-inst2-core.txt
│   ├── mas-inst2-appId.txt
│   └── namespaces.txt
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

