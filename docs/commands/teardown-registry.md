Tear Down Private Registry
===============================================================================
This function is used to delete a private/mirror registry from a given cluster to enable a clean start.

Usage
-------------------------------------------------------------------------------
Note that using the `teardown-registry` command will delete the registry completely including the PVC storage and the registry namespace. The registry will need to be recreated after running this command if desired. To start up the registry again, run the `setup-registry`command. Images previously stored in the registry before the teardown will no longer be available and will need to be mirrored again once the registry setup has completed. Take precaution when using this function and expect that images can no longer be accessed from the registry that is being torn down. 

**IMPORTANT:** The `teardown-registry` command permanently deletes all registry data.

An appropriate time to use this tear-down function is when the registry has too many images that are not being used or when there has been a shift to support newer versions but images of older versions are clogging the registry. The tear-down function frees the disk space and allows for a new registry to be setup.

**Note:** Recreating the registry will create a new ca cert for the new registry.

`mas setup-registry [options]`

### Registry Cluster Configuration (optional)
- `-n|--namespace` Registry namespace (default is airgap-registry)

### Other Commands:
- `-h|--help` Show help message

Examples
-------------------------------------------------------------------------------

### Interactive Mode
```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas teardown-registry
```

### Non-Interactive Mode
```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas teardown-registry \
  -n airgap \
  --no-confirm
```

