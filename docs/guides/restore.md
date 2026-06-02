# Restore
The MAS restore process uses Tekton pipelines to orchestrate the restoration of MAS instances from backup archives. The restore operation can recover a complete MAS environment or selectively restore components based on your requirements. The restore process provides extensive configuration flexibility, allowing you to modify key settings during restoration such as domain names, SLS/DRO URLs, and storage classes.

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


Restore Overview
-------------------------------------------------------------------------------
### Restore Components

The restore process handles the following components:

- **IBM Operator Catalogs** - Restores catalog source definitions
- **Certificate Manager** - Restores certificate configurations (RedHat only)
- **MongoDB** - Restores MongoDB instance with SLS & MAS databases (Community Edition only)
- **Suite License Service (SLS)** - Restores SLS instance with license server data (optional, can use external SLS)
- **MAS Suite Configuration** - Restores core MAS instance configuration and custom resources
- **Suite-level SLSCfg** - Restores or provides custom Suite-level SLS configuration with optional URL override
- **Suite-level BASCfg/DROCfg** - Restores or provides custom Suite-level DRO/BAS configuration with optional URL override
- **Manage Database** - Optionally restores incluster Db2 database associated with Manage workspace
- **Manage Application** - Optionally restores Manage application namespace resources and persistent volume data
- **Grafana** - Optionally installs Grafana for monitoring (not part of backup)
- **Data Reporter Operator (DRO)** - Optionally installs DRO (not part of backup), when DRO is installed, an auto-generated Suite-level BASCfg CR will be applied automatically.

### Restore Limitations

!!! warning
    Be aware of the following limitations before performing a restore:

- **Restoring from S3 or Artifactory Only** - When using the pipeline, the restore process is limited to restoring from S3 or Artifactory. Restoring from a local backup file is not supported yet.
- **MongoDB Community Edition only** - Restore supports only in-cluster MongoDB Community Edition. Restoring to an external or enterprise MongoDB deployment is not supported.
- **Db2 standalone operator only** - The restore process supports only the in-cluster standalone Db2 operator. Other Db2 operator implementations are not included.
- **Db2uInstance not supported, only Db2uCluster** - The restore process does not support Db2uInstance for now. Will be supported in future release.
- **Certificate Manager (RedHat only)** - Certificate Manager restore is supported only for RedHat Certificate Manager. Other implementations are not handled during restore.
- **Same MAS version required** - Restoring a backup to a cluster running a different MAS version may result in incompatibilities. It is strongly recommended to restore to the same MAS version as the backup source.
- **Same MAS Instance ID required** - It is strongly recommended to restore to the same MAS instance ID as the backup source.
- **Manage application only for app restore** - Only the Manage application is supported. Other MAS applications will be supported in future releases.
- **Tekton pipeline dependency** - The restore process requires Tekton pipelines to be available and functional on the target cluster.
- **Target cluster must be pre-provisioned** - The restore process does not provision a new OpenShift cluster. A running, accessible cluster with sufficient resources must already exist.
- **Storage class compatibility** - The target cluster must have compatible storage classes. If storage classes differ from the source cluster, overrides must be explicitly configured.
- **No partial component restore** - Individual components cannot be selectively restored in isolation without running the full pipeline; component selection is configured at pipeline launch time.
- **Manual Certificate Management Restriction:** Certificates and secrets from backups will be restored. However, changing the domain during the restoration process will cause issues with manual certificates/secrets, and manual updates of certificates and secrets are required.
- **Domain changes require DNS updates** - If restoring with a domain change, DNS records and TLS certificates must be updated manually outside of the restore process.
- **Single MAS instance per restore** - Each restore operation targets a single MAS instance. Restoring multiple instances requires separate restore runs.
- **Grafana and DRO are not restored from backup** - Grafana and DRO are optionally installed fresh during restore; their previous configurations are not recovered from the backup archive. However, Suite-level BASCFG CR resource is backed up and can be restored.
- **No support for CP4D** - The restore process does not support restoring CP4D environments.

!!! tip
    We are working on reducing the limitations of the restore process and will be adding new capabilties and support for other MAS applications in future releases.

### Configuration Flexibility

The restore process supports several configuration overrides to adapt the restored environment to new infrastructure:

- **Domain Configuration** - Change the MAS domain in the Suite CR during restore
- **SLS Configuration** - Restore Suite-level SLSCfg from backup or provide custom configuration file, with optional SLS URL override
- **DRO/BAS Configuration** - Restore Suite-level BASCfg from backup or provide custom configuration file, with optional DRO URL override
- **Storage Class Override** - Override storage classes for all components (MongoDB, Manage app, Manage DB) when restoring to clusters with different storage providers
- **SLS Domain Override** - Change the SLS domain used in the License Service CR
- **Backup Download** - Download backup archives from S3 or Artifactory before restore (useful for cross-cluster restores)

### Backup Archive Management

The restore process can work with backup archives in multiple ways:

- **Local Backup** - Restore from backup archives already present in the cluster
- **S3 Download** - Download backup archives from S3-compatible storage before restore
- **Artifactory Download** - Download backup archives from Artifactory (development mode only)
- **Custom Archive Names** - Support for custom backup archive naming conventions
- **Automatic Cleanup** - Optional cleanup of downloaded archives after successful restore

When downloading from S3 or Artifactory, the `download_backup_archive` role selectively downloads only the archives required for the restore operation. The following archive selection parameters control which archives are downloaded:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `include_mongo_archive` | `false` | Download the Mongo backup archive |
| `include_sls_archive` | `false` | Download the SLS backup archive |
| `include_manage_db_archive` | `false` | Download the Manage Db2 database backup archive |
| `include_manage_app_archive` | `false` | Download the Manage application backup archive |

These parameters are automatically set by the restore pipeline based on the restore configuration (e.g. `--restore-manage-app`, `--restore-manage-db`, `--include-sls`), so you do not need to set them manually when using the `mas restore` command.

### Ansible DevOps Integration

The `mas restore` command launches a Tekton pipeline that executes the following Ansible roles from the [IBM MAS DevOps Collection](https://ibm-mas.github.io/ansible-devops/):

- [`ibm.mas_devops.ibm_catalogs`](https://ibm-mas.github.io/ansible-devops/roles/ibm_catalogs/) - Restores IBM Operator Catalog definitions
- [`ibm.mas_devops.cert_manager`](https://ibm-mas.github.io/ansible-devops/roles/cert_manager/) - Restores Certificate Manager configurations
- [`ibm.mas_devops.mongodb`](https://ibm-mas.github.io/ansible-devops/roles/mongodb/) - Restores MongoDB Community Edition instance and database
- [`ibm.mas_devops.sls`](https://ibm-mas.github.io/ansible-devops/roles/sls/) - Restores Suite License Service data
- [`ibm.mas_devops.suite_restore`](https://ibm-mas.github.io/ansible-devops/roles/suite_restore/) - Restores MAS Core configuration
- [`ibm.mas_devops.db2`](https://ibm-mas.github.io/ansible-devops/roles/db2/) - Restores Db2u instance and database
- [`ibm.mas_devops.suite_app_restore`](https://ibm-mas.github.io/ansible-devops/roles/suite_app_restore/) - Restores supported MAS Application configuration
- [`ibm.mas_devops.grafana`](https://ibm-mas.github.io/ansible-devops/roles/grafana/) - Installs Grafana (optional)
- [`ibm.mas_devops.dro`](https://ibm-mas.github.io/ansible-devops/roles/dro/) - Installs Data Reporter Operator (optional)


Restore Modes
-------------------------------------------------------------------------------

### Interactive Mode

Interactive mode guides you through the restore process with prompts for all required configuration. This is the recommended approach for manual restores.

```bash
docker run -ti --rm quay.io/ibmmas/cli mas restore
```

The interactive session will:

1. Prompt for OpenShift cluster connection
2. Request MAS instance ID (must match backup)
3. Request backup version to restore
4. Configure MongoDB storage class override
5. Configure Grafana installation
6. Configure SLS restoration
7. Configure DRO installation
8. Configure MAS domain settings
9. Configure SLS and DRO configuration options
10. Configure Manage application restore
11. Configure Manage Db2 restore
12. Request backup storage size
13. Offer optional download from S3 or Artifactory

### Non-Interactive Mode

Non-interactive mode is ideal for automation, scheduled restores, and CI/CD pipelines. All required parameters must be provided via command-line arguments.

```bash
docker run -ti --rm quay.io/ibmmas/cli mas restore \
  --instance-id inst1 \
  --restore-version 20260117-191701 \
  --no-confirm
```


Restore Process Details
-------------------------------------------------------------------------------

### Pipeline Execution

When you run `mas restore`, the following occurs:

1. **Validation** - Verifies cluster connectivity and prerequisites
2. **Namespace Preparation** - Creates/updates `mas-{instance-id}-pipelines` namespace
3. **OpenShift Pipelines** - Validates or installs OpenShift Pipelines Operator
4. **PVC Creation** - Provisions persistent volume for backup storage
5. **Tekton Pipeline Launch** - Submits PipelineRun with configured parameters
6. **Pre-Restore Check** - Validates cluster readiness
7. **Download** (optional) - Downloads backup archive from S3 or Artifactory
8. **Component Restore** - Executes restore tasks in sequence:
   - IBM Catalogs restore
   - Certificate Manager restore
   - Grafana installation (if enabled)
   - MongoDB restore (with optional storage class override)
   - SLS restore (if included)
   - DRO installation (if enabled)
9. **Suite Restore** - Restores MAS core configuration with optional domain/URL overrides
10. **Manage Application Restore** (if enabled) - Restores Manage application and database
11. **Post-Restore Verification** - Validates restored MAS instance
12. **Workspace Cleanup** (optional, default: enabled) - Cleans backup and config workspaces

### Monitoring Progress

After launching the restore, a URL to the Tekton PipelineRun is displayed:

```
View progress:
  https://console-openshift-console.apps.cluster.example.com/k8s/ns/mas-inst1-pipelines/tekton.dev~v1beta1~PipelineRun/mas-restore-20260117-191701-YYMMDD-HHMM
```

Use this URL to:

- Monitor real-time restore progress
- View logs from individual restore tasks
- Troubleshoot any failures
- Verify successful completion

### Configuration Flexibility

The restore process provides several options for handling configurations:

#### MAS Domain Configuration
- **From Backup** (default) - Uses the domain stored in the Suite backup
- **Override** - Specify `--mas-domain-restore` to change the domain during restore

#### SLS Configuration
- **From Backup** (default) - Restores SLSCfg from backup with `--include-slscfg-from-backup`
- **Custom File** - Use `--exclude-slscfg-from-backup` and provide `--sls-cfg-file`
- **Change URL** - Use `--sls-url-restore` to modify the SLS URL while keeping other configuration

#### DRO Configuration
- **From Backup** (default) - Restores BASCfg from backup with `--include-drocfg-from-backup`
- **Custom File** - Use `--exclude-drocfg-from-backup` and provide `--dro-cfg-file`
- **Change URL** - Use `--dro-url-restore` to modify the DRO URL while keeping other configuration


Restore Scenarios - Non-Interactive Mode
-------------------------------------------------------------------------------

### Scenario 1: Basic Restore from Local Backup

**Environment:**
- Backup archive already present in the cluster PVC
- Standard restore with all defaults

**Restore Command:**
```bash
mas restore \
  --instance-id inst1 \
  --restore-version 20260117-191701 \
  --no-confirm
```

### Scenario 2: Restore with S3 Download

**Environment:**
- Backup stored in AWS S3
- Need to download before restore

**Restore Command:**
```bash
mas restore \
  --instance-id inst1 \
  --restore-version 20260117-191701 \
  --download-backup \
  --aws-access-key-id AKIAIOSFODNN7EXAMPLE \ #pragma: allowlist secret
  --aws-secret-access-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY \ #pragma: allowlist secret
  --s3-bucket-name mas-backups-prod \
  --s3-region us-east-1 \
  --no-confirm
```

### Scenario 3: Restore with Domain Change

**Environment:**
- Restoring to a different cluster with new domain
- Need to update MAS domain

**Restore Command:**
```bash
mas restore \
  --instance-id inst1 \
  --restore-version 20260117-191701 \
  --mas-domain-restore new-cluster.example.com \
  --no-confirm
```

### Scenario 4: Restore with External SLS

**Environment:**
- Using external SLS instance
- Skip SLS restore but provide custom SLS configuration

**Restore Command:**
```bash
mas restore \
  --instance-id inst1 \
  --restore-version 20260117-191701 \
  --exclude-sls \
  --exclude-slscfg-from-backup \
  --sls-cfg-file /path/to/custom-sls-config.yaml \
  --no-confirm
```

### Scenario 5: Restore with SLS URL Override

**Environment:**
- Restore SLS from backup but change the URL
- SLS moved to different endpoint

**Restore Command:**
```bash
mas restore \
  --instance-id inst1 \
  --restore-version 20260117-191701 \
  --include-sls \
  --include-slscfg-from-backup \
  --sls-url-restore https://new-sls.example.com \
  --no-confirm
```

### Scenario 6: Restore with DRO Installation

**Environment:**
- Install new DRO instance during restore
- Provide DRO configuration details

**Restore Command:**
```bash
mas restore \
  --instance-id inst1 \
  --restore-version 20260117-191701 \
  --include-dro \
  --ibm-entitlement-key YOUR_ENTITLEMENT_KEY \ #pragma: allowlist secret
  --contact-email admin@example.com \
  --contact-firstname John \
  --contact-lastname Doe \
  --dro-namespace redhat-marketplace \
  --no-confirm
```

### Scenario 7: Restore Without Grafana

**Environment:**
- Skip Grafana installation
- Monitoring not required

**Restore Command:**
```bash
mas restore \
  --instance-id inst1 \
  --restore-version 20260117-191701 \
  --exclude-grafana \
  --no-confirm
```

### Scenario 8: Complete Restore with All Options

**Environment:**
- Download from S3
- Change domain and SLS URL
- Install DRO and Grafana
- Custom storage size

**Restore Command:**
```bash
mas restore \
  --instance-id inst1 \
  --restore-version 20260117-191701 \
  --backup-storage-size 100Gi \
  --mas-domain-restore new-cluster.example.com \
  --include-sls \
  --include-slscfg-from-backup \
  --sls-url-restore https://new-sls.example.com \
  --include-drocfg-from-backup \
  --dro-url-restore https://new-dro.example.com \
  --include-grafana \
  --include-dro \
  --ibm-entitlement-key YOUR_ENTITLEMENT_KEY \ #pragma: allowlist secret
  --contact-email admin@example.com \
  --contact-firstname John \
  --contact-lastname Doe \
  --dro-namespace redhat-marketplace \
  --download-backup \
  --aws-access-key-id AKIAIOSFODNN7EXAMPLE \ #pragma: allowlist secret
  --aws-secret-access-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY \ #pragma: allowlist secret
  --s3-bucket-name mas-backups-prod \
  --s3-region us-east-1 \
  --no-confirm
```

### Scenario 9: Restore for Troubleshooting (No Cleanup)

**Environment:**
- Need to inspect workspace contents after restore
- Workspace cleanup disabled

**Restore Command:**
```bash
mas restore \
  --instance-id inst1 \
  --restore-version 20260117-191701 \
  --no-clean-backup \
  --no-confirm
```

!!! note
    Use `--no-clean-backup` when you need to inspect the restore workspace contents for troubleshooting. Remember to manually clean up the workspaces later to free up storage.

### Scenario 10: Emergency Restore (Skip Pre-Check)

**Environment:**
- Emergency restore scenario
- Skip pre-restore validation for speed

**Restore Command:**
```bash
mas restore \
  --instance-id inst1 \
  --restore-version 20260117-191701 \
  --skip-pre-check \
  --no-confirm
```

!!! warning
    Use `--skip-pre-check` only in emergency situations. Pre-restore checks validate cluster readiness and can prevent restore failures.

### Scenario 11: Restore with MongoDB Storage Class Override

**Environment:**
- Restoring to a cluster with different storage classes
- Need to override MongoDB storage class

**Restore Command:**
```bash
mas restore \
  --instance-id inst1 \
  --restore-version 20260117-191701 \
  --override-mongodb-storageclass \
  --mongodb-storageclass-name custom-rwo-storage \
  --no-confirm
```

### Scenario 12: Restore with Manage Application

**Environment:**
- Need to restore Manage application in addition to MAS Suite
- Restore Manage namespace resources and persistent volume data

**Restore Command:**
```bash
mas restore \
  --instance-id inst1 \
  --restore-version 20260117-191701 \
  --restore-manage-app \
  --no-confirm
```

### Scenario 13: Restore with Manage Application and Database

**Environment:**
- Restore both Manage application and its incluster Db2 database
- Complete Manage workspace restoration

**Restore Command:**
```bash
mas restore \
  --instance-id inst1 \
  --restore-version 20260117-191701 \
  --restore-manage-app \
  --restore-manage-db \
  --no-confirm
```

!!! warning
    Manage database restore is an offline operation. The Manage application will be unavailable during the restore process.

### Scenario 14: Restore Manage with Custom Storage Classes

**Environment:**
- Restoring to a cluster with different storage infrastructure
- Need to override storage classes for both Manage app and Db2

**Restore Command:**
```bash
mas restore \
  --instance-id inst1 \
  --restore-version 20260117-191701 \
  --restore-manage-app \
  --restore-manage-db \
  --override-manage-app-storageclass \
  --manage-app-storage-class-rwx custom-rwx-storage \
  --manage-app-storage-class-rwo custom-rwo-storage \
  --override-manage-db-storageclass \
  --manage-db-storage-class-rwx custom-rwx-storage \
  --manage-db-storage-class-rwo custom-rwo-storage \
  --no-confirm
```

!!! note
    The Manage Db2 storage class override now uses a single ReadWriteMany (`--manage-db-storage-class-rwx`) and ReadWriteOnce (`--manage-db-storage-class-rwo`) storage class, applied across all Db2 persistent volumes based on the access modes. The previous per-volume flags (`--manage-db-meta-storage-class`, `--manage-db-data-storage-class`, `--manage-db-backup-storage-class`, `--manage-db-logs-storage-class`, `--manage-db-temp-storage-class`) have been removed.

### Scenario 15: Complete Restore with MongoDB Override and Manage

**Environment:**
- Comprehensive restore with all new features
- Override MongoDB storage class
- Restore Manage application and database
- Download from S3

**Restore Command:**
```bash
mas restore \
  --instance-id inst1 \
  --restore-version 20260117-191701 \
  --backup-storage-size 100Gi \
  --override-mongodb-storageclass \
  --mongodb-storageclass-name custom-rwo-storage \
  --restore-manage-app \
  --restore-manage-db \
  --override-manage-db-storageclass \
  --manage-db-storage-class-rwx custom-rwx-storage \
  --manage-db-storage-class-rwo custom-rwo-storage \
  --download-backup \
  --aws-access-key-id AKIAIOSFODNN7EXAMPLE \ #pragma: allowlist secret
  --aws-secret-access-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY \ #pragma: allowlist secret
  --s3-bucket-name mas-backups-prod \
  --s3-region us-east-1 \
  --no-confirm
```


Restore Best Practices
-------------------------------------------------------------------------------

### Pre-Restore Checklist

1. **Verify Backup Integrity** - Ensure backup archives are complete and accessible
2. **Check Cluster Resources** - Verify sufficient CPU, memory, and storage
3. **Review Target Environment** - Confirm cluster version and configuration compatibility
4. **Plan Domain Changes** - Determine if domain or URL changes are needed
5. **Prepare External Services** - Ensure external SLS/DRO are accessible if used
6. **Review Storage Classes** - Identify if MongoDB or Manage storage class overrides are needed
7. **Plan Manage Restore** - Determine if Manage application and database should be restored
8. **Document Configuration** - Record any custom configurations or overrides

### During Restore

1. **Monitor Pipeline** - Watch the Tekton PipelineRun for any issues
2. **Check Logs** - Review task logs if any failures occur
3. **Verify Components** - Ensure each component restores successfully
4. **Note Timing** - Track restore duration for future planning

### Post-Restore Verification

1. **Validate Suite Status** - Confirm MAS Suite CR is ready
2. **Check Application Access** - Verify MAS applications are accessible
3. **Test Integrations** - Validate connections to databases and external services
4. **Verify MongoDB** - Confirm MongoDB is running with correct storage class if overridden
5. **Validate Manage Application** - If restored, verify Manage application is accessible and functional
6. **Check Manage Database** - If restored, confirm Db2 database is running with correct storage classes
7. **Review Configurations** - Confirm all configurations are correct
8. **Update DNS** - Update DNS records if domain changed
9. **Test Functionality** - Perform smoke tests on critical functions

### Common Restore Scenarios

#### Disaster Recovery
- Use latest backup from off-site storage
- May require domain and URL changes
- Verify all external dependencies are available
- Consider MongoDB storage class override if infrastructure changed
- Include Manage application and database restore if needed

#### Cluster Migration
- Download backup from source cluster storage
- Change domain to match new cluster
- Update SLS and DRO URLs if needed
- Override MongoDB and Manage storage classes for different infrastructure
- Verify network connectivity and routes
- Plan for Manage database downtime during restore

#### Environment Cloning
- Use production backup for dev/test
- Change domain to avoid conflicts
- Consider using external SLS to share licenses
- May exclude DRO for non-production environments
- Override storage classes to use lower-cost storage in non-production
- Optionally restore Manage application for testing


Restore Troubleshooting
-------------------------------------------------------------------------------

### Common Restore Issues

**Issue: "Backup archive not found"**

- Verify backup archive exists in PVC or download location
- Check backup version matches the archive name
- Ensure download credentials are correct if downloading from S3/Artifactory

**Issue: "Pre-restore check failed"**

- Review cluster resource availability
- Check OpenShift version compatibility
- Verify required operators are available
- Use `--skip-pre-check` only if necessary

**Issue: "MongoDB restore failed"**

- Verify MongoDB namespace and instance name match backup
- Ensure sufficient storage for MongoDB data
- Check MongoDB operator is installed and ready
- If using storage class override, verify the storage class exists and is accessible
- Ensure the specified storage class supports ReadWriteOnce access mode

**Issue: "SLS restore failed"**

- Verify SLS namespace is correct
- Check if using `--include-sls` or `--exclude-sls` appropriately
- Ensure SLS configuration file is valid if using custom config

**Issue: "Suite restore failed with domain mismatch"**

- Use `--mas-domain-restore` to override domain from backup
- Verify DNS records are updated for new domain
- Check certificate configurations match new domain

**Issue: "DRO installation failed"**

- Verify IBM entitlement key is valid
- Check DRO namespace has sufficient permissions
- Ensure contact information is provided correctly

**Issue: "Download from S3 failed"**

- Verify AWS credentials are correct
- Check S3 bucket exists and is accessible
- Verify network connectivity to AWS
- Ensure IAM permissions allow GetObject operations

**Issue: "Configuration file not found"**
**Issue: "Manage application restore failed"**

- Verify Manage workspace exists in the backup
- Ensure sufficient storage for Manage application persistent volumes
- Check that storage class overrides (if specified) are valid and accessible
- Verify both ReadWriteMany and ReadWriteOnce storage classes are available if using overrides
- Review Manage namespace for any conflicting resources

**Issue: "Manage Db2 database restore failed"**

- Verify Db2 instance exists in the backup
- Ensure sufficient storage for all Db2 persistent volumes (meta, data, backup, logs, temp)
- Check that all specified storage classes exist and support required access modes
- Verify Db2 operator is installed and ready
- Review Db2 pod logs for specific error messages
- Note: Db2 restore is an offline operation - ensure no active connections during restore

**Issue: "Storage class not found during restore"**

- Verify the specified storage class exists in the target cluster: `oc get storageclass`
- Check storage class supports the required access mode (RWO or RWX)
- If using cluster defaults, ensure default storage classes are configured
- Review storage class provisioner compatibility with the cluster infrastructure


- Verify custom config file paths are correct
- Ensure files are accessible from the CLI container
- Check file format is valid YAML
