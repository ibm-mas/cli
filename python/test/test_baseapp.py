#!/usr/bin/env python
# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

import os
from mas.cli.cli import BaseApp
from prompt_toolkit.application import create_app_session
from prompt_toolkit.output import DummyOutput


def test_version():
    """
    Test that BaseApp.version matches the VERSION environment variable when set
    """
    expected_version = "100.0.0-pre.local"
    if 'VERSION' in os.environ:
        expected_version = os.environ['VERSION']

    with create_app_session(output=DummyOutput()):
        app = BaseApp()
        assert app.version == expected_version, f"Expected version {expected_version}, but got {app.version}"
