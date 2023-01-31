Catalog Options
-------------------------------------------------------------------------------

!!! important
    Whether you are using dynamic or static catalogs we **strongly discourage the use of manual update approvals on subscriptions**.  In our experience it leads to overly complicated updates requiring significant administrative effort when taking into account the range of operators running in a cluster across numerous namespaces.

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

- [v8-230111-amd64](v8-230111-amd64.md)
- [v8-221228-amd64](v8-221228-amd64.md)
- [v8-221129-amd64](v8-221129-amd64.md)
- [v8-221025-amd64](v8-221025-amd64.md)
- [v8-220927-amd64](v8-220927-amd64.md)
- [v8-220805-amd64](v8-220805-amd64.md)
- [v8-220717-amd64](v8-220717-amd64.md)
