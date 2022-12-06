Mirror Images
===============================================================================

Usage
-------------------------------------------------------------------------------
`mas mirror-images [options]`

### Mirror Mode
- `-m|--mode MIRROR_MODE` Operation mode (direct, to-filesystem, from-filesystem)
- `-d|--dir MIRROR_WORKING_DIR` Working directory for the mirror process

### Registry Details
- `-H|--host REGISTRY_PUBLIC_HOST` Hostname of the target registry
- `-P|--port REGISTRY_PUBLIC_PORT` Port number for the target registry

### Registry Authentication
- `-u|--username REGISTRY_USERNAME` Username to authenticate to the target registry
- `-p|--password REGISTRY_PASSWORD` Password to authenticate to the target registry

### Source Registry Entitlements
- `--ibm-entitlement IBM_ENTITLEMENT_KEY` IBM Entitlement Key
- `--redhat-username REDHAT_CONNECT_USERNAME` Red Hat Connect Username
- `--redhat-password REDHAT_CONNECT_PASSWORD` Red Hat Connect Password

### Maximo Operator Catalog Selection
- `-c|--catalog MAS_CATALOG_VERSION` Maximo Operator Catalog Version to mirror (e.g. v8-221129)
- `-C|--channel MAS_CHANNEL` Maximo Application Suite Channel to mirror (e.g. 8.9.x)
- `--mirror-core` Mirror images for IBM Maximo Application Suite Core & dependencies
- `--mirror-assist`  Mirror images for IBM Maximo Assist
- `--mirror-hputilities` Mirror images for IBM Maximo Health & Predict Utilities
- `--mirror-iot` Mirror images for IBM Maximo IoT & dependencies
- `--mirror-manage` Mirror images for IBM Maximo Manage & dependencies
- `--mirror-monitor` Mirror images for IBM Maximo Monitor
- `--mirror-predict` Mirror images for IBM Maximo Predict
- `--mirror-optimizer` Mirror images for IBM Maximo Optimizer
- `--mirror-visualinspection` Mirror images for IBM Maximo Visual Inspection

### Maximo Core Image Mirroring Configuration
- `--skip-cfs` Skip mirroring images for IBM Cloud Pak Foundation Services
- `--skip-uds` Skip mirroring images for IBM User Data Services
- `--skip-sls` Skip mirroring images for IBM Suite License Service
- `--skip-tsm` Skip mirroring images for IBM Truststore Manager
- `--skip-mongo` Skip mirroring images for MongoDb Community Edition

### Maximo IoT Image Mirroring Configuration
- `--skip-db2` Skip mirroring images for IBM Db2 dependency

### Maximo Manage Image Mirroring Configuration
- `--skip-db2` Skip mirroring images for IBM Db2 dependency

### Other Options
- `--no-confirm` Mirror images without prompting for confirmation
- `-h|--help` Show help message


Examples
-------------------------------------------------------------------------------
### Interactive Image Mirroring
```bash
docker pull quay.io/ibmmas/cli
docker run -ti --rm -v /mnt/registry:/mnt/registry quay.io/ibmmas/cli mas mirror-images
```

### Two-Phase Image Mirroring
Two-Phase image mirroring is required when you do not have a single system with both access to the public registries containing the source container images **and** your internal private registry.  In this case you will require a system with internet connectivity and another with access to your private network, along with a means to transfer data from one to the other (for example, a portable drive).

!!! important
    The examples here use a specific version of the container image (3.3.0).  You should always use the latest available container image, but because we are working in a disconnected environment we need to be specific about the version we are using.  Replace `3.3.0` with the appropriate version.

#### Phase 1: Mirror to Filesystem
First, download the latest version of the container image and start up a terminal session inside the container image, we are going to mount a local directory into the running container to persist the mirror filesystem.

!!! tip
    Mirroring images for Core, Manage and all dependencies will require approximately 62Gb available capacity.

```bash
docker pull quay.io/ibmmas/cli:3.3.0
docker run -ti --rm -v /mnt/registry:/mnt/registry quay.io/ibmmas/cli mas mirror-images \
  --mode to-filesystem \
  --dir /mnt/registry \
  --ibm-entitlement $IBM_ENTITLEMENT_KEY \
  --redhat-username $REDHAT_CONNECT_USERNAME \
  --redhat-password $REDHAT_CONNECT_PASSWORD \
  -H mirror.mydomain.com -P 32500 \
  -u $MIRROR_USERNAME -p $MIRROR_PASSWORD \
  -c v8-220927-amd64 -C 8.9.x \
  --mirror-core --mirror-iot --mirror-manage --mirror-optimizer \
  --no-confirm
```

Once this process completes you will find the mirrored images in `/mnt/registry` ready to transfer to the system inside your disconnected network on which we will perform phase 2 of this operator.  However, before we can do that we also need to mirror the CLI image to your mirror registry so that it's available on the disconnected host system.

```bash
oc image mirror --dir /mnt/registry quay.io/ibmmas/cli:3.3.0 file://ibmmas/cli:3.3.0
```


#### Phase 2: Mirror from Filesystem
Transfer the content of `/mnt/registry` to your system in the disconnected network.  Now we are going to put the CLI image in your registry:

```bash
docker login <YOURPRIVATEREGISTRY> -u MIRROR_USERNAME -p MIRROR_PASSWORD
oc image mirror --dir /mnt/myportabledisk file://ibmmas/cli:3.3.0 mirror.mydomain.com:32500/ibmmas/cli:3.3.0
```

Now we are ready to mirror the images to your registry using the CLI image in the same way we mirrored the images to the local disk in the first place:

```bash
docker pull mirror.mydomain.com:32500/ibmmas/cli:3.3.0
docker run -ti --rm -v /mnt/mirrorregistry:/mnt/mirrorregistry mirror.mydomain.com:32500/ibmmas/cli:3.3.0 mas mirror-images \
  --mode from-filesystem \
  --dir /mnt/registry \
  --ibm-entitlement $IBM_ENTITLEMENT_KEY \
  --redhat-username $REDHAT_CONNECT_USERNAME \
  --redhat-password $REDHAT_CONNECT_PASSWORD \
  -H mirror.mydomain.com -P 32500 \
  -u $MIRROR_USERNAME -p $MIRROR_PASSWORD \
  -c v8-220927-amd64 -C 8.9.x \
  --mirror-core --mirror-iot --mirror-manage --mirror-optimizer \
  --no-confirm
```


### Direct Image Mirroring
The following example will mirror all images required for Maximo Application Suite Core and the Maximo Manage and IoT applications directly to your target registry, without prompting for confirmation.

```bash
docker pull quay.io/ibmmas/cli
docker run -ti --rm quay.io/ibmmas/cli mas mirror-images \
  --mode direct \
  --dir /mnt/registry \
  --ibm-entitlement $IBM_ENTITLEMENT_KEY \
  --redhat-username $REDHAT_CONNECT_USERNAME \
  --redhat-password $REDHAT_CONNECT_PASSWORD \
  -H mirror.mydomain.com -P 32500 \
  -u $MIRROR_USERNAME -p $MIRROR_PASSWORD \
  -c v8-220927-amd64 -C 8.9.x \
  --mirror-core --mirror-iot --mirror-manage --mirror-optimizer \
  --no-confirm
```
