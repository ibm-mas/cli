# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

from .db2Settings import Db2SettingsMixin
from .kafkaSettings import KafkaSettingsMixin
from .manageSettings import ManageSettingsMixin
from .turbonomicSettings import TurbonomicSettingsMixin
from .additionalConfigs import AdditionalConfigsMixin
from .MongodbSettings import MongodbSettingsMixin

class InstallSettingsMixin(Db2SettingsMixin, KafkaSettingsMixin, ManageSettingsMixin, TurbonomicSettingsMixin, AdditionalConfigsMixin,MongodbSettingsMixin):
  """
  This class collects all the Mixins providing interactive prompts for mas-install
  """
  pass
