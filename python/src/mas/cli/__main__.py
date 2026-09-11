# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
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
from kubernetes.client.exceptions import ApiException
from prompt_toolkit import HTML, print_formatted_text
from urllib3.exceptions import MaxRetryError

from mas.cli import __version__ as VERSION

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
            + " - <ForestGreen>mas-cli db2ucluster-migration</ForestGreen> Migrate Db2uCluster to Db2uInstance\n"
        )
    )
    print_formatted_text(HTML("For usage information run <ForestGreen>mas-cli [action] --help</ForestGreen>\n"))


def main() -> None:
    """Run the mas-cli command dispatcher."""
    app = None
    try:
        function = argv[1]

        # Lazy-load app modules to optimize startup time.
        # Only import and instantiate the specific app module needed for the requested function,
        # rather than loading all app modules upfront. This significantly reduces initial load time.
        if function == "install":
            from mas.cli.install.app import InstallApp

            app = InstallApp()
            raise SystemExit(app.install(argv[2:]))
        if function == "aiservice-install":
            from mas.cli.aiservice.install.app import AiServiceInstallApp

            app = AiServiceInstallApp()
            raise SystemExit(app.install(argv[2:]))
        if function == "aiservice-upgrade":
            from mas.cli.aiservice.upgrade.app import AiServiceUpgradeApp

            app = AiServiceUpgradeApp()
            raise SystemExit(app.upgrade(argv[2:]))
        if function == "uninstall":
            from mas.cli.uninstall.app import UninstallApp

            app = UninstallApp()
            raise SystemExit(app.uninstall(argv[2:]))
        if function == "update":
            from mas.cli.update.app import UpdateApp

            app = UpdateApp()
            raise SystemExit(app.update(argv[2:]))
        if function == "upgrade":
            from mas.cli.upgrade.app import UpgradeApp

            app = UpgradeApp()
            app.upgrade(argv[2:])
            return
        if function == "backup":
            from mas.cli.backup.app import BackupApp

            app = BackupApp()
            app.backup(argv[2:])
            return
        if function == "restore":
            from mas.cli.restore.app import RestoreApp

            app = RestoreApp()
            app.restore(argv[2:])
            return
        if function == "mirror":
            from mas.cli.mirror.app import MirrorApp

            app = MirrorApp()
            app.mirror(argv[2:])
            return
        if function == "setup-rbac":
            from mas.cli.setup_rbac.app import SetupRBACApp

            app = SetupRBACApp()
            app.setupRBAC(argv[2:])
            return
        if function == "pre-install":
            from mas.cli.pre_install.app import SetupPreinstallRBACApp

            app = SetupPreinstallRBACApp()
            app.setupPreinstallRBAC(argv[2:])
            return
        if function == "must-gather":
            from mas.cli.must_gather.app import MustGatherApp

            app = MustGatherApp()
            app.mustGather(argv[2:])
            return
        if function == "db2ucluster-migration":
            from mas.cli.db2_migration.app import Db2MigrationApp

            app = Db2MigrationApp()
            app.migrate(argv[2:])
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


if __name__ == "__main__":
    main()
