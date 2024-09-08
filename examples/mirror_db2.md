Mirror IBM Db2 Content
===============================================================================

This example shows how to mirror just the IBM Db2u content associated with a specific release of the **IBM Maximo Operator Catalog**

```bash
#!/bin/bash

# Destination registry
export REGISTRY_PRIVATE_HOST=airgap-registry-lb.airgap-registry.svc
export REGISTRY_PRIVATE_PORT=5000
export REGISTRY_USERNAME=x
export REGISTRY_PASSWORD=x

# Source registry
export IBM_ENTITLEMENT_KEY=x

# Catalog
export CATALOG=v9-240827-amd64

mas mirror-images -m to-filesystem -d /pvc/mirror/$CATALOG --no-confirm \
  -H $REGISTRY_PRIVATE_HOST -P $REGISTRY_PRIVATE_PORT -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  --ibm-entitlement $IBM_ENTITLEMENT_KEY \
  -c $CATALOG -C 9.0.x \
  --mirror-db2
```
