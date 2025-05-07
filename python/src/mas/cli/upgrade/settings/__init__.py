# *****************************************************************************
# Copyright (c) 2025 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

from ...install.settings.db2Settings import Db2SettingsMixin
from ...install.settings.manageSettings import ManageSettingsMixin


class UpgradeSettingsMixin(Db2SettingsMixin, ManageSettingsMixin):
    """
    This class collects all the Mixins providing interactive prompts for mas-upgrade
    """
    pass
