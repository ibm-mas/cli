# *****************************************************************************
# Copyright (c) 2024, 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

from typing import TYPE_CHECKING, Dict, List


if TYPE_CHECKING:
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.validation import Validator


class RedisSettingsMixin():
    if TYPE_CHECKING:
        # Attributes from BaseApp and other mixins
        params: Dict[str, str]
        showAdvancedOptions: bool

        # Methods from BaseApp
        def setParam(self, param: str, value: str) -> None:
            ...

        def getParam(self, param: str) -> str:
            ...

        # Methods from PrintMixin
        def printH1(self, message: str) -> None:
            ...

        def printDescription(self, content: List[str]) -> None:
            ...

        # Methods from PromptMixin
        def promptForString(
            self,
            message: str,
            param: str | None = None,
            default: str = "",
            isPassword: bool = False,
            validator: Validator | None = None,
            completer: WordCompleter | None = None
        ) -> str:
            ...

    def configRedis(self) -> None:
        """
        Configure Redis for Collaborate addon.
        Redis will be deployed automatically when Collaborate is enabled.
        """
        self.printH1("Configure Redis for Collaborate")
        self.printDescription([
            "Redis is required for the Collaborate addon to support caching.",
            "The installer will automatically deploy Redis with high availability (Sentinel + HAProxy)."
        ])

        if self.showAdvancedOptions:
            self.promptForString("Redis namespace", "redis_namespace", default="redis")
        else:
            # Use default namespace
            self.setParam("redis_namespace", "redis")

        # Always install Redis when Collaborate is enabled
        self.setParam("redis_action", "install")
        self.setParam("redis_cfg_file", f"/workspace/configs/redis-{self.getParam('redis_namespace')}.yml")
