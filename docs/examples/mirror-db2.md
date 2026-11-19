Mirror IBM Db2 Content
===============================================================================

This example shows how to mirror just the IBM Db2u content associated with a specific release of the **IBM Maximo Operator Catalog**.


Direct Mirroring
-------------------------------------------------------------------------------
With direct image mirroring (`m2m` mode) the content is transferred directly from the IBM Container Registry (ICR) to your private container registry.

```bash
#!/bin/bash

# Destination registry
export REGISTRY_PRIVATE_HOST=x
export REGISTRY_USERNAME=x
export REGISTRY_PASSWORD=x

# Source registry
export IBM_ENTITLEMENT_KEY=x

docker run -e IBM_ENTITLEMENT_KEY -e REGISTRY_USERNAME -e REGISTRY_PASSWORD -ti --rm --pull always quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ \
  mas mirror --catalog @@MAS_LATEST_CATALOG@@ --release @@MAS_LATEST_CHANNEL@@ \
  --mode m2m --target-registry $REGISTRY_PRIVATE_HOST \
  --dir /tmp/mirror \
  --db2u-s11 --db2u-s12
```

Two-Phase Mirroring
-------------------------------------------------------------------------------
Two-phase mirroring first mirrors the content to your local filesystem (`m2d` mode), which can then be mirrored to your private container registry (`d2m` mode).

```bash
#!/bin/bash

# Destination registry
export REGISTRY_PRIVATE_HOST=x
export REGISTRY_USERNAME=x
export REGISTRY_PASSWORD=x

# Source registry
export IBM_ENTITLEMENT_KEY=x

# Catalog
export CATALOG=@@MAS_LATEST_CATALOG@@

docker run -e IBM_ENTITLEMENT_KEY -ti --rm -v /tmp/mirror/$CATALOG:/mnt/mirror --pull always quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ \
  mas mirror --catalog $CATALOG --release @@MAS_LATEST_CHANNEL@@ \
  --mode m2d \
  --dir /mnt/mirror \
  --db2u-s11 --db2u-s12
```

Once the images are mirrored to the local filesystem we can mirror them to the target registry using the `d2m` mode.

```bash
docker run -e REGISTRY_USERNAME -e REGISTRY_PASSWORD -ti --rm -v /tmp/mirror/$CATALOG:/mnt/mirror --pull always quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ \
  mas mirror --catalog $CATALOG --release @@MAS_LATEST_CHANNEL@@ \
  --mode d2m --target-registry $REGISTRY_PRIVATE_HOST \
  --dir /mnt/mirror \
  --db2u-s11 --db2u-s12
```
