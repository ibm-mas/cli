IBM Maximo Application Suite CLI Utility
===============================================================================
There are various dependencies to meet on your own computer to use the CLI, depending on which functions you are using:

- Bash (v4)
- OpenShift client
- IBMCloud client with container plugin enabled
- Ansible
- Python
- Network access to the OpenShift cluster


Installation
-------------------------------------------------------------------------------
The best way to use the CLI is to not install it at all and use the container image we publish:

```bash
docker run -ti -v ~:/home/local --pull always quay.io/ibmmas/cli
```

!!! tip
    Running `docker pull` before `docker run` will ensure you are using the latest release of the container image.

    If you want to stick with a specific release of the image you can attach a specific version tag to the docker run command: `docker run -ti -v ~:/home/local quay.io/ibmmas/cli:x.y.z`

If you prefer to install the client it can be obtained from the [GitHub releases page](https://github.com/ibm-mas/cli/releases).

```bash
wget https://github.com/ibm-mas/cli/releases/download/2.3.1/ibm-mas-cli-2.3.1.tgz
tar -xvf ibm-mas-cli-2.3.1.tgz
./mas mirror-images
```