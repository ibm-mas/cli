AI Service Installation
===============================================================================
Usage
-------------------------------------------------------------------------------
For full usage information run `mas aiservice-install --help`

The `mas aiservice-install` command is specifically designed for standalone installation of AI Service version 9.1.x or above. This command provides a streamlined installation process focused solely on AI Service and its dependencies.

!!! note "AI Service Installation Options"
    - **Standalone Installation (9.1.x+)**: Use `mas aiservice-install` for dedicated AI Service installation
    - **Integrated Installation**: AI Service can also be installed alongside MAS applications using `mas install` command

Preparation
-------------------------------------------------------------------------------
### IBM Entitlement Key
Access [Container Software Library](https://myibm.ibm.com/products-services/containerlibrary) using your IBMId to obtain your entitlement key.

### MAS License File
Access [IBM License Key Center](https://licensing.flexnetoperations.com/), on the **Get Keys** menu select **IBM AppPoint Suites**. Select `IBM MAXIMO APPLICATION SUITE AppPOINT LIC` and on the next page fill in the information as below:

| Field            | Content                                                                       |
| ---------------- | ----------------------------------------------------------------------------- |
| Number of Keys   | How many AppPoints to assign to the license file                              |
| Host ID Type     | Set to **Ethernet Address**                                                   |
| Host ID          | Enter any 12 digit hexadecimal string                                         |
| Hostname         | Set to the hostname of your OCP instance, but this can be any value really.   |
| Port             | Set to **27000**                                                              |

The other values can be left at their defaults. Finally, click **Generate** and download the license file to your home directory as `entitlement.lic`.

!!! note
    The license file is only required if IBM Suite License Service (SLS) has not been previously installed in your cluster. If SLS is already configured, you can skip the license file configuration.

### OpenShift Cluster
You should already have a target OpenShift cluster ready to install AI Service into. If you do not already have one then refer to the [OpenShift Container Platform installation overview](https://docs.openshift.com/container-platform/4.15/installing/index.html).

The CLI also supports OpenShift provisioning in many hyperscaler providers:

- [AWS](../commands/provision-rosa.md)
- [IBM Cloud](../commands/provision-roks.md)
- [IBM DevIT FYRE (Internal)](../commands/provision-fyre.md)

### Operator Catalog Selection
If you have not already determined the catalog version for your installation, refer to the information in the [Operator Catalog](../catalogs/index.md) topic, or contact IBM Support for guidance.


Interactive Install
-------------------------------------------------------------------------------
Run the `mas aiservice-install` command and follow the interactive prompts. Mount your home directory to access the license file when needed.

```bash
docker run -ti --rm -v ~:/mnt/home quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ mas aiservice-install
```

The interactive install will guide you through the following steps:

<div>
  <cds-accordion>
    <cds-accordion-item title="Connect to OpenShift and Choose a Catalog">
      <p>If you are not already connected to an OpenShift cluster you will be prompted to provide the server URL & token to make a new connection. If you are already connected to a cluster you will be given the option to change to another cluster.</p>
      <p>You will be presented with a table of available catalogs with information about the different releases of MAS available in each.</p>
      <p>Confirm that you accept the IBM Maximo Application Suite license terms.</p>
    </cds-accordion-item>
    <cds-accordion-item title="Select Storage Classes">
      <p>AI Service requires both a `ReadWriteMany` and a `ReadWriteOnce` capable storage class to be available in the cluster. The installer has the ability to recognize certain storage class providers and will default to the most appropriate storage class in these cases:</p>
      <ul>
        <li>IBMCloud Storage (ibmc-block-gold & ibmc-file-gold-gid)</li>
        <li>OpenShift Container Storage (ocs-storagecluster-ceph-rbd & ocs-storagecluster-cephfs)</li>
        <li>External OpenShift Container Storage (ocs-external-storagecluster-ceph-rbd & ocs-external-storagecluster-cephfs)</li>
        <li>NFS Client (nfs-client)</li>
        <li>Azure Managed Storage (managed-premium & azurefiles-premium)</li>
        <li>AWS Storage (gp3-cs & efs)</li>
      </ul>
      <p>The names in brackets represent the `ReadWriteOnce` and `ReadWriteMany` class that will be used. Even when a recognized storage provider is detected you will be provided with the option to select your own storage classes if you wish.</p>
    </cds-accordion-item>
    <cds-accordion-item title="Provide a License File and Entitlement Key">
      <p>Provide the location of your license file (e.g., `/mnt/home/entitlement.lic`), contact information, and IBM entitlement key. If you have set the <code>IBM_ENTITLEMENT_KEY</code> environment variable, this field will be pre-filled.</p>
      <p><strong>Note:</strong> This step is only required if IBM Suite License Service (SLS) has not been previously installed in your cluster.</p>
    </cds-accordion-item>
    <cds-accordion-item title="Configure AI Service Instance">
      <p>Provide the configuration details for your AI Service instance:</p>
      <ul>
        <li><strong>Instance ID:</strong> Unique identifier for your AI Service instance</li>
        <li><strong>Channel:</strong> AI Service version channel (e.g., 9.1.x)</li>
        <li><strong>S3 Storage Configuration:</strong> Configure object storage for AI Service data</li>
        <li><strong>Database Configuration:</strong> Set up database connection for AI Service</li>
        <li><strong>RSL Configuration:</strong> Configure Red Hat Service Locator integration</li>
        <li><strong>Tenant Configuration:</strong> Set up AI Service tenant(s)</li>
        <li><strong>Operational Mode:</strong> Choose between production or non-production mode</li>
      </ul>
    </cds-accordion-item>
    <cds-accordion-item title="Configure Dependencies">
      <p>Choose how to configure AI Service dependencies:</p>
      <ul>
        <li><strong>IBM Suite License Service (SLS):</strong> Install new instance or use existing SLS</li>
        <li><strong>Database (Db2):</strong> Install in-cluster Db2 or provide connection to existing database</li>
        <li><strong>IBM Data Reporter Operator (DRO):</strong> Install DRO or provide alternative configuration</li>
        <li><strong>MinIO:</strong> Configure object storage for AI Service</li>
      </ul>
      <p>For each dependency, you can choose to install it automatically or provide connection details to an existing instance.</p>
    </cds-accordion-item>
    <cds-accordion-item title="Review Choices">
      <p>Before the install starts, you will be presented with a summary of all your choices and a non-interactive command that will allow you to repeat the same installation without going through all the prompts again.</p>
    </cds-accordion-item>
  </cds-accordion>
</div>


Non-Interactive Install
-------------------------------------------------------------------------------
The following command demonstrates a complete AI Service installation with all configuration options. This command will launch the MAS CLI container image, login to your OpenShift Cluster and start the AI Service installation without triggering any prompts.

```bash
IBM_ENTITLEMENT_KEY=your_entitlement_key_here

docker run -e IBM_ENTITLEMENT_KEY -ti --rm -v ~:/mnt/home quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ bash -c "
  oc login --token=sha256~xxxx --server=https://xxx &&
  mas aiservice-install \
    --mas-catalog-version @@MAS_LATEST_CATALOG@@ \
    --ibm-entitlement-key \${IBM_ENTITLEMENT_KEY} \
    --aiservice-instance-id aiservice1 \
    --aiservice-channel 9.1.x \
    \
    --storage-class-rwo nfs-client \
    --storage-class-rwx nfs-client \
    --storage-pipeline nfs-client \
    --storage-accessmode ReadWriteMany \
    \
    --license-file /mnt/home/entitlement.lic \
    --uds-email admin@example.com \
    --uds-firstname John \
    --uds-lastname Doe \
    \
    --dro-namespace redhat-marketplace \
    --mongodb-namespace mongoce \
    \
    --s3-tenants-bucket km-tenants \
    --s3-templates-bucket km-templates \
    \
    --odh-model-deployment-type serverless \
    \
    --watsonxai-apikey your_watsonx_api_key \
    --watsonxai-url https://us-south.ml.cloud.ibm.com \
    --watsonxai-project-id your_project_id \
    \
    --install-minio
    --minio-root-user minio \
    --minio-root-password minio123 \
    \
    --tenant-entitlement-type standard \
    --tenant-entitlement-start-date 2025-01-01 \
    --tenant-entitlement-end-date 2026-01-01 \
    \
    --rsl-url http://your-rsl-host:3001/api/v3/vector/query \
    --rsl-org-id your_org_id \
    --rsl-token 'Bearer your_rsl_token' \
    \
    --accept-license --no-confirm
"
```

### Core Parameters

| Parameter | Description | Required | Example |
|-----------|-------------|----------|---------|
| `--mas-catalog-version` | MAS operator catalog version | Yes | `v9-250902-amd64` |
| `--aiservice-instance-id` | Unique identifier for AI Service instance | Yes | `aiservice1` |
| `--aiservice-channel` | AI Service version channel | Yes | `9.1.x` |
| `--ibm-entitlement-key` | IBM Container Registry entitlement key | Yes | `$IBM_ENTITLEMENT_KEY` |

### Storage Configuration

| Parameter | Description | Required | Example |
|-----------|-------------|----------|---------|
| `--storage-class-rwo` | ReadWriteOnce storage class | Yes | `nfs-client` |
| `--storage-class-rwx` | ReadWriteMany storage class | Yes | `nfs-client` |
| `--storage-pipeline` | Storage class for pipeline workloads | Yes | `nfs-client` |
| `--storage-accessmode` | Storage access mode | Yes | `ReadWriteMany` |

### License and Contact Information

| Parameter | Description | Required | Example |
|-----------|-------------|----------|---------|
| `--license-file` | Path to MAS license file (required if SLS not installed) | Conditional | `/mnt/home/entitlement.lic` |
| `--uds-email` | Contact email address | Yes | `admin@example.com` |
| `--uds-firstname` | Contact first name | Yes | `John` |
| `--uds-lastname` | Contact last name | Yes | `Doe` |

### Dependency Configuration

| Parameter | Description | Required | Example |
|-----------|-------------|----------|---------|
| `--dro-namespace` | IBM Data Reporter Operator namespace | Optional | `redhat-marketplace` |
| `--mongodb-namespace` | MongoDB namespace (for SLS) | Optional | `mongoce` |

### S3 Storage Configuration

| Parameter | Description | Required | Example |
|-----------|-------------|----------|---------|
| `--s3-accesskey` | S3 access key | Yes | `minio` |
| `--s3-secretkey` | S3 secret key | Yes | `minio123` |
| `--s3-host` | S3 service host | Yes | `minio-service.minio.svc.cluster.local` |
| `--s3-port` | S3 service port | Yes | `9000` |
| `--s3-ssl` | Enable SSL for S3 connection | Yes | `false` |
| `--s3-region` | S3 region | Yes | `none` |
| `--s3-bucket-prefix` | Prefix for S3 buckets | Yes | `s3-` |
| `--s3-tenants-bucket` | S3 bucket for tenant data | Yes | `km-tenants` |
| `--s3-templates-bucket` | S3 bucket for templates | Yes | `km-templates` |

### OpenDataHub Configuration

| Parameter | Description | Required | Example |
|-----------|-------------|----------|---------|
| `--odh-model-deployment-type` | Model deployment type (serverless/raw) | Yes | `serverless` |

### Watson AI Configuration

| Parameter | Description | Required | Example |
|-----------|-------------|----------|---------|
| `--watsonxai-apikey` | Watson AI API key | Optional | `your_api_key` |
| `--watsonxai-url` | Watson AI service URL | Optional | `https://us-south.ml.cloud.ibm.com` |
| `--watsonxai-project-id` | Watson AI project ID | Optional | `your_project_id` |

### MinIO Configuration

| Parameter | Description | Required | Example |
|-----------|-------------|----------|---------|
| `--minio-root-user` | MinIO root username | Yes | `minio` |
| `--minio-root-password` | MinIO root password | Yes | `minio123` |

### Tenant Configuration

| Parameter | Description | Required | Example |
|-----------|-------------|----------|---------|
| `--tenant-entitlement-type` | Tenant entitlement type | Yes | `standard` |
| `--tenant-entitlement-start-date` | Entitlement start date (YYYY-MM-DD) | Yes | `2025-01-01` |
| `--tenant-entitlement-end-date` | Entitlement end date (YYYY-MM-DD) | Yes | `2026-01-01` |

### RSL (Red Hat Service Locator) Configuration

| Parameter | Description | Required | Example |
|-----------|-------------|----------|---------|
| `--rsl-url` | RSL service URL | Optional | `http://host:3001/api/v3/vector/query` |
| `--rsl-org-id` | RSL organization ID | Optional | `your_org_id` |
| `--rsl-token` | RSL authentication token | Optional | `Bearer your_token` |

### Additional Options

| Parameter | Description | Required |
|-----------|-------------|----------|
| `--accept-license` | Accept license terms | Yes |
| `--no-confirm` | Skip confirmation prompts | Optional |


Dependencies
-------------------------------------------------------------------------------
The AI Service installation automatically handles the following dependencies:

### Required Dependencies
- **IBM Suite License Service (SLS)**: Manages licensing for AI Service. Automatically installed if not present, or can use existing SLS instance.
- **IBM Data Reporter Operator (DRO)**: Handles data reporting and metrics
- **Red Hat Certificate Manager**: Manages TLS certificates
- **MinIO**: Provides S3-compatible object storage for AI Service data
- **Db2**: Database for AI Service metadata and configuration

### Optional Dependencies
- **MongoDB Community Edition**: Only required if installing SLS for the first time


More Information
-------------------------------------------------------------------------------
The AI Service installation is designed to work on any OCP cluster, but has been specifically tested in these environments:

- IBMCloud ROKS
- Microsoft Azure
- AWS ROSA
- IBM DevIT FYRE (internal)

The engine that performs all tasks is written in Ansible. The code is open source and available in [ibm-mas/ansible-devops](https://github.com/ibm-mas/ansible-devops), and the collection is also available to install directly from [Ansible Galaxy](https://galaxy.ansible.com/ibm/mas_devops).

The installation is performed inside your RedHat OpenShift cluster utilizing [OpenShift Pipelines](https://cloud.redhat.com/learn/topics/ci-cd):

> OpenShift Pipelines is a Kubernetes-native CI/CD solution based on Tekton. It builds on Tekton to provide a CI/CD experience through tight integration with OpenShift and Red Hat developer tools. OpenShift Pipelines is designed to run each step of the CI/CD pipeline in its own container, allowing each step to scale independently to meet the demands of the pipeline.


Integration with Maximo Manage
-------------------------------------------------------------------------------
After installing AI Service, you can bind it to Maximo Manage to enable AI capabilities:

**During Manage Installation:**

When installing Manage alongside AI Service using `mas install`:

- **Installing AI Service with Manage** (using `--aiservice-channel`):
  - The binding is configured automatically with default "user" tenant
  - No additional parameters needed
  - Any `--manage-aiservice-instance-id` or `--manage-aiservice-tenant-id` parameters will be ignored

- **Using Existing AI Service** (not using `--aiservice-channel`):
  - **Interactive Mode**: You will be prompted to select the AI Service instance and tenant
  - **Non-Interactive Mode**: Use `--manage-aiservice-instance-id` and `--manage-aiservice-tenant-id` parameters

**Post-Installation:**

You can configure the AI Service binding through the Maximo Manage UI.

For more information on integrating AI Service with Manage, see the [Installation Guide](install.md#application-configuration).