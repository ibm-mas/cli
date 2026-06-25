Provision OpenShift on IBM DevIT FYRE
===============================================================================

!!! warning "Internal IBM Use Only"
    FYRE (Functional Verification Environment) is an internal IBM development and testing platform. This guide is intended for IBM employees and authorized users only.

Overview
-------------------------------------------------------------------------------
The MAS CLI provides automated provisioning of OpenShift Container Platform clusters on IBM's internal FYRE infrastructure. FYRE offers rapid cluster deployment for development, testing, and demonstration purposes with flexible resource allocation and quota management.

This guide covers the complete process of provisioning an OpenShift cluster on FYRE, from obtaining credentials to configuring storage providers.

!!! tip
    FYRE clusters are ideal for short-term development and testing. For production deployments, use supported cloud providers like AWS, Azure, or IBM Cloud.


Preparation
-------------------------------------------------------------------------------

### FYRE Account and Credentials
You must have an active FYRE account with appropriate quota allocation. To obtain FYRE credentials:

1. Access the [FYRE Portal](https://fyre.ibm.com)
2. Log in with your IBM credentials
3. Navigate to **Account Settings** to retrieve your API key
4. Note your username and API key for use with the CLI

### Product Group and Quota
FYRE uses product groups to organize and allocate resources. You will need:

- **Product Group ID** - The numeric identifier for your product group
- **Quota Type** - Either `quick_burn` (temporary, time-limited) or `product_group` (allocated quota)

Contact your FYRE administrator if you need assistance with product group access or quota allocation.

### OpenShift Version Selection
Choose an OpenShift version supported by both FYRE and your target MAS version.  Refer to the [MAS system requirements](https://www.ibm.com/docs/en/mas-cd/continuous-delivery) for version compatibility.


Cluster Configuration
-------------------------------------------------------------------------------

### Cluster Naming
Cluster names must:

- Use lowercase letters only
- Be unique within your FYRE account
- Be descriptive for easy identification
- Follow your organization's naming conventions

Example: `mas-dev-cluster`, `test-env-01`

### Worker Node Sizing
Configure worker nodes based on your workload requirements:

| Configuration | CPU | Memory | Use Case |
|---------------|-----|--------|----------|
| **Small** | 4 | 16 GB | Development, testing |
| **Medium** | 8 | 32 GB | Standard MAS installation |
| **Large** | 16 | 64 GB | Production-like environments |

!!! note
    MAS requires a minimum of 3 worker nodes for high availability. Each worker should have at least 8 CPUs and 32 GB memory for production-like installations.

### Additional Storage Disks
FYRE allows attaching additional disks to worker nodes for storage providers like ODF or Longhorn. Specify disk sizes as a comma-separated list:

- `200,200` - Two 200 GB disks per worker
- `500` - One 500 GB disk per worker

Additional disks are required when using ODF (OpenShift Data Foundation) for persistent storage.

### Storage Provider Options
The CLI can automatically configure storage providers:

- **NFS** - Network File System, simple and fast setup
- **ODF** - OpenShift Data Foundation, production-grade storage
- **Longhorn** - Cloud-native distributed storage

!!! tip
    For development and testing, NFS provides the fastest setup. For production-like environments, use ODF.


Provisioning Modes
-------------------------------------------------------------------------------

### Interactive Mode
Interactive mode guides you through the provisioning process with prompts for all configuration options.

```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas provision-fyre
```

The interactive session will:

1. Prompt for FYRE credentials
2. Request cluster configuration details
3. Configure worker node specifications
4. Optionally configure storage provider
5. Display a summary and request confirmation

### Non-Interactive Mode
Non-interactive mode is ideal for automation and scripting. All required parameters must be provided via command-line arguments or environment variables.

```bash
export FYRE_USERNAME=your-username
export FYRE_APIKEY=your-api-key

docker run -ti --rm --pull always quay.io/ibmmas/cli mas provision-fyre \
  -u $FYRE_USERNAME \
  -a $FYRE_APIKEY \
  -p 225 \
  -q product_group \
  -c mas-dev-cluster \
  -d "MAS Development Cluster" \
  -v 4.15 \
  --worker-count 3 \
  --worker-cpu 8 \
  --worker-memory 32 \
  --no-confirm
```


Configuration Examples
-------------------------------------------------------------------------------

### Basic Development Cluster
Minimal configuration for development and testing:

```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas provision-fyre \
  -u $FYRE_USERNAME \
  -a $FYRE_APIKEY \
  -p 225 \
  -q quick_burn \
  -c dev-cluster \
  -v 4.15 \
  --worker-count 3 \
  --worker-cpu 4 \
  --worker-memory 16 \
  --storage nfs \
  --no-confirm
```

### Standard MAS Installation Cluster
Recommended configuration for typical MAS installations:

```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas provision-fyre \
  -u $FYRE_USERNAME \
  -a $FYRE_APIKEY \
  -p 225 \
  -q product_group \
  -c mas-standard \
  -d "MAS Standard Installation" \
  -v 4.15 \
  --worker-count 3 \
  --worker-cpu 8 \
  --worker-memory 32 \
  --storage nfs \
  --nfs-image-registry-size 100 \
  --no-confirm
```

### Cluster with ODF Storage
Configuration with OpenShift Data Foundation for production-like storage:

```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas provision-fyre \
  -u $FYRE_USERNAME \
  -a $FYRE_APIKEY \
  -p 225 \
  -q product_group \
  -c mas-odf-cluster \
  -d "MAS Cluster with ODF" \
  -v 4.15 \
  --worker-count 3 \
  --worker-cpu 16 \
  --worker-memory 64 \
  --worker-additional-disks "200,200" \
  --storage odf \
  --no-confirm
```

### Large Cluster for Performance Testing
High-resource configuration for performance testing:

```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas provision-fyre \
  -u $FYRE_USERNAME \
  -a $FYRE_APIKEY \
  -p 225 \
  -q product_group \
  -c mas-perf-test \
  -d "MAS Performance Testing" \
  -v 4.15 \
  --worker-count 5 \
  --worker-cpu 16 \
  --worker-memory 64 \
  --worker-additional-disks "500,500" \
  --storage odf \
  --no-confirm
```


Command Reference
-------------------------------------------------------------------------------

### FYRE Credentials
- `-u, --username FYRE_USERNAME` - FYRE username (required)
- `-a, --apikey FYRE_APIKEY` - FYRE API key (required)

### Cluster Configuration
- `-p, --product-id FYRE_PRODUCT_ID` - FYRE product group ID (required)
- `-q, --quota-type FYRE_QUOTA_TYPE` - Quota type: `quick_burn` or `product_group` (required)
- `-c, --cluster-name CLUSTER_NAME` - Cluster name, lowercase only (required)
- `-v, --ocp-version OCP_VERSION` - OpenShift version, e.g., `4.14`, `4.15` (required)
- `-d, --description FYRE_DESCRIPTION` - Cluster description (optional)

### Worker Node Configuration
- `--worker-count FYRE_WORKER_COUNT` - Number of worker nodes (default: 3)
- `--worker-cpu FYRE_WORKER_CPU` - CPUs per worker node (default: 8)
- `--worker-memory FYRE_WORKER_MEMORY` - Memory per worker in GB (default: 32)
- `--worker-additional-disks FYRE_WORKER_ADDITIONAL_DISKS` - Comma-separated disk sizes in GB (optional)
- `--fyre-cluster-size FYRE_CLUSTER_SIZE` - Quick burn size: `medium` or `large` (optional)

### Storage Configuration
- `--storage` - Storage provider: `nfs`, `odf`, or `longhorn` (optional)
- `--nfs-image-registry-size FYRE_NFS_IMAGE_REGISTRY_SIZE` - NFS registry size in GB (default: 100)

### Other Options
- `--no-confirm` - Skip confirmation prompt
- `-h, --help` - Display help message


Post-Provisioning Steps
-------------------------------------------------------------------------------

### Accessing Your Cluster
After provisioning completes, the CLI will display:

1. **Cluster URL** - OpenShift console access URL
2. **Kubeadmin Credentials** - Initial admin username and password
3. **API Server URL** - For CLI access

Save these credentials securely.

### Connecting with oc CLI
```bash
oc login --server=https://api.your-cluster.fyre.ibm.com:6443 \
  --username=kubeadmin \
  --password=<provided-password>
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

### Next Steps
With your FYRE cluster provisioned, you can proceed to:

- [Install MAS](install.md)
- Configure additional cluster resources
- Set up monitoring and logging


Troubleshooting
-------------------------------------------------------------------------------

### Provisioning Failures

**Quota Exceeded**
```
Error: Insufficient quota available
```
- Verify your product group has available quota
- Contact your FYRE administrator to increase quota
- Use `quick_burn` quota for temporary clusters

**Invalid Cluster Name**
```
Error: Cluster name must be lowercase
```
- Ensure cluster name contains only lowercase letters, numbers, and hyphens
- Avoid uppercase letters and special characters

**Version Not Available**
```
Error: OpenShift version not supported
```
- Check available versions in the FYRE portal
- Use a supported version (typically 4.14, 4.15, or 4.16)

### Storage Configuration Issues

**NFS Registry Size Too Large**
```
Error: Requested size exceeds available storage
```
- Reduce `--nfs-image-registry-size` value
- Default 100 GB is usually sufficient

**ODF Requires Additional Disks**
```
Error: ODF requires additional disks on worker nodes
```
- Add `--worker-additional-disks` parameter
- Minimum two disks recommended: `--worker-additional-disks "200,200"`

### Connection Issues

**Unable to Access Cluster**
- Verify you are on IBM network or VPN
- Check cluster status in FYRE portal
- Ensure firewall rules allow access

**Authentication Failures**
- Verify credentials are correct
- Check if password has expired
- Try regenerating kubeadmin password in FYRE portal


Best Practices
-------------------------------------------------------------------------------

### Resource Planning
- **Development**: 3 workers, 4 CPU, 16 GB memory
- **Testing**: 3 workers, 8 CPU, 32 GB memory
- **Production-like**: 5+ workers, 16 CPU, 64 GB memory

### Quota Management
- Use `quick_burn` for short-term testing (auto-expires)
- Use `product_group` quota for longer-term environments
- Monitor quota usage regularly
- Clean up unused clusters promptly

### Naming Conventions
- Include purpose in name: `mas-dev`, `mas-test`, `mas-demo`
- Add date for temporary clusters: `mas-test-20260520`
- Use team or project identifiers: `team-a-mas-dev`

### Storage Selection
- **NFS**: Fast setup, good for development
- **ODF**: Production-grade, requires more resources
- **Longhorn**: Alternative to ODF, lighter weight

!!! tip
    Always provision with `--no-confirm` in automation scripts to avoid interactive prompts.