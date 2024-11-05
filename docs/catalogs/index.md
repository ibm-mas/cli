IBM Maximo Operator Catalog
-------------------------------------------------------------------------------
This catalog is a **curated** catalog, the Maximo Application Suite team take a snapshot of the online IBM Operator Catalog and test compatibility of all dependent IBM operators with supported releases of Maximo Application Suite; this allows the team to intercept any breaking changes that may have evaded other teams' testing before they reach your cluster.

### Availability
All versions of the catalog are available **indefinitely**, but they have a useful lifespan limited by the support statements of the packages available in the catalog and the OCP release the catalog is certified on.  We **never** remove catalog images from the IBM Container Registry (ICR); even the [first](v8-220717-amd64.md) Maximo Operator Catalog ever published is still available today, however it's usefulness is questionable due to the end of life of all compatible OCP releases.

### CLI Support
The MAS CLI maintains a rolling window of approximately four months worth of supported catalogs for the install, mirror-images, and update functions.  When using an older catalog it is recommended to use a version of the CLI that was released around the same time as the catalog, refer to the table below for the recommended version of the CLI to use with older versions of the operator catalog.

### Known Issues
- **October 2024** IBM Cloud Pak for Data 4.8, used in catalogs released between June and October 2024 uses a Postgres license key that expired on October 1, 2024.  A fix is available from CLI version 11.2.1 onwards; if you are installing CP4D as a MAS dependency you must use at least version 11.2.1 of the CLI.  If you need to install MAS with CP4D using an older catalog than supported by this version of the CLI please contact IBM support for assistance.

### Architecture
- amd64
- s390x

### Catalog Directory

<cds-tabs trigger-content="Select an item" value="2024">
  <cds-tab id="tab-2024" target="panel-2024" value="2024">2024 Catalogs</cds-tab>
  <cds-tab id="tab-2023" target="panel-2023" value="2023">2023 Catalogs</cds-tab>
  <cds-tab id="tab-2022" target="panel-2022" value="2022">2022 Catalogs</cds-tab>
</cds-tabs>

<div class="tab-panel">
  <div id="panel-2024" role="tabpanel" aria-labelledby="tab-2024" hidden>
    <table>
    <thead>
    <tr>
    <th>Catalog</th>
    <th>OCP Support</th>
    <th>Recommended CLI</th>
    <th>Support Notes</th>
    </tr>
    </thead>
    <tbody>
    <tr>
    <td><a href="v9-241003-amd64/">v9-241003-amd64</a></td>
    <td>4.12 - 4.15</td>
    <td>latest</td>
    <td>OCP 4.14 EOS October 31, 2025</td>
    </tr>
    <tr>
    <td><a href="v9-240827-amd64/">v9-240827-amd64</a></td>
    <td>4.12 - 4.15</td>
    <td>latest</td>
    <td>OCP 4.14 EOS October 31, 2025</td>
    </tr>
    <tr>
    <td><a href="v9-240730-amd64/">v9-240730-amd64</a></td>
    <td>4.12 - 4.15</td>
    <td>latest</td>
    <td>OCP 4.14 EOS October 31, 2025</td>
    </tr>
    <tr>
    <td><a href="v9-240625-amd64/">v9-240625-amd64</a></td>
    <td>4.12 - 4.14</td>
    <td>latest</td>
    <td>OCP 4.14 EOS October 31, 2025</td>
    </tr>
    <tr>
    <td><a href="v8-240528-amd64/">v8-240528-amd64</a></td>
    <td>4.12 - 4.14</td>
    <td>10.8.1</td>
    <td>OCP 4.14 EOS October 31, 2025</td>
    </tr>
    <tr>
    <td><a href="v8-240430-amd64/">v8-240430-amd64</a></td>
    <td>4.12 - 4.14</td>
    <td>9.4.0</td>
    <td>OCP 4.14 EOS October 31, 2025</td>
    </tr>
    <tr>
    <td><a href="v8-240405-amd64/">v8-240405-amd64</a></td>
    <td>4.12 - 4.14</td>
    <td>9.4.0</td>
    <td>OCP 4.14 EOS October 31, 2025</td>
    </tr>
    <tr>
    <td><a href="v8-240326-amd64/">v8-240326-amd64</a></td>
    <td>4.12 - 4.14</td>
    <td>9.4.0</td>
    <td>OCP 4.14 EOS October 31, 2025</td>
    </tr>
    <tr>
    <td><a href="v8-240227-amd64/">v8-240227-amd64</a></td>
    <td>4.12</td>
    <td>8.2.2</td>
    <td>OCP 4.12 EOS January 17, 2025</td>
    </tr>
    <tr>
    <td><a href="v8-240130-amd64/">v8-240130-amd64</a></td>
    <td>4.12</td>
    <td>8.2.2</td>
    <td>OCP 4.12 EOS January 17, 2025</td>
    </tr>
    </tbody>
    </table>
  </div>
  <div id="panel-2023" role="tabpanel" aria-labelledby="tab-2023" hidden>
    <table>
    <thead>
    <tr>
    <th>Catalog</th>
    <th>OCP Support</th>
    <th>Recommended CLI</th>
    <th>Support Notes</th>
    </tr>
    </thead>
    <tbody>
    <tr>
    <td><a href="v8-231228-amd64/">v8-231228-amd64</a></td>
    <td>4.11 - 4.12</td>
    <td>8.2.2</td>
    <td>OCP 4.12 EOS January 17, 2025</td>
    </tr>
    <tr>
    <td><a href="v8-231128-amd64/">v8-231128-amd64</a></td>
    <td>4.11 - 4.12</td>
    <td>8.2.2</td>
    <td>OCP 4.12 EOS January 17, 2025</td>
    </tr>
    <tr>
    <td><a href="v8-231031-amd64/">v8-231031-amd64</a></td>
    <td>4.11 - 4.12</td>
    <td>7.12.1</td>
    <td>OCP 4.12 EOS January 17, 2025</td>
    </tr>
    <tr>
    <td><a href="v8-231004-amd64/">v8-231004-amd64</a></td>
    <td>4.11 - 4.12</td>
    <td>7.12.1</td>
    <td>OCP 4.12 EOS January 17, 2025</td>
    </tr>
    <tr>
    <td><a href="v8-230926-amd64/">v8-230926-amd64</a></td>
    <td>4.11 - 4.12</td>
    <td>7.12.1</td>
    <td>OCP 4.12 EOS January 17, 2025</td>
    </tr>
    <tr>
    <td><a href="v8-230829-amd64/">v8-230829-amd64</a></td>
    <td>4.10 - 4.12</td>
    <td>7.12.1</td>
    <td>OCP 4.12 EOS January 17, 2025</td>
    </tr>
    <tr>
    <td><a href="v8-230725-amd64/">v8-230725-amd64</a></td>
    <td>4.10 - 4.12</td>
    <td>7.12.1</td>
    <td>OCP 4.12 EOS January 17, 2025</td>
    </tr>
    <tr>
    <td><a href="v8-230721-amd64/">v8-230721-amd64</a></td>
    <td>4.10 - 4.12</td>
    <td>7.12.1</td>
    <td>OCP 4.12 EOS January 17, 2025</td>
    </tr>
    <tr>
    <td><a href="v8-230627-amd64/">v8-230627-amd64</a></td>
    <td>4.10 - 4.12</td>
    <td>5.5.0</td>
    <td>OCP 4.12 EOS January 17, 2025</td>
    </tr>
    <tr>
    <td><a href="v8-230616-amd64/">v8-230616-amd64</a></td>
    <td>4.10 - 4.12</td>
    <td>5.5.0</td>
    <td>OCP 4.12 EOS January 17, 2025</td>
    </tr>
    <tr>
    <td><a href="v8-230526-amd64/">v8-230526-amd64</a></td>
    <td>4.10</td>
    <td>5.5.0</td>
    <td>OCP 4.10 EOS September 10, 2023</td>
    </tr>
    <tr>
    <td><a href="v8-230518-amd64/">v8-230518-amd64</a></td>
    <td>4.10</td>
    <td>5.5.0</td>
    <td>OCP 4.10 EOS September 10, 2023</td>
    </tr>
    <tr>
    <td><a href="v8-230414-amd64/">v8-230414-amd64</a></td>
    <td>4.8 - 4.10</td>
    <td>5.5.0</td>
    <td>OCP 4.10 EOS September 10, 2023</td>
    </tr>
    <tr>
    <td><a href="v8-230314-amd64/">v8-230314-amd64</a></td>
    <td>4.8 - 4.10</td>
    <td>4.3.1</td>
    <td>OCP 4.10 EOS September 10, 2023</td>
    </tr>
    <tr>
    <td><a href="v8-230217-amd64/">v8-230217-amd64</a></td>
    <td>4.8 - 4.10</td>
    <td>4.3.1</td>
    <td>OCP 4.10 EOS September 10, 2023</td>
    </tr>
    <tr>
    <td><a href="v8-230111-amd64/">v8-230111-amd64</a></td>
    <td>4.8 - 4.10</td>
    <td>4.3.1</td>
    <td>OCP 4.10 EOS September 10, 2023</td>
    </tr>
    </tbody>
    </table>
  </div>
  <div id="panel-2022" role="tabpanel" aria-labelledby="tab-2022" hidden>
    <table>
    <thead>
    <tr>
    <th>Catalog</th>
    <th>OCP Support</th>
    <th>Recommended CLI</th>
    <th>Support Notes</th>
    </tr>
    </thead>
    <tbody>
    <tr>
    <td><a href="v8-221228-amd64/">v8-221228-amd64</a></td>
    <td>4.6 - 4.10</td>
    <td>3.9.0</td>
    <td>OCP 4.10 EOS September 10, 2023</td>
    </tr>
    <tr>
    <td><a href="v8-221129-amd64/">v8-221129-amd64</a></td>
    <td>4.6 - 4.10</td>
    <td>3.9.0</td>
    <td>OCP 4.10 EOS September 10, 2023</td>
    </tr>
    <tr>
    <td><a href="v8-221025-amd64/">v8-221025-amd64</a></td>
    <td>4.6 - 4.10</td>
    <td>3.9.0</td>
    <td>OCP 4.10 EOS September 10, 2023</td>
    </tr>
    <tr>
    <td><a href="v8-220927-amd64/">v8-220927-amd64</a></td>
    <td>4.6 - 4.10</td>
    <td>3.5.0</td>
    <td>OCP 4.10 EOS September 10, 2023</td>
    </tr>
    <tr>
    <td><a href="v8-220805-amd64/">v8-220805-amd64</a></td>
    <td>4.6 - 4.10</td>
    <td>3.5.0</td>
    <td>OCP 4.10 EOS September 10, 2023</td>
    </tr>
    <tr>
    <td><a href="v8-220717-amd64/">v8-220717-amd64</a></td>
    <td>4.6 - 4.10</td>
    <td>3.5.0</td>
    <td>OCP 4.10 EOS September 10, 2023</td>
    </tr>
    </tbody>
    </table>
  </div>
</div>

### FAQ
#### User-Controlled Updates
> I want to control when updates are introduced into my cluster

The packages available in the Maximo Operator Catalog are fixed. Multiple installations at different times will always result in exactly the same version of all IBM-provided operators being installed.  To receive security updates and bug fixes you must periodically update the version of the static catalog that you have installed in the cluster.  Once you do this all operators that you have installed from the catalog will automatically update to the newer version.  We aim to release a catalog update monthly.  When you are ready to apply updates you simply modify the CatalogSource installed in your cluster, changing it from e.g. `@@MAS_PREVIOUS_CATALOG@@` to `@@MAS_LATEST_CATALOG@@`.

We **strongly discourage the use of manual update approval strategy for operator subscriptions** and all IBM-provided automation is designed to work with the automatic update approval strategy only.  In our experience the use of manual subscription approvals leads to overly complicated updates requiring significant administrative effort when taking into account the range of operators running in a cluster across numerous namespaces. We promote a model of **controling when updates are introduced to a cluster at the catalog level**.

Updating the operators is only one aspect of keeping a system up to date, when using the MAS CLI [update](../commands/update.md) function many other additional actions will be performed autoamtically, if you are not using the MAS CLI to drive updates then you should implement your own processes for the non-operator update actions that are part of the MAS update pipeline.

#### Repeatable Install
> I want repeatable installs across multiple OpenShift clusters, for instance in a development, staging, production setup

The packages available in these catalogs are fixed. Multiple installations at different times will always result in exactly the same version of all operators being installed.  By choosing the same version of the catalog across multiple clusters the user is guaranteed that their installations are identical, right down to the patch level of the operators installed.  Updates can be rolled out in a controlled manner, and the upgrade path between two catalog versions will always be identical regardless of how much time passes between upgrades in different clusters.

#### Disconnected Install
> I want to run a disconnected environment using a private mirror registry

The MAS CLI [mirror-images](../commands/mirror-images.md) function is the easiest way to mirror the content from a specific version of the Maximo Operator Catalog.  Once the images are mirrored simply run the [configure-airgap](../commands/configure-airgap.md) function to add the IBM Maximo Application Suite **ImageContentSourcePolicy** to your cluster before starting the installation.


### Dynamic Catalog
The legacy dynamic operator catalog is only supported for Maximo Application Suite v8 releases, if you use the dynamic catalog you will always have access to the latest operator updates without updating the **CatalogSource** on your OpenShift cluster.

#### Manual Installation
`oc apply -f https://raw.githubusercontent.com/ibm-mas/cli/master/catalogs/v8-amd64.yaml`

#### Source
```yaml
apiVersion: operators.coreos.com/v1alpha1
kind: CatalogSource
metadata:
  name: ibm-operator-catalog
  namespace: openshift-marketplace
spec:
  displayName: IBM Maximo Operators (v8-amd64)
  publisher: IBM
  description: Dynamic Catalog Source for IBM Maximo Application Suite
  sourceType: grpc
  image: icr.io/cpopen/ibm-maximo-operator-catalog:v8-amd64
  priority: 90
```

