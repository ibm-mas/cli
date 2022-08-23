Mirror Images
===============================================================================

Usage
-------------------------------------------------------------------------------
`mas mirror-images [options]`

### Options
#### Registry Details (Required)
- `-H|--host REGISTRY_PUBLIC_HOST` Hostname of the target registry
- `-P|--port REGISTRY_PUBLIC_PORT` Port number for the target registry

#### Registry Authentication (Optional)
- `-u|--username REGISTRY_USERNAME` Username to authenticate to the target registry
- `-p|--password REGISTRY_PASSWORD` Password to authenticate to the target registry

#### Source Registry Entitlements (Required)
- `--ibm-entitlement IBM_ENTITLEMENT_KEY` IBM Entitlement Key
- `--redhat-username REDHAT_CONNECT_USERNAME` Red Hat Connect Username
- `--redhat-password REDHAT_CONNECT_PASSWORD` Red Hat Connect Password

#### Maximo Operator Catalog Selection (Required)
- `-c|--catalog MAS_CATALOG_VERSION` Maximo Operator Catalog Version to mirror (e.g. v8-220717)
- `--mirror-core` Mirror images for IBM Maximo Application Suite Core & dependencies
- `--mirror-assist`  Mirror images for IBM Maximo Assist
- `--mirror-hputilities` Mirror images for IBM Maximo Health & Predict Utilities
- `--mirror-iot` Mirror images for IBM Maximo IoT & dependencies
- `--mirror-manage` Mirror images for IBM Maximo Manage & dependencies
- `--mirror-monitor` Mirror images for IBM Maximo Monitor
- `--mirror-predict` Mirror images for IBM Maximo Predict
- `--mirror-optimizer` Mirror images for IBM Maximo Optimizer
- `--mirror-safety` Mirror images for IBM Maximo Safety
- `--mirror-visualinspection` Mirror images for IBM Maximo Visual Inspection

#### Maximo Core Image Mirroring Configuration (Optional)
- `--skip-cfs` Skip mirroring images for IBM Cloud Pak Foundation Services
- `--skip-uds` Skip mirroring images for IBM User Data Services
- `--skip-sls` Skip mirroring images for IBM Suite License Service
- `--skip-tsm` Skip mirroring images for IBM Truststore Manager
- `--skip-mongo` Skip mirroring images for MongoDb Community Edition

#### Maximo IoT Image Mirroring Configuration (Optional)
- `--skip-db2` Skip mirroring images for IBM Db2 dependency

#### Maximo Manage Image Mirroring Configuration (Optional)
- `--skip-db2` Skip mirroring images for IBM Db2 dependency

#### Other Options
- `--no-confirm` Mirror images without prompting for confirmation
- `-h|--help` Show help message


Examples
-------------------------------------------------------------------------------
### Interactive Mode
```bash
docker pull quay.io/ibmmas/cli
docker run -ti --rm quay.io/ibmmas/cli mas mirror-images
```

### Non-Interactive Mode
The following example will mirror all images required for Maximo Application Suite Core and the Maximo Manage and IoT applications without prompting for confirmation.
```
docker pull quay.io/ibmmas/cli
docker run -ti --rm quay.io/ibmmas/cli mas mirror-images \
  --ibm-entitlement $IBM_ENTITLEMENT_KEY \
  --redhat-username $REDHAT_CONNECT_USERNAME \
  --redhat-password $REDHAT_CONNECT_PASSWORD \
  -H mirror.mydomain.com -P 32500 \
  -u $MIRROR_USERNAME -p $MIRROR_PASSWORD \
  -c v8-220805-amd64 \
  --mirror-core --mirror-iot --mirror-manage \
  --no-confirm
```
