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
from typing import TYPE_CHECKING
from halo import Halo
from prompt_toolkit import print_formatted_text, HTML

if TYPE_CHECKING:
    from .app import GitOpsInstallApp

from .functions.gitops_cluster import gitops_cluster
from .functions.gitops_instance import gitops_instance
from .functions.gitops_apps import gitops_apps

from mas.devops.ocp import createNamespace
from mas.devops.tekton import (
    installOpenShiftPipelines,
    updateTektonDefinitions,
    preparePipelinesNamespace,
    prepareGitOpsInstallSecrets,
    launchGitOpsDeps,
    launchGitOpsClusterPipeline,
    launchGitOpsInstancePipeline,
    launchGitOpsAppsPipeline,
    getConsoleURL
)


logger = logging.getLogger(__name__)


class GitOpsInstallExecutor():
    """
    Executor class for performing GitOps installation operations.

    This class handles the actual execution of the GitOps installation process
    by routing to either Tekton pipeline execution or direct mode execution.
    """

    def __init__(self, app: 'GitOpsInstallApp'):
        """
        Initialize the GitOps install executor.

        Args:
            app: Reference to the GitOpsInstallApp instance containing all configuration
        """
        self.app = app
        logger.debug("GitOpsInstallExecutor initialized")

    def execute(self) -> bool:
        """
        Main entry point that routes to tekton or direct mode based on app.executionMode.

        Returns:
            bool: True if installation completed successfully, False otherwise
        """
        logger.info(f"Executing GitOps installation in {self.app.executionMode} mode")

        if self.app.executionMode == "tekton":
            return self.executeTektonMode()
        else:
            return self.executeDirectMode()

    def executeTektonMode(self) -> bool:
        """
        Launch four sequential PipelineRuns for GitOps installation.

        This method will:
        0. Install OpenShift Pipelines operator and prepare namespace
        1. Launch gitops-deps PipelineRun (optional, for off-cluster dependencies)
        2. Launch gitops-cluster PipelineRun
        3. Launch gitops-instance PipelineRun (waits for cluster)
        4. Launch gitops-apps PipelineRun (waits for instance)

        Returns:
            bool: True if all PipelineRuns were successfully launched
        """
        logger.info("Launching Tekton PipelineRuns for GitOps installation")

        try:
            # Get instance ID to create instance-specific namespace
            instanceId = self.app.getParam('mas_instance_id')
            if not instanceId:
                logger.error("Instance ID is required for Tekton mode execution")
                return False

            pipelinesNamespace = f"mas-{instanceId}-pipelines"

            # Determine storage class and access mode for pipeline PVC
            # Prefer ReadWriteMany (RWX), but fall back to ReadWriteOnce (RWO) if necessary
            storageClassRWX = self.app.getParam('storage_class_rwx')
            storageClassRWO = self.app.getParam('storage_class_rwo')

            if storageClassRWX and storageClassRWX != "none":
                pipelineStorageClass = storageClassRWX
                pipelineStorageAccessMode = "ReadWriteMany"
            else:
                pipelineStorageClass = storageClassRWO
                pipelineStorageAccessMode = "ReadWriteOnce"

            # Configure RBAC unless a custom service account is specified
            # GitOps install typically doesn't use custom service accounts, so default to True
            serviceAccountName = self.app.getParam('service_account_name')
            configureRBAC = (serviceAccountName is None or serviceAccountName == "")

            # Step 0: Install OpenShift Pipelines operator and prepare namespace
            with Halo(text='Validating OpenShift Pipelines installation', spinner=self.app.spinner) as h:
                if installOpenShiftPipelines(self.app.dynamicClient):
                    h.stop_and_persist(symbol=self.app.successIcon, text="OpenShift Pipelines Operator is installed and ready to use")
                else:
                    h.stop_and_persist(symbol=self.app.failureIcon, text="OpenShift Pipelines Operator installation failed")
                    return False

            with Halo(text=f'Preparing namespace ({pipelinesNamespace})', spinner=self.app.spinner) as h:
                createNamespace(self.app.dynamicClient, pipelinesNamespace)
                preparePipelinesNamespace(
                    dynClient=self.app.dynamicClient,
                    instanceId=instanceId,  # Use instance-specific namespace
                    storageClass=pipelineStorageClass,
                    accessMode=pipelineStorageAccessMode,
                    configureRBAC=configureRBAC
                )
                h.stop_and_persist(symbol=self.app.successIcon, text=f"Namespace is ready ({pipelinesNamespace})")

            with Halo(text=f'Installing latest Tekton definitions (v{self.app.version})', spinner=self.app.spinner) as h:
                updateTektonDefinitions(pipelinesNamespace, self.app.tektonDefsPath)
                h.stop_and_persist(symbol=self.app.successIcon, text=f"Latest Tekton definitions are installed (v{self.app.version})")

            with Halo(text='Preparing GitOps installation secrets', spinner=self.app.spinner) as h:
                # Prepare secure properties (passwords, tokens, access keys)
                secure_properties = self.app.prepareSecureProperties()

                # Prepare GitOps configuration files (instance-level)
                gitops_configs = self.app.prepareGitOpsConfigFiles()

                # Prepare app-specific configuration files
                app_configs = self.app.prepareAppSpecificConfigFiles()

                # Merge app-specific configs into gitops_configs
                if app_configs:
                    gitops_configs.update(app_configs)

                # Prepare additional configuration files
                additional_configs = self.app.prepareAdditionalConfigFiles()

                # Prepare SLS entitlement file
                sls_entitlement = self.app.prepareSLSEntitlementFile()

                # Build secret dictionaries with proper structure
                gitops_configs_secret = None
                if gitops_configs:
                    gitops_configs_secret = {
                        "apiVersion": "v1",
                        "kind": "Secret",
                        "type": "Opaque",
                        "metadata": {
                            "name": "pipeline-gitops-configs"
                        },
                        "data": gitops_configs
                    }

                additional_configs_secret = None
                if additional_configs:
                    additional_configs_secret = {
                        "apiVersion": "v1",
                        "kind": "Secret",
                        "type": "Opaque",
                        "metadata": {
                            "name": "pipeline-additional-configs"
                        },
                        "data": additional_configs
                    }

                sls_entitlement_secret = None
                if sls_entitlement:
                    sls_entitlement_secret = {
                        "apiVersion": "v1",
                        "kind": "Secret",
                        "type": "Opaque",
                        "metadata": {
                            "name": "pipeline-sls-entitlement"
                        },
                        "data": sls_entitlement
                    }

                prepareGitOpsInstallSecrets(
                    dynClient=self.app.dynamicClient,
                    namespace=pipelinesNamespace,
                    gitopsConfigs=gitops_configs_secret,
                    additionalConfigs=additional_configs_secret,
                    slsLicenseFile=sls_entitlement_secret,
                    secureProperties=secure_properties
                )
                h.stop_and_persist(symbol=self.app.successIcon, text="GitOps installation secrets are ready")

            # Check if we need to launch deps pipeline
            # Dependencies pipeline is optional and only runs if mongodb_action, kafka_action, cos_action, or efs_action is set
            deps_params = self.app.prepareDepsParams()
            deps_pipelinerun_name = None

            # Check if any dependency action is configured
            has_deps = (
                deps_params.get('mongodb_action') or
                deps_params.get('kafka_action') or
                deps_params.get('cos_action') or
                deps_params.get('efs_action')
            )

            if has_deps:
                # Launch deps PipelineRun
                with Halo(text='Submitting PipelineRun for gitops-deps', spinner=self.app.spinner) as h:
                    deps_pipelinerun_name = launchGitOpsDeps(
                        dynClient=self.app.dynamicClient,
                        params=deps_params,
                        instanceId=instanceId
                    )

                    if deps_pipelinerun_name is not None:
                        h.stop_and_persist(symbol=self.app.successIcon, text="PipelineRun for gitops-deps submitted")
                        # Construct console URL for the PipelineRun
                        console_url = getConsoleURL(self.app.dynamicClient)
                        deps_pipeline_url = f"{console_url}/k8s/ns/{pipelinesNamespace}/tekton.dev~v1beta1~PipelineRun/{deps_pipelinerun_name}"
                        print_formatted_text(HTML(f"\nView progress:\n  <Cyan><u>{deps_pipeline_url}</u></Cyan>\n"))
                    else:
                        h.stop_and_persist(symbol=self.app.failureIcon, text="Failed to submit PipelineRun for gitops-deps, see log file for details")
                        print()
                        return False

            # Prepare parameters for cluster pipeline
            cluster_params = self.app.prepareClusterParams()

            # Launch cluster PipelineRun (optionally wait for deps if it was launched)
            with Halo(text='Submitting PipelineRun for gitops-cluster', spinner=self.app.spinner) as h:
                # If deps pipeline was launched, pass it to cluster pipeline to wait for completion
                cluster_pipelinerun_name = launchGitOpsClusterPipeline(
                    dynClient=self.app.dynamicClient,
                    params=cluster_params,
                    instanceId=instanceId,
                    deps_pipelinerun_name=deps_pipelinerun_name
                )

                if cluster_pipelinerun_name is not None:
                    h.stop_and_persist(symbol=self.app.successIcon, text="PipelineRun for gitops-cluster submitted")
                    # Construct console URL for the PipelineRun
                    console_url = getConsoleURL(self.app.dynamicClient)
                    cluster_pipeline_url = f"{console_url}/k8s/ns/{pipelinesNamespace}/tekton.dev~v1beta1~PipelineRun/{cluster_pipelinerun_name}"
                    print_formatted_text(HTML(f"\nView progress:\n  <Cyan><u>{cluster_pipeline_url}</u></Cyan>\n"))
                else:
                    h.stop_and_persist(symbol=self.app.failureIcon, text="Failed to submit PipelineRun for gitops-cluster, see log file for details")
                    print()
                    return False

            # Prepare parameters for instance pipeline
            instance_params = self.app.prepareInstanceParams()
            # Merge cluster_params into instance_params
            instance_params.update(cluster_params)

            # Launch instance PipelineRun (with wait for cluster)
            with Halo(text='Submitting PipelineRun for gitops-instance', spinner=self.app.spinner) as h:
                instance_pipelinerun_name = launchGitOpsInstancePipeline(
                    dynClient=self.app.dynamicClient,
                    params=instance_params,
                    cluster_pipelinerun_name=cluster_pipelinerun_name
                )

                if instance_pipelinerun_name is not None:
                    h.stop_and_persist(symbol=self.app.successIcon, text="PipelineRun for gitops-instance submitted")
                    # Construct console URL for the PipelineRun
                    instance_pipeline_url = f"{console_url}/k8s/ns/{pipelinesNamespace}/tekton.dev~v1beta1~PipelineRun/{instance_pipelinerun_name}"
                    print_formatted_text(HTML(f"\nView progress:\n  <Cyan><u>{instance_pipeline_url}</u></Cyan>\n"))
                else:
                    h.stop_and_persist(symbol=self.app.failureIcon, text="Failed to submit PipelineRun for gitops-instance, see log file for details")
                    print()
                    return False

            # Prepare parameters for apps pipeline
            apps_params = self.app.prepareAppsParams()
            # Merge cluster_params and instance_params into apps_params
            apps_params.update(cluster_params)
            apps_params.update(instance_params)

            # Launch apps PipelineRun (with wait for instance)
            with Halo(text='Submitting PipelineRun for gitops-apps', spinner=self.app.spinner) as h:
                apps_pipelinerun_name = launchGitOpsAppsPipeline(
                    dynClient=self.app.dynamicClient,
                    params=apps_params,
                    instance_pipelinerun_name=instance_pipelinerun_name
                )

                if apps_pipelinerun_name is not None:
                    h.stop_and_persist(symbol=self.app.successIcon, text="PipelineRun for gitops-apps submitted")
                    # Construct console URL for the PipelineRun
                    apps_pipeline_url = f"{console_url}/k8s/ns/{pipelinesNamespace}/tekton.dev~v1beta1~PipelineRun/{apps_pipelinerun_name}"
                    print_formatted_text(HTML(f"\nView progress:\n  <Cyan><u>{apps_pipeline_url}</u></Cyan>\n"))
                else:
                    h.stop_and_persist(symbol=self.app.failureIcon, text="Failed to submit PipelineRun for gitops-apps, see log file for details")
                    print()
                    return False

            logger.info("All GitOps PipelineRuns launched successfully")
            return True

        except Exception as e:
            logger.error(f"Error launching Tekton PipelineRuns: {e}")
            return False

    def executeDirectMode(self) -> bool:
        """
        Execute installation in direct mode by calling three functions sequentially.

        This method will:
        1. Call gitops_cluster() to configure cluster resources
        2. Call gitops_instance() to configure MAS instance
        3. Call gitops_apps() to configure MAS applications

        Returns:
            bool: True if all functions completed successfully
        """
        logger.info("Executing GitOps installation in direct mode")

        try:
            # Prepare parameters for cluster function (will be implemented in Phase 4)
            cluster_params = self.app.prepareClusterParams()

            # Execute cluster configuration
            logger.info("Executing gitops_cluster()")
            cluster_result = gitops_cluster(cluster_params)

            if not cluster_result:
                logger.error("gitops_cluster() failed")
                return False

            logger.info("gitops_cluster() completed successfully")

            # Prepare parameters for instance function (will be implemented in Phase 4)
            instance_params = self.app.prepareInstanceParams()

            # Execute instance configuration
            logger.info("Executing gitops_instance()")
            instance_result = gitops_instance(instance_params)

            if not instance_result:
                logger.error("gitops_instance() failed")
                return False

            logger.info("gitops_instance() completed successfully")

            # Prepare parameters for apps function (will be implemented in Phase 4)
            apps_params = self.app.prepareAppsParams()

            # Execute apps configuration
            logger.info("Executing gitops_apps()")
            apps_result = gitops_apps(apps_params)

            if not apps_result:
                logger.error("gitops_apps() failed")
                return False

            logger.info("gitops_apps() completed successfully")

            logger.info("All GitOps direct mode functions completed successfully")
            return True

        except Exception as e:
            logger.error(f"Error executing direct mode: {e}")
            return False
