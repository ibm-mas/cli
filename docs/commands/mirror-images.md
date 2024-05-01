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
- `-u|--username REGISTRY_USERNAME` Username to authenticate to the target registry
- `-p|--password REGISTRY_PASSWORD` Password to authenticate to the target registry

### Source Registry Entitlements
- `--ibm-entitlement IBM_ENTITLEMENT_KEY` IBM Entitlement Key
- `--redhat-username REDHAT_CONNECT_USERNAME` Red Hat Connect Username (only required when mirroring UDS images)
- `--redhat-password REDHAT_CONNECT_PASSWORD` Red Hat Connect Password (only required when mirroring UDS images)

### Maximo Operator Catalog Selection
- `-c|--catalog MAS_CATALOG_VERSION` Maximo Operator Catalog Version to mirror (e.g. v8-230627-amd64)
- `-C|--channel MAS_CHANNEL` Maximo Application Suite Channel to mirror (e.g. 8.10.x)

### Content Selection (Core Platform)
- `--mirror-catalog` Mirror the IBM Maximo Operator Catalog
- `--mirror-core` Mirror images for IBM Maximo Application Suite Core

### Content Selection (Applications)
- `--mirror-assist`  Mirror images for IBM Maximo Assist
- `--mirror-hputilities` Mirror images for IBM Maximo Health & Predict Utilities
- `--mirror-iot` Mirror images for IBM Maximo IoT
- `--mirror-manage` Mirror images for IBM Maximo Manage
- `--mirror-monitor` Mirror images for IBM Maximo Monitor
- `--mirror-optimizer` Mirror images for IBM Maximo Optimizer
- `--mirror-predict` Mirror images for IBM Maximo Predict
- `--mirror-visualinspection` Mirror images for IBM Maximo Visual Inspection

### Content Selection (Cloud Pak for Data)
- `--mirror-cp4d` Mirror images for IBM Cloud Pak for Data Platform
- `--mirror-wd` Mirror images for IBM Watson Discovery
- `--mirror-wsl` Mirror images for IBM Watson Studio Local
- `--mirror-wml` Mirror images for IBM Watson Machine Learning
- `--mirror-spark` Mirror images for IBM Analytics Engine (Spark)
- `--mirror-cognos` Mirror images for IBM Cognos Analytics

### Content Selection (Other Dependencies)
- `--mirror-cfs` Mirror images for IBM Cloud Pak Foundation Services
- `--mirror-uds` Mirror images for IBM User Data Services
- `--mirror-sls` Mirror images for IBM Suite License Service
- `--mirror-tsm` Mirror images for IBM Truststore Manager
- `--mirror-mongo` Mirror images for MongoDb Community Edition
- `--mirror-db2` Mirror images for IBM Db2
- `--mirror-appconnect` Mirror images for IBM AppConnect


### Other Options
- `--no-confirm` Mirror images without prompting for confirmation
- `-h|--help` Show help message


Storage Requirements
-------------------------------------------------------------------------------
As of MAS 8.10 (June 2023) the total capacity requirement to mirror content from the IBM Maximo Operator Catalog is approximately **484G**, the following table can be used to determine the approximate storage requirement for your mirrored content based on what content you need to mirror:

| Maximo Application Suite        | Command Flag                | Size    |
| ------------------------------- | --------------------------- | ------- |
| Maximo Operator Catalog         | `--mirror-catalog`          | 50M     |
| Maximo Application Suite Core   | `--mirror-core`             | 4G      |
| Maximo Assist                   | `--mirror-assist`           | 5G      |
| Maximo HP Utilities             | `--mirror-hputilities`      | 2G      |
| Maximo IoT                      | `--mirror-iot`              | 9G      |
| Maximo Manage                   | `--mirror-manage`           | 8G      |
| Maximo Monitor                  | `--mirror-monitor`          | 17G     |
| Maximo Optimizer                | `--mirror-optimizer`        | 3G      |
| Maximo Predict                  | `--mirror-predict`          | 6G      |
| Maximo Visual Inspection        | `--mirror-visualinspection` | 40G     |
| **Total**                       |                             | **94G** |

| IBM Cloud Pak for Data       | Command Flag                | Size     |
| ---------------------------- | --------------------------- | -------- |
| IBM CP4D Platform            | `--mirror-cp4d`             | 2G       |
| IBM Watson Discovery         | `--mirror-wd`               | 41G      |
| IBM Analytics Engine (Spark) | `--mirror-spark`            | 54G      |
| IBM Watson Machine Learning  | `--mirror-wml`              | 91G      |
| IBM Watson Studio Local      | `--mirror-wsl`              | 85G      |
| **Total**                    |                             | **273G** |

| Other Dependencies                | Command Flag                | Size     |
| --------------------------------- | --------------------------- | -------- |
| Mongo Community Edition           | `--mirror-mongo`            | 500M     |
| IBM Truststore Manager            | `--mirror-tsm`              | 1G       |
| IBM User Data Services            | `--mirror-uds`              | 7G       |
| IBM Suite License Service         | `--mirror-sls`              | 1G       |
| IBM Cloud Pak Foundation Services | `--mirror-cfs`              | 21G      |
| IBM AppConnect                    | `--mirror-appconnect`       | 13G      |
| IBM Db2                           | `--mirror-db2`              | 73G      |
| **Total**                         |                             | **117G** |

!!! note
    The total capacity used on the filesystem in the target mirror registry itself may be lower than this due to the use of shared image layers, particularly across applications in IBM Maximo Application Suite itself.


Interactive Image Mirroring
-------------------------------------------------------------------------------
You can start image mirroring by running the `mas mirror-images` command with no parameters, you will be prompted to select the mirror mode and working directory, configure the target registry, and select which content you wish to mirror.

```bash
docker run -ti --rm -v /mnt/registry:/mnt/registry --pull always quay.io/ibmmas/cli mas mirror-images
```


Direct Image Mirroring
-------------------------------------------------------------------------------
The following example will mirror all images required for Maximo Application Suite Core and the Maximo Manage and IoT applications directly to your target registry, without prompting for confirmation.

```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas mirror-images \
  --mode direct --dir /tmp/registry \
  --ibm-entitlement $IBM_ENTITLEMENT_KEY --redhat-username $REDHAT_USERNAME --redhat-password $REDHAT_PASSWORD \
  -H mirror.mydomain.com -P 5000 -u $MIRROR_USERNAME -p $MIRROR_PASSWORD \
  -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
  --mirror-catalog --mirror-core --mirror-iot --mirror-manage \
  --mirror-cfs --mirror-uds --mirror-sls --mirror-tsm --mirror-mongo --mirror-db2 \
  --no-confirm
```


Two-Phase Image Mirroring
-------------------------------------------------------------------------------
Two-Phase image mirroring is required when you do not have a single system with both access to the public registries containing the source container images **and** your internal private registry.  In this case you will require a system with internet connectivity and another with access to your private network, along with a means to transfer data from one to the other (for example, a portable drive).

### Phase 1: Mirror to Filesystem
First, download the latest version of the container image and start up a terminal session inside the container image, we are going to mount a local directory into the running container to persist the mirror filesystem.

```bash
docker pull quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@
docker run -ti --rm -v /registry:/mnt/registry quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror-images \
  --mode to-filesystem --dir /mnt/registry \
  --ibm-entitlement $IBM_ENTITLEMENT_KEY --redhat-username $REDHAT_USERNAME --redhat-password $REDHAT_PASSWORD \
  -H mirror.mydomain.com -P 5000 -u $MIRROR_USERNAME -p $MIRROR_PASSWORD \
  -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
  --mirror-catalog --mirror-core --mirror-iot --mirror-manage \
  --mirror-cfs --mirror-uds --mirror-sls --mirror-tsm --mirror-mongo --mirror-db2 \
  --no-confirm
```

Once this process completes you will find the mirrored images in `/registry` on your local filesystem ready to transfer to the system inside your disconnected network on which we will perform phase 2 of this operation.  However, before we can do that we also need to mirror the CLI image to your mirror registry so that it's available on the disconnected host system.

```bash
oc image mirror --dir /registry quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ file://ibmmas/cli:@@CLI_LATEST_VERSION@@
```


### Phase 2: Mirror from Filesystem
Transfer the content of `/registry` to your system in the disconnected network.  Now we are going to put the CLI image in your registry:

```bash
docker login mirror.mydomain.com:5000 -u $MIRROR_USERNAME -p $MIRROR_PASSWORD
oc image mirror --dir /registry file://ibmmas/cli:@@CLI_LATEST_VERSION@@ mirror.mydomain.com:5000/ibmmas/cli:@@CLI_LATEST_VERSION@@
```

Now we are ready to mirror the images to your registry using the CLI image in the same way we mirrored the images to the local disk in the first place:

```bash
docker pull mirror.mydomain.com:5000/ibmmas/cli:@@CLI_LATEST_VERSION@@
docker run -ti --rm -v /registry:/mnt/registry mirror.mydomain.com:5000/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror-images \
  --mode from-filesystem --dir /mnt/registry \
  --ibm-entitlement $IBM_ENTITLEMENT_KEY --redhat-username $REDHAT_USERNAME --redhat-password $REDHAT_PASSWORD \
  -H mirror.mydomain.com -P 5000 -u $MIRROR_USERNAME -p $MIRROR_PASSWORD \
  -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
  --mirror-catalog --mirror-core --mirror-iot --mirror-manage \
  --mirror-cfs --mirror-uds --mirror-sls --mirror-tsm --mirror-mongo --mirror-db2 \
  --no-confirm
```

