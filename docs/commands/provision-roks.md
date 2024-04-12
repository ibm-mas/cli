Provision OCP on IBMCloud ROKS
===============================================================================

Usage
-------------------------------------------------------------------------------
`mas provision-roks [options]`

### IBMCloud Credentials
- `-a|--apikey IBMCLOUD_APIKEY` IBMCloud API key

### Cluster Configuration
- `-r|--resource-group IBMCLOUD_RESOURCEGROUP` IBMCloud resource group to deploy the cluster in
- `-c|--cluster-name CLUSTER_NAME` Name of the cluster to be provisioned
- `-v|--ocp-version OCP_VERSION` OCP version to use (e.g 4.13_openshift, 4.14_openshift)

### Worker Node Configuration
- `--worker-count ROKS_WORKERS` Number of worker nodes to provision
- `--worker-flavor ROKS_FLAVOR` The flavour of worker node to use (e.g. b3c.16x64.300gb)
- `--worker-zone ROKS_ZONE` IBM Cloud zone where the cluster should be provisioned. (e.g. dal10)

### GPU Support
- `--gpu-worker-count GPU_WORKERS` Number of GPU worker nodes to provision
- `--gpu-workerpool-name GPU_WORKERPOOL_NAME` Name of the GPU workerpool

### Other Commands
- `--no-confirm` Provision the cluster without prompting for confirmation
- `-h|--help` Show help message


Examples
-------------------------------------------------------------------------------

### Interactive Mode
```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas provision-roks
```

### Non-Interactive Mode
```bash
export IBMCLOUD_APIKEY=xxx
docker run -ti --rm --pull always quay.io/ibmmas/cli mas provision-roks \
  -a $IBMCLOUD_APIKEY -r mas-development \
  -c masonroks -v 4.14_openshift \
  --worker-count 3 --worker-flavor b3c.16x64.300gb --worker-zone dal10 \
  --no-confirm
```
