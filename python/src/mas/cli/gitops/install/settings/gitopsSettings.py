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
import re
from typing import List

logger = logging.getLogger(__name__)


class GitOpsInstallGitOpsSettingsMixin():
    """
    Mixin class for managing GitOps repository and ArgoCD settings.

    This class provides methods for configuring:
    - GitOps repository connection (URL, branch, credentials)
    - ArgoCD installation and configuration
    - Account and cluster identification
    - Repository structure and organization
    """

    # Type stubs for methods provided by BaseApp (available at runtime through multiple inheritance)
    def printH2(self, message: str) -> None:
        ...  # type: ignore

    def printDescription(self, content: List[str]) -> None:
        ...  # type: ignore

    def getParam(self, param: str) -> str:
        ...  # type: ignore

    def setParam(self, param: str, value: str) -> None:
        ...  # type: ignore

    def promptForString(self, message: str, param: str = None, default: str = "", isPassword: bool = False) -> str:
        ...  # type: ignore

    dynamicClient: any  # type: ignore
    noConfirm: bool  # type: ignore

    def configGitOpsRepository(self) -> None:
        """
        Configure GitOps repository settings.

        Collects:
        - github_host: GitHub host (e.g., github.com)
        - github_org: GitHub organization
        - github_repo: Repository name
        - git_branch: Branch to use (default: main)
        - gitops_repo_token_secret: GitHub repository token for authentication
        """
        logger.debug("Configuring GitOps repository")

        self.printH2("GitOps Repository")
        self.printDescription([
            "Configure the Git repository where GitOps configuration will be stored.",
            "This repository will contain all ArgoCD Application definitions and configuration files."
        ])

        # Check if values are already set (non-interactive mode)
        if not self.getParam("github_host"):
            self.promptForString("GitHub host", "github_host", default="github.com")

        if not self.getParam("github_org"):
            self.promptForString("GitHub organization", "github_org")

        if not self.getParam("github_repo"):
            self.promptForString("GitHub repository name", "github_repo")

        if not self.getParam("git_branch"):
            self.promptForString("Git branch", "git_branch", default="main")

        if not self.getParam("gitops_repo_token_secret"):
            self.promptForString("GitHub repository token secret", "gitops_repo_token_secret", isPassword=True)

        # Validate GitHub parameters
        github_host = self.getParam("github_host")
        github_org = self.getParam("github_org")
        github_repo = self.getParam("github_repo")
        git_branch = self.getParam("git_branch")

        # Validate github_host: basic hostname format
        if github_host and not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$', github_host):
            raise ValueError(f"Invalid GitHub host '{github_host}'. Must be a valid hostname.")

        # Validate github_org: alphanumeric with hyphens
        if github_org and not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,38}[a-zA-Z0-9])?$', github_org):
            raise ValueError(
                f"Invalid GitHub organization '{github_org}'. "
                "Must contain only alphanumeric characters and hyphens, "
                "start and end with alphanumeric characters, and be 1-39 characters long."
            )

        # Validate github_repo: alphanumeric with hyphens, underscores, and dots
        if github_repo and not re.match(r'^[a-zA-Z0-9._-]+$', github_repo):
            raise ValueError(
                f"Invalid GitHub repository name '{github_repo}'. "
                "Must contain only alphanumeric characters, hyphens, underscores, and dots."
            )

        # Validate git_branch: valid git branch name (no spaces, control chars, or special git chars)
        if git_branch and not re.match(r'^[a-zA-Z0-9._/-]+$', git_branch):
            raise ValueError(
                f"Invalid git branch name '{git_branch}'. "
                "Must contain only alphanumeric characters, dots, hyphens, underscores, and forward slashes."
            )

    def configGitOpsCluster(self) -> None:
        """
        Configure cluster identification for GitOps.

        Collects:
        - account_id: Account identifier (top-level organization)
        - region_id: Region identifier (e.g., us-east, eu-west)
        - cluster_id: Unique cluster identifier
        - cluster_url: OpenShift cluster URL
        """
        logger.debug("Configuring GitOps cluster identification")

        self.printH2("Cluster Identification")
        self.printDescription([
            "Configure cluster identification for GitOps configuration.",
            "The merge-key structure will be: account_id/region_id/cluster_id"
        ])

        # Check if values are already set (non-interactive mode)
        if not self.getParam("account_id"):
            self.promptForString("Account ID", "account_id")

        if not self.getParam("cluster_id"):
            self.promptForString("Cluster ID", "cluster_id")

        # Get cluster URL from current connection if not set
        if not self.getParam("cluster_url"):
            try:
                # Try to get from current cluster connection
                cluster_url = self.dynamicClient.configuration.host
                self.setParam("cluster_url", cluster_url)
                logger.debug(f"Auto-detected cluster URL: {cluster_url}")
            except Exception as e:
                logger.warning(f"Could not auto-detect cluster URL: {e}")
                # In non-interactive mode, this is a fatal error
                if self.noConfirm:
                    raise ValueError(
                        "Cluster URL could not be auto-detected and must be provided "
                        "in non-interactive mode. Use --cluster-url parameter."
                    ) from e
                self.promptForString("Cluster URL", "cluster_url")

    def configGitOpsSecrets(self) -> None:
        """
        Configure secrets management for GitOps.

        Collects:
        - secrets_path: Path to secrets in AWS Secrets Manager or other secret store
        - avp_aws_secret_region: AWS region for secrets (if using AWS Secrets Manager)
        - sm_aws_access_key_id: AWS access key ID for Secrets Manager access
        - sm_aws_secret_access_key: AWS secret access key for Secrets Manager access
        """
        logger.debug("Configuring GitOps secrets management")

        self.printH2("Secrets Management")
        self.printDescription([
            "Configure how secrets will be managed in the GitOps repository.",
            "Secrets can be stored in AWS Secrets Manager and referenced using ArgoCD Vault Plugin (AVP)."
        ])

        # Check if values are already set (non-interactive mode)
        if not self.getParam("avp_aws_secret_region"):
            self.promptForString("AWS Secrets Manager region", "avp_aws_secret_region", default="us-east-1")

        sm_region = self.getParam("avp_aws_secret_region")
        account_id = self.getParam("account_id")

        if not self.getParam("secrets_path"):
            self.promptForString("Secrets path", "secrets_path",
                                 default=f"arn:aws:secretsmanager:{sm_region}:{account_id}:secret")

        # AWS credentials for Secrets Manager access
        if not self.getParam("sm_aws_access_key_id"):
            self.promptForString("AWS Access Key ID for Secrets Manager", "sm_aws_access_key_id", isPassword=True)

        if not self.getParam("sm_aws_secret_access_key"):
            self.promptForString("AWS Secret Access Key for Secrets Manager", "sm_aws_secret_access_key", isPassword=True)

    def validateGitOpsSettings(self) -> tuple[bool, list[str]]:
        """
        Validate GitOps configuration settings.

        Checks:
        - Repository is accessible
        - Git credentials are valid
        - ArgoCD is installed and accessible
        - Account/cluster IDs are valid

        Returns:
            tuple: (is_valid, list of error messages)
        """
        # TODO: Implement GitOps settings validation in Phase 3
        logger.info("Validating GitOps settings (stub)")
        return True, []
