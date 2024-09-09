Mirror IBM Db2 Content
===============================================================================

This example shows how to mirror just the IBM Db2u content associated with a specific release of the **IBM Maximo Operator Catalog**.


Direct Mirroring
-------------------------------------------------------------------------------
With direct image mirroring the content is transferred directly from the IBM Container Registry (ICR) to your private container registry.

```bash
#!/bin/bash

# Destination registry
export REGISTRY_PRIVATE_HOST=x
export REGISTRY_PRIVATE_PORT=x
export REGISTRY_USERNAME=x
export REGISTRY_PASSWORD=x

# Source registry
export IBM_ENTITLEMENT_KEY=x

docker run -e IBM_ENTITLEMENT_KEY -ti --rm --pull always quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ \
  mas mirror-images -m direct -d /tmp/mirror --no-confirm \
    -H $REGISTRY_PRIVATE_HOST -P $REGISTRY_PRIVATE_PORT -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
    -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
    --mirror-db2
```

Two-Phase Mirroring
-------------------------------------------------------------------------------
Two-phase mirroring first mirrors the content to your local filesystem, which can then be mirrored to your private container registry.

```bash
#!/bin/bash

# Destination registry
export REGISTRY_PRIVATE_HOST=x
export REGISTRY_PRIVATE_PORT=x
export REGISTRY_USERNAME=x
export REGISTRY_PASSWORD=x

# Source registry
export IBM_ENTITLEMENT_KEY=x

# Catalog
export CATALOG=@@MAS_LATEST_CATALOG@@

docker run -e IBM_ENTITLEMENT_KEY -ti --rm -v /tmp/mirror/$CATALOG:/mnt/mirror --pull always quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ \
  mas mirror-images -m to-filesystem -d /mnt/mirror --no-confirm \
    -H $REGISTRY_PRIVATE_HOST -P $REGISTRY_PRIVATE_PORT -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
    -c $CATALOG -C @@MAS_LATEST_CHANNEL@@ \
    --mirror-db2
```

Once the images are mirrored to the local filesystem we can mirror them to the target registry using the`--from-filesystem` mode flag.

```bash
docker run -ti --rm -v /tmp/mirror/$CATALOG:/mnt/mirror --pull always quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ \
  mas mirror-images -m from-filesystem -d /mnt/mirror --no-confirm \
    -H $REGISTRY_PRIVATE_HOST -P $REGISTRY_PRIVATE_PORT -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
    -c $CATALOG -C @@MAS_LATEST_CHANNEL@@ \
    --mirror-db2
```
