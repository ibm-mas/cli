MAS Install Minimal RBAC
===============================================================================
The minimal permissions required to run `mas install` are captured here.  The RBAC defintions here will create two service accounts:

- `mas-{{mas_instance_id}}-user`
- `mas-{{mas_instance_id}}-pipeline`

The **user account** is provided the minimum permissions to successfully run the `mas install` command.  The **pipeline account** is provided the exact permissions required to perform a **full** install of Maximo Application Suite with all applications and dependencies in place.

The two **ClusterRoleBindings** are named `mas:{{mas_instance_id}}:install-pipeline` and `mas:{{mas_instance_id}}:install-user`, each **RoleBinding** will be created in the format: `mas:{{mas_instance_id}}:install-pipeline:{{namespace}}`.


## Usage
To directly use these definition you can follow the example below, note the flag passed to the CLI to inform it not to set up the default pipeline service account RBAC:

```bash
MAS_INSTANCE_ID=parkerda
# Install the minimal RBAC for the MAS install
oc login --token $INSTALL_TOKEN --server=https://c100-e.eu-gb.containers.cloud.ibm.com:31350
kustomize build . | jinja -D mas_instance_id $MAS_INSTANCE_ID | oc apply -f -

# Get the access token for the user
INSTALL_TOKEN=$(oc -n mas-${MAS_INSTANCE_ID}-pipelines get secret masinstall-token -o jsonpath="{.data.token}" | base64 -d)
echo $INSTALL_TOKEN

# Login to the cluster
oc login --token $INSTALL_TOKEN --server https://c100-e.eu-gb.containers.cloud.ibm.com:31350

# Install MAS
docker run -ti --rm -v ~:/mnt/home --pull always quay.io/ibmmas/cli:13.3.0 bash -c "
  oc login --token $INSTALL_TOKEN --server=https://c100-e.eu-gb.containers.cloud.ibm.com:31350 &&
  mas install --mas-catalog-version v9-250206-amd64 --ibm-entitlement-key $IBM_ENTITLEMENT_KEY \
    --mas-channel 9.0.x --mas-instance-id parkerda --mas-workspace-id masdev --mas-workspace-name "My Workspace" \
    --storage-class-rwo "ibmc-block-gold" --storage-class-rwx "ibmc-file-gold-gid" \
    --storage-pipeline "ibmc-file-gold-gid" --storage-accessmode "ReadWriteMany" \
    --license-file "/home/david/entitlement.lic" \
    --uds-email "parkerda@uk.ibm.com" --uds-firstname "David" --uds-lastname "Parker" \
    --mongodb-namespace "mongoce" \
    --accept-license --no-confirm
  "
```
