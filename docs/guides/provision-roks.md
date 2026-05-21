Provision OpenShift on IBM Cloud ROKS
===============================================================================

Overview
-------------------------------------------------------------------------------
The MAS CLI provides automated provisioning of Red Hat OpenShift Kubernetes Service (ROKS) clusters on IBM Cloud. ROKS is IBM's managed OpenShift offering that provides enterprise-grade Kubernetes with integrated IBM Cloud services, automated updates, and built-in security features.

This guide covers the complete process of provisioning an OpenShift cluster on IBM Cloud ROKS, from obtaining credentials to configuring worker nodes and optional GPU support.

!!! tip
    ROKS clusters are ideal for production deployments with IBM Cloud integration, managed services, and enterprise support.


Preparation
-------------------------------------------------------------------------------

### IBM Cloud Account
You must have an active IBM Cloud account with appropriate permissions. To get started:

1. Create an account at [IBM Cloud](https://cloud.ibm.com)
2. Ensure you have access to create Kubernetes/OpenShift clusters
3. Verify billing is configured for your account

### IBM Cloud API Key
Generate an API key for authentication:

1. Log in to [IBM Cloud](https://cloud.ibm.com)
2. Navigate to **Manage** → **Access (IAM)** → **API keys**
3. Click **Create an IBM Cloud API key**
4. Provide a name and description
5. Copy and securely store the API key (it will only be shown once)

!!! warning
    Treat your API key as a password. Never commit it to source control or share it publicly.

### Resource Group
IBM Cloud uses resource groups to organize and manage resources. You will need:

- **Resource Group Name** - The name of an existing resource group (e.g., `Default`, `mas-development`)
- **Permissions** - Ensure you have Editor or Administrator role on the resource group

To view available resource groups:
```bash
ibmcloud resource groups
```

### OpenShift Version Selection
Choose an OpenShift version supported by both ROKS and your target MAS version. ROKS versions use the format `X.Y_openshift`.  Refer to the [MAS system requirements](https://www.ibm.com/docs/en/mas-cd/continuous-delivery) for version compatibility.


Cluster Configuration
-------------------------------------------------------------------------------
### Worker Node Flavors
ROKS offers various worker node flavors optimized for different workloads.  MAS requires a minimum of 3 worker nodes for high availability. We do not recommend running MAS with worker nodes smaller than 8 vCPUs and 32 GB memory.

To view all available flavors:
```bash
ibmcloud ks flavors --zone <zone>
```

### GPU Support (Optional)
ROKS supports GPU-enabled worker nodes for AI/ML workloads. GPU configuration includes:

- **GPU Worker Count** - Number of GPU-enabled workers
- **GPU Workerpool Name** - Identifier for the GPU worker pool
- **GPU Flavor** - GPU-enabled worker flavor (e.g., `gx2.16x128.1v100`)

!!! tip
    GPU workers are only required for MAS applications with AI/ML capabilities like Predict or Visual Inspection.


Provisioning Modes
-------------------------------------------------------------------------------

### Interactive Mode
Interactive mode guides you through the provisioning process with prompts for all configuration options.

```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas provision-roks
```

The interactive session will:

1. Prompt for IBM Cloud API key
2. Request resource group and cluster name
3. Configure OpenShift version
4. Set worker node specifications
5. Optionally configure GPU workers
6. Display a summary and request confirmation

### Non-Interactive Mode
Non-interactive mode is ideal for automation and CI/CD pipelines. All required parameters must be provided via command-line arguments or environment variables.

```bash
export IBMCLOUD_APIKEY=your-api-key

docker run -ti --rm --pull always quay.io/ibmmas/cli mas provision-roks \
  -a $IBMCLOUD_APIKEY \
  -r mas-development \
  -c mas-prod-cluster \
  -v 4.15_openshift \
  --worker-count 3 \
  --worker-flavor b3c.16x64 \
  --worker-zone dal10 \
  --no-confirm
```

Command Reference
-------------------------------------------------------------------------------

### IBM Cloud Credentials
- `-a, --apikey IBMCLOUD_APIKEY` - IBM Cloud API key (required)

### Cluster Configuration
- `-r, --resource-group IBMCLOUD_RESOURCEGROUP` - IBM Cloud resource group (required)
- `-c, --cluster-name CLUSTER_NAME` - Cluster name (required)
- `-v, --ocp-version OCP_VERSION` - OpenShift version, e.g., `4.15_openshift` (required)

### Worker Node Configuration
- `--worker-count ROKS_WORKERS` - Number of worker nodes (default: 3)
- `--worker-flavor ROKS_FLAVOR` - Worker node flavor, e.g., `b3c.16x64` (required)
- `--worker-zone ROKS_ZONE` - IBM Cloud zone, e.g., `dal10` (required)

### GPU Configuration
- `--gpu-worker-count GPU_WORKERS` - Number of GPU worker nodes (optional)
- `--gpu-workerpool-name GPU_WORKERPOOL_NAME` - GPU workerpool name (optional)

### Other Options
- `--no-confirm` - Skip confirmation prompt
- `-h, --help` - Display help message


Post-Provisioning Steps
-------------------------------------------------------------------------------

### Accessing Your Cluster
After provisioning completes, access your cluster through the IBM Cloud console or CLI.

#### Using IBM Cloud Console
1. Navigate to [IBM Cloud Kubernetes Service](https://cloud.ibm.com/kubernetes/clusters)
2. Select your cluster
3. Click **OpenShift web console** to access the cluster

#### Using IBM Cloud CLI
```bash
# Log in to IBM Cloud
ibmcloud login --apikey $IBMCLOUD_APIKEY

# Set target resource group
ibmcloud target -g mas-production

# Get cluster configuration
ibmcloud ks cluster config --cluster mas-prod-cluster

# Verify connection
oc get nodes
```

### Verifying Cluster Health
Check that all nodes are ready:

```bash
oc get nodes
```

Verify storage classes are available:

```bash
oc get storageclass
```

Expected storage classes on ROKS:

- `ibmc-block-gold` - Block storage (RWO)
- `ibmc-file-gold` - File storage (RWX)
- `ibmc-file-gold-gid` - File storage with GID support

### Configuring Cluster Access
Set up cluster access for your team:

1. **IAM Policies** - Configure IBM Cloud IAM for user access
2. **RBAC** - Set up Kubernetes RBAC for fine-grained permissions
3. **Service IDs** - Create service IDs for automation

### Next Steps
With your ROKS cluster provisioned, you can proceed to:

- [Install MAS](install.md)
- Configure IBM Cloud services integration
- Set up monitoring and logging
- Configure backup and disaster recovery

!!! warning "ROKS Limitations"
    ROKS clusters do not support `ImageDigestMirrorSet` resources, which limits airgap/image mirroring capabilities. For airgap installations, consider using other OpenShift deployment options.
