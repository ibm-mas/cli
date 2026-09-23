Image Mirroring (v2)
===============================================================================
The `mas mirror` command is the next-generation Python-based image mirroring tool, replacing the legacy `mas mirror-images` bash command.  It uses [oc-mirror](https://docs.openshift.com/container-platform/latest/installing/disconnected_install/installing-mirroring-disconnected.html) under the hood and supports three mirror modes:

| Mode  | Description                                                                    |
| ----- | ------------------------------------------------------------------------------ |
| `m2m` | **Mirror to mirror** — pull from IBM registries and push directly to your private registry |
| `m2d` | **Mirror to disk** — pull from IBM registries and save to the local filesystem |
| `d2m` | **Disk to mirror** — push previously saved filesystem content to your private registry |

Two-phase mirroring (`m2d` followed by `d2m`) is recommended in most cases.  It requires more storage but cleanly separates the internet-facing download from the private-network upload, making it easier to recover from network interruptions.

This guide assumes you are targeting the latest release (**@@MAS_LATEST_CHANNEL@@**) from the most recent catalog (**@@MAS_LATEST_CATALOG@@**).  Remove any `--<package>` flags that correspond to applications or dependencies you are not deploying.


Usage
-------------------------------------------------------------------------------
For full usage information run:

```bash
mas mirror --help
```


Environment Variables
-------------------------------------------------------------------------------
The following environment variables are used to authenticate with registries.  Which ones are required depends on the mirror mode in use:

| Variable              | Required for modes | Description                                                  |
| --------------------- | ------------------ | ------------------------------------------------------------ |
| `IBM_ENTITLEMENT_KEY` | `m2m`, `m2d`       | IBM Entitlement Key to pull images from `cp.icr.io`          |
| `REGISTRY_USERNAME`   | `m2m`, `d2m`       | Username for your private target registry                    |
| `REGISTRY_PASSWORD`   | `m2m`, `d2m`       | Password for your private target registry                    |

```bash
export IBM_ENTITLEMENT_KEY=xxx
export REGISTRY_USERNAME=xxx
export REGISTRY_PASSWORD=xxx
```

Alternatively, you can provide a pre-built Docker/Podman credentials file via `--authfile <path>` to bypass automatic credential generation.


Interactive Image Mirroring
-------------------------------------------------------------------------------
Start image mirroring by running `mas mirror` with no extra flags.  You will be prompted to choose a mirror mode, a working directory, and which content to mirror:

```bash
LOCAL_DIR=/home/david/mirrorfiles
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror
```


Non-Interactive Image Mirroring
-------------------------------------------------------------------------------
The sections below walk through mirroring content in four stages using the two-phase approach (`m2d` + `d2m`).  Clear milestones make it easier to diagnose failures and measure progress:

- [Preparation](#preparation)
- [Stage 1 — MAS Core & Catalog](#stage-1-mas-core--catalog)
- [Stage 2 — MAS Applications](#stage-2-mas-applications)
- [Stage 3 — Cloud Pak for Data](#stage-3-cloud-pak-for-data)
- [Stage 4 — Other Dependencies](#stage-4-other-dependencies)


### Preparation
Set these environment variables once; they are reused in every stage:

```bash
export IBM_ENTITLEMENT_KEY=xxx
export LOCAL_DIR=xxx
export REGISTRY_HOST=xxx
export REGISTRY_USERNAME=xxx
export REGISTRY_PASSWORD=xxx
```

If the system that has internet access **cannot** reach your private registry, you will need to transfer the filesystem content (produced in the `m2d` phase) to a separate system on your private network before running the `d2m` phase.

To bootstrap the MAS CLI container itself into an air-gapped environment, first mirror it to the filesystem from an internet-connected system:

```bash
oc image mirror --dir $LOCAL_DIR/cli quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ file://ibmmas/cli:@@CLI_LATEST_VERSION@@ --filter-by-os='.*'
```

Transfer `$LOCAL_DIR/cli` to your private-network system and push the image to your mirror registry:

```bash
docker login $REGISTRY_HOST -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD
oc image mirror --dir $LOCAL_DIR/cli file://ibmmas/cli:@@CLI_LATEST_VERSION@@ $REGISTRY_HOST/ibmmas/cli:@@CLI_LATEST_VERSION@@ --filter-by-os='.*'
```

!!! note
    To mirror single-architecture images and save storage, export `MIRROR_SINGLE_ARCH` before running any stage. Supported values: `amd64`, `ppc64le`, `s390x`.
    ```bash
    export MIRROR_SINGLE_ARCH=amd64
    ```


### Stage 1 — MAS Core & Catalog

<cds-tabs trigger-content="Select an item" value="m2m">
  <cds-tab id="tab-m2m-core" target="panel-m2m-core" value="m2m">Mirror to Mirror</cds-tab>
  <cds-tab id="tab-m2d-core" target="panel-m2d-core" value="m2d">Mirror to Disk</cds-tab>
  <cds-tab id="tab-d2m-core" target="panel-d2m-core" value="d2m">Disk to Mirror</cds-tab>
</cds-tabs>

<div class="tab-panel">
  <div id="panel-m2m-core" role="tabpanel" aria-labelledby="tab-m2m-core" hidden>

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry \
  -e IBM_ENTITLEMENT_KEY=$IBM_ENTITLEMENT_KEY \
  -e REGISTRY_USERNAME=$REGISTRY_USERNAME \
  -e REGISTRY_PASSWORD=$REGISTRY_PASSWORD \
  quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror \
  --catalog @@MAS_LATEST_CATALOG@@ --release @@MAS_LATEST_CHANNEL@@ \
  --mode m2m --target-registry $REGISTRY_HOST \
  --dir /mnt/registry/core \
  --core
```

  </div>
  <div id="panel-m2d-core" role="tabpanel" aria-labelledby="tab-m2d-core" hidden>

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry \
  -e IBM_ENTITLEMENT_KEY=$IBM_ENTITLEMENT_KEY \
  quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror \
  --catalog @@MAS_LATEST_CATALOG@@ --release @@MAS_LATEST_CHANNEL@@ \
  --mode m2d \
  --dir /mnt/registry/core \
  --core
```

  </div>
  <div id="panel-d2m-core" role="tabpanel" aria-labelledby="tab-d2m-core" hidden>
    <p>Transfer the contents of <code>$LOCAL_DIR/core</code> to your system in the private network and run the disk-to-mirror phase using the CLI image from your mirror registry.</p>

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry \
  -e REGISTRY_USERNAME=$REGISTRY_USERNAME \
  -e REGISTRY_PASSWORD=$REGISTRY_PASSWORD \
  $REGISTRY_HOST/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror \
  --catalog @@MAS_LATEST_CATALOG@@ --release @@MAS_LATEST_CHANNEL@@ \
  --mode d2m --target-registry $REGISTRY_HOST \
  --dir /mnt/registry/core \
  --core
```

  </div>
</div>


### Stage 2 — MAS Applications

<cds-tabs trigger-content="Select an item" value="m2m">
  <cds-tab id="tab-m2m-apps" target="panel-m2m-apps" value="m2m">Mirror to Mirror</cds-tab>
  <cds-tab id="tab-m2d-apps" target="panel-m2d-apps" value="m2d">Mirror to Disk</cds-tab>
  <cds-tab id="tab-d2m-apps" target="panel-d2m-apps" value="d2m">Disk to Mirror</cds-tab>
</cds-tabs>

<div class="tab-panel">
  <div id="panel-m2m-apps" role="tabpanel" aria-labelledby="tab-m2m-apps" hidden>

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry \
  -e IBM_ENTITLEMENT_KEY=$IBM_ENTITLEMENT_KEY \
  -e REGISTRY_USERNAME=$REGISTRY_USERNAME \
  -e REGISTRY_PASSWORD=$REGISTRY_PASSWORD \
  quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror \
  --catalog @@MAS_LATEST_CATALOG@@ --release @@MAS_LATEST_CHANNEL@@ \
  --mode m2m --target-registry $REGISTRY_HOST \
  --dir /mnt/registry/apps \
  --assist --iot --manage --manage-icd --monitor --optimizer --predict --visualinspection --facilities
```

  </div>
  <div id="panel-m2d-apps" role="tabpanel" aria-labelledby="tab-m2d-apps" hidden>

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry \
  -e IBM_ENTITLEMENT_KEY=$IBM_ENTITLEMENT_KEY \
  quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror \
  --catalog @@MAS_LATEST_CATALOG@@ --release @@MAS_LATEST_CHANNEL@@ \
  --mode m2d \
  --dir /mnt/registry/apps \
  --assist --iot --manage --manage-icd --monitor --optimizer --predict --visualinspection --facilities
```

  </div>
  <div id="panel-d2m-apps" role="tabpanel" aria-labelledby="tab-d2m-apps" hidden>
    <p>Transfer the contents of <code>$LOCAL_DIR/apps</code> to your system in the private network and run the disk-to-mirror phase.</p>

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry \
  -e REGISTRY_USERNAME=$REGISTRY_USERNAME \
  -e REGISTRY_PASSWORD=$REGISTRY_PASSWORD \
  $REGISTRY_HOST/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror \
  --catalog @@MAS_LATEST_CATALOG@@ --release @@MAS_LATEST_CHANNEL@@ \
  --mode d2m --target-registry $REGISTRY_HOST \
  --dir /mnt/registry/apps \
  --assist --iot --manage --manage-icd --monitor --optimizer --predict --visualinspection --facilities
```

  </div>
</div>


### Stage 3 — Cloud Pak for Data

<cds-tabs trigger-content="Select an item" value="m2m">
  <cds-tab id="tab-m2m-cp4d" target="panel-m2m-cp4d" value="m2m">Mirror to Mirror</cds-tab>
  <cds-tab id="tab-m2d-cp4d" target="panel-m2d-cp4d" value="m2d">Mirror to Disk</cds-tab>
  <cds-tab id="tab-d2m-cp4d" target="panel-d2m-cp4d" value="d2m">Disk to Mirror</cds-tab>
</cds-tabs>

<div class="tab-panel">
  <div id="panel-m2m-cp4d" role="tabpanel" aria-labelledby="tab-m2m-cp4d" hidden>

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry \
  -e IBM_ENTITLEMENT_KEY=$IBM_ENTITLEMENT_KEY \
  -e REGISTRY_USERNAME=$REGISTRY_USERNAME \
  -e REGISTRY_PASSWORD=$REGISTRY_PASSWORD \
  quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror \
  --catalog @@MAS_LATEST_CATALOG@@ --release @@MAS_LATEST_CHANNEL@@ \
  --mode m2m --target-registry $REGISTRY_HOST \
  --dir /mnt/registry/cp4d \
  --cp4d-platform --cp4d-wsl --cp4d-wml --cp4d-spark --cp4d-cognos
```

  </div>
  <div id="panel-m2d-cp4d" role="tabpanel" aria-labelledby="tab-m2d-cp4d" hidden>

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry \
  -e IBM_ENTITLEMENT_KEY=$IBM_ENTITLEMENT_KEY \
  quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror \
  --catalog @@MAS_LATEST_CATALOG@@ --release @@MAS_LATEST_CHANNEL@@ \
  --mode m2d \
  --dir /mnt/registry/cp4d \
  --cp4d-platform --cp4d-wsl --cp4d-wml --cp4d-spark --cp4d-cognos
```

  </div>
  <div id="panel-d2m-cp4d" role="tabpanel" aria-labelledby="tab-d2m-cp4d" hidden>
    <p>Transfer the contents of <code>$LOCAL_DIR/cp4d</code> to your system in the private network and run the disk-to-mirror phase.</p>

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry \
  -e REGISTRY_USERNAME=$REGISTRY_USERNAME \
  -e REGISTRY_PASSWORD=$REGISTRY_PASSWORD \
  $REGISTRY_HOST/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror \
  --catalog @@MAS_LATEST_CATALOG@@ --release @@MAS_LATEST_CHANNEL@@ \
  --mode d2m --target-registry $REGISTRY_HOST \
  --dir /mnt/registry/cp4d \
  --cp4d-platform --cp4d-wsl --cp4d-wml --cp4d-spark --cp4d-cognos
```

  </div>
</div>


### Stage 4 — Other Dependencies

<cds-tabs trigger-content="Select an item" value="m2m">
  <cds-tab id="tab-m2m-deps" target="panel-m2m-deps" value="m2m">Mirror to Mirror</cds-tab>
  <cds-tab id="tab-m2d-deps" target="panel-m2d-deps" value="m2d">Mirror to Disk</cds-tab>
  <cds-tab id="tab-d2m-deps" target="panel-d2m-deps" value="d2m">Disk to Mirror</cds-tab>
</cds-tabs>

<div class="tab-panel">
  <div id="panel-m2m-deps" role="tabpanel" aria-labelledby="tab-m2m-deps" hidden>

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry \
  -e IBM_ENTITLEMENT_KEY=$IBM_ENTITLEMENT_KEY \
  -e REGISTRY_USERNAME=$REGISTRY_USERNAME \
  -e REGISTRY_PASSWORD=$REGISTRY_PASSWORD \
  quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror \
  --catalog @@MAS_LATEST_CATALOG@@ --release @@MAS_LATEST_CHANNEL@@ \
  --mode m2m --target-registry $REGISTRY_HOST \
  --dir /mnt/registry/deps \
  --sls --tsm --mongodb-ce --db2u-s11 --db2u-s12 --data-dictionary --amlen
```

  </div>
  <div id="panel-m2d-deps" role="tabpanel" aria-labelledby="tab-m2d-deps" hidden>

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry \
  -e IBM_ENTITLEMENT_KEY=$IBM_ENTITLEMENT_KEY \
  quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror \
  --catalog @@MAS_LATEST_CATALOG@@ --release @@MAS_LATEST_CHANNEL@@ \
  --mode m2d \
  --dir /mnt/registry/deps \
  --sls --tsm --mongodb-ce --db2u-s11 --db2u-s12 --data-dictionary --amlen
```

  </div>
  <div id="panel-d2m-deps" role="tabpanel" aria-labelledby="tab-d2m-deps" hidden>
    <p>Transfer the contents of <code>$LOCAL_DIR/deps</code> to your system in the private network and run the disk-to-mirror phase.</p>

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry \
  -e REGISTRY_USERNAME=$REGISTRY_USERNAME \
  -e REGISTRY_PASSWORD=$REGISTRY_PASSWORD \
  $REGISTRY_HOST/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror \
  --catalog @@MAS_LATEST_CATALOG@@ --release @@MAS_LATEST_CHANNEL@@ \
  --mode d2m --target-registry $REGISTRY_HOST \
  --dir /mnt/registry/deps \
  --sls --tsm --mongodb-ce --db2u-s11 --db2u-s12 --data-dictionary --amlen
```

  </div>
</div>


Mirror All Packages
-------------------------------------------------------------------------------
To mirror every supported package in one command, use `--all`.  This is convenient but will require significantly more storage and time than mirroring only what you need.

```bash
docker run -ti --rm -v $LOCAL_DIR:/mnt/registry \
  -e IBM_ENTITLEMENT_KEY=$IBM_ENTITLEMENT_KEY \
  -e REGISTRY_USERNAME=$REGISTRY_USERNAME \
  -e REGISTRY_PASSWORD=$REGISTRY_PASSWORD \
  quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas mirror \
  --catalog @@MAS_LATEST_CATALOG@@ --release @@MAS_LATEST_CHANNEL@@ \
  --mode m2m --target-registry $REGISTRY_HOST \
  --dir /mnt/registry/all \
  --all
```

!!! note
    [Mirror Red Hat images](https://ibm-mas.github.io/cli/commands/mirror-redhat-images) to install required Red Hat dependencies (DRO, Cert Manager, and Grafana) needed for MAS installation. Missing this step will result in installation failures.


Advanced Options
-------------------------------------------------------------------------------

| Flag                     | Default | Description                                                                 |
| ------------------------ | ------- | --------------------------------------------------------------------------- |
| `--authfile <path>`      | —       | Path to an existing Docker/Podman auth file; skips credential auto-generation |
| `--dest-tls-verify`      | `true`  | Verify TLS certificates for the destination registry (`true`/`false`)       |
| `--image-timeout`        | `20m`   | Per-image operation timeout (e.g., `1h20m10s`, `1h`, `20m`, `10s`)         |
