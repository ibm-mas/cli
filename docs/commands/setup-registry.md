Setup Private Registry
===============================================================================

Usage
-------------------------------------------------------------------------------
`mas setup-registry [options]`

### Registry Credentials (required)
- `-u|--username` Registry username
- `-p|--password` Registry password

### Registry Cluster Configuration (optional)
- `-n|--namespace` Registry namespace (default is airgap-registry)
- `-s|--storage-class` Registry storage class (default is ibmc-block-gold)
- `-c|--storage-capacity` Registry storage capacity (default is 2000Gi)
- `-t|--service-type` Registry service type (default is loadbalancer)

### Other Commands:
- `-h|--help` Show help message

Examples
-------------------------------------------------------------------------------

### Interactive Mode
```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas setup-registry
```

### Non-Interactive Mode
```bash
export REGISTRY_PASSWORD=xxx
docker run -ti --rm --pull always quay.io/ibmmas/cli mas setup-registry \
  -u my-registry-user \
  -p $REGISTRY_PASSWORD \
  -n airgap -s nfs-client \
  --service-type loadbalancer \
  --storage-capacity 2000Gi \
  --no-confirm
```