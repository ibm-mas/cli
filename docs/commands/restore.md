Restore
===============================================================================

Usage
-------------------------------------------------------------------------------
Usage information can be obtained using `mas restore --help`

```
usage: mas restore [-i MAS_INSTANCE_ID] [--restore-version RESTORE_VERSION] [--backup-storage-size BACKUP_STORAGE_SIZE]
                   [--mas-domain-restore MAS_DOMAIN_ON_RESTORE] [--sls-url-restore SLS_URL_ON_RESTORE]
                   [--dro-url-restore DRO_URL_ON_RESTORE] [--include-slscfg-from-backup] [--exclude-slscfg-from-backup]
                   [--sls-cfg-file SLS_CFG_FILE] [--dro-cfg-file DRO_CFG_FILE] [--include-drocfg-from-backup]
                   [--exclude-drocfg-from-backup] [--clean-backup] [--no-clean-backup] [--download-backup]
                   [--aws-access-key-id AWS_ACCESS_KEY_ID] [--aws-secret-access-key AWS_SECRET_ACCESS_KEY]
                   [--s3-bucket-name S3_BUCKET_NAME] [--s3-region S3_REGION] [--artifactory-url ARTIFACTORY_URL]
                   [--artifactory-repository ARTIFACTORY_REPOSITORY] [--custom-backup-archive-name BACKUP_ARCHIVE_NAME]
                   [--include-grafana] [--exclude-grafana] [--include-dro] [--exclude-dro] [--include-sls] [--exclude-sls]
                   [--sls-domain SLS_DOMAIN] [--ibm-entitlement-key IBM_ENTITLEMENT_KEY] [--contact-email DRO_CONTACT_EMAIL]
                   [--contact-firstname DRO_CONTACT_FIRSTNAME] [--contact-lastname DRO_CONTACT_LASTNAME]
                   [--dro-namespace DRO_NAMESPACE] [--artifactory-username ARTIFACTORY_USERNAME]
                   [--artifactory-token ARTIFACTORY_TOKEN] [--dev-mode] [--no-confirm] [--skip-pre-check] [-h]

IBM Maximo Application Suite Admin CLI v18.10.0
Restore a MAS instance from backup by configuring and launching the MAS Restore Tekton Pipeline.

Interactive Mode:
Omitting the --instance-id option will trigger an interactive prompt

MAS Instance:
  -i, --instance-id MAS_INSTANCE_ID
                        MAS Instance ID to restore, must match the instance ID of the backup.
  --mas-domain-restore MAS_DOMAIN_ON_RESTORE
                        MAS Domain to restore. If not specified, the domain will be taken from the backup.
  --sls-url-restore SLS_URL_ON_RESTORE
                        SLS URL to restore in Suite configuration. If not specified, the url will be taken from the backup.
  --dro-url-restore DRO_URL_ON_RESTORE
                        DRO URL to restore in Suite configuration. If not specified, the url will be taken from the backup.
  --include-slscfg-from-backup
                        Use SLS config from backup during Suite restore.
  --exclude-slscfg-from-backup
                        Exclude SLS config from backup during Suite restore.
  --sls-cfg-file SLS_CFG_FILE
                        SLS config file path to restore, must be provided if own SLS is used.
  --dro-cfg-file DRO_CFG_FILE
                        DRO config file path to restore, must be provided if own DRO is used.
  --include-drocfg-from-backup
                        Include DRO config from backup during Suite restore.
  --exclude-drocfg-from-backup
                        Exclude DRO config from backup during Suite restore.

Restore Configuration:
  --restore-version RESTORE_VERSION
                        Version/timestamp used in backup. Example: YYYYMMDD-HHMMSS
  --backup-storage-size BACKUP_STORAGE_SIZE
                        Size of the PVC storage, must be bigger than backup archive size. (default: 20Gi)
  --clean-backup        Clean backup and config workspaces after completion (default: true)
  --no-clean-backup     Do not clean backup and config workspaces after completion

Download Configuration:
  --download-backup     Download the backup archive from S3 or Artifactory
  --aws-access-key-id AWS_ACCESS_KEY_ID
                        AWS Access Key ID for S3 download
  --aws-secret-access-key AWS_SECRET_ACCESS_KEY
                        AWS Secret Access Key for S3 download
  --s3-bucket-name S3_BUCKET_NAME
                        S3 bucket name for backup download
  --s3-region S3_REGION
                        AWS region for S3 bucket
  --artifactory-url ARTIFACTORY_URL
                        Artifactory URL for backup download
  --artifactory-repository ARTIFACTORY_REPOSITORY
                        Artifactory repository for backup download
  --custom-backup-archive-name BACKUP_ARCHIVE_NAME
                        Custom backup archive name to download from S3 or Artifactory

Components:
  --include-grafana     Include Grafana in restore (default: true)
  --exclude-grafana     Skip installing Grafana.
  --include-dro         Include DRO in restore (default: true)
  --exclude-dro         Skip installing DRO.
  --include-sls         Include SLS in restore (default: true)
  --exclude-sls         Exclude SLS from restore (use if SLS is external)

IBM Suite License Service Operator:
  --sls-domain SLS_DOMAIN
                        SLS domain to use during SLS instance restore (optional).

IBM Data Reporting Operator:
  --ibm-entitlement-key IBM_ENTITLEMENT_KEY
                        IBM entitlement key
  --contact-email DRO_CONTACT_EMAIL
                        Contact e-mail address
  --contact-firstname DRO_CONTACT_FIRSTNAME
                        Contact first name
  --contact-lastname DRO_CONTACT_LASTNAME
                        Contact last name
  --dro-namespace DRO_NAMESPACE
                        Namespace for DRO

More:
  --artifactory-username ARTIFACTORY_USERNAME
                        Username for access to development builds on Artifactory
  --artifactory-token ARTIFACTORY_TOKEN
                        API Token for access to development builds on Artifactory
  --dev-mode            Configure restore in development mode
  --no-confirm          Launch the backup without prompting for confirmation
  --skip-pre-check      Skips the 'pre-restore-check' task in the restore pipeline
  -h, --help            Show this help message and exit
```

Examples
-------------------------------------------------------------------------------

### Interactive Restore
Launch an interactive restore session that will prompt you for all required configuration:

```bash
mas restore
```

### Non-Interactive Restore with Minimal Configuration
Restore a specific MAS instance from a backup with default settings:

```bash
mas restore --instance-id inst1 --restore-version 20260117-191701 --no-confirm
```

### Restore with Custom Storage Size
Specify a custom storage size for the restore PVC:

```bash
mas restore --instance-id inst1 --restore-version 20260117-191701 --backup-storage-size 50Gi --no-confirm
```

### Restore with Changed MAS Domain
Restore a backup and change the MAS domain in the Suite CR:

```bash
mas restore \
  --instance-id inst1 \
  --restore-version 20260117-191701 \
  --mas-domain-restore new.domain.com \
  --no-confirm
```

### Restore with S3 Download
Download a backup from S3 and restore it:

```bash
mas restore \
  --instance-id inst1 \
  --restore-version 20260117-191701 \
  --download-backup \
  --aws-access-key-id AKIAIOSFODNN7EXAMPLE \ #pragma: allowlist secret
  --aws-secret-access-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY \ #pragma: allowlist secret
  --s3-bucket-name my-mas-backups \
  --s3-region us-east-1 \
  --no-confirm
```

### Restore with Custom Backup Archive Name
Download and restore a backup with a custom archive name:

```bash
mas restore \
  --instance-id inst1 \
  --restore-version 20260117-191701 \
  --download-backup \
  --custom-backup-archive-name custom-backup-name.tar.gz \
  --aws-access-key-id AKIAIOSFODNN7EXAMPLE \ #pragma: allowlist secret
  --aws-secret-access-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY \ #pragma: allowlist secret
  --s3-bucket-name my-mas-backups \
  --s3-region us-east-1 \
  --no-confirm
```

### Restore Excluding SLS
Restore a backup without including Suite License Service (useful when using external SLS):

```bash
mas restore \
  --instance-id inst1 \
  --restore-version 20260117-191701 \
  --exclude-sls \
  --no-confirm
```

### Restore with Custom SLS Configuration File
Restore using a custom SLS configuration file instead of the one from backup:

```bash
mas restore \
  --instance-id inst1 \
  --restore-version 20260117-191701 \
  --exclude-slscfg-from-backup \
  --sls-cfg-file /path/to/sls-config.yaml \
  --no-confirm
```

### Restore with Changed SLS URL
Restore SLS configuration from backup but change the SLS URL:

```bash
mas restore \
  --instance-id inst1 \
  --restore-version 20260117-191701 \
  --include-slscfg-from-backup \
  --sls-url-restore https://new-sls-url.com \
  --no-confirm
```

### Restore with Custom DRO Configuration File
Restore using a custom DRO/BAS configuration file instead of the one from backup:

```bash
mas restore \
  --instance-id inst1 \
  --restore-version 20260117-191701 \
  --exclude-drocfg-from-backup \
  --dro-cfg-file /path/to/dro-config.yaml \
  --no-confirm
```

### Restore with DRO Installation
Restore and install a new DRO instance:

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

### Restore with Custom SLS Domain
Restore SLS instance with a custom domain:

```bash
mas restore \
  --instance-id inst1 \
  --restore-version 20260117-191701 \
  --include-sls \
  --sls-domain custom-sls.domain.com \
  --no-confirm
```

### Restore Excluding Grafana
Restore without installing Grafana:

```bash
mas restore \
  --instance-id inst1 \
  --restore-version 20260117-191701 \
  --exclude-grafana \
  --no-confirm
```

### Restore Skipping Pre-Check
Skip the pre-restore validation check (use with caution):

```bash
mas restore --instance-id inst1 --restore-version 20260117-191701 --skip-pre-check --no-confirm
```

### Restore Without Workspace Cleanup
Keep backup and config workspace contents after completion (useful for troubleshooting):

```bash
mas restore --instance-id inst1 --restore-version 20260117-191701 --no-clean-backup --no-confirm
```

!!! note
    By default, workspaces are cleaned after restore completion to free up storage. Use `--no-clean-backup` only when you need to inspect the workspace contents for troubleshooting purposes.

### Complete Non-Interactive Restore Example
A comprehensive example with all major options configured:

```bash
mas restore \
  --instance-id inst1 \
  --restore-version 20260117-191701 \
  --backup-storage-size 100Gi \
  --mas-domain-restore new.domain.com \
  --include-sls \
  --sls-domain custom-sls.domain.com \
  --include-slscfg-from-backup \
  --sls-url-restore https://new-sls-url.com \
  --include-drocfg-from-backup \
  --dro-url-restore https://new-dro-url.com \
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
  --s3-bucket-name my-mas-backups \
  --s3-region us-east-1 \
  --no-confirm
```

Notes
-------------------------------------------------------------------------------

### Restore Process
The restore command performs the following operations:

1. **Validates the target cluster** - Ensures OpenShift cluster connectivity
2. **Prepares the pipeline namespace** - Creates or updates the `mas-{instance-id}-pipelines` namespace
3. **Installs OpenShift Pipelines** - Validates or installs the OpenShift Pipelines Operator
4. **Creates backup PVC** - Provisions persistent storage for the backup data
5. **Downloads backup archive** - If configured, downloads the backup from S3 or Artifactory
6. **Launches the restore pipeline** - Submits a Tekton PipelineRun to perform the restore
7. **Restores MAS components** - Restores MAS instance, configurations, and selected components

### Default Values
If not specified, the following defaults are used:

- **Backup Storage Size**: `20Gi`
- **Clean Workspaces**: `true` (workspaces are cleaned after completion)
- **Include SLS**: `true`
- **Include Grafana**: `true`
- **Include DRO**: `true`
- **Include SLSCfg from Backup**: `true`
- **Include DROCfg from Backup**: `true`

### Storage Requirements
Ensure sufficient storage is available for the restore PVC. The required size must be larger than the backup archive size and depends on:

- Size of the backup archive
- Temporary extraction space needed during restore
- Any additional workspace requirements

### Download Sources
Two download sources are supported:

- **S3**: Standard AWS S3 bucket download (available in all modes)
- **Artifactory**: Artifactory repository download (requires `--dev-mode`)

### Configuration Options
The restore command provides flexibility in how configurations are restored:

#### SLS Configuration
- **From Backup**: Use `--include-slscfg-from-backup` (default) to restore SLS configuration from the backup
- **Custom File**: Use `--exclude-slscfg-from-backup` and provide `--sls-cfg-file` to use a custom configuration
- **Change URL**: Use `--sls-url-restore` to modify the SLS URL while keeping other configuration from backup

#### DRO Configuration
- **From Backup**: Use `--include-drocfg-from-backup` (default) to restore DRO configuration from the backup
- **Custom File**: Use `--exclude-drocfg-from-backup` and provide `--dro-cfg-file` to use a custom configuration
- **Change URL**: Use `--dro-url-restore` to modify the DRO URL while keeping other configuration from backup

#### MAS Domain
- By default, the MAS domain is restored from the backup
- Use `--mas-domain-restore` to change the domain during restore

### Component Installation
The restore process can optionally install components that are not part of the backup:

- **Grafana**: Monitoring and visualization (not backed up, can be installed during restore)
- **DRO**: Data Reporting Operator (not backed up, can be installed during restore)
- **SLS**: Suite License Service (backed up, can be restored or skipped if using external SLS)

### Interactive Mode
When running without `--instance-id`, the command enters interactive mode and will prompt for:

1. Target OpenShift cluster connection
2. MAS instance ID (must match the backup)
3. Backup version to restore
4. Grafana installation preference
5. SLS installation and configuration
6. DRO installation and configuration
7. MAS domain configuration
8. Backup storage size
9. Download configuration (optional)

### Pipeline Monitoring
After launching the restore, a URL to the Tekton PipelineRun will be displayed. Use this URL to monitor the restore progress in the OpenShift Console.

### Important Considerations

!!! warning
    - The MAS instance ID used for restore must match the instance ID from the backup
    - Ensure the target cluster has sufficient resources for the restored instance
    - Review and update configuration URLs (SLS, DRO) if the target environment differs from the backup source
    - If using external SLS or DRO, provide appropriate configuration files

!!! tip
    - Use `--skip-pre-check` only if you're confident about the cluster state
    - Keep `--no-clean-backup` disabled unless troubleshooting to save storage space
    - When changing domains or URLs, ensure DNS and network configurations are updated accordingly