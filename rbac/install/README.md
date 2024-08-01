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

oc new-project eck
oc new-project grafana5
oc new-project ibm-common-services
oc new-project redhat-marketplace

oc apply -f pipeline/serviceaccount.yaml -n mas-${MAS_INSTANCE_ID}-pipelines

oc apply -f pipeline/cluster.yaml

oc apply -f pipeline/eck.yaml
oc apply -f pipeline/grafana5.yaml
oc apply -f pipeline/ibm-common-services.yaml
oc apply -f pipeline/openshift-config.yaml
oc apply -f pipeline/openshift-ingress-operator.yaml
oc apply -f pipeline/openshift-ingress.yaml
oc apply -f pipeline/openshift-marketplace.yaml
oc apply -f pipeline/openshift-monitoring.yaml
oc apply -f pipeline/openshift-operators.yaml
oc apply -f pipeline/openshift-user-workload-monitoring.yaml
oc apply -f pipeline/redhat-marketplace.yaml
```

Note that to use these you will need to modify `subjects[0].namespace` in each of the bindings.


## Useful Commands
To get the service account token
```bash
oc -n kube-system describe secret $(oc -n kube-system get secret | grep masinstall-sa | awk '{print $1}')
```