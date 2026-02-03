Backup
===============================================================================

Usage
-------------------------------------------------------------------------------
Usage information can be obtained using `mas backup --help`

```
usage: mas backup [-i MAS_INSTANCE_ID] [--backup-version BACKUP_VERSION] [--backup-storage-size BACKUP_STORAGE_SIZE]
                  [--clean-backup] [--no-clean-backup] [--upload-backup] [--aws-access-key-id AWS_ACCESS_KEY_ID]
                  [--aws-secret-access-key AWS_SECRET_ACCESS_KEY] [--s3-bucket-name S3_BUCKET_NAME] [--s3-region S3_REGION]
                  [--artifactory-url ARTIFACTORY_URL] [--artifactory-repository ARTIFACTORY_REPOSITORY] [--include-sls]
                  [--exclude-sls] [--mongodb-namespace MONGODB_NAMESPACE] [--mongodb-instance-name MONGODB_INSTANCE_NAME]
                  [--mongodb-provider {community}] [--sls-namespace SLS_NAMESPACE] [--cert-manager-provider {redhat,ibm}]
                  [--artifactory-username ARTIFACTORY_USERNAME] [--artifactory-token ARTIFACTORY_TOKEN] [--dev-mode] [--no-confirm]
                  [--skip-pre-check] [-h]

IBM Maximo Application Suite Admin CLI v18.10.0
Backup a MAS instance by configuring and launching the MAS Backup Tekton Pipeline.

Interactive Mode:
Omitting the --instance-id option will trigger an interactive prompt

MAS Instance:
  -i, --instance-id MAS_INSTANCE_ID
                        MAS Instance ID to backup

Backup Configuration:
  --backup-version BACKUP_VERSION
                        Version/timestamp for the backup (auto-generated if not provided)
  --backup-storage-size BACKUP_STORAGE_SIZE
                        Size of the backup PVC storage (default: 20Gi)
  --clean-backup        Clean backup and config workspaces after completion (default: true)
  --no-clean-backup     Do not clean backup and config workspaces after completion

Upload Configuration:
  --upload-backup       Upload the backup archive after completion
  --aws-access-key-id AWS_ACCESS_KEY_ID
                        AWS Access Key ID for S3 upload
  --aws-secret-access-key AWS_SECRET_ACCESS_KEY
                        AWS Secret Access Key for S3 upload
  --s3-bucket-name S3_BUCKET_NAME
                        S3 bucket name for backup upload
  --s3-region S3_REGION
                        AWS region for S3 bucket
  --artifactory-url ARTIFACTORY_URL
                        Artifactory URL for backup upload (dev-mode only)
  --artifactory-repository ARTIFACTORY_REPOSITORY
                        Artifactory repository for backup upload (dev-mode only)

Components:
  --include-sls         Include SLS in backup (default: true)
  --exclude-sls         Exclude SLS from backup (use if SLS is external)

Dependencies Configuration:
  --mongodb-namespace MONGODB_NAMESPACE
                        MongoDB namespace (default: mongoce)
  --mongodb-instance-name MONGODB_INSTANCE_NAME
                        MongoDB instance name to backup (default: mas-mongo-ce)
  --mongodb-provider {community}
                        MongoDB provider (only community is supported for backup)
  --sls-namespace SLS_NAMESPACE
                        SLS namespace (default: ibm-sls)
  --cert-manager-provider {redhat,ibm}
                        Certificate manager provider (default: redhat)

More:
  --artifactory-username ARTIFACTORY_USERNAME
                        Username for access to development builds on Artifactory (dev-mode only)
  --artifactory-token ARTIFACTORY_TOKEN
                        API Token for access to development builds on Artifactory (dev-mode only)
  --dev-mode            Configure backup for development mode
  --no-confirm          Launch the backup without prompting for confirmation
  --skip-pre-check      Skips the 'pre-backup-check' task in the backup pipeline
  -h, --help            Show this help message and exit
```

Examples
-------------------------------------------------------------------------------

### Interactive Backup
Launch an interactive backup session that will prompt you for all required configuration:

```bash
mas backup
```

### Non-Interactive Backup with Minimal Configuration
Backup a specific MAS instance with default settings:

```bash
mas backup --instance-id inst1 --no-confirm
```

### Backup with Custom Storage Size
Specify a custom storage size for the backup PVC:

```bash
mas backup --instance-id inst1 --backup-storage-size 50Gi --no-confirm
```

### Backup with Custom Version
Set a custom backup version identifier:

```bash
mas backup --instance-id inst1 --backup-version 1.0.0 --no-confirm
```

### Backup with S3 Upload
Create a backup and automatically upload it to an S3 bucket:

```bash
mas backup \
  --instance-id inst1 \
  --upload-backup \
  --aws-access-key-id AKIAIOSFODNN7EXAMPLE \ #pragma: allowlist secret
  --aws-secret-access-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY \ #pragma: allowlist secret
  --s3-bucket-name my-mas-backups \
  --s3-region us-east-1 \
  --no-confirm
```

### Backup Excluding SLS
Create a backup without including Suite License Service (useful when SLS is external):

```bash
mas backup --instance-id inst1 --exclude-sls --no-confirm
```

### Backup with Custom MongoDB Configuration
Specify custom MongoDB settings:

```bash
mas backup \
  --instance-id inst1 \
  --mongodb-namespace my-mongo \
  --mongodb-instance-name my-mongo-instance \
  --mongodb-provider community \
  --no-confirm
```

### Backup with Custom SLS Configuration
Specify a custom SLS namespace:

```bash
mas backup \
  --instance-id inst1 \
  --sls-namespace my-sls \
  --no-confirm
```


### Backup Skipping Pre-Check
Skip the pre-backup validation check (use with caution):

```bash
mas backup --instance-id inst1 --skip-pre-check --no-confirm
```

### Backup Without Workspace Cleanup
Keep backup and config workspace contents after completion (useful for troubleshooting):

```bash
mas backup --instance-id inst1 --no-clean-backup --no-confirm
```

!!! note
    By default, workspaces are cleaned after backup completion to free up storage. Use `--no-clean-backup` only when you need to inspect the workspace contents for troubleshooting purposes.

### Complete Non-Interactive Backup Example
A comprehensive example with all major options configured:

```bash
mas backup \
  --instance-id inst1 \
  --backup-version 20240315-prod \
  --backup-storage-size 100Gi \
  --include-sls \
  --mongodb-namespace mongoce \
  --mongodb-instance-name mas-mongo-ce \
  --mongodb-provider community \
  --sls-namespace ibm-sls \
  --cert-manager-provider redhat \
  --upload-backup \
  --aws-access-key-id AKIAIOSFODNN7EXAMPLE \ #pragma: allowlist secret
  --aws-secret-access-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY \ #pragma: allowlist secret
  --s3-bucket-name my-mas-backups \
  --s3-region us-east-1 \
  --no-confirm
```

Notes
-------------------------------------------------------------------------------

### Backup Process
The backup command performs the following operations:

1. **Validates the target cluster** - Ensures OpenShift cluster connectivity and checks for MAS instances
2. **Prepares the pipeline namespace** - Creates or updates the `mas-{instance-id}-pipelines` namespace
3. **Installs OpenShift Pipelines** - Validates or installs the OpenShift Pipelines Operator
4. **Creates backup PVC** - Provisions persistent storage for the backup data
5. **Launches the backup pipeline** - Submits a Tekton PipelineRun to perform the backup
6. **Optionally uploads the backup** - If configured, uploads the backup archive to S3 or Artifactory

### Default Values
If not specified, the following defaults are used:

- **Backup Storage Size**: `20Gi`
- **Backup Version**: Auto-generated timestamp in format `YYYYMMDD-HHMMSS`
- **Clean Workspaces**: `true` (workspaces are cleaned after completion)
- **MongoDB Namespace**: `mongoce`
- **MongoDB Instance Name**: `mas-mongo-ce`
- **MongoDB Provider**: `community`
- **SLS Namespace**: `ibm-sls`
- **Certificate Manager Provider**: `redhat`
- **Include SLS**: `true`

### Storage Requirements
Ensure sufficient storage is available for the backup PVC. The required size depends on:

- Size of MAS configuration data
- Size of MongoDB database
- Size of SLS data (if included)
- Any additional application data

### Upload Destinations
Two upload destinations are supported:

- **S3**: Standard AWS S3 bucket upload (available in all modes)
- **Artifactory**: Artifactory repository upload (requires `--dev-mode`)

### Interactive Mode
When running without `--instance-id`, the command enters interactive mode and will prompt for:

1. Target OpenShift cluster connection
2. MAS instance selection (if multiple instances exist)
3. Backup storage size
4. Backup version (or auto-generate)
5. Workspace cleanup preference
6. Upload configuration (optional)

#### Example Interactive Mode Output

![backup-cmd](../img/backup-cmd.png)


### Pipeline Monitoring
After launching the backup, a URL to the Tekton PipelineRun will be displayed. Use this URL to monitor the backup progress in the OpenShift Console.