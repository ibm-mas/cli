# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

import pytest

from mas.cli.rollback.app import RollbackApp
from prompt_toolkit.application import create_app_session
from prompt_toolkit.output import DummyOutput


def testRollbackHelp():
    """
    Should exit with RC = 0 after printing help message.

    GIVEN the rollback CLI is invoked with --help
    WHEN rollback() processes the argv
    THEN SystemExit(0) is raised.
    """
    with create_app_session(output=DummyOutput()):
        with pytest.raises(SystemExit) as e:
            app = RollbackApp()
            app.rollback(argv=["--help"])
        assert e.type == SystemExit
        assert e.value.code == 0
