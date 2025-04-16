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
from os import path, environ
from sys import exit
from subprocess import PIPE, Popen, TimeoutExpired
import threading
import json

# Use of the openshift client rather than the kubernetes client allows us access to "apply"
from kubernetes import config
from kubernetes.client import api_client, Configuration
from openshift.dynamic import DynamicClient
from openshift.dynamic.exceptions import NotFoundError

from prompt_toolkit import prompt, print_formatted_text, HTML

from mas.devops.mas import isAirgapInstall
from mas.devops.ocp import connect, isSNO, getNodes

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
        logger.warning("argparse help formatter failed, falling back.")
        return formatter


class RunCmdResult(object):
    def __init__(self, returnCode, output, error):
        self.rc = returnCode
        self.out = output
        self.err = error

    def successful(self):
        return self.rc == 0

    def failed(self):
        return self.rc != 0


def runCmd(cmdArray, timeout=630):
    """
    Run a command on the local host.  This drives all the helm operations,
    as there is no python Helm client available.
    # Parameters
    cmdArray (list<string>): Command to execute
    timeout (int): How long to allow for the command to complete
    # Returns
    [int, string, string]: `returnCode`, `stdOut`, `stdErr`
    """

    lock = threading.Lock()

    with lock:
        p = Popen(cmdArray, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=-1)
        try:
            output, error = p.communicate(timeout=timeout)
            return RunCmdResult(p.returncode, output, error)
        except TimeoutExpired as e:
            return RunCmdResult(127, 'TimeoutExpired', str(e))


def logMethodCall(func):
    def wrapper(self, *args, **kwargs):
        logger.debug(f">>> BaseApp.{func.__name__}")
        result = func(self, *args, **kwargs)
        logger.debug(f"<<< BaseApp.{func.__name__}")
        return result
    return wrapper


class BaseApp(PrintMixin, PromptMixin):
    def __init__(self):
        # Set up a log formatter
        chFormatter = logging.Formatter('%(asctime)-25s' + ' %(levelname)-8s %(message)s')

        # Set up a log handler (5mb rotating log file)
        ch = logging.handlers.RotatingFileHandler(
            "mas.log", maxBytes=(1048576 * 5), backupCount=2
        )
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(chFormatter)

        # Configure the root logger
        rootLogger = logging.getLogger()
        rootLogger.addHandler(ch)
        rootLogger.setLevel(logging.DEBUG)
        logging.getLogger('asyncio').setLevel(logging.INFO)

        # Supports extended semver, unlike mas.cli.__version__
        self.version = "100.0.0-pre.local"
        self.h1count = 0
        self.h2count = 0

        self.localConfigDir = None
        self.templatesDir = path.join(path.abspath(path.dirname(__file__)), "templates")
        self.tektonDefsWithoutDigestPath = path.join(self.templatesDir, "ibm-mas-tekton.yaml")
        self.tektonDefsWithDigestPath = path.join(self.templatesDir, "ibm-mas-tekton-with-digest.yaml")

        # Default to using the tekton definitions without image digests
        self.tektonDefsPath = self.tektonDefsWithoutDigestPath

        # Initialize the dictionary that will hold the parameters we pass to a PipelineRun
        self.params = dict()

        # These dicts will hold the additional-configs, pod-templates, sls license file and manual certificates secrets
        self.additionalConfigsSecret = None
        self.podTemplatesSecret = None
        self.slsLicenseFileSecret = None
        self.certsSecret = None

        self._isSNO = None
        self._isAirgap = None

        # Until we connect to the cluster we don't know what architecture it's worker nodes are
        self.architecture = None

        self.compatibilityMatrix = {
            "9.1.x-feature": {
                "assist": ["9.0.x"],
                "iot": ["9.0.x"],
                "manage": ["9.1.x-feature", "9.0.x"],
                "monitor": ["9.0.x"],
                "optimizer": ["9.1.x-feature", "9.0.x"],
                "predict": ["9.0.x"],
                "visualinspection": ["9.1.x-feature", "9.0.x"],
                "aibroker": ["9.0.x"],
            },
            "9.0.x": {
                "assist": ["9.0.x", "8.8.x"],
                "iot": ["9.0.x", "8.8.x"],
                "manage": ["9.0.x", "8.7.x"],
                "monitor": ["9.0.x", "8.11.x"],
                "optimizer": ["9.0.x", "8.5.x"],
                "predict": ["9.0.x", "8.9.x"],
                "visualinspection": ["9.0.x", "8.9.x"],
                "aibroker": ["9.0.x"],
            },
            "8.11.x": {
                "assist": ["8.8.x", "8.7.x"],
                "iot": ["8.8.x", "8.7.x"],
                "manage": ["8.7.x", "8.6.x"],
                "monitor": ["8.11.x", "8.10.x"],
                "optimizer": ["8.5.x", "8.4.x"],
                "predict": ["8.9.x", "8.8.x"],
                "visualinspection": ["8.9.x", "8.8.x"],
            },
            "8.10.x": {
                "assist": ["8.7.x", "8.6.x"],
                "hputilities": ["8.6.x", "8.5.x"],
                "iot": ["8.7.x", "8.6.x"],
                "manage": ["8.6.x", "8.5.x"],
                "monitor": ["8.10.x", "8.9.x"],
                "optimizer": ["8.4.x", "8.3.x"],
                "predict": ["8.8.x", "8.7.x"],
                "visualinspection": ["8.8.x", "8.7.x"],
            },
        }

        self.licenses = {
            "8.9.x": " - <u>https://ibm.biz/MAS89-License</u>",
            "8.10.x": " - <u>https://ibm.biz/MAS810-License</u>",
            "8.11.x": " - <u>https://ibm.biz/MAS811-License</u>\n - <u>https://ibm.biz/MAXIT81-License</u>",
            "9.0.x": " - <u>https://ibm.biz/MAS90-License</u>\n - <u>https://ibm.biz/MaximoIT90-License</u>\n - <u>https://ibm.biz/MAXArcGIS90-License</u>",
            "9.1.x-feature": " - <u>https://ibm.biz/MAS90-License</u>\n - <u>https://ibm.biz/MaximoIT90-License</u>\n - <u>https://ibm.biz/MAXArcGIS90-License</u>\n\nBe aware, this channel subscription is supported for non-production use only.   \nIt allows early access to new features for evaluation in non-production environments.   \nThis subscription is offered alongside and in parallel with our normal maintained streams.   \nWhen using this subscription, IBM Support will only accept cases for the latest available bundle deployed in a non-production environment.   \nSeverity must be either 3 or 4 and cases cannot be escalated.   \nPlease refer to IBM documentation for more details.\n",
        }

        self.upgrade_path = {
            "9.0.x": "9.1.x-feature",
            "8.11.x": "9.0.x",
            "8.10.x": "8.11.x",
            "8.9.x": "8.10.x",
        }

        self.spinner = {
            "interval": 80,
            "frames": [" ⠋", " ⠙", " ⠹", " ⠸", " ⠼", " ⠴", " ⠦", " ⠧", " ⠇", " ⠏"]
        }
        self.successIcon = "✅️"
        self.failureIcon = "❌"

        self._dynClient = None

        self.printTitle(f"\nIBM Maximo Application Suite Admin CLI v{self.version}")
        print_formatted_text(HTML("Powered by <Orange><u>https://github.com/ibm-mas/ansible-devops/</u></Orange> and <Orange><u>https://tekton.dev/</u></Orange>\n"))
        if which("kubectl") is None:
            self.fatalError("Could not find kubectl on the path, see <Orange><u>https://kubernetes.io/docs/tasks/tools/#kubectl</u></Orange> for installation instructions")

    @logMethodCall
    def createTektonFileWithDigest(self) -> None:
        if path.exists(self.tektonDefsWithDigestPath):
            logger.debug(f"We have already generated {self.tektonDefsWithDigestPath}")
        elif isAirgapInstall(self.dynamicClient):
            # We need to modify the tekton definitions to
            imageWithoutDigest = f"quay.io/ibmmas/cli:{self.version}"
            self.printH1("Disconnected OpenShift Preparation")
            self.printDescription([
                f"Unless the {imageWithoutDigest} image is accessible from your cluster the MAS CLI container image must be present in your mirror registry"
            ])
            cmdArray = ["skopeo", "inspect", f"docker://{imageWithoutDigest}"]
            logger.info(f"Skopeo inspect command: {' '.join(cmdArray)}")
            skopeoResult = runCmd(cmdArray)
            if skopeoResult.successful():
                skopeoData = json.loads(skopeoResult.out)
                logger.info(f"Skopeo Data for {imageWithoutDigest}: {skopeoData}")
                if "Digest" not in skopeoData:
                    self.fatalError("Recieved bad data inspecting CLI manifest to determine digest")
                cliImageDigest = skopeoData["Digest"]
            else:
                warning = f"Unable to retrieve image digest for {imageWithoutDigest} ({skopeoResult.rc})"
                self.printWarning(warning)
                logger.warning(warning)
                logger.warning(skopeoResult.err)
                if self.noConfirm:
                    self.fatalError("Unable to automatically determine CLI image digest and --no-confirm flag has been set")
                else:
                    cliImageDigest = self.promptForString(f"Enter {imageWithoutDigest} image digest")

            # Overwrite the tekton definitions with one that uses the looked up image digest
            imageWithDigest = f"quay.io/ibmmas/cli@{cliImageDigest}"
            self.printHighlight(f"\nConverting Tekton definitions to use {imageWithDigest}")
            with open(self.tektonDefsPath, 'r') as file:
                tektonDefsWithoutDigest = file.read()

            tektonDefsWithDigest = tektonDefsWithoutDigest.replace(imageWithoutDigest, imageWithDigest)

            with open(self.tektonDefsWithDigestPath, 'w') as file:
                file.write(tektonDefsWithDigest)

            self.tektonDefsPath = self.tektonDefsWithDigestPath

    @logMethodCall
    def getCompatibleVersions(self, coreChannel: str, appId: str) -> list:
        if coreChannel in self.compatibilityMatrix:
            return self.compatibilityMatrix[coreChannel][appId]
        else:
            return []

    @logMethodCall
    def fatalError(self, message: str, exception: Exception = None) -> None:
        if exception is not None:
            logger.error(message)
            logger.exception(exception, stack_info=True)
            print_formatted_text(HTML(f"<Red>Fatal Exception: {message.replace(' & ', ' &amp; ')}: {exception}</Red>\n"))
        else:
            logger.error(message)
            print_formatted_text(HTML(f"<Red>Fatal Error: {message.replace(' & ', ' &amp; ')}</Red>\n"))
        exit(1)

    @logMethodCall
    def isSNO(self):
        if self._isSNO is None:
            self._isSNO = isSNO(self.dynamicClient)
        return self._isSNO

    @logMethodCall
    def isAirgap(self):
        if self._isAirgap is None:
            # First check if the legacy ICSP is installed.  If it is raise an error and instruct the user to re-run configure-airgap to
            # migrate the cluster from ICSP to IDMS
            if isAirgapInstall(self.dynamicClient, checkICSP=True):
                self.fatalError("Deprecated Maximo Application Suite ImageContentSourcePolicy detected on the target cluster.  Run 'mas configure-airgap' to migrate to the replacement ImageDigestMirrorSet beofre proceeding.")
            self._isAirgap = isAirgapInstall(self.dynamicClient)
        return self._isAirgap

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

    @logMethodCall
    def reloadDynamicClient(self):
        """
        Configure the Kubernetes API Client using the active context in kubeconfig
        """
        logger.debug("Reloading Kubernetes Client Configuration")
        try:
            if "KUBERNETES_SERVICE_HOST" in environ:
                config.load_incluster_config()
                k8s_config = Configuration.get_default_copy()
                self._apiClient = api_client.ApiClient(configuration=k8s_config)
                self._dynClient = DynamicClient(self._apiClient)
            else:
                config.load_kube_config()
                self._apiClient = api_client.ApiClient()
                self._dynClient = DynamicClient(self._apiClient)
            return self._dynClient
        except Exception as e:
            logger.warning(f"Error: Unable to connect to OpenShift Container Platform: {e}")
            logger.exception(e, stack_info=True)
            return None

    @logMethodCall
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
                    promptForNewServer = not self.yesOrNo("Proceed with this cluster")
            except Exception as e:
                # We are already connected to a cluster, but the connection is not valid so prompt for connection details
                logger.debug("Failed looking up OpenShift Console route to verify connection")
                logger.exception(e, stack_info=True)
                promptForNewServer = True
        else:
            # We are not already connected to any cluster, so prompt for connection details
            promptForNewServer = True

        if promptForNewServer:
            # Prompt for new connection properties
            server = prompt(HTML('<Yellow>Server URL:</Yellow> '), placeholder="https://...")
            token = prompt(HTML('<Yellow>Login Token:</Yellow> '), is_password=True, placeholder="sha256~...")
            skipVerify = self.yesOrNo('Disable TLS Verify')
            connect(server, token, skipVerify)
            self.reloadDynamicClient()
            if self._dynClient is None:
                print_formatted_text(HTML("<Red>Unable to connect to cluster.  See log file for details</Red>"))
                exit(1)

        # Now that we are connected, inspect the architecture of the OpenShift cluster
        self.lookupTargetArchitecture()

    @logMethodCall
    def lookupTargetArchitecture(self, architecture: str = None) -> None:
        logger.debug("Looking up worker node architecture")
        if architecture is not None:
            self.architecture = architecture
            logger.debug(f"Target architecture (overridden): {self.architecture}")
        else:
            nodes = getNodes(self.dynamicClient)
            self.architecture = nodes[0]["status"]["nodeInfo"]["architecture"]
            logger.debug(f"Target architecture: {self.architecture}")

        if self.architecture not in ["amd64", "s390x"]:
            self.fatalError(f"Unsupported worker node architecture: {self.architecture}")

    @logMethodCall
    def initializeApprovalConfigMap(self, namespace: str, id: str, enabled: bool, maxRetries: int = 100, delay: int = 300, ignoreFailure: bool = True) -> None:
        """
        Set key = None if you don't want approval workflow enabled
        """
        cmAPI = self.dynamicClient.resources.get(api_version="v1", kind="ConfigMap")
        configMap = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": f"approval-{id}",
                "namespace": namespace
            },
            "data": {
                "MAX_RETRIES": str(maxRetries),
                "DELAY": str(delay),
                "IGNORE_FAILURE": str(ignoreFailure),
                "STATUS": ""
            }
        }

        # Delete any existing configmap and create a new one
        try:
            logger.debug(f"Deleting any existing approval workflow configmap for {id}")
            cmAPI.delete(name=f"approval-{id}", namespace=namespace)
        except NotFoundError:
            pass

        if enabled:
            logger.debug(f"Enabling approval workflow for {id} with {maxRetries} max retries on a {delay}s delay ({'ignoring failures' if ignoreFailure else 'abort on failure'})")
            cmAPI.create(body=configMap, namespace=namespace)
