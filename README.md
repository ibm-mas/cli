# IBM Maximo Application Suite CLI Utility
[![GitHub release](https://img.shields.io/github/v/release/ibm-mas/cli)](https://github.com/ibm-mas/cli/releases/latest)
[![Ansible Galaxy Release](https://img.shields.io/badge/dynamic/json?style=flat&label=ibm.mas_devops&prefix=v&url=https://galaxy.ansible.com/api/v2/collections/ibm/mas_devops/&query=latest_version.version)](https://galaxy.ansible.com/ibm/mas_devops)

## Introduction

There are minimal dependencies to meet on your own computer to use the CLI:

- Bash (v4)
- OpenShift client
- IBMCloud client with container plugin enabled
- Ansible
- Python
- Network access to the OpenShift cluster

The best way to use the CLI is via the container image: `docker run -ti -v ~:/mnt/home --pull always quay.io/ibmmas/cli`.

All settings can be controlled via environment variables to avoid needing to manually type them out, for example if you `export IBM_ENTITLEMENT_KEY=xxxx` then when you run the install that input will be prefilled with the value from the environment variable, allowing you to press Enter to continue, or modify the value if you need to.

The engine that performs all tasks is written in Ansible, you can directly use the same automation outside of this CLI if you wish.  The code is open source and available in [ibm-mas/ansible-devops](https://github.com/ibm-mas/ansible-devops), the collection is also available to install directly from Ansible Galaxy:

- [Ansible Galaxy: ibm.mas_devops](https://galaxy.ansible.com/ibm/mas_devops)


## Documentation
[https://ibm-mas.github.io/cli/](https://ibm-mas.github.io/cli/)
