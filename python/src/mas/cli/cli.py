# *****************************************************************************
# Copyright (c) 2024, 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

import logging
import logging.handlers
import urllib3

from argparse import RawTextHelpFormatter
from shutil import which
from os import path, environ
from sys import exit
from subprocess import PIPE, Popen, TimeoutExpired
import threading
import json
from typing import List, Dict, Any, Callable, Type, NoReturn

from kubernetes import config
from kubernetes.client.api_client import ApiClient
from kubernetes.client import Configuration
from kubernetes.dynamic import DynamicClient
from kubernetes.dynamic.exceptions import NotFoundError

from prompt_toolkit import prompt, print_formatted_text, HTML

from mas.devops.mas import isAirgapInstall
from mas.devops.ocp import connect, isSNO, getNodes
from mas.devops.utils import validateIBMEntitlementKey

from .displayMixins import PrintMixin, PromptMixin

# Configure the logger
logger = logging.getLogger(__name__)

# Disable warnings when users are connecting to OCP clusters with self-signed certificates
urllib3.disable_warnings()


def getHelpFormatter(formatter: Type[RawTextHelpFormatter] = RawTextHelpFormatter, w: int = 160, h: int = 50) -> Callable:
    """
    Return a wider HelpFormatter, if possible.

    https://stackoverflow.com/a/57655311
    """
    try:
        kwargs = {"width": w, "max_help_position": h}
        formatter(None, **kwargs)  # type: ignore
        return lambda prog: formatter(prog, **kwargs)
    except TypeError:
        logger.warning("argparse help formatter failed, falling back.")
        return formatter


class RunCmdResult(object):
    def __init__(self, returnCode: int, output: bytes, error: bytes) -> None:
        self.rc: int = returnCode
        self.out: bytes = output
        self.err: bytes = error

    def successful(self) -> bool:
        return self.rc == 0

    def failed(self) -> bool:
        return self.rc != 0


def runCmd(cmdArray: List[str], timeout: int = 630) -> RunCmdResult:
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
            return RunCmdResult(127, b"TimeoutExpired", str(e).encode())


def logMethodCall(func: Callable) -> Callable:
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        logger.debug(f">>> BaseApp.{func.__name__}")
        result = func(self, *args, **kwargs)
        logger.debug(f"<<< BaseApp.{func.__name__}")
        return result

    return wrapper


class BaseApp(PrintMixin, PromptMixin):
    def __init__(self) -> None:
        # Set up a log formatter with module name and line number
        chFormatter = logging.Formatter("%(asctime)s | %(name)-45s [%(lineno)-3d] | %(levelname)-8s %(message)s")

        # Set up a log handler (5mb rotating log file)
        ch = logging.handlers.RotatingFileHandler("mas.log", maxBytes=(1048576 * 5), backupCount=2)
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(chFormatter)

        # Configure the root logger
        rootLogger = logging.getLogger()
        rootLogger.addHandler(ch)
        rootLogger.setLevel(logging.INFO)

        # Set MAS CLI loggers to DEBUG for detailed logging
        logging.getLogger("mas").setLevel(logging.DEBUG)

        # Keep third-party libraries at INFO to avoid verbose HTTP logs
        logging.getLogger("asyncio").setLevel(logging.INFO)
        logging.getLogger("kubernetes").setLevel(logging.INFO)
        logging.getLogger("urllib3").setLevel(logging.INFO)

        # Supports extended semver, unlike mas.cli.__version__
        self.version: str = "100.0.0-pre.local"
        self.h1count: int = 0
        self.h2count: int = 0

        self.localConfigDir: str | None = None
        self.cliRootDir: str = path.join(path.abspath(path.dirname(__file__)), "..", "..", "..", "..")
        self.templatesDir: str = path.join(path.abspath(path.dirname(__file__)), "templates")
        self.installRBACDir: str = path.join(self.cliRootDir, "rbac", "install")
        if not path.isfile(path.join(self.installRBACDir, "kustomization.yaml")):
            logger.error(f"Could not find install RBAC bundle at {self.installRBACDir}, this is required for the setup-rbac command")
            # Try alternative path for containerized environment
            alt_path = path.join(path.abspath(path.dirname(__file__)), "..", "..", "..", "..", "rbac", "install")
            if path.isfile(path.join(alt_path, "kustomization.yaml")):
                self.installRBACDir = alt_path
            else:
                self.installRBACDir = "/opt/app-root/src/rbac/install"
        self.tektonDefsWithoutDigestPath: str = path.join(self.templatesDir, "ibm-mas-tekton.yaml")
        self.tektonDefsWithDigestPath: str = path.join(self.templatesDir, "ibm-mas-tekton-with-digest.yaml")

        # Default to using the tekton definitions without image digests
        self.tektonDefsPath: str = self.tektonDefsWithoutDigestPath

        # Initialize the dictionary that will hold the parameters we pass to a PipelineRun
        self.params: Dict[str, str] = dict()

        # These dicts will hold the additional-configs, pod-templates, sls license file and manual certificates secrets
        self.additionalConfigsSecret: Dict[str, Any] | None = None
        self.podTemplatesSecret: Dict[str, Any] | None = None
        self.slsLicenseFileSecret: Dict[str, Any] | None = None
        self.certsSecret: Dict[str, Any] | None = None

        self._isSNO: bool | None = None
        self._isAirgap: bool | None = None
        self.useCliDigest: bool = False
        self.cliDigest: str | None = None

        # Until we connect to the cluster we don't know what architecture it's worker nodes are
        self.architecture: str | None = None

        self.compatibilityMatrix: Dict[str, Dict[str, List[str]]] = {
            "9.2.x": {
                "manage": ["9.2.x", "9.2.x-feature", "9.1.x"],
                "optimizer": ["9.2.x", "9.2.x-feature", "9.1.x"],
                "visualinspection": ["9.2.x", "9.2.x-feature", "9.1.x"],
                "iot": ["9.2.x", "9.2.x-feature", "9.1.x"],
                "monitor": ["9.2.x", "9.2.x-feature", "9.1.x"],
                "predict": ["9.2.x", "9.2.x-feature", "9.1.x"],
                "facilities": ["9.2.x", "9.2.x-feature", "9.1.x"],
            },
            "9.2.x-feature": {
                "manage": ["9.2.x-feature", "9.1.x"],
                "optimizer": ["9.2.x-feature", "9.1.x"],
                "visualinspection": ["9.2.x-feature", "9.1.x"],
                "iot": ["9.2.x-feature", "9.1.x"],
                "monitor": ["9.2.x-feature", "9.1.x"],
                "predict": ["9.2.x-feature", "9.1.x"],
                "facilities": ["9.2.x-feature", "9.1.x"],
            },
            "9.1.x": {
                "facilities": ["9.1.x"],
                "assist": ["9.1.x", "9.0.x"],
                "iot": ["9.1.x", "9.0.x"],
                "manage": ["9.1.x", "9.1.x-feature", "9.0.x"],
                "monitor": ["9.1.x", "9.0.x"],
                "optimizer": ["9.1.x", "9.1.x-feature", "9.0.x"],
                "predict": ["9.1.x", "9.0.x"],
                "visualinspection": ["9.1.x", "9.1.x-feature", "9.0.x"],
            },
            "9.1.x-feature": {
                "assist": ["9.0.x"],
                "iot": ["9.0.x"],
                "manage": ["9.1.x-feature", "9.0.x"],
                "monitor": ["9.0.x"],
                "optimizer": ["9.1.x-feature", "9.0.x"],
                "predict": ["9.0.x"],
                "visualinspection": ["9.1.x-feature", "9.0.x"],
            },
            "9.0.x": {
                "assist": ["9.0.x", "8.8.x"],
                "iot": ["9.0.x", "8.8.x"],
                "manage": ["9.0.x", "8.7.x"],
                "monitor": ["9.0.x", "8.11.x"],
                "optimizer": ["9.0.x", "8.5.x"],
                "predict": ["9.0.x", "8.9.x"],
                "visualinspection": ["9.0.x", "8.9.x"],
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

        self.licenses: Dict[str, str] = {
            "8.9.x": " - <u>https://ibm.biz/MAS89-License</u>",
            "8.10.x": " - <u>https://ibm.biz/MAS810-License</u>",
            "8.11.x": " - <u>https://ibm.biz/MAS811-License</u>\n - <u>https://ibm.biz/MAXIT81-License</u>",
            "9.0.x": " - <u>https://ibm.biz/MAS90-License</u>\n - <u>https://ibm.biz/MaximoIT90-License</u>\n - <u>https://ibm.biz/MAXArcGIS90-License</u>",
            "9.1.x-feature": " - <u>https://ibm.biz/MAS90-License</u>\n - <u>https://ibm.biz/MaximoIT90-License</u>\n - <u>https://ibm.biz/MAXArcGIS90-License</u>\n\nBe aware, this channel subscription is supported for non-production use only.   \nIt allows early access to new features for evaluation in non-production environments.   \nThis subscription is offered alongside and in parallel with our normal maintained streams.   \nWhen using this subscription, IBM Support will only accept cases for the latest available bundle deployed in a non-production environment.   \nSeverity must be either 3 or 4 and cases cannot be escalated.   \nPlease refer to IBM documentation for more details.\n",
            "9.1.x": " - <u>https://ibm.biz/MAS91-License</u>\n - <u>https://ibm.biz/MAXIT91-License</u>\n - <u>https://ibm.biz/MAXESRI91-License</u>",
            "aibroker-9.1.x": " - <u>https://ibm.biz/MAS91-License</u>",
            "9.2.x-feature": " - <u>https://ibm.biz/MAS91-License</u>\n - <u>https://ibm.biz/MAXIT91-License</u>\n - <u>https://ibm.biz/MAXESRI91-License</u>\n\nBe aware, this channel subscription is supported for non-production use only.   \nIt allows early access to new features for evaluation in non-production environments.   \nThis subscription is offered alongside and in parallel with our normal maintained streams.   \nWhen using this subscription, IBM Support will only accept cases for the latest available bundle deployed in a non-production environment.   \nSeverity must be either 3 or 4 and cases cannot be escalated.   \nPlease refer to IBM documentation for more details.\n",
            "9.2.x": " - <u>https://ibm.biz/MAS92-License</u>\n - <u>https://ibm.biz/MAXIT92-License</u>\n - <u>https://ibm.biz/MAXESRI92-License</u>\n\nBe aware, this channel subscription is supported for non-production use only.   \nIt allows early access to new features for evaluation in non-production environments.   \nThis subscription is offered alongside and in parallel with our normal maintained streams.   \nWhen using this subscription, IBM Support will only accept cases for the latest available bundle deployed in a non-production environment.   \nSeverity must be either 3 or 4 and cases cannot be escalated.   \nPlease refer to IBM documentation for more details.\n",
        }

        self.upgrade_path: Dict[str, str] = {
            "9.2.x-feature": "9.2.x",
            "9.1.x": "9.2.x",
            "9.1.x-feature": "9.1.x",
            "9.0.x": "9.1.x",
            "8.11.x": "9.0.x",
            "8.10.x": "8.11.x",
            "8.9.x": "8.10.x",
        }

        self.spinner: Dict[str, Any] = {"interval": 80, "frames": [" ⠋", " ⠙", " ⠹", " ⠸", " ⠼", " ⠴", " ⠦", " ⠧", " ⠇", " ⠏"]}
        self.successIcon: str = "✅️"
        self.failureIcon: str = "❌"

        self._dynClient: DynamicClient | None = None
        self._apiClient: ApiClient | None = None

        self.printTitle(f"\nIBM Maximo Application Suite Admin CLI v{self.version}")
        print_formatted_text(
            HTML("Powered by <Orange><u>https://github.com/ibm-mas/ansible-devops/</u></Orange> and <Orange><u>https://tekton.dev/</u></Orange>\n")
        )
        if which("kubectl") is None:
            self.fatalError(
                "Could not find kubectl on the path, see <Orange><u>https://kubernetes.io/docs/tasks/tools/#kubectl</u></Orange> for installation instructions"
            )

    @logMethodCall
    def createTektonFileWithDigest(self) -> None:
        if path.exists(self.tektonDefsWithDigestPath):
            logger.debug(f"We have already generated {self.tektonDefsWithDigestPath}")
            self.tektonDefsPath = self.tektonDefsWithDigestPath
        elif isAirgapInstall(self.dynamicClient) or self.useCliDigest:
            # We need to modify the tekton definitions to use image digest
            imageWithoutDigest = f"quay.io/ibmmas/cli:{self.version}"

            if self.useCliDigest:
                self.printH1("CLI Digest Preparation")
                self.printDescription(
                    [f"Converting Tekton pipeline definitions to use {imageWithoutDigest} image digest instead of tag to avoid registry QPS issues"]
                )

                # Check if user provided a specific digest
                if self.cliDigest:
                    logger.info(f"Using user-provided CLI image digest: {self.cliDigest}")
                    cliImageDigest = self.cliDigest
                else:
                    logger.info(f"--use-cli-digest flag is set, will lookup digest for {imageWithoutDigest}")
                    # Auto-lookup the digest
                    cmdArray = ["skopeo", "inspect", f"docker://{imageWithoutDigest}"]
                    logger.info(f"Skopeo inspect command: {' '.join(cmdArray)}")
                    skopeoResult = runCmd(cmdArray)
                    if skopeoResult.successful():
                        skopeoData = json.loads(skopeoResult.out)
                        logger.debug(f"Skopeo Data for {imageWithoutDigest}: {skopeoData}")
                        if "Digest" not in skopeoData:
                            self.fatalError("Recieved bad data inspecting CLI manifest to determine digest")
                        cliImageDigest = skopeoData["Digest"]
                        logger.info(f"Successfully retrieved CLI image digest: {cliImageDigest}")
                    else:
                        warning = f"Unable to retrieve image digest for {imageWithoutDigest} ({skopeoResult.rc})"
                        self.printWarning(warning)
                        logger.warning(warning)
                        logger.warning(skopeoResult.err)
                        if self.noConfirm:
                            self.fatalError("Unable to automatically determine CLI image digest and --no-confirm flag has been set")
                        else:
                            cliImageDigest = self.promptForString(f"Enter {imageWithoutDigest} image digest")
                            logger.info(f"User provided CLI image digest: {cliImageDigest}")
            else:
                # Airgap install
                self.printH1("Disconnected OpenShift Preparation")
                self.printDescription(
                    [
                        f"Unless the {imageWithoutDigest} image is accessible from your cluster the MAS CLI container image must be present in your mirror registry"
                    ]
                )
                logger.info(f"Airgap install detected, will lookup digest for {imageWithoutDigest}")

                cmdArray = ["skopeo", "inspect", f"docker://{imageWithoutDigest}"]
                logger.info(f"Skopeo inspect command: {' '.join(cmdArray)}")
                skopeoResult = runCmd(cmdArray)
                if skopeoResult.successful():
                    skopeoData = json.loads(skopeoResult.out)
                    logger.debug(f"Skopeo Data for {imageWithoutDigest}: {skopeoData}")
                    if "Digest" not in skopeoData:
                        self.fatalError("Recieved bad data inspecting CLI manifest to determine digest")
                    cliImageDigest = skopeoData["Digest"]
                    logger.info(f"Successfully retrieved CLI image digest: {cliImageDigest}")
                else:
                    warning = f"Unable to retrieve image digest for {imageWithoutDigest} ({skopeoResult.rc})"
                    self.printWarning(warning)
                    logger.warning(warning)
                    logger.warning(skopeoResult.err)
                    if self.noConfirm:
                        self.fatalError("Unable to automatically determine CLI image digest and --no-confirm flag has been set")
                    else:
                        cliImageDigest = self.promptForString(f"Enter {imageWithoutDigest} image digest")
                        logger.info(f"User provided CLI image digest: {cliImageDigest}")

            # Overwrite the tekton definitions with one that uses the looked up image digest
            imageWithDigest = f"quay.io/ibmmas/cli@{cliImageDigest}"
            self.printHighlight(f"\nConverting Tekton definitions to use {imageWithDigest}")
            logger.info(f"Converting from tag-based image ({imageWithoutDigest}) to digest-based image ({imageWithDigest})")

            with open(self.tektonDefsPath, "r") as file:
                tektonDefsWithoutDigest = file.read()

            tektonDefsWithDigest = tektonDefsWithoutDigest.replace(imageWithoutDigest, imageWithDigest)

            logger.info(f"Writing Tekton definitions with digest to {self.tektonDefsWithDigestPath}")
            with open(self.tektonDefsWithDigestPath, "w") as file:
                file.write(tektonDefsWithDigest)

            self.tektonDefsPath = self.tektonDefsWithDigestPath
            logger.info("Successfully created Tekton definitions with CLI digest")

    @logMethodCall
    def getCompatibleVersions(self, coreChannel: str, appId: str) -> List[str]:
        if coreChannel in self.compatibilityMatrix:
            return self.compatibilityMatrix[coreChannel][appId]
        else:
            return []

    @logMethodCall
    def fatalError(self, message: str, exception: Exception | None = None) -> NoReturn:
        if exception is not None:
            logger.error(message)
            logger.exception(exception, stack_info=True)
            print_formatted_text(HTML(f"<Red>Fatal Exception: {message.replace(' & ', ' &amp; ')}: {exception}</Red>\n"))
        else:
            logger.error(message)
            print_formatted_text(HTML(f"<Red>Fatal Error: {message.replace(' & ', ' &amp; ')}</Red>\n"))
        exit(1)

    @logMethodCall
    def isSNO(self) -> bool:
        if self._isSNO is None:
            self._isSNO = isSNO(self.dynamicClient)
        return self._isSNO

    @logMethodCall
    def isAirgap(self) -> bool:
        if self._isAirgap is None:
            # First check if the legacy ICSP is installed.  If it is raise an error and instruct the user to re-run configure-airgap to
            # migrate the cluster from ICSP to IDMS
            if isAirgapInstall(self.dynamicClient, checkICSP=True):
                self.fatalError(
                    "Deprecated Maximo Application Suite ImageContentSourcePolicy detected on the target cluster.  Run 'mas configure-airgap' to migrate to the replacement ImageDigestMirrorSet beofre proceeding."
                )
            self._isAirgap = isAirgapInstall(self.dynamicClient)
        return self._isAirgap

    def setParam(self, param: str, value: str) -> None:
        self.params[param] = value

    def getParam(self, param: str) -> str:
        """
        Returns the value of a parameter, or an empty string is the parameter has not set at all or is set to None
        """
        if param in self.params and self.params[param] is not None:
            return self.params[param]
        else:
            return ""

    @property
    def dynamicClient(self) -> DynamicClient:
        if self._dynClient is not None:
            return self._dynClient
        else:
            return self.reloadDynamicClient()

    @logMethodCall
    def reloadDynamicClient(self) -> DynamicClient | None:
        """
        Configure the Kubernetes API Client using the active context in kubeconfig
        """
        logger.debug("Reloading Kubernetes Client Configuration")
        try:
            if "KUBERNETES_SERVICE_HOST" in environ:
                config.load_incluster_config()
                k8s_config = Configuration.get_default_copy()
                self._apiClient = ApiClient(configuration=k8s_config)
                self._dynClient = DynamicClient(self._apiClient)
            else:
                config.load_kube_config()
                self._apiClient = ApiClient()
                self._dynClient = DynamicClient(self._apiClient)
            return self._dynClient
        except Exception as e:
            logger.warning(f"Error: Unable to connect to OpenShift Container Platform: {e}")
            logger.exception(e, stack_info=True)
            return None

    def getReconciledVersion(self, instance: Dict[str, Any]) -> str:
        """
        Get the reconciled version from an instance's status.

        Checks if the instance is in a healthy state by verifying the presence of a reconciled version.
        If the instance is unhealthy (missing reconciled version), triggers a fatal error with a clear message.

        Args:
            instance (dict): The instance resource dictionary containing metadata, kind, and status

        Returns:
            str: The reconciled version if the instance is healthy

        Raises:
            SystemExit: Via fatalError if the instance is unhealthy
        """
        instanceId = instance["metadata"]["name"]
        instanceKind = instance.get("kind", "Instance")
        reconciledVersion = instance.get("status", {}).get("versions", {}).get("reconciled")

        if not reconciledVersion:
            self.fatalError(
                f"{instanceKind} '{instanceId}' is in an unhealthy state (missing reconciled version). "
                f"We do not recommend (and thus do not support) continuing when there are unhealthy instances on the cluster. "
                f"Please resolve the instance health issues before attempting to proceed."
            )

        return reconciledVersion

    @logMethodCall
    def connect(self) -> None:
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
            server = prompt(HTML("<Yellow>Server URL:</Yellow> "), placeholder="https://...")
            token = prompt(HTML("<Yellow>Login Token:</Yellow> "), is_password=True, placeholder="sha256~...")
            skipVerify = self.yesOrNo("Disable TLS Verify")
            connect(server, token, skipVerify)
            self.reloadDynamicClient()
            if self._dynClient is None:
                print_formatted_text(HTML("<Red>Unable to connect to cluster.  See log file for details</Red>"))
                exit(1)

        # Now that we are connected, inspect the architecture of the OpenShift cluster
        self.lookupTargetArchitecture()

    @logMethodCall
    def lookupTargetArchitecture(self, architecture: str | None = None) -> None:
        logger.debug("Looking up worker node architecture")
        if architecture is not None:
            self.architecture = architecture
            logger.debug(f"Target architecture (overridden): {self.architecture}")
        elif self.dynamicClient is not None:
            nodes = getNodes(self.dynamicClient)
            self.architecture = nodes[0]["status"]["nodeInfo"]["architecture"]
            logger.debug(f"Target architecture: {self.architecture}")
        else:
            return

        if self.architecture not in ["amd64", "s390x", "ppc64le"]:
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
            "metadata": {"name": f"approval-{id}", "namespace": namespace},
            "data": {"MAX_RETRIES": str(maxRetries), "DELAY": str(delay), "IGNORE_FAILURE": str(ignoreFailure), "STATUS": ""},
        }

        # Delete any existing configmap and create a new one
        try:
            logger.debug(f"Deleting any existing approval workflow configmap for {id}")
            cmAPI.delete(name=f"approval-{id}", namespace=namespace)
        except NotFoundError:
            pass

        if enabled:
            logger.debug(
                f"Enabling approval workflow for {id} with {maxRetries} max retries on a {delay}s delay ({'ignoring failures' if ignoreFailure else 'abort on failure'})"
            )
            cmAPI.create(body=configMap, namespace=namespace)

    @logMethodCall
    def selectLocalConfigDir(self) -> None:
        if self.localConfigDir is None:
            # You need to tell us where the configuration file can be found
            self.localConfigDir = self.promptForDir("Select Local configuration directory")

    @logMethodCall
    def validateEntitlementKey(self, entitlementKey: str, repository: str = "cp/mas/coreapi", timeout: int = 30) -> bool:
        """
        Validate IBM entitlement key using mas.devops.utils.validateIBMEntitlementKey.

        Args:
            entitlementKey: The entitlement key to validate
            repository: Docker repository to test against. Defaults to "cp/mas/coreapi".
            timeout: Timeout in seconds for validation. Defaults to 30.

        Returns:
            bool: True if valid, False if invalid
        """
        try:
            logger.info(f"Validating IBM entitlement key against repository: {repository}")
            isValid = validateIBMEntitlementKey(entitlementKey, repository, timeout)
            if isValid:
                logger.info("IBM entitlement key validation successful")
            else:
                logger.warning("IBM entitlement key validation failed")
            return isValid
        except Exception as e:
            logger.error(f"Error validating IBM entitlement key: {e}")
            logger.exception(e, stack_info=True)
            return False

    @logMethodCall
    def promptForEntitlementKey(self, message: str, param: str, repository: str = "cp/mas/coreapi", timeout: int = 30) -> str:
        """
        Prompt for IBM entitlement key with validation.

        In interactive mode:
        - Validates the key after user input
        - If invalid, offers: 1) Try again, 2) Continue anyway, 3) Quit
        - Loops until valid key or user chooses to continue/quit

        In non-interactive mode with --no-confirm:
        - Validates but only warns if invalid, does not block

        Args:
            message: Prompt message to display
            param: Parameter name to store the key
            repository: Docker repository to test against
            timeout: Timeout in seconds for validation

        Returns:
            str: The entitlement key (validated or user chose to continue anyway)
        """
        while True:
            # Prompt for the entitlement key
            entitlementKey = self.promptForString(message, param=None, isPassword=True)

            # Validate the key
            isValid = self.validateEntitlementKey(entitlementKey, repository, timeout)

            if isValid:
                # Key is valid, show success message and continue
                self.printHighlight("✓ IBM entitlement key validated successfully")
                self.setParam(param, entitlementKey)
                return entitlementKey

            # Key is invalid
            if self.noConfirm:
                # Non-interactive mode with --no-confirm: warn but continue
                self.printWarning("IBM entitlement key validation failed, but continuing due to --no-confirm flag")
                self.setParam(param, entitlementKey)
                return entitlementKey

            # Interactive mode or non-interactive without --no-confirm: offer options
            self.printWarning("IBM entitlement key validation failed")
            print()
            self.printDescription(
                [
                    "What would you like to do?",
                    "  1. Try again (re-enter the entitlement key)",
                    "  2. Continue anyway (skip validation)",
                    "  3. Quit (exit the application)",
                ]
            )

            choice = self.promptForInt("Select an option", min=1, max=3)

            if choice == 1:
                # Try again - loop will continue
                continue
            elif choice == 2:
                # Continue anyway
                logger.warning("User chose to continue with invalid entitlement key")
                self.setParam(param, entitlementKey)
                return entitlementKey
            else:  # choice == 3
                # Quit
                logger.info("User chose to quit due to invalid entitlement key")
                exit(1)
