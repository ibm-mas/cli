Private Container Registry Management
===============================================================================

Overview
-------------------------------------------------------------------------------
The MAS CLI provides automated deployment and management of a private container registry within your OpenShift cluster. This in-cluster registry is essential for airgap (disconnected) environments where direct access to public container registries is not available.

!!! tip
    This in-cluster private registry is ideal for development and test environments. For production deployments, consider enterprise registry solutions like Red Hat Quay or Harbor.


Understanding Private Registries
-------------------------------------------------------------------------------

### What is a Private Registry?
A private container registry is a secure repository for storing and distributing container images within your organization. In the context of OpenShift and MAS:

- Stores mirrored container images from public registries
- Provides local image distribution without internet access
- Enables airgap deployments
- Reduces external bandwidth usage
- Improves image pull performance

### When to Use In-Cluster Registry
The MAS CLI's in-cluster registry is suitable for:

- **Airgap Environments** - Clusters without internet access
- **Development and Testing** - Quick setup for non-production environments
- **Proof of Concept** - Demonstrating MAS in disconnected scenarios
- **Temporary Deployments** - Short-term testing or migration scenarios

### When to Use External Registry
Consider external registry solutions for:

- **Production Deployments** - Enterprise-grade reliability and support
- **Multi-Cluster Environments** - Shared registry across multiple clusters
- **High Availability Requirements** - Redundancy and disaster recovery
- **Advanced Features** - Image scanning, replication, access control


Preparation
-------------------------------------------------------------------------------

### Cluster Requirements
Before deploying a private registry, ensure your cluster meets these requirements:

**Storage:**
- Available storage class for persistent volumes
- Sufficient storage capacity (minimum 500 GB, recommended 2000 GB+)
- Storage class supporting ReadWriteOnce (RWO) access mode

**Network:**
- LoadBalancer service type support (for external access)
- Or NodePort service type (alternative for clusters without LoadBalancer)
- Network connectivity between cluster nodes and registry

**Resources:**
- Sufficient CPU and memory for registry pods
- Available namespace for registry deployment

### Storage Class Selection
Choose an appropriate storage class based on your environment:

| Environment | Recommended Storage Class | Notes |
|-------------|--------------------------|-------|
| **IBM Cloud ROKS** | `ibmc-block-gold` | High-performance block storage |
| **AWS** | `gp3-csi` or `gp2-csi` | General purpose SSD |
| **Azure** | `managed-premium` | Premium SSD |
| **On-Premises** | `nfs-client` or `local-storage` | Depends on infrastructure |
| **OpenShift Data Foundation** | `ocs-storagecluster-ceph-rbd` | Ceph block storage |

To list available storage classes:
```bash
oc get storageclass
```

### Registry Credentials
Prepare credentials for registry authentication:

- **Username** - Registry admin username
- **Password** - Strong password for registry access

!!! warning "Security"
    Use a strong, unique password for the registry. This password will be used to authenticate all image push and pull operations.


Registry Deployment
-------------------------------------------------------------------------------

### How Registry Setup Works
The `setup-registry` command performs the following steps:

1. **Creates Namespace** - Deploys registry in dedicated namespace
2. **Configures Storage** - Creates PersistentVolumeClaim for image storage
3. **Deploys Registry** - Installs Docker Registry v2 container
4. **Generates Certificates** - Creates self-signed TLS certificates
5. **Creates Service** - Exposes registry via LoadBalancer or NodePort
6. **Configures Authentication** - Sets up basic authentication with provided credentials

### Interactive Mode
Interactive mode guides you through the deployment process with prompts for all configuration options.

```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas setup-registry
```

The interactive session will:

1. Prompt for OpenShift cluster connection
2. Request registry credentials (username, password)
3. Request namespace name (default: `airgap-registry`)
4. Request storage class
5. Request storage capacity (default: `2000Gi`)
6. Request service type (LoadBalancer or NodePort)
7. Display configuration summary
8. Request confirmation before deployment

### Non-Interactive Mode
Non-interactive mode is ideal for automation and scripting. All required parameters must be provided via command-line arguments.

```bash
export REGISTRY_PASSWORD=secure-password

docker run -ti --rm --pull always quay.io/ibmmas/cli mas setup-registry \
  -u registry-admin \
  -p $REGISTRY_PASSWORD \
  -n airgap-registry \
  -s ibmc-block-gold \
  -c 2000Gi \
  -t loadbalancer \
  --no-confirm
```

Command Reference
-------------------------------------------------------------------------------

### Setup Registry

#### Required Parameters
- `-u, --username REGISTRY_USERNAME` - Registry admin username (required)
- `-p, --password REGISTRY_PASSWORD` - Registry admin password (required)

#### Optional Parameters
- `-n, --namespace REGISTRY_NAMESPACE` - Registry namespace (default: `airgap-registry`)
- `-s, --storage-class STORAGE_CLASS` - Storage class for PVC (default: `ibmc-block-gold`)
- `-c, --storage-capacity STORAGE_CAPACITY` - Storage capacity (default: `2000Gi`)
- `-t, --service-type SERVICE_TYPE` - Service type: `loadbalancer` or `nodeport` (default: `loadbalancer`)

#### Other Options
- `--no-confirm` - Skip confirmation prompt
- `-h, --help` - Display help message


Post-Deployment Steps
-------------------------------------------------------------------------------

### Accessing the Registry
After deployment completes, retrieve registry access information:

```bash
# Get registry service details
oc get svc -n airgap-registry

# Get registry hostname/IP
oc get svc -n airgap-registry -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}'

# For NodePort service
oc get svc -n airgap-registry -o jsonpath='{.items[0].spec.ports[0].nodePort}'
```

### Retrieving CA Certificate
The registry uses self-signed certificates. Retrieve the CA certificate for client configuration:

```bash
# Extract CA certificate
oc get secret -n airgap-registry registry-tls -o jsonpath='{.data.ca\.crt}' | base64 -d > registry-ca.crt
```

### Testing Registry Access
Test registry connectivity and authentication:

```bash
# Test with curl (replace with your registry hostname)
curl -k -u admin:password https://registry.example.com:5000/v2/

# Expected response: {}
```

### Configuring Docker/Podman
Configure your local Docker or Podman to trust the registry:

```bash
# Copy CA certificate to Docker trust store
sudo mkdir -p /etc/docker/certs.d/registry.example.com:5000
sudo cp registry-ca.crt /etc/docker/certs.d/registry.example.com:5000/ca.crt

# Test login
docker login registry.example.com:5000 -u admin -p password
```

### Next Steps
With your private registry deployed, you can proceed to:

- [Mirror images](image-mirroring.md) to the registry
- [Configure airgap](configure-airgap.md) environment
- [Install MAS](install.md) using the private registry


Registry Removal
-------------------------------------------------------------------------------

### Understanding Registry Teardown
The `teardown-registry` command permanently removes the registry and all its data. This operation:

- Deletes the registry namespace and all resources
- Removes the PersistentVolumeClaim and stored images
- Deletes TLS certificates and authentication secrets
- Cannot be undone - all registry data is lost

!!! danger "Data Loss Warning"
    The `teardown-registry` command permanently deletes all registry data, including all stored container images. Ensure you have backups or can re-mirror images before proceeding.

### Interactive Teardown
Interactive mode prompts for confirmation before deletion:

```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas teardown-registry
```

### Non-Interactive Teardown
Non-interactive mode for automation (use with caution):

```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas teardown-registry \
  -n airgap-registry \
  --no-confirm
```

### Teardown Command Reference

#### Optional Parameters
- `-n, --namespace REGISTRY_NAMESPACE` - Registry namespace to remove (default: `airgap-registry`)

#### Other Options
- `--no-confirm` - Skip confirmation prompt (dangerous)
- `-h, --help` - Display help message
