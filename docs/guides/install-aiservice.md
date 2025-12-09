Installation
===============================================================================
Usage
-------------------------------------------------------------------------------
For full usage information run `mas aiservice-install --help` <br>
`mas aiservice-install` is specifically built for installation of Aiservice 9.1.x or above. <br>
<br>
For installation of Aiservice 9.0.x have to use `mas install` command.

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


Interactive Install
-------------------------------------------------------------------------------
Regardless of whether you are running a connected or disconnected installation, simply run the `mas aiservice-install` command and follow the prompts, the basic structure of the interactive flow is described below.

We will need the `entitlement.lic` file to perform the installation so we will mount your home directory into the running container.  When prompted you will be able to set license file to `/mnt/home/entitlement.lic` - <b> This is a prerequisite step, required only when `sls` has not been installed previously. </b>

```bash
docker run -ti --rm -v ~:/mnt/home quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas aiservice-install
```

The interactive install will guide you through a series of questioned designed to help you arrive at the best configuration for your scenario, it can be broken down as below:

<div>
  <cds-accordion>
    <cds-accordion-item title="Connect to OpenShift and Choose a Catalog">
      <p>If you are not already connected to an OpenShift cluster you will be prompted to provide the server URL & token to make a new connection.  If you are already connected to a cluster you will be given the option to change to another cluster</p>
      <p>You will be presented with a table of available catalogs with information about the different releases of MAS</p>
      <p>Confirm that you accept the IBM Maximo Application Suite license terms</p>
    </cds-accordion-item>
    <cds-accordion-item title="Select Storage Classes">
      <p>MAS requires both a `ReadWriteMany` and a `ReadWriteOnce` capable storage class to be available in the cluster.  The installer has the ability to recognize certain storage class providers and will default to the most appropriate storage class in these cases:</p>
      <ul>
        <li>IBMCloud Storage (ibmc-block-gold & ibmc-file-gold-gid)</li>
        <li>OpenShift Container Storage (ocs-storagecluster-ceph-rbd & ocs-storagecluster-cephfs)</li>
        <li>External OpenShift Container Storage (ocs-external-storagecluster-ceph-rbd & ocs-external-storagecluster-cephfs)</li>
        <li>NFS Client (nfs-client)</li>
        <li>Azure Managed Storage (managed-premium & azurefiles-premium)</li>
        <li>AWS Storage (gp3-cs & efs)</li>
      </ul>
      <p>The names in brackets represent the `ReadWriteOnce` and `ReadWriteMany` class that will be used, in the case of NFS the same storage class will be used for both `ReadWriteOnce` and `ReadWriteMany` volumes.  Even when a recognized storage provider is detected you will be provided with the option to select your own storages classes if you wish.</p>
      <p>When selecting your own storage classes you will be presented with a list of those available and must select both a `ReadWriteMany` and a `ReadWriteOnce` storage class.  Unfortunately there is no way for the install to verify that the storage class selected actually supports the appropriate access mode, refer to the documentation from the storage class provider to determine whether your storage class supports `ReadWriteOnce` and/or `ReadWriteMany`.</p>
    </cds-accordion-item>
    <cds-accordion-item title="Provide a License File and Entitlement Key">
      <p>Provide the location of your license file, contact information, and IBM entitlement key (if you have set the <code>IBM_ENTITLEMENT_KEY</code> environment variable then this field will be pre-filled with that value already).</p>
    </cds-accordion-item>
    <cds-accordion-item title="Configure your Aiservice Instance">
      <p>Provide the basic information about your Aiservice instance:</p>
      <ul>
        <li>Instance ID</li>
        <li>Configure s3 storage, DB, RSL and tenant</li>
        <li>Choose to install SLS, DB2, or DRO as a dependency, or opt out and provide alternative information including connection URL and token.</li>
        <li>Operational Mode (production or non-production)</li>
      </ul>
    </cds-accordion-item>
    <cds-accordion-item title="Review Choices">
      <p>Before the install actually starts you will be presented with a summary of all your choices and a non-interactive command that will allow you to repeat the same installation without going through all the prompts again.</p>
    </cds-accordion-item>

  </cds-accordion>
</div>

Non-Interactive Install
-------------------------------------------------------------------------------
The following command will launch the MAS CLI container image, login to your OpenShift Cluster and start the install of MAS without triggering any prompts.  This is how we install MAS in development hundreds of times every single week.

```bash
IBM_ENTITLEMENT_KEY=xxx

docker run -e IBM_ENTITLEMENT_KEY -e SUPERUSER_PASSWORD -ti --rm -v ~:/mnt/home quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@  bash -c "
  oc login --token=sha256~xxxx --server=https://xxx &&
  mas aiservice-install \
    --mas-catalog-version @@MAS_LATEST_CATALOG@@ \
    --aiservice-instance-id aib1 \
    --aiservice-channel 9.1.x \
    \
    --ibm-entitlement-key '${IBM_ENTITLEMENT_KEY}' \
    --license-file /mnt/home/entitlement.lic \
    --contact-email myemail@email.com \
    --contact-firstname John \
    --contact-lastname Barnes \
    \
    --storage-rwo ibmc-block-gold \
    --storage-rwx ibmc-file-gold-gid \
    --storage-pipeline ibmc-file-gold-gid \
    --storage-accessmode ReadWriteMany \
    \
    --accept-license --no-confirm
```

More Information
-------------------------------------------------------------------------------
The install is designed to work on any OCP cluster, but has been specifically tested in these environments:

- IBMCloud ROKS
- IBM DevIT FYRE (internal)

The engine that performs all tasks is written in Ansible, you can directly use the same automation outside of this CLI if you wish.  The code is open source and available in [ibm-mas/ansible-devops](https://github.com/ibm-mas/ansible-devops), the collection is also available to install directly from [Ansible Galaxy](https://galaxy.ansible.com/ibm/mas_devops), the install supports the following actions:

- IBM Maximo Operator Catalog installation
- Required dependency installation:
    - MongoDb (Community Edition) - only needed when want to install SLS.
    - IBM Suite License Service (installed instance of SLS also can be used).
    - IBM Data Reporter Operator
    - Red Hat Certificate Manager
    - Minio
    - db2
-  Aiservice installation

<div style="clear: right"></div>

The installation is performed inside your RedHat OpenShift cluster utilizing [Openshift Pipelines](https://cloud.redhat.com/learn/topics/ci-cd)

> OpenShift Pipelines is a Kubernetes-native CI/CD solution based on Tekton. It builds on Tekton to provide a CI/CD experience through tight integration with OpenShift and Red Hat developer tools. OpenShift Pipelines is designed to run each step of the CI/CD pipeline in its own container, allowing each step to scale independently to meet the demands of the pipeline.
