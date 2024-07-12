# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

import logging
import urllib3

from argparse import RawTextHelpFormatter
from shutil import which
from os import path
from sys import exit

# Use of the openshift client rather than the kubernetes client allows us access to "apply"
from openshift import dynamic
from kubernetes import config
from kubernetes.client import api_client

from prompt_toolkit import prompt, print_formatted_text, HTML

from mas.devops.ocp import connect, isSNO

from . import __version__ as packageVersion
from .validators import YesNoValidator
from .displayMixins import PrintMixin, PromptMixin

# Configure the logger
logger = logging.getLogger(__name__)

# Disable warnings when users are connecting to OCP clusters with self-signed certificates
urllib3.disable_warnings()

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


class BaseApp(PrintMixin, PromptMixin):
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

        # Initialize the dictionary that will hold the parameters we pass to a PipelineRun
        self.params = dict()

        # These dicts will hold the additional-configs, pod-templates and manual certificates secrets
        self.additionalConfigsSecret = None
        self.podTemplatesSecret = None
        self.certsSecret = None

        self._isSNO = None

        self.compatibilityMatrix = {
            "9.0.x": {
                "assist": ["9.0.x", "8.8.x"],
                "iot": ["9.0.x", "8.8.x"],
                "manage": ["9.0.x", "8.7.x"],
                "monitor": ["9.0.x", "8.11.x"],
                "optimizer": ["9.0.x", "8.5.x"],
                "predict": ["9.0.x", "8.9.x"],
                "visualinspection": ["9.0.x", "8.9.x"]
            },
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

        self.printTitle(f"\nIBM Maximo Application Suite Admin CLI v{self.version}")
        print_formatted_text(HTML("Powered by <DarkGoldenRod><u>https://github.com/ibm-mas/ansible-devops/</u></DarkGoldenRod> and <DarkGoldenRod><u>https://tekton.dev/</u></DarkGoldenRod>\n"))
        if which("kubectl") is None:
            self.fatalError("Could not find kubectl on the path, see <DarkGoldenRod><u>https://kubernetes.io/docs/tasks/tools/#kubectl</u></DarkGoldenRod> for installation instructions")

    def getCompatibleVersions(self, coreChannel: str, appId: str) -> list:
        if coreChannel in self.compatibilityMatrix:
            return self.compatibilityMatrix[coreChannel][appId]
        else:
            return []

    def fatalError(self, message: str, exception: Exception=None) -> None:
        if exception is not None:
            logger.error(message)
            logger.exception(exception, stack_info=True)
            print_formatted_text(HTML(f"<Red>Fatal Exception: {message.replace(' & ', ' &amp; ')}: {exception}</Red>\n"))
        else:
            logger.error(message)
            print_formatted_text(HTML(f"<Red>Fatal Error: {message.replace(' & ', ' &amp; ')}</Red>\n"))
        exit(1)

    def isSNO(self):
        if self._isSNO is None:
            self._isSNO = isSNO(self.dynamicClient)
        return self._isSNO

    def setParam(self, param: str, value: str):
        self.params[param] = value

    def getParam(self, param: str):
        """
        Returns the value of a parameter, or an empty string is the parameter has not set at all or is set to None
        """
        if param in self.params and self.params[param] is not None:
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

    def connect(self):
        promptForNewServer = False
        self.reloadDynamicClient()
        if self._dynClient is not None:
            try:
                routesAPI = self._dynClient.resources.get(api_version="route.openshift.io/v1", kind="Route")
                consoleRoute = routesAPI.get(name="console", namespace="openshift-console")
                print_formatted_text(HTML(f"Already connected to OCP Cluster:\n <u><Orange>https://{consoleRoute.spec.host}</Orange></u>"))
                print()
                if not self.noConfirm:
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
