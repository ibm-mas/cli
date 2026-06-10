Must-Gather
===============================================================================

Overview
-------------------------------------------------------------------------------
The must-gather tool collects diagnostic information from IBM Maximo Application Suite (MAS) installations on OpenShift clusters. It gathers cluster resources, application configurations, logs, and other diagnostic data into a compressed archive for troubleshooting and support purposes.

Usage
-------------------------------------------------------------------------------
:::mas-cli-usage
module: mas.cli.must_gather.arg_parser
parser: mustGatherArgParser
ignore_description: true
ignore_epilog: true
:::

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
│   |   |   └── subscriptions.txt
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

### Basic Collection
Collect data for all MAS instances, critical cluster resources, and most MAS dependencies (Db2, Cloud Pak Foundational Services, Cloud Pak for Data, etc).

```bash
uvx mas-cli must-gather -d /mnt/home/must-gather
```

### Include Secret Data
By default secret data is not included in the must-gather archive, only the existence of the secret is recorded and how many fields it contains. Adding the `--secret-data` flag will trigger the inclusion of the secret data as well.

```bash
uvx mas-cli must-gather -d /mnt/home/must-gather --secret-data
```

### Quick Collection
This must-gather will omit pod logs, it runs faster but collects less diagnostic data.

```bash
uvx mas-cli must-gather -d /mnt/home/must-gather --no-logs
```

### Target Specific MAS Instance
By setting `--mas-instance-ids` to a comma-separated list of instance IDs you can instruct the must-gather to focus on specific instances only.

```bash
uvx mas-cli must-gather -d /mnt/home/must-gather --mas-instance-ids inst1
```

### Target Specific Applications
Setting `--mas-app-ids` to a comma-separated list of MAS application IDs will restrict the MAS-specific must-gather to those applications only, which can be combined with `--collectors` & `--mas-instance-ids` to focus the collection to a specific namespace/MAS application.

```bash
# Target Core in inst1, skip OCP and dependencies
uvx mas-cli must-gather -d /mnt/home/must-gather --collectors mas --mas-instance-ids "inst1" --mas-app-ids "core"

# Target Core + Manage in inst2, skip OCP and dependencies
uvx mas-cli must-gather -d /mnt/home/must-gather --collectors mas --mas-instance-ids "inst2" --mas-app-ids "core,manage"

# Collect only MAS and SLS, skip OCP and other dependencies
uvx mas-cli must-gather -d /mnt/home/must-gather --collectors mas,sls --mas-instance-ids "inst3" --mas-app-ids "manage"
```

### Containerized Execution
You can also run the must-gather in a containerized environment:

Using Docker:

```bash
docker run --rm -v /~:/mnt/home:z quay.io/ibmmas/cli /bin/bash -c "oc login --token=sha256~XFnSk...fc8U --server=https://api.<openshift domain>:6443/ --insecure-skip-tls-verify; mas must-gather -d /mnt/home/must-gather"
```

Or using Podman:

```bash
podman run --rm -v /data:/mnt/home:z quay.io/ibmmas/cli /bin/bash -c "oc login --token=sha256~XFnSk...fc8U --server=https://api.<openshift domain>:6443/ --insecure-skip-tls-verify; mas must-gather -d /mnt/home/must-gather"