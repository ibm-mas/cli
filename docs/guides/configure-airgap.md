Configure OpenShift for Airgap Install
===============================================================================

Overview
-------------------------------------------------------------------------------
The MAS CLI provides automated configuration of airgap (disconnected) OpenShift environments for Maximo Application Suite installations. Airgap configuration enables OpenShift clusters without direct internet access to pull container images from a private registry by configuring ImageDigestMirrorSet (IDMS) resources.

This guide covers the complete process of configuring an OpenShift cluster to use a private container registry for airgap deployments.

!!! warning "ROKS Limitation"
    The `configure-airgap` command does not work on **IBM Cloud ROKS** clusters. This is a limitation of the IBM Cloud ROKS service which disables key parts of OpenShift functionality required to configure and use ImageDigestMirrorSet resources (which is the basis of airgap/image mirroring support in OpenShift).


Understanding Airgap Configuration
-------------------------------------------------------------------------------

### What is Airgap?
An airgap (or air-gapped) environment is a network security measure where a computer or network is physically isolated from unsecured networks, including the internet. In the context of OpenShift and MAS:

- Cluster has no direct internet connectivity
- Cannot pull images from public registries (quay.io, docker.io, etc.)
- Requires all container images to be available in a private registry
- Uses ImageDigestMirrorSet (IDMS) to redirect image pulls to private registry

### How Airgap Works

1. Application requests image from `quay.io/ibmmas/example:latest`
2. IDMS instructs Kubernetes to redirect request to `private-registry.company.com/ibmmas/example:latest`
3. Image is pulled from private registry instead of public registry

### Prerequisites for Airgap
Before configuring airgap, you must:

1. **Mirror Images** - Copy all required images to your private registry
2. **Private Registry** - Have a functioning private container registry
3. **Network Access** - Cluster must have network access to private registry
4. **Registry Credentials** - Authentication credentials for the private registry


Preparation
-------------------------------------------------------------------------------

### Private Container Registry
You must have a private container registry accessible from your OpenShift cluster. Supported registries include:

- **Red Hat Quay** - Enterprise container registry
- **Harbor** - Open source container registry
- **Artifactory** - Universal artifact repository
- **Docker Registry** - Simple registry implementation
- **AWS ECR** - Amazon Elastic Container Registry
- **Azure ACR** - Azure Container Registry

The registry must:
- Be accessible from the OpenShift cluster network
- Support Docker Registry HTTP API V2
- Have sufficient storage for mirrored images
- Support authentication (username/password or token)

### Registry Certificate
If your private registry uses TLS with a custom certificate authority (CA):

1. Obtain the CA certificate file (`.crt` or `.pem` format)
2. Save it to a location accessible to the CLI
3. Note the file path for use during configuration

!!! tip
    Self-signed certificates are common in private registries. The CLI can configure OpenShift to trust your custom CA.

### Registry Credentials
Prepare authentication credentials for your private registry:

- **Username** - Registry username or service account
- **Password** - Registry password or access token
- **Registry URL** - Full registry hostname and port

Example registry URLs:
- `registry.company.com:5000`
- `harbor.internal.net`
- `quay.enterprise.com`

### Mirrored Images
Before configuring airgap, ensure all required images are mirrored to your private registry:

- **MAS Operator Images** - Core MAS operators and dependencies
- **Application Images** - MAS application images (Manage, Monitor, etc.)
- **Dependency Images** - MongoDB, Db2, Certificate Manager, etc.
- **Red Hat Images** - OpenShift operators and components

Refer to the [Image Mirroring Guide](image-mirroring.md) for detailed mirroring instructions.


Configuration Process
-------------------------------------------------------------------------------

### How Airgap Configuration Works
The `configure-airgap` command performs the following steps:

1. **Validates Registry Access** - Tests connectivity to private registry
2. **Creates Pull Secret** - Configures registry authentication
3. **Creates IDMS Resources** - Configures image source redirection
4. **Trusts CA Certificate** - Adds custom CA to cluster trust (if provided)
5. **Restarts Machine Config** - Applies configuration to all nodes

!!! note
    Node restarts are required to apply IDMS configuration. The cluster will experience a rolling restart of all nodes, which may take 30-60 minutes depending on cluster size.

### Interactive Mode
Interactive mode guides you through the configuration process with prompts for all required information.

```bash
docker run -ti --rm -v ~:/mnt/local --pull always quay.io/ibmmas/cli mas configure-airgap
```

The interactive session will:

1. Prompt for OpenShift cluster connection
2. Request private registry details (hostname, port)
3. Request registry credentials (username, password)
4. Optionally request CA certificate file path
5. Display configuration summary
6. Request confirmation before applying changes

### Non-Interactive Mode
Non-interactive mode is ideal for automation and scripting. All required parameters must be provided via command-line arguments.

```bash
docker run -ti --rm -v ~:/mnt/local --pull always quay.io/ibmmas/cli mas configure-airgap \
  -H registry.company.com \
  -P 5000 \
  -u $REGISTRY_USERNAME \
  -p $REGISTRY_PASSWORD \
  --ca-file /mnt/local/registry-ca.crt \
  --no-confirm
```


Configuration Examples
-------------------------------------------------------------------------------

### Basic Configuration (No Custom CA)
Configure airgap with a registry using publicly trusted certificates:

```bash
export REGISTRY_USERNAME=admin
export REGISTRY_PASSWORD=secure-password

docker run -ti --rm --pull always quay.io/ibmmas/cli mas configure-airgap \
  -H registry.company.com \
  -P 443 \
  -u $REGISTRY_USERNAME \
  -p $REGISTRY_PASSWORD \
  --no-confirm
```

### Configuration with Custom CA Certificate
Configure airgap with a registry using self-signed or custom CA certificates:

```bash
# Save CA certificate to local directory
cat > ~/registry-ca.crt <<EOF
-----BEGIN CERTIFICATE-----
MIIDXTCCAkWgAwIBAgIJAKL0UG+mRKtjMA0GCSqGSIb3DQEBCwUAMEUxCzAJBgNV
...
-----END CERTIFICATE-----
EOF

# Configure airgap with CA certificate
docker run -ti --rm -v ~:/mnt/local --pull always quay.io/ibmmas/cli mas configure-airgap \
  -H registry.internal.net \
  -P 5000 \
  -u $REGISTRY_USERNAME \
  -p $REGISTRY_PASSWORD \
  --ca-file /mnt/local/registry-ca.crt \
  --no-confirm
```

### Harbor Registry Configuration
Configure airgap for Harbor registry:

```bash
docker run -ti --rm -v ~:/mnt/local --pull always quay.io/ibmmas/cli mas configure-airgap \
  -H harbor.company.com \
  -P 443 \
  -u robot-account \
  -p $HARBOR_TOKEN \
  --ca-file /mnt/local/harbor-ca.crt \
  --no-confirm
```

### Red Hat Quay Configuration
Configure airgap for Red Hat Quay registry:

```bash
docker run -ti --rm -v ~:/mnt/local --pull always quay.io/ibmmas/cli mas configure-airgap \
  -H quay.enterprise.com \
  -P 443 \
  -u quay-user \
  -p $QUAY_PASSWORD \
  --no-confirm
```

### Docker Registry Configuration
Configure airgap for simple Docker registry:

```bash
docker run -ti --rm -v ~:/mnt/local --pull always quay.io/ibmmas/cli mas configure-airgap \
  -H docker-registry.local \
  -P 5000 \
  -u registry-user \
  -p $REGISTRY_PASSWORD \
  --ca-file /mnt/local/docker-ca.crt \
  --no-confirm
```


Command Reference
-------------------------------------------------------------------------------

### Registry Configuration
- `-H, --registry-host REGISTRY_HOST` - Private registry hostname (required)
- `-P, --registry-port REGISTRY_PORT` - Private registry port (default: 443)
- `-u, --username REGISTRY_USERNAME` - Registry username (required)
- `-p, --password REGISTRY_PASSWORD` - Registry password (required)

### Certificate Configuration
- `--ca-file CA_FILE_PATH` - Path to CA certificate file (optional)

### Other Options
- `--no-confirm` - Skip confirmation prompt
- `-h, --help` - Display help message


Post-Configuration Steps
-------------------------------------------------------------------------------

### Monitoring Node Restarts
After applying airgap configuration, OpenShift will perform a rolling restart of all nodes to apply the new configuration. Monitor the process:

```bash
# Watch machine config pools
watch oc get mcp

# Expected output shows nodes updating
NAME     CONFIG                                             UPDATED   UPDATING   DEGRADED   MACHINECOUNT   READYMACHINECOUNT   UPDATEDMACHINECOUNT   DEGRADEDMACHINECOUNT   AGE
master   rendered-master-abc123                             False     True       False      3              2                   2                     0                      10m
worker   rendered-worker-def456                             False     True       False      3              2                   2                     0                      10m
```

Wait until all machine config pools show `UPDATED=True` and `UPDATING=False`.

### Verifying Configuration

#### Check IDMS Resources
```bash
# List ImageDigestMirrorSet resources
oc get imagedigestmirrorset

# View IDMS details
oc describe imagedigestmirrorset <idms-name>
```


#### Check Pull Secret
```bash
# Verify pull secret includes private registry
oc get secret pull-secret -n openshift-config -o jsonpath='{.data.\.dockerconfigjson}' | base64 -d | jq
```

#### Check CA Trust
If you provided a CA certificate:

```bash
# Verify CA is in cluster trust bundle
oc get configmap -n openshift-config user-ca-bundle -o yaml
```

#### Test Image Pull
Test pulling an image from your private registry:

```bash
# Create test pod
oc run test-pull --image=registry.company.com:5000/ibmmas/cli:latest --restart=Never

# Check pod status
oc get pod test-pull

# Clean up
oc delete pod test-pull
```

### Next Steps
With airgap configuration complete, you can proceed to:

- [Install MAS](install.md) in the airgap environment
- Configure additional registry mirrors if needed
- Set up monitoring for registry connectivity


Troubleshooting
-------------------------------------------------------------------------------

### Configuration Failures

**Registry Not Accessible**
```
Error: Unable to connect to registry
```
- Verify registry hostname and port are correct
- Check network connectivity from cluster to registry
- Ensure firewall rules allow traffic
- Test connectivity: `curl -k https://registry.company.com:5000/v2/`

**Authentication Failed**
```
Error: Authentication to registry failed
```
- Verify username and password are correct
- Check if credentials have expired
- Ensure user has pull permissions
- Test authentication: `docker login registry.company.com:5000`

**Invalid CA Certificate**
```
Error: CA certificate validation failed
```
- Verify CA certificate file is in correct format (PEM)
- Ensure certificate is not expired
- Check certificate includes full chain if needed
- Validate certificate: `openssl x509 -in ca.crt -text -noout`

### Node Restart Issues

**Nodes Stuck in Updating State**
```
NAME     UPDATED   UPDATING   DEGRADED
worker   False     True       False
```
- Check machine config operator logs: `oc logs -n openshift-machine-config-operator <pod-name>`
- Review node status: `oc describe node <node-name>`
- Check for resource constraints or disk space issues
- Wait longer - large clusters may take 60+ minutes

**Nodes in Degraded State**
```
NAME     UPDATED   UPDATING   DEGRADED
worker   False     False      True
```
- Check machine config daemon logs: `oc logs -n openshift-machine-config-operator <mcd-pod>`
- Review node events: `oc get events -n openshift-machine-config-operator`
- Check for configuration conflicts
- May require manual intervention or rollback

### Image Pull Failures

**Images Not Found in Private Registry**
```
Error: Failed to pull image: manifest unknown
```
- Verify images are mirrored to private registry
- Check image paths match IDMS configuration
- Ensure registry namespace structure is correct
- Review mirroring logs for errors

**IDMS Not Applied**
```
Error: Still pulling from public registry
```
- Verify IDMS resources exist: `oc get imagedigestmirrorset`
- Check machine config pools are updated: `oc get mcp`
- Ensure nodes have restarted
- Review IDMS configuration for errors

**Certificate Trust Issues**
```
Error: x509: certificate signed by unknown authority
```
- Verify CA certificate was provided during configuration
- Check CA is in cluster trust bundle
- Ensure certificate is valid and not expired
- May need to reconfigure with correct CA

### Registry Connectivity

**Intermittent Connection Failures**
```
Error: Timeout connecting to registry
```
- Check network stability between cluster and registry
- Verify registry is not overloaded
- Review registry logs for errors
- Consider increasing timeout values

**DNS Resolution Failures**
```
Error: Cannot resolve registry hostname
```
- Verify DNS configuration in cluster
- Check if registry hostname is resolvable: `oc debug node/<node> -- chroot /host nslookup registry.company.com`
- Consider using IP address instead of hostname
- Verify DNS servers are accessible
