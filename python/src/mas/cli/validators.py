# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

from re import match
from os import path

# Use of the openshift client rather than the kubernetes client allows us access to "apply"
from openshift import dynamic
from kubernetes import config
from kubernetes.client import api_client

from prompt_toolkit.validation import Validator, ValidationError

from mas.devops.ocp import getStorageClass
from mas.devops.mas import verifyMasInstance

import logging

logger = logging.getLogger(__name__)


class InstanceIDFormatValidator(Validator):
    def validate(self, document):
        """
        Validate that a MAS instance ID exists on the target cluster
        """
        instanceId = document.text

        if not match(r"^[a-z][a-z0-9-]{1,10}[a-z0-9]$", instanceId):
            raise ValidationError(message='MAS instance ID does not meet the requirements', cursor_position=len(instanceId))


class WorkspaceIDFormatValidator(Validator):
    def validate(self, document):
        """
        Validate that a MAS instance ID exists on the target cluster
        """
        instanceId = document.text

        if not match(r"^[a-z][a-z0-9]{2,11}$", instanceId):
            raise ValidationError(message='Workspace ID does not meet the requirements', cursor_position=len(instanceId))


class TimeoutFormatValidator(Validator):
    def validate(self, document):
        """
        Validate that a MAS instance ID exists on the target cluster
        """
        string_to_validate = document.text
        if string_to_validate != "" and not match(r'^([0-9]+)([hm])$', string_to_validate):
            message = f"Error: Your input: {string_to_validate} does not meet the required pattern. Please use it in hours or minutes format (e.g., 12h, 12m)."
            raise ValidationError(message=message, cursor_position=len(string_to_validate))


class WorkspaceNameFormatValidator(Validator):
    def validate(self, document):
        """
        Validate that a MAS instance ID exists on the target cluster
        """
        instanceId = document.text

        if not match(r"^.{3,300}$", instanceId):
            raise ValidationError(message='Workspace name does not meet the requirements', cursor_position=len(instanceId))


class InstanceIDValidator(Validator):
    def validate(self, document):
        """
        Validate that a MAS instance ID exists on the target cluster
        """
        instanceId = document.text

        dynClient = dynamic.DynamicClient(
            api_client.ApiClient(configuration=config.load_kube_config())
        )
        if not verifyMasInstance(dynClient, instanceId):
            raise ValidationError(message='Not a valid MAS instance ID on this cluster', cursor_position=len(instanceId))


class StorageClassValidator(Validator):
    def validate(self, document):
        """
        Validate that a StorageClass exists on the target cluster
        """
        name = document.text

        dynClient = dynamic.DynamicClient(
            api_client.ApiClient(configuration=config.load_kube_config())
        )
        if getStorageClass(dynClient, name) is None:
            raise ValidationError(message='Specified storage class is not available on this cluster', cursor_position=len(name))


class YesNoValidator(Validator):
    def validate(self, document):
        """
        Validate that a response is understandable as a yes/no response
        """
        response = document.text
        if response.lower() not in ["y", "n", "yes", "no"]:
            raise ValidationError(message='Enter a valid response: y(es), n(o)', cursor_position=len(response))


class FileExistsValidator(Validator):
    def validate(self, document):
        """
        Validate that a file exists on the local system
        """
        response = document.text
        if not path.isfile(response):
            raise ValidationError(message=f"{response} does not exist, or is not a file", cursor_position=len(response))


class DirectoryExistsValidator(Validator):
    def validate(self, document):
        """
        Validate that a file exists on the local system
        """
        response = document.text
        if not path.isdir(response):
            raise ValidationError(message=f"{response} does not exist, or is not a directory", cursor_position=len(response))


class OptimizerInstallPlanValidator(Validator):
    def validate(self, document):
        """
        Validate that a response is a valid install plan for Optimizer
        """
        response = document.text
        if response not in ["full", "limited"]:
            raise ValidationError(message='Enter a valid response: full, limited', cursor_position=len(response))
