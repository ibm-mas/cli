Catalog Options
-------------------------------------------------------------------------------
As the MAS CLI is updated we maintain a rolling window of approximately four months worth of catalogs in the interactive mode choices for install, mirror-images, and update functions; after this period the catalogs will be removed from the options, generally speaking customers are recommended to use the latest catalog with the latest CLI for new installs, even if installing an older release of MAS.

Older catalogs can still be used once they are not shown in the interactive prompt, but this is not recommended, refer to the table below for the recommended version of the CLI to use with each catalog update.

All catalogs are available **indefinitely**, but they have a useful lifespan limited by the support statements of the packages available in the catalog and the OCP release the catalog is certified on.  We **never** remove catalog images from the IBM Container Registry (ICR), even the first Maximo Operator Catalog ever published - [v8-220717-amd64](v8-220717-amd64.md) - is still available today, however it's usefulness is questionable due to the end of life of all compatible OCP releases.


!!! important
    Whether you are using dynamic or static catalogs we **strongly discourage the use of manual update approvals on subscriptions**, and when using the MAS CLI **use of manual update approvals is outright not supported**.  In our experience it leads to overly complicated updates requiring significant administrative effort when taking into account the range of operators running in a cluster across numerous namespaces.

    If you desire control over when updates are introduced to your cluster we highly recommend the use of static operator catalogs.

### Dynamic Catalog
The dynamic operator catalog is continuously updated, if you use the dynamic catalog you will always have access to the latest operator updates.

This catalog is a **curated** catalog, the Maximo Application Suite team take a snapshot of the online IBM Operator Catalog and test compatibility of all dependent IBM operators with supported releases of Maximo Application suite; this allows the team to intercept any breaking changes that may have evaded other teams' testing before they reach your cluster.

No updates are made to this catalog without extensive testing with all in-support version of Maximo Application Suite, so you can trust this dynamic catalog, even in a production environment.

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

### Static Catalogs
The static operator catalogs provide a fixed reference point, if you use a static catalog you can rely on the fact that it will never change which allows for 100% reproducible installations no matter how much time has passed between the install.

To receive security updates and bug fixes you must periodically update the version of the static catalog that you have installed in the cluster.  Once you do this all operators that you have installed from the catalog will automatically update to the newer version.  We aim to release a catalog update monthly.

#### 2024
| Catalog                               | OCP Support | Recommended CLI | End of Support                  |
| ------------------------------------- | ----------- | --------------- | ------------------------------- |
| [v8-240405-amd64](v8-240405-amd64.md) | 4.12 - 4.14 | latest          | OCP 4.12 EOS January 17, 2025   |
| [v8-240326-amd64](v8-240326-amd64.md) | 4.12 - 4.14 | latest          | OCP 4.12 EOS January 17, 2025   |
| [v8-240227-amd64](v8-240227-amd64.md) | 4.12        | latest          | OCP 4.12 EOS January 17, 2025   |
| [v8-240130-amd64](v8-240130-amd64.md) | 4.12        | latest          | OCP 4.12 EOS January 17, 2025   |

#### 2023
| Catalog                               | OCP Support | Recommended CLI | End of Support                  |
| ------------------------------------- | ----------- | --------------- | ------------------------------- |
| [v8-231228-amd64](v8-231228-amd64.md) | 4.11 - 4.12 | latest          | OCP 4.12 EOS January 17, 2025   |
| [v8-231128-amd64](v8-231128-amd64.md) | 4.11 - 4.12 | latest          | OCP 4.12 EOS January 17, 2025   |
| [v8-231031-amd64](v8-231031-amd64.md) | 4.11 - 4.12 | 7.12.1          | OCP 4.12 EOS January 17, 2025   |
| [v8-231004-amd64](v8-231004-amd64.md) | 4.11 - 4.12 | 7.12.1          | OCP 4.12 EOS January 17, 2025   |
| [v8-230926-amd64](v8-230926-amd64.md) | 4.11 - 4.12 | 7.12.1          | OCP 4.12 EOS January 17, 2025   |
| [v8-230829-amd64](v8-230829-amd64.md) | 4.10 - 4.12 | 7.12.1          | OCP 4.12 EOS January 17, 2025   |
| [v8-230725-amd64](v8-230725-amd64.md) | 4.10 - 4.12 | 7.12.1          | OCP 4.12 EOS January 17, 2025   |
| [v8-230721-amd64](v8-230721-amd64.md) | 4.10 - 4.12 | 7.12.1          | OCP 4.12 EOS January 17, 2025   |
| [v8-230627-amd64](v8-230627-amd64.md) | 4.10 - 4.12 | 5.5.0           | OCP 4.12 EOS January 17, 2025   |
| [v8-230616-amd64](v8-230616-amd64.md) | 4.10 - 4.12 | 5.5.0           | OCP 4.12 EOS January 17, 2025   |
| [v8-230526-amd64](v8-230526-amd64.md) | 4.10        | 5.5.0           | OCP 4.10 EOS September 10, 2023 |
| [v8-230518-amd64](v8-230518-amd64.md) | 4.10        | 5.5.0           | OCP 4.10 EOS September 10, 2023 |
| [v8-230414-amd64](v8-230414-amd64.md) | 4.8 - 4.10  | 5.5.0           | OCP 4.10 EOS September 10, 2023 |
| [v8-230314-amd64](v8-230314-amd64.md) | 4.8 - 4.10  | 4.3.1           | OCP 4.10 EOS September 10, 2023 |
| [v8-230217-amd64](v8-230217-amd64.md) | 4.8 - 4.10  | 4.3.1           | OCP 4.10 EOS September 10, 2023 |
| [v8-230111-amd64](v8-230111-amd64.md) | 4.8 - 4.10  | 4.3.1           | OCP 4.10 EOS September 10, 2023 |

#### 2022
| Catalog                               | OCP Support | Recommended CLI | End of Support                  |
| ------------------------------------- | ----------- | --------------- |------------------------------- |
| [v8-221228-amd64](v8-221228-amd64.md) | 4.6 - 4.10  | 3.9.0           | OCP 4.10 EOS September 10, 2023 |
| [v8-221129-amd64](v8-221129-amd64.md) | 4.6 - 4.10  | 3.9.0           | OCP 4.10 EOS September 10, 2023 |
| [v8-221025-amd64](v8-221025-amd64.md) | 4.6 - 4.10  | 3.9.0           | OCP 4.10 EOS September 10, 2023 |
| [v8-220927-amd64](v8-220927-amd64.md) | 4.6 - 4.10  | 3.5.0           | OCP 4.10 EOS September 10, 2023 |
| [v8-220805-amd64](v8-220805-amd64.md) | 4.6 - 4.10  | 3.5.0           | OCP 4.10 EOS September 10, 2023 |
