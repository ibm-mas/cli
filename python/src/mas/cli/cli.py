# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************
from argparse import RawTextHelpFormatter
from shutil import which
from os import path
from sys import exit

# Use of the openshift client rather than the kubernetes client allows us access to "apply"
from openshift import dynamic
from kubernetes import config
from kubernetes.client import api_client

from prompt_toolkit import prompt, print_formatted_text, HTML
from prompt_toolkit.validation import Validator

from .validators import YesNoValidator, FileExistsValidator, DirectoryExistsValidator

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

from mas.cli import __version__ as packageVersion
from mas.devops.ocp import connect, isSNO

from sys import exit

import logging

logger = logging.getLogger(__name__)


def getHelpFormatter(formatter=RawTextHelpFormatter, w=160, h=50):
    """
    Return a wider HelpFormatter, if possible.

    https://stackoverflow.com/a/57655311
    """
    try:
        kwargs = {'width': w, 'max_help_position': h}
        formatter(None, **kwargs)
        return lambda prog: formatter(prog, **kwargs)
    except TypeError:
        logger.warn("argparse help formatter failed, falling back.")
        return formatter


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

        self.version = packageVersion
        self.h1count = 0
        self.h2count = 0

        self.localConfigDir = None
        self.templatesDir = path.join(path.abspath(path.dirname(__file__)), "templates")
        self.tektonDefsPath = path.join(self.templatesDir, "ibm-mas-tekton.yaml")

        self._isSNO = None

        self.compatibilityMatrix = {
            "8.11.x": {
                "assist": ["8.8.x", "8.7.x"],
                "iot": ["8.8.x", "8.7.x"],
                "manage": ["8.7.x", "8.6.x"],
                "monitor": ["8.11.x", "8.10.x"],
                "optimizer": ["8.5.x", "8.4.x"],
                "predict": ["8.9.x", "8.8.x"],
                "visualinspection": ["8.9.x", "8.8.x"]
            },
            "8.10.x": {
                "assist": ["8.7.x", "8.6.x"],
                "hputilities": ["8.6.x", "8.5.x"],
                "iot": ["8.7.x", "8.6.x"],
                "manage": ["8.6.x", "8.5.x"],
                "monitor": ["8.10.x", "8.9.x"],
                "optimizer": ["8.4.x", "8.3.x"],
                "predict": ["8.8.x", "8.7.x"],
                "visualinspection": ["8.8.x", "8.7.x"]
            }
        }

        self.spinner = {
            "interval": 80,
            "frames": [" ⠋", " ⠙", " ⠹", " ⠸", " ⠼", " ⠴", " ⠦", " ⠧", " ⠇", " ⠏"]
        }
        self.successIcon = "✅️"
        self.failureIcon = "❌"

        self._dynClient = None

        self.printTitle(f"IBM Maximo Application Suite Admin CLI v{self.version}")
        print_formatted_text(HTML("Powered by <DarkGoldenRod><u>https://github.com/ibm-mas/ansible-devops/</u></DarkGoldenRod> and <DarkGoldenRod><u>https://tekton.dev/</u></DarkGoldenRod>"))

        if which("kubectl") is None:
            logger.error("Could not find kubectl on the path")
            print_formatted_text(HTML("\n<Red>Error: Could not find kubectl on the path, see <u>https://kubernetes.io/docs/tasks/tools/#kubectl</u> for installation instructions</Red>\n"))
            exit(1)

    def getCompatibleVersions(self, coreChannel: str, appId: str) -> list:
        if coreChannel in self.compatibilityMatrix:
            return self.compatibilityMatrix[coreChannel][appId]
        else:
            return []

    def printTitle(self, message):
        print_formatted_text(HTML(f"<b><u>{message.replace(' & ', ' &amp; ')}</u></b>"))

    def printH1(self, message):
        self.h1count += 1
        self.h2count = 0
        print()
        print_formatted_text(HTML(f"<u><SteelBlue>{self.h1count}) {message.replace(' & ', ' &amp; ')}</SteelBlue></u>"))

    def printH2(self, message):
        self.h2count += 1
        print()
        print_formatted_text(HTML(f"<u><SkyBlue>{self.h1count}.{self.h2count}) {message.replace(' & ', ' &amp; ')}</SkyBlue></u>"))

    def printDescription(self, content: list) -> None:
        content[0] = "<LightSlateGrey>" + content[0]
        content[len(content) - 1] = content[len(content) - 1] + "</LightSlateGrey>"
        print_formatted_text(HTML("\n".join(content)))

    def printSummary(self, title: str, value: str) -> None:
        titleLength = len(title)
        message = f"{title} {'.' * (40 - titleLength)} {value}"
        print_formatted_text(HTML(f"  <SkyBlue>{message.replace(' & ', ' &amp; ')}</SkyBlue>"))

    def printParamSummary(self, message: str, param: str) -> None:
        if self.getParam(param) is None:
            self.printSummary(message, "<LightSlateGrey>Undefined</LightSlateGrey>")
        elif self.getParam(param) == "":
            self.printSummary(message, "<LightSlateGrey>Default</LightSlateGrey>")
        else:
            self.printSummary(message, self.getParam(param))

    def fatalError(self, message: str, exception: Exception=None) -> None:
        if exception is not None:
            print_formatted_text(HTML(f"<Red>Fatal Exception: {message.replace(' & ', ' &amp; ')}: {exception}</Red>"))
        else:
            print_formatted_text(HTML(f"<Red>Fatal Error: {message.replace(' & ', ' &amp; ')}</Red>"))
        exit(1)

    def isSNO(self):
        if self._isSNO is None:
            self._isSNO = isSNO(self.dynamicClient)
        return self._isSNO

    def yesOrNo(self, message: str, param: str=None) -> bool:
        response = prompt(HTML(f"<Yellow>{message.replace(' & ', ' &amp; ')}? [y/n]</Yellow> "), validator=YesNoValidator(), validate_while_typing=False)
        responseAsBool = response.lower() in ["y", "yes"]
        if param is not None:
            self.params[param] = "true" if responseAsBool else "false"
        return responseAsBool

    def promptForString(self, message: str, param: str=None, default: str="", isPassword: bool=False, validator: Validator=None) -> str:
        messageHTML = HTML(f"<Yellow>{message.replace(' & ', ' &amp; ')}</Yellow> ")
        response = prompt(messageHTML, is_password=isPassword, default=default, validator=validator, validate_while_typing=False)
        if param is not None:
            self.params[param] = response
        return response

    def promptForInt(self, message: str, param: str=None, default: int=None) -> int:
        if default is None:
            response = int(prompt(HTML(f"<Yellow>{message.replace(' & ', ' &amp; ')}</Yellow> ")))
        else:
            response = int(prompt(HTML(f"<Yellow>{message.replace(' & ', ' &amp; ')}</Yellow> "), default=str(default)))
        if param is not None:
            self.params[param] = str(response)
        return response

    def promptForListSelect(self, message: str, options: list, param: str=None, default: int=None) -> str:
        selection = self.promptForInt(message=message, default=default)
        self.setParam(param, options[selection+1])

    def promptForFile(self, message: str, mustExist: bool=True, default: str="") -> None:
        if mustExist:
            return prompt(HTML(f"<Yellow>{message.replace(' & ', ' &amp; ')}</Yellow> "), validator=FileExistsValidator(), validate_while_typing=False, default=default)
        else:
            return prompt(HTML(f"<Yellow>{message.replace(' & ', ' &amp; ')}</Yellow> "), default=default)

    def promptForDir(self, message: str, mustExist: bool=True, default: str="") -> None:
        if mustExist:
            return prompt(HTML(f"<Yellow>{message.replace(' & ', ' &amp; ')}</Yellow> "), validator=DirectoryExistsValidator(), validate_while_typing=False, default=default)
        else:
            return prompt(HTML(f"<Yellow>{message.replace(' & ', ' &amp; ')}</Yellow> "), default=default)

    def setParam(self, param: str, value: str):
        self.params[param] = value

    def getParam(self, param: str):
        if param in self.params:
            return self.params[param]
        else:
            return ""

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
        try:
            config.load_kube_config()
            self._dynClient = dynamic.DynamicClient(
                api_client.ApiClient(configuration=config.load_kube_config())
            )
            return self._dynClient
        except Exception as e:
            logger.warning(f"Error: Unable to connect to OpenShift Container Platform: {e}")
            return None

    def connect(self, noConfirm):
        promptForNewServer = False
        self.reloadDynamicClient()
        if self._dynClient is not None:
            try:
                routesAPI = self._dynClient.resources.get(api_version="route.openshift.io/v1", kind="Route")
                consoleRoute = routesAPI.get(name="console", namespace="openshift-console")
                print_formatted_text(HTML(f"Already connected to OCP Cluster:\n <u><Orange>https://{consoleRoute.spec.host}</Orange></u>"))
                print()
                if not noConfirm:
                    # We are already connected to a cluster, but prompt the user if they want to use this connection
                    continueWithExistingCluster = prompt(HTML('<Yellow>Proceed with this cluster?</Yellow> '), validator=YesNoValidator(), validate_while_typing=False)
                    promptForNewServer = continueWithExistingCluster in ["n", "no"]
            except Exception:
                # We are already connected to a cluster, but the connection is not valid so prompt for connection details
                promptForNewServer = True
        else:
            # We are not already connected to any cluster, so prompt for connection details
            promptForNewServer = True

        if promptForNewServer:
            # Prompt for new connection properties
            server = prompt(HTML('<Yellow>Server URL:</Yellow> '), placeholder="https://...")
            token = prompt(HTML('<Yellow>Login Token:</Yellow> '), is_password=True, placeholder="sha256~...")
            connect(server, token)
            self.reloadDynamicClient()
            if self._dynClient is None:
                print_formatted_text(HTML("<Red>Unable to connect to cluster.  See log file for details</Red>"))
                exit(1)
