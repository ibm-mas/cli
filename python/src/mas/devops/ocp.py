# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

import logging
from kubeconfig import KubeConfig
from kubeconfig.exceptions import KubectlNotFoundError
from openshift.dynamic.exceptions import NotFoundError

logger = logging.getLogger(__name__)

def connect(server, token):
    """
    Connect to target OCP
    """
    logger.info(f"Connect(server={server}, token=***)")

    try:
        conf = KubeConfig()
    except KubectlNotFoundError:
        logger.warning("Unable to locate kubectl on the path")
        return False

    conf.view()
    logger.debug(f"Starting KubeConfig context: {conf.current_context()}")

    conf.set_credentials(
        name='my-credentials',
        token=token
    )
    conf.set_cluster(
        name='my-cluster',
        server=server
    )
    conf.set_context(
        name='my-context',
        cluster='my-cluster',
        user='my-credentials'
    )

    conf.use_context('my-context')
    conf.view()
    logger.info(f"KubeConfig context changed to {conf.current_context()}")
    return True


def createNamespace(dynClient, namespace):
    """
    Create a namespace if it does not exist
    """
    namespaceAPI = dynClient.resources.get(api_version="v1", kind="Namespace")
    try:
        namespaceAPI.get(name=namespace)
        logger.debug(f"Namespace {namespace} already exists")
    except NotFoundError as e:
        nsObj = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": namespace
            }
        }
        namespaceAPI.create(body=nsObj)
        logger.debug(f"Created namespace {namespace}")
    return True
