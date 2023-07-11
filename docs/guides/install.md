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

| Application                | First Version to Support Air Gap                                |
| -------------------------- | --------------------------------------------------------------- |
| Core                       |  v8.8.0 ([v8-220717-amd64](../catalogs/v8-220717-amd64.md))     |
| Assist                     |  No support                                                     |
| Health & Predict Utilities |  No support                                                     |
| IoT                        |  v8.5.1 ([v8-220805-amd64](../catalogs/v8-220805-amd64.md))     |
| Manage                     |  v8.4.0 ([v8-220717-amd64](../catalogs/v8-220717-amd64.md))     |
| Monitor                    |  v8.10.0 ([v8-230414-amd64](../catalogs/v8-230414-amd64.md))    |
| Optimizer                  |  v8.2.0 ([v8-220717-amd64](../catalogs/v8-220717-amd64.md))     |
| Predict                    |  No support                                                     |
| Visual Inspection          |  No support                                                     |


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

!!! tip
    Wherever you see a `[Y/n]` or `[y/N]` prompt, the option in upper case is the default, and can be accepted just by hitting return.

    Selections are saved to file (`$HOME/.ibm-mas/cli.env`), if you make a mistake use `Ctrl+C` to quit the installer and when you run the install command again it will remember all your choices made to that point.

    In the unlikely event that you are running the install on a shared computer you should delete the `$HOME/.ibm-mas` directory after launching the installation.


### Step 1: Set Target OpenShift Cluster
If you are not already connected to an OpenShift cluster you will be prompted to provide the server URL & token, and whether to verify the server certificate or not,  If you are already connected to a cluster you will be given the option to change to another cluster.


### Step 2: Install OpenShift Pipelines Operator
No input is required during this step.  The Red Hat Pipelines Operator will be installed on the cluster (if it is not already).


### Step 3: IBM Maximo Operator Catalog Selection
You must decide whether to use the online dynamic catalog or an offline static catalog.  The default is to use the static catalog, for more information about catalog choice refer to [Choosing the right catalog](choosing-the-right-catalog.md).

If you selected to use a static catalog then you will be presented with a table of available catalogs and the versions of MAS available in the catalog.  Make the selection using the numbers in the left-most column.


### Step 4: License Terms
Confirm that you accept the IBM Maximo Application Suite license terms


### Step 5: Configure MAS Instance
Provide the basic information about your MAS instance:

- Instance ID
- Workspace ID
- Workspace Display Name


### Step 6: Configure Operation Mode
The install will default to a production mode installation, but by choosing "y" at the prompt you will be able to install MAS in non-production mode.


### Step 7. Configure Domain & Certificate Management
By default MAS will be installed in a subdomain of your OpenShift clusters domain matching the MAS instance ID that you chose.  For example if your OpenShift cluster is `myocp.net` and you are installing MAS with an instance ID of `prod1` then MAS will be installed with a default domain something like `prod1.apps.myocp.net`, depending on the exact network configuration of your cluster.

If you wish to use a custom domain for the MAS install you can choose to configure this by selecting "n" at the prompt.  The install supports DNS integrations for Cloudflare, IBM Cloud Internet Services, AWS Route 53 out of the box and is able to configure a certificate issuer using LetsEncrypt (production or staging) or a self-signed certificate authority per your choices.


### Step 8. Application Selection
Select the applications that you would like to install. Note that some applications cannot be installed unless an application they depend on is also installed:

- Monitor is only available for install if IoT is selected
- Assist and Predict are only available for install if Monitor is selected


### Step 9. Configure Datbases
If you have selected one or more applications that require a JDBC datasource (IoT, Manage, Monitor, & Predict) you must choose how to provide that dependency:

- Use the IBM Db2 Universal Operator
- Provide a JDBC configuration

If you choose the latter then you will be prompted to select a local directory where the configuration will be staged and requested to provide a display name, the JDBC connection URL, username, password, and whether the endpoint is SSL enabled (if it is then you will also be asked to provide the SSL certificate required to connect to the database).

!!! tip
    If you have already generated the configuration file (manually, or using the install previously) the CLI will detect this and prompt whether you wish to re-use the existing configuration, or generate a new one.


### Step 10. Additional Configurations
Additional resource definitions can be applied to the OpenShift Cluster during the MAS configuration step, here you will be asked whether you wish to provide any additional configurations and if you do in what directory they reside.

!!! note
    If you provided one or more JDBC configurations in step 9 then additional configurations will already be enabled and be pointing at the directory you chose for the JDBC configurations.


### Step 11. Configure Storage Class Usage
MAS requires both a `ReadWriteMany` and a `ReadWriteOnce` capable storage class to be available in the cluster.  The installer has the ability to recognize certain storage class providers and will default to the most appropriate storage class in these cases:

- IBMCloud Storage (`ibmc-block-gold` & `ibmc-file-gold`)
- OpenShift Container Storage (`ocs-storagecluster-ceph-rbd` & `ocs-storagecluster-cephfs`)
- Azure Managed Storage (`azurefiles-premium` & `managed-premium`)
- AWS Storage (`gp2` & `efs`)

Even when a recognized storage provider is detected you will be provided with the option to select your own storages classes anyway.

When selecting storage classes you will be presented with a list of available storage classes and must select both a `ReadWriteMany` and a `ReadWriteOnce` storage class.

!!! warning
    Unfortunately there is no way for the install to verify that the storage class selected actually supports the appropriate access mode, refer to the documention from the storage class provider to determine whetheryour storage class supports `ReadWriteOnce` and/or `ReadWriteMany`.


### Step 12. Advanced Settings
These settings can generally be ignored for most installations.

### Change Cluster monitoring storage defaults?
Answering "y" at the prompt will allow you to customize the storage capacity and data retention period in Grafana and Prometheus.

#### Change default install namespaces?
Answering "y" will allow you to customise the namespace where Db2, Grafana, and MongoDb are installed in the cluster.


### Step 13. Configure IBM Container Registry
Provide your IBM entitlement key.  If you have set the `IBM_ENTITLEMENT_KEY` environment variable then you will first be prompted whether you just want to re-use the saved entitlement key.


### Step 14. Configure Product License
Provide your license ID and the location of your license file.


### Step 15. Configure UDS
Maximo Application Suite's required integration with IBM User Data Services requires your e-mail address and first/last name be provided.


### Step 16. Prepare Installation
No input is required here, the install will prepare the namespace where install will be executed on the cluster and validate that the CLI container image (which will perform the installation) is accessible from your cluster.

!!! note
    For disconnected installations you may need to provide the digest of the ibmmas/cli container image.

### Step 17. Review Settings
A summary of all your choices will be presented and you will be prompted to provide a final confirmation as to whether to proceed with the install, or abort.
