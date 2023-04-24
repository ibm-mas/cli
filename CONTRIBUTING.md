# Contributing

## Building the tekton definitions
```bash
export VERSION=4.1.0-pre.mg
export DEV_MODE=true
bash build/bin/build-tekton.sh
```


## Building the container image locally
```bash
# Build & install ansible collections, save them to image/cli/, build the docker container, then run the container
make
docker run -ti --rm quay.io/ibmmas:local
```


## Using the docker image
This is a great way to test in a clean environment (e.g. to ensure the myriad of environment variables that you no doubt have set up are not impacting your test scenarios).  After you commit your changes to the repository a pre-release container image will be built, which contains your in-development version of the collection:

```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli:x.y.z-pre.mybranch
oc login --token=xxxx --server=https://myocpserver
export STUFF
ansible localhost -m include_role -a name=ibm.mas_devops.ocp_verify
ansible-playbook ibm.mas_devops.oneclick_core
mas install
```
