Installation
===============================================================================

:::mas-cli-usage
module: mas.cli.install.argParser
parser: installArgParser
ignore_description: true
ignore_epilog: true
:::


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

### OpenShift Container Platform
You should already have a target OpenShift cluster ready to install Maximo Application suite into.  If you do not already have one then refer to the [OpenShift Container Platform installation overview](https://docs.redhat.com/en/documentation/openshift_container_platform/4.20/html/installation_overview/index).  The CLI also supports OpenShift provisioning in many hyperscaler providers:

- [AWS](../commands/provision-rosa.md)
- [IBM Cloud](../commands/provision-roks.md)
- [IBM DevIT FYRE (Internal)](../commands/provision-fyre.md)

IBM Maximo Application Suite is designed to run on a continuously evolving OpenShift platform. Red Hat regularly updates its operator catalogs (including the Community Operators catalog that provides components such as Grafana), and these updates can sometimes introduce breaking changes. To ensure stable, reproducible installations, it is essential to align the versions of OpenShift, Red Hat operator catalogs, the IBM Maximo operator catalog, and the MAS CLI.

#### Supporting Older Versions of MAS
When newer Red Hat operator catalogs are used with older MAS versions, incompatibilities can occur. A common example is issues with Grafana (sourced from the Red Hat Community Operators catalog). The Maximo team deliver compatibility fixes and workarounds for these kinds of issues in the monthly updates; but these fixes can not be made available in older catalogs because they are immutable.

##### Understanding the Challenge: An Analogy
If you want to freeze the version of the apps you are running on your mobile device you would also turn off auto-updates for the operating system. You would not expect year-old versions of those apps to function with modern versions of the operating system. With Red Hat OpenShift and Maximo Application Suite it is the same.

Customers who wish to maintain an older MAS version for an extended period must apply the same versioning discipline to the entire underlying platform. Mixing an older Maximo operator catalog with newer Red Hat operator catalogs is not supported and will lead to unexpected behavior.

If your organization's policies require extended stability windows (e.g., 6–12 months without updates), you must lock **all** components at specific, immutable versions. This approach is supported but carries increased security exposure over time.

##### When to Use Static Versioning

Use this approach if:

- Your organization requires 6-12+ month stability windows between updates
- You need guaranteed reproducibility for compliance, audit, or regulatory purposes
- You have strict change control processes that prevent frequent updates
- You can accept delayed security updates and increased security risk over time
- You have resources to manage and document version pinning

Do NOT use this approach if:

- You need the latest security patches and bug fixes
- Your compliance requirements mandate current security updates
- You lack resources to maintain detailed version documentation
- You cannot accept increased security exposure

##### Creating a Fully Reproducible, Static Installation

To guarantee an identical installation months or years later, you must lock all four of the following elements:

| Component | Example | How to Pin | Notes |
|-----------|---------|------------|-------|
| **OpenShift Version** | `4.18.3` | Disable cluster auto-updates | Specific patch version required |
| **Red Hat Catalogs** | `sha256:xxxxx` | Use digest in CatalogSource | Must pin all Red Hat catalogs |
| **IBM MAS Catalog** | `@@MAS_LATEST_CATALOG@@` | Specify exact catalog version | Use immutable catalog version |
| **MAS CLI Version** | `@@CLI_LATEST_VERSION@@` | Use specific image tag | Document exact version used |

!!! warning "Critical Requirement"
    All four elements must be pinned together. Pinning only some components creates an unstable, unsupported configuration. If any one element is allowed to vary, you do not have a static, reproducible environment.

##### Step-by-Step Guidance

###### Step 1: Extract Catalog Digests

For each Red Hat CatalogSource you want to pin, retrieve the current digest:

```bash
for CATALOG_NAME in "community-operators" "redhat-operators" "certified-operators"; do
  oc get pods -n openshift-marketplace -l olm.catalogSource=${CATALOG_NAME} \
    -o jsonpath='{.items[0].status.containerStatuses[0].imageID}' && echo
done
```

This will produce output similar to the following:

```plaintext
registry.redhat.io/redhat/community-operator-index@sha256:7e2eca1a...
registry.redhat.io/redhat/redhat-operator-index@sha256:17e179ef...
registry.redhat.io/redhat/certified-operator-index@sha256:1df4aaf5...
```

###### Step 2: Update CatalogSource Resources

For each CatalogSource, update the resource to use the digest and remove automatic polling.

**Before (Dynamic):**
```yaml
spec:
  image: registry.redhat.io/redhat/community-operator-index:v4.18
  updateStrategy:
    registryPoll:
      interval: 10m
```

**After (Static):**
```yaml
spec:
  image: registry.redhat.io/redhat/community-operator-index@sha256:xxxxxxxx
  # updateStrategy section completely removed – no automatic polling
```

You can update the CatalogSource using:
```bash
oc edit catalogsource community-operators -n openshift-marketplace
```

###### Step 3: Document Your Configuration
Create a comprehensive configuration document that includes:

- **Date of pinning**: When the static configuration was implemented
- **All four pinned versions**:
  - OpenShift version (e.g., `4.18.3`)
  - Red Hat catalog digests (all catalogs with full SHA256)
  - IBM MAS catalog version (e.g., `@@MAS_LATEST_CATALOG@@`)
  - MAS CLI version (e.g., `@@CLI_LATEST_VERSION@@`)
- **Reason for pinning**: Business justification and requirements
- **Planned review date**: When the configuration will be reviewed for updates
- **Responsible contact**: Person or team responsible for maintenance
- **Exact installation command**: The complete `mas install` command used

Store this documentation in your configuration management system and update it whenever changes are made.

##### Important Security and Support Considerations

###### Security Exposure Timeline

| Time Since Pinning | Risk Level | Recommended Action |
|--------------------|------------|-------------------|
| 0-3 months | Low | Monitor security advisories |
| 3-6 months | Medium | Plan update window |
| 6-12 months | High | Update strongly recommended |
| 12+ months | Critical | Update immediately |

###### Security Implications

- Installing older versions of Maximo Application Suite, or not applying updates for extended periods of time means you are not receiving important security updates.
- You must maintain your own security scanning and vulnerability monitoring processes.
- Security patches and fixes released after your pinned versions will not be automatically applied.

###### IBM Support Implications

- IBM Support may require you to reproduce issues on current versions.
- IBM cannot accept liability for security incidents that occur in environments that do not have the latest updates.
- Support for older versions may be limited depending on the age of the pinned components.

###### Compliance Considerations

- Some compliance frameworks (e.g., PCI-DSS, HIPAA) require current security patches and may not permit extended use of outdated software.
- Document your risk acceptance decision with your compliance and security teams.
- Maintain evidence of security monitoring and compensating controls.
- If you choose to adopt low-frequency updates, you accept full responsibility for the security posture of your environment.

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
To set up Red Hat Operator, Community, and Certified catalogs with IDMS, run the below command. (Needed to install DRO and Grafana operators)
```bash
docker run -ti --pull always quay.io/ibmmas/cli mas configure-airgap --setup-redhat-catalogs
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
Regardless of whether you are running a connected or disconnected installation, simply run the `mas install` command and follow the prompts, the basic structure of the interactive flow is described below.  We will need the `entitlement.lic` file to perform the installation so we will mount your home directory into the running container.  When prompted you will be able to set license file to `/mnt/home/entitlement.lic`

!!! note "NEW: AI Service Installation Options"
    **NEW UPDATE:** AI Service can now be installed in two ways:

    - **Integrated Installation**: AI Service is now available as an option during the MAS installation process using the `mas install` command. You can select AI Service along with other MAS applications during the interactive application selection step or you can run Non-interactive command as well.
    - **Standalone Installation**: For standalone AI Service installation, use the dedicated `mas aiservice-install` command to install AI Service independently of the main MAS installation.

```bash
docker run -ti --rm -v ~:/mnt/home quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas install
```

The interactive install will guide you through a series of questioned designed to help you arrive at the best configuration for your scenario, it can be broken down as below:

<div>
  <cds-accordion>
    <cds-accordion-item title="Connect to OpenShift and Choose a Catalog">
      <p>If you are not already connected to an OpenShift cluster you will be prompted to provide the server URL & token to make a new connection.  If you are already connected to a cluster you will be given the option to change to another cluster</p>
      <p>You will be presented with a table of available catalogs with information about the different releases of MAS available in each</p>
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
    <cds-accordion-item title="Configure your MAS Instance">
      <p>Provide the basic information about your MAS instance:</p>
      <ul>
        <li>Instance ID</li>
        <li>Workspace ID</li>
        <li>Workspace Display Name</li>
        <li>Operational Mode (production or non-production)</li>
      </ul>
    </cds-accordion-item>
    <cds-accordion-item title="Configure Domain & Certificate Management">
      <p>By default MAS will be installed in a subdomain of your OpenShift clusters domain matching the MAS instance ID that you chose.  For example if your OpenShift cluster is <code>myocp.net</code> and you are installing MAS with an instance ID of <code>prod1</code> then MAS will be installed with a default domain something like <code>prod1.apps.myocp.net</code>, depending on the exact network configuration of your cluster.</p>
      <p>If you wish to use a custom domain for the MAS install you can choose to configure this by selecting "n" at the prompt.  The install supports DNS integrations for Cloudflare, IBM Cloud Internet Services, AWS Route 53 out of the box and is able to configure a certificate issuer using LetsEncrypt (production or staging) or a self-signed certificate authority per your choices.</p>
    </cds-accordion-item>
    <cds-accordion-item title="Advanced Settings">
      <p>You will also be able to configure the following advanced settings:</p>
      <ul>
        <li>Single Sign-On (SSO)</li>
        <li>Whether to allow special character in User IDs and Usernames</li>
        <li>Whether Guided Tours are enabled</li>
        <li>Network Routing Mode (path or subdomain)</li>
      </ul>
      <h4>Routing Mode</h4>
      <p>Starting from MAS 9.2.0, you can configure how Maximo Application Suite is accessed through URLs:</p>
      <ul>
        <li><strong>Path Mode (single domain):</strong> All applications are accessed through a single domain with different paths (e.g., <code>mas.example.com/manage</code>, <code>mas.example.com/admin</code>)</li>
        <li><strong>Subdomain Mode (multi domain):</strong> Each application is accessed through its own subdomain (e.g., <code>manage.mas.example.com</code>, <code>admin.mas.example.com</code>)</li>
      </ul>
      <p><strong>Path-Based Routing Requirements:</strong> When using path mode, the OpenShift IngressController must be configured with <code>namespaceOwnership: InterNamespaceAllowed</code>. The CLI will validate the configuration and offer to configure it automatically if needed. <code>--ingress-controller-name</code> and <code>--configure-ingress</code> both applicable only for <code>--routing path</code>. If <code>--configure-ingress</code> not specified and the IngressController is not configured, the installation will fail with instructions.</p>
      <p><strong>Note:</strong> <code>--ingress-controller-name</code> specifies the name of the OpenShift <code>IngressController</code> resource to use for path-based routing. The <code>IngressController</code> is an OpenShift resource (in the <code>openshift-ingress-operator</code> namespace) that manages how external traffic is routed into the cluster. Defaults to <code>default</code> if not specified.</p>
    </cds-accordion-item>
    <cds-accordion-item title="Application Selection">
      <p>Select the applications that you would like to install. Note that some applications cannot be installed unless an application they depend on is also installed:</p>
      <ul>
        <li><strong>Version-based dependencies:</strong>
          <ul>
            <li><strong>Monitor < 9.2.0:</strong> Monitor depends on IoT (IoT must be installed first)</li>
            <li><strong>Monitor >= 9.2.0:</strong> IoT depends on Monitor (Monitor must be installed first)</li>
          </ul>
        </li>
        <li>Assist and Predict are only available for install if Monitor is selected</li>
        <li>From MAS 9.1 onwards, Assist will be rebranded as Collaborate in the MAS UI. It will still appear as Assist in the MAS CLI and within the OpenShift Cluster, but from the MAS UI it will appear as Collaborate.</li>
        <li><strong>NEW UPDATE:</strong> AI Service is now available as an installation option during the application selection step.</li>
      </ul>
    </cds-accordion-item>
    <cds-accordion-item title="Application Configuration">
      <p>Some Maximo applications support additional configuration, you will be taken through the configuration options for each application that you chose to install.</p>
      <h4>NEW UPDATE: Maximo Manage - AI Service Binding</h4>
      <p><strong>NEW UPDATE:</strong> When installing Maximo Manage, you can optionally bind it to an AI Service Tenant. This integration enables AI capabilities within Manage through the AI Config Application.</p>
      <ul>
        <li><strong>Installing AI Service with Manage:</strong> If you select AI Service during the application selection step (using <code>--aiservice-channel</code>), the binding is configured automatically:
          <ul>
            <li>A default tenant ID "user" is automatically created and bound to Manage</li>
            <li>The AI Service instance being installed is automatically used for the binding</li>
            <li>No additional configuration is required - the binding parameters are set automatically</li>
            <li><strong>Important:</strong> When AI Service is being installed, any <code>--manage-aiservice-instance-id</code> or <code>--manage-aiservice-tenant-id</code> parameters provided will be ignored, as the binding is automatically configured</li>
          </ul>
        </li>
        <li><strong>Using Existing AI Service:</strong> If AI Service is already installed in your cluster (not using <code>--aiservice-channel</code>), you can bind Manage to an existing AI Service tenant:
          <ul>
            <li><strong>Interactive Mode:</strong> You will be prompted to select from available AI Service instances and tenants</li>
            <li><strong>Non-Interactive Mode:</strong> Use <code>--manage-aiservice-instance-id</code> and <code>--manage-aiservice-tenant-id</code> parameters to specify the binding</li>
          </ul>
        </li>
      </ul>
    </cds-accordion-item>
    <cds-accordion-item title="Configure Databases">
      <p>The install supports the automatic provision of in-cluster MongoDb and Db2 databases for use with Maximo Application Suite, you may also choose to bring your own (BYO) by providing the necessary configuration files (which the installer will also help you create).</p>
    </cds-accordion-item>
    <cds-accordion-item title="Configure Integrations & Additional Configuration">
      <p>The install supports the abilty to install and configure the Grafana Community Operator.  Additional resource definitions can be applied to the OpenShift Cluster during the MAS configuration step, here you will be asked whether you wish to provide any additional configurations and if you do in what directory they reside.</p>
      <p>If you provided one or more configurations for BYO databases then additional configurations will already be enabled and pointing at the directory you chose earlier.</p>
    </cds-accordion-item>
    <cds-accordion-item title="Pod Templates">
      <p>You can choose between three pre-defined pod templates allowing you to configure MAS in each of the standard Kubernetes quality of service (QoS) levels: Burstable, <a href="https://github.com/ibm-mas/cli/blob/master/image/cli/mascli/templates/pod-templates/best-effort">BestEffort</a> and <a href="https://github.com/ibm-mas/cli/blob/master/image/cli/mascli/templates/pod-templates/guaranteed">Guaranteed. By default MAS applications are deployed with a Burstable QoS.</p>
      <p>Additionally, you may provide your own custom pod templates definition by providing the directory containing your configuration files. More information on podTemplates can be found in the <a href="https://www.ibm.com/docs/en/mas-cd/continuous-delivery?topic=configuring-customizing-workloads">product documentation</a>.  Note that pod templating support is only available from IBM Maximo Application Suite v8.11 onwards</p>
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


How It Works
-------------------------------------------------------------------------------
The engine that performs all tasks is written in Ansible, you can directly use the same automation outside of this CLI if you wish.  The code is open source and available in [ibm-mas/ansible-devops](https://github.com/ibm-mas/ansible-devops), the collection is also available to install directly from [Ansible Galaxy](https://galaxy.ansible.com/ibm/mas_devops), the install supports the following actions:

- IBM Maximo Operator Catalog installation
- Required dependency installation:
    - MongoDb (Community Edition)
    - IBM Suite License Service
    - IBM Data Reporter Operator
    - Red Hat Certificate Manager
- Optional dependency installation:
    - Apache Kafka
    - IBM Maximo AI Service
    - IBM Db2
    - IBM Cloud Pak for Data Platform and Services
        - Watson Studio Local
        - Watson Machine Learning
        - Analytics Engine (Apache Spark)
        - Cognos Analytics
    - Grafana
- Suite core services installation
- Suite application installation

The installation is performed inside your RedHat OpenShift cluster utilizing [Openshift Pipelines](https://cloud.redhat.com/learn/topics/ci-cd)

> OpenShift Pipelines is a Kubernetes-native CI/CD solution based on Tekton. It builds on Tekton to provide a CI/CD experience through tight integration with OpenShift and Red Hat developer tools. OpenShift Pipelines is designed to run each step of the CI/CD pipeline in its own container, allowing each step to scale independently to meet the demands of the pipeline.
