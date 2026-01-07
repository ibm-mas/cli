# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

from os import getenv
from prompt_toolkit import prompt, print_formatted_text, HTML, PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import Validator
from typing import List

from .validators import YesNoValidator, IntValidator, FileExistsValidator, DirectoryExistsValidator

import logging
logger = logging.getLogger(__name__)

H1COLOR = "SkyBlue"
H2COLOR = "SkyBlue"
DESCRIPTIONCOLOR = "LightSlateGrey"
SUMMARYCOLOR = "SkyBlue"
UNDEFINEDPARAMCOLOR = "LightSlateGrey"
PROMPTCOLOR = "Yellow"


class PrintMixin():
    def printTitle(self, message: str) -> None:
        print_formatted_text(HTML(f"<b><u>{message.replace(' & ', ' &amp; ')}</u></b>"))

    def printH1(self, message: str) -> None:
        self.h1count += 1  # type: ignore
        self.h2count = 0  # type: ignore
        print()
        print_formatted_text(HTML(f"<u><{H1COLOR}>{self.h1count}) {message.replace(' & ', ' &amp; ')}</{H1COLOR}></u>"))  # type: ignore

    def printH2(self, message: str) -> None:
        self.h2count += 1  # type: ignore
        print()
        print_formatted_text(HTML(f"<u><{H2COLOR}>{self.h1count}.{self.h2count}) {message.replace(' & ', ' &amp; ')}</{H2COLOR}></u>"))  # type: ignore

    def printDescription(self, content: List[str]) -> None:
        content[0] = f"<{DESCRIPTIONCOLOR}>{content[0]}"
        content[len(content) - 1] = f"{content[len(content) - 1]}</{DESCRIPTIONCOLOR}>"
        print_formatted_text(HTML("\n".join(content)))

    def printHighlight(self, message: str | List[str]) -> None:
        if isinstance(message, list):
            message = "\n".join(message)

        print_formatted_text(HTML(f"<MediumTurquoise>{message.replace(' & ', ' &amp; ')}</MediumTurquoise>"))

    def printWarning(self, message: str) -> None:
        print_formatted_text(HTML(f"<Red>Warning: {message.replace(' & ', ' &amp; ')}</Red>"))

    def printSummary(self, title: str, value: str) -> None:
        titleLength = len(title)
        message = f"{title} {'.' * (40 - titleLength)} {value}"
        print_formatted_text(HTML(f"  <{SUMMARYCOLOR}>{message.replace(' & ', ' &amp; ')}</{SUMMARYCOLOR}>"))

    def printParamSummary(self, message: str, param: str) -> None:
        if self.getParam(param) is None:  # type: ignore
            self.printSummary(message, f"<{UNDEFINEDPARAMCOLOR}>Undefined</{UNDEFINEDPARAMCOLOR}>")
        elif self.getParam(param) == "":  # type: ignore
            self.printSummary(message, f"<{UNDEFINEDPARAMCOLOR}>Default</{UNDEFINEDPARAMCOLOR}>")
        else:
            self.printSummary(message, self.getParam(param))  # type: ignore


def masPromptYesOrNo(message: str) -> HTML:
    return HTML(f"<{PROMPTCOLOR}>{message.replace(' & ', ' &amp; ')}? [y/n]</{PROMPTCOLOR}> ")


def masPromptValue(message: str) -> HTML:
    return HTML(f"<{PROMPTCOLOR}>{message.replace(' & ', ' &amp; ')}</{PROMPTCOLOR}> ")


class PromptMixin():
    def yesOrNo(self, message: str, param: str | None = None) -> bool:
        response = prompt(message=masPromptYesOrNo(message), validator=YesNoValidator(), validate_while_typing=False)
        responseAsBool = response.lower() in ["y", "yes"]

        if param is not None:
            self.params[param] = "true" if responseAsBool else "false"  # type: ignore
        return responseAsBool

    def promptForString(self, message: str, param: str | None = None, default: str = "", isPassword: bool = False, validator: Validator | None = None, completer: WordCompleter | None = None) -> str:
        if param is not None and default == "":
            default = getenv(param.upper(), default="")

        if completer is not None:
            promptSession = PromptSession()
            response = promptSession.prompt(message=masPromptValue(message), is_password=isPassword, default=default, completer=completer, validator=validator, validate_while_typing=False, pre_run=promptSession.default_buffer.start_completion)
        else:
            response = prompt(message=masPromptValue(message), is_password=isPassword, default=default, completer=completer, validator=validator, validate_while_typing=False)

        if param is not None:
            self.params[param] = response  # type: ignore
        return response

    def promptForInt(self, message: str, param: str | None = None, default: int | None = None, min: int | None = None, max: int | None = None) -> int:
        if param is not None and default is None:
            default = getenv(param.upper(), default=None)  # type: ignore

        if default is None:
            response = int(prompt(message=masPromptValue(message), validator=IntValidator(min, max)))
        else:
            response = int(prompt(message=masPromptValue(message), validator=IntValidator(min, max), default=str(default)))
        if param is not None:
            self.params[param] = str(response)  # type: ignore
        return response

    def promptForListSelect(self, message: str, options: List[str], param: str | None = None, default: int | None = None) -> str:
        selection = self.promptForInt(message=message, default=default, min=1, max=len(options))
        # List indices are 0 origin, so we need to subtract 1 from the selection made to arrive at the correct value
        result = options[selection - 1]
        if param is not None:
            self.setParam(param, result)  # type: ignore
        return result

    def promptForFile(self, message: str, mustExist: bool = True, default: str = "", envVar: str = "") -> str:
        if default == "" and envVar != "":
            default = getenv(envVar, "")
        if mustExist:
            return prompt(message=masPromptValue(message), validator=FileExistsValidator(), validate_while_typing=False, default=default)
        else:
            return prompt(message=masPromptValue(message), default=default)

    def promptForDir(self, message: str, mustExist: bool = True, default: str = "") -> str:
        if mustExist:
            return prompt(message=masPromptValue(message), validator=DirectoryExistsValidator(), validate_while_typing=False, default=default)
        else:
            return prompt(message=masPromptValue(message), default=default)

# Made with Bob
