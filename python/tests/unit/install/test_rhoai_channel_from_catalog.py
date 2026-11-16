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

"""
Unit tests for AiSettingsMixin.setRhoaiChannelFromCatalog.

  GIVEN a catalog with aiservice_platform: rhoai-v3 (November 2026 catalog onwards)
  THEN the RHOAI channel is set to stable-3.x

  GIVEN a catalog without aiservice_platform (before the November 2026 catalog)
  THEN the RHOAI channel is set to stable (RHOAI v2)

  GIVEN the user explicitly provided --rhoai-channel
  THEN the catalog never overrides it
"""

from mas.cli.install.app import InstallApp
from mas.cli.aiservice.install.app import AiServiceInstallApp


def _make_app(app_class, catalog: dict, rhoai_channel: str = ""):
    app = app_class.__new__(app_class)
    app.params = {"rhoai_channel": rhoai_channel} if rhoai_channel else {}
    app.chosenCatalog = catalog
    return app


class TestSetRhoaiChannelFromCatalog:
    def test_rhoai_v3_platform_uses_stable_3x(self):
        app = _make_app(InstallApp, {"aiservice_platform": "rhoai-v3"})
        app.setRhoaiChannelFromCatalog()
        assert app.getParam("rhoai_channel") == "stable-3.x"

    def test_missing_platform_uses_stable_for_rhoai_v2(self):
        app = _make_app(InstallApp, {"aiservice_version": {"9.1.x": "9.1.0"}})
        app.setRhoaiChannelFromCatalog()
        assert app.getParam("rhoai_channel") == "stable"

    def test_user_provided_channel_is_not_overridden(self):
        app = _make_app(InstallApp, {"aiservice_platform": "rhoai-v3"}, rhoai_channel="stable-2.25")
        app.setRhoaiChannelFromCatalog()
        assert app.getParam("rhoai_channel") == "stable-2.25"

    def test_unknown_platform_leaves_channel_unset(self):
        app = _make_app(InstallApp, {"aiservice_platform": "something-else"})
        app.setRhoaiChannelFromCatalog()
        assert app.getParam("rhoai_channel") == ""

    def test_no_catalog_leaves_channel_unset(self):
        app = _make_app(InstallApp, None)
        app.setRhoaiChannelFromCatalog()
        assert app.getParam("rhoai_channel") == ""

    def test_standalone_aiservice_install_uses_same_logic(self):
        app = _make_app(AiServiceInstallApp, {"aiservice_platform": "rhoai-v3"})
        app.setRhoaiChannelFromCatalog()
        assert app.getParam("rhoai_channel") == "stable-3.x"

    def test_process_catalog_choice_sets_channel(self):
        app = _make_app(
            AiServiceInstallApp,
            {
                "catalog_digest": "sha256:abc",
                "mongo_extras_version_default": "7.0.0",
                "aiservice_version": {"9.2.x": "9.2.0"},
                "aiservice_platform": "rhoai-v3",
            },
        )
        app.params["mas_catalog_version"] = "v9-261105-amd64"
        app.processCatalogChoice()
        assert app.getParam("rhoai_channel") == "stable-3.x"
