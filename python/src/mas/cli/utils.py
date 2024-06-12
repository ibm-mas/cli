# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

# Use of the openshift client rather than the kubernetes client allows us access to "apply"
from openshift import dynamic
from kubernetes import config
from kubernetes.client import api_client

from prompt_toolkit import prompt, print_formatted_text, HTML
from prompt_toolkit.output import ColorDepth
from prompt_toolkit.validation import Validator, ValidationError

# Available named colours in prompt_toolkit
# -----------------------------------------------------------------------------
# AliceBlue  AntiqueWhite  Aqua  Aquamarine  Azure  Beige  Bisque  Black  BlanchedAlmond  Blue  BlueViolet
# Brown  BurlyWood  CadetBlue  Chartreuse  Chocolate  Coral  CornflowerBlue  Cornsilk  Crimson  Cyan
# DarkBlue  DarkCyan  DarkGoldenRod  DarkGray  DarkGreen  DarkGrey  DarkKhaki  DarkMagenta  DarkOliveGreen
# DarkOrange  DarkOrchid  DarkRed  DarkSalmon  DarkSeaGreen  DarkSlateBlue  DarkSlateGray  DarkSlateGrey
# DarkTurquoise  DarkViolet  DeepPink  DeepSkyBlue  DimGray  DimGrey  DodgerBlue  FireBrick  FloralWhite
# ForestGreen  Fuchsia  Gainsboro  GhostWhite  Gold  GoldenRod  Gray  Green  GreenYellow  Grey  HoneyDew
# HotPink  IndianRed  Indigo  Ivory  Khaki  Lavender  LavenderBlush  LawnGreen  LemonChiffon  LightBlue
# LightCoral  LightCyan  LightGoldenRodYellow  LightGray  LightGreen  LightGrey  LightPink  LightSalmon
# LightSeaGreen  LightSkyBlue  LightSlateGray  LightSlateGrey  LightSteelBlue  LightYellow  Lime
# LimeGreen  Linen  Magenta  Maroon  MediumAquaMarine  MediumBlue  MediumOrchid  MediumPurple  MediumSeaGreen
# MediumSlateBlue  MediumSpringGreen  MediumTurquoise  MediumVioletRed  MidnightBlue  MintCream  MistyRose
# Moccasin  NavajoWhite  Navy  OldLace  Olive  OliveDrab  Orange  OrangeRed  Orchid  PaleGoldenRod  PaleGreen
# PaleTurquoise  PaleVioletRed  PapayaWhip  PeachPuff  Peru  Pink  Plum  PowderBlue  Purple  RebeccaPurple
# Red  RosyBrown  RoyalBlue  SaddleBrown  Salmon  SandyBrown  SeaGreen  SeaShell  Sienna  Silver  SkyBlue
# SlateBlue  SlateGray  SlateGrey  Snow  SpringGreen  SteelBlue  Tan  Teal  Thistle  Tomato  Turquoise
# Violet  Wheat  White  WhiteSmoke  Yellow  YellowGreen

from mas.devops.ocp import connect
from mas.devops.mas import verifyMasInstance

from sys import exit

import logging

logger = logging.getLogger(__name__)

class InstanceIDValidator(Validator):
    def validate(self, document):
        """
        Validate that a MAS instance ID exists on the target cluster
        """
        instanceId = document.text

        dynClient = dynamic.DynamicClient(
            api_client.ApiClient(configuration=config.load_kube_config())
        )
        if not verifyMasInstance(dynClient, instanceId):
            raise ValidationError(message='Not a valid MAS instance ID on this cluster', cursor_position=len(instanceId))


class YesNoValidator(Validator):
    def validate(self, document):
        """
        Validate that a response is understandable as a yes/no response
        """
        response = document.text
        if response.lower() not in ["y", "n", "yes", "no" ]:
            raise ValidationError(message='Enter a valid response: y(es), n(o)', cursor_position=len(response))


class BaseApp(object):
    def __init__(self):
        # Set up a log formatter
        chFormatter = logging.Formatter('%(asctime)-25s' + ' %(levelname)-8s %(message)s')

        # Set up a log handler (5mb rotating log file)
        ch = logging.handlers.RotatingFileHandler(
            "mas.log", maxBytes=(1048576*5), backupCount=2
        )
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(chFormatter)

        # Configure the root logger
        rootLogger = logging.getLogger()
        rootLogger.addHandler(ch)
        rootLogger.setLevel(logging.DEBUG)

        self.version = "1.0.0"
        self.h1count = 0

        self.spinner = {
            "interval": 80,
            "frames": [ " ⠋", " ⠙", " ⠹", " ⠸", " ⠼", " ⠴", " ⠦", " ⠧", " ⠇", " ⠏" ]
        }
        self.successIcon="✅️"
        self.failureIcon="❌"

        self._dynClient = None

        self.printTitle(f"IBM Maximo Application Suite Admin CLI v{self.version}")
        print_formatted_text(HTML("Powered by <DarkGoldenRod><u>https://github.com/ibm-mas/ansible-devops/</u></DarkGoldenRod> and <DarkGoldenRod><u>https://tekton.dev/</u></DarkGoldenRod>"))


    def printTitle(self, message):
        print_formatted_text(HTML(f"<b><u><DeepSkyBlue>{message}</DeepSkyBlue></u></b>"), color_depth=ColorDepth.TRUE_COLOR)


    def printH1(self, message):
        self.h1count += 1
        print()
        print_formatted_text(HTML(f"<u><SteelBlue>{self.h1count}. {message}</SteelBlue></u>"), color_depth=ColorDepth.TRUE_COLOR)


    @property
    def dynamicClient(self):
        if self._dynClient is not None:
            return self._dynClient
        else:
            return self.reloadDynamicClient()


    def reloadDynamicClient(self):
        """
        Configure the Kubernetes API Client using the active context in kubeconfig
        """
        logger.debug("Reloading Kubernetes Client Configuration")
        config.load_kube_config()
        try:
            self._dynClient = dynamic.DynamicClient(
                api_client.ApiClient(configuration=config.load_kube_config())
            )
            return self._dynClient
        except Exception as e:
            logger.warning(f"Error: Unable to connect to OpenShift Container Platform: {e}")
            print_formatted_text(HTML(f"<Red>Error: Unable to connect to OpenShift Container Platform.  See log file for details</Red>"))
            return None


    def connect(self, noConfirm):
        promptForNewServer = False
        self.reloadDynamicClient()
        if self.dynamicClient is not None:
            routesAPI = self.dynamicClient.resources.get(api_version="route.openshift.io/v1", kind="Route")
            consoleRoute = routesAPI.get(name="console", namespace="openshift-console")
            print_formatted_text(HTML(f"Already connected to OCP Cluster:\n <u><Orange>https://{consoleRoute.spec.host}</Orange></u>"))
            print()
            if not noConfirm:
                continueWithExistingCluster = prompt(HTML(f'<Yellow>Proceed with this cluster?</Yellow> '), validator=YesNoValidator(), validate_while_typing=False, default="y")
                promptForNewServer = continueWithExistingCluster in ["n", "no"]
        else:
            promptForNewServer = True

        if promptForNewServer:
            # Prompt for new connection properties
            server = prompt(HTML(f'<Yellow>Server URL:</Yellow> '), placeholder="https://...")
            token = prompt(HTML(f'<Yellow>Login Token:</Yellow> '), is_password=True, placeholder="sha256~...")
            connect(server, token)
            self.reloadDynamicClient()
            if self.dynamicClient is None:
                print_formatted_text(HTML(f"<Red>Unable to connect to cluster.  See log file for details</Red>"))
                exit(1)
