Provision OpenShift on AWS ROSA
===============================================================================

Overview
-------------------------------------------------------------------------------
The MAS CLI provides automated provisioning of Red Hat OpenShift Service on AWS (ROSA) clusters. ROSA is a managed OpenShift offering jointly operated by Red Hat and AWS, with the cluster running in your own AWS account.

This guide covers obtaining the required credentials and provisioning a ROSA cluster using `mas provision-rosa`.

!!! note
    This is different from [provision-aws](provision-aws.md), which uses Installer Provisioned Infrastructure (IPI) to deploy a self-managed OpenShift cluster on AWS.


Preparation
-------------------------------------------------------------------------------

### ROSA Token
The ROSA token authenticates the CLI with the Red Hat OpenShift Cluster Manager:

1. Log in to [Red Hat OpenShift Cluster Manager](https://console.redhat.com/openshift/token/rosa/show)
2. Copy the offline token shown on the page

!!! warning
    Treat your ROSA token as a password. Never commit it to source control or share it publicly.

### AWS Credentials
You will need an AWS access key ID and secret access key for an AWS account that has been [enabled for ROSA](https://console.aws.amazon.com/rosa/home). The IAM user must have permission to create the ROSA account roles, the cluster itself, and EFS file systems.

### Cluster Admin Password
A password for the `cluster-admin` user that will be created on the cluster. Choose a strong password as this user has full administrative access to the cluster.

### OpenShift Version
Specify the full OpenShift version to install (e.g. `4.22.8`). Refer to the [MAS system requirements](https://www.ibm.com/docs/en/mas-cd/continuous-delivery) for version compatibility.


Cluster Configuration
-------------------------------------------------------------------------------
### Worker Nodes
MAS requires a minimum of 3 worker nodes for high availability. The default worker machine type is `m5.4xlarge` (16 vCPU, 64 GB memory).

### Storage
After the cluster is ready the provisioner configures Amazon EFS storage classes on the cluster.

### Turbonomic Integration (Optional)
If a Turbonomic target name is supplied, the cluster will be registered with your Turbonomic server.


Provisioning Modes
-------------------------------------------------------------------------------

### Interactive Mode
Interactive mode guides you through the provisioning process with prompts for all configuration options.

```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas provision-rosa
```

The interactive session will:

1. Prompt for the ROSA token and cluster admin password
2. Prompt for AWS credentials and region
3. Request cluster name, OpenShift version and worker node configuration
4. Optionally configure Turbonomic integration
5. Display a summary and request confirmation

### Non-Interactive Mode
Non-interactive mode is ideal for automation and CI/CD pipelines. All required parameters must be provided via command-line arguments or environment variables.

```bash
export ROSA_TOKEN=your-rosa-token
export ROSA_CLUSTER_ADMIN_PASSWORD=your-admin-password #pragma: allowlist secret
export AWS_ACCESS_KEY_ID=your-access-key-id
export AWS_SECRET_ACCESS_KEY=your-secret-access-key #pragma: allowlist secret

docker run -ti --rm --pull always quay.io/ibmmas/cli mas provision-rosa \
  -t $ROSA_TOKEN \
  -p $ROSA_CLUSTER_ADMIN_PASSWORD \
  -a $AWS_ACCESS_KEY_ID \
  -k $AWS_SECRET_ACCESS_KEY \
  -r us-east-1 \
  -c mas-rosa-cluster \
  -v 4.22.8 \
  --worker-count 3 \
  --worker-flavor m5.4xlarge \
  --no-confirm
```


Command Reference
-------------------------------------------------------------------------------

### ROSA Credentials
- `-t, --rosa-token ROSA_TOKEN` - Red Hat OpenShift Cluster Manager API token (required)
- `-p, --admin-password ROSA_CLUSTER_ADMIN_PASSWORD` - Password for the cluster-admin user (required)

### AWS Credentials
- `-a, --accesskeyid AWS_ACCESS_KEY_ID` - AWS access key ID (required)
- `-k, --secretkey AWS_SECRET_ACCESS_KEY` - AWS secret access key (required)
- `-r, --region AWS_DEFAULT_REGION` - AWS region for the cluster, e.g., `us-east-1`

### Cluster Configuration
- `-c, --cluster-name CLUSTER_NAME` - Cluster name (required)
- `-v, --ocp-version OCP_VERSION` - OpenShift version, e.g., `4.22.8` (required)

### Worker Node Configuration
- `--worker-count ROSA_COMPUTE_NODES` - Number of worker nodes (required)
- `--worker-flavor ROSA_COMPUTE_MACHINE_TYPE` - AWS machine type of the worker nodes, e.g., `m5.4xlarge` (default: `m5.4xlarge`)

### Turbonomic Integration
- `--turbonomic-name TURBONOMIC_TARGET_NAME` - Target name in Turbonomic
- `--turbonomic-url TURBONOMIC_SERVER_URL` - Turbonomic server URL
- `--turbonomic-version TURBONOMIC_SERVER_VERSION` - Turbonomic server version
- `--turbonomic-username TURBONOMIC_USERNAME` - Turbonomic username
- `--turbonomic-password TURBONOMIC_PASSWORD` - Turbonomic password

### Other Options
- `--no-confirm` - Skip confirmation prompt
- `-h, --help` - Display help message


Post-Provisioning Steps
-------------------------------------------------------------------------------

### Accessing Your Cluster
When provisioning completes the CLI connects to the new cluster and prints the OpenShift console URL. Log in as the `cluster-admin` user with the password you supplied.

To retrieve the cluster details at any time:

```bash
rosa login --token $ROSA_TOKEN
rosa describe cluster -c mas-rosa-cluster
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
With your ROSA cluster provisioned, you can proceed to:

- [Install MAS](install.md)
