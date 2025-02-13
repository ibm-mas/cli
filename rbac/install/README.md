MAS Install Minimal RBAC
===============================================================================
By default the MAS install pipeline will run under an automatically created service account that is granted the **cluster-admin** ClusterRole.  Some customers may wish to run the install pipeline under a more restricted service account, to achieve this the install should be started with the `--service-account` optional command flag denoting the service account to use, this will instruct the installer not to create a new service account and to use the account identified by this parameter.

The minimal permissions required to run `mas install` are captured here in the **user** and **pipeline** folders.  The RBAC defintions here will create two service accounts:

- `mas-{{mas_instance_id}}-user`
- `mas-{{mas_instance_id}}-pipeline`

The **user account** provices the minimum permissions to successfully run the `mas install` command.  The **pipeline account** provides the exact permissions required by the pipeline that will be started on the cluster to perform a **full** install of Maximo Application Suite with all applications and dependencies in place.

All **Roles**, **RoleBindings**, **ClusterRoles**, and **ClusterRoleBindings** are prefixed `mas:{{mas_instance_id}}:install-pipeline` or `mas:{{mas_instance_id}}:install-user`.


## Usage
To directly use these definitions we recommend using **kustomize** and **jinja** following the example below.  Note the `--service-account` flag passed to the CLI to inform it not to set up the default pipeline RBAC:

```bash
MAS_INSTANCE_ID=parkerda
# Install the minimal RBAC for the MAS install (as OpenShift administrator)
oc login --token xxx --server=https://c100-e.eu-gb.containers.cloud.ibm.com:30516
kustomize build rbac/install | jinja -D mas_instance_id $MAS_INSTANCE_ID | oc apply -f -

# Get the access token for the user
export INSTALL_TOKEN=$(oc -n mas-${MAS_INSTANCE_ID}-pipelines get secret mas-${MAS_INSTANCE_ID}-install-token -o jsonpath="{.data.token}" | base64 -d)
echo $INSTALL_TOKEN

# Login to the cluster (as MAS install user service account)
oc login --token $INSTALL_TOKEN --server https://c100-e.eu-gb.containers.cloud.ibm.com:30516

# Install MAS
docker run -ti --rm -v ~:/mnt/home --pull always quay.io/ibmmas/cli:13.6.0-pre.boeing bash -c "
  oc login --token $INSTALL_TOKEN --server=https://c100-e.eu-gb.containers.cloud.ibm.com:30516 &&
  mas install --mas-catalog-version v9-250206-amd64 --ibm-entitlement-key $IBM_ENTITLEMENT_KEY \
    --mas-channel 9.0.x --mas-instance-id ${MAS_INSTANCE_ID} --mas-workspace-id masdev --mas-workspace-name "My Workspace" \
    --storage-class-rwo "ibmc-block-gold" --storage-class-rwx "ibmc-file-gold-gid" \
    --storage-pipeline "ibmc-file-gold-gid" --storage-accessmode "ReadWriteMany" \
    --license-file "/mnt/home/entitlement.lic" \
    --uds-email "parkerda@uk.ibm.com" --uds-firstname "David" --uds-lastname "Parker" \
    --mongodb-namespace "mongoce" \
    --accept-license --no-confirm --service-account mas-${MAS_INSTANCE_ID}-install-pipeline
  "
```

## Tip
You can view the effective permissions of the MAS service accounts in specific namespaces using `oc auth` as below:

```bash
oc auth can-i --list --as=system:serviceaccount:mas-${MAS_INSTANCE_ID}-pipelines:mas-${MAS_INSTANCE_ID}-install-pipeline -n openshift-marketplace
oc auth can-i --list --as=system:serviceaccount:mas-${MAS_INSTANCE_ID}-pipelines:mas-${MAS_INSTANCE_ID}-install-user -n openshift-marketplace
```