MAS Install Minimal RBAC
===============================================================================
**Work in Progress**

The minimal permissions required to run `mas install` are captured in these files:

```bash
export MAS_INSTANCE_ID=dev1

oc apply -f user/serviceaccount.yaml

oc apply -f user/cluster.yaml
oc apply -f user/mas-x-pipelines.yaml -n mas-${MAS_INSTANCE_ID}-pipelines
oc apply -f user/openshift-console.yaml
oc apply -f user/openshift-image-registry.yaml
oc apply -f user/openshift-marketplace.yaml
oc apply -f user/openshift-operators.yaml
```

If using these minimal permissions then the `pipelines` service account must have already been set up by someone with cluster-admin permissions, because the install pipeline will require access beyond that of the person who runs the install command, as below:

```bash
export MAS_INSTANCE_ID=dev1

oc apply -f pipeline/serviceaccount.yaml -n mas-${MAS_INSTANCE_ID}-pipelines

```
