#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2014:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

"""
The objects package contains definition classes of the different objects
 that can be declared in configuration files.

 """


from item import Item, Items
from timeperiod import Timeperiod, Timeperiods
from schedulingitem import SchedulingItem
from matchingitem import MatchingItem
from service import Service, Services
from command import Command, Commands
from resultmodulation import Resultmodulation, Resultmodulations
from escalation import Escalation, Escalations
from serviceescalation import Serviceescalation, Serviceescalations
from hostescalation import Hostescalation, Hostescalations
from host import Host, Hosts
from hostgroup import Hostgroup, Hostgroups
from realm import Realm, Realms
from contact import Contact, Contacts
from contactgroup import Contactgroup, Contactgroups
from notificationway import NotificationWay, NotificationWays
from servicegroup import Servicegroup, Servicegroups
from servicedependency import Servicedependency, Servicedependencies
from hostdependency import Hostdependency, Hostdependencies
from module import Module, Modules
from discoveryrule import Discoveryrule, Discoveryrules
from discoveryrun import Discoveryrun, Discoveryruns
from trigger import Trigger, Triggers
from businessimpactmodulation import Businessimpactmodulation, Businessimpactmodulations
from macromodulation import MacroModulation, MacroModulations

# from config import Config
