#!/usr/bin/env python
# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

import tkinter as tk
import tkinter.font as font
import logging
import logging.handlers

from os import path

# Use of the openshift client rather than the kubernetes client allows us access to "apply"
from openshift import dynamic
from kubernetes import config
from kubernetes.client import api_client

from mas.devops.ocp import connect, createNamespace
from mas.devops.mas import listMasInstances
from mas.devops.tekton import installOpenShiftPipelines, updateTektonDefinitions, launchUpgradePipeline

logger = logging.getLogger(__name__)

# Useful materials:
# - https://realpython.com/python-gui-tkinter

class MasGui():
    def __init__(self):

        self.homeDir = path.abspath(path.dirname(__file__))
        logger.debug(f"Home directory = {self.homeDir}")
        # Root Window
        self.window = tk.Tk()
        self.window.title('IBM Maximo Application Suite Admin Tool')
        self.window.resizable(False, False)

        # Fonts
        self.defaultFont = font.nametofont("TkDefaultFont")
        self.defaultFont.configure(family="Tahoma", size=10, weight=font.NORMAL)

        self.titleFont=font.Font(family="tahoma",size=14)
        self.entryFont=font.Font(family="tahoma",size=10)

        # Top-Level Frames
        self.frame1 = tk.Frame(master=self.window, width=600, height=100)
        self.frame2 = tk.Frame(master=self.window, width=600, height=500)
        self.frame2.pack_propagate(0)
        self.frame3 = tk.Frame(master=self.window, width=600, height=50)
        self.frame3.pack_propagate(0)

        # frame1.columnconfigure(0, minsize=500)
        # window.rowconfigure([0, 1], minsize=500)

        # Frame 1: Connect to OCP
        self.connectHeader = tk.Label(master=self.window, font=self.titleFont, text="Connect to OpenShift")

        self.serverLabel = tk.Label(master=self.frame1, text="Server")
        self.serverField = tk.Entry(master=self.frame1, font=self.entryFont, width=80)

        self.tokenLabel = tk.Label(master=self.frame1, text="Token")
        self.tokenField = tk.Entry(master=self.frame1, font=self.entryFont, width=80)

        self.connectButton = tk.Button(master=self.frame1, text="Connect", command=self.connectAndUpdateUI)

        self.serverLabel.grid(row=0, column=0, padx=2, pady=2, sticky="E")
        self.serverField.grid(row=0, column=1, padx=2, pady=2)
        self.tokenLabel.grid(row=1, column=0, padx=2, pady=2, sticky="E")
        self.tokenField.grid(row=1, column=1, padx=2, pady=2)
        self.connectButton.grid(row=1, column=2, padx=2, pady=2)

        # Frame 2: Table of MAS Instances
        self.tableHeader = tk.Label(master=self.frame2, font=self.titleFont, text="Select MAS Instance to Upgrade")
        self.tableFrame = tk.Frame(master=self.frame2)

        # Frame 3: Status Bar
        self.status = tk.StringVar()
        self.statusIcon = tk.Label(self.frame3, text="!")
        self.statusIcon.grid(row=0, column=0, sticky="NW")
        self.statusInfo = tk.Label(self.frame3, textvariable=self.status)
        self.statusInfo.grid(row=0, column=1, sticky="NW")

        self.connectHeader.pack(padx=2, pady=5)
        self.frame1.pack()
        self.frame2.pack(fill=None, expand=False)
        self.frame3.pack(side=tk.LEFT)

    def updateStatus(self, message):
        logger.info(f"Status change: {message}")
        self.status.set(message)
        self.statusInfo.update_idletasks()
        # self.statusInfo.config(text=message)
        # self.statusInfo.grid(row=0, column=1, sticky="NW")

    def mainloop(self):
        self.window.mainloop()

    def connectAndUpdateUI(self):
        server = self.serverField.get()
        token = self.tokenField.get()

        self.serverField.config(state=tk.DISABLED)
        self.tokenField.config(state=tk.DISABLED)
        self.connectButton.config(state=tk.DISABLED)
        self.updateStatus(f"Connecting to {server}")
        connect(server=server, token=token)

        # Configure the Kubernetes API Client
        config.load_kube_config()
        self.dynClient = dynamic.DynamicClient(
            api_client.ApiClient(configuration=config.load_kube_config())
        )

        # Get a list of all MAS instances installed on the cluster
        suites = listMasInstances(self.dynClient)

        self.updateStatus(f"Successfully connected to {server}")

        self.upgradeButtons={}
        row = 0
        for suite in suites:
            name = tk.Label(master=self.tableFrame, text=suite['metadata']['name'], width=20)
            version = tk.Label(master=self.tableFrame, text=suite['status']['versions']['reconciled'], width=20)
            self.upgradeButtons[suite['metadata']['name']] = tk.Button(master=self.tableFrame, text="Upgrade", width=20, command=lambda: self.upgradeAndUpdateUI(suite['metadata']['name']))

            name.grid(row=row, column=0)
            version.grid(row=row, column=1)
            self.upgradeButtons[suite['metadata']['name']].grid(row=row, column=2)
            row += 1

        self.tableHeader.pack(padx=2, pady=5)
        self.tableFrame.pack(padx=2, pady=5)

    def upgradeAndUpdateUI(self, instanceId):
        self.updateStatus(f"Starting upgrade for {instanceId}")

        pipelinesNamespace = f"mas-{instanceId}-pipelines"

        self.updateStatus("Validating OpenShift Pipelines Installation")
        installOpenShiftPipelines(self.dynClient, self.homeDir)

        self.updateStatus(f"Setting up {pipelinesNamespace} namespace")
        createNamespace(self.dynClient, pipelinesNamespace)

        self.updateStatus(f"Updating MAS tekton definitions in {pipelinesNamespace}")
        updateTektonDefinitions(pipelinesNamespace, self.homeDir)

        self.updateStatus(f"Launching upgrade pipeline for {instanceId}")
        launchUpgradePipeline(instanceId)

        self.updateStatus(f"Upgrade of {instanceId} started (not really, this is just a poc)")
        self.upgradeButtons[instanceId].config(state=tk.DISABLED)


if __name__ == '__main__':
    # Set up a log formatter
    chFormatter = logging.Formatter('%(asctime)-25s' + ' %(levelname)-8s %(message)s')

    # Set up a log handler (5mb rotating log file)
    ch = logging.handlers.RotatingFileHandler(
        "mas.log", maxBytes=(1048576*5), backupCount=2
    )

    ch.setLevel(logging.DEBUG)
    ch.setFormatter(chFormatter)

    # Configure the root logger
    rootLogger = logging.getLogger()
    rootLogger.addHandler(ch)
    rootLogger.setLevel(logging.DEBUG)

    gui = MasGui()
    gui.mainloop()
