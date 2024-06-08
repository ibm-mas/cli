Install
===============================================================================

Usage
-------------------------------------------------------------------------------
`mas install [options]`

### Catalog Selection (Required):
- `-c, --mas-catalog-version MAS_CATALOG_VERSION` IBM Maximo Operator Catalog to install (e.g. v8-amd64)

### Entitlement & Licensing (Required):
- `--ibm-entitlement-key IBM_ENTITLEMENT_KEY`  IBM entitlement key
- `--license-file SLS_LICENSE_FILE_LOCAL`      Path to MAS license file
- `--uds-email UDS_CONTACT_EMAIL`              Contact e-mail address
- `--uds-firstname UDS_CONTACT_FIRSTNAME`      Contact first name
- `--uds-lastname UDS_CONTACT_LASTNAME`        Contact last name

### Storage Class Selection (Required):
- `--storage-rwo STORAGE_CLASS_RWO`                   Read Write Once (RWO) storage class (e.g. ibmc-block-gold)
- `--storage-rwx STORAGE_CLASS_RWX`                   Read Write Many (RWX) storage class (e.g. ibmc-file-gold-gid)
- `--storage-pipeline PIPELINE_STORAGE_CLASS`         Install pipeline storage class (e.g. ibmc-file-gold-gid)
- `--storage-accessmode PIPELINE_STORAGE_ACCESSMODE`  Install pipeline storage class access mode (ReadWriteMany or ReadWriteOnce)

### Maximo Application Suite Instance (Required):
- `-i, --mas-instance-id MAS_INSTANCE_ID`             MAS Instance ID
- `-w, --mas-workspace-id MAS_WORKSPACE_ID`           MAS Workspace ID
- `-W, --mas-workspace-name MAS_WORKSPACE_ID`         MAS Workspace Name

### Advanced MAS Configuration (Optional):
- `--additional-configs LOCAL_MAS_CONFIG_DIR`                       Path to a directory containing additional configuration files to be applied
- `--non-prod`                                                      Install MAS in Non-production mode
- `--ocp-ingress-tls-secret-name OCP_INGRESS_TLS_SECRET_NAME`       Name of the secret holding the cluster's ingress certificates
- `--mas-trust-default-cas MAS_TRUST_DEFAULT_CAS`                   Trust certificates signed by well-known CAs
- `--workload-scale-profile`                                        Set a pre-defined workload scale profile [`Burstable`, `BestEffort`, `Guaranteed`]
- `--mas-pod-templates-dir`                                         Path to directory containing custom podTemplates configuration files to be applied. Takes precedence over `--workload-scale-profile`

### Maximo Application Suite Core Platform (Required):
- `--mas-channel MAS_CHANNEL`                                    Subscription channel for the Core Platform

### Maximo Application Suite Application Selection (Optional):
- `--iot-channel MAS_APP_CHANNEL_IOT`                            Subscription channel for Maximo IoT
- `--monitor-channel MAS_APP_CHANNEL_MONITOR`                    Subscription channel for Maximo Monitor
- `--manage-channel MAS_APP_CHANNEL_MANAGE`                      Subscription channel for Maximo Manage
- `--manage-jdbc MAS_APPWS_BINDINGS_JDBC_MANAGE`                 Configure Maximo Manage JDBC binding (workspace-application or system)
- `--predict-channel MAS_APP_CHANNEL_PREDICT`                    Subscription channel for Maximo Predict
- `--assist-channel MAS_APP_CHANNEL_ASSIST`                      Subscription channel for Maximo Assist
- `--visualinspection-channel MAS_APP_CHANNEL_VISUALINSPECTION`  Subscription channel for Maximo Visual Inspection
- `--optimizer-channel MAS_APP_CHANNEL_OPTIMIZER`                Subscription channel for Maximo optimizer
- `--optimizer-plan MAS_APP_PLAN_OPTIMIZER`                      Installation plan for Maximo Optimizer (full or limited)

### IBM Cloud Pak for Data (Required when installing Predict or Assist):
- `--cp4d-version CP4D_VERSION`                                  Product version of CP4D to use
- `--cp4d-install-cognos`                                        Adds Cognos as part of Cloud Pak for Data (Requires Manage application to be installed too).
- `--cp4d-install-spss`                                          Adds SPSS Modeler as part of Cloud Pak for Data.
- `--cp4d-install-openscale`                                     Adds Watson Openscale as part of Cloud Pak for Data.

### Kafka - Common Arguments (Optional, required to install Maximo IoT):
- `--kafka-provider KAFKA_PROVIDER`                             Required. Set Kafka provider. Supported options are `redhat` (Red Hat AMQ Streams), `strimzi` and `ibm` (IBM Event Streams) and `aws` (AWS MSK)
- `--kafka-version KAFKA_VERSION`                               Optional. Set version of the Kafka cluster that the Strimzi or AMQ Streams operator will create
- `--kafka-namespace KAFKA_NAMESPACE`                           Optional. Set Kafka namespace. Only applicable if installing `redhat` (Red Hat AMQ Streams) or `strimzi`
- `--kafka-username KAFKA_USER_NAME`                            Required. Set Kafka instance username. Only applicable if installing `redhat` (Red Hat AMQ Streams), `strimzi` or `aws` (AWS MSK)
- `--kafka-password KAFKA_USER_PASSWORD`                        Required. Set Kafka instance password. Only applicable if installing `redhat` (Red Hat AMQ Streams), `strimzi` or `aws` (AWS MSK)

### Kafka - AWS MSK:
- `--aws-region AWS_REGION`                                     Required. Set target AWS region for the MSK instance
- `--aws-access-key-id AWS_ACCESS_KEY_ID`                       Required. Set AWS access key ID for the target AWS account
- `--aws-secret-access-key AWS_SECRET_ACCESS_KEY`               Required. Set AWS secret access key for the target AWS account
- `--aws-vpc-id VPC_ID`                                         Required. Set target Virtual Private Cloud ID for the MSK instance
- `--msk-instance-type AWS_MSK_INSTANCE_TYPE`                   Optional. Set the MSK instance type
- `--msk-instance-nodes AWS_MSK_INSTANCE_NUMBER`                Optional. Set total number of MSK instance nodes
- `--msk-instance-volume-size AWS_MSK_VOLUME_SIZE`              Optional. Set storage/volume size for the MSK instance
- `--msk-cidr-az1 AWS_MSK_CIDR_AZ1`                             Required. Set the CIDR subnet for availability zone 1 for the MSK instance
- `--msk-cidr-az2 AWS_MSK_CIDR_AZ2`                             Required. Set the CIDR subnet for availability zone 2 for the MSK instance
- `--msk-cidr-az3 AWS_MSK_CIDR_AZ3`                             Required. Set the CIDR subnet for availability zone 3 for the MSK instance
- `--msk-cidr-ingress AWS_MSK_INGRESS_CIDR`                     Required. Set the CIDR for ingress connectivity
- `--msk-cidr-egress AWS_MSK_EGRESS_CIDR`                       Required. Set the CIDR for egress connectivity

### Kafka - IBM Cloud Event Streams:
- `--ibmcloud-apikey IBMCLOUD_APIKEY`                           Required. Set IBM Cloud API Key.
- `--eventstreams-resource-group EVENTSTREAMS_RESOURCEGROUP`    Optional. Set IBM Cloud resource group to target the Event Streams instance provisioning.
- `--eventstreams-instance-name EVENTSTREAMS_NAME`              Optional. Set IBM Event Streams instance name.
- `--eventstreams-instance-location EVENTSTREAMS_LOCATION`      Optional. Set IBM Event Streams instance location.

### IBM Db2 (Optional, required to use IBM Db2 Universal Operator):
- `--db2u-channel DB2_CHANNEL`          Subscription channel for Db2u (e.g. v110508.0)
- `--db2u-system`                       Install a shared Db2u instance for MAS (required by IoT & Monitor, supported by Manage)
- `--db2u-manage`                       Install a dedicated Db2u instance for Maximo Manage (supported by Manage)
- `--db2u-manage-type`                  Optional. Choose the type of the Manage dedicated Db2u instance. Available options are `db2wh` (default) or `db2oltp`.

### Advanced Db2u Universal Operator Configuration (Optional):
- `--db2u-namespace DB2_NAMESPACE` Change namespace where Db2u instances will be created

### Advanced Db2u Universal Operator Configuration - Node Scheduling (Optional):
- `--db2u-affinity-key DB2_AFFINITY_KEY`             Set a node label to declare affinity to
- `--db2u-affinity-value DB2_AFFINITY_VALUE`         Set the value of the node label to affine with
- `--db2u-tolerate-key DB2_TOLERATE_KEY`             Set a node taint to tolerate
- `--db2u-tolerate-value DB2_TOLERATE_VALUE`         Set the value of the taint to tolerate
- `--db2u-tolerate-effect DB2_TOLERATE_EFFECT`       Set the effect that will be tolerated (NoSchedule, PreferNoSchedule, or NoExecute)

### Advanced Db2u Universal Operator Configuration - Resource Requests (Optional):
- `--db2u-cpu-request DB2_CPU_REQUESTS`              Customize Db2 CPU request
- `--db2u-cpu-limit DB2_CPU_LIMITS`                  Customize Db2 CPU limit
- `--db2u-memory-request DB2_MEMORY_REQUESTS`        Customize Db2 memory request
- `--db2u-memory-limit DB2_MEMORY_LIMITS`            Customize Db2 memory limit

### Advanced Db2u Universal Operator Configuration - Storage (Optional):
- `--db2u-backup-storage DB2_BACKUP_STORAGE_SIZE`    Customize Db2 storage capacity
- `--db2u-data-storage DB2_DATA_STORAGE_SIZE`        Customize Db2 storage capacity
- `--db2u-logs-storage DB2_LOGS_STORAGE_SIZE`        Customize Db2 storage capacity
- `--db2u-meta-storage DB2_META_STORAGE_SIZE`        Customize Db2 storage capacity
- `--db2u-temp-storage DB2_TEMP_STORAGE_SIZE`        Customize Db2 storage capacity

### Manage Application - Advanced Configuration (Optional):

- `--manage-server-bundle-size MAS_APP_SETTINGS_SERVER_BUNDLES_SIZE`                        Set Manage server bundle size configuration i.e `dev, small, jms or snojms`
- `--manage-components MAS_APPWS_COMPONENTS`                                                Set Manage Components to be installed i.e `base=latest,health=latest,civil=latest`

  List of all identifiers for Manage industry solutions and add-ons that can be installed with Manage (base):

    - `acm` (Asset Configuration Manager)
    - `aviation` (Aviation)
    - `civil` (Civil Infrastructure)
    - `envizi` (Envizi)
    - `hse` (Health, Safety and Environment)
    - `health` (Health)
    - `icd` (Maximo IT)
    - `nuclear` (Nuclear)
    - `oilandgas` (Oil & Gas)
    - `oracleadapter` (Connector for Oracle Applications)
    - `sapadapter` (Connector for SAP Applications)
    - `serviceprovider` (Service Provider)
    - `spatial` (Spatial)
    - `strategize` (Strategize)
    - `transportation` (Transportation)
    - `tririga` (Tririga)
    - `utilities` (Utilities)
    - `workday` (Workday Applications)

  For detailed information about each of the available Manage Industry Solutions or Add-ons, please check the [Maximo Manage components](https://www.ibm.com/docs/en/mas-cd/maximo-manage/continuous-delivery?topic=overview-maximo-manage-components) documentation.

- `--manage-base-language MAS_APP_SETTINGS_BASE_LANG`                                       Set Manage base language to be installed. Default is `EN` (English).
- `--manage-secondary-languages MAS_APP_SETTINGS_SECONDARY_LANGS`                           Set a comma-separated list of Manage secondary languages to be installed. As example: `JA,DE,AR` For a complete list of available languages, please check the [Maximo Manage language support](https://www.ibm.com/docs/en/mas-cd/mhmpmh-and-p-u/continuous-delivery?topic=deploy-language-support) documentation.
- `--manage-server-timezone MAS_APP_SETTINGS_SERVER_TIMEZONE`                               Set the Manage server timezone. Default is `GMT`.
- `--manage-customization-archive-name MAS_APP_SETTINGS_CUSTOMIZATION_ARCHIVE_NAME`         Set Manage Archive name
- `--manage-customization-archive-url MAS_APP_SETTINGS_CUSTOMIZATION_ARCHIVE_URL`           Set Manage Archive url
- `--manage-customization-archive-username MAS_APP_SETTINGS_CUSTOMIZATION_ARCHIVE_USERNAME` Set Manage Archive username, in case url requires basic authentication to pull the archive
- `--manage-customization-archive-password MAS_APP_SETTINGS_CUSTOMIZATION_ARCHIVE_PASSWORD` Set Manage Archive password, in case url requires basic authentication to download the archive
- `--manage-crypto-key MAS_APP_SETTINGS_CRYPTO_KEY`                                         Set `MXE_SECURITY_CRYPTO_KEY` value if you want to customize your Manage database encryption keys
- `--manage-cryptox-key MAS_APP_SETTINGS_CRYPTOX_KEY`                                       Set `MXE_SECURITY_CRYPTOX_KEY` value if you want to customize your Manage database encryption keys
- `--manage-old-crypto-key MAS_APP_SETTINGS_OLD_CRYPTO_KEY`                                 Set `MXE_SECURITY_OLD_CRYPTO_KEY` value if you want to customize your Manage database encryption keys
- `--manage-old-cryptox-key MAS_APP_SETTINGS_OLD_CRYPTOX_KEY`                               Set `MXE_SECURITY_OLD_CRYPTOX_KEY` value if you want to customize your Manage database encryption keys
- `--manage-override-encryption-secrets`                                                    Overrides any existing Manage database encryption keys. A backup of the original secret holding existing encryption keys is taken prior overriding it with the new defined keys.
-- `--manage-db-tablespace MAS_APP_SETTINGS_TABLESPACE`                                     Optional. Set the database tablespace name that Manage will use to be installed. Default is `MAXDATA`.
-- `--manage-db-indexspace MAS_APP_SETTINGS_INDEXSPACE`                                     Optional. Set the database indexspace name that Manage will use to be installed. Default is `MAXINDEX`.
-- `--manage-db-schema MAS_APP_SETTINGS_DB2_SCHEMA`                                         Optional. Set the DB2 database schema name that Manage will use to be installed. Default is `maximo`. Note: This is only applicable to the cases where a DB2 instance will be created for Manage via MAS CLI.

### Other Commands:
- `--no-wait-for-pvcs` If you are using using storage classes that utilize 'WaitForFirstConsumer' binding mode use this flag
- `--no-confirm`       Launch the install without prompting for confirmation
- `--accept-license`   Accept MAS and Maximo IT (if applicable) licenses
- `--skip-pre-check`   Skips the 'pre-install-check' task in the install pipeline
- `-h, --help`         Show install help message

Non-Interactive Install
-------------------------------------------------------------------------------
```bash
docker run -ti --rm -v ~:/mnt/home --pull always quay.io/ibmmas/cli
export ENTITLEMENT_KEY=xxx
mas install -i mas1 -w ws1 -W "My Workspace" -c v8-amd64 --mas-channel 8.10.x \
  --ibm-entitlement-key $ENTITLEMENT_KEY \
  --license-id xxxxxxxxxxxx --license-file /mnt/home/entitlement.lic \
  --uds-email myemail@email.com --uds-firstname John --uds-lastname Barnes \
  --storage-rwo ibmc-block-gold --storage-rwx ibmc-file-gold-gid \
  --storage-pipeline ibmc-file-gold-gid --storage-accessmode ReadWriteMany \
  --no-confirm \
  --accept-license
```


Interactive Install
-------------------------------------------------------------------------------

```bash
docker run -ti --rm -v ~:/mnt/home --pull always quay.io/ibmmas/cli
mas install
```

!!! important
    We will need the `entitlement.lic` file to perform the installation which is why we mount your home directory into the container.  If you saved the entitlement file elsewhere, mount that directory instead.

    When prompted you will be able to set license file to `/mnt/home/entitlement.lic`


!!! tip
    Wherever you see a `[Y/n]` or `[y/N]` prompt, the option in upper case is the default, and can be accepted just by hitting return.

    Selections are saved to file (`$HOME/.ibm-mas/cli.env`), if you make a mistake use `Ctrl+C` to quit the installer and when you run the install command again it will remember all your choices made to that point.

    In the unlikely event that you are running the install on a shared computer you should delete the `$HOME/.ibm-mas` directory after launching the installation.


### Step 1: Set Target OpenShift Cluster
If you are not already connected to an OpenShift cluster you will be prompted to provide the server URL & token, and whether to verify the server certificate or not,  If you are already connected to a cluster you will be given the option to change to another cluster.


### Step 2: Install OpenShift Pipelines Operator
No input is required during this step.  The Red Hat Pipelines Operator will be installed on the cluster (if it is not already).


### Step 3: IBM Maximo Operator Catalog Selection
You must decide whether to use the online dynamic catalog or an offline static catalog.  The default is to use the static catalog, for more information about catalog choice refer to [Choosing the right catalog](../guides/choosing-the-right-catalog.md).

If you selected to use a static catalog then you will be presented with a table of available catalogs and the versions of MAS available in the catalog.  Make the selection using the numbers in the left-most column.


### Step 4: License Terms
Confirm that you accept the IBM Maximo Application Suite license terms


### Step 5: Configure MAS Instance
Provide the basic information about your MAS instance:

- Instance ID
- Workspace ID
- Workspace Display Name

!!! important
    Instance ID restrictions:

    - Must be 3-12 characters long
    - Must only use lowercase letters, numbers, and hyphen (`-`) symbol
    - Must start with a lowercase letter
    - Must end with a lowercase letter or a number

    Workspace ID restrictions:

    - Must be 3-12 characters long
    - Must only use lowercase letters and numbers
    - Must start with a lowercase letter

    Workspace display name restrictions:

    - Must be 3-300 characters long

### Step 6: Configure Operation Mode
The install will default to a production mode installation, but by choosing "y" at the prompt you will be able to install MAS in non-production mode.


### Step 7. Configure Domain & Certificate Management
By default MAS will be installed in a subdomain of your OpenShift clusters domain matching the MAS instance ID that you chose.  For example if your OpenShift cluster is `myocp.net` and you are installing MAS with an instance ID of `prod1` then MAS will be installed with a default domain something like `prod1.apps.myocp.net`, depending on the exact network configuration of your cluster.

If you wish to use a custom domain for the MAS install you can choose to configure this by selecting "n" at the prompt.  The install supports DNS integrations for Cloudflare, IBM Cloud Internet Services, AWS Route 53 out of the box and is able to configure a certificate issuer using LetsEncrypt (production or staging) or a self-signed certificate authority per your choices.


### Step 8. Application Selection
Select the applications that you would like to install. Note that some applications cannot be installed unless an application they depend on is also installed:

- Monitor is only available for install if IoT is selected
- Assist and Predict are only available for install if Monitor is selected


### Step 9. Configure Databases
If you have selected one or more applications that require a JDBC datasource (IoT, Manage, Monitor, & Predict) you must choose how to provide that dependency:

- Use the IBM Db2 Universal Operator
- Provide a JDBC configuration

If you choose the latter then you will be prompted to select a local directory where the configuration will be staged and requested to provide a display name, the JDBC connection URL, username, password, and whether the endpoint is SSL enabled (if it is then you will also be asked to provide the SSL certificate required to connect to the database).

!!! tip
    If you have already generated the configuration file (manually, or using the install previously) the CLI will detect this and prompt whether you wish to re-use the existing configuration, or generate a new one.


### Step 10. Configure Turbonomic
The [IBM Turbonomic](https://www.ibm.com/products/turbonomic) hybrid cloud cost optimization platform allows you to eliminate this guesswork with solutions that save time and optimize costs.  To enable Turbonomic integration you must provide the following information:

- Target name
- Server URL
- Server version
- Authentication credentials (username & password)


### Step 11. Additional Configurations
Additional resource definitions can be applied to the OpenShift Cluster during the MAS configuration step, here you will be asked whether you wish to provide any additional configurations and if you do in what directory they reside.

!!! note
    If you provided one or more JDBC configurations in step 9 then additional configurations will already be enabled and be pointing at the directory you chose for the JDBC configurations.


### Step 12. Configure Storage Class Usage
MAS requires both a `ReadWriteMany` and a `ReadWriteOnce` capable storage class to be available in the cluster.  The installer has the ability to recognize certain storage class providers and will default to the most appropriate storage class in these cases:

- IBMCloud Storage (`ibmc-block-gold` & `ibmc-file-gold`)
- OpenShift Container Storage (`ocs-storagecluster-ceph-rbd` & `ocs-storagecluster-cephfs`)
- Azure Managed Storage (`azurefiles-premium` & `managed-premium`)
- AWS Storage (`gp2` & `efs`)

Even when a recognized storage provider is detected you will be provided with the option to select your own storages classes anyway.

When selecting storage classes you will be presented with a list of available storage classes and must select both a `ReadWriteMany` and a `ReadWriteOnce` storage class.

!!! warning
    Unfortunately there is no way for the install to verify that the storage class selected actually supports the appropriate access mode, refer to the documentation from the storage class provider to determine whether your storage class supports `ReadWriteOnce` and/or `ReadWriteMany`.


### Step 13. Advanced Settings
These settings can generally be ignored for most installations.

#### Configure Scaling Profile

You can choose between three pre-defined workload scaling classes - `Burstable`, `BestEffort` and `Guaranteed`; or choose a custom profile of your own. By default MAS applications use `Burstable`.

When choosing a custom profile you will be prompted for the directory of your config files. For each supported application you will need to create separate config file. The naming convention for custom config files is `ibm-<appname>-<customresourcename>.yml`.

Currently supported config files:
- ibm-mas
  - ibm-mas-bascfg.yml
  - ibm-mas-pushnotificationcfg.yml
  - ibm-mas-scimcfg.yml
  - ibm-mas-slscfg.yml
  - ibm-mas-smtpcfg.yml
  - ibm-mas-coreidp.yml
  - ibm-mas-suite.yml
- ibm-sls
  - ibm-sls-licenseservice.yml
- ibm-data-dictionary
  - ibm-data-dictionary-assetdatadictionary.yml
- ibm-mas-iot
  - ibm-mas-iot-actions.yml
  - ibm-mas-iot-auth.yml
  - ibm-mas-iot-datapower.yml
  - ibm-mas-iot-devops.yml
  - ibm-mas-iot-dm.yml
  - ibm-mas-iot-dsc.yml
  - ibm-mas-iot-edgeconfig.yml
  - ibm-mas-iot-fpl.yml
  - ibm-mas-iot-guardian.yml
  - ibm-mas-iot-iot.yml
  - ibm-mas-iot-mbgx.yml
  - ibm-mas-iot-mfgx.yml
  - ibm-mas-iot-monitor.yml
  - ibm-mas-iot-orgmgmt.yml
  - ibm-mas-iot-provision.yml
  - ibm-mas-iot-registry.yml
  - ibm-mas-iot-state.yml
  - ibm-mas-iot-webui.yml
- ibm-mas-manage
  - ibm-mas-manage-manageapp.yml
  - ibm-mas-manage-manageworkspace.yml
  - ibm-mas-manage-imagestitching.yml
  - ibm-mas-manage-slackproxy.yml
  - ibm-mas-manage-healthextworkspace.yml

For examples on these config files take a look into the pre-defined configs: [BestEffort](https://github.com/ibm-mas/cli/blob/master/image/cli/mascli/templates/pod-templates/best-effort) and [Guaranteed](https://github.com/ibm-mas/cli/blob/master/image/cli/mascli/templates/pod-templates/guaranteed). More information on podTemplates can be found in our official IBM documentation [here](https://www.ibm.com/docs/en/mas-cd/continuous-delivery?topic=configuring-customizing-workloads).

!!! Note: This feature is only supported starting in MAS 8.11.0 and SLS 3.8.0

#### Change default install namespaces?
Answering "y" will allow you to customize the namespace where Db2, Grafana, and MongoDb are installed in the cluster.


### Step 15. Configure IBM Container Registry
Provide your IBM entitlement key.  If you have set the `IBM_ENTITLEMENT_KEY` environment variable then you will first be prompted whether you just want to re-use the saved entitlement key.


### Step 16. Configure Product License
Provide your license ID and the location of your license file.


### Step 19. Configure UDS
Maximo Application Suite's required integration with either IBM User Data Services OR IBM Data Reporter Operator requires your e-mail address and first/last name be provided.


### Step 20. Prepare Installation
No input is required here, the install will prepare the namespace where install will be executed on the cluster and validate that the CLI container image (which will perform the installation) is accessible from your cluster.

!!! note
    For disconnected installations you may need to provide the digest of the ibmmas/cli container image.

### Step 21. Review Settings
A summary of all your choices will be presented and you will be prompted to provide a final confirmation as to whether to proceed with the install, or abort.



Air Gap Support
-------------------------------------------------------------------------------
If you have already ran `mas configure-airgap` to install the ImageContentSourcePolicy for IBM Maximo Application Suite then the installer will automatically detect the presence of this and tailor the installation configuration for a disconnected installation.

A number of applications are not currently available when using a private mirror registry in this fashion, as a result you will not be asked whether you wish to install these applications:

- Maximo Assist
- Maximo Health & Predict Utilities
- Maximo Visual Inspection


More Information
-------------------------------------------------------------------------------
The install is designed to work on any OCP cluster, but has been specifically tested in these environments:

- IBMCloud ROKS
- Microsoft Azure
- AWS ROSA
- IBM DevIT FYRE (internal)

### The Automation Engine
The engine that performs all tasks is written in Ansible, you can directly use the same automation outside of this CLI if you wish.  The code is open source and available in [ibm-mas/ansible-devops](https://github.com/ibm-mas/ansible-devops), the collection is also available to install directly from Ansible Galaxy:

- [Ansible Galaxy: ibm.mas_devops](https://galaxy.ansible.com/ibm/mas_devops)

### The Automation Driver
The install is performed inside your RedHat OpenShift cluster utilizing [Openshift Pipelines](https://cloud.redhat.com/learn/topics/ci-cd)

> OpenShift Pipelines is a Kubernetes-native CI/CD solution based on Tekton. It builds on Tekton to provide a CI/CD experience through tight integration with OpenShift and Red Hat developer tools. OpenShift Pipelines is designed to run each step of the CI/CD pipeline in its own container, allowing each step to scale independently to meet the demands of the pipeline.

![](../img/pipeline.png)

### Support
The installer supports:

- IBM Maximo Operator Catalog installation
- Required dependency installation:
    - MongoDb
    - IBM Suite License Service
    - IBM User Data Services
    - IBM Certificate Manager
- Optional dependency installation:
    - Apache Kafka
    - IBM Db2
    - IBM Cloud Pak for Data Platform and Services
        - [Watson Studio](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.0?topic=services-watson-studio)
        - [Watson Machine Learning](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.0?topic=services-watson-machine-learning)
        - [Watson OpenScale](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.0?topic=services-watson-openscale)
        - [Analytics Engine (Apache Spark)](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.0?topic=services-analytics-engine-powered-by-apache-spark)
- Suite core services installation
- Suite application installation

The installer will automatically provision and set up the required dependencies based on the applications that you select to install.

The install can be launched with the command `mas install`.  The end result will be a pipeline run started in your target cluster where you can track the progress of the installation.

![](../img/pipelineruns.png)
