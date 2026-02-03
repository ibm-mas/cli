Backup and Restore
===============================================================================

This guide provides comprehensive information on backing up and restoring IBM Maximo Application Suite (MAS) instances. The backup process captures critical configuration data, MongoDB databases, Suite License Service (SLS) data, and certificate manager configurations to enable disaster recovery and migration scenarios.

!!! important
    This guide currently covers **backup operations only**. Restore functionality documentation will be added in a future update.


Overview
-------------------------------------------------------------------------------

The MAS backup process uses Tekton pipelines to orchestrate the backup of multiple components. The Tekton pipeline executes [Ansible DevOps Collection](https://ibm-mas.github.io/ansible-devops/) roles to perform the actual backup operations.

### Backup Components

- **IBM Operator Catalogs** - Catalog source definitions
- **Certificate Manager** - Certificate configurations (Red Hat or IBM)
- **MongoDB** - MAS configuration database (Community Edition only)
- **Suite License Service (SLS)** - License server data (optional)
- **MAS Suite Configuration** - Core MAS instance configuration and custom resources

The backup creates a compressed archive that can be stored locally or uploaded to cloud storage (S3 or Artifactory).

### Ansible DevOps Integration

The `mas backup` command launches a Tekton pipeline that executes the following Ansible roles from the [IBM MAS DevOps Collection](https://ibm-mas.github.io/ansible-devops/):

- [`ibm.mas_devops.ibm_catalogs`](https://ibm-mas.github.io/ansible-devops/roles/ibm_catalogs/) - Backs up IBM Operator Catalog definitions
- [`ibm.mas_devops.cert_manager`](https://ibm-mas.github.io/ansible-devops/roles/cert_manager/) - Backs up Certificate Manager configurations
- [`ibm.mas_devops.mongodb`](https://ibm-mas.github.io/ansible-devops/roles/mongodb/) - Backs up MongoDB Community Edition databases
- [`ibm.mas_devops.sls`](https://ibm-mas.github.io/ansible-devops/roles/sls/) - Backs up Suite License Service data
- [`ibm.mas_devops.suite_backup`](https://ibm-mas.github.io/ansible-devops/roles/suite_backup/) - Backs up MAS Core configuration

For detailed information about the underlying Ansible automation, see the [Backup and Restore Playbook Documentation](https://ibm-mas.github.io/ansible-devops/playbooks/backup-restore/).

!!! tip
    Advanced users can use the Ansible roles directly for custom backup workflows. The CLI provides a managed, simplified interface to these roles with additional features like automatic pipeline setup and cloud upload capabilities.


When to Backup
-------------------------------------------------------------------------------

### Regular Backup Schedule
Establish a regular backup schedule based on your organization's requirements:

- **Before major upgrades** - Always backup before upgrading MAS or its dependencies
- **After configuration changes** - Backup after significant configuration modifications
- **Regular intervals** - Weekly or monthly backups for disaster recovery
- **Before cluster maintenance** - Backup before OpenShift cluster maintenance windows

### Migration Scenarios
Backups are essential for:

- **Cluster migration** - Moving MAS from one OpenShift cluster to another
- **Disaster recovery** - Recovering from cluster failures or data corruption
- **Environment cloning** - Creating test/dev environments from production backups
- **Version rollback** - Reverting to a previous configuration state


Component Selection
-------------------------------------------------------------------------------

### Including SLS in Backups

**Include SLS (`--include-sls` or default behavior)** when:

- SLS is deployed **in-cluster** in the same OpenShift environment as MAS
- You are using the standard MAS installation with bundled SLS
- The SLS namespace is accessible from your backup environment
- You want a complete, self-contained backup for disaster recovery

**Exclude SLS (`--exclude-sls`)** when:

- SLS is deployed **externally** in a separate cluster or environment
- You are using a shared SLS instance across multiple MAS installations
- SLS is managed by a different team or organization
- The SLS namespace is not accessible from your backup environment
- You only need to backup MAS-specific configuration

!!! note
    The default behavior is to **include SLS** in backups. You must explicitly use `--exclude-sls` to skip SLS backup.

### Data Reporter Operator (DRO)

The Data Reporter Operator (DRO) is **not included in backup operations** as it is typically configured during restore or installation. DRO configuration is handled separately and can be:

- **Installed during restore** - DRO will be automatically installed when restoring from a backup
- **Configured externally** - If using an external DRO instance, it should be configured independently
- **Skipped** - DRO installation can be skipped during restore if not required

!!! info
    DRO backup and restore behavior is managed by the underlying [Ansible DevOps roles](https://ibm-mas.github.io/ansible-devops/playbooks/backup-restore/). The CLI backup command focuses on capturing MAS configuration and data, while DRO is handled during the restore process.

### MongoDB Configuration

The backup process supports **MongoDB Community Edition only**. Ensure you specify the correct MongoDB configuration:

- **Namespace** - Where MongoDB is deployed (default: `mongoce`)
- **Instance Name** - MongoDB instance identifier (default: `mas-mongo-ce`)
- **Provider** - Must be `community` (only supported provider for backup)

!!! warning
    IBM Cloud Databases for MongoDB and other external MongoDB providers are not supported by the backup process. You must use their native backup mechanisms.

### Certificate Manager

Specify the certificate manager provider used in your environment:

- **Red Hat Certificate Manager** (`--cert-manager-provider redhat`) - Default option
- **IBM Certificate Manager** (`--cert-manager-provider ibm`) - For IBM Cloud Pak deployments

The backup captures certificate configurations but not the actual certificates, which are regenerated during restore.


Backup Modes
-------------------------------------------------------------------------------

### Interactive Mode

Interactive mode guides you through the backup process with prompts for all required configuration. This is the recommended approach for manual backups.

```bash
docker run -ti --rm quay.io/ibmmas/cli mas backup
```

The interactive session will:

1. Prompt for OpenShift cluster connection
2. Display detected MAS instances
3. Request backup storage size
4. Offer auto-generated or custom backup version
5. Configure optional upload to S3 or Artifactory

### Non-Interactive Mode

Non-interactive mode is ideal for automation, scheduled backups, and CI/CD pipelines. All required parameters must be provided via command-line arguments.

```bash
docker run -ti --rm quay.io/ibmmas/cli mas backup \
  --instance-id inst1 \
  --no-confirm
```


Backup Scenarios - Non-Interactive Mode
-------------------------------------------------------------------------------

### Scenario 1: Standard In-Cluster Deployment

**Environment:**
- MAS with all dependencies in a single OpenShift cluster
- MongoDB Community Edition
- In-cluster SLS
- Red Hat Certificate Manager

**Backup Command:**
```bash
mas backup \
  --instance-id inst1 \
  --backup-storage-size 50Gi \
  --no-confirm
```

This uses all default values and includes SLS in the backup.

### Scenario 2: External SLS Deployment

**Environment:**
- MAS in OpenShift cluster
- MongoDB Community Edition in-cluster
- SLS deployed in separate cluster or external environment
- Red Hat Certificate Manager

**Backup Command:**
```bash
mas backup \
  --instance-id inst1 \
  --backup-storage-size 30Gi \
  --exclude-sls \
  --no-confirm
```

Use `--exclude-sls` to skip backing up SLS when it's managed externally.

### Scenario 3: Custom MongoDB Configuration and backup version

**Environment:**
- MAS with custom MongoDB namespace
- Custom backup version desired
- Custom MongoDB instance name
- In-cluster SLS
- Red Hat Certificate Manager

**Backup Command:**
```bash
mas backup \
  --instance-id inst1 \
  --backup-version prod-backup-$(date +%Y%m%d) \
  --backup-storage-size 50Gi \
  --mongodb-namespace my-mongodb \
  --mongodb-instance-name custom-mongo-instance \
  --mongodb-provider community \
  --no-confirm
```

### Scenario 4: Backup with S3 Upload

**Environment:**
- Standard MAS deployment
- Custom backup version desired
- Automatic upload to AWS S3 for off-site storage

**Backup Command:**
```bash
mas backup \
  --instance-id inst1 \
  --backup-version prod-$(date +%Y%m%d-%H%M%S) \
  --backup-storage-size 50Gi \
  --upload-backup \
  --aws-access-key-id AKIAIOSFODNN7EXAMPLE \ #pragma: allowlist secret
  --aws-secret-access-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY \ #pragma: allowlist secret
  --s3-bucket-name mas-backups-prod \
  --s3-region us-east-1 \
  --no-confirm
```

!!! tip
    Store AWS credentials securely using environment variables or secrets management systems rather than hardcoding them in scripts.

### Scenario 7: Minimal Backup (Skip Pre-Check)

**Environment:**
- Emergency backup scenario
- Custom backup version desired
- Skip pre-backup validation for speed, and when the cluster is not 100% healthy

**Backup Command:**
```bash
mas backup \
  --instance-id inst1 \
  --backup-version emergency-$(date +%Y%m%d-%H%M%S) \
  --backup-storage-size 50Gi \
  --skip-pre-check \
  --no-confirm
```

!!! warning
    Use `--skip-pre-check` only in emergency situations. Pre-backup checks validate cluster health and can prevent incomplete backups.


Storage Requirements
-------------------------------------------------------------------------------

### Backup Storage Sizing

The backup storage size depends on several factors:

| Component | Typical Size | Notes |
|-----------|-------------|-------|
| MAS Configuration | < 1 GB | Core MAS custom resources and configurations |
| MongoDB Database | 5-50 GB | Varies based on workspace count and data volume |
| SLS Data | < 1 GB | License server database and configuration |
| IBM Catalogs | < 1 GB | Operator catalog definitions |
| Certificate Manager | < 1 GB | Certificate configurations |

**Recommended Minimum Sizes:**

- **Small deployment** (1-2 workspaces): `20Gi` (default)
- **Medium deployment** (3-5 workspaces): `50Gi`
- **Large deployment** (6+ workspaces): `100Gi` or more

!!! tip
    Monitor your first backup to determine actual storage requirements, then adjust the `--backup-storage-size` parameter for future backups.

### Storage Class Considerations

The backup process automatically selects appropriate storage:

- **Single Node OpenShift (SNO)**: Uses ReadWriteOnce (RWO) storage
- **Multi-node clusters**: Prefers ReadWriteMany (RWX) storage when available
- Falls back to RWO if RWX is not available

The storage class is determined from your cluster's default storage classes.


Backup Process Details
-------------------------------------------------------------------------------

### Pipeline Execution

When you run `mas backup`, the following occurs:

1. **Validation** - Verifies cluster connectivity and MAS instance existence
2. **Namespace Preparation** - Creates/updates `mas-{instance-id}-pipelines` namespace
3. **OpenShift Pipelines** - Validates or installs OpenShift Pipelines Operator
4. **PVC Creation** - Provisions persistent volume for backup storage
5. **Tekton Pipeline Launch** - Submits PipelineRun with configured parameters
6. **Component Backup** - Executes backup tasks in parallel where possible:
   - IBM Catalogs backup
   - Certificate Manager backup
   - MongoDB backup
   - SLS backup (if included)
7. **Suite Backup** - Backs up MAS core configuration
8. **Archive Creation** - Compresses backup into tar.gz archive
9. **Upload** (optional) - Uploads archive to S3 or Artifactory

### Monitoring Progress

After launching the backup, a URL to the Tekton PipelineRun is displayed:

```
View progress:
  https://console-openshift-console.apps.cluster.example.com/k8s/ns/mas-inst1-pipelines/tekton.dev~v1beta1~PipelineRun/mas-backup-20240315-120000
```

Use this URL to:

- Monitor real-time backup progress
- View logs from individual backup tasks
- Troubleshoot any failures
- Verify successful completion

### Backup Artifacts

Backups are stored in the pipeline namespace PVC at:

- **Backup Directory**: `/workspace/backups`
- **Config Directory**: `/workspace/configs`

The final backup archive is named: `mas-backup-{instance-id}-{backup-version}.tar.gz`


Best Practices
-------------------------------------------------------------------------------

### Backup Strategy

1. **Regular Schedule** - Implement automated backups on a regular schedule
2. **Version Naming** - Use descriptive backup versions (e.g., `prod-20240315-pre-upgrade`)
3. **Retention Policy** - Define how long to keep backups based on compliance requirements
4. **Off-site Storage** - Upload backups to S3 or Artifactory for disaster recovery
5. **Test Restores** - Periodically test restore procedures in non-production environments
6. **Document Configuration** - Keep records of custom configurations and dependencies

### Security Considerations

1. **Credentials** - Never hardcode credentials in scripts; use environment variables or secrets
2. **Access Control** - Restrict access to backup storage and archives
3. **Encryption** - Consider encrypting backup archives for sensitive environments
4. **Audit Trail** - Maintain logs of backup operations and access

### Automation

For automated backups, you have several options depending on your infrastructure and requirements:

#### Option 1: Shell Script with MAS CLI

Create a simple shell script or CI/CD pipeline using the MAS CLI:

```bash
#!/bin/bash
# Automated MAS Backup Script

INSTANCE_ID="inst1"
BACKUP_VERSION="auto-$(date +%Y%m%d-%H%M%S)"
S3_BUCKET="mas-backups-prod"

# Login to OpenShift
oc login --token=${OCP_TOKEN} --server=${OCP_SERVER}

# Run backup with S3 upload
docker run --rm \
  -v ~/.kube:/root/.kube:z \
  quay.io/ibmmas/cli mas backup \
  --instance-id ${INSTANCE_ID} \
  --backup-version ${BACKUP_VERSION} \
  --backup-storage-size 50Gi \
  --upload-backup \
  --aws-access-key-id ${AWS_ACCESS_KEY_ID} \
  --aws-secret-access-key ${AWS_SECRET_ACCESS_KEY} \
  --s3-bucket-name ${S3_BUCKET} \
  --s3-region us-east-1 \
  --no-confirm

# Check exit code
if [ $? -eq 0 ]; then
  echo "Backup completed successfully: ${BACKUP_VERSION}"
else
  echo "Backup failed!"
  exit 1
fi
```

#### Option 2: Red Hat Ansible Automation Platform

For enterprise-grade automation with advanced features, use **Red Hat Ansible Automation Platform (AAP)** to execute the backup playbooks and roles directly. The [MAS DevOps Execution Environment](https://ibm-mas.github.io/ansible-devops/execution-environment/) provides a pre-built container image (`quay.io/ibmmas/ansible-devops-ee`) that includes the `ibm.mas_devops` collection and all required dependencies.

**Benefits of using AAP:**

- **Centralized Management** - Single control plane for all automation
- **Role-Based Access Control (RBAC)** - Fine-grained permissions for backup operations
- **Scheduling** - Built-in job scheduling for regular backups
- **Audit Logging** - Complete audit trail of all backup operations
- **Credential Management** - Secure storage and injection of credentials
- **Notifications** - Integration with email, Slack, PagerDuty, and other systems
- **Job Templates** - Reusable backup configurations
- **Workflow Automation** - Chain backup with other operations (e.g., validation, upload)

**To use AAP for MAS backups:**

1. **Configure the Execution Environment** - Set up AAP to use the `quay.io/ibmmas/ansible-devops-ee` image (see [Execution Environment setup guide](https://ibm-mas.github.io/ansible-devops/execution-environment/))
2. **Create a Project** - Point to your playbook repository (or use the sample playbooks as a starting point)
3. **Create Job Templates** - Configure job templates for backup operations using the [`ibm.mas_devops.br_core`](https://ibm-mas.github.io/ansible-devops/playbooks/backup-restore/) playbook
4. **Configure Credentials** - Set up OpenShift credentials and any cloud storage credentials
5. **Schedule Backups** - Set up recurring schedules for automated backups
6. **Configure Notifications** - Set up alerts for backup success/failure

**Example AAP Job Template Variables:**

```yaml
mas_instance_id: inst1
br_action: backup
mas_backup_dir: /backup/mas
backup_version: "{{ ansible_date_time.date }}-{{ ansible_date_time.hour }}{{ ansible_date_time.minute }}"
include_sls: true
mongodb_namespace: mongoce
```

For detailed information on setting up and using Ansible Automation Platform with MAS DevOps, see:
- [MAS DevOps Execution Environment](https://ibm-mas.github.io/ansible-devops/execution-environment/) - Complete AAP setup guide
- [Backup and Restore Playbook](https://ibm-mas.github.io/ansible-devops/playbooks/backup-restore/) - Playbook documentation and examples

!!! tip
    AAP is recommended for production environments where you need enterprise features like RBAC, audit logging, and centralized management. For simpler use cases, the MAS CLI with shell scripts may be sufficient.




Troubleshooting
-------------------------------------------------------------------------------

### Common Issues

**Issue: "No MAS instances were detected on the cluster"**

- Verify you're connected to the correct OpenShift cluster
- Ensure MAS is installed and the Suite CR exists
- Check that you have permissions to view Suite resources

**Issue: "OpenShift Pipelines Operator installation failed"**

- Verify cluster admin permissions
- Check cluster connectivity and operator hub availability
- Review operator installation logs

**Issue: "Insufficient storage for backup PVC"**

- Increase `--backup-storage-size` parameter
- Verify storage class has available capacity
- Check cluster storage quotas

**Issue: "MongoDB backup failed"**

- Verify MongoDB namespace and instance name are correct
- Ensure MongoDB is running and accessible
- Check MongoDB provider is set to `community`

**Issue: "SLS backup failed"**

- Verify SLS namespace is correct
- Ensure SLS is running and accessible
- Consider using `--exclude-sls` if SLS is external

**Issue: "Upload to S3 failed"**

- Verify AWS credentials are correct
- Check S3 bucket exists and is accessible
- Verify network connectivity to AWS
- Ensure IAM permissions allow PutObject operations


Additional Resources
-------------------------------------------------------------------------------

### MAS CLI Documentation
- [Backup Command Reference](../commands/backup.md) - Complete command-line options and usage

### Ansible DevOps Collection
- [Backup and Restore Playbook](https://ibm-mas.github.io/ansible-devops/playbooks/backup-restore/) - Detailed Ansible playbook documentation
- [Execution Environment](https://ibm-mas.github.io/ansible-devops/execution-environment/) - Ansible Automation Platform setup guide
- [IBM Catalogs Role](https://ibm-mas.github.io/ansible-devops/roles/ibm_catalogs/) - IBM Operator Catalog backup/restore
- [Certificate Manager Role](https://ibm-mas.github.io/ansible-devops/roles/cert_manager/) - Certificate Manager backup/restore
- [MongoDB Role](https://ibm-mas.github.io/ansible-devops/roles/mongodb/) - MongoDB backup/restore
- [SLS Role](https://ibm-mas.github.io/ansible-devops/roles/sls/) - Suite License Service backup/restore
- [Suite Backup Role](https://ibm-mas.github.io/ansible-devops/roles/suite_backup/) - MAS Core backup
- [Suite Restore Role](https://ibm-mas.github.io/ansible-devops/roles/suite_restore/) - MAS Core restore

### External Documentation
- [MAS Documentation](https://www.ibm.com/docs/en/mas) - Official IBM Maximo Application Suite documentation
- [OpenShift Pipelines](https://docs.openshift.com/container-platform/latest/cicd/pipelines/understanding-openshift-pipelines.html) - Tekton pipeline documentation
- [Ansible DevOps Collection](https://ibm-mas.github.io/ansible-devops/) - Complete Ansible automation documentation
- [Red Hat Ansible Automation Platform](https://www.redhat.com/en/technologies/management/ansible) - Enterprise automation platform