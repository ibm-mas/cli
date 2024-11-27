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

from .validators import YesNoValidator, FileExistsValidator, DirectoryExistsValidator

import logging
logger = logging.getLogger(__name__)

H1COLOR = "SkyBlue"
H2COLOR = "SkyBlue"
DESCRIPTIONCOLOR = "LightSlateGrey"
SUMMARYCOLOR = "SkyBlue"
UNDEFINEDPARAMCOLOR = "LightSlateGrey"
PROMPTCOLOR = "Yellow"


class PrintMixin():
    def printTitle(self, message):
        print_formatted_text(HTML(f"<b><u>{message.replace(' & ', ' &amp; ')}</u></b>"))

    def printH1(self, message):
        self.h1count += 1
        self.h2count = 0
        print()
        print_formatted_text(HTML(f"<u><{H1COLOR}>{self.h1count}) {message.replace(' & ', ' &amp; ')}</{H1COLOR}></u>"))

    def printH2(self, message):
        self.h2count += 1
        print()
        print_formatted_text(HTML(f"<u><{H2COLOR}>{self.h1count}.{self.h2count}) {message.replace(' & ', ' &amp; ')}</{H2COLOR}></u>"))

    def printDescription(self, content: list) -> None:
        content[0] = f"<{DESCRIPTIONCOLOR}>{content[0]}"
        content[len(content) - 1] = f"{content[len(content) - 1]}</{DESCRIPTIONCOLOR}>"
        print_formatted_text(HTML("\n".join(content)))

    def printHighlight(self, message: str) -> None:
        if isinstance(message, list):
            message = "\n".join(message)

        print_formatted_text(HTML(f"<MediumTurquoise>{message.replace(' & ', ' &amp; ')}</MediumTurquoise>"))

    def printWarning(self, message):
        print_formatted_text(HTML(f"<Red>Warning: {message.replace(' & ', ' &amp; ')}</Red>"))

    def printSummary(self, title: str, value: str) -> None:
        titleLength = len(title)
        message = f"{title} {'.' * (40 - titleLength)} {value}"
        print_formatted_text(HTML(f"  <{SUMMARYCOLOR}>{message.replace(' & ', ' &amp; ')}</{SUMMARYCOLOR}>"))

    def printParamSummary(self, message: str, param: str) -> None:
        if self.getParam(param) is None:
            self.printSummary(message, f"<{UNDEFINEDPARAMCOLOR}>Undefined</{UNDEFINEDPARAMCOLOR}>")
        elif self.getParam(param) == "":
            self.printSummary(message, f"<{UNDEFINEDPARAMCOLOR}>Default</{UNDEFINEDPARAMCOLOR}>")
        else:
            self.printSummary(message, self.getParam(param))


def masPromptYesOrNo(message):
    return HTML(f"<{PROMPTCOLOR}>{message.replace(' & ', ' &amp; ')}? [y/n]</{PROMPTCOLOR}> ")


def masPromptValue(message):
    return HTML(f"<{PROMPTCOLOR}>{message.replace(' & ', ' &amp; ')}</{PROMPTCOLOR}> ")


class PromptMixin():
    def yesOrNo(self, message: str, param: str = None) -> bool:
        response = prompt(masPromptYesOrNo(message), validator=YesNoValidator(), validate_while_typing=False)
        responseAsBool = response.lower() in ["y", "yes"]

        if param is not None:
            self.params[param] = "true" if responseAsBool else "false"
        return responseAsBool

    def promptForString(self, message: str, param: str = None, default: str = "", isPassword: bool = False, validator: Validator = None, completer: WordCompleter = None) -> str:
        if param is not None and default == "":
            default = getenv(param.upper(), default="")

        if completer is not None:
            promptSession = PromptSession()
            response = promptSession.prompt(masPromptValue(message), is_password=isPassword, default=default, completer=completer, validator=validator, validate_while_typing=False, pre_run=promptSession.default_buffer.start_completion)
        else:
            response = prompt(masPromptValue(message), is_password=isPassword, default=default, completer=completer, validator=validator, validate_while_typing=False)

        if param is not None:
            self.params[param] = response
        return response

    def promptForInt(self, message: str, param: str = None, default: int = None) -> int:
        if param is not None and default is None:
            default = getenv(param.upper(), default=None)

        if default is None:
            response = int(prompt(masPromptValue(message)))
        else:
            response = int(prompt(masPromptValue(message), default=str(default)))
        if param is not None:
            self.params[param] = str(response)
        return response

    def promptForListSelect(self, message: str, options: list, param: str = None, default: int = None) -> str:
        selection = self.promptForInt(message=message, default=default)
        # List indices are 0 origin, so we need to subtract 1 from the selection made to arrive at the correct value
        self.setParam(param, options[selection - 1])

    def promptForFile(self, message: str, mustExist: bool = True, default: str = "", envVar: str = "") -> None:
        if default == "" and envVar != "":
            default = getenv(envVar, "")
        if mustExist:
            return prompt(masPromptValue(message), validator=FileExistsValidator(), validate_while_typing=False, default=default)
        else:
            return prompt(masPromptValue(message), default=default)

    def promptForDir(self, message: str, mustExist: bool = True, default: str = "") -> None:
        if mustExist:
            return prompt(masPromptValue(message), validator=DirectoryExistsValidator(), validate_while_typing=False, default=default)
        else:
            return prompt(masPromptValue(message), default=default)
