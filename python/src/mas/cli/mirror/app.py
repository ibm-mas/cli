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

import logging

from ..cli import BaseApp
from .argParser import mirrorArgParser


logger = logging.getLogger(__name__)


def logMethodCall(func):
    def wrapper(self, *args, **kwargs):
        logger.debug(f">>> InstallApp.{func.__name__}")
        result = func(self, *args, **kwargs)
        logger.debug(f"<<< InstallApp.{func.__name__}")
        return result
    return wrapper


class MirrorApp(BaseApp):

    @logMethodCall
    def interactiveMode(self, simplified: bool, advanced: bool) -> None:
        # Interactive mode
        self._interactiveMode = True

    @logMethodCall
    def nonInteractiveMode(self) -> None:
        self._interactiveMode = False

    @logMethodCall
    def mirror(self, argv):
        args = mirrorArgParser.parse_args(args=argv)
        print(args)
