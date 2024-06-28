Update
===============================================================================

Usage
-------------------------------------------------------------------------------
`mas update [options]`

### Maximo Operator Catalog Selection
- `-c|--catalog MAS_CATALOG_VERSION` Maximo Operator Catalog Version to mirror (e.g. v9-240625-amd64)

### Other Options
- `--no-confirm`         Launch the update without prompting for confirmation
- `--db2u-namespace`     DB2 namespace where instances update will be performed
- `--mongodb-namespace`  Namespace where MongoCE operator and instance will be updated
- `--mongodb-v6-upgrade` Confirms that Mongo can be upgraded to version 6 if needed as part of the update
- `--kafka-namespace`    Namespace where Kafka operator and instance will be updated
- `--kafka-provider`     Set Kafka provider. Supported options are 'redhat' (Red Hat AMQ Streams), or 'strimzi'
- `--dro-migration`      Confirm the removal of UDS and replacement with DRO as part of the update
- `--cp4d-version`       Optional. Set Cloud Pak for Data version for the upgrade.  This overrides the default CP4D version defined by the Maximo Operator Catalog version
- `--skip-pre-check`     Skips the 'pre-update-check' and 'post-update-verify' task in the update pipeline
- `--skip-cp4d-upgrade`  Skips Cloud Pak for Data upgrade
- `-h|--help`            Show help message

Limitations
-------------------------------------------------------------------------------
- Cloud Pak for Data upgrade is not supported if not initially installed using MAS CLI or ansible-devops (i.e under `ibm-cpd` namespace). You should not upgrade Cloud Pak For Data using `mas update` if installed in first place using `cpd-cli` tool. Refer to [Cloud Pak for Data documentation](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.8.x?topic=48-preparing-upgrade-instance-cloud-pak-data) for upgrade steps if you have used `cpd-cli` for your initial installation.

Examples
-------------------------------------------------------------------------------
### Interactive Update
```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas update
```

### Non-Interactive Update
```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas update -c v9-240625-amd64 --no-confirm
```
