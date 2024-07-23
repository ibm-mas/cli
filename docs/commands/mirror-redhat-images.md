Mirror Red Hat Images
===============================================================================

Usage
-------------------------------------------------------------------------------
`mas mirror-redhat-images [options]`

### Mirror Mode
- `-m|--mode MIRROR_MODE` Operation mode (direct, to-filesystem, from-filesystem)
- `-d|--dir MIRROR_WORKING_DIR` Working directory for the mirror process
- `--mirror-platform` Mirror Red Hat Platform images
- `--mirror-operators` Mirror selected content from Red Hat Operator catalogs

### Registry Details
- `-H|--host REGISTRY_PUBLIC_HOST` Hostname of the target registry
- `-P|--port REGISTRY_PUBLIC_PORT` Port number for the target registry
- `-x|--prefix REGISTRY_PREFIX` Prefix for the mirror image (optional)
- `-u|--username REGISTRY_USERNAME` Username to authenticate to the target registry
- `-p|--password REGISTRY_PASSWORD` Password to authenticate to the target registry

### Red Hat Image Pull Secret (Required):
- `--pullsecret REDHAT_PULLSECRET` [Red Hat OpenShift Pull Secret](https://console.redhat.com/openshift/install/pull-secret)

### Content Selection (Optional):
- `--release OCP_RELEASE` OCP Release to mirror content for (e.g. 4.13, 4.14)

### Platform Version Range (Optional):
- `--min-version OCP_MIN_VERSION` Minimum version of the OCP release to mirror
- `--max-version OCP_MAX_VERSION` Maximum version of the OCP release to mirror

### Other Options
- `--no-confirm` Mirror images without prompting for confirmation
- `-h|--help` Show help message


Storage Requirements
-------------------------------------------------------------------------------
The selected content from the three required OpenShift operator catalogs requires approximately 80Gb.  The storage requirements for the OpenShift platform itself will vary depending on how many versions of the release you intent to mirror.


Video Walkthrough
-------------------------------------------------------------------------------
<iframe width="720" height="405" src="https://www.youtube.com/embed/d0qCF8qGumc?si=mWV0vmnnLnWvuicA" title="Video Walkthough: Mirror Red Hat Images" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>
<br />

Examples
-------------------------------------------------------------------------------
### Interactive Image Mirroring
```bash
docker run -ti --rm -v /mnt/storage:/mnt/local --pull always quay.io/ibmmas/cli mas mirror-redhat-images
```

### Two-Phase Image Mirroring
Two-Phase image mirroring is required when you do not have a single system with both access to the public registries containing the source container images **and** your internal private registry.  In this case you will require a system with internet connectivity and another with access to your private network, along with a means to transfer data from one to the other (for example, a portable drive).

!!! important
    The examples here use a specific version of the container image (6.0.0).  You should always use the latest available container image, but because we are working in a disconnected environment we need to be specific about the version we are using.  Replace `6.0.0` with the appropriate version.

#### Phase 1: Mirror to Filesystem
First, download the latest version of the container image and start up a terminal session inside the container image, we are going to mount a local directory into the running container to persist the mirror filesystem.

!!! tip
    Mirroring images for Core, Manage and all dependencies will require approximately 62Gb available capacity.

```bash
docker pull quay.io/ibmmas/cli:6.0.0
docker run -ti --rm -v /mnt/storage:/mnt/workspace quay.io/ibmmas/cli:6.0.0 mas mirror-redhat-images \
  --mode to-filesystem \
  --dir /mnt/workspace \
  --pull-secret /mnt/local/pull-secret.json
  --mirror-platform \
  --mirror-operators \
  --release 4.10 \
  --no-confirm
```

You must now transfer the content of `/mnt/storage` on your local filesystem to a system inside your disconnected network on which we will perform phase 2 of this operator.  However, before we can do that we also need to mirror the CLI image to your registry so that it's available on the disconnected host system.

```bash
oc image mirror --dir /mnt/workspace quay.io/ibmmas/cli:6.0.0 file://ibmmas/cli:6.0.0
```


#### Phase 2: Mirror from Filesystem
Transfer the content of `/mnt/storage` to your system in the disconnected network.  Now we are going to put the CLI image in your registry:

```bash
docker login mirror.mydomain.com:32500 -u admin -p password
oc image mirror --dir /mnt/storage file://ibmmas/cli:6.0.0 mirror.mydomain.com:32500/ibmmas/cli:6.0.0
```

Now we are ready to mirror the images to your registry using the CLI image in the same way we mirrored the images to the local disk in the first place:

```bash
docker pull mirror.mydomain.com:32500/ibmmas/cli:6.0.0
docker run -ti --rm -v /mnt/storage:/mnt/workspace mirror.mydomain.com:32500/ibmmas/cli:6.0.0 mas mirror-redhat-images \
  --mode from-filesystem \
  --dir /mnt/workspace \
  -H mirror.mydomain.com -P 32500 \
  -u admin -p password \
  --no-confirm
```


### Direct Image Mirroring
The following example will mirror all images required for Maximo Application Suite Core and the Maximo Manage and IoT applications directly to your target registry, without prompting for confirmation.

```bash
docker run -ti --rm -v /mnt/storage:/mnt/workspace --pull always quay.io/ibmmas/cli mas mirror-redhat-images \
  --mode direct \
  --dir /mnt/workspace \
  -H mirror.mydomain.com -P 32500 \
  -u admin -p password \
  --mirror-platform \
  --mirror-operators \
  --ocp-release 4.14 \
  --no-confirm
```
