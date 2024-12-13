import pytest

from mas.cli.install.app import InstallApp
from mas.cli.upgrade.app import UpgradeApp
from mas.cli.uninstall.app import UninstallApp

from prompt_toolkit.application import create_app_session
from prompt_toolkit.output import DummyOutput


def testInstallHelp():
    """
    Should exit with RC = 0 after printing help message
    """
    with create_app_session(output=DummyOutput()):
        with pytest.raises(SystemExit) as e:
            app = InstallApp()
            app.install(argv=["--help"])
        assert e.type == SystemExit
        assert e.value.code == 0


def testUninstallHelp():
    """
    Should exit with RC = 0 after printing help message
    """
    with create_app_session(output=DummyOutput()):
        with pytest.raises(SystemExit) as e:
            app = UninstallApp()
            app.uninstall(argv=["--help"])
        assert e.type == SystemExit
        assert e.value.code == 0


def testUpgradeHelp():
    """
    Should exit with RC = 0 after printing help message
    """
    with create_app_session(output=DummyOutput()):
        with pytest.raises(SystemExit) as e:
            app = UpgradeApp()
            app.upgrade(argv=["--help"])
        assert e.type == SystemExit
        assert e.value.code == 0
