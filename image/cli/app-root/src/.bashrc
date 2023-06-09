#!/bin/bash

# Note:bash uses \[ \] to determine the "displayed length": text between those two escapes is considered unprintable and
# not counted in the total length; everything else is.
export PS1="[\[\e[0;32m\]ibmmas/cli:$VERSION\[\e[0m\]]\[\e[0;36m\]\W\[\e[0m\]\$ "
COLOR_RED=`tput setaf 1`
COLOR_GREEN=`tput setaf 2`
COLOR_YELLOW=`tput setaf 3`
COLOR_BLUE=`tput setaf 4`
COLOR_MAGENTA=`tput setaf 5`
COLOR_CYAN=`tput setaf 6`
COLOR_RESET=`tput sgr0`

TEXT_BOLD=$(tput bold)
TEXT_DIM=$(tput dim)
TEXT_UNDERLINE=$(tput smul)
TEXT_RESET=$(tput sgr0)

echo "${TEXT_UNDERLINE}IBM Maximo Application Suite CLI Container ${TEXT_BOLD}v${VERSION}${TEXT_RESET}"
echo
echo "${COLOR_CYAN}${TEXT_UNDERLINE}https://github.com/ibm-mas/ansible-devops${TEXT_RESET}"
echo "${COLOR_CYAN}${TEXT_UNDERLINE}https://github.com/ibm-mas/cli${TEXT_RESET}"
echo
echo "MAS Management:"
echo "  - ${TEXT_BOLD}${COLOR_GREEN}mas install${TEXT_RESET} to install a new MAS instance"
echo "  - ${TEXT_BOLD}${COLOR_GREEN}mas update${TEXT_RESET} to apply a new catalog update"
echo "  - ${TEXT_BOLD}${COLOR_GREEN}mas upgrade${TEXT_RESET} to upgrade an existing MAS install to a new release"
echo "  - ${TEXT_BOLD}${COLOR_GREEN}mas must-gather${TEXT_RESET} to perform must-gather against the target cluster"
echo "  - ${TEXT_BOLD}${COLOR_GREEN}mas uninstall${TEXT_RESET} to uninstall a MAS instance"
echo "Disconnected Install Support:"
echo "  - ${TEXT_BOLD}${COLOR_GREEN}mas setup-registry${TEXT_RESET} to setup a private container registry on an OCP cluster"
echo "  - ${TEXT_BOLD}${COLOR_GREEN}mas mirror-images${TEXT_RESET} to mirror container images required by mas to a private registry"
echo "  - ${TEXT_BOLD}${COLOR_GREEN}mas configure-mirror${TEXT_RESET} to configure a cluster to use a private registry as a mirror"
echo "Cluster Management:"
echo "  - ${TEXT_BOLD}${COLOR_GREEN}mas provision-fyre${TEXT_RESET} to provision an OCP cluster on IBM DevIT Fyre (internal)"
echo "  - ${TEXT_BOLD}${COLOR_GREEN}mas provision-roks${TEXT_RESET} to provision an OCP cluster on IBMCloud Red Hat OpenShift Service (ROKS)"
echo "  - ${TEXT_BOLD}${COLOR_GREEN}mas provision-aws${TEXT_RESET} to provision an OCP cluster on AWS"
echo "  - ${TEXT_BOLD}${COLOR_GREEN}mas provision-rosa${TEXT_RESET} to provision an OCP cluster on AWS Red Hat OpenShift Service (ROSA)"
echo
