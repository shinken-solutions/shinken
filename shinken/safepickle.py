# -*- coding: utf-8 -*-

# Copyright (C) 2009-2014:
#     Gabes Jean, naparuba@gmail.com
#     Gerhard Lausser, Gerhard.Lausser@consol.de
#     Gregory Starck, g.starck@gmail.com
#     Hartmut Goebel, h.goebel@goebel-consult.de
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

from __future__ import absolute_import, division, print_function, unicode_literals

import six
import sys
import io

# Unpickle but strip and remove all __reduce__ things
# so we don't allow external code to be executed
PICKLE_SAFE = {
    'copy_reg'                                : ['_reconstructor'],
    '__builtin__'                             : ['object', 'set'],
    'builtins'                                : ['object', 'set'],

    # Be sure to white list all we need to pickle.loads so user cannot exploit other modules (like bottle ^^)
    'shinken.acknowledge'                     : ['Acknowledge'],
    'shinken.basemodule'                      : ['BaseModule'],
    'shinken.borg'                            : ['Borg'],
    'shinken.check'                           : ['Check'],
    'shinken.brok'                            : ['Brok'],
    'shinken.commandcall'                     : ['CommandCall'],
    'shinken.comment'                         : ['Comment'],
    'shinken.complexexpression'               : ['ComplexExpressionNode'],
    'shinken.contactdowntime'                 : ['ContactDowntime'],
    'shinken.daterange'                       : ['Timerange',
                                                     'Daterange',
                                                     'CalendarDaterange',
                                                     'StandardDaterange',
                                                     'MonthWeekDayDaterange',
                                                     'MonthDateDaterange',
                                                     'WeekDayDaterange',
                                                     'MonthDayDaterange',
                                                     ],
    'shinken.dependencynode'                  : ['DependencyNode'],
    'shinken.downtime'                        : ['Downtime'],
    'shinken.discovery.discoverymanager'      : ['DiscoveredHost'],
    'shinken.eventhandler'                    : ['EventHandler'],
    'shinken.external_command'                : ['ExternalCommand'],
    'shinken.graph'                           : ['Graph'],
    'shinken.message'                         : ['Message'],
    'shinken.modulesctx'                      : ['ModulesContext'],
    'shinken.modulesmanager'                  : ['ModulesManager'],
    'shinken.notification'                    : ['Notification'],
    'shinken.objects.command'                 : ['DummyCommand', 'Command', 'Commands'],
    'shinken.objects.arbiterlink'             : ['ArbiterLink', 'ArbiterLinks'],
    'shinken.objects.businessimpactmodulation': ['Businessimpactmodulation', 'Businessimpactmodulations'],
    'shinken.objects.brokerlink'              : ['BrokerLink', 'BrokerLinks'],
    'shinken.objects.checkmodulation'         : ['CheckModulation', 'CheckModulations'],
    'shinken.objects.config'                  : ['Config'],
    'shinken.objects.contact'                 : ['Contact', 'Contacts'],
    'shinken.objects.contactgroup'            : ['Contactgroup', 'Contactgroups'],
    'shinken.objects.discoveryrule'           : ['Discoveryrule', 'Discoveryrules'],
    'shinken.objects.discoveryrun'            : ['Discoveryrun', 'Discoveryruns'],
    'shinken.objects.escalation'              : ['Escalation', 'Escalations'],
    'shinken.objects.hostdependency'          : ['Hostdependency', 'Hostdependencies'],
    'shinken.objects.host'                    : ['Host', 'Hosts'],
    'shinken.objects.hostescalation'          : ['Hostescalation', 'Hostescalations'],
    'shinken.objects.itemgroup'               : ['Itemgroup', 'Itemgroups'],
    'shinken.objects.hostgroup'               : ['Hostgroup', 'Hostgroups'],
    'shinken.objects.hostextinfo'             : ['HostExtInfo', 'HostsExtInfo'],
    'shinken.objects.item'                    : ['Item', 'Items'],
    'shinken.objects.macromodulation'         : ['MacroModulation', 'MacroModulations'],
    'shinken.objects.matchingitem'            : ['MatchingItem'],
    'shinken.objects.pack'                    : ['Pack', 'Packs'],
    'shinken.objects.notificationway'         : ['NotificationWay', 'NotificationWays'],
    'shinken.objects.module'                  : ['Module', 'Modules'],
    'shinken.objects.pollerlink'              : ['PollerLink', 'PollerLinks'],
    'shinken.objects.reactionnerlink'         : ['ReactionnerLink', 'ReactionnerLinks'],
    'shinken.objects.realm'                   : ['Realm', 'Realms'],
    'shinken.objects.receiverlink'            : ['ReceiverLink', 'ReceiverLinks'],
    'shinken.objects.resultmodulation'        : ['Resultmodulation', 'Resultmodulations'],
    'shinken.objects.satellitelink'           : ['SatelliteLink', 'SatelliteLinks'],
    'shinken.objects.schedulingitem'          : ['SchedulingItem'],
    'shinken.objects.schedulerlink'           : ['SchedulerLink', 'SchedulerLinks'],
    'shinken.objects.service'                 : ['Service', 'Services'],
    'shinken.objects.servicedependency'       : ['Servicedependency', 'Servicedependencies'],
    'shinken.objects.serviceescalation'       : ['Serviceescalation', 'Serviceescalations'],
    'shinken.objects.serviceextinfo'          : ['ServiceExtInfo', 'ServicesExtInfo'],
    'shinken.objects.servicegroup'            : ['Servicegroup', 'Servicegroups'],
    'shinken.objects.timeperiod'              : ['Timeperiod', 'Timeperiods'],
    'shinken.objects.trigger'                 : ['Trigger', 'Triggers'],

}


def find_class(module, name):
    if module not in PICKLE_SAFE:
        raise ValueError('Attempting to unpickle unsafe module %s' % module)
    __import__(module)
    mod = sys.modules[module]
    if name not in PICKLE_SAFE[module]:
        raise ValueError('Attempting to unpickle unsafe class %s/%s' %
                         (module, name))
    return getattr(mod, name)


if six.PY2:
    # This is a dirty hack for python2 as it's impossible to subclass
    # Unpickler from the cPickle module.
    # This implementation mimics the Unpickler interface but use an external
    # Unpickler instance
    import cPickle

    class SafeUnpickler(object):

        def __init__(self, _bytes):
            self._bytes = _bytes

        def load(self):
            pickle_obj = cPickle.Unpickler(self._bytes)
            pickle_obj.find_global = find_class
            return pickle_obj.load()
else:
    import pickle

    class SafeUnpickler(pickle.Unpickler):

        find_class = staticmethod(find_class)
