IBM Maximo Application Suite CLI Utility
===============================================================================
The CLI comes in two flavours; **container image** and **standalone uvx tool**.


Container Image
-------------------------------------------------------------------------------
The MAS CLI container image is published to quay.io:

```bash
podman run -ti --rm -v ~:/mnt/home --pull always quay.io/ibmmas/cli mas install --help
```

!!! tip
    If you want to stick with a specific release of the image you can attach a  version tag to the docker run command: `docker run -ti --rm -v ~:/mnt/home quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@`

The container image provides an out of the box environment for managing MAS on OpenShift, with numerous dependencies pre-installed (see [cli-base](https://github.com/ibm-mas/cli-base) for details).  The Maximo Application Suite Ansible Collection is included in these dependencies, so even if you prefer to drive Ansible directly, the CLI image can be a useful tool:

```bash
podman run -ti --rm -v ~:/mnt/home --pull always quay.io/ibmmas/cli ansible-playbook ibm.mas_devops.mas_install_core
```


Standalone
-------------------------------------------------------------------------------
Introduced in 2026, replacing the standalone binary built with PyInstaller, the mas-cli is now compatible with [uv](https://docs.astral.sh/uv/) and is the easiest way run the CLI yet.

- [Install uv](https://docs.astral.sh/uv/getting-started/installation/)

### Ephemeral Execution
Run the MAS CLI without any install:

```bash
uvx mas-cli --help
```

### Persistent Installation
Install the MAS CLI globally:

```bash
# Install the latest version of mas-cli
uv tool install mas-cli

# The 'mas-cli' command is available in your PATH
mas-cli --help

# Upgrade or uninstall the mas-cli
uv tool upgrade mas-cli
uv tool uninstall mas-cli
```

!!! tip "Choosing a specific version"
    You can use a specific version of mas-cli by with ephemeral execution or installation using `mas-cli@@@CLI_LATEST_VERSION@@`


Function support
-------------------------------------------------------------------------------
Not all functions supported in the container image are available in the standalone CLI (yet):

| CLI Function                                                        | container |  uvx |
| ------------------------------------------------------------------- | :-------: | :---: |
| [install](guides/install.md)                                        |    ✅    |   ✅  |
| [aiservice-install](guides/aiservice-install.md)                    |    ✅    |   ✅  |
| [update](guides/update.md)                                          |    ✅    |   ✅  |
| [upgrade](guides/upgrade.md)                                        |    ✅    |   ✅  |
| [uninstall](guides/uninstall.md)                                    |    ✅    |   ✅  |
| [must-gather](commands/must-gather.md)                              |    ✅    |   ✅  |
| [backup](guides/backup.md)                                          |    ✅    |   ✅  |
| [restore](guides/restore.md)                                        |    ✅    |   ✅  |
| [configure-airgap](guides/configure-airgap.md)                      |    ✅    |   ❌  |
| [mirror-images](guides/image-mirroring.md)                          |    ✅    |   ❌  |
| [mirror-redhat-images](commands/mirror-redhat-images.md)            |    ✅    |   ❌  |
| [setup-registry](guides/private-registry.md#registry-removal)       |    ✅    |   ❌  |
| [teardown-registry](guides/private-registry.md#registry-deployment) |    ✅    |   ❌  |
| [provision-aws](guides/provision-aws.md)                            |    ✅    |   ❌  |
| [provision-fyre](guides/provision-fyre.md)                          |    ✅    |   ❌  |
| [provision-roks](guides/provision-roks.md)                          |    ✅    |   ❌  |
| [configtool-oidc](commands/configtool-oidc.md)                      |    ✅    |   ❌  |
