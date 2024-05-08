Image Mirroring
===============================================================================


Image Mirroring Overview
-------------------------------------------------------------------------------
We recommend the use of two-phase mirroring, it is slower than direct mirroring and requires more storage capacity, but can allow you to more easily recover from network glitches and creates a clean seperation of the tasks of getting the content from the source registry and putting it into the target registry which can make debugging failures easier.

This guide assumes that you are looking to mirror content for the latest release (**@@MAS_LATEST_CHANNEL@@**) from the most recent catalog update (**@@MAS_LATEST_CATALOG@@**), and that you are installing all MAS applications.  If you are not installing certain applications or dependencies take care to remove the appropriate `--mirror-x` flags to avoid mirroring unnecessary images.


Preparation
-------------------------------------------------------------------------------
Set the following environment variables that will be used in each stage:

```bash
export IBM_ENTITLEMENT_KEY=xxx
export LOCAL_DIR=xxx
export REGISTRY_HOST=xxx
export REGISTRY_PORT=xxx
export REGISTRY_USERNAME=xxx
export REGISTRY_PASSWORD=xxx
export REDHAT_USERNAME=xxx
export REDHAT_PASSWORD=xxx
```


Stage 1 - Core
-------------------------------------------------------------------------------
Let's start simple and just get the MAS Core and IBM Maximo Operator Catalog mirrored to the registry, this shouldn't take long and provides an early measure of the download and upload performance to help estimate the time to complete the larger stages.

```bash
mas mirror-images -m to-filesystem -d $LOCAL_DIR/core \
  -H $REGISTRY_HOST -P $REGISTRY_PORT -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
  --mirror-catalog --mirror-core \
  --ibm-entitlement $IBM_ENTITLEMENT_KEY
```

Once the images are mirrored to local disk, we will mirror them from local disk to your registry, this should complete in very little time, depends on the speed of your internal network:

```bash
mas mirror-images -m from-filesystem -d $LOCAL_DIR/core \
  -H $REGISTRY_HOST -P $REGISTRY_PORT -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
  --mirror-catalog --mirror-core
```


Stage 2 - Apps
-------------------------------------------------------------------------------
```bash
mas mirror-images -m to-filesystem -d $LOCAL_DIR/apps \
  -H $REGISTRY_HOST -P $REGISTRY_PORT -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
  --mirror-assist --mirror-hputilities --mirror-iot --mirror-manage --mirror-monitor --mirror-optimizer --mirror-predict --mirror-visualinspection \
  --ibm-entitlement $IBM_ENTITLEMENT_KEY
```

```bash
mas mirror-images -m from-filesystem -d $LOCAL_DIR/apps \
  -H $REGISTRY_HOST -P $REGISTRY_PORT -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
  --mirror-assist --mirror-hputilities --mirror-iot --mirror-manage --mirror-monitor --mirror-optimizer --mirror-predict --mirror-visualinspection
```


Stage 3 - CP4D
-------------------------------------------------------------------------------
```bash
mas mirror-images -m to-filesystem -d $LOCAL_DIR/cp4d \
  -H $REGISTRY_HOST -P $REGISTRY_PORT- u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
  --mirror-cp4d --mirror-wd --mirror-spark --mirror-wml --mirror-wsl \
  --ibm-entitlement $IBM_ENTITLEMENT_KEY
```

```bash
mas mirror-images -m from-filesystem -d $LOCAL_DIR/cp4d \
  -H $REGISTRY_HOST -P $REGISTRY_PORT- u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
  --mirror-cp4d --mirror-wd --mirror-spark --mirror-wml --mirror-wsl
```


Stage 4 - Other Dependencies
-------------------------------------------------------------------------------
```bash
mas mirror-images -m to-filesystem -d $LOCAL_DIR/other \
  -H $REGISTRY_HOST -P $REGISTRY_PORT -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
  --mirror-mongo --mirror-tsm --mirror-uds --mirror-sls --mirror-cfs --mirror-appconnect --mirror-db2 \
  --ibm-entitlement $IBM_ENTITLEMENT_KEY --redhat-username $REDHAT_USERNAME --redhat-password $REDHAT_PASSWORD
```

```bash
mas mirror-images -m from-filesystem -d $LOCAL_DIR/other \
  -H $REGISTRY_HOST -P $REGISTRY_PORT -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
  --mirror-mongo --mirror-tsm --mirror-uds --mirror-sls --mirror-cfs --mirror-appconnect --mirror-db2
```
