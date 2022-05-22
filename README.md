# One-Click MAS Installer

The install itself is performed inside your RedHat OpenShift cluster utilizing [Openshift Pipelines](https://cloud.redhat.com/learn/topics/ci-cd)

> OpenShift Pipelines is a Kubernetes-native CI/CD solution based on Tekton. It builds on Tekton to provide a CI/CD experience through tight integration with OpenShift and Red Hat developer tools. OpenShift Pipelines is designed to run each step of the CI/CD pipeline in its own container, allowing each step to scale independently to meet the demands of the pipeline.

The engine that performs the installation is written in Ansible, and you can directly use the same automtion outside of this installer if you wish.  The code is open source and available in [GitHub](https://github.com/ibm-mas/ansible-devops), the collection is also available to install directly from [Ansible Galaxy](https://galaxy.ansible.com/ibm/mas_devops).

![](docs/pipeline.png)

There are minimal dependencies to meet on your own computer:
- Bash
- OpenShift client
- Network access to the OpenShift cluster

Alternatively run the install from inside our docker container image: `docker run -ti quay.io/ibmmas/installer`

The install is designed to work on any OCP cluster, but has been specifically tested in these environments:
- IBMCloud ROKS
- Azure
- IBM DevIT Fyre (internal)

## One-Click Install
All settings can be controlled via environment variables to avoid needing to manually type them out, for example if you `export CPD_ENTITLEMENT_KEY=xxxx` then when you run the install that input will be prefilled with the value from the environment variable, allowing you to press Enter to continue, or modify the value if you need to.

Before running the installer you must login to the OpenShift cluster that you want to install MAS into using the `oc login` command.

The installers supports:
- IBM Operator Catalog Configuration
- Required Dependency Installation:
  - MongoDb
  - IBM Suite License Service
  - IBM User Data Services
  - IBM Certificate Manager
  - Service Binding Operator
- Optional Dependency Installation:
  - Apache Kafka
  - IBM Db2
  - IBM Cloud Pak for Data
    - [Watson Discovery](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.0?topic=services-watson-discovery)
    - [Watson Studio](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.0?topic=services-watson-studio)
    - [Watson Machine Learning](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.0?topic=services-watson-machine-learning)
    - [Watson OpenScale](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.0?topic=services-watson-openscale)
    - [Analytics Engine (Apache Spark)](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.0?topic=services-analytics-engine-powered-by-apache-spark)
- Suite Core Services Installation
- Suite Application Installation:
  - IoT
  - Manage
  - Monitor
  - MSO
  - Predict
  - Safety

The installer will automatically provision and set up the required dependencies based on the applications that you select to install.

```bash
$ mas install djp2204b
Connected to OCP cluster: https://console-openshift-console.djp2204b-6f1620198115433da1cac8216c06779b-0000.eu-gb.containers.appdomain.cloud
Proceed with installation on this cluster [y/N]  y
 - Installing OpenShift Pipelines Operator
 - Installing Maximo Application Suite Pipeline Definition

Configure Installation:
  MAS_CHANNEL:
    1. 8.7
    2. 8.6
  Select Subscription Channel> 1

  CPD_ENTITLEMENT_KEY> *******************
  MAS_LICENSE_FILE> /home/david/maximoappsuite/devops-configs/config/authorized_entitlement.lic
  UDS_CONTACT_EMAIL> email@uk.ibm.com
  UDS_CONTACT_FIRSTNAME> David
  UDS_CONTACT_LASTNAME> Parker

Select Applications:
  Install IoT Application [y/N] n
  Install Manage Application [y/N] n


IBMCloud Settings
-------------------------------------------------------------
IBMCLOUD_APIKEY ........... ********...

IBM Maximo Application Suite Settings
-------------------------------------------------------------
MAS_INSTANCE_ID ........... djp2204b
MAS_CATALOG_SOURCE ........ ibm-operator-catalog
MAS_CHANNEL ............... 8.7.x
MAS_ICR_CP ................ cp.icr.io/cp
MAS_ICR_CPOPEN ............ icr.io/cpopen
MAS_ENTITLEMENT_USERNAME .. email@uk.ibm.com
MAS_ENTITLEMENT_KEY ....... ********...

CloudPak for Data Settings
-------------------------------------------------------------
CPD_ENTITLEMENT_KEY ....... eyJhbGci...

IBM Suite License Service Settings
-------------------------------------------------------------
SLS_LICENSE_ID ............ ********
SLS_ICR_CP ................ cp.icr.io/cp
SLS_ICR_CPOPEN ............ icr.io/cpopen
SLS_ENTITLEMENT_USERNAME .. email@uk.ibm.com
SLS_ENTITLEMENT_KEY ....... ********...
SLS_LICENSE_FILE .......... /workspace/entitlement/authorized_entitlement.lic

IBM User Data Services Settings
-------------------------------------------------------------
UDS_CONTACT_EMAIL ......... email@uk.ibm.com
UDS_CONTACT_FIRSTNAME ..... David
UDS_CONTACT_LASTNAME ...... Parker

Connected to OCP cluster: https://console-openshift-console.djp2204b-6f1620198115433da1cac8216c06779b-0000.eu-gb.containers.appdomain.cloud
Proceed with these settings [y/N]  y

View progress: https://console-openshift-console.djp2204b-6f1620198115433da1cac8216c06779b-0000.eu-gb.containers.appdomain.cloud/pipelines/ns/mas-djp2204b-pipelines
```

![](docs/pipelineruns.png)


## Mustgather
The pipeline sets a "finally" block that is executed at the end of the steps regardless of success or failure. Inside this finally block the **mustgather** ClusterTask is executed which runs the IBM AI Applications' Must Gather tool against a MAS instance. It uses the mustgather workspace to persist the output into a Persistent Volume for retrieval after the pipeline has completed.

Users can then use the **ibm.mas_devops.suite_mustgather_download** playbook locally to pull the mustgather output from the persistent volume.

Note: The **mustgather** clusterTask will clear any previous content found in the `/workspace/mustgather` persistent volume before each call to the mustgather playbook. This is to ensure that the persistent volume does not become full after multiple runs using the same persistent volume/namespace.

## Other Utilities
### Provision a ROKS Cluster
This is a convenient utility to easily provision a new RedHat OpenShift Cluster in IBM Cloud.  It it not part of the MAS installer.

```bash
$ bin/mas-provision-roks mycluster
```

