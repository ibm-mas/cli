Update
===============================================================================

Update Overview
-------------------------------------------------------------------------------
This guide is specifically for environments using **static catalogs**.  If you are using the **dynamic catalog** then updates are automatically applied as soon as they are released.

1. [Disconnected Update Preparation](#1-disconnected-install-preparation)
2. [Update MAS](#2-update-maximo-application-suite)


1 Disconnected Update Preparation
-------------------------------------------------------------------------------
Before you start the update, you must mirror the images for the new catalog that you wish to update to. Mirroring the images is a simple but time consuming process.  Three modes are available for the mirror process:

- **direct** mirrors images directly from the source registry to your private registry
- **to-filesystem** mirrors images from the source to a local directory
- **from-filesystem** mirrors images from a local directory to your private registry

```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas mirror-images
```

You will be prompted to set the target registry for the image mirroring and to [select the version of IBM Maximo Operator Catalog to mirror](choosing-the-right-catalog.md) and the subset of content that you wish to mirror.  You can choose to mirror everything from the catalog, or control exactly what is mirrored to your private registry to reduce the time and bandwidth used to mirror the images, as well reducing the storage requirements of the registry.

This command can also be ran non-interactive, for full details refer to the [mirror-images](../commands/mirror-images.md) command documentation.

```bash
mas mirror-images \
  -m direct \
  -d /mnt/local-mirror/ \
  -H myprivateregistry.com -P 5000 -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  -c v8-221129-amd64 -C 8.9.x --mirror-core --mirror-iot --mirror-optimizer --mirror-manage \
  --ibm-entitlement $IBM_ENTITLEMENT_KEY \
  --redhat-username $REDHAT_USERNAME --redhat-password $REDHAT_PASSWORD \
  --no-confirm
```

!!! important
    Make sure to select the release of MAS you currently have installed in the cluster, if you have multiple instances of MAS in the cluster running different releases then you must run the mirror command multiple time to ensure that you have mirrored the content for all releases of MAS that are in use in the cluster.


2 Update Maximo Application Suite
-------------------------------------------------------------------------------
Run `mas update` and choose the catalog to update to.  This will update the operator catalog installed in your cluster, and the Operator Lifecycle Manager (OLM) will automatically update all installed operators to the newest version available on the current subscription channel.

!!! important
    You must select a newer catalog than what is already in use.  Updating to an older static catalog is not supported.

```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas update
```


The command can akso be ran non-interactive.

```bash
mas update -c v8-221129-amd64 --no-confirm
```
