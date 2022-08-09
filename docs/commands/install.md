# Install

## Details
The install is performed inside your RedHat OpenShift cluster utilizing [Openshift Pipelines](https://cloud.redhat.com/learn/topics/ci-cd)

> OpenShift Pipelines is a Kubernetes-native CI/CD solution based on Tekton. It builds on Tekton to provide a CI/CD experience through tight integration with OpenShift and Red Hat developer tools. OpenShift Pipelines is designed to run each step of the CI/CD pipeline in its own container, allowing each step to scale independently to meet the demands of the pipeline.

![](../img/pipeline.png)

The installer supports:

- IBM operator catalog configuration
- Required dependency installation:
    - MongoDb
    - IBM Suite License Service
    - IBM User Data Services
    - IBM Certificate Manager
    - Red Hat Service Binding Operator
- Optional dependency installation:
    - Apache Kafka
    - IBM Db2
    - IBM Cloud Pak for Data
        - [Watson Discovery](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.0?topic=services-watson-discovery)
        - [Watson Studio](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.0?topic=services-watson-studio)
        - [Watson Machine Learning](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.0?topic=services-watson-machine-learning)
        - [Watson OpenScale](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.0?topic=services-watson-openscale)
        - [Analytics Engine (Apache Spark)](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.0?topic=services-analytics-engine-powered-by-apache-spark)
- Suite core services installation
- Suite application installation

The installer will automatically provision and set up the required dependencies based on the applications that you select to install.

The install can be launched with the command `mas install`.  The end result will be a pipeline run being started in your target cluster where you can track the progress of the installation.

![](../img/pipelineruns.png)


## Pre-reqs

### 1. IBM Entitlement key
Access [Container Software Library](https://myibm.ibm.com/products-services/containerlibrary) using your IBMId to access your entitlement key

### 2. MAS License File
Access [IBM License Key Center](https://licensing.subscribenet.com/control/ibmr/login), on the **Get Keys** menu select **IBM AppPoint Suites**.  Select `IBM MAXIMO APPLICATION SUITE AppPOINT LIC` and on the next page fill in the information as below:

| Field            | Content                                           |
| ---------------- | ------------------------------------------------- |
| Number of Keys   | How many AppPoints to assign to the license file  |
| Host ID Type     | Set to **Ethernet Address**                       |
| Host ID          | Enter any 12 digit hexadecimal string             |
| Hostname         | Set to the hostname of your OCP instance          |
| Port             | Set to **27000**                                  |


The other values can be left at their defaults.  Finally, click **Generate** and download the license file to your home directory as `entitlement.lic`.

!!! note
    For more information about how to access the IBM License Key Center review the [getting started documentation](https://www.ibm.com/support/pages/system/files/inline-files/GettingStartedEnglish_2020.pdf) available from the IBM support website.


## Usage

!!! important
    We will need the `entitlement.lic` file to perform the installation which is why we mount your home directory into the container.  If you saved the entitlement file elsewhere, mount that directory instead.

    When prompted you will be able to set license file to `/home/local/entitlement.lic`


```bash
docker pull quay.io/ibmmas/cli
docker run -ti --rm -v ~:/home/local quay.io/ibmmas/cli
mas install
```

## Mustgather
The pipeline sets a "finally" block that is executed at the end of the steps regardless of success or failure. Inside this finally block the **mustgather** Task is executed which runs the IBM AI Applications' Must Gather tool against a MAS instance. It uses the mustgather workspace to persist the output into a Persistent Volume for retrieval after the pipeline has completed.

Users can then use the **ibm.mas_devops.suite_mustgather_download** playbook locally to pull the mustgather output from the persistent volume.

!!! note
    The **mustgather** Task will clear any previous content found in the `/workspace/mustgather` persistent volume before each call to the mustgather playbook. This is to ensure that the persistent volume does not become full after multiple runs using the same persistent volume/namespace.
