#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
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

# This Class is an example of an Scheduler module
# Here for the configuration phase AND running one

import re

from shinken.objects import Timeperiod, Timeperiods
from shinken.objects import Service, Services
from shinken.objects import Host, Hosts
from shinken.objects import Contact, Contacts
from shinken.comment import Comment
from shinken.downtime import Downtime
from shinken.basemodule import BaseModule
from shinken.util import to_bool
from shinken.log import logger

properties = {
    'daemons': ['scheduler'],
    'type': 'nagios_retention_file',
    'external': False,
}


# called by the plugin manager to get a broker
def get_instance(plugin):
    logger.info('Get a Nagios3 retention scheduler module for plugin %s' % (plugin.get_name()))
    path = plugin.path
    instance = Nagios_retention_scheduler(plugin, path)
    return instance


# Just print some stuff
class Nagios_retention_scheduler(BaseModule):
    def __init__(self, mod_conf, path):
        BaseModule.__init__(self, mod_conf)
        self.path = path

    # Ok, main function that is called in the retention creation pass
    def hook_save_retention(self, daemon):
        logger.info("[NagiosRetention] asking me to update the retention objects, but I won't do it.")

    def _cut_line(self, line):
        #punct = '"#$%&\'()*+/<=>?@[\\]^`{|}~'
        tmp = re.split("=", line)
        r = [elt for elt in tmp if elt != '']
        return r

    def read_retention_buf(self, buf):
        params = []
        objectscfg = {'void': [],
                      'timeperiod': [],
                      'command': [],
                      'contactgroup': [],
                      'hostgroup': [],
                      'contact': [],
                      'notificationway': [],
                      'host': [],
                      'service': [],
                      'servicegroup': [],
                      'servicedependency': [],
                      'hostdependency': [],
                      'hostcomment': [],
                      'hostdowntime': [],
                      'servicecomment': [],
                      'servicedowntime': [],
                      }
        tmp = []
        tmp_type = 'void'
        in_define = False
        continuation_line = False
        tmp_line = ''
        lines = buf.split('\n')
        for line in lines:
            line = line.decode('utf8', 'ignore')
            line = line.split(';')[0]
            # A backslash means, there is more to come
            if re.search("\\\s*$", line):
                continuation_line = True
                line = re.sub("\\\s*$", "", line)
                line = re.sub("^\s+", " ", line)
                tmp_line += line
                continue
            elif continuation_line:
                # Now the continuation line is complete
                line = re.sub("^\s+", "", line)
                line = tmp_line + line
                tmp_line = ''
                continuation_line = False
            if re.search("}", line):
                in_define = False
            if re.search("^\s*\t*#|^\s*$|^\s*}", line):
                pass

            # A define must be catch and the type save
            # The old entry must be save before
            elif re.search("{$", line):
                in_define = True
                if tmp_type not in objectscfg:
                    objectscfg[tmp_type] = []
                objectscfg[tmp_type].append(tmp)
                tmp = []
                # Get new type
                elts = re.split('\s', line)
                tmp_type = elts[0]
                #tmp_type = tmp_type.split('{')[0]
                #print "TMP type", tmp_type
            else:
                if in_define:
                    tmp.append(line)
                else:
                    params.append(line)

        objectscfg[tmp_type].append(tmp)
        objects = {}

        #print "Loaded", objectscfg

        for type in objectscfg:
            objects[type] = []
            for items in objectscfg[type]:
                tmp = {}
                for line in items:
                    elts = self._cut_line(line)
                    if elts != []:
                        prop = elts[0]
                        value = ' '.join(elts[1:])
                        tmp[prop] = value
                if tmp != {}:
                    objects[type].append(tmp)

        return objects

    # We've got raw objects in string, now create real Instances
    def create_objects(self, raw_objects, types_creations):
        all_obj = {}
        for t in types_creations:
            all_obj[t] = self.create_objects_for_type(raw_objects, t, types_creations)
        return all_obj

    def pythonize_running(self, obj, obj_cfg):
        cls = obj.__class__
        running_properties = cls.running_properties
        for prop, entry in running_properties.items():
            if hasattr(obj, prop) and prop in obj_cfg:
                #if 'pythonize' in entry:
                f = entry.pythonize
                if f is not None:  # mean it's a string
                    #print "Apply", f, "to the property", prop, "for ", cls.my_type
                    val = getattr(obj, prop)
                    val = f(val)
                    setattr(obj, prop, val)
                else:  # no pythonize, int by default
                    # if cls.my_type != 'service':
                    #  print "Intify", prop, getattr(obj, prop)
                    if prop != 'state_type':
                        val = int(getattr(obj, prop))
                        setattr(obj, prop, val)
                    else:  # state type is a int, but should be set HARd or SOFT
                        val = int(getattr(obj, prop))
                        if val == 1:
                            setattr(obj, prop, 'HARD')
                        else:
                            setattr(obj, prop, 'SOFT')

    def create_objects_for_type(self, raw_objects, type, types_creations):
        t = type
        # Ex: the above code do for timeperiods:
        # timeperiods = []
        # for timeperiodcfg in objects['timeperiod']:
        #    t = Timeperiod(timeperiodcfg)
        #    t.clean()
        #    timeperiods.append(t)
        #self.timeperiods = Timeperiods(timeperiods)

        (cls, clss, prop) = types_creations[t]
        # List where we put objects
        lst = []
        for obj_cfg in raw_objects[t]:
            # We create the object
            # print "Create obj", obj_cfg
            o = cls(obj_cfg)
            o.clean()
            if t in self.property_mapping:
                entry = self.property_mapping[t]
                for (old, new) in entry:
                    value = getattr(o, old)
                    setattr(o, new, value)
                    delattr(o, old)
                    obj_cfg[new] = obj_cfg[old]
                    del obj_cfg[old]
            o.pythonize()
            self.pythonize_running(o, obj_cfg)
            lst.append(o)
        #print "Got", lst
        # we create the objects Class and we set it in prop
        #setattr(self, prop, clss(lst))
        #print "Object?", clss(lst)
        return clss(lst)

    def create_and_link_comments(self, raw_objects, all_obj):
        # first service
        for obj_cfg in raw_objects['servicecomment']:
            #print "Managing", obj_cfg
            host_name = obj_cfg['host_name']
            service_description = obj_cfg['service_description']
            srv = all_obj['service'].find_srv_by_name_and_hostname(host_name, service_description)
            #print "Find my service", srv
            if srv is not None:
                cmd = Comment(srv, to_bool(obj_cfg['persistent']), obj_cfg['author'], obj_cfg['comment_data'], 1, int(obj_cfg['entry_type']), int(obj_cfg['source']), to_bool(obj_cfg['expires']), int(obj_cfg['expire_time']))
                #print "Created cmd", cmd
                srv.add_comment(cmd)

        # then hosts
        for obj_cfg in raw_objects['hostcomment']:
            #print "Managing", obj_cfg
            host_name = obj_cfg['host_name']
            hst = all_obj['host'].find_by_name(host_name)
            #print "Find my host", hst
            if hst is not None:
                cmd = Comment(hst, to_bool(obj_cfg['persistent']), obj_cfg['author'], obj_cfg['comment_data'], 1, int(obj_cfg['entry_type']), int(obj_cfg['source']), to_bool(obj_cfg['expires']), int(obj_cfg['expire_time']))
                #print "Created cmd", cmd
                hst.add_comment(cmd)

    def create_and_link_downtimes(self, raw_objects, all_obj):
        # first service
        for obj_cfg in raw_objects['servicedowntime']:
            #print "Managing", obj_cfg
            host_name = obj_cfg['host_name']
            service_description = obj_cfg['service_description']
            srv = all_obj['service'].find_srv_by_name_and_hostname(host_name, service_description)
            #print "Find my service", srv
            if srv is not None:
                dwn = Downtime(srv, int(obj_cfg['start_time']), int(obj_cfg['end_time']), to_bool(obj_cfg['fixed']), int(obj_cfg['triggered_by']), int(obj_cfg['duration']), obj_cfg['author'], obj_cfg['comment'])
                #print "Created dwn", dwn
                srv.add_downtime(dwn)

        # then hosts
        for obj_cfg in raw_objects['hostdowntime']:
            #print "Managing", obj_cfg
            host_name = obj_cfg['host_name']
            hst = all_obj['host'].find_by_name(host_name)
            #print "Find my host", hst
            if hst is not None:
                dwn = Downtime(hst, int(obj_cfg['start_time']), int(obj_cfg['end_time']), to_bool(obj_cfg['fixed']), int(obj_cfg['triggered_by']), int(obj_cfg['duration']), obj_cfg['author'], obj_cfg['comment'])
                #print "Created dwn", dwn
                hst.add_downtime(dwn)

    # Should return if it succeed in the retention load or not
    def hook_load_retention(self, sched):
        logger.info("[NagiosRetention] asking me to load the retention file")

        # Now the old flat file way :(
        logger.info('[NagiosRetention]Reading from retention_file %s' % (self.path))
        try:
            f = open(self.path)
            buf = f.read()
            f.close()
        except EOFError, exp:
            logger.error('Failed to load retention file %s with error %s' % (self.path,exp))
            return False
        except ValueError, exp:
            logger.error('ValueError reading the retention file with error %s' % (exp))
            return False
        except IOError, exp:
            logger.error('IOError reading the retention file with error %s' % (exp))
            return False
        except IndexError, exp:
            s = "Sorry, the ressource file is not compatible"
            logger.error(s)
            return False
        except TypeError, exp:
            s = "Sorry, the ressource file is not compatible"
            logger.warning(s)
            return False
        logger.info('[NagiosRetention]Finished trying to load retention_file %s' % (self.path))

        raw_objects = self.read_retention_buf(buf)

        types_creations = {'timeperiod': (Timeperiod, Timeperiods, 'timeperiods'),
                   'service': (Service, Services, 'services'),
                   'host': (Host, Hosts, 'hosts'),
                   'contact': (Contact, Contacts, 'contacts'),
                   }

        self.property_mapping = {
            'service': [('current_attempt', 'attempt'), ('current_state', 'state_type_id'),
                         ('plugin_output', 'output'), ('last_check', 'last_chk'),
                         ('performance_data', 'perf_data'), ('next_check', 'next_chk'),
                         ('long_plugin_output', 'long_output'), ('check_execution_time', 'execution_time'),
                         ('check_latency', 'latency')],
            'host': [('current_attempt', 'attempt'), ('current_state', 'state_type_id'),
                      ('plugin_output', 'output'), ('last_check', 'last_chk'),
                 ('performance_data', 'perf_data'), ('next_check', 'next_chk'),
                      ('long_plugin_output', 'long_output'), ('check_execution_time', 'execution_time'),
                      ('check_latency', 'latency')],
            }

        all_obj = self.create_objects(raw_objects, types_creations)

        logger.info('Received all obj %s' % (all_obj))

        self.create_and_link_comments(raw_objects, all_obj)

        self.create_and_link_downtimes(raw_objects, all_obj)

        # Taken from the scheduler code... sorry
        all_data = {'hosts': {}, 'services': {}}
        for h in all_obj['host']:
            d = {}
            running_properties = h.__class__.running_properties
            for prop, entry in running_properties.items():
                if entry.retention:
                    d[prop] = getattr(h, prop)
            all_data['hosts'][h.host_name] = d

        # Now same for services
        for s in all_obj['service']:
            d = {}
            running_properties = s.__class__.running_properties
            for prop, entry in running_properties.items():
                if entry.retention:
                    d[prop] = getattr(s, prop)
            all_data['services'][(s.host_name, s.service_description)] = d
        #all_data = {'hosts': {}, 'services': {}}

        sched.restore_retention_data(all_data)
        log_mgr.log("[NagiosRetention] OK we've load data from retention file")

        return True
