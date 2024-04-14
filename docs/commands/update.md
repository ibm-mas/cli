Update
===============================================================================

Usage
-------------------------------------------------------------------------------
`mas update [options]`

### Maximo Operator Catalog Selection
- `-c|--catalog MAS_CATALOG_VERSION` Maximo Operator Catalog Version to mirror (e.g. v8-221129)

### Other Options
- `--no-confirm`         Launch the update without prompting for confirmation
- `--db2u-namespace`     DB2 namespace where instances update will be performed
- `--mongodb-namespace`  Namespace where MongoCE operator and instance will be updated
- `--mongodb-v5-upgrade` Confirms that Mongo can be upgraded to version 5 if needed as part of the update
- `--kafka-namespace`    Namespace where Kafka operator and instance will be updated
- `--kafka-provider`     Set Kafka provider. Supported options are 'redhat' (Red Hat AMQ Streams), or 'strimzi'
- `--dro-migration`      Confirm the removal of UDS and replacement with DRO as part of the update
- `--cp4d-version`       Optional. Set Cloud Pak for Data version for the upgrade. All CP4D Services will be upgraded except Watson Discovery as this does not support seamless upgrade. 
**Note:** This overrides the default CP4D version defined by the Maximo Operator Catalog version.
- `-h|--help`            Show help message

Examples
-------------------------------------------------------------------------------
### Interactive Update
```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas update
```

### Non-Interactive Update
```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas update -c v8-220927-amd64 --no-confirm
```
