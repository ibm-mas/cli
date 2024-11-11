Install
===============================================================================

Usage
-------------------------------------------------------------------------------
For full usage information run `mas install --help`


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


### Connect to OpenShift
If you are not already connected to an OpenShift cluster you will be prompted to provide the server URL & token, and whether to verify the server certificate or not.

```
1) Set Target OpenShift Cluster
Server URL: https://c100-e.eu-gb.containers.cloud.ibm.com:32173
Login Token: **************************************************
Disable TLS Verify? [y/n] n
```

If you are already connected to a cluster you will be given the option to change to another cluster.

```
1) Set Target OpenShift Cluster
Already connected to OCP Cluster:
 https://console-openshift-console.xarchtest-6f1620198115433da1cac8216c06779b-0000.eu-gb.containers.appdomain.cloud

Proceed with this cluster? [y/n]
```

### Choose a Catalog Source
You will be presented with a table of available catalogs with information about the different releases of MAS available in each.  Make the selection using the numbers in the first column.

```
2) IBM Maximo Operator Catalog Selection
┌─────┬─────────────────┬───────────┬─────────┬──────────┬────────┬──────────┬───────────┬─────────────┬───────────┬──────────────┬────────────┐
│   # │ catalog         │ release   │ core    │ assist   │ iot    │ manage   │ monitor   │ optimizer   │ predict   │ inspection   │ aibroker   │
├─────┼─────────────────┼───────────┼─────────┼──────────┼────────┼──────────┼───────────┼─────────────┼───────────┼──────────────┼────────────┤
│   1 │ v9-241003-amd64 │ 9.0.x     │ 9.0.3   │ 9.0.2    │ 9.0.3  │ 9.0.3    │ 9.0.3     │ 9.0.3       │ 9.0.2     │ 9.0.3        │ 9.0.2      │
├─────┼─────────────────┼───────────┼─────────┼──────────┼────────┼──────────┼───────────┼─────────────┼───────────┼──────────────┼────────────┤
│   2 │ v9-241003-amd64 │ 8.11.x    │ 8.11.15 │ 8.8.6    │ 8.8.13 │ 8.7.12   │ 8.11.11   │ 8.5.9       │ 8.9.5     │ 8.9.6        │            │
├─────┼─────────────────┼───────────┼─────────┼──────────┼────────┼──────────┼───────────┼─────────────┼───────────┼──────────────┼────────────┤
│   3 │ v9-241003-amd64 │ 8.10.x    │ 8.10.18 │ 8.7.7    │ 8.7.17 │ 8.6.18   │ 8.10.14   │ 8.4.10      │ 8.8.3     │ 8.8.4        │            │
├─────┼─────────────────┼───────────┼─────────┼──────────┼────────┼──────────┼───────────┼─────────────┼───────────┼──────────────┼────────────┤
│   4 │ v9-240827-amd64 │ 9.0.x     │ 9.0.2   │ 9.0.2    │ 9.0.2  │ 9.0.2    │ 9.0.2     │ 9.0.2       │ 9.0.1     │ 9.0.2        │            │
├─────┼─────────────────┼───────────┼─────────┼──────────┼────────┼──────────┼───────────┼─────────────┼───────────┼──────────────┼────────────┤
│   5 │ v9-240827-amd64 │ 8.11.x    │ 8.11.14 │ 8.8.6    │ 8.8.12 │ 8.7.11   │ 8.11.10   │ 8.5.8       │ 8.9.3     │ 8.9.5        │            │
├─────┼─────────────────┼───────────┼─────────┼──────────┼────────┼──────────┼───────────┼─────────────┼───────────┼──────────────┼────────────┤
│   6 │ v9-240827-amd64 │ 8.10.x    │ 8.10.17 │ 8.7.7    │ 8.7.16 │ 8.6.17   │ 8.10.13   │ 8.4.9       │ 8.8.3     │ 8.8.4        │            │
├─────┼─────────────────┼───────────┼─────────┼──────────┼────────┼──────────┼───────────┼─────────────┼───────────┼──────────────┼────────────┤
│   7 │ v9-240730-amd64 │ 9.0.x     │ 9.0.1   │ 9.0.1    │ 9.0.1  │ 9.0.1    │ 9.0.1     │ 9.0.1       │ 9.0.0     │ 9.0.0        │            │
├─────┼─────────────────┼───────────┼─────────┼──────────┼────────┼──────────┼───────────┼─────────────┼───────────┼──────────────┼────────────┤
│   8 │ v9-240730-amd64 │ 8.11.x    │ 8.11.13 │ 8.8.5    │ 8.8.11 │ 8.7.10   │ 8.11.9    │ 8.5.7       │ 8.9.3     │ 8.9.4        │            │
├─────┼─────────────────┼───────────┼─────────┼──────────┼────────┼──────────┼───────────┼─────────────┼───────────┼──────────────┼────────────┤
│   9 │ v9-240730-amd64 │ 8.10.x    │ 8.10.16 │ 8.7.6    │ 8.7.15 │ 8.6.16   │ 8.10.12   │ 8.4.8       │ 8.8.3     │ 8.8.4        │            │
└─────┴─────────────────┴───────────┴─────────┴──────────┴────────┴──────────┴───────────┴─────────────┴───────────┴──────────────┴────────────┘
Select catalog and release 1
```

### Accept the License Terms
Confirm that you accept the IBM Maximo Application Suite license terms

```
3) License Terms
To continue with the installation, you must accept the license terms:
 - https://ibm.biz/MAS90-License
 - https://ibm.biz/MaximoIT90-License
 - https://ibm.biz/MAXArcGIS90-License
Do you accept the license terms? [y/n] y
```

### Select Storage Classes
MAS requires both a `ReadWriteMany` and a `ReadWriteOnce` capable storage class to be available in the cluster.  The installer has the ability to recognize certain storage class providers and will default to the most appropriate storage class in these cases:

- IBMCloud Storage (`ibmc-block-gold` & `ibmc-file-gold`)
- OpenShift Container Storage (`ocs-storagecluster-ceph-rbd` & `ocs-storagecluster-cephfs`)
- Azure Managed Storage (`azurefiles-premium` & `managed-premium`)
- AWS Storage (`gp2` & `efs`)

Even when a recognized storage provider is detected you will be provided with the option to select your own storages classes anyway.

When selecting storage classes you will be presented with a list of available storage classes and must select both a `ReadWriteMany` and a `ReadWriteOnce` storage class.

```
4) Configure Storage Class Usage
Maximo Application Suite and it's dependencies require storage classes that support ReadWriteOnce (RWO) and ReadWriteMany (RWX) access modes:
  - ReadWriteOnce volumes can be mounted as read-write by multiple pods on a single node.
  - ReadWriteMany volumes can be mounted as read-write by multiple pods across many nodes.

Storage provider auto-detected: IBMCloud ROKS
  - Storage class (ReadWriteOnce): ibmc-block-gold
  - Storage class (ReadWriteMany): ibmc-file-gold-gid
Use the auto-detected storage classes? [y/n] y
```

!!! warning
    Unfortunately there is no way for the install to verify that the storage class selected actually supports the appropriate access mode, refer to the documentation from the storage class provider to determine whether your storage class supports `ReadWriteOnce` and/or `ReadWriteMany`.

### Provide a License File
Provide the location of your license file and your contact information.

```
5) Configure Product License
License file /mnt/home/entitlement.lic
Contact e-mail address test@uk.ibm.com
Contact first name David
Contact last name Parker
IBM Data Reporter Operator (DRO) Namespace redhat-marketplace
```

### Provide your IBM Entitlement Key
Provide your IBM entitlement key.  If you have set the `IBM_ENTITLEMENT_KEY` environment variable then this field will be pre-filled with that value already.

```
6) Configure IBM Container Registry
IBM entitlement key ******************************************
```

### Configure your MAS Instance
Provide the basic information about your MAS instance:

- Instance ID
- Workspace ID
- Workspace Display Name

```
7) Configure MAS Instance
Instance ID restrictions:
 - Must be 3-12 characters long
 - Must only use lowercase letters, numbers, and hypen (-) symbol
 - Must start with a lowercase letter
 - Must end with a lowercase letter or a number
Instance ID mas1

Workspace ID restrictions:
 - Must be 3-12 characters long
 - Must only use lowercase letters and numbers
 - Must start with a lowercase letter
Workspace ID ws1

Workspace display name restrictions:
 - Must be 3-300 characters long
Workspace name ws1
```

### Choose Operational Mode
The install will default to a production mode installation, but by choosing "y" at the prompt you will be able to install MAS in non-production mode.

```
8) Configure Operational Mode
Maximo Application Suite can be installed in a non-production mode for internal development and testing, this setting cannot be changed after installation:
 - All applications, add-ons, and solutions have 0 (zero) installation AppPoints in non-production installations.
 - These specifications are also visible in the metrics that are shared with IBM and in the product UI.

  1. Production
  2. Non-Production
Operational Mode 2
```

### Configure Root CA Trust
```
9) Certificate Authority Trust
By default, Maximo Application Suite is configured to trust well-known certificate authoritories, you can disable this so that it will only trust the CAs that you explicitly define
Trust default CAs? [y/n] y
```

### Override the OpenShift Ingress Secret
```
10) Cluster Ingress Secret Override
In most OpenShift clusters the installation is able to automatically locate the default ingress certificate, however in some configurations it is necessary to manually configure the name of the secret
Unless you see an error during the ocp-verify stage indicating that the secret can not be determined you do not need to set this and can leave the response empty
Cluster ingress certificate secret name
```

### Configure Domain & Certificate Management
By default MAS will be installed in a subdomain of your OpenShift clusters domain matching the MAS instance ID that you chose.  For example if your OpenShift cluster is `myocp.net` and you are installing MAS with an instance ID of `prod1` then MAS will be installed with a default domain something like `prod1.apps.myocp.net`, depending on the exact network configuration of your cluster.

If you wish to use a custom domain for the MAS install you can choose to configure this by selecting "n" at the prompt.  The install supports DNS integrations for Cloudflare, IBM Cloud Internet Services, AWS Route 53 out of the box and is able to configure a certificate issuer using LetsEncrypt (production or staging) or a self-signed certificate authority per your choices.

```
11) Configure Domain & Certificate Management
Configure domain & certificate management? [y/n] n
```

### Customize MAS SSO
```
12) Single Sign-On (SSO)
Many aspects of Maximo Application Suite's Single Sign-On (SSO) can be customized:
 - Idle session automatic logout timer
 - Session, access token, and refresh token timeouts
 - Default identity provider (IDP), and seamless login
 - Brower cookie properties
Configure SSO properties? [y/n] n
```

### Allow special character in User IDs and Usernames
```
13) Configure special characters for userID and username
Do you want to allow special characters for user IDs and usernames?? [y/n] n
```

### Configure Whether Guided Tours Are Shown
```
14) Enable Guided Tour
By default, Maximo Application Suite is configured with guided tour, you can disable this if it not required
Enable Guided Tour? [y/n] n
```

### Application Selection
Select the applications that you would like to install. Note that some applications cannot be installed unless an application they depend on is also installed:

- Monitor is only available for install if IoT is selected
- Assist and Predict are only available for install if Monitor is selected

```
15) Application Selection
Install IoT? [y/n] n
Install Manage? [y/n] y
Install Assist? [y/n] n
Install Optimizer? [y/n] n
Install Visual Inspection? [y/n] n
Install AI Broker? [y/n] n
```

### Application Configuration
```
16) Configure Maximo Manage
Customize your Manage installation, refer to the product documentation for more information

16.1) Maximo Manage Components
The default configuration will install Manage with Health enabled, alternatively choose exactly what industry solutions and add-ons will be configured
Select components to enable? [y/n] y
 - Asset Configuration Manager? [y/n] n
 - Aviation? [y/n] n
 - Civil Infrastructure? [y/n] n
 - Envizi? [y/n] n
 - Health? [y/n] n
 - Health, Safety and Environment? [y/n] n
 - Maximo IT? [y/n] n
 - Nuclear? [y/n] n
 - Oil & Gas? [y/n] n
 - Connector for Oracle Applications? [y/n] n
 - Connector for SAP Application? [y/n] n
 - Service Provider? [y/n] n
 - Spatial? [y/n] n
 - Strategize? [y/n] n
 - Transportation? [y/n] n
 - Tririga? [y/n] n
 - Utilities? [y/n] n
 - Workday Applications? [y/n] n

16.2) Maximo Manage Settings - Server Bundles
Define how you want to configure Manage servers:
 - You can have one or multiple Manage servers distributing workload
 - Additionally, you can choose to include JMS server for messaging queues

Configurations:
  1. Deploy the 'all' server pod only (workload is concentrated in just one server pod but consumes less resource)
  2. Deploy the 'all' and 'jms' bundle pods (workload is concentrated in just one server pod and includes jms server)
  3. Deploy the 'mea', 'report', 'ui' and 'cron' bundle pods (workload is distributed across multiple server pods)
  4. Deploy the 'mea', 'report', 'ui', 'cron' and 'jms' bundle pods (workload is distributed across multiple server pods and includes jms server)
Select a server bundle configuration 1

16.3) Maximo Manage Settings - Database
Customise the schema, tablespace, indexspace, and encryption settings used by Manage
Customize database settings? [y/n] n

16.4) Maximo Manage Settings - Customization
Provide a customization archive to be used in the Manage build process
Include customization archive? [y/n] n

16.5) Maximo Manage Settings - Other
Configure additional settings:
  - Demo data
  - Base and additional languages
  - Server timezone
  - Cognos integration (install Cloud Pak for Data)
  - Watson Studio Local integration (install Cloud Pak for Data)
Configure Additional Settings? [y/n] n
```

### Configure MongoDb
```
17) Configure MongoDb
Install namespace mongoce
```

### Configure Databases
If you have selected one or more applications that require a JDBC datasource (IoT, Manage, Monitor, & Predict) you must choose how to provide that dependency:

- Use the IBM Db2 Universal Operator
- Provide a JDBC configuration

If you choose the latter then you will be prompted to select a local directory where the configuration will be staged and requested to provide a display name, the JDBC connection URL, username, password, and whether the endpoint is SSL enabled (if it is then you will also be asked to provide the SSL certificate required to connect to the database).

!!! tip
    If you have already generated the configuration file (manually, or using the install previously) the CLI will detect this and prompt whether you wish to re-use the existing configuration, or generate a new one.

```
18) Configure Databases
The installer can setup one or more IBM Db2 instances in your OpenShift cluster for the use of applications that require a JDBC datasource (IoT, Manage, Monitor, & Predict) or you may choose to configure MAS to use an existing database

18.1) Database Configuration for Maximo Manage
Maximo Manage can be configured to share the system Db2 instance or use it's own dedicated database:
 - Use of a shared instance has a significant footprint reduction but is only recommended for development/test/demo installs
 - In most production systems you will want to use a dedicated database
 - IBM Db2, Oracle Database, & Microsoft SQL Server are all supported database options
Create manage dedicated Db2 instance using the IBM Db2 Universal Operator? [y/n] y
Available Db2 instance types for Manage:
  1. DB2 Warehouse (Default option)
  2. DB2 Online Transactional Processing (OLTP)
Select the Manage dedicated DB2 instance type 1

18.2) Installation Namespace
Install namespace db2u

18.3) Node Affinity and Tolerations
Note that the same settings are applied to both the IoT and Manage Db2 instances
Use existing node labels and taints to control scheduling of the Db2 workload in your cluster
For more information refer to the Red Hat documentation:
 - https://docs.openshift.com/container-platform/4.12/nodes/scheduling/nodes-scheduler-node-affinity.html
 - https://docs.openshift.com/container-platform/4.12/nodes/scheduling/nodes-scheduler-taints-tolerations.html
Configure node affinity? [y/n] n
Configure node tolerations? [y/n] n

18.4) Database CPU & Memory
Note that the same settings are applied to both the IoT and Manage Db2 instances
Customize CPU and memory request/limit? [y/n] n

18.5) Database Storage Capacity
Note that the same settings are applied to both the IoT and Manage Db2 instances
Customize storage capacity? [y/n] n
```

### Configure Grafana
```
19) Configure Grafana
Install namespace grafana5
Grafana storage size 10Gi
```

### Configure Turbonomic
The [IBM Turbonomic](https://www.ibm.com/products/turbonomic) hybrid cloud cost optimization platform allows you to eliminate this guesswork with solutions that save time and optimize costs.  To enable Turbonomic integration you must provide the following information:

- Target name
- Server URL
- Server version
- Authentication credentials (username & password)

```
20) Configure Turbonomic
The IBM Turbonomic hybrid cloud cost optimization platform allows you to eliminate this guesswork with solutions that save time and optimize costs
 - Learn more: https://www.ibm.com/products/turbonomic
Configure IBM Turbonomic integration? [y/n] n
```

### Additional Configurations
Additional resource definitions can be applied to the OpenShift Cluster during the MAS configuration step, here you will be asked whether you wish to provide any additional configurations and if you do in what directory they reside.

!!! note
    If you provided one or more JDBC configurations in step 9 then additional configurations will already be enabled and be pointing at the directory you chose for the JDBC configurations.

```
21) Additional Configuration
Additional resource definitions can be applied to the OpenShift Cluster during the MAS configuration step
The primary purpose of this is to apply configuration for Maximo Application Suite itself, but you can use this to deploy ANY additional resource into your cluster
Use additional configurations? [y/n] n
```

### Pod Templates
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

!!! Note
    This feature is only supported starting in MAS 8.11.0 and SLS 3.8.0

```
22) Configure Pod Templates
The CLI supports two pod template profiles out of the box that allow you to reconfigure MAS for either a guaranteed or best effort QoS level
For more information about the Kubernetes quality of service (QoS) levels, see https://kubernetes.io/docs/concepts/workloads/pods/pod-qos/
You may also choose to use your own customized pod template definitions
Use pod templates? [y/n] n
```

### Review Choices
```
23) Non-Interactive Install Command
Save and re-use the following script to re-run this install without needing to answer the interactive prompts again

export IBM_ENTITLEMENT_KEY=x
mas install --mas-catalog-version v9-241003-amd64 --ibm-entitlement-key $IBM_ENTITLEMENT_KEY \
  --mas-channel 9.0.x --mas-instance-id mas1 --mas-workspace-id ws1 --mas-workspace-name "ws1" \
  --non-prod \
  --disable-walkme \
  --storage-class-rwo "ibmc-block-gold" --storage-class-rwx "ibmc-file-gold-gid" \
  --storage-pipeline "ibmc-file-gold-gid" --storage-accessmode "ReadWriteMany" \
  --license-file "/mnt/home/entitlement.lic" \
  --uds-email "parkerda@uk.ibm.com" --uds-firstname "David" --uds-lastname "Parker" \
  --dro-namespace "redhat-marketplace" \
  --mongodb-namespace "mongoce" \
  --manage-channel "9.0.x" \
  --manage-jdbc "workspace-application" \
  --manage-components "base=latest" \
  --manage-server-bundle-size "dev" \
  --accept-license --no-confirm

24) Review Settings
Connected to:
 - https://openshift-cluster.containers.appdomain.cloud

24.1) OpenShift Container Platform
  Storage Class Provider .................. ibmc
  ReadWriteOnce Storage Class ............. ibmc-block-gold
  ReadWriteMany Storage Class ............. ibmc-file-gold-gid
  Certificate Manager ..................... redhat
  Cluster Ingress Certificate Secret ...... Default
  Single Node OpenShift ................... No
  Skip Pre-Install Healthcheck ............ No
  Skip Grafana-Install .................... No

24.2) IBM Data Reporter Operator (DRO) Configuration
  Contact e-mail .......................... test@uk.ibm.com
  First name .............................. David
  Last name ............................... Parker
  Install Namespace ....................... redhat-marketplace

24.3) IBM Suite License Service
  License File ............................ /mnt/home/entitlement.lic
  IBM Open Registry ....................... icr.io/cpopen

24.4) IBM Maximo Application Suite
  Instance ID ............................. mas1
  Workspace ID ............................ ws1
  Workspace Name .......................... ws1

  Operational Mode ........................ Non-Production
  Install Mode ............................ Connected Install

  Manual Certificates ..................... Not Configured

  Enable Guided Tour ...................... false

  Catalog Version ......................... v9-241003-amd64
  Subscription Channel .................... 9.0.x

  IBM Entitled Registry ................... cp.icr.io/cp
  IBM Open Registry ....................... icr.io/cpopen

  Trust Default Cert Authorities .......... true

  Additional Config ....................... Not Configured
  Pod Templates ........................... Not Configured

24.5) IBM Maximo Application Suite Applications
  IoT ..................................... Do Not Install
  Monitor ................................. Do Not Install
  Manage .................................. 9.0.x
  + Components
    + ACM ................................. Disabled
    + Aviation ............................ Disabled
    + Civil Infrastructure ................ Disabled
    + Envizi .............................. Disabled
    + Health .............................. Disabled
    + HSE ................................. Disabled
    + Maximo IT ........................... Disabled
    + Nuclear ............................. Disabled
    + Oil & Gas ........................... Disabled
    + Connector for Oracle ................ Disabled
    + Connector for SAP ................... Disabled
    + Service Provider .................... Disabled
    + Spatial ............................. Disabled
    + Strategize .......................... Disabled
    + Transportation ...................... Disabled
    + Tririga ............................. Disabled
    + Utilities ........................... Disabled
    + Workday Applications ................ Disabled
  + Server bundle size .................... dev
  + Enable JMS queues ..................... Default
  + Server Timezone ....................... Default
  + Base Language ......................... Default
  + Additional Languages .................. Default
  + Database Settings
    + Schema .............................. Default
    + Username ............................ Default
    + Tablespace .......................... Default
    + Indexspace .......................... Default
  Loc Srv Esri (arcgis) ................... Do Not Install
  Predict ................................. Do Not Install
  Optimizer ............................... Do Not Install
  Assist .................................. Do Not Install
  Visual Inspection ....................... Do Not Install
  AI Broker ............................... Do Not Install

24.6) MongoDb
  Install Namespace ....................... mongoce

24.7) IBM Db2 Univeral Operator Configuration
  System Instance ......................... Do Not Install
  Dedicated Manage Instance ............... Install
   - Type ................................. db2wh
   - Timezone ............................. Default

  Install Namespace ....................... db2u
  Subscription Channel .................... v110509.0

  CPU Request ............................. 4000m
  CPU Limit ............................... 6000m
  Memory Request .......................... 8Gi
  Memory Limit  ........................... 12Gi

  Meta Storage ............................ 20Gi
  Data Storage ............................ 100Gi
  Backup Storage .......................... 100Gi
  Temp Storage ............................ 100Gi
  Transaction Logs Storage ................ 100Gi

  Node Affinity ........................... None
  Node Tolerations ........................ None

24.8) Cloud Object Storage
  Type .................................... None

24.9) Grafana
  Install Grafana ......................... Install

24.10) Turbonomic
  Turbonomic Integration .................. Disabled

Please carefully review your choices above, correcting mistakes now is much easier than after the install has begun
Proceed with these settings? [y/n] y
```


Air Gap Support
-------------------------------------------------------------------------------
If you have already ran `mas configure-airgap` to install the ImageContentSourcePolicy for IBM Maximo Application Suite then the installer will automatically detect the presence of this and tailor the installation configuration for a disconnected installation.


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
The install pipeline supports:

- IBM Maximo Operator Catalog installation
- Required dependency installation:
    - MongoDb (Community Edition)
    - IBM Suite License Service
    - IBM Data Reporter Operator
    - Red Hat Certificate Manager
- Optional dependency installation:
    - Apache Kafka
    - IBM Db2
    - IBM Cloud Pak for Data Platform and Services
        - [Watson Studio](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.0?topic=services-watson-studio)
        - [Watson Machine Learning](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.0?topic=services-watson-machine-learning)
        - [Watson OpenScale](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.0?topic=services-watson-openscale)
        - [Analytics Engine (Apache Spark)](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.0?topic=services-analytics-engine-powered-by-apache-spark)
    - Grafana
    - Turbonomic Kubernetes Agent
- Suite core services installation
- Suite application installation

The installer will automatically provision and set up the required dependencies based on the applications that you select to install.

The install can be launched with the command `mas install`.  The end result will be a pipeline run started in your target cluster where you can track the progress of the installation.

![](../img/pipelineruns.png)
