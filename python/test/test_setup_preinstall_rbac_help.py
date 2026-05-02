import pytest

from mas.cli.setup_preinstall_rbac.app import SetupPreinstallRBACApp

from prompt_toolkit.application import create_app_session
from prompt_toolkit.output import DummyOutput


def testSetupPreinstallRBACHelp():
    """
    Should exit with RC = 0 after printing help message
    """
    with create_app_session(output=DummyOutput()):
        with pytest.raises(SystemExit) as e:
            app = SetupPreinstallRBACApp()
            app.setupPreinstallRBAC(argv=["--help"])
        assert e.type == SystemExit
        assert e.value.code == 0
