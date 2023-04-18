Installation
===============================================================================

Installation Overview
-------------------------------------------------------------------------------
1. [Pre-requistes](#1-pre-requisites)
    - 1.1 [IBM Entitlement Key](#11-ibm-entitlement-key)
    - 1.2 [MAS License File](#12-mas-license-file)
    - 1.3 [OpenShift Cluster](#13-openshift-cluster)
    - 1.4 [Operator Catalog Selection](#14-operator-catalog-selection)
2. [Disconnected Install Preparation](#2-disconnected-install-preparation)
    - 2.1 [Disconnected Install Limitations](#21-disconnected-install-limitations)
    - 2.2 [Prepare your Private Registry](#22-prepare-the-private-registry)
    - 2.3 [Mirror Container Images](#23-mirror-container-images)
    - 2.4 [Configure OpenShift to use your Private Registry for MAS](#24-configure-openshift-to-use-your-private-registry-for-mas)
3. [Install MAS](#3-install-maximo-application-suite)


1 Pre-requisites
-------------------------------------------------------------------------------
### 1.1 IBM Entitlement Key
Access [Container Software Library](https://myibm.ibm.com/products-services/containerlibrary) using your IBMId to obtain your entitlement key.

### 1.2 MAS License File
Access [IBM License Key Center](https://licensing.subscribenet.com/control/ibmr/login), on the **Get Keys** menu select **IBM AppPoint Suites**.  Select `IBM MAXIMO APPLICATION SUITE AppPOINT LIC` and on the next page fill in the information as below:

| Field            | Content                                                                       |
| ---------------- | ----------------------------------------------------------------------------- |
| Number of Keys   | How many AppPoints to assign to the license file                              |
| Host ID Type     | Set to **Ethernet Address**                                                   |
| Host ID          | Enter any 12 digit hexadecimal string                                         |
| Hostname         | Set to the hostname of your OCP instance, but this can be any value really.   |
| Port             | Set to **27000**                                                              |


The other values can be left at their defaults.  Finally, click **Generate** and download the license file to your home directory as `entitlement.lic`.

!!! note
    For more information about how to access the IBM License Key Center review the [getting started documentation](https://www.ibm.com/support/pages/system/files/inline-files/GettingStartedEnglish_2020.pdf) available from the IBM support website.

### 1.3 OpenShift Cluster
You should already have a target OpenShift cluster ready to install Maximo Application suite into.  If you do not already have one then refer to the [OpenShift Container Platform installation overview](https://docs.openshift.com/container-platform/4.10/installing/index.html).

The CLI also supports OpenShift provisioning in many hyperscaler providers:

- [AWS](../commands/provision-rosa.md)
- [IBM Cloud](../commands/provision-roks.md)
- [IBM DevIT FYRE(Internal)](../commands/provision-fyre.md)


### 1.4 Operator Catalog Selection
If you have not already determined the best catalog source for your installation, refer to the information in the [choosing the right IBM Maximo Operator Catalog to meet your requirements](choosing-the-right-catalog.md) guide, or contact IBM Support for guidance.


2 Disconnected Install Preparation
-------------------------------------------------------------------------------

### 2.1 Disconnected Install Limitations
Disconnected install for IBM Maximo Application Suite is supported from MAS v8.8 onwards with some restrictions:

| Application                | First Version to Support Air Gap  |
| -------------------------- | --------------------------------- |
| Core                       |  v8.8.0 ([v8-220717-amd64](../catalogs/v8-220717-amd64.md))     |
| Assist                     |  No support                       |
| Health & Predict Utilities |  No support                       |
| IoT                        |  v8.5.1 ([v8-220805-amd64](../catalogs/v8-220805-amd64.md))     |
| Manage                     |  v8.4.0 ([v8-220717-amd64](../catalogs/v8-220717-amd64.md))     |
| Monitor                    |  v8.10.0 ([v8-230414-amd64](../catalogs/v8-230414-amd64.md))    |
| Optimizer                  |  v8.2.0 ([v8-220717-amd64](../catalogs/v8-220717-amd64.md))     |
| Predict                    |  No support                       |
| Safety                     |  No support                       |
| Visual Inspection          |  No support                       |


### 2.2 Prepare the Private Registry
If you do not already have a private registry available to use as your mirror then you can use the `setup-mirror` function to deploy a private registry inside a target OpenShift cluster.

```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas setup-registry
```

The registry will be setup running on port 32500.  For more details on this step, refer to the [setup-registry](../commands/setup-registry.md) command's documentation.  Regardless of whether you set up a new registry or already had one, you need to collect the following information about your private registry:

| Name                | Detail                                                                                                             |
| ------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Private Hostname    | The hostname by which the registry will be accessible from the target OCP cluster.                                 |
| Private Port        | The port number by which the registry will be accessible from the target OCP cluster.                              |
| Public Hostname     | The hostname by which the registry will be accessible from the machine that will be performing image mirroring.    |
| Public Port         | The port number by which the registry will be accessible from the machine that will be performing image mirroring. |
| CA certificate file | The CA certificate that the registry will present on the **private** hostname. Save this to your home directory.   |
| Username            | Optional.  Authentication username for the registry.                                                               |
| Password            | Optional.  Authentication password for the registry.                                                               |


### 2.3 Mirror Container Images
Mirroring the images is a simple but time consuming process, this step must be performed from a system with internet connectivity and network access your private registry, but does not need access to your target OpenShift cluster.  Three modes are available for the mirror process:

- **direct** mirrors images directly from the source registry to your private registry
- **to-filesystem** mirrors images from the source to a local directory
- **from-filesystem** mirrors images from a local directory to your private registry

```bash
docker run -ti --pull always quay.io/ibmmas/cli mas mirror-images
```

You will be prompted to set the target registry for the image mirroring and to [select the version of IBM Maximo Operator Catalog to mirror](choosing-the-right-catalog.md) and the subset of content that you wish to mirror.  You can choose to mirror everything from the catalog, or control exactly what is mirrored to your private registry to reduce the time and bandwidth used to mirror the images, as well reducing the storage requirements of the registry.

This command can also be ran non-interactive, for full details refer to the [mirror-images](../commands/mirror-images.md) command documentation.

```bash
mas mirror-images \
  -m direct \
  -d /mnt/local-mirror/ \
  -H myprivateregistry.com -P 5000 -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  -c v8-221025-amd64 --mirror-core --mirror-iot --mirror-optimizer --mirror-manage \
  --ibm-entitlement $IBM_ENTITLEMENT_KEY \
  --redhat-username $REDHAT_USERNAME --redhat-password $REDHAT_PASSWORD \
  --no-confirm
```

### 2.4 Configure OpenShift to use your Private Registry for MAS
Your cluster must be configured to use the private registry as a mirror for the MAS container images.  An `ImageContentSourcePolicy` named `mas-and-dependencies` will be created in the cluster, this is also the resource that the MAS install will use to detect whether the installation is a disconnected install and tailor the options presented when you run the `mas install` command.

```bash
docker run -ti --pull always quay.io/ibmmas/cli mas configure-airgap
```

You will be prompted to provide information about the private registry, including the CA certificate necessary to configure your cluster to trust the private registry.

This command can also be ran non-interactive, for full details refer to the [configure-airgap](../commands/configure-airgap.md) command documentation.

```bash
mas configure-airgap \
  -H myprivateregistry.com -P 5000 -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD \
  --ca-file /mnt/local-mirror/registry-ca.crt \
  --no-confirm
```


3 Install Maximo Application Suite
-------------------------------------------------------------------------------
Regardless of whether you are running a connected or disconnect installation, simply run the `mas install` command and follow the prompts.

```bash
docker run -ti --pull always quay.io/ibmmas/cli mas install
```
