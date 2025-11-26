Minimal RBAC for MAS
===============================================================================

Disclaimer
-------------------------------------------------------------------------------
This is a work in progress, for more information see the following issues:

- [#1471 Provide minimal RBAC for full MAS install](https://github.com/ibm-mas/cli/issues/1471)
- [#1472 Create minimal RBAC for update](https://github.com/ibm-mas/cli/issues/1472)
- [#1473 Create minimal RBAC for upgrade](https://github.com/ibm-mas/cli/issues/1473)


Introduction
-------------------------------------------------------------------------------
By default the MAS CLI is expected to be ran with the **cluster-admin** ClusterRole, and the pipelines it launches will run under an automatically created service account that is granted the same ClusterRole.

Some customers may wish to work with MAS under a more restricted access level, to achieve this the CLI supports an optional `--service-account` parameter denoting the service account to use instead of creating one and assigning it cluster-admin permissions.


Install
-------------------------------------------------------------------------------
The minimal permissions required to run `mas install` are captured in the [/rbac/install](https://github.com/ibm-mas/cli/tree/master/rbac/install) under separate **user** and **pipeline** folders.  The RBAC definitions here can be used as a starting point to build the exact permissions user, and service account you wish to run the install with or can be used as-is.

When used as-is they will result in two service accounts being created:

- `mas-{{mas_instance_id}}-user`
- `mas-{{mas_instance_id}}-pipeline`

The **user account** provices the minimum permissions to successfully run the `mas install` command.  The **pipeline account** provides the exact permissions required by the pipeline that will be started on the cluster to perform the install.

All **Roles**, **RoleBindings**, **ClusterRoles**, and **ClusterRoleBindings** are prefixed `mas:{{mas_instance_id}}:install-pipeline` or `mas:{{mas_instance_id}}:install-user`.

!!! important
    The RBAC definitions here are only sufficient to install MAS Core Platform & it's dependencies, we are actively working on expanding this to cover the entire suite and all dependencies.

To directly use these definitions you will want to use **kustomize** and **jinja**, following the steps below.  Note the `--service-account` flag passed to the CLI to inform it not to set up the default pipeline RBAC:

```bash
MAS_INSTANCE_ID=dev1
export SERVER=https://myocp.net
# Install the minimal RBAC for the MAS install (as OpenShift administrator)
oc login --token xxx --server=$SERVER
export mas_instance_id=$MAS_INSTANCE_ID
kustomize build rbac/install > rbac-install.yaml
jinjanate rbac-install.yaml | oc apply -f -

# Get the access token for the user
export INSTALL_TOKEN=$(oc -n mas-${MAS_INSTANCE_ID}-pipelines get secret mas-${MAS_INSTANCE_ID}-install-token -o jsonpath="{.data.token}" | base64 -d)
echo $INSTALL_TOKEN

# Login to the cluster (as MAS install user service account)
oc login --token $INSTALL_TOKEN --server $SERVER

# Install MAS (using IBMCloud storage classes)
docker run -ti --rm -v ~:/mnt/home --pull always quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ bash -c "
  oc login --token $INSTALL_TOKEN --server=$SERVER &&
  mas install --mas-catalog-version @@MAS_LATEST_CATALOG@@ --ibm-entitlement-key $IBM_ENTITLEMENT_KEY \
    --mas-channel 9.1.x --mas-instance-id ${MAS_INSTANCE_ID} --mas-workspace-id masdev --mas-workspace-name "My Workspace" \
    --storage-class-rwo "ibmc-block-gold" --storage-class-rwx "ibmc-file-gold-gid" \
    --storage-pipeline "ibmc-file-gold-gid" --storage-accessmode "ReadWriteMany" \
    --license-file "/mnt/home/entitlement.lic" \
    --contact-email "parkerda@uk.ibm.com" --contact-firstname "David" --contact-lastname "Parker" \
    --mongodb-namespace "mongoce" \
    --accept-license --no-confirm --service-account mas-${MAS_INSTANCE_ID}-install-pipeline
  "
```

Tip
-------------------------------------------------------------------------------
You can view the effective permissions of the MAS service accounts in specific namespaces using `oc auth` as below:

```bash
oc auth can-i --list --as=system:serviceaccount:mas-${MAS_INSTANCE_ID}-pipelines:mas-${MAS_INSTANCE_ID}-install-pipeline -n openshift-marketplace

oc auth can-i --list --as=system:serviceaccount:mas-${MAS_INSTANCE_ID}-pipelines:mas-${MAS_INSTANCE_ID}-install-user -n openshift-marketplace
```
