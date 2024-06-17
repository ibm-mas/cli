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
import yaml

from datetime import datetime
from os import path
from time import sleep

from kubeconfig import kubectl
from kubeconfig.exceptions import KubectlCommandError
from openshift.dynamic import DynamicClient
from openshift.dynamic.exceptions import NotFoundError, UnprocessibleEntityError

from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateNotFound

from .ocp import getConsoleURL

logger = logging.getLogger(__name__)


def installOpenShiftPipelines(dynClient: DynamicClient) -> bool:
    """
    Install the OpenShift Pipelines Operator and wait for it to be ready to use
    """
    packagemanifestAPI = dynClient.resources.get(api_version="packages.operators.coreos.com/v1", kind="PackageManifest")
    subscriptionsAPI = dynClient.resources.get(api_version="operators.coreos.com/v1alpha1", kind="Subscription")
    crdAPI = dynClient.resources.get(api_version="apiextensions.k8s.io/v1", kind="CustomResourceDefinition")

    # Create the Operator Subscription
    try:
        manifest = packagemanifestAPI.get(name="openshift-pipelines-operator-rh", namespace="openshift-marketplace")
        defaultChannel = manifest.status.defaultChannel
        catalogSource = manifest.status.catalogSource
        catalogSourceNamespace = manifest.status.catalogSourceNamespace

        logger.info(f"OpenShift Pipelines Operator Details: {catalogSourceNamespace}/{catalogSource}@{defaultChannel}")

        templateDir = path.join(path.abspath(path.dirname(__file__)), "templates")
        env = Environment(
            loader=FileSystemLoader(searchpath=templateDir)
        )
        try:
            template = env.get_template("templates/subscription.yml.j2")
        except TemplateNotFound as e:
            logger.warning(f"Could not find subscription template in {templateDir}: {e}")
            return False
        renderedTemplate = template.render(
            pipelines_channel=defaultChannel,
            pipelines_source=catalogSource,
            pipelines_source_namespace=catalogSourceNamespace
        )
        subscription = yaml.safe_load(renderedTemplate)
        subscriptionsAPI.apply(body=subscription, namespace="openshift-operators")

    except NotFoundError as e:
        logger.warning("Error: Couldn't find package manifest for Red Hat Openshift Pipelines Operator")
    except UnprocessibleEntityError as e:
        logger.warning("Error: Couldn't create/update OpenShift Pipelines Operator Subscription")

    foundReadyCRD = False
    while not foundReadyCRD:
        try:
            tasksCRD = crdAPI.get(name="tasks.tekton.dev")
            conditions = tasksCRD.status.conditions
            for condition in conditions:
                if condition.type == "Established":
                    if condition.status == "True":
                        foundReadyCRD = True
                    else:
                        logger.debug("Waiting 5s for tasks.tekton.dev CRD to be ready before checking again ...")
                        sleep(5)
                        continue
        except NotFoundError as e:
            logger.debug("Waiting 5s for tasks.tekton.dev CRD to be installed before checking again ...")
            sleep(5)

    logger.info("OpenShift Pipelines Operator is installed and ready")
    return True


def updateTektonDefinitions(namespace: str) -> bool:
    """
    Install/update the MAS tekton pipeline and task definitions

    Unfortunately there's no API equivalent of what the kubectl CLI gives us with the ability to just apply a file containing a mix of
    """
    # https://github.com/gtaylor/kubeconfig-python/blob/master/kubeconfig/kubectl.py
    thisDir = path.abspath(path.dirname(__file__))
    try:
        result = kubectl.run(subcmd_args=['apply', '-n', namespace, '-f', path.join(thisDir, "templates", "ibm-mas-tekton.yaml")])
        for line in result.split("\n"):
            logger.debug(line)
        return True
    except KubectlCommandError as e:
        logger.warning(f"Error: Unable to install/update Tekton definitions: {e}")
        return False


def launchUpgradePipeline(dynClient: DynamicClient,
                          instanceId: str,
                          masChannel: str="") -> str:
    """
    Create a PipelineRun to upgrade the chosen MAS instance
    """
    pipelineRunsAPI = dynClient.resources.get(api_version="tekton.dev/v1beta1", kind="PipelineRun")
    namespace = f"mas-{instanceId}-pipelines"
    timestamp = datetime.now().strftime("%y%m%d-%H%M")
    # Create the PipelineRun
    try:
        templateDir = path.join(path.abspath(path.dirname(__file__)), "templates")
        env = Environment(
            loader=FileSystemLoader(searchpath=templateDir)
        )
        try:
            template = env.get_template("pipelinerun-upgrade.yml.j2")
        except TemplateNotFound as e:
            logger.warning(f"Could not find pipelinerun template in {templateDir}: {e}")
            return None
        renderedTemplate = template.render(
            timestamp = timestamp,
            mas_instance_id = instanceId,
            mas_channel = masChannel
        )
        pipelineRun = yaml.safe_load(renderedTemplate)
        pipelineRunsAPI.apply(body=pipelineRun, namespace=namespace)

    except Exception as e:
        logger.warning(f"Error: An unexpected error occured: {e}")
        logger.debug(renderedTemplate)
        return None

    pipelineURL = f"{getConsoleURL(dynClient)}/k8s/ns/mas-{instanceId}-pipelines/tekton.dev~v1beta1~PipelineRun/{instanceId}-upgrade-{timestamp}"
    return pipelineURL

def launchUninstallPipeline(dynClient: DynamicClient,
                            instanceId: str,
                            certManagerProvider: str="redhat",
                            uninstallCertManager: bool=False,
                            uninstallGrafana: bool=False,
                            uninstallCatalog: bool=False,
                            uninstallCommonServices: bool=False,
                            uninstallUDS: bool=False,
                            uninstallMongoDb: bool=False,
                            uninstallSLS: bool=False) -> str:
    """
    Create a PipelineRun to uninstall the chosen MAS instance (and selected dependencies)
    """
    pipelineRunsAPI = dynClient.resources.get(api_version="tekton.dev/v1beta1", kind="PipelineRun")
    namespace = f"mas-{instanceId}-pipelines"
    timestamp = datetime.now().strftime("%y%m%d-%H%M")
    # Create the PipelineRun
    try:
        templateDir = path.join(path.abspath(path.dirname(__file__)), "templates")
        env = Environment(
            loader=FileSystemLoader(searchpath=templateDir)
        )
        try:
            template = env.get_template("pipelinerun-uninstall.yml.j2")
        except TemplateNotFound as e:
            logger.warning(f"Could not find pipelinerun template in {templateDir}: {e}")
            return None

        grafanaAction = "uninstall" if uninstallGrafana else "none"
        certManagerAction = "uninstall" if uninstallCertManager else "none"
        commonServicesAction = "uninstall" if uninstallCommonServices else "none"
        ibmCatalogAction = "uninstall" if uninstallCatalog else "none"
        mongoDbAction = "uninstall" if uninstallMongoDb else "none"
        slsAction = "uninstall" if uninstallSLS else "none"
        udsAction = "uninstall" if uninstallUDS else "none"

        # Render the pipelineRun
        renderedTemplate = template.render(
            timestamp = timestamp,
            mas_instance_id = instanceId,
            grafana_action = grafanaAction,
            cert_manager_provider = certManagerProvider,
            cert_manager_action = certManagerAction,
            common_services_action = commonServicesAction,
            ibm_catalogs_action = ibmCatalogAction,
            mongodb_action = mongoDbAction,
            sls_action = slsAction,
            uds_action = udsAction
        )
        pipelineRun = yaml.safe_load(renderedTemplate)
        pipelineRunsAPI.apply(body=pipelineRun, namespace=namespace)

    except Exception as e:
        logger.warning(f"Error: An unexpected error occured: {e}")
        logger.debug(renderedTemplate)
        return None

    pipelineURL = f"{getConsoleURL(dynClient)}/k8s/ns/mas-{instanceId}-pipelines/tekton.dev~v1beta1~PipelineRun/{instanceId}-uninstall-{timestamp}"
    return pipelineURL
