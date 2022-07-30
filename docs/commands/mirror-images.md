# Mirror Images

## Usage
`mas mirror-images [options]`

### Registry Details (Required):
- `-H|--host REGISTRY_PUBLIC_HOST` Hostname of the target registry
- `-P|--port REGISTRY_PUBLIC_PORT` Port number for the target registry

### Registry Authentication (Optional):
- `-u|--username REGISTRY_USERNAME` Username to authenticate to the target registry
- `-p|--password REGISTRY_PASSWORD` Password to authenticate to the target registry

### Source Registry Entitlements (Required):
- `--ibm-entitlement IBM_ENTITLEMENT_KEY` IBM Entitlement Key
- `--redhat-username REDHAT_CONNECT_USERNAME` Red Hat Connect Username
- `--redhat-password REDHAT_CONNECT_PASSWORD` Red Hat Connect Password

### Maximo Operator Catalog Selection (Required):
- `-c|--catalog MAS_CATALOG_VERSION` Maximo Operator Catalog Version to mirror (e.g. v8-220717)
- `--mirror-core` Mirror images for IBM Maximo Application Suite Core & dependencies
- `--mirror-iot` Mirror images for IBM Maximo IoT & dependencies

### Maximo Core Image Mirroring Configuration (Optional):
- `--skip-cfs` Skip mirroring images for IBM Cloud Pak Foundation Services
- `--skip-uds` Skip mirroring images for IBM User Data Services
- `--skip-sls` Skip mirroring images for IBM Suite License Service
- `--skip-tsm` Skip mirroring images for IBM Truststore Manager
- `--skip-mongo` Skip mirroring images for MongoDb Community Edition

### Maximo IoT Image Mirroring Configuration (Optional):
- `--skip-db2` Skip mirroring images for IBM Db2

### Other Commands:
- `--no-confirm` Mirror images without prompting for confirmation
- `-h|--help` Show help message

## Examples
### Interactive Mode
```bash
docker pull quay.io/ibmmas/cli
docker run -ti --rm quay.io/ibmmas/cli mas mirror-images
```

### Non-Interactive Mode
```
docker pull quay.io/ibmmas/cli
docker run -ti --rm quay.io/ibmmas/cli mas mirror-images -H mirror.mydomain.com -P 32500 -u $MIRROR_USERNAME -p $MIRROR_PASSWORD -c v8-220717 --mirror-core --mirror-iot --no-confirm
```
