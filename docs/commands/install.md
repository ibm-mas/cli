Install
===============================================================================

Usage
-------------------------------------------------------------------------------
`mas install [options]`

### Catalog Selection (Required):
- `-c, --mas-catalog-version MAS_CATALOG_VERSION` IBM Maximo Operator Catalog to install (e.g. v8-amd64)

### Entitlement & Licensing (Required):
- `--ibm-entitlement-key IBM_ENTITLEMENT_KEY`  IBM entitlement key
- `--license-id SLS_LICENSE_ID`                MAS license ID
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
- `--additional-configs LOCAL_MAS_CONFIG_DIR`         Path to a directory containing additional configuration files to be applied
- `--non-prod`                                        Install MAS in Non-production mode
- `--mas-trust-default-cas MAS_TRUST_DEFAULT_CAS`     Trust certificates signed by well-known CAs

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

### IBM Db2 (Optional, required to use IBM Db2 Universal Operator):
- `--db2u-channel DB2_CHANNEL`     Subscription channel for Db2u (e.g. v110508.0)
- `--db2u-system`                  Install a shared Db2u instance for MAS (required by IoT & Monitor, supported by Manage)
- `--db2u-manage`                  Install a dedicated Db2u instance for Maximo Manage (supported by Manage)

### Advanced Db2u Universal Operator Configuration (Optional):
- `--db2u-namespace DB2_NAMESPACE` Change namespace where Db2u instances will be created

### Advanced Db2u Universal Operator Configuration - Node Scheduling (Optional):
- `--db2u-affinity-key DB2_AFFINITY_KEY`             Set a node label to declare affinity to
- `--db2u-affinity-value DB2_AFFINITY_VALUE`         Set the value of the node label to affine with
- `--db2u-tolerate-key DB2_TOLERATE_KEY`             Set a node taint to tolerate
- `--db2u-tolerate-value DB2_TOLERATE_VALUE`         Set the value of the taint to tolerate
- `--db2u-tolerate-effect DB2_TOLERATE_EFFECT`       Set the effect that will be tolerated (NoSchedule, PreferNoSchedule, or NoExecute)

### Advanced Db2u Universal Operator Configuration - Resource Requests (Optional):
- `--db2u-cpu-request DB2_CPU_REQUESTS`              Customise Db2 CPU request
- `--db2u-cpu-limit DB2_CPU_LIMITS`                  Customise Db2 CPU limit
- `--db2u-memory-request DB2_MEMORY_REQUESTS`        Customise Db2 memory request
- `--db2u-memory-limit DB2_MEMORY_LIMITS`            Customise Db2 memory limit

### Advanced Db2u Universal Operator Configuration - Storage (Optional):
- `--db2u-backup-storage DB2_BACKUP_STORAGE_SIZE`    Customise Db2 storage capacity
- `--db2u-data-storage DB2_DATA_STORAGE_SIZE`        Customise Db2 storage capacity
- `--db2u-logs-storage DB2_LOGS_STORAGE_SIZE`        Customise Db2 storage capacity
- `--db2u-meta-storage DB2_META_STORAGE_SIZE`        Customise Db2 storage capacity
- `--db2u-temp-storage DB2_TEMP_STORAGE_SIZE`        Customise Db2 storage capacity

### Other Commands:
- `--no-wait-for-pvcs` If you are using using storage classes that utilize 'WaitForFirstConsumer' binding mode use this flag
- `--no-confirm`       Mirror images without prompting for confirmation
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
  --no-confirm
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
    - Must only use lowercase letters, numbers, and hypen (`-`) symbol
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
Additional resource definitions can be applied to the OpenShift Cluster during the MAS configuration step, here you will be asked whether you wish to provide any additional configurations and if you do in what directory they reside.

!!! note
    If you provided one or more JDBC configurations in step 9 then additional configurations will already be enabled and be pointing at the directory you chose for the JDBC configurations.

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
    Unfortunately there is no way for the install to verify that the storage class selected actually supports the appropriate access mode, refer to the documention from the storage class provider to determine whetheryour storage class supports `ReadWriteOnce` and/or `ReadWriteMany`.


### Step 13. Advanced Settings
These settings can generally be ignored for most installations.

#### Change Cluster monitoring storage defaults?
Answering "y" at the prompt will allow you to customize the storage capacity and data retention period in Grafana and Prometheus.

#### Change default install namespaces?
Answering "y" will allow you to customise the namespace where Db2, Grafana, and MongoDb are installed in the cluster.


### Step 15. Configure IBM Container Registry
Provide your IBM entitlement key.  If you have set the `IBM_ENTITLEMENT_KEY` environment variable then you will first be prompted whether you just want to re-use the saved entitlement key.


### Step 16. Configure Product License
Provide your license ID and the location of your license file.


### Step 19. Configure UDS
Maximo Application Suite's required integration with IBM User Data Services requires your e-mail address and first/last name be provided.


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
        - [Watson Discovery](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.0?topic=services-watson-discovery)
        - [Watson Studio](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.0?topic=services-watson-studio)
        - [Watson Machine Learning](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.0?topic=services-watson-machine-learning)
        - [Watson OpenScale](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.0?topic=services-watson-openscale)
        - [Analytics Engine (Apache Spark)](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.0?topic=services-analytics-engine-powered-by-apache-spark)
- Suite core services installation
- Suite application installation

The installer will automatically provision and set up the required dependencies based on the applications that you select to install.

The install can be launched with the command `mas install`.  The end result will be a pipeline run started in your target cluster where you can track the progress of the installation.

![](../img/pipelineruns.png)
