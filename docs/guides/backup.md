# Backup
The MAS backup process uses Tekton pipelines to orchestrate the backup of multiple components. The Tekton pipeline executes [Ansible DevOps Collection](https://ibm-mas.github.io/ansible-devops/) roles to perform the actual backup operations.

!!! warning
    Before you begin

    Be aware of the following versioning considerations for the MAS CLI releases:

    The MAS backup and restore in CLI release v19.0.0 and later contains process, backup archive file and directory changes that are not backward compatible with earlier backup and restore versions.

    Run the backup processes using v19.0.0 or later to ensure that you can successfully run a restore. You cannot run a restore process using v19.0.0 or later from back ups created on an older version.

**Supported MAS versions**

- MAS 9.1.x

Note: MAS 9.0.x (Not supported yet, its in testing)

**User Permissions Required**

- `oc` CLI with cluster admin permissions
- `mas` CLI with appropriate permissions
- Access to Tekton pipeline resources


Backup Overview
-------------------------------------------------------------------------------
### Backup Components

- **IBM Operator Catalogs** - Catalog source definitions
- **Certificate Manager** - Certificate configurations (RedHat only)
- **MongoDB** - MAS configuration database (Community Edition only)
- **Suite License Service (SLS)** - License server data (optional)
- **MAS Suite Configuration** - Core MAS instance configuration and custom resources
- **MAS Applications** - Application-specific resources and persistent volume data (optional)
- **Db2 Database** - Db2 instance resources and database backups (optional)

The backup creates a compressed archive for each supported component that can be stored locally or uploaded to cloud storage (S3 or Artifactory).

### Backup Limitations

!!! warning
    Be aware of the following limitations before performing a backup:

- **MongoDB Community Edition only** - The backup process supports only in-cluster MongoDB Community Edition. External or enterprise MongoDB deployments are not backed up.
- **Db2 standalone operator only** - The backup process supports only the in-cluster standalone Db2 operator. Other Db2 operator implementations are not included.
- **Certificate Manager (RedHat only)** - Certificate Manager backup is supported only for RedHat Certificate Manager. Other certificate manager implementations are not included.
- **No support for some apps** - Only Manage application is supported for now. Other MAS applications (Facilities, Monitor, IoT, Predict, etc.) are not supported, but will be added in later releases.
- **No OpenShift cluster state** - The backup does not capture the full OpenShift cluster state, node configurations, or cluster-level resources outside of MAS namespaces.
- **No IBM Cloud Pak for Data backups** - The backup process does not support backing up CP4D itself.
- **No Incremental backups** - Each backup is a full backup; incremental or differential backups are not supported.
- **Single MAS instance per backup** - Each backup operation targets a single MAS instance. Multi-instance environments require separate backup runs per instance.
- **Tekton pipeline dependency** - The backup process requires Tekton pipelines to be available and functional on the cluster.
- **Storage class dependency** - Backup of Manage application's persistent volumes depends on the storage class supporting volume snapshots or the relevant backup mechanism.
- **S3/Artifactory upload is optional** - Without configuring cloud storage upload, backups are stored locally in the cluster and may be lost if the cluster is decommissioned.
- **Download backup archives to local machine manually** - The backup archives are stored in the cluster's pvc or uploaded to S3/Artifactory and must be downloaded to a local machine manually.

!!! tip
    We are working on reducing the limitations of the backup process and will be adding new capabilties and support for other MAS applications in future releases.

### Ansible DevOps Integration

The `mas backup` command launches a Tekton pipeline that executes the following Ansible roles from the [IBM MAS DevOps Collection](https://ibm-mas.github.io/ansible-devops/):

- [`ibm.mas_devops.ibm_catalogs`](https://ibm-mas.github.io/ansible-devops/roles/ibm_catalogs/) - Backs up IBM Operator Catalog definitions
- [`ibm.mas_devops.cert_manager`](https://ibm-mas.github.io/ansible-devops/roles/cert_manager/) - Backs up Certificate Manager configurations
- [`ibm.mas_devops.mongodb`](https://ibm-mas.github.io/ansible-devops/roles/mongodb/) - Backs up MongoDB Community Edition instance and database
- [`ibm.mas_devops.sls`](https://ibm-mas.github.io/ansible-devops/roles/sls/) - Backs up Suite License Service data
- [`ibm.mas_devops.suite_backup`](https://ibm-mas.github.io/ansible-devops/roles/suite_backup/) - Backs up MAS Core configuration
- [`ibm.mas_devops.db2`](https://ibm-mas.github.io/ansible-devops/roles/db2/) - Backs up DB2 resources and persistent volume data
- [`ibm.mas_devops.suite_app_backup`](https://ibm-mas.github.io/ansible-devops/roles/suite_app_backup/) - Backs up MAS application resources and persistent volume data

For detailed information about the underlying Ansible automation, see the [Backup and Restore Playbook Documentation](https://ibm-mas.github.io/ansible-devops/playbooks/backup-restore/).

!!! tip
    Advanced users can use the Ansible roles directly for custom backup workflows. The CLI provides a managed, simplified interface to these roles with additional features like automatic pipeline setup and cloud upload capabilities.

### Backup Artifacts

Backups are stored in the pipeline namespace PVC at:

- **Backup Directory**: `/workspace/backups`

When S3/artifactory upload is enabled, the backup archives will be uploaded to the bucket/artifactory repo under `mas-<instanceid>-backups` directory.

**S3 Backup Archive Directory Structure:**

```
s3://bucket-name/ (or Artfactory - https://na.artifactory.swg-devops.com/artifactory/repo-name/)
├── mas-<instanceid>-backups/
    ├── mas-<instanceid>-backup-<backupversion>-catalog.tar.gz
    ├── mas-<instanceid>-backup-<backupversion>-certmanager.tar.gz
    ├── mas-<instanceid>-backup-<backupversion>-db2u-manage.tar.gz
    ├── mas-<instanceid>-backup-<backupversion>-mongoce.tar.gz
    ├── mas-<instanceid>-backup-<backupversion>-sls.tar.gz
    └── mas-<instanceid>-backup-<backupversion>-suite.tar.gz
    ├── mas-<instanceid>-backup-<backupversion>-app-manage.tar.gz
```

Each backup archive follows the naming convention: `<instance-id>-backup-<timestamp>-<component>.tar.gz`

**Archive Components:**

| Archive | Description |
|---------|-------------|
| `catalog.tar.gz` | IBM Operator Catalog configurations |
| `certmanager.tar.gz` | Certificate Manager configurations |
| `mongoce.tar.gz` | MongoDB Community Edition database backup |
| `sls.tar.gz` | Suite License Service data (if included) |
| `suite.tar.gz` | MAS Core configuration and data |
| `db2u-manage.tar.gz` | Manage Db2 database backup (if included) |
| `app-manage.tar.gz` | Manage application configuration (if included) |

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

- **Installed during restore** - DRO will be installed when restoring from a backup when `--include-dro` is specified
- **Configured externally** - If using an external DRO instance, it should be configured independently
- **Skipped** - DRO installation can be skipped during restore if not required, use `--exclude-dro` to skip DRO installation

!!! info
    DRO backup and restore behavior is managed by the underlying [Ansible DevOps roles](https://ibm-mas.github.io/ansible-devops/playbooks/backup-restore/). The CLI backup command focuses on capturing MAS configuration and data, while DRO is handled during the restore process.

### MongoDB Configuration

The backup process supports **MongoDB Community Edition only**. By default, MongoDB is included in the backup. You can configure MongoDB settings or exclude it if using an external MongoDB provider.

**Including MongoDB in Backup (Default)**

When MongoDB is included, ensure you specify the correct MongoDB configuration:

- **Namespace** - Where MongoDB is deployed (default: `mongoce`)
- **Instance Name** - MongoDB instance identifier (default: `mas-mongo-ce`)
- **Provider** - Must be `community` (only supported provider for backup)

**Excluding MongoDB from Backup**

If you are using an external MongoDB provider (such as IBM Cloud Databases for MongoDB or other hosted MongoDB services), you should exclude MongoDB from the backup:

- Use `--exclude-mongo` flag in non-interactive mode
- In interactive mode, answer "No" when prompted to include MongoDB in backup

!!! warning
    IBM Cloud Databases for MongoDB and other external MongoDB providers are not supported by the backup process. You must use their native backup mechanisms. When using external MongoDB, always use `--exclude-mongo` to skip MongoDB backup.

!!! tip
    When excluding MongoDB from backup, you are responsible for backing up your MongoDB database using your provider's native backup tools. Ensure MongoDB backups are coordinated with MAS backups for consistency.

### Certificate Manager

Specify the certificate manager provider used in your environment:

- **Red Hat Certificate Manager** (`--cert-manager-provider redhat`) - Default option, and the only supported provider.

The backup captures certificate configurations but not the actual certificates, which are regenerated during restore.

### MAS Application Backup

The backup process supports backing up MAS application resources and persistent volume data. Currently supported:

- **Manage Application** - Backs up Manage namespace resources and optionally persistent volume data
- **Facilities Application** - Backs up Facilities namespace resources and optionally persistent volume data

When backing up a Manage or Facilities application, the following resources are included:

**Namespace Resources**:
- Application custom resource (e.g., `ManageApp`, `FacilitiesApp`)
- Workspace custom resource (e.g., `ManageWorkspace`, `FacilitiesWorkspace`)
- Encryption secrets (dynamically determined from Workspace CR)
- Certificates with `mas.ibm.com/instanceId` label
- Subscription and OperatorGroup
- IBM entitlement secret
- All referenced secrets (auto-discovered)

**Persistent Volume Data** (optional, controlled by flags):
- Use `--backup-manage-include-pvc` to include Manage PVC data
- Use `--backup-facilities-include-pvc` to include Facilities PVC data
- All persistent volumes defined in `spec.settings.deployment.persistentVolumes`
- Data backed up as compressed tar.gz archives
- Each PVC's mount path archived separately
- Common PVCs include JMS server data, custom fonts, and attachments

!!! note
    Application backup is optional and configured during the interactive backup process or via command-line parameters (`--backup-manage-app`, `--manage-workspace-id`, `--backup-manage-include-pvc` for Manage; `--backup-facilities-app`, `--facilities-workspace-id`, `--backup-facilities-include-pvc` for Facilities).

### Db2 Database Backup

The backup process supports backing up Db2 databases used by MAS applications. When backing up a Db2 database, the following are included:

**Db2 Instance Resources**:
- `Db2uCluster` custom resource
- Secrets (instance password, certificates, LDAP credentials)
- ConfigMaps
- Services and routes
- Operator subscription

**Database Data**:
- Complete database backup (full backup)
- Stored in the backup archive alongside other components
- Supports both online and offline backup modes

**Backup Types**:

- **Online Backup** - Database remains accessible during backup; requires archive logging enabled
- **Offline Backup** - Database unavailable during backup; works with circular logging (default configuration)

!!! warning
    If your Db2 instance uses circular logging (the default configuration), you **must** use offline backup type. Online backups require archive logging to be enabled via `LOGARCHMETH1` and `LOGARCHMETH2` configuration.

!!! note
    Db2 backup is optional and configured during the interactive backup process or via command-line parameters (`--backup-manage-db`, `--manage-db2-namespace`, `--manage-db2-instance-name`, `--manage-db2-backup-type`).


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

### Scenario 4: External MongoDB Deployment

**Environment:**
- MAS in OpenShift cluster
- MongoDB hosted externally (e.g., IBM Cloud Databases for MongoDB, MongoDB Atlas, or other managed service)
- In-cluster SLS
- Red Hat Certificate Manager

**Backup Command:**
```bash
mas backup \
  --instance-id inst1 \
  --backup-storage-size 30Gi \
  --exclude-mongo \
  --no-confirm
```

Use `--exclude-mongo` to skip backing up MongoDB when it's managed externally. You must use your MongoDB provider's native backup mechanisms to back up the database separately.

!!! important
    When using external MongoDB, coordinate your MongoDB backups with MAS backups to ensure data consistency. Back up MongoDB before or immediately after the MAS backup completes.

### Scenario 5: Backup with S3 Upload

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

### Scenario 6: Backup with Manage Application and Db2 Database

**Environment:**
- Standard MAS deployment with Manage application
- Manage workspace with persistent volumes configured
- In-cluster Db2 database for Manage
- Need to backup application resources, PV data, and database

**Backup Command:**
```bash
mas backup \
  --instance-id inst1 \
  --backup-storage-size 100Gi \
  --backup-manage-app \
  --manage-workspace-id masdev \
  --backup-manage-db \
  --manage-db2-namespace db2u \
  --manage-db2-instance-name mas-inst1-masdev-manage \
  --manage-db2-backup-type offline \
  --no-confirm
```

!!! tip
    When backing up Manage with Db2, ensure sufficient backup storage (100Gi+ recommended) to accommodate application PV data and database backups. Use offline backup type if your Db2 instance uses the default circular logging configuration.

### Scenario 7: Backup with Manage Application Only (External Db2)

**Environment:**
- MAS deployment with Manage application
- External Db2 database (managed separately)
- Only need to backup application resources and PV data

**Backup Command:**
```bash
mas backup \
  --instance-id inst1 \
  --backup-storage-size 50Gi \
  --backup-manage-app \
  --manage-workspace-id masdev \
  --no-confirm
```

!!! note
    When using an external Db2 database, omit the `--backup-manage-db` flag. The database should be backed up separately using your organization's database backup procedures.

### Scenario 8: Backup for Troubleshooting (No Cleanup)

**Environment:**
- Backup for troubleshooting purposes
- Custom backup version desired
- Need to inspect workspace contents after backup
- Workspace cleanup disabled

**Backup Command:**
```bash
mas backup \
  --instance-id inst1 \
  --backup-version debug-$(date +%Y%m%d-%H%M%S) \
  --backup-storage-size 50Gi \
  --no-clean-backup \
  --no-confirm
```

!!! note
    Use `--no-clean-backup` when you need to inspect the backup workspace contents for troubleshooting. Remember to manually clean up the workspaces later to free up storage.

### Scenario 9: Minimal Backup (Skip Pre-Check)

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
| MAS Configuration | < 1 MB | Core MAS custom resources and configurations |
| MongoDB Database | 0.05-20 GB | Varies based on MAS app count and data volume |
| SLS Data | < 1 MB | License server database and configuration |
| IBM Catalogs | < 1 MB | Operator catalog definitions |
| Certificate Manager | < 1 MB | Certificate configurations |
| Manage App Resources | < 10 MB | Manage namespace Kubernetes resources |
| Manage PV Data | 1-100 GB | JMS server, fonts, attachments (if configured) |
| Db2 Instance Resources | < 10 MB | Db2 Kubernetes resources and metadata |
| Db2 Database Backup | Varies | 0.5-2x database size when compressed; depends on data volume |

!!! tip
    Monitor your first backup to determine actual storage requirements, then adjust the `--backup-storage-size` parameter for future backups. When backing up Manage with Db2, plan for significantly larger storage requirements (100GB+ recommended).

### Storage Class Considerations

The backup process automatically selects appropriate storage:

- **Single Node OpenShift (SNO)**: Uses ReadWriteOnce (RWO) storage
- **Multi-node clusters**: Prefers ReadWriteMany (RWX) storage when available
- Falls back to RWO if RWX is not available

The storage class is determined from your cluster's storage classes.

You can override the default storage configuration using:

- `--backup-storage-class`: Specify a custom storage class for the backup PVC
- `--backup-storage-access-mode`: Specify the access mode (e.g., ReadWriteOnce, ReadWriteMany) for the backup PVC


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
8. **Database Backup** (optional) - Backs up Db2 instance and database:
   - Db2 instance resources backup
   - Db2 database backup (online or offline)
9. **Application Backup** (optional) - Backs up MAS application resources and persistent volumes:
   - Manage namespace resources backup
   - Manage persistent volume data backup
10. **Archive Creation** - Compresses backup into tar.gz archives for each component
11. **Upload** (optional) - Uploads archives to S3 or Artifactory
12. **Workspace Cleanup** (optional, default: enabled) - Cleans backup and config workspaces to free up storage

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

### Workspace Cleanup

By default, the backup pipeline automatically cleans the workspace directories after backup completion to free up storage space. This cleanup occurs in the pipeline's `finally` block, ensuring it runs regardless of backup success or failure.

**To disable workspace cleanup:**

- **Interactive mode**: Answer "No" when prompted about cleaning workspaces
- **Non-interactive mode**: Use the `--no-clean-backup` flag

**When to disable cleanup:**

- Troubleshooting backup issues and need to inspect workspace contents
- Running multiple backups in sequence and want to preserve intermediate files
- Custom post-backup processing that requires access to workspace files

!!! tip
    Workspace cleanup is recommended for production backups to prevent PVC storage exhaustion. Only disable it when you have a specific need to inspect or process the workspace contents.


Best Practices
-------------------------------------------------------------------------------

### Backup Strategy

1. **Regular Schedule** - Implement automated backups on a regular schedule
2. **Version Naming** - Use descriptive backup versions (e.g., `prod-20240315-pre-upgrade`)
3. **Retention Policy** - Define how long to keep backups based on compliance requirements
4. **Off-site Storage** - Upload backups to S3 or Artifactory for disaster recovery
5. **Test Restores** - Periodically test restore procedures in non-production environments
6. **Document Configuration** - Keep records of custom configurations and dependencies
7. **Application Backups** - Include Manage application and Db2 database in regular backup schedule
8. **Coordinate Backups** - When backing up Manage, always include the Db2 database for consistency
9. **Storage Planning** - Allocate sufficient backup storage when including applications and databases (100Gi+ recommended)

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
  -v ~:/mnt/home \
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

**Issue: "Manage application backup failed"**

- Verify Manage workspace ID is correct
- Ensure ManageWorkspace CR exists in the cluster
- Check that Manage pods are running and healthy
- Verify persistent volumes are properly configured in ManageWorkspace CR
- Ensure sufficient storage space in backup PVC

**Issue: "Db2 backup failed"**

- Verify Db2 namespace and instance name are correct
- Ensure Db2 instance is running and accessible
- Check backup type matches Db2 logging configuration (use offline for circular logging)
- Verify sufficient storage space in Db2 backup PVC
- Review Db2 pod logs for database-specific errors

**Issue: "Manage persistent volume backup is slow"**

- PV backup duration depends on data volume
- Large JMS server or attachment PVCs can take significant time
- Monitor backup progress in Tekton pipeline logs
- Consider scheduling backups during maintenance windows
- Ensure network bandwidth is sufficient for data transfer
