Image Mirroring
===============================================================================
We recommend the use of two-phase mirroring in most cases, it is slower than direct mirroring and requires more storage capacity, but can allow you to more easily recover from network glitches and creates a clean seperation of the tasks of getting the content from the source registry and putting it into the target registry which can make debugging failures easier.

This guide assumes that you are looking to mirror content for the latest release (**@@MAS_LATEST_CHANNEL@@**) from the most recent catalog update (**@@MAS_LATEST_CATALOG@@**), and that you are installing all MAS applications & dependencies.  If you are not installing certain applications or dependencies take care to remove the appropriate `--mirror-x` flags to avoid mirroring unnecessary images.

By default image repositories will be prefixed using the datestamp of the Maximo Operator Catalog that you are mirroring from, this allows for simpler registry management, you can prune all images under `mas-241105/*` in your mirror registry once you know that you have updated all clusters to a newer version of the catalog.


Usage
-------------------------------------------------------------------------------
For full usage information run `mas mirror-images --help`


Interactive Image Mirroring
-------------------------------------------------------------------------------
You can start image mirroring by running the `mas mirror-images` command with no parameters, you will be prompted to select the mirror mode and working directory, configure the target registry, and select which content you wish to mirror.

The easiest way to do this is using the MAS CLI container image as below:

```bash
LOCAL_DIR=/home/david/mirrorfiles
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror-images
```


Non-Interactive Image Mirroring
-------------------------------------------------------------------------------
This guide will take you through we mirror images in our own development environment, breaking up the task into 4 distinct stages to further break down the work and make it easier to address any problems by providing clear milestones:

- [Preparation](#preparation)
- [IBM Maximo Application Suite Core](#stage-1-core)
- [IBM Maximo Applications](#stage-2-apps)
- [IBM Cloud Pak for Data](#stage-3-cp4d)
- [Other Dependencies](#stage-4-other-dependencies)

### Preparation
Set the following environment variables that will be used in each stage:

```bash
export IBM_ENTITLEMENT_KEY=xxx
export LOCAL_DIR=xxx
export REGISTRY_HOST=xxx
export REGISTRY_PORT=xxx
export REGISTRY_USERNAME=xxx
export REGISTRY_PASSWORD=xxx
```

If you do not have a single system with both access to the public source registries **and** your internal private registry then you will require a system with internet connectivity and another with access to your private network, along with a means to transfer data from one to the other (for example, a portable drive).

In this scenario, we must also transfer the CLI image to your local registry:

```bash
oc image mirror --dir $LOCAL_DIR/cli quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ file://ibmmas/cli:@@CLI_LATEST_VERSION@@ --filter-by-os='.*'
```

Transfer the content of `$LOCAL_DIR/cli` to your system within the private network and transfer the image to your mirror registry.

```bash
docker login $REGISTRY_HOST:$REGISTRY_PORT -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD
oc image mirror --dir $LOCAL_DIR/cli file://ibmmas/cli:@@CLI_LATEST_VERSION@@ $REGISTRY_HOST:$REGISTRY_PORT/ibmmas/cli:@@CLI_LATEST_VERSION@@ --filter-by-os='.*'
```
!!! note
    For the next steps, if you want to mirror Single architecture images, include the variable as explained below depending on your environment. Available list of arch images include "amd64", "ppc64le", "s390x". 
```bash
    export MIRROR_SINGLE_ARCH=amd64
```
export the variable in the mascli container before we begin to mirror images. This step helps save storage space else all the images with three architectures get downloaded. 

### Stage 1 - Core
Let's start simple and just get the MAS Core and IBM Maximo Operator Catalog mirrored to the registry, this shouldn't take long and provides an early measure of the download and upload performance to help estimate the time to complete the larger stages.

<cds-tabs trigger-content="Select an item" value="direct">
  <cds-tab id="tab-direct-core" target="panel-direct-core" value="direct">Direct</cds-tab>
  <cds-tab id="tab-to-core" target="panel-to-core" value="to">To Filesystem</cds-tab>
  <cds-tab id="tab-from-core" target="panel-from-core" value="from">From Filesystem</cds-tab>
  <cds-tab id="tab-from-restricted-core" target="panel-from-restricted-core" value="from-restricted">From Filesystem (Restricted)</cds-tab>
</cds-tabs>

<div class="tab-panel">
  <div id="panel-direct-core" role="tabpanel" aria-labelledby="tab-direct-core" hidden>

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror-images \
  -m direct -d /mnt/registry/core \
  -H $REGISTRY_HOST -P $REGISTRY_PORT -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
  --mirror-catalog --mirror-core \
  --ibm-entitlement $IBM_ENTITLEMENT_KEY
```

  </div>
  <div id="panel-to-core" role="tabpanel" aria-labelledby="tab-to-core" hidden>

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror-images \
  -m to-filesystem -d /mnt/registry/core \
  -H $REGISTRY_HOST -P $REGISTRY_PORT -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
  --mirror-catalog --mirror-core \
  --ibm-entitlement $IBM_ENTITLEMENT_KEY
```

  </div>
  <div id="panel-from-core" role="tabpanel" aria-labelledby="tab-from-core" hidden>

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror-images \
  -m from-filesystem -d /mnt/registry/core \
  -H $REGISTRY_HOST -P $REGISTRY_PORT -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
  --mirror-catalog --mirror-core
```

  </div>
  <div id="panel-from-restricted-core" role="tabpanel" aria-labelledby="tab-from-restricted-core" hidden>
    <p>Transfer the contents of <code>$LOCAL_DIR/core</code> to your system in the private network and run the second phase using the CLI image that was mirrored to your private registry during preparation.</p>

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry $REGISTRY_HOST:$REGISTRY_PORT/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror-images \
  -m from-filesystem -d /mnt/registry/core \
  -H $REGISTRY_HOST -P $REGISTRY_PORT -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
  --mirror-catalog --mirror-core
```

  </div>
</div>


### Stage 2 - Apps

<cds-tabs trigger-content="Select an item" value="direct">
  <cds-tab id="tab-direct-apps" target="panel-direct-apps" value="direct">Direct</cds-tab>
  <cds-tab id="tab-to-apps" target="panel-to-apps" value="to">To Filesystem</cds-tab>
  <cds-tab id="tab-from-apps" target="panel-from-apps" value="from">From Filesystem</cds-tab>
  <cds-tab id="tab-from-restricted-apps" target="panel-from-restricted-apps" value="from-restricted">From Filesystem (Restricted)</cds-tab>
</cds-tabs>

<div class="tab-panel">
  <div id="panel-direct-apps" role="tabpanel" aria-labelledby="tab-direct-apps" hidden>

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror-images \
  -m direct -d /mnt/registry/apps \
  -H $REGISTRY_HOST -P $REGISTRY_PORT -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
  --mirror-assist --mirror-iot --mirror-manage --mirror-icd --mirror-monitor --mirror-optimizer --mirror-predict --mirror-visualinspection --mirror-facilities \
  --ibm-entitlement $IBM_ENTITLEMENT_KEY
```

  </div>
  <div id="panel-to-apps" role="tabpanel" aria-labelledby="tab-to-apps" hidden>

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror-images \
  -m to-filesystem -d /mnt/registry/apps \
  -H $REGISTRY_HOST -P $REGISTRY_PORT -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
  --mirror-assist --mirror-iot --mirror-manage --mirror-icd --mirror-monitor --mirror-optimizer --mirror-predict --mirror-visualinspection --mirror-facilities \
  --ibm-entitlement $IBM_ENTITLEMENT_KEY
```

  </div>
  <div id="panel-from-apps" role="tabpanel" aria-labelledby="tab-from-apps" hidden>

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror-images \
  -m from-filesystem -d /mnt/registry/apps \
  -H $REGISTRY_HOST -P $REGISTRY_PORT -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
  --mirror-assist --mirror-iot --mirror-manage --mirror-icd --mirror-monitor --mirror-optimizer --mirror-predict --mirror-visualinspection --mirror-facilities
```

  </div>
  <div id="panel-from-restricted-apps" role="tabpanel" aria-labelledby="tab-from-restricted-apps" hidden>
    <p>Transfer the contents of <code>$LOCAL_DIR/apps</code> to your system in the private network and run the second phase using the CLI image that was mirrored to your private registry during preparation.</p>

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry $REGISTRY_HOST:$REGISTRY_PORT/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror-images \
  -m from-filesystem -d /mnt/registry/apps \
  -H $REGISTRY_HOST -P $REGISTRY_PORT -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
  --mirror-assist --mirror-iot --mirror-manage --mirror-icd --mirror-monitor --mirror-optimizer --mirror-predict --mirror-visualinspection --mirror-facilities
```

  </div>
</div>


### Stage 3 - CP4D

<cds-tabs trigger-content="Select an item" value="direct">
  <cds-tab id="tab-direct-cp4d" target="panel-direct-cp4d" value="direct">Direct</cds-tab>
  <cds-tab id="tab-to-cp4d" target="panel-to-cp4d" value="to">To Filesystem</cds-tab>
  <cds-tab id="tab-from-cp4d" target="panel-from-cp4d" value="from">From Filesystem</cds-tab>
  <cds-tab id="tab-from-restricted-cp4d" target="panel-from-restricted-cp4d" value="from-restricted">From Filesystem (Restricted)</cds-tab>
</cds-tabs>

<div class="tab-panel">
  <div id="panel-direct-cp4d" role="tabpanel" aria-labelledby="tab-direct-cp4d" hidden>

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror-images \
  -m direct -d /mnt/registry/cp4d \
  -H $REGISTRY_HOST -P $REGISTRY_PORT- u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
  --mirror-cp4d --mirror-spark --mirror-wml --mirror-wsl --mirror-cognos \
  --ibm-entitlement $IBM_ENTITLEMENT_KEY
```

  </div>
  <div id="panel-to-cp4d" role="tabpanel" aria-labelledby="tab-to-cp4d" hidden>

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror-images \
  -m to-filesystem -d /mnt/registry/cp4d \
  -H $REGISTRY_HOST -P $REGISTRY_PORT- u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
  --mirror-cp4d --mirror-spark --mirror-wml --mirror-wsl --mirror-cognos \
  --ibm-entitlement $IBM_ENTITLEMENT_KEY
```

  </div>
  <div id="panel-from-cp4d" role="tabpanel" aria-labelledby="tab-from-cp4d" hidden>

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror-images \
  -m from-filesystem -d /mnt/registry/cp4d \
  -H $REGISTRY_HOST -P $REGISTRY_PORT- u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
  --mirror-cp4d --mirror-spark --mirror-wml --mirror-wsl --mirror-cognos
```

  </div>
  <div id="panel-from-restricted-cp4d" role="tabpanel" aria-labelledby="tab-from-restricted-cp4d" hidden>
    <p>Transfer the contents of <code>$LOCAL_DIR/cp4d</code> to your system in the private network and run the second phase using the CLI image that was mirrored to your private registry during preparation.</p>

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry $REGISTRY_HOST:$REGISTRY_PORT/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror-images \
  -m from-filesystem -d /mnt/registry/cp4d \
  -H $REGISTRY_HOST -P $REGISTRY_PORT- u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
  --mirror-cp4d --mirror-spark --mirror-wml --mirror-wsl --mirror-cognos
```

  </div>
</div>


### Stage 4 - Other Dependencies

<cds-tabs trigger-content="Select an item" value="direct">
  <cds-tab id="tab-direct-other" target="panel-direct-other" value="direct">Direct</cds-tab>
  <cds-tab id="tab-to-other" target="panel-to-other" value="to">To Filesystem</cds-tab>
  <cds-tab id="tab-from-other" target="panel-from-other" value="from">From Filesystem</cds-tab>
  <cds-tab id="tab-from-restricted-other" target="panel-from-restricted-other" value="from-restricted">From Filesystem (Restricted)</cds-tab>
</cds-tabs>

<div class="tab-panel">
  <div id="panel-direct-other" role="tabpanel" aria-labelledby="tab-direct-other" hidden>

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror-images \
  -m direct -d /mnt/registry/other \
  -H $REGISTRY_HOST -P $REGISTRY_PORT -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
  --mirror-mongo --mirror-tsm --mirror-sls --mirror-cfs --mirror-db2 \
  --ibm-entitlement $IBM_ENTITLEMENT_KEY
```

  </div>
  <div id="panel-to-other" role="tabpanel" aria-labelledby="tab-to-other" hidden>

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror-images \
  -m to-filesystem -d /mnt/registry/other \
  -H $REGISTRY_HOST -P $REGISTRY_PORT -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
  --mirror-mongo --mirror-tsm --mirror-sls --mirror-cfs --mirror-db2 \
  --ibm-entitlement $IBM_ENTITLEMENT_KEY
```

  </div>
  <div id="panel-from-other" role="tabpanel" aria-labelledby="tab-from-other" hidden>

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror-images \
  -m from-filesystem -d /mnt/registry/other \
  -H $REGISTRY_HOST -P $REGISTRY_PORT -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
  --mirror-mongo --mirror-tsm --mirror-sls --mirror-cfs --mirror-db2
```

  </div>
  <div id="panel-from-restricted-other" role="tabpanel" aria-labelledby="tab-from-restricted-other" hidden>
    <p>Transfer the contents of <code>$LOCAL_DIR/other</code> to your system in the private network and run the second phase using the CLI image that was mirrored to your private registry during preparation.</p>

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry $REGISTRY_HOST:$REGISTRY_PORT/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror-images \
  -m from-filesystem -d /mnt/registry/other \
  -H $REGISTRY_HOST -P $REGISTRY_PORT -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  -c @@MAS_LATEST_CATALOG@@ -C @@MAS_LATEST_CHANNEL@@ \
  --mirror-mongo --mirror-tsm --mirror-sls --mirror-cfs --mirror-db2
```

  </div>
</div>

!!! note
    [Mirror Redhat images](https://ibm-mas.github.io/cli/commands/mirror-redhat-images) to install required ( DRO, Cert Manager and Grafana) redhat dependencies for Mas installation to progress. Missing this step will result in installation failures.

Storage Requirements
-------------------------------------------------------------------------------
As of MAS 8.10 (June 2023) the total capacity requirement to mirror content from the IBM Maximo Operator Catalog is approximately **484G**, the following table can be used to determine the approximate storage requirement for your mirrored content based on what content you need to mirror:

| Maximo Application Suite         | Command Flag                | Size    |
| -------------------------------- | --------------------------- | ------- |
| Maximo Operator Catalog          | `--mirror-catalog`          | 50M     |
| Maximo Application Suite Core    | `--mirror-core`             | 4G      |
| Maximo Assist                    | `--mirror-assist`           | 5G      |
| Maximo IoT                       | `--mirror-iot`              | 9G      |
| Maximo Manage                    | `--mirror-manage`           | 8G      |
| Maximo Monitor                   | `--mirror-monitor`          | 17G     |
| Maximo Optimizer                 | `--mirror-optimizer`        | 3G      |
| Maximo Predict                   | `--mirror-predict`          | 6G      |
| Maximo Visual Inspection         | `--mirror-visualinspection` | 40G     |
| Maximo Real Estate and Facilities| `--mirror-facilities`.      | TBD     |
| **Total**                        |                             | **92G** |

| IBM Cloud Pak for Data       | Command Flag                | Size     |
| ---------------------------- | --------------------------- | -------- |
| IBM CP4D Platform            | `--mirror-cp4d`             | 2G       |
| IBM Analytics Engine (Spark) | `--mirror-spark`            | 54G      |
| IBM Watson Machine Learning  | `--mirror-wml`              | 91G      |
| IBM Watson Studio Local      | `--mirror-wsl`              | 85G      |
| **Total**                    |                             | **273G** |

| Other Dependencies                | Command Flag                | Size     |
| --------------------------------- | --------------------------- | -------- |
| Mongo Community Edition           | `--mirror-mongo`            | 500M     |
| IBM Truststore Manager            | `--mirror-tsm`              | 1G       |
| IBM Suite License Service         | `--mirror-sls`              | 1G       |
| IBM Cloud Pak Foundation Services | `--mirror-cfs`              | 21G      |
| IBM Db2                           | `--mirror-db2`              | 73G      |
| **Total**                         |                             | **117G** |

!!! note
    The total capacity used on the filesystem in the target mirror registry itself may be lower than this due to the use of shared image layers, particularly across applications in IBM Maximo Application Suite itself.
