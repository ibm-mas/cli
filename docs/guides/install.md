Installation
===============================================================================


Pre-requisites
-------------------------------------------------------------------------------
### IBM Entitlement Key
Access [Container Software Library](https://myibm.ibm.com/products-services/containerlibrary) using your IBMId to obtain your entitlement key.

### MAS License File
Access [IBM License Key Center](https://licensing.subscribenet.com/control/ibmr/login), on the **Get Keys** menu select **IBM AppPoint Suites**.  Select `IBM MAXIMO APPLICATION SUITE AppPOINT LIC` and on the next page fill in the information as below:

| Field            | Content                                           |
| ---------------- | ------------------------------------------------- |
| Number of Keys   | How many AppPoints to assign to the license file  |
| Host ID Type     | Set to **Ethernet Address**                       |
| Host ID          | Enter any 12 digit hexadecimal string             |
| Hostname         | Set to the hostname of your OCP instance          |
| Port             | Set to **27000**                                  |


The other values can be left at their defaults.  Finally, click **Generate** and download the license file to your home directory as `entitlement.lic`.

!!! note
    For more information about how to access the IBM License Key Center review the [getting started documentation](https://www.ibm.com/support/pages/system/files/inline-files/GettingStartedEnglish_2020.pdf) available from the IBM support website.

### OpenShift Cluster
You should already have a target OpenShift cluster ready to install Maximo Application suite into.  If you do not already have one then refer to the [OpenShift Container Platform installation overview](https://docs.openshift.com/container-platform/4.10/installing/index.html).

The CLI also supports OpenShift provisioning in many hyperscaler providers:

- [AWS](../commands/provision_rosa.md)
- [IBM Cloud](../commands/provision_roks.md)
- [IBM DevIT FYRE(Internal)](../commands/provision_fyre.md)


### Operator Catalog Selection
If you have not already determined the best catalog source for your installation, refer to the information in the [choosing the right IBM Maximo Operator Catalog to meet your requirements](choosing-the-right-catalog.md) guide, or contact IBM Support for guidance.


Disconnected Install Limitations
-------------------------------------------------------------------------------
Disconnected install for IBM Maximo Application Suite is supported from MAS v8.8 onwards with some restrictions:

| Application                | First Version to Support Air Gap  |
| -------------------------- | --------------------------------- |
| Core                       |  v8.8.0 ([v8-2022-07-17-amd64](../catalogs/v8-220717-amd64.md))     |
| Assist                     |  No support                       |
| Health & Predict Utilities |  No support                       |
| IoT                        |  v8.5.1 ([v8-2022-08-05-amd64](../catalogs/v8-220805-amd64.md))     |
| Manage                     |  v8.4.0 ([v8-2022-07-17-amd64](../catalogs/v8-220717-amd64.md))     |
| Monitor                    |  No support                       |
| Optimizer                  |  v8.2.0 ([v8-2022-07-17-amd64](../catalogs/v8-220717-amd64.md))     |
| Predict                    |  No support                       |
| Safety                     |  No support                       |
| Visual Inspection          |  No support                       |


Installation Overview
-------------------------------------------------------------------------------
1. [Prepare your Private Registry](#prepare-the-private-registry) (disconnected install only)
2. [Mirror Container Images](#mirror-container-images) (disconnected install only)
3. [Configure OpenShift to use your Private Registry for MAS](#configure-the-cluster) (disconnected install only)
4. [Install MAS](#install-maximo-application-suite)


Prepare the Private Registry
-------------------------------------------------------------------------------
If you do not already have a private registry available to use as your mirror then you can use the `setup-mirror` function to deploy a private registry inside a target OpenShift cluster.

```bash
docker pull quay.io/ibmmas/cli
docker run -ti quay.io/ibmmas/cli mas setup-registry
```

The registry will be setup running on port 32500.  For more details on this step, refer to the [setup-registry](../commands/setup-registry.md) command's documentation.  Regardless of whether you set up a new registry or already had one, you need to collect the following information about your private registry:

| Name | Detail |
| ---- | ------ |
| Private Hostname | The hostname by which the registry will be accessible from the target OCP cluster. |
| Private Port | The port number by which the registry will be accessible from the target OCP cluster. |
| Public Hostname | The hostname by which the registry will be accessible from the machine that will be performing image mirroring. |
| Public Port | The port number by which the registry will be accessible from the machine that will be performing image mirroring. |
| CA certificate file | The CA certificate that the registry will present on the **private** hostname. Save this to your home directory.  |
| Username | Optional.  Authentication username for the registry. |
| Password | Optional.  Authentication password for the registry. |


Mirror Container Images
-------------------------------------------------------------------------------
Mirroring the images is a simple but time consuming process, this step must be performed from a system with internet connectivity and network access your private registry, but does not need access to your target OpenShift cluster.

!!! tip
    You can also use this command to mirror the images for OpenShift itself, but that is beyond the scope of this guide.

```bash
docker pull quay.io/ibmmas/cli
docker run -ti quay.io/ibmmas/cli mas mirror-images
```

You will be prompted to set the target registry for the image mirroring and to [select the version of IBM Maximo Operator Catalog to mirror](choosing-the-right-catalog.md) and the subset of content that you wish to mirror  You can choose to mirror everything from the catalog, or control exactly what is mirrored to your private registry to reduce the time and bandwidth used to mirror the images, as well reducing the storage requirements of the registry.

This command can also be ran non-interactive, for full details refer to the [mirror-images](../commands/mirror-images.md) command documentation.


Configure OpenShift to use your Private Registry for MAS
-------------------------------------------------------------------------------
TODO: Work in progress ... basically run `mas configure-airgap`


Install Maximo Application Suite
-------------------------------------------------------------------------------
TODO: Work in progress .. basically run the install as normal: `mas install`
