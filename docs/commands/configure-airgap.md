# Configure Airgap

!!! important
    The `configure-airgap` command does not work on **IBMCloud ROKS** clusters.  This is a limitation of the service provided in IBMCloud which disables key parts of OpenShift functionality required to configure and use ImageContentSourcePolicy resources (which is the basis of airgap/image mirroring support in OpenShift).


## Usage

### Interactive
```bash
docker run -ti --rm -v ~:/mnt/local quay.io/ibmmas/cli mas configure-airgap
```

### Non-Interactive
```bash
docker run -ti --rm -v ~:/mnt/local quay.io/ibmmas/cli mas configure-airgap \
  -H myprivateregistry.com -P 5000 -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  --ca-file /mnt/local/registry-ca.crt \
  --no-confirm
```
