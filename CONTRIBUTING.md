# Contributing

## Useful commands
```bash
# Build & install ansible collections, save them to image/cli/bin and build the docker container, then run the container
make
make all

# Build ansible collections, save them to image/cli/bin
make ansible-build

# Install ansible collections (from image/cli/bin)
make ansible-install

# Build & install ansible collections, save them to image/cli/bin
make ansible-all

# Build the docker container
make docker-build

# Run the docker container
make docker-run

# Build and run the docker container
make docker-all

# Deploy the CLI container image in Kubernetes
oc apply -f deployment.yml

# Exec into the container
oc exec -ti $(oc get pod -l app=mas-cli -o name) -- bash

# Pick up a rebuild of the image
oc delete $(oc get pod -l app=mas-cli -o name)
```
