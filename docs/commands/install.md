Install
===============================================================================

Usage
-------------------------------------------------------------------------------
For full usage information run `mas install --help`

```
mas install [-c MAS_CATALOG_VERSION] [--mas-catalog-digest MAS_CATALOG_DIGEST] [--ibm-entitlement-key IBM_ENTITLEMENT_KEY] [-i MAS_INSTANCE_ID]
            [-w MAS_WORKSPACE_ID] [-W MAS_WORKSPACE_NAME] [--mas-channel MAS_CHANNEL] [--eck] [--eck-enable-logstash]
            [--eck-remote-es-hosts ECK_REMOTE_ES_HOSTS] [--eck-remote-es-username ECK_REMOTE_ES_USERNAME]
            [--eck-remote-es-password ECK_REMOTE_ES_PASSWORD] [--superuser-username MAS_SUPERUSER_USERNAME] [--superuser-password MAS_SUPERUSER_PASSWORD]
            [--additional-configs ADDITIONAL_CONFIGS] [--pod-templates POD_TEMPLATES] [--non-prod] [--disable-ca-trust]
            [--manual-certificates MANUAL_CERTIFICATES] [--disable-walkme] [--storage-class-rwo STORAGE_CLASS_RWO]
            [--storage-class-rwx STORAGE_CLASS_RWX] [--storage-pipeline STORAGE_PIPELINE] [--storage-accessmode {ReadWriteMany,ReadWriteOnce}]
            [--license-file LICENSE_FILE] [--uds-email UDS_CONTACT_EMAIL] [--uds-firstname UDS_CONTACT_FIRSTNAME] [--uds-lastname UDS_CONTACT_LASTNAME]
            [--dro-namespace DRO_NAMESPACE] [--mongodb-namespace MONGODB_NAMESPACE] [--ocp-ingress-tls-secret-name OCP_INGRESS_TLS_SECRET_NAME]
            [--assist-channel ASSIST_CHANNEL] [--iot-channel IOT_CHANNEL] [--monitor-channel MONITOR_CHANNEL] [--manage-channel MANAGE_CHANNEL]
            [--predict-channel PREDICT_CHANNEL] [--visualinspection-channel VISUALINSPECTION_CHANNEL] [--optimizer-channel OPTIMIZER_CHANNEL]
            [--optimizer-plan {full,limited}] [--install-arcgis] [--arcgis-channel MAS_ARCGIS_CHANNEL]
            [--manage-server-bundle-size {dev,snojms,small,jms}] [--manage-jms] [--manage-persistent-volumes]
            [--manage-jdbc {system,workspace-application}] [--manage-demodata] [--manage-components MAS_APPWS_COMPONENTS]
            [--manage-customization-archive-name MAS_APP_SETTINGS_CUSTOMIZATION_ARCHIVE_NAME]
            [--manage-customization-archive-url MAS_APP_SETTINGS_CUSTOMIZATION_ARCHIVE_URL]
            [--manage-customization-archive-username MAS_APP_SETTINGS_CUSTOMIZATION_ARCHIVE_USERNAME]
            [--manage-customization-archive-password MAS_APP_SETTINGS_CUSTOMIZATION_ARCHIVE_PASSWORD]
            [--manage-db-tablespace MAS_APP_SETTINGS_TABLESPACE] [--manage-db-indexspace MAS_APP_SETTINGS_INDEXSPACE]
            [--manage-db-schema MAS_APP_SETTINGS_DB2_SCHEMA] [--manage-crypto-key MAS_APP_SETTINGS_CRYPTO_KEY]
            [--manage-cryptox-key MAS_APP_SETTINGS_CRYPTOX_KEY] [--manage-old-crypto-key MAS_APP_SETTINGS_OLD_CRYPTO_KEY]
            [--manage-old-cryptox-key MAS_APP_SETTINGS_OLD_CRYPTOX_KEY] [--manage-override-encryption-secrets]
            [--manage-base-language MAS_APP_SETTINGS_BASE_LANG] [--manage-secondary-languages MAS_APP_SETTINGS_SECONDARY_LANGS]
            [--manage-server-timezone MAS_APP_SETTINGS_SERVER_TIMEZONE] [--cp4d-version CPD_PRODUCT_VERSION] [--cp4d-install-spss]
            [--cp4d-install-openscale] [--cp4d-install-cognos] [--db2-namespace DB2_NAMESPACE] [--db2-channel DB2_CHANNEL] [--db2-system] [--db2-manage]
            [--db2-type DB2_TYPE] [--db2-timezone DB2_TIMEZONE] [--db2-affinity-key DB2_AFFINITY_KEY] [--db2-affinity-value DB2_AFFINITY_VALUE]
            [--db2-tolerate-key DB2_TOLERATE_KEY] [--db2-tolerate-value DB2_TOLERATE_VALUE] [--db2-tolerate-effect DB2_TOLERATE_EFFECT]
            [--db2-cpu-requests DB2_CPU_REQUESTS] [--db2-cpu-limits DB2_CPU_LIMITS] [--db2-memory-requests DB2_MEMORY_REQUESTS]
            [--db2-memory-limits DB2_MEMORY_LIMITS] [--db2-backup-storage DB2_BACKUP_STORAGE_SIZE] [--db2-data-storage DB2_DATA_STORAGE_SIZE]
            [--db2-logs-storage DB2_LOGS_STORAGE_SIZE] [--db2-meta-storage DB2_META_STORAGE_SIZE] [--db2-temp-storage DB2_TEMP_STORAGE_SIZE]
            [--kafka-provider {strimzi,redhat,ibm,aws}] [--kafka-username KAFKA_USERNAME] [--kafka-password KAFKA_PASSWORD]
            [--kafka-namespace KAFKA_NAMESPACE] [--kafka-version KAFKA_VERSION] [--msk-instance-type AWS_MSK_INSTANCE_TYPE]
            [--msk-instance-nodes AWS_MSK_INSTANCE_NUMBER] [--msk-instance-volume-size AWS_MSK_VOLUME_SIZE] [--msk-cidr-az1 AWS_MSK_CIDR_AZ1]
            [--msk-cidr-az2 AWS_MSK_CIDR_AZ2] [--msk-cidr-az3 AWS_MSK_CIDR_AZ3] [--msk-cidr-egress AWS_MSK_EGRESS_CIDR]
            [--msk-cidr-ingress AWS_MSK_INGRESS_CIDR] [--eventstreams-resource-group EVENTSTREAMS_RESOURCE_GROUP]
            [--eventstreams-instance-name EVENTSTREAMS_INSTANCE_NAME] [--eventstreams-instance-location EVENTSTREAMS_INSTANCE_LOCATION] [--cos {ibm,ocs}]
            [--cos-resourcegroup COS_RESOURCEGROUP] [--turbonomic-name TURBONOMIC_TARGET_NAME] [--turbonomic-url TURBONOMIC_SERVER_URL]
            [--turbonomic-version TURBONOMIC_SERVER_VERSION] [--turbonomic-username TURBONOMIC_USERNAME] [--turbonomic-password TURBONOMIC_PASSWORD]
            [--ibmcloud-apikey IBMCLOUD_APIKEY] [--aws-region AWS_REGION] [--aws-access-key-id AWS_ACCESS_KEY_ID] [--secret-access-key SECRET_ACCESS_KEY]
            [--aws-vpc-id AWS_VPC_ID] [--artifactory-username ARTIFACTORY_USERNAME] [--artifactory-token ARTIFACTORY_TOKEN] [--allow-special-chars MAS_SPECIAL_CHARACTERS]
            [--approval-core APPROVAL_CORE] [--approval-assist APPROVAL_ASSIST] [--approval-iot APPROVAL_IOT] [--approval-manage APPROVAL_MANAGE]
            [--approval-monitor APPROVAL_MONITOR] [--approval-optimizer APPROVAL_OPTIMIZER] [--approval-predict APPROVAL_PREDICT]
            [--approval-visualinspection APPROVAL_VISUALINSPECTION] [--accept-license] [--dev-mode] [--no-wait-for-pvc] [--skip-pre-check]
            [--skip-grafana-install] [--no-confirm] [-h]
```


Non-Interactive Install
-------------------------------------------------------------------------------
```bash
docker run -ti --rm -v ~:/mnt/home --pull always quay.io/ibmmas/cli
export ENTITLEMENT_KEY=xxx
mas install -i mas1 -w ws1 -W "My Workspace" -c @@MAS_LATEST_CATALOG@@ --mas-channel @@MAS_LATEST_CHANNEL@@ \
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
