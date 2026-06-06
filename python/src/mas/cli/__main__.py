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
from sys import argv

from jinja2.exceptions import TemplateNotFound
from kubeconfig.exceptions import KubectlCommandError
from kubernetes.client.exceptions import ApiException
from prompt_toolkit import HTML, print_formatted_text
from urllib3.exceptions import MaxRetryError

from mas.cli import __version__ as VERSION
from mas.cli.aiservice.install.app import AiServiceInstallApp
from mas.cli.aiservice.upgrade.app import AiServiceUpgradeApp
from mas.cli.backup.app import BackupApp
from mas.cli.install.app import InstallApp
from mas.cli.mirror.app import MirrorApp
from mas.cli.must_gather.app import MustGatherApp
from mas.cli.pre_install.app import SetupPreinstallRBACApp
from mas.cli.restore.app import RestoreApp
from mas.cli.setup_rbac.app import SetupRBACApp
from mas.cli.uninstall.app import UninstallApp
from mas.cli.update.app import UpdateApp
from mas.cli.upgrade.app import UpgradeApp

logger = logging.getLogger(__name__)


def usage() -> None:
    """Print CLI usage information."""
    print_formatted_text(HTML(""))

    print_formatted_text(HTML(f"\n<u>IBM Maximo Application Suite Admin CLI v{VERSION}</u>"))
    print_formatted_text(
        HTML(
            "Powered by <DarkGoldenRod><u>https://github.com/ibm-mas/ansible-devops/</u></DarkGoldenRod> and <DarkGoldenRod><u>https://tekton.dev/</u></DarkGoldenRod>"
        )
    )
    print("")
    print_formatted_text(
        HTML(
            "Important Notice:\nThis standalone CLI (<ForestGreen>mas-cli</ForestGreen>) is still in beta state, not all functions supported by the <ForestGreen>mas</ForestGreen> function in quay.io/ibmmas/cli are supported yet"
        )
    )
    print("")
    print_formatted_text(
        HTML(
            "<b>MAS Management Actions:</b>\n"
            + " - <ForestGreen>mas-cli install</ForestGreen>   Install IBM Maximo Application Suite\n"
            + " - <ForestGreen>mas-cli update</ForestGreen>    Apply updates and security fixes\n"
            + " - <ForestGreen>mas-cli upgrade</ForestGreen>   Upgrade to a new MAS release\n"
            + " - <ForestGreen>mas-cli backup</ForestGreen>    Backup a MAS instance\n"
            + " - <ForestGreen>mas-cli uninstall</ForestGreen> Remove MAS from the cluster\n"
            + " - <ForestGreen>mas-cli mirror</ForestGreen>    Mirror container images\n"
            + " - <ForestGreen>mas-cli must-gather</ForestGreen> Collect diagnostic information\n"
            + " - <ForestGreen>mas-cli setup-rbac</ForestGreen>  Set up RBAC resources for MAS installation\n"
            + " - <ForestGreen>mas-cli pre-install</ForestGreen>  Set up pre-install RBAC for MAS\n"
        )
    )
    print_formatted_text(HTML("For usage information run <ForestGreen>mas-cli [action] --help</ForestGreen>\n"))


def main() -> None:
    """Run the mas-cli command dispatcher."""
    app = None
    try:
        function = argv[1]

        if function == "install":
            app = InstallApp()
            raise SystemExit(app.install(argv[2:]))
        if function == "aiservice-install":
            app = AiServiceInstallApp()
            raise SystemExit(app.install(argv[2:]))
        if function == "aiservice-upgrade":
            app = AiServiceUpgradeApp()
            raise SystemExit(app.upgrade(argv[2:]))
        if function == "uninstall":
            app = UninstallApp()
            raise SystemExit(app.uninstall(argv[2:]))
        if function == "update":
            app = UpdateApp()
            raise SystemExit(app.update(argv[2:]))
        if function == "upgrade":
            app = UpgradeApp()
            app.upgrade(argv[2:])
            return
        if function == "backup":
            app = BackupApp()
            app.backup(argv[2:])
            return
        if function == "restore":
            app = RestoreApp()
            app.restore(argv[2:])
            return
        if function == "mirror":
            app = MirrorApp()
            app.mirror(argv[2:])
            return
        if function == "setup-rbac":
            app = SetupRBACApp()
            app.setupRBAC(argv[2:])
            return
        if function == "pre-install":
            app = SetupPreinstallRBACApp()
            app.setupPreinstallRBAC(argv[2:])
            return
        if function == "must-gather":
            app = MustGatherApp()
            app.mustGather(argv[2:])
            return
        if function in ["-h", "--help"]:
            usage()
            raise SystemExit(0)

        usage()
        print_formatted_text(HTML(f"<Red>Unknown action: {function}</Red>\n"))
        raise SystemExit(1)

    except KeyboardInterrupt:
        return
    except ApiException as exception:
        error_message = f"[{exception.status}:{exception.reason}] {exception.body if hasattr(exception, 'body') else str(exception)}"
        if app:
            app.fatalError(message=error_message)
        else:
            logger.error(error_message)
            raise SystemExit(1) from exception
    except MaxRetryError as exception:
        if app:
            app.fatalError(message="Unable to connect to API server", exception=exception)
        else:
            logger.error("Unable to connect to API server", exc_info=exception)
            raise SystemExit(1) from exception
    except TemplateNotFound as exception:
        if app:
            app.fatalError("Could not find template", exception=exception)
        else:
            logger.error("Could not find template", exc_info=exception)
            raise SystemExit(1) from exception
    except KubectlCommandError as exception:
        if app:
            app.fatalError("Could not execute kubectl command", exception=exception)
        else:
            logger.error("Could not execute kubectl command", exc_info=exception)
            raise SystemExit(1) from exception


if __name__ == "__main__":
    main()
