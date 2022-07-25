# IBM Maximo Application Suite CLI Utility

There are various dependencies to meet on your own computer to use the CLI, depending on which functions you are using:

- Bash (v4)
- OpenShift client
- IBMCloud client with container plugin enabled
- Ansible
- Python
- Network access to the OpenShift cluster

The best way to use the CLI is via the container image: `docker run -ti -v ~:/home/local quay.io/ibmmas/cli`.  To ensure you have the latest version of the image run `docker pull quay.io/ibmmas/cli` first.

The install is designed to work on any OCP cluster, but has been specifically tested in these environments:

- IBMCloud ROKS
- Microsoft Azure
- IBM DevIT FYRE (internal)

All settings can be controlled via environment variables to avoid needing to manually type them out, for example if you `export IBM_ENTITLEMENT_KEY=xxxx` then when you run the install that input will be prefilled with the value from the environment variable, allowing you to press Enter to continue, or modify the value if you need to.

The engine that performs all tasks is written in Ansible, you can directly use the same automation outside of this CLI if you wish.  The code is open source and available in [ibm-mas/ansible-devops](https://github.com/ibm-mas/ansible-devops) and [ibm-mas/ansible-airgap](https://github.com/ibm-mas/ansible-airgap), the collections are also available to install directly from Ansible Galaxy:

- [Ansible Galaxy: ibm.mas_devops](https://galaxy.ansible.com/ibm/mas_devops)
- [Ansible Galaxy: ibm.mas_airgap](https://galaxy.ansible.com/ibm/mas_airgap)
