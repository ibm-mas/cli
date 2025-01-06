Installation
===============================================================================
The install is designed to work on any OCP cluster, but has been specifically tested in these environments:

- IBMCloud ROKS
- Microsoft Azure
- AWS ROSA
- IBM DevIT FYRE (internal)

The engine that performs all tasks is written in Ansible, you can directly use the same automation outside of this CLI if you wish.  The code is open source and available in [ibm-mas/ansible-devops](https://github.com/ibm-mas/ansible-devops), the collection is also available to install directly from [Ansible Galaxy](https://galaxy.ansible.com/ibm/mas_devops), the install supports the following actions:

- IBM Maximo Operator Catalog installation
- Required dependency installation:
    - MongoDb (Community Edition)
    - IBM Suite License Service
    - IBM Data Reporter Operator
    - Red Hat Certificate Manager
- Optional dependency installation:
    - Apache Kafka
    - IBM Db2
    - IBM Cloud Pak for Data Platform and Services
        - [Watson Studio Local](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.0?topic=services-watson-studio)
        - [Watson Machine Learning](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.0?topic=services-watson-machine-learning)
        - [Watson OpenScale](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.0?topic=services-watson-openscale)
        - [Analytics Engine (Apache Spark)](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.0?topic=services-analytics-engine-powered-by-apache-spark)
        - Cognos Analytics
    - Grafana
    - Turbonomic Kubernetes Agent
- Suite core services installation
- Suite application installation

The installation is performed inside your RedHat OpenShift cluster utilizing [Openshift Pipelines](https://cloud.redhat.com/learn/topics/ci-cd)

> OpenShift Pipelines is a Kubernetes-native CI/CD solution based on Tekton. It builds on Tekton to provide a CI/CD experience through tight integration with OpenShift and Red Hat developer tools. OpenShift Pipelines is designed to run each step of the CI/CD pipeline in its own container, allowing each step to scale independently to meet the demands of the pipeline.

![](../img/pipeline.png)


Usage
-------------------------------------------------------------------------------
For full usage information run `mas install --help`


Preparation
-------------------------------------------------------------------------------
### IBM Entitlement Key
Access [Container Software Library](https://myibm.ibm.com/products-services/containerlibrary) using your IBMId to obtain your entitlement key.

### MAS License File
Access [IBM License Key Center](https://licensing.flexnetoperations.com/), on the **Get Keys** menu select **IBM AppPoint Suites**.  Select `IBM MAXIMO APPLICATION SUITE AppPOINT LIC` and on the next page fill in the information as below:

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

### OpenShift Cluster
You should already have a target OpenShift cluster ready to install Maximo Application suite into.  If you do not already have one then refer to the [OpenShift Container Platform installation overview](https://docs.openshift.com/container-platform/4.15/installing/index.html).

The CLI also supports OpenShift provisioning in many hyperscaler providers:

- [AWS](../commands/provision-rosa.md)
- [IBM Cloud](../commands/provision-roks.md)
- [IBM DevIT FYRE (Internal)](../commands/provision-fyre.md)


### Operator Catalog Selection
If you have not already determined the catalog version for your installation, refer to the information in the [Operator Catalog](../catalogs/index.md) topic, or contact IBM Support for guidance.


Disconnected Install Preparation
-------------------------------------------------------------------------------
### Prepare the Private Registry
You must have a production grade Docker v2 compatible registry such as [Quay Enterprise](https://www.redhat.com/en/technologies/cloud-computing/quay), [JFrog Artifactory](https://jfrog.com/integration/docker-registry/), or [Docker Registry](https://docs.docker.com/registry/).  If you do not already have a private registry available to use as your mirror then you can use the `setup-mirror` function to deploy a private registry using the [Docker registry container image](https://hub.docker.com/_/registry) inside a target OpenShift cluster.

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


### Mirror Container Images
Mirroring the images is a simple but time consuming process, this step must be performed from a system with internet connectivity and network access your private registry, but does not need access to your target OpenShift cluster.  Three modes are available for the mirror process:

- **direct** mirrors images directly from the source registry to your private registry
- **to-filesystem** mirrors images from the source to a local directory
- **from-filesystem** mirrors images from a local directory to your private registry

For full details on this process review the [image mirroring](image-mirroring.md) guide.


### Configure OpenShift to use your Private Registry
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


Interactive Install
-------------------------------------------------------------------------------
Regardless of whether you are running a connected or disconnected installation, simply run the `mas install` command and follow the prompts, the basic structure of the interactive flow is described below.

```bash
docker run -ti --rm -v ~:/mnt/home quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas install
```

!!! important
    We will need the `entitlement.lic` file to perform the installation which is why we mount your home directory into the container.  If you saved the entitlement file elsewhere, mount that directory instead.

    When prompted you will be able to set license file to `/mnt/home/entitlement.lic`


### Connect to OpenShift and Choose a Catalog
- If you are not already connected to an OpenShift cluster you will be prompted to provide the server URL & token to make a new connection.  If you are already connected to a cluster you will be given the option to change to another cluster
- You will be presented with a table of available catalogs with information about the different releases of MAS available in each
- Confirm that you accept the IBM Maximo Application Suite license terms


### Select Storage Classes
MAS requires both a `ReadWriteMany` and a `ReadWriteOnce` capable storage class to be available in the cluster.  The installer has the ability to recognize certain storage class providers and will default to the most appropriate storage class in these cases:

- IBMCloud Storage (`ibmc-block-gold` & `ibmc-file-gold-gid`)
- OpenShift Container Storage (`ocs-storagecluster-ceph-rbd` & `ocs-storagecluster-cephfs`)
- External OpenShift Container Storage (`ocs-external-storagecluster-ceph-rbd` & `ocs-external-storagecluster-cephfs`)
- NFS Client (`nfs-client`)
- Azure Managed Storage (`managed-premium` & `azurefiles-premium`)
- AWS Storage (`gp3-cs` & `efs`)

The names in brackets represent the `ReadWriteOnce` and `ReadWriteMany` class that will be used, in the case of NFS the same storage class will be used for both `ReadWriteOnce` and `ReadWriteMany` volumes.  Even when a recognized storage provider is detected you will be provided with the option to select your own storages classes if you wish.

When selecting your own storage classes you will be presented with a list of those available and must select both a `ReadWriteMany` and a `ReadWriteOnce` storage class.

!!! warning
    Unfortunately there is no way for the install to verify that the storage class selected actually supports the appropriate access mode, refer to the documentation from the storage class provider to determine whether your storage class supports `ReadWriteOnce` and/or `ReadWriteMany`.


### Provide a License File and Entitlement Key
Provide the location of your license file, contact information, and IBM entitlement key (if you have set the `IBM_ENTITLEMENT_KEY` environment variable then this field will be pre-filled with that value already).


### Configure your MAS Instance
Provide the basic information about your MAS instance:

- Instance ID
- Workspace ID
- Workspace Display Name
- Operational Mode (production or non-production)


### Configure Domain & Certificate Management
By default MAS will be installed in a subdomain of your OpenShift clusters domain matching the MAS instance ID that you chose.  For example if your OpenShift cluster is `myocp.net` and you are installing MAS with an instance ID of `prod1` then MAS will be installed with a default domain something like `prod1.apps.myocp.net`, depending on the exact network configuration of your cluster.

If you wish to use a custom domain for the MAS install you can choose to configure this by selecting "n" at the prompt.  The install supports DNS integrations for Cloudflare, IBM Cloud Internet Services, AWS Route 53 out of the box and is able to configure a certificate issuer using LetsEncrypt (production or staging) or a self-signed certificate authority per your choices.


### Advanced Settings
You will also be able to configure the following advanced settings:

- Single Sign-On (SSO)
- Whether to allow special character in User IDs and Usernames
- Whether Guided Tours are enabled


### Application Selection
Select the applications that you would like to install. Note that some applications cannot be installed unless an application they depend on is also installed:

- Monitor is only available for install if IoT is selected
- Assist and Predict are only available for install if Monitor is selected


### Application Configuration
Some Maximo applications support additional configuration, you will be taken through the configuration options for each application that you chose to install


### Configure Databases
The install supports the automatic provision of in-cluster MongoDb and Db2 databases for use with Maximo Application Suite, you may also choose to bring your own (BYO) by providing the necessary configuration files (which the installer will also help you create).


### Configure Integrations & Additional Configuration
The install supports the abilty to install and configure Turbonomic's Kubeturbo operator and the Grafana Community Operator.  Additional resource definitions can be applied to the OpenShift Cluster during the MAS configuration step, here you will be asked whether you wish to provide any additional configurations and if you do in what directory they reside.

!!! note
    If you provided one or more configurations for BYO databases then additional configurations will already be enabled and pointing at the directory you chose earlier.


### Pod Templates
You can choose between three pre-defined pod templates allowing you to configure MAS in each of the standard Kubernetes quality of service (QoS) levels: **Burstable**, [**BestEffort**](https://github.com/ibm-mas/cli/blob/master/image/cli/mascli/templates/pod-templates/best-effort) and [**Guaranteed**](https://github.com/ibm-mas/cli/blob/master/image/cli/mascli/templates/pod-templates/guaranteed). By default MAS applications are deployed with a `Burstable` QoS.

Additionally, you may provide your own custom pod templates definition by providing the directory containing your configuration files. More information on podTemplates can be found in the [product documentation](https://www.ibm.com/docs/en/mas-cd/continuous-delivery?topic=configuring-customizing-workloads).

!!! Note
    Pod templating support is only available in IBM Maximo Application Suite v8.11+


### Review Choices
Before the install actually starts you will be presented with a summary of all your choices and a non-interactive command that will allow you to repeat the same installation without going through all the prompts again.


Non-Interactive Install
-------------------------------------------------------------------------------
The following command will launch the MAS CLI container image, login to your OpenShift Cluster and start the install of MAS without triggering any prompts.  This is how we install MAS in development hundreds of times every single week.

```bash
IBM_ENTITLEMENT_KEY=xxx
SUPERUSER_PASSWORD=xxx

docker run -e IBM_ENTITLEMENT_KEY -e SUPERUSER_PASSWORD -ti --rm -v ~:/mnt/home quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@  bash -c "
  oc login --token=sha256~xxxx --server=https://xxx &&
  mas install \
    --mas-catalog-version @@MAS_LATEST_CATALOG@@ \
    --mas-instance-id mas1 \
    --mas-workspace-id ws1 \
    --mas-workspace-name "My Workspace"
    \
    --superuser-username superuser \
    --superuser-password '${SUPERUSER_PASSWORD}' \
    \
    --mas-channel @@MAS_LATEST_CHANNEL@@ \
    \
    --ibm-entitlement-key '${IBM_ENTITLEMENT_KEY}' \
    --license-file /mnt/home/entitlement.lic \
    --uds-email myemail@email.com \
    --uds-firstname John \
    --uds-lastname Barnes \
    \
    --storage-rwo ibmc-block-gold \
    --storage-rwx ibmc-file-gold-gid \
    --storage-pipeline ibmc-file-gold-gid \
    --storage-accessmode ReadWriteMany \
    \
    --accept-license --no-confirm
```
