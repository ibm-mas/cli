IBM Maximo Application Suite CLI Utility
===============================================================================
The CLI comes in two flavours; **container image** and **standalone binary**.

The standalone CLI is available for three platforms, and available from the downloads page on each [GitHub release](https://github.com/ibm-mas/cli/releases/tag/@@CLI_LATEST_VERSION@@), however it does not currently support everything supported by the container image:

| CLI Function                                             | Image    | Binary   |
| -------------------------------------------------------- | :------: | :------: |
| [install](commands/install.md)                           | &#10003; | &#10003; |
| [update](commands/update.md)                             | &#10003; | &#10003; |
| [upgrade](commands/upgrade.md)                           | &#10003; | &#10003; |
| [uninstall](commands/uninstall.md)                       | &#10003; | &#10003; |
| [must-gather](commands/must-gather.md)                   | &#10003; | &#10005; |
| [configure-airgap](commands/configure-airgap.md)         | &#10003; | &#10005; |
| [mirror-images](commands/mirror-images.md)               | &#10003; | &#10005; |
| [mirror-redhat-images](commands/mirror-redhat-images.md) | &#10003; | &#10005; |
| [setup-registry](commands/setup-registry.md)             | &#10003; | &#10005; |
| [teardown-registry](commands/teardown-registry.md)       | &#10003; | &#10005; |
| [provision-fyre](commands/provision-fyre.md)             | &#10003; | &#10005; |
| [provision-roks](commands/provision-roks.md)             | &#10003; | &#10005; |
| [provision-rosa](commands/provision-rosa.md)             | &#10003; | &#10005; |
| [configtool-oidc](commands/configtool-oidc.md)           | &#10003; | &#10005; |


Container Image
-------------------------------------------------------------------------------
The best way to use the MAS CLI is to use the container image we publish to quay.io:

```bash
docker run -ti --rm -v ~:/mnt/home --pull always quay.io/ibmmas/cli mas install --help
```

!!! tip
    If you want to stick with a specific release of the image you can attach a  version tag to the docker run command: `docker run -ti --rm -v ~:/mnt/home quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@`

The container image provides an out of the box environment for managing MAS on OpenShift, with numerous dependencies pre-installed (see [cli-base](https://github.com/ibm-mas/cli-base) for details).  The Maximo Application Suite Ansible Collection is included in these dependencies, so even if you prefer to drive Ansible directy the CLI image can be a useful tool:

```bash
docker run -ti --rm -v ~:/mnt/home --pull always quay.io/ibmmas/cli ansible-playbook ibm.mas_devops.oneclick_core
```


Standalone Binary
-------------------------------------------------------------------------------
Introduced in Summer 2024, the standalone binary is a new way to use the MAS CLI, you can download version @@CLI_LATEST_VERSION@@ of the CLI for following platforms using the links below:

- [Windows (amd64)](https://github.com/ibm-mas/cli/releases/download/@@CLI_LATEST_VERSION@@/mas-cli-windows-amd64)
- [Linux (amd64)](https://github.com/ibm-mas/cli/releases/download/@@CLI_LATEST_VERSION@@/mas-cli-linux-amd64)
- [MacOS (arm64)](https://github.com/ibm-mas/cli/releases/download/@@CLI_LATEST_VERSION@@/mas-cli-macos-arm64)

For example, to install the CLI and launch a MAS install on Linux:

```bash
wget https://github.com/ibm-mas/cli/releases/download/@@CLI_LATEST_VERSION@@/mas-cli-linux-amd64
cp mas-cli-linux-amd64 /usr/local/bin/mas-cli
mas-cli install --help
```
