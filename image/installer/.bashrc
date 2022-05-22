#!/bin/bash

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

echo "${TEXT_UNDERLINE}IBM Maximo Application Suite Installer Container ${TEXT_BOLD}v${VERSION}${TEXT_RESET}"
echo
echo "${COLOR_CYAN}${TEXT_UNDERLINE}https://github.ibm.com/ibm-mas/installer${TEXT_RESET}"
echo
echo "Type ${TEXT_BOLD}${COLOR_GREEN}mas install${TEXT_RESET} to begin ..."
echo