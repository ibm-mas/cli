extra_breadcrumb_title_1: Operator Catalog
extra_breadcrumb_title_2: IBM Maximo Operator Catalog
extra_breadcrumb_url_2: ../
nav_title: Operator Catalog

IBM Maximo Operator Catalog v9 (multiarch-new)
===============================================================================

Details
-------------------------------------------------------------------------------

<table>
  <tr><td>Image</td><td>docker-na-public.artifactory.swg-devops.com/wiotp-docker-local/cpopen/ibm-maximo-operator-catalog</tr></tr>
  <tr><td>Tag</td><td>v9-multiarch-new-s390x</tr></tr>
  <tr><td>Digest</td><td>sha256:64795d088edcd888d21f45eb665c2b5ef6616d490312b4605082413704a4ff30</tr></tr> 
  <!-- ^^^^^ tbc -->
</table>


What's New
-------------------------------------------------------------------------------
- **Security updates and bug fixes**
    - IBM Maximo Application Suite Core Platform v9.1
    - IBM Maximo Manage v9.1
    - IBM Maximo IoT not supporting
    - IBM Maximo Monitor not supporting
    - IBM Maximo Optimizer not supporting
    - IBM Maximo Predict not supporting
    - IBM Maximo Visualinspection not supporting
    - IBM Data Dictionary not supporting


Manual Installation
-------------------------------------------------------------------------------
`oc apply -f https://raw.githubusercontent.com/ibm-mas/cli/master/catalogs/v9-multiarch-new-s390x.yaml`


Source
-------------------------------------------------------------------------------
```yaml
apiVersion: operators.coreos.com/v1alpha1
kind: CatalogSource
metadata:
  name: ibm-operator-catalog
  namespace: openshift-marketplace
spec:
  displayName: IBM Maximo Operators (v9-multiarch-new-s390x)
  publisher: IBM
  description: Static Catalog Source for IBM Maximo Application Suite
  sourceType: grpc
  image: docker-na-public.artifactory.swg-devops.com/wiotp-docker-local/cpopen/ibm-maximo-operator-catalog@sha256:64795d088edcd888d21f45eb665c2b5ef6616d490312b4605082413704a4ff30
  priority: 90
```

Red Hat OpenShift Container Platform Support
-------------------------------------------------------------------------------
IBM Maximo Application Suite will run only on IBM Cloud , you can run a supported OpenShift release on s390x architecture, including:

- [IBM Cloud](https://www.ibm.com/cloud/openshift)

For more information about the OCP lifecycle refer to the [Red Hat OpenShift Container Platform Life Cycle Policy](https://access.redhat.com/support/policy/updates/openshift/).

IBM Maximo Application Suite customers receive a standard Red Hat OpenShift Container Platform subscription as part of their purchase. This includes 18 months of maintenance support for each OpenShift minor release.  A further 6 months support is available to purchase as an Extended Update Support (EUS) Add-on to s390x versions of Red Hat OpenShift Kubernetes Engine, Red Hat OpenShift Container Platform, and Red Hat OpenShift Platform Plus Standard subscriptions.

!!! note
Extended Update Support is included with Premium subscriptions of s390x versions of Red Hat OpenShift Kubernetes Engine, Red Hat OpenShift Container Platform, and Red Hat OpenShift Platform Plus. Please contact your Red Hat Sales Representative if you are unsure if you have access to EUS and to help decide if it is appropriate for your environment.

<table class="compatabilityMatrix">
  <tr>
    <th>OCP</th><td rowspan="5" class="spacer"></td>
    <th>General Availability</th>
    <th>Standard Support</th>
    <th>Extended Support</th>
    <th>Supported MAS Releases</th>
  </tr>
  <tr>
    <td class="firstColumn">4.15</td>
    <td>February 27, 2024</td>
    <td>August 27, 2025</td>
    <td>N/A</td>
    <td>8.10 - 9.0</td>
  </tr>
  <tr>
    <td class="firstColumn">4.14</td>
    <td>October 31, 2023</td>
    <td>May 1, 2025</td>
    <td>October 31, 2026</td>
    <td>8.10 - 9.0</td>
  </tr>
  <tr>
    <td class="firstColumn">4.13</td>
    <td>May 17, 2023</td>
    <td>November 17, 2024</td>
    <td>N/A</td>
    <td>8.10 - 9.0</td>
  </tr>
  <tr>
    <td class="firstColumn">4.12</td>
    <td>January 17, 2023</td>
    <td>July 17, 2024</td>
    <td>January 17, 2025</td>
    <td>8.10 - 9.0</td>
  </tr>
</table>


### Certified Operators
- `registry.redhat.io/redhat/certified-operator-index:v4.15`
- `registry.redhat.io/redhat/certified-operator-index:v4.14`
- `registry.redhat.io/redhat/certified-operator-index:v4.13`
- `registry.redhat.io/redhat/certified-operator-index:v4.12`

The following packages from this catalog are used in the Maximo Application Suite install:

- **gpu-operator-certified** required by `ibm.mas_devops.nvidia_gpu` role
- **kubeturbo-certified** required by `ibm.mas_devops.kubeturbo` role


### Community Operators
- `registry.redhat.io/redhat/community-operator-index:v4.15`
- `registry.redhat.io/redhat/community-operator-index:v4.14`
- `registry.redhat.io/redhat/community-operator-index:v4.13`
- `registry.redhat.io/redhat/community-operator-index:v4.12`

The following packages from this catalog are used in the Maximo Application Suite install:

- **grafana-operator** required by `ibm.mas_devops.grafana` role
- **opentelemetry-operator** required by `ibm.mas_devops.opentelemetry` role
- **strimzi-kafka-operator** required by `ibm.mas_devops.kafka` role (if using Strimzi as Kakfa provider)


### Red Hat Operators
- `registry.redhat.io/redhat/redhat-operator-index:v4.15`
- `registry.redhat.io/redhat/redhat-operator-index:v4.14`
- `registry.redhat.io/redhat/redhat-operator-index:v4.13`

The following packages from these catalogs are used in the Maximo Application Suite install:

- **amq-streams** required by `ibm.mas_devops.kafka` role (if using AMQ Streams as Kakfa provider)
- **openshift-pipelines-operator-rh** required by the MAS CLI
- **nfd** required by `ibm.mas_devops.nvidia_gpu` role
- **aws-efs-csi-driver-operator**  required by `ibm.mas_devops.ocp_efs` role
- **local-storage-operator**  required by `ibm.mas_devops.ocs` role
- **odf-operator**  required by `ibm.mas_devops.ocs` role


IBM Cloud Pak for Data Compatibility
-------------------------------------------------------------------------------
For more information on Cloud Pak for Data's support policy review this [IBM Cloud Pak for Data Software Support Lifecycle Addendum](https://www.ibm.com/support/pages/node/6593147).

Cloud Pak for Data covers the following application's dependencies:

- **Assist**: Watson Text to Speak, Watson Speach to Text, Watson Assistant
- **Predict**: Watson Studio, Watson Machine Learning, Watson Analytics Service, Watson Openscale

<table class="compatabilityMatrix">
  <tr>
    <th class="firstColumn" rowspan="2">OCP</th>
    <td rowspan="8" class="spacer"></td>
    <th colspan="3">Cloud Pak for Data</th>
    <td rowspan="9" class="spacer"></td>
    <th rowspan="2">Supported MAS Releases</th>
  </tr>
  <tr>
    <th class="firstColumn">Release</th>
    <th>General Availability</th>
    <th>End of Support</th>
  </tr>
  <tr> <td class="firstColumn" rowspan="1">4.14</td><td>4.8.0</td>            <td>March, 2024</td>    <td>TBD</td> <td>8.10 - 9.0</td></tr>
  <tr> <td class="firstColumn" rowspan="1">4.13</td><td>4.8.0</td>            <td>March, 2024</td>    <td>TBD</td> <td>8.10 - 9.0</td></tr>
  <tr> <td class="firstColumn" rowspan="1">4.12</td><td>4.8.0</td>            <td>February, 2023</td>    <td>February, 2024</td> <td>8.10 - 8.11</td> </tr>
</table>


Package Manifest
-------------------------------------------------------------------------------



### IBM Maximo Application Suite
| Package                  | Default Channel | Channel     | Latest Version |
|--------------------------|-----------------|-------------|----------------|
| ibm-mas                  | 9.0.x           | 9.0.x       | 9.0.x          |
| ibm-mas-aibroker         | not support     | not support | not support    |
| ibm-mas-arcgis           | not support     | not support | not support    |
| ibm-mas-assist           | not support     | not support | not support    |
| ibm-mas-hputilities      | not support     | not support | not support    |
| ibm-mas-iot              | not support     | not support | not support    |
| ibm-mas-manage           | 9.1.x           | 9.1.x       | 9.1.x          |
| ibm-mas-monitor          | not support     | not support | not support    |
| ibm-mas-optimizer        | not support     | not support | not support    |
| ibm-mas-predict          | not support     | not support | not support    |
| ibm-mas-visualinspection | not support     | not support | not support    |



### IBM Utilities
| Package             | Default Channel   | Channel   | Latest Version   |
|---------------------|-------------------|-----------|------------------|
| ibm-data-dictionary | 1.1.x             | 1.1.x     | 1.1.12           |
| ibm-sls             | 3.x               | 3.x       | 3.10.0           |
| ibm-truststore-mgr  | 1.x               | 1.x       | 1.5.4            |


### IBM Cloud Pak Foundational Services
| Package                             | Default Channel   | Channel      | Latest Version   |
|-------------------------------------|-------------------|--------------|------------------|
| cloud-native-postgresql             | stable-v1.18      | fast         | 1.18.3           |
|                                     |                   | stable       | 1.18.7           |
|                                     |                   | stable-v1.15 | 1.15.5           |
|                                     |                   | stable-v1.17 | 1.17.3           |
|                                     |                   | stable-v1.18 | 1.18.7           |
| ibm-cert-manager-operator           | v3.23             | beta         | 3.9.0            |
|                                     |                   | v3           | 3.25.13          |
|                                     |                   | v3.20        | 3.22.0           |
|                                     |                   | v3.21        | 3.23.0           |
|                                     |                   | v3.22        | 3.24.0           |
|                                     |                   | v3.23        | 3.25.13          |
|                                     |                   | v4.0         | 4.0.0            |
|                                     |                   | v4.1         | 4.1.0            |
|                                     |                   | v4.2         | 4.2.7            |
| ibm-common-service-operator         | v3.23             | beta         | 103.103.103      |
|                                     |                   | v3           | 3.19.22          |
|                                     |                   | v3.20        | 3.20.1           |
|                                     |                   | v3.21        | 3.21.0           |
|                                     |                   | v3.22        | 3.22.0           |
|                                     |                   | v3.23        | 3.23.14          |
|                                     |                   | v4.0         | 4.0.1            |
|                                     |                   | v4.1         | 4.1.0            |
|                                     |                   | v4.2         | 4.2.0            |
|                                     |                   | v4.3         | 4.3.1            |
|                                     |                   | v4.4         | 4.4.0            |
|                                     |                   | v4.5         | 4.5.0            |
|                                     |                   | v4.6         | 4.6.5            |
|                                     |                   | v4.7         | 4.7.0            |
|                                     |                   | v4.8         | 4.8.0            |
| ibm-commonui-operator-app           | v3.23             | beta         | 1.5.1            |
|                                     |                   | v3           | 1.21.14          |
|                                     |                   | v3.20        | 1.18.1           |
|                                     |                   | v3.21        | 1.19.0           |
|                                     |                   | v3.22        | 1.20.0           |
|                                     |                   | v3.23        | 1.21.14          |
|                                     |                   | v4.0         | 4.0.0            |
|                                     |                   | v4.1         | 4.1.0            |
|                                     |                   | v4.2         | 4.2.0            |
|                                     |                   | v4.3         | 4.3.1            |
|                                     |                   | v4.4         | 4.4.4            |
|                                     |                   | v4.5         | 4.5.1            |
| ibm-events-operator                 | v3                | beta         | 3.7.1            |
|                                     |                   | v3           | 5.0.1            |
| ibm-ingress-nginx-operator-app      | v3.23             | beta         | 1.5.0            |
|                                     |                   | v3           | 1.20.13          |
|                                     |                   | v3.20        | 1.17.1           |
|                                     |                   | v3.21        | 1.18.0           |
|                                     |                   | v3.22        | 1.19.0           |
|                                     |                   | v3.23        | 1.20.13          |
| ibm-licensing-operator-app          | v3.23             | beta         | 1.4.1            |
|                                     |                   | v3           | 1.20.13          |
|                                     |                   | v3.20        | 1.17.0           |
|                                     |                   | v3.21        | 1.18.0           |
|                                     |                   | v3.22        | 1.19.0           |
|                                     |                   | v3.23        | 1.20.13          |
|                                     |                   | v4.0         | 4.0.0            |
|                                     |                   | v4.1         | 4.1.0            |
|                                     |                   | v4.2         | 4.2.7            |
| ibm-management-ingress-operator-app | v3.23             | beta         | 1.5.1            |
|                                     |                   | v3           | 1.20.13          |
|                                     |                   | v3.20        | 1.17.0           |
|                                     |                   | v3.21        | 1.18.0           |
|                                     |                   | v3.22        | 1.19.0           |
|                                     |                   | v3.23        | 1.20.13          |
| ibm-mongodb-operator-app            | v3.23             | beta         | 1.3.1            |
|                                     |                   | v3           | 1.18.13          |
|                                     |                   | v3.20        | 1.15.0           |
|                                     |                   | v3.21        | 1.16.0           |
|                                     |                   | v3.22        | 1.17.0           |
|                                     |                   | v3.23        | 1.18.13          |
|                                     |                   | v4.0         | 4.0.0            |
|                                     |                   | v4.1         | 4.1.0            |
|                                     |                   | v4.2         | 4.2.2            |
| ibm-namespace-scope-operator        | v3.23             | beta         | 1.1.1            |
|                                     |                   | v3           | 1.17.13          |
|                                     |                   | v3.20        | 1.14.0           |
|                                     |                   | v3.21        | 1.15.0           |
|                                     |                   | v3.22        | 1.16.0           |
|                                     |                   | v3.23        | 1.17.13          |
|                                     |                   | v4.0         | 4.0.0            |
|                                     |                   | v4.1         | 4.1.0            |
|                                     |                   | v4.2         | 4.2.7            |
| ibm-odlm                            | v3.23             | beta         | 1.5.0            |
|                                     |                   | v3           | 1.21.13          |
|                                     |                   | v3.20        | 1.18.0           |
|                                     |                   | v3.21        | 1.19.0           |
|                                     |                   | v3.22        | 1.20.0           |
|                                     |                   | v3.23        | 1.21.13          |
|                                     |                   | v4.0         | 4.0.0            |
|                                     |                   | v4.1         | 4.1.0            |
|                                     |                   | v4.2         | 4.2.3            |
|                                     |                   | v4.3         | 4.3.4            |
| ibm-platform-api-operator-app       | v3.23             | beta         | 3.9.1            |
|                                     |                   | v3           | 3.25.13          |
|                                     |                   | v3.20        | 3.22.0           |
|                                     |                   | v3.21        | 3.23.0           |
|                                     |                   | v3.22        | 3.24.0           |
|                                     |                   | v3.23        | 3.25.13          |
| ibm-user-data-services-operator     | alpha             | alpha        | 2.0.12           |
| ibm-zen-operator                    | v3.23             | beta         | 1.0.1            |
|                                     |                   | v3           | 1.8.13           |
|                                     |                   | v3.20        | 1.7.1            |
|                                     |                   | v3.21        | 1.7.2            |
|                                     |                   | v3.22        | 1.8.0            |
|                                     |                   | v3.23        | 1.8.13           |
|                                     |                   | v4.0         | 5.0.0            |
|                                     |                   | v4.1         | 5.0.1            |
|                                     |                   | v4.2         | 5.0.2            |
|                                     |                   | v4.3         | 5.1.1            |
|                                     |                   | v4.4         | 5.1.7            |
|                                     |                   | v6.0         | 6.0.2            |
| isf-operator                        | v2.0              | v2.0         | 2.8.1            |


### IBM Cloud Pak for Data
| Package                       | Default Channel   | Channel   | Latest Version   |
|-------------------------------|-------------------|-----------|------------------|
| analyticsengine-operator      | v5.4              | beta      | 1.0.1            |
|                               |                   | stable-v1 | 1.0.9            |
|                               |                   | v2.0      | 2.0.0            |
|                               |                   | v2.1      | 2.1.0            |
|                               |                   | v2.2      | 2.2.0            |
|                               |                   | v2.3      | 2.3.0            |
|                               |                   | v3.0      | 3.0.0            |
|                               |                   | v3.1      | 3.1.0            |
|                               |                   | v3.3      | 3.3.0            |
|                               |                   | v3.4      | 3.4.0            |
|                               |                   | v3.5      | 3.5.0            |
|                               |                   | v4.0      | 4.0.0            |
|                               |                   | v4.1      | 4.1.0            |
|                               |                   | v4.2      | 4.2.0            |
|                               |                   | v4.3      | 4.3.0            |
|                               |                   | v5.0      | 5.0.0            |
|                               |                   | v5.1      | 5.1.0            |
|                               |                   | v5.3      | 5.3.0            |
|                               |                   | v5.4      | 5.4.0            |
|                               |                   | v6.0      | 6.0.0            |
| cpd-platform-operator         | v6.0              | beta      | 2.0.0            |
|                               |                   | stable-v1 | 2.0.0            |
|                               |                   | v2.0      | 2.0.8            |
|                               |                   | v3.0      | 3.0.0            |
|                               |                   | v3.1      | 3.1.0            |
|                               |                   | v3.2      | 3.2.0            |
|                               |                   | v3.3      | 3.3.0            |
|                               |                   | v3.4      | 3.4.0            |
|                               |                   | v3.5      | 3.5.0            |
|                               |                   | v3.6      | 3.6.0            |
|                               |                   | v3.7      | 3.7.0            |
|                               |                   | v3.8      | 3.8.0            |
|                               |                   | v4.0      | 4.0.0            |
|                               |                   | v4.1      | 4.1.0            |
|                               |                   | v4.2      | 4.2.0            |
|                               |                   | v4.3      | 4.3.0            |
|                               |                   | v4.4      | 4.4.0            |
|                               |                   | v5.0      | 5.0.0            |
|                               |                   | v5.1      | 5.1.0            |
|                               |                   | v5.2      | 5.2.0            |
|                               |                   | v5.3      | 5.3.0            |
|                               |                   | v5.4      | 5.4.0            |
|                               |                   | v5.5      | 5.5.0            |
|                               |                   | v5.6      | 5.6.0            |
|                               |                   | v6.0      | 6.0.2            |
| ibm-ca-operator               | v26.2             | v22.0     | 22.0.0           |
|                               |                   | v22.1     | 22.1.0           |
|                               |                   | v22.2     | 22.2.0           |
|                               |                   | v22.3     | 22.3.0           |
|                               |                   | v23.0     | 23.0.0           |
|                               |                   | v23.1     | 23.1.0           |
|                               |                   | v23.3     | 23.3.0           |
|                               |                   | v23.4     | 23.4.0           |
|                               |                   | v23.5     | 23.5.0           |
|                               |                   | v24.0     | 24.0.0           |
|                               |                   | v24.3     | 24.3.0           |
|                               |                   | v25.0     | 25.0.0           |
|                               |                   | v25.2     | 25.2.0           |
|                               |                   | v25.3     | 25.3.0           |
|                               |                   | v25.4     | 25.4.0           |
|                               |                   | v26.0     | 26.0.0           |
|                               |                   | v26.1     | 26.1.0           |
|                               |                   | v26.2     | 26.2.0           |
|                               |                   | v4.0      | 4.0.8            |
| ibm-cpd-canvasbase            | v8.5              | v8.0      | 8.0.0            |
|                               |                   | v8.1      | 8.1.0            |
|                               |                   | v8.3      | 8.3.0            |
|                               |                   | v8.4      | 8.4.0            |
|                               |                   | v8.5      | 8.5.0            |
|                               |                   | v9.0      | 9.0.0            |
| ibm-cpd-ccs                   | v9.2              | v1.0      | 1.0.9            |
|                               |                   | v2.0      | 2.0.0            |
|                               |                   | v2.1      | 2.1.0            |
|                               |                   | v2.2      | 2.2.0            |
|                               |                   | v2.3      | 2.3.0            |
|                               |                   | v6.0      | 6.0.0            |
|                               |                   | v6.1      | 6.1.0            |
|                               |                   | v6.3      | 6.3.0            |
|                               |                   | v6.4      | 6.4.0            |
|                               |                   | v6.5      | 6.5.0            |
|                               |                   | v7.0      | 7.0.0            |
|                               |                   | v7.1      | 7.1.0            |
|                               |                   | v7.2      | 7.2.0            |
|                               |                   | v7.3      | 7.3.0            |
|                               |                   | v8.0      | 8.0.0            |
|                               |                   | v8.1      | 8.1.0            |
|                               |                   | v8.2      | 8.2.0            |
|                               |                   | v8.3      | 8.3.0            |
|                               |                   | v8.4      | 8.4.0            |
|                               |                   | v8.5      | 8.5.0            |
|                               |                   | v8.6      | 8.6.0            |
|                               |                   | v9.0      | 9.0.0            |
|                               |                   | v9.1      | 9.1.0            |
|                               |                   | v9.2      | 9.2.0            |
| ibm-cpd-datarefinery          | v9.1              | v1.0      | 1.0.10           |
|                               |                   | v2.0      | 2.0.0            |
|                               |                   | v2.1      | 2.1.0            |
|                               |                   | v2.2      | 2.2.0            |
|                               |                   | v2.3      | 2.3.0            |
|                               |                   | v6.0      | 6.0.0            |
|                               |                   | v6.1      | 6.1.0            |
|                               |                   | v6.3      | 6.3.0            |
|                               |                   | v6.4      | 6.4.0            |
|                               |                   | v6.5      | 6.5.0            |
|                               |                   | v7.0      | 7.0.0            |
|                               |                   | v8.0      | 8.0.0            |
|                               |                   | v8.1      | 8.1.0            |
|                               |                   | v8.3      | 8.3.0            |
|                               |                   | v8.4      | 8.4.0            |
|                               |                   | v8.5      | 8.5.0            |
|                               |                   | v8.6      | 8.6.0            |
|                               |                   | v9.0      | 9.0.0            |
|                               |                   | v9.1      | 9.1.0            |
| ibm-cpd-spss                  | v8.5              | v1.0      | 1.0.9            |
|                               |                   | v2.0      | 2.0.0            |
|                               |                   | v2.1      | 2.1.0            |
|                               |                   | v2.2      | 2.2.0            |
|                               |                   | v2.3      | 2.3.0            |
|                               |                   | v6.0      | 6.0.0            |
|                               |                   | v6.1      | 6.1.0            |
|                               |                   | v6.3      | 6.3.0            |
|                               |                   | v6.4      | 6.4.0            |
|                               |                   | v6.5      | 6.5.0            |
|                               |                   | v7.0      | 7.0.0            |
|                               |                   | v8.0      | 8.0.0            |
|                               |                   | v8.1      | 8.1.0            |
|                               |                   | v8.3      | 8.3.0            |
|                               |                   | v8.4      | 8.4.0            |
|                               |                   | v8.5      | 8.5.0            |
|                               |                   | v9.0      | 9.0.0            |
| ibm-cpd-wml-operator          | v6.1              | alpha     | 1.1.0            |
|                               |                   | beta      | 1.0.1486         |
|                               |                   | v1.1      | 1.1.8            |
|                               |                   | v2.0      | 2.0.0            |
|                               |                   | v2.1      | 2.1.0            |
|                               |                   | v2.2      | 2.2.0            |
|                               |                   | v2.3      | 2.3.0            |
|                               |                   | v3.0      | 3.0.0            |
|                               |                   | v3.1      | 3.1.0            |
|                               |                   | v3.3      | 3.3.0            |
|                               |                   | v3.4      | 3.4.0            |
|                               |                   | v3.5      | 3.5.0            |
|                               |                   | v4.0      | 4.0.0            |
|                               |                   | v5.0      | 5.0.0            |
|                               |                   | v5.1      | 5.1.0            |
|                               |                   | v5.3      | 5.3.0            |
|                               |                   | v5.4      | 5.4.0            |
|                               |                   | v5.5      | 5.5.0            |
|                               |                   | v5.6      | 5.6.0            |
|                               |                   | v6.0      | 6.0.0            |
|                               |                   | v6.1      | 6.1.0            |
| ibm-cpd-wos                   | v6.1              | alpha     | 1.2.0            |
|                               |                   | v1        | 1.5.0            |
|                               |                   | v1.5      | 1.5.4            |
|                               |                   | v2.0      | 2.0.0            |
|                               |                   | v2.1      | 2.1.0            |
|                               |                   | v2.2      | 2.2.0            |
|                               |                   | v2.3      | 2.3.0            |
|                               |                   | v3.0      | 3.0.0            |
|                               |                   | v3.1      | 3.1.0            |
|                               |                   | v3.3      | 3.3.0            |
|                               |                   | v3.4      | 3.4.0            |
|                               |                   | v3.5      | 3.5.0            |
|                               |                   | v4.0      | 4.0.0            |
|                               |                   | v4.2      | 4.2.0            |
|                               |                   | v5.0      | 5.0.0            |
|                               |                   | v5.3      | 5.3.0            |
|                               |                   | v5.4      | 5.4.0            |
|                               |                   | v5.5      | 5.5.0            |
|                               |                   | v5.6      | 5.6.0            |
|                               |                   | v6.0      | 6.0.0            |
|                               |                   | v6.1      | 6.1.0            |
| ibm-cpd-ws-runtimes           | v9.1              | v1.0      | 1.0.9            |
|                               |                   | v5.0      | 5.0.0            |
|                               |                   | v5.1      | 5.1.0            |
|                               |                   | v5.2      | 5.2.0            |
|                               |                   | v5.3      | 5.3.0            |
|                               |                   | v6.0      | 6.0.0            |
|                               |                   | v6.1      | 6.1.0            |
|                               |                   | v6.3      | 6.3.0            |
|                               |                   | v6.4      | 6.4.0            |
|                               |                   | v6.5      | 6.5.0            |
|                               |                   | v7.0      | 7.0.0            |
|                               |                   | v8.0      | 8.0.0            |
|                               |                   | v8.1      | 8.1.0            |
|                               |                   | v8.3      | 8.3.0            |
|                               |                   | v8.4      | 8.4.0            |
|                               |                   | v8.5      | 8.5.0            |
|                               |                   | v8.6      | 8.6.0            |
|                               |                   | v9.0      | 9.0.0            |
|                               |                   | v9.1      | 9.1.0            |
| ibm-cpd-wsl                   | v9.1              | v2.0      | 2.0.9            |
|                               |                   | v3.0      | 3.0.0            |
|                               |                   | v3.1      | 3.1.0            |
|                               |                   | v3.2      | 3.2.0            |
|                               |                   | v3.3      | 3.3.0            |
|                               |                   | v6.0      | 6.0.0            |
|                               |                   | v6.1      | 6.1.0            |
|                               |                   | v6.3      | 6.3.0            |
|                               |                   | v6.4      | 6.4.0            |
|                               |                   | v6.5      | 6.5.0            |
|                               |                   | v7.0      | 7.0.0            |
|                               |                   | v8.0      | 8.0.0            |
|                               |                   | v8.1      | 8.1.0            |
|                               |                   | v8.3      | 8.3.0            |
|                               |                   | v8.4      | 8.4.0            |
|                               |                   | v8.5      | 8.5.0            |
|                               |                   | v8.6      | 8.6.0            |
|                               |                   | v9.0      | 9.0.0            |
|                               |                   | v9.1      | 9.1.0            |
| ibm-elasticsearch-operator    | v1.1              | v1.1      | 1.1.2238         |
| ibm-etcd-operator             | v1.0              | v1.0      | 1.0.30           |
| ibm-iam-operator              | v3.23             | beta      | 3.9.1            |
|                               |                   | v3        | 3.23.14          |
|                               |                   | v3.20     | 3.20.1           |
|                               |                   | v3.21     | 3.21.0           |
|                               |                   | v3.22     | 3.22.0           |
|                               |                   | v3.23     | 3.23.14          |
|                               |                   | v4.0      | 4.0.1            |
|                               |                   | v4.1      | 4.1.0            |
|                               |                   | v4.2      | 4.2.0            |
|                               |                   | v4.3      | 4.3.1            |
|                               |                   | v4.4      | 4.4.0            |
|                               |                   | v4.5      | 4.5.4            |
|                               |                   | v4.6      | 4.6.0            |
|                               |                   | v4.7      | 4.7.0            |
| ibm-minio-operator            | v1.0              | v1.0      | 1.0.18           |
| ibm-model-train-operator      | v2.0              | v1.1      | 1.1.15           |
|                               |                   | v2.0      | 2.0.0            |
| ibm-rabbitmq-operator         | v1.0              | v1.0      | 1.0.29           |
| ibm-watson-discovery-operator | v8.1              | v4.0      | 4.0.9            |
|                               |                   | v4.5      | 4.5.0            |
|                               |                   | v4.6      | 4.6.0            |
|                               |                   | v4.7      | 4.7.0            |
|                               |                   | v5.0      | 5.0.0            |
|                               |                   | v5.2      | 5.2.0            |
|                               |                   | v5.3      | 5.3.0            |
|                               |                   | v5.5      | 5.5.0            |
|                               |                   | v6.0      | 6.0.0            |
|                               |                   | v6.1      | 6.1.0            |
|                               |                   | v6.3      | 6.3.0            |
|                               |                   | v7.0      | 7.0.0            |
|                               |                   | v7.2      | 7.2.0            |
|                               |                   | v7.3      | 7.3.0            |
|                               |                   | v7.4      | 7.4.0            |
|                               |                   | v7.5      | 7.5.0            |
|                               |                   | v7.6      | 7.6.0            |
|                               |                   | v8.0      | 8.0.0            |
|                               |                   | v8.1      | 8.1.0            |
| ibm-watson-gateway-operator   | v1.0              | v1.0      | 1.0.23           |


### IBM Db2 Universal Operator
| Package       | Default Channel   | Channel   | Latest Version   |
|---------------|-------------------|-----------|------------------|
| db2u-operator | v110509.0         | v1.0      | 1.0.11           |
|               |                   | v1.1      | 1.1.13           |
|               |                   | v110508.0 | 110508.0.3       |
|               |                   | v110509.0 | 110509.0.2       |
|               |                   | v2.0      | 2.0.0            |
|               |                   | v2.1      | 2.1.0            |
|               |                   | v2.2      | 2.2.0            |
|               |                   | v3.0      | 3.0.0            |
|               |                   | v3.1      | 3.1.0            |
|               |                   | v3.2      | 3.2.0            |
|               |                   | v4.0      | 4.0.0            |
|               |                   | v4.1      | 4.1.0            |
|               |                   | v4.2      | 4.2.0            |
|               |                   | v5.0      | 5.0.0            |
|               |                   | v5.1      | 5.1.0            |
|               |                   | v5.2      | 5.2.0            |
|               |                   | v5.3      | 5.3.0            |
|               |                   | v6.0      | 6.0.0            |


### IBM AppConnect
| Package          | Default Channel   | Channel   | Latest Version   |
|------------------|-------------------|-----------|------------------|
| couchdb-operator | v2.2              | beta      | 1.4.2            |
|                  |                   | stable    | 2.2.1            |
|                  |                   | v1.0      | 1.0.14           |
|                  |                   | v1.1      | 1.1.0            |
|                  |                   | v1.2      | 1.2.1            |
|                  |                   | v1.3      | 1.3.1            |
|                  |                   | v1.4      | 1.4.4            |
|                  |                   | v2.0      | 2.0.0            |
|                  |                   | v2.1      | 2.0.1            |
|                  |                   | v2.2      | 2.2.1            |
| ibm-appconnect   | v12.3             | cd        | 5.2.0            |
|                  |                   | v1.0      | 1.0.5            |
|                  |                   | v1.1-eus  | 1.1.10           |
|                  |                   | v1.2      | 1.2.0            |
|                  |                   | v1.3      | 1.3.2            |
|                  |                   | v1.4      | 1.4.0            |
|                  |                   | v1.5      | 1.5.2            |
|                  |                   | v10.0     | 10.0.1           |
|                  |                   | v10.1     | 10.1.1           |
|                  |                   | v11.0     | 11.0.1           |
|                  |                   | v11.1     | 11.1.0           |
|                  |                   | v11.2     | 11.2.1           |
|                  |                   | v11.3     | 11.3.0           |
|                  |                   | v11.4     | 11.4.0           |
|                  |                   | v11.5     | 11.5.1           |
|                  |                   | v11.6     | 11.6.0           |
|                  |                   | v12.0-sc2 | 12.0.3           |
|                  |                   | v12.1     | 12.1.2           |
|                  |                   | v12.2     | 12.2.1           |
|                  |                   | v12.3     | 12.3.0           |
|                  |                   | v2.0      | 2.0.0            |
|                  |                   | v2.1      | 2.1.0            |
|                  |                   | v3.0      | 3.0.0            |
|                  |                   | v3.1      | 3.1.0            |
|                  |                   | v4.0      | 4.0.0            |
|                  |                   | v4.1      | 4.1.0            |
|                  |                   | v4.2      | 4.2.0            |
|                  |                   | v5.0-lts  | 5.0.20           |
|                  |                   | v5.1      | 5.1.0            |
|                  |                   | v5.2      | 5.2.0            |
|                  |                   | v6.0      | 6.0.0            |
|                  |                   | v6.1      | 6.1.1            |
|                  |                   | v6.2      | 6.2.0            |
|                  |                   | v7.0      | 7.0.0            |
|                  |                   | v7.1      | 7.1.0            |
|                  |                   | v7.2      | 7.2.0            |
|                  |                   | v8.0      | 8.0.0            |
|                  |                   | v8.1      | 8.1.0            |
|                  |                   | v8.2      | 8.2.1            |
|                  |                   | v9.0      | 9.0.0            |
|                  |                   | v9.1      | 9.1.0            |
|                  |                   | v9.2      | 9.2.1            |


### Eclipse Amlen
| Package                | Default Channel   | Channel   | Latest Version   |
|------------------------|-------------------|-----------|------------------|
| eclipse-amlen-operator | 1.x               | 1.x       | 1.1.1            |