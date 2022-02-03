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

import sys
import cPickle
from cStringIO import StringIO


# Unpickle but strip and remove all __reduce__ things so we don't allow external code to be executed
# Code from Graphite::carbon project
class SafeUnpickler(object):
    PICKLE_SAFE = {
        'copy_reg'                                : set(['_reconstructor']),
        '__builtin__'                             : set(['object', 'set']),
        
        # Be sure to white list all we need to pickle.loads so user cannot exploit other modules (like bottle ^^)
        'shinken.acknowledge'                     : set(['Acknowledge']),
        'shinken.basemodule'                      : set(['BaseModule']),
        'shinken.borg'                            : set(['Borg']),
        'shinken.check'                           : set(['Check']),
        'shinken.brok'                            : set(['Brok']),
        'shinken.commandcall'                     : set(['CommandCall']),
        'shinken.comment'                         : set(['Comment']),
        'shinken.complexexpression'               : set(['ComplexExpressionNode']),
        'shinken.contactdowntime'                 : set(['ContactDowntime']),
        'shinken.daterange'                       : set(['Timerange',
                                                         'Daterange',
                                                         'CalendarDaterange',
                                                         'StandardDaterange',
                                                         'MonthWeekDayDaterange',
                                                         'MonthDateDaterange',
                                                         'WeekDayDaterange',
                                                         'MonthDayDaterange',
                                                         ]),
        'shinken.dependencynode'                  : set(['DependencyNode']),
        'shinken.downtime'                        : set(['Downtime']),
        'shinken.discovery.discoverymanager'      : set(['DiscoveredHost']),
        'shinken.eventhandler'                    : set(['EventHandler']),
        'shinken.external_command'                : set(['ExternalCommand']),
        'shinken.graph'                           : set(['Graph']),
        'shinken.message'                         : set(['Message']),
        'shinken.modulesctx'                      : set(['ModulesContext']),
        'shinken.modulesmanager'                  : set(['ModulesManager']),
        'shinken.notification'                    : set(['Notification']),
        'shinken.objects.command'                 : set(['DummyCommand', 'Command', 'Commands']),
        'shinken.objects.arbiterlink'             : set(['ArbiterLink', 'ArbiterLinks']),
        'shinken.objects.businessimpactmodulation': set(['Businessimpactmodulation', 'Businessimpactmodulations']),
        'shinken.objects.brokerlink'              : set(['BrokerLink', 'BrokerLinks']),
        'shinken.objects.checkmodulation'         : set(['CheckModulation', 'CheckModulations']),
        'shinken.objects.config'                  : set(['Config']),
        'shinken.objects.contact'                 : set(['Contact', 'Contacts']),
        'shinken.objects.contactgroup'            : set(['Contactgroup', 'Contactgroups']),
        'shinken.objects.discoveryrule'           : set(['Discoveryrule', 'Discoveryrules']),
        'shinken.objects.discoveryrun'            : set(['Discoveryrun', 'Discoveryruns']),
        'shinken.objects.escalation'              : set(['Escalation', 'Escalations']),
        'shinken.objects.hostdependency'          : set(['Hostdependency', 'Hostdependencies']),
        'shinken.objects.host'                    : set(['Host', 'Hosts']),
        'shinken.objects.hostescalation'          : set(['Hostescalation', 'Hostescalations']),
        'shinken.objects.itemgroup'               : set(['Itemgroup', 'Itemgroups']),
        'shinken.objects.hostgroup'               : set(['Hostgroup', 'Hostgroups']),
        'shinken.objects.hostextinfo'             : set(['HostExtInfo', 'HostsExtInfo']),
        'shinken.objects.item'                    : set(['Item', 'Items']),
        'shinken.objects.macromodulation'         : set(['MacroModulation', 'MacroModulations']),
        'shinken.objects.matchingitem'            : set(['MatchingItem']),
        'shinken.objects.pack'                    : set(['Pack', 'Packs']),
        'shinken.objects.notificationway'         : set(['NotificationWay', 'NotificationWays']),
        'shinken.objects.module'                  : set(['Module', 'Modules']),
        'shinken.objects.pollerlink'              : set(['PollerLink', 'PollerLinks']),
        'shinken.objects.reactionnerlink'         : set(['ReactionnerLink', 'ReactionnerLinks']),
        'shinken.objects.realm'                   : set(['Realm', 'Realms']),
        'shinken.objects.receiverlink'            : set(['ReceiverLink', 'ReceiverLinks']),
        'shinken.objects.resultmodulation'        : set(['Resultmodulation', 'Resultmodulations']),
        'shinken.objects.satellitelink'           : set(['SatelliteLink', 'SatelliteLinks']),
        'shinken.objects.schedulingitem'          : set(['SchedulingItem']),
        'shinken.objects.schedulerlink'           : set(['SchedulerLink', 'SchedulerLinks']),
        'shinken.objects.service'                 : set(['Service', 'Services']),
        'shinken.objects.servicedependency'       : set(['Servicedependency', 'Servicedependencies']),
        'shinken.objects.serviceescalation'       : set(['Serviceescalation', 'Serviceescalations']),
        'shinken.objects.serviceextinfo'          : set(['ServiceExtInfo', 'ServicesExtInfo']),
        'shinken.objects.servicegroup'            : set(['Servicegroup', 'Servicegroups']),
        'shinken.objects.timeperiod'              : set(['Timeperiod', 'Timeperiods']),
        'shinken.objects.trigger'                 : set(['Trigger', 'Triggers']),
        
    }
    
    
    @classmethod
    def find_class(cls, module, name):
        if module not in cls.PICKLE_SAFE:
            raise ValueError('Attempting to unpickle unsafe module %s' % module)
        __import__(module)
        mod = sys.modules[module]
        if name not in cls.PICKLE_SAFE[module]:
            raise ValueError('Attempting to unpickle unsafe class %s/%s' %
                             (module, name))
        return getattr(mod, name)
    
    
    @classmethod
    def loads(cls, pickle_string):
        pickle_obj = cPickle.Unpickler(StringIO(pickle_string))
        pickle_obj.find_global = cls.find_class
        return pickle_obj.load()
