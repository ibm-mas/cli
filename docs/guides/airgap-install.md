Air Gap Installation
===============================================================================

Limitations
-------------------------------------------------------------------------------
Air gap installation for Maximo Application Suite is supported from MAS v8.8 onwards:

| Application                | First Version to Support Air Gap  |
| -------------------------- | --------------------------------- |
| Core                       |  v8.8.0 (v8-2022-07-17-amd64)     |
| Assist                     |  No support                       |
| Health & Predict Utilities |  No support                       |
| IoT                        |  v8.5.1 (v8-2022-08-05-amd64)     |
| Manage                     |  v8.4.0 (v8-2022-07-17-amd64)     |
| Monitor                    |  No support                       |
| Optimizer                  |  v8.2.0 (v8-2022-07-17-amd64)     |
| Predict                    |  No support                       |
| Safety                     |  No support                       |
| Visual Inspection          |  No support                       |

Pre-requisites
-------------------------------------------------------------------------------
### 1. IBM Entitlement key
Access [Container Software Library](https://myibm.ibm.com/products-services/containerlibrary) using your IBMId to obtain your entitlement key.

### 2. MAS License File
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

### 3. Working OpenShift cluster
You should already have a target OpenShift cluster ready to install Maximo Application suite into.


Prepare the Private Registry
-------------------------------------------------------------------------------
If you do not already have a mirror registry you can use the setup-mirror function to deploy a mirror registry inside a target OpenShift cluster

```bash
docker pull quay.io/ibmmas/cli
docker run -ti quay.io/ibmmas/cli mas setup-registry
```

The registry will be setup running on port 32500

Regardless of whether you set up a new mirror using `setup-registry` or already had one you need to collection the following information about your private registry:

| Name | Detail |
| ---- | ------ |
| Private Hostname | The hostname by which the registry will be accessible from the OCP cluster you are installing Maximo Application Suite. |
| Private Port | The port number by which the registry will be accessible from the OCP cluster you are installing Maximo Application Suite. |
| Public Hostname | The hostname by which the registry will be accessible from the machine that will be performing image mirroring. |
| Public Port | The port number by which the registry will be accessible from the machine that will be performing image mirroring. |
| CA certificate file | The CA certificate that the registry will present on the **private** hostname. Save this to your home directory.  |
| Username | Optional.  The username to authenticate to the registry as. |
| Password | Optional.  The password to authenticate to the registry with. |

For more details on this step, refer to the [install](../commands/install.md) command's documentation.


Populate the Mirror
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


Configure the Cluster
-------------------------------------------------------------------------------
TODO: Work in progress


Install Maximo Application Suite
-------------------------------------------------------------------------------
TODO: Work in progress
