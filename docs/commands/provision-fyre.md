Provision OCP on FYRE
===============================================================================

Usage
-------------------------------------------------------------------------------
`mas provision-fyre [options]`

### FYRE Credentials
- `-u|--username FYRE_USERNAME` FYRE username
- `-a|--apikey FYRE_APIKEY` FYRE API key

### Cluster Configuration
- `-p|--product-id FYRE_PRODUCT_ID` FYRE product group ID that will own the cluster
- `-q|--quota-type FYRE_QUOTA_TYPE` Declare the quota to use when provisioning the cluster ("quick_burn" or "product_group")
- `-c|--cluster-name CLUSTER_NAME` Name of the cluster to be provisioned (lowercase only)
- `-v|--ocp-version OCP_VERSION` OCP version to use (e.g 4.13, 4.14)
- `-d|--description FYRE_DESCRIPTION` Description of the OCP cluster

### Worker Node Configuration
- `--worker-count FYRE_WORKER_COUNT` Number of worker nodes to provision
- `--worker-cpu FYRE_WORKER_CPU` How many CPUs to allocate per worker node
- `--worker-memory FYRE_WORKER_MEMORY` How much memory to allocate per worker node
- `--worker-additional-disks FYRE_WORKER_ADDITIONAL_DISKS` Comma-seperated list of additional disks (in Gb) added to each worker node (e.g. "200,200")
- `--fyre-cluster-size FYRE_CLUSTER_SIZE` When Fyre Quick Burn, defines the size category ("medium" or "large")

### Storage Provisioner Configuration
- `--no-storage`  Disable setup of the nfs-client storage class
- `--nfs-image-registry-size FYRE_NFS_IMAGE_REGISTRY_SIZE` Defines the image registry storage size when configured to use NFS (default 100gb). The size allocated cannot be superior of storage available in the Fyre Infrastructure node.

### Other Commands
- `--no-confirm` Provision the cluster without prompting for confirmation
- `-h|--help` Show this help message

Examples
-------------------------------------------------------------------------------
### Interactive Mode
```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas provision-fyre
```

### Non-Interactive Mode
```bash
export FYRE_USERNAME=xxx
export FYRE_APIKEY=xxx
docker run -ti --rm --pull always quay.io/ibmmas/cli mas provision-fyre \
  -u $FYRE_USERNAME -a $FYRE_APIKEY \
  -p 225 -q product_group \
  -c masonfyre -d "My Cluster" -v 4.15 \
  --worker-count 3 --worker-cpu 8 --worker-memory 32 \
  --no-confirm
```
