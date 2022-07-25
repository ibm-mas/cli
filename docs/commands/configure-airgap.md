# Configure Airgap

!!! important
    The `configure-airgap` command does not work for **IBMCloud ROKS** clusters.  This is a limitation of the service provided in IBMCloud which disables key parts of OpenShift functionality required to configure and use ImageContentSourcePolicy resources (which is the basis of airgap/image mirroring support in OpenShift).


## Usage

```bash
docker run -ti --rm -v ~:/home/local quay.io/ibmmas/cli mas configure-airgap
```


## Air Gap Environments
Three commands are available to aid in the deployment of an Air Gap MAS installation.

### Stage 1: Prepare your mirror registry
- `mas setup-registry` will deploy a private docker registry on an OCP cluster suitable for hosting a mirror of all container images used in a MAS installation
- `mas mirror-images` will mirror all (or a subset) container images needed for a MAS installation to your private registry

### Stage 2: Configure the target cluster to use the mirror registry
- `mas configure-airgap` will configure your target OCP cluster to use a private docker register and will install the operator catalogs required by MAS from that mirror
