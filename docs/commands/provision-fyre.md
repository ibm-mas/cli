# Provision OCP on FYRE

## Usage
`mas provision-fyre [options]`

### FYRE Credentials
Required

- `-u|--username FYRE_USERNAME` FYRE username
- `-a|--apikey FYRE_APIKEY` FYRE API key

### Cluster Configuration
Required

- `-p|--product-id FYRE_PRODUCT_ID` FYRE product group ID that will own the cluster
- `-q|--quota-type FYRE_QUOTA_TYPE` Declare the quota to use when provisioning the cluster ("quick_burn" or "product_group")
- `-c|--cluster-name CLUSTER_NAME` Name of the cluster to be provisioned
- `-v|--ocp-version OCP_VERSION` OCP version to use (e.g 4.8, 4.10)
- `-d|--description FYRE_DESCRIPTION` Description of the OCP cluster

### Worker Node Configuration
Optional, only takes effect when quota-type is set to "product_group"

- `--worker-count FYRE_WORKER_COUNT` Number of worker nodes to provision
- `--worker-cpu FYRE_WORKER_CPU` How many CPUs to allocate per worker node
- `--worker-memory FYRE_WORKER_MEMORY` How much memory to allocate per worker node

### Other Commands
- `-s|--simulate-airgap` Set flag to apply the simulated airgap network configuration to the cluster after provisioning
- `--no-confirm` Provision the cluster without prompting for confirmation
- `-h|--help` Show this help message


## Examples
### Interactive Mode
```bash
docker pull quay.io/ibmmas/cli
docker run -ti --rm quay.io/ibmmas/cli mas provision-fyre
```

### Non-Interactive Mode
```bash
export FYRE_USERNAME=xxx
export FYRE_APIKEY=xxx
docker pull quay.io/ibmmas/cli
docker run -ti --rm quay.io/ibmmas/cli mas provision-fyre -u $FYRE_USERNAME -a $FYRE_APIKEY -p 225 -q product_group -c masonfyre -d "My Cluster" -v 4.10 --worker-count 3 --worker-cpu 8 --worker-memory 32 --no-confirm
```
