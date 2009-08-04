#!/usr/bin/python
#Copyright (C) 2009 Gabes Jean, naparuba@gmail.com
#
#This file is part of Shinken.
#
#Shinken is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Shinken is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with Shinken.  If not, see <http://www.gnu.org/licenses/>.


import os, time
from util import to_int, to_char, to_split, to_bool
from downtime import Downtime

class ExternalCommand:

    commands = {
        'CHANGE_CONTACT_MODSATTR' : {'global' : True, 'args' : ['contact', None]},
        'CHANGE_CONTACT_MODHATTR' : {'global' : True, 'args' : ['contact', None]},
        'CHANGE_CONTACT_MODATTR' : {'global' : True, 'args' : ['contact', None]},
        'CHANGE_CONTACT_HOST_NOTIFICATION_TIMEPERIOD' : {'global' : False, 'args' : ['contact', 'time_period']},
        'ADD_SVC_COMMENT'  : {'global' : False, 'args' : ['service', 'to_bool', 'author', None]},
        'ADD_HOST_COMMENT' : {'global' : False, 'args' : ['host', 'to_bool', 'author', None]},
        'ACKNOWLEDGE_SVC_PROBLEM' : {'global' : False, 'args' : ['service' , 'to_bool', 'to_bool', 'to_bool', 'author', None]},
        'ACKNOWLEDGE_HOST_PROBLEM' : {'global' : False, 'args' : ['host', 'to_bool', 'to_bool', 'to_bool', 'author', None]},
        'CHANGE_CONTACT_SVC_NOTIFICATION_TIMEPERIOD' : {'global' : True, 'args' : ['contact', 'time_period']},
        'CHANGE_CUSTOM_CONTACT_VAR' : {'global' : True, 'args' : ['contact', None,None]},
        'CHANGE_CUSTOM_HOST_VAR' : {'global' : False, 'args' : ['host', None,None]},
        'CHANGE_CUSTOM_SVC_VAR' : {'global' : False, 'args' : ['service', None,None]},
        'CHANGE_GLOBAL_HOST_EVENT_HANDLER' : {'global' : True, 'args' : ['command']},
        'CHANGE_GLOBAL_SVC_EVENT_HANDLER' : {'global' : True, 'args' : ['command']},
        'CHANGE_HOST_CHECK_COMMAND' : {'global' : False, 'args' : ['host', 'command']},
        'CHANGE_HOST_CHECK_TIMEPERIOD' : {'global' : False, 'args' : ['host', 'time_period']},
        'CHANGE_HOST_CHECK_TIMEPERIOD' : {'global' : False, 'args' : ['host', 'time_period']},
        'CHANGE_HOST_EVENT_HANDLER' : {'global' : False, 'args' : ['host', 'command']},
        'CHANGE_HOST_MODATTR' : {'global' : False, 'args' : ['host', 'to_int']},
        'CHANGE_MAX_HOST_CHECK_ATTEMPTS': {'global' : False, 'args' : ['host', 'to_int']},
        'CHANGE_MAX_SVC_CHECK_ATTEMPTS' : {'global' : False, 'args' : ['service', 'to_int']},
        'CHANGE_NORMAL_HOST_CHECK_INTERVAL' : {'global' : False, 'args' : ['host', 'to_int']},
        'CHANGE_NORMAL_SVC_CHECK_INTERVAL' : {'global' : False, 'args' : ['service', 'to_int']},
        'CHANGE_RETRY_HOST_CHECK_INTERVAL' : {'global' : False, 'args' : ['service', 'to_int']},
        'CHANGE_RETRY_SVC_CHECK_INTERVAL' : {'global' : False, 'args' : ['service', 'to_int']},
        'CHANGE_SVC_CHECK_COMMAND' : {'global' : False, 'args' : ['service', 'command']},
        'CHANGE_SVC_CHECK_TIMEPERIOD' : {'global' : False, 'args' : ['service', 'time_period']},
        'CHANGE_SVC_EVENT_HANDLER' : {'global' : False, 'args' : ['service', 'command']},
        'CHANGE_SVC_MODATTR' : {'global' : False, 'args' : ['service', 'to_int']},
        'CHANGE_SVC_NOTIFICATION_TIMEPERIOD' : {'global' : False, 'args' : ['service', 'time_period']},
        'DELAY_HOST_NOTIFICATION' : {'global' : False, 'args' : ['host', 'to_int']},
        'DELAY_SVC_NOTIFICATION' : {'global' : False, 'args' : ['service', 'to_int']},
        'DEL_ALL_HOST_COMMENTS' : {'global' : False, 'args' : ['host']},
        'DEL_ALL_SVC_COMMENTS' : {'global' : False, 'args' : ['service']},
        'DEL_HOST_COMMENT' : {'global' : True, 'args' : ['to_int']},
        'DEL_HOST_DOWNTIME' : {'global' : True, 'args' : ['to_int']},
        'DEL_SVC_COMMENT' : {'global' : True, 'args' : ['to_int']},
        'DEL_SVC_DOWNTIME' : {'global' : True, 'args' : ['to_int']},
        'DISABLE_ALL_NOTIFICATIONS_BEYOND_HOST' : {'global' : False, 'args' : ['host']},
        'DISABLE_CONTACTGROUP_HOST_NOTIFICATIONS' : {'global' : True, 'args' : ['contact_group']},
        'DISABLE_CONTACTGROUP_SVC_NOTIFICATIONS' : {'global' : True, 'args' : ['contact_group']},
        'DISABLE_CONTACT_HOST_NOTIFICATIONS' : {'global' : True, 'args' : ['contact']},
        'DISABLE_CONTACT_SVC_NOTIFICATIONS' : {'global' : True, 'args' : ['contact']},
        'DISABLE_EVENT_HANDLERS' : {'global' : True, 'args' : []},
        'DISABLE_FAILURE_PREDICTION' : {'global' : True, 'args' : []},
        'DISABLE_FLAP_DETECTION' : {'global' : True, 'args' : []},
        'DISABLE_HOSTGROUP_HOST_CHECKS' : {'global' : True, 'args' : ['host_group']},
        'DISABLE_HOSTGROUP_HOST_NOTIFICATIONS' : {'global' : True, 'args' : ['host_group']},
        'DISABLE_HOSTGROUP_PASSIVE_HOST_CHECKS' : {'global' : True, 'args' : ['host_group']},
        'DISABLE_HOSTGROUP_PASSIVE_SVC_CHECKS' : {'global' : True, 'args' : ['host_group']},
        'DISABLE_HOSTGROUP_SVC_CHECKS' : {'global' : True, 'args' : ['host_group']},
        'DISABLE_HOSTGROUP_SVC_NOTIFICATIONS' : {'global' : True, 'args' : ['host_group']},
        'DISABLE_HOST_AND_CHILD_NOTIFICATIONS' : {'global' : False, 'args' : ['host']},
        'DISABLE_HOST_CHECK' : {'global' : False, 'args' : ['host']},
        'DISABLE_HOST_EVENT_HANDLER' : {'global' : False, 'args' : ['host']},
        'DISABLE_HOST_FLAP_DETECTION' : {'global' : False, 'args' : ['host']},
        'DISABLE_HOST_FRESHNESS_CHECKS' : {'global' : True, 'args' : []},
        'DISABLE_HOST_NOTIFICATIONS' : {'global' : False, 'args' : ['host']},
        'DISABLE_HOST_SVC_CHECKS' : {'global' : False, 'args' : ['host']},
        'DISABLE_HOST_SVC_NOTIFICATIONS' : {'global' : False, 'args' : ['host']},
        'DISABLE_NOTIFICATIONS' : {'global' : True, 'args' : []},
        'DISABLE_PASSIVE_HOST_CHECKS' : {'global' : False, 'args' : ['host']},
        'DISABLE_PASSIVE_SVC_CHECKS' : {'global' : False, 'args' : ['service']},
        'DISABLE_PERFORMANCE_DATA' : {'global' : True, 'args' : []},
        'DISABLE_SERVICEGROUP_HOST_CHECKS' : {'global' : True, 'args' : ['service_group']},
        'DISABLE_SERVICEGROUP_HOST_NOTIFICATIONS' : {'global' : True, 'args' : ['service_group']},
        'DISABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS' : {'global' : True, 'args' : ['service_group']},
        'DISABLE_SERVICEGROUP_PASSIVE_SVC_CHECKS' : {'global' : True, 'args' : ['service_group']},
        'DISABLE_SERVICEGROUP_SVC_CHECKS' : {'global' : True, 'args' : ['service_group']},
        'DISABLE_SERVICEGROUP_SVC_NOTIFICATIONS' : {'global' : True, 'args' : ['service_group']},
        'DISABLE_SERVICE_FLAP_DETECTION' : {'global' : False, 'args' : ['service']},
        'DISABLE_SERVICE_FRESHNESS_CHECKS' : {'global' : True, 'args' : []},
        'DISABLE_SVC_CHECK' : {'global' : False, 'args' : ['service']},
        'DISABLE_SVC_EVENT_HANDLER' : {'global' : False, 'args' : ['service']},
        'DISABLE_SVC_FLAP_DETECTION' : {'global' : False, 'args' : ['service']},
        'DISABLE_SVC_NOTIFICATIONS' : {'global' : False, 'args' : ['service']},
        'ENABLE_ALL_NOTIFICATIONS_BEYOND_HOST' : {'global' : False, 'args' : ['host']},
        'ENABLE_CONTACTGROUP_HOST_NOTIFICATIONS' : {'global' : True, 'args' : ['contact_group']},
        'ENABLE_CONTACTGROUP_SVC_NOTIFICATIONS' : {'global' : True, 'args' : ['contact_group']},
        'ENABLE_CONTACT_HOST_NOTIFICATIONS' : {'global' : True, 'args' : ['contact']},
        'ENABLE_CONTACT_SVC_NOTIFICATIONS' : {'global' : True, 'args' : ['contact']},
        'ENABLE_EVENT_HANDLERS' : {'global' : True, 'args' : []},
        'ENABLE_FAILURE_PREDICTION' : {'global' : True, 'args' : []},
        'ENABLE_FLAP_DETECTION' : {'global' : True, 'args' : []},
        'ENABLE_HOSTGROUP_HOST_CHECKS' : {'global' : True, 'args' : ['host_group']},
        'ENABLE_HOSTGROUP_HOST_NOTIFICATIONS' : {'global' : True, 'args' : ['host_group']},
        'ENABLE_HOSTGROUP_PASSIVE_HOST_CHECKS' : {'global' : True, 'args' : ['host_group']},
        'ENABLE_HOSTGROUP_PASSIVE_SVC_CHECKS' : {'global' : True, 'args' : ['host_group']},
        'ENABLE_HOSTGROUP_SVC_CHECKS' : {'global' : True, 'args' : ['host_group']},
        'ENABLE_HOSTGROUP_SVC_NOTIFICATIONS' : {'global' : True, 'args' : ['host_group']},
        'ENABLE_HOST_AND_CHILD_NOTIFICATIONS' : {'global' : False, 'args' : ['host']},
        'ENABLE_HOST_CHECK' : {'global' : False, 'args' : ['host']},
        'ENABLE_HOST_EVENT_HANDLER' : {'global' : False, 'args' : ['host']},
        'ENABLE_HOST_FLAP_DETECTION' : {'global' : False, 'args' : ['host']},
        'ENABLE_HOST_FRESHNESS_CHECKS' : {'global' : True, 'args' : []},
        'ENABLE_HOST_NOTIFICATIONS' : {'global' : False, 'args' : ['host']},
        'ENABLE_HOST_SVC_CHECKS' : {'global' : False, 'args' : ['host']},
        'ENABLE_HOST_SVC_NOTIFICATIONS' : {'global' : False, 'args' : ['host']},
        'ENABLE_NOTIFICATIONS' : {'global' : True, 'args' : []},
        'ENABLE_PASSIVE_HOST_CHECKS' : {'global' : False, 'args' : ['host']},
        'ENABLE_PASSIVE_SVC_CHECKS' : {'global' : False, 'args' : ['service']},
        'ENABLE_PERFORMANCE_DATA' : {'global' : True, 'args' : []},
        'ENABLE_SERVICEGROUP_HOST_CHECKS' : {'global' : True, 'args' : ['service_group']},
        'ENABLE_SERVICEGROUP_HOST_NOTIFICATIONS' : {'global' : True, 'args' : ['service_group']},
        'ENABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS' : {'global' : True, 'args' : ['service_group']},
        'ENABLE_SERVICEGROUP_PASSIVE_SVC_CHECKS' : {'global' : True, 'args' : ['service_group']},
        'ENABLE_SERVICEGROUP_SVC_CHECKS' : {'global' : True, 'args' : ['service_group']},
        'ENABLE_SERVICEGROUP_SVC_NOTIFICATIONS' : {'global' : True, 'args' : ['service_group']},
        'ENABLE_SERVICE_FRESHNESS_CHECKS' : {'global' : True, 'args' : []},
        'ENABLE_SVC_CHECK': {'global' : False, 'args' : ['service']},
        'ENABLE_SVC_EVENT_HANDLER' : {'global' : False, 'args' : ['service']},
        'ENABLE_SVC_FLAP_DETECTION' : {'global' : False, 'args' : ['service']},
        'ENABLE_SVC_NOTIFICATIONS' : {'global' : False, 'args' : ['service']},
        'PROCESS_FILE' : {'global' : True, 'args' : [None, 'to_bool']},
        'PROCESS_HOST_CHECK_RESULT' : {'global' : False, 'args' : ['host', 'to_int', None]},
        'PROCESS_SERVICE_CHECK_RESULT' : {'global' : False, 'args' : ['service', 'to_int', None]},
        'READ_STATE_INFORMATION' : {'global' : True, 'args' : []},
        'REMOVE_HOST_ACKNOWLEDGEMENT' : {'global' : False, 'args' : ['host']},
        'REMOVE_SVC_ACKNOWLEDGEMENT' : {'global' : False, 'args' : ['service']},
        'RESTART_PROGRAM' : {'global' : True, 'args' : []},
        'SAVE_STATE_INFORMATION' : {'global' : True, 'args' : []},
        'SCHEDULE_AND_PROPAGATE_HOST_DOWNTIME' : {'global' : False, 'args' : ['host', 'to_int', 'to_int', 'to_bool', 'to_int', 'to_int', 'author',None]},
        'SCHEDULE_AND_PROPAGATE_TRIGGERED_HOST_DOWNTIME' : {'global' : False, 'args' : ['host', 'to_int', 'to_int', 'to_bool', 'to_int', 'to_int', 'author', None]},
        'SCHEDULE_FORCED_HOST_CHECK' : {'global' : False, 'args' : ['host', 'to_int']},
        'SCHEDULE_FORCED_HOST_SVC_CHECKS' : {'global' : False, 'args' : ['host', 'to_int']},
        'SCHEDULE_FORCED_SVC_CHECK' : {'global' : False, 'args' : ['service', 'to_int']},
        'SCHEDULE_HOSTGROUP_HOST_DOWNTIME' : {'global' : True, 'args' : ['host_group', 'to_int', 'to_int', 'to_bool', 'to_int', 'to_int', 'author',None]},
        'SCHEDULE_HOSTGROUP_SVC_DOWNTIME' : {'global' : True, 'args' : ['host_group', 'to_int', 'to_int', 'to_bool', 'to_int', 'to_int', 'author',None]},
        'SCHEDULE_HOST_CHECK' : {'global' : False, 'args' : ['host', 'to_int']},
        'SCHEDULE_HOST_DOWNTIME' : {'global' : False, 'args' : ['host', 'to_int', 'to_int', 'to_bool', 'to_int', 'to_int', 'author', None]},
        'SCHEDULE_HOST_SVC_CHECKS' : {'global' : False, 'args' : ['host', 'to_int']},
        'SCHEDULE_HOST_SVC_DOWNTIME' : {'global' : False, 'args' : ['host', 'to_int', 'to_int', 'to_bool', 'to_int', 'to_int', 'author', None]},
        'SCHEDULE_SERVICEGROUP_HOST_DOWNTIME' : {'global' : True, 'args' : ['service_group', 'to_int', 'to_int', 'to_bool', 'to_int', 'to_int', 'author', None]},
        'SCHEDULE_SERVICEGROUP_SVC_DOWNTIME' : {'global' : True, 'args' : ['service_group', 'to_int', 'to_int', 'to_bool', 'to_int', 'to_int', 'author', None]},
        'SCHEDULE_SVC_CHECK' : {'global' : False, 'args' : ['service', 'to_int']},
        'SCHEDULE_SVC_DOWNTIME' : {'global' : False, 'args' : ['service', 'to_int', 'to_int', 'to_bool', 'to_int', 'to_int', 'author', None]},
        'SEND_CUSTOM_HOST_NOTIFICATION' : {'global' : False, 'args' : ['host', 'to_int', 'author', None]},
        'SEND_CUSTOM_SVC_NOTIFICATION' : {'global' : False, 'args' : ['service', 'to_int', 'author', None]},
        'SET_HOST_NOTIFICATION_NUMBER' : {'global' : False, 'args' : ['host', 'to_int']},
        'SET_SVC_NOTIFICATION_NUMBER' : {'global' : False, 'args' : ['service', 'to_int']},
        'SHUTDOWN_PROGRAM' : {'global' : True, 'args' : []},
        'START_ACCEPTING_PASSIVE_HOST_CHECKS' : {'global' : True, 'args' : []},
        'START_ACCEPTING_PASSIVE_SVC_CHECKS' : {'global' : True, 'args' : []},
        'START_EXECUTING_HOST_CHECKS' : {'global' : True, 'args' : []},
        'START_EXECUTING_SVC_CHECKS' : {'global' : True, 'args' : []},
        'START_OBSESSING_OVER_HOST' : {'global' : False, 'args' : ['host']},
        'START_OBSESSING_OVER_HOST_CHECKS' : {'global' : True, 'args' : []},
        'START_OBSESSING_OVER_SVC' : {'global' : False, 'args' : ['service']},
        'start_OBSESSING_OVER_SVC_CHECKS' : {'global' : True, 'args' : []},
        'STOP_ACCEPTING_PASSIVE_HOST_CHECKS' : {'global' : True, 'args' : []},
        'STOP_ACCEPTING_PASSIVE_SVC_CHECKS' : {'global' : True, 'args' : []},
        'STOP_EXECUTING_HOST_CHECKS' : {'global' : True, 'args' : []},
        'STOP_EXECUTING_SVC_CHECKS' : {'global' : True, 'args' : []},
        'STOP_OBSESSING_OVER_HOST' : {'global' : False, 'args' : ['host']},
        'STOP_OBSESSING_OVER_HOST_CHECKS' : {'global' : True, 'args' : []},
        'STOP_OBSESSING_OVER_SVC' : {'global' : False, 'args' : ['service']},
        'STOP_OBSESSING_OVER_SVC_CHECKS' : {'global' : True, 'args' : []}
    }

    
    def __init__(self, conf, mode):
        self.mode = mode
        self.conf = conf
        self.hosts = conf.hosts
        self.services = conf.services
        self.contacts = conf.contacts
        self.hostgroups = conf.hostgroups
        self.commands = conf.commands
        self.servicegroups = conf.servicegroups
        self.contactgroups = conf.contactgroups
        self.timeperiods = conf.timeperiods
        self.pipe_path = '/tmp/my_fifo'
        self.fifo = None
        if self.mode == 'dispatcher':
            self.confs = conf.confs


    def load_scheduler(self, scheduler):
        self.sched = scheduler


    def open(self):
        #At the first open del and create the fifo
        if self.fifo == None:
            if os.path.exists(self.pipe_path):
                os.unlink(self.pipe_path)
                
            if not os.path.exists(self.pipe_path):
                os.umask(0)
                os.mkfifo(self.pipe_path, 0660)
                open(self.pipe_path, 'w+', os.O_NONBLOCK)
        self.fifo = os.open(self.pipe_path, os.O_NONBLOCK)
        #print 'Fifo:', self.fifo
        return self.fifo

    
    def read_and_interpret(self):
        buf = os.read(self.fifo, 8096)
        os.close(self.fifo)
        if buf != '':
            self.resolve_command(buf)

    
    def resolve_command(self, command):
        self.get_command_and_args(command)


    def search_host_and_dispatch(self, host_name, command):
        for cfg in self.confs.values():
            if cfg.hosts.find_by_name(host_name) is not None:
                print "Host", host_name, "found in a configuration"
                if cfg.is_assigned :
                    sched = cfg.assigned_to
                    sched.run_external_command(command)
                else:
                    print "Problem: a configuration is found, but is not assigned!"
            
    def dispatch_global_command(self, command):
        for sched in self.conf.schedulerlinks:
            print "Sending command", command, 'to sched', sched
            if sched.is_active:
                sched.run_external_command(command)


    #We need to get the first part, the command name
    def get_command_and_args(self, command):
        print "Trying to resolve", command
        if command[-1] == '\n':
            command = command[:-1]
        elts = command.split(';')
        part1 = elts[0]
        
        elts2 = part1.split(' ')
        print "Elts2:", elts2
        if len(elts2) != 2:
            print "Malformed command", command
            return None
        c_name = elts2[1]
        
        print "Get command name", c_name
        if c_name not in ExternalCommand.commands:
            print "This command is not recognized, sorry"
            return None

        if self.mode == 'dispatcher' and ExternalCommand.commands[c_name]['global']:
            print "This command is a global one, we resent it to all schedulers"
            self.dispatch_global_command(command)
            return None
        print "This command have arguments:", ExternalCommand.commands[c_name]['args'], len(ExternalCommand.commands[c_name]['args'])

        

        args = []
        i = 1
        in_service = False
        tmp_host = ''
        try:
            for elt in elts[1:]:
                print "Searching for a new arg:", elt, i
                val = elts[i].strip()
                if val[-1] == '\n':
                    val = val[:-1]

                print "For command arg", val

                if not in_service:                    
                    type_searched = ExternalCommand.commands[c_name]['args'][i-1]
                    print "Search for a arg", type_searched
                    
                    if type_searched == 'host':
                        if self.mode == 'dispatcher':
                            self.search_host_and_dispatch(val, command)
                            return None
                        h = self.hosts.find_by_name(val)
                        if h is not None:
                            args.append(h)

                    elif type_searched == 'contact':
                        c = self.contacts.find_by_name(val)
                        if c is not None:
                            args.append(c)

                    elif type_searched == 'time_period':
                        t = self.timeperiods.find_by_name(val)
                        if t is not None:
                            args.append(t)

                    elif type_searched == 'to_bool':
                        args.append(to_bool(val))

                    elif type_searched == 'to_int':
                        args.append(to_int(val))

                    elif type_searched == 'author' or type_searched == None:
                        args.append(val)

                    elif type_searched == 'command':
                        c = self.commands.find_cmd_by_name(val)
                        if c is not None:
                            args.append(c)

                    elif type_searched == 'host_group':
                        hg = self.host_groups.find_by_name(val)
                        if hg is not None:
                            args.append(hg)

                    elif type_searched == 'service_group':
                        sg = self.service_groups.find_by_name(val)
                        if sg is not None:
                            args.append(sg)

                    elif type_searched == 'contact_group':
                        cg = self.contact_groups.find_by_name(val)
                        if cg is not None:
                            args.append(cg)
                    
                    #special case: service are TWO args host;service, so one more loop
                    #to get the two parts
                    elif type_searched == 'service':
                        in_service = True
                        tmp_host = elts[i].strip()
                        if tmp_host[-1] == '\n':
                            tmp_host = tmp_host[:-1]
                            #If 
                            if self.mode == 'dispatcher':
                                self.search_host_and_dispatch(tmp_host, command)
                                return None


                else:
                    in_service = False
                    srv_name = elts[i]
                    if srv_name[-1] == '\n':
                        srv_name = srv_name[:-1]
                    print "Got service full", tmp_host, srv_name
                    s = self.services.find_srv_by_name_and_hostname(tmp_host, srv_name)
                    if s is not None:
                        args.append(s)
                i += 1

        except IndexError:
            print "Sorry, the arguments are not corrects"
            return None
        print 'Finally got ARGS:', args
        if len(args) == len(ExternalCommand.commands[c_name]['args']):
            print "OK, we can call the command", c_name, "with", args
            f = getattr(self, c_name)
            apply(f, args)
        else:
            print "Sorry, the arguments are not corrects", args


    
    #CHANGE_CONTACT_MODSATTR;<contact_name>;<value>
    def CHANGE_CONTACT_MODSATTR(self, contact, value):
        pass
    
    #CHANGE_CONTACT_MODHATTR;<contact_name>;<value>
    def CHANGE_CONTACT_MODHATTR(self, contact, value):
        pass

    #CHANGE_CONTACT_MODATTR;<contact_name>;<value>
    def CHANGE_CONTACT_MODATTR(self, contact, value):
        pass

    #CHANGE_CONTACT_HOST_NOTIFICATION_TIMEPERIOD;<contact_name>;<notification_timeperiod>
    def CHANGE_CONTACT_HOST_NOTIFICATION_TIMEPERIOD(self, contact, notification_timeperiod):
        pass

    #ADD_SVC_COMMENT;<host_name>;<service_description>;<persistent>;<author>;<comment>
    def ADD_SVC_COMMENT(self, service, persistent, author, comment):
        pass

    #ADD_HOST_COMMENT;<host_name>;<persistent>;<author>;<comment>
    def ADD_HOST_COMMENT(self, host, persistent, author, comment):
        pass

    #ACKNOWLEDGE_SVC_PROBLEM;<host_name>;<service_description>;<sticky>;<notify>;<persistent>;<author>;<comment>
    def ACKNOWLEDGE_SVC_PROBLEM(self, service, sticky, notify, persistent, author, comment):
        pass

    #ACKNOWLEDGE_HOST_PROBLEM;<host_name>;<sticky>;<notify>;<persistent>;<author>;<comment>
    def ACKNOWLEDGE_HOST_PROBLEM(self, host, sticky, notify, persistent, author, comment):
        pass

    #CHANGE_CONTACT_SVC_NOTIFICATION_TIMEPERIOD;<contact_name>;<notification_timeperiod>
    def CHANGE_CONTACT_SVC_NOTIFICATION_TIMEPERIOD(self, contact, notification_timeperiod):
        pass

    #CHANGE_CUSTOM_CONTACT_VAR;<contact_name>;<varname>;<varvalue>
    def CHANGE_CUSTOM_CONTACT_VAR(self, contact, varname, varvalue):
        contact.customs[varname] = varvalue
    
    #CHANGE_CUSTOM_HOST_VAR;<host_name>;<varname>;<varvalue>
    def CHANGE_CUSTOM_HOST_VAR(self, host, varname, varvalue):
        host.customs[varname] = varvalue

    #CHANGE_CUSTOM_SVC_VAR;<host_name>;<service_description>;<varname>;<varvalue>
    def CHANGE_CUSTOM_SVC_VAR(self, service, varname, varvalue):
        service.customs[varname] = varvalue

    #CHANGE_GLOBAL_HOST_EVENT_HANDLER;<event_handler_command>
    def CHANGE_GLOBAL_HOST_EVENT_HANDLER(self, event_handler_command):
        pass

    #CHANGE_GLOBAL_SVC_EVENT_HANDLER;<event_handler_command>
    def CHANGE_GLOBAL_SVC_EVENT_HANDLER(self, event_handler_command):
        pass
    
    #CHANGE_HOST_CHECK_COMMAND;<host_name>;<check_command>
    def CHANGE_HOST_CHECK_COMMAND(self, host, check_command):
        pass

    #CHANGE_HOST_CHECK_TIMEPERIOD;<host_name>;<timeperiod>
    def CHANGE_HOST_CHECK_TIMEPERIOD(self, host, timeperiod):
        pass

    #CHANGE_HOST_CHECK_TIMEPERIOD;<host_name>;<check_timeperod>
    def CHANGE_HOST_CHECK_TIMEPERIOD(host, check_timeperod):
        pass

    #CHANGE_HOST_EVENT_HANDLER;<host_name>;<event_handler_command>
    def CHANGE_HOST_EVENT_HANDLER(self, host, event_handler_command):
        pass

    #CHANGE_HOST_MODATTR;<host_name>;<value>
    def CHANGE_HOST_MODATTR(self, host, value):
        pass

    #CHANGE_MAX_HOST_CHECK_ATTEMPTS;<host_name>;<check_attempts>
    def CHANGE_MAX_HOST_CHECK_ATTEMPTS(self, host, check_attempts):
        host.max_check_attempts = check_attempts

    #CHANGE_MAX_SVC_CHECK_ATTEMPTS;<host_name>;<service_description>;<check_attempts>
    def CHANGE_MAX_SVC_CHECK_ATTEMPTS(self, service, check_attempts):
        service.max_check_attempts = check_attempts

    #CHANGE_NORMAL_HOST_CHECK_INTERVAL;<host_name>;<check_interval>
    def CHANGE_NORMAL_HOST_CHECK_INTERVAL(self, host, check_interval):
        host.check_interval = check_interval

    #CHANGE_NORMAL_SVC_CHECK_INTERVAL;<host_name>;<service_description>;<check_interval>
    def CHANGE_NORMAL_SVC_CHECK_INTERVAL(self, service, check_interval):
        service.check_interval = check_interval

    #CHANGE_RETRY_HOST_CHECK_INTERVAL;<host_name>;<service_description>;<check_interval>
    def CHANGE_RETRY_HOST_CHECK_INTERVAL(self, host, check_interval):
        host.retry_interval = check_interval

    #CHANGE_RETRY_SVC_CHECK_INTERVAL;<host_name>;<service_description>;<check_interval>
    def CHANGE_RETRY_SVC_CHECK_INTERVAL(self, service, check_interval):
        service.retry_interval = check_interval

    #CHANGE_SVC_CHECK_COMMAND;<host_name>;<service_description>;<check_command>
    def CHANGE_SVC_CHECK_COMMAND(self, service, check_command):
        pass

    #CHANGE_SVC_CHECK_TIMEPERIOD;<host_name>;<service_description>;<check_timeperiod>
    def CHANGE_SVC_CHECK_TIMEPERIOD(self, service, check_timeperiod):
        pass

    #CHANGE_SVC_EVENT_HANDLER;<host_name>;<service_description>;<event_handler_command>
    def CHANGE_SVC_EVENT_HANDLER(self, service, event_handler_command):
        pass

    #CHANGE_SVC_MODATTR;<host_name>;<service_description>;<value>
    def CHANGE_SVC_MODATTR(self, service, value):
        pass

    #CHANGE_SVC_NOTIFICATION_TIMEPERIOD;<host_name>;<service_description>;<notification_timeperiod>
    def CHANGE_SVC_NOTIFICATION_TIMEPERIOD(self, service, notification_timeperiod):
        pass

    #DELAY_HOST_NOTIFICATION;<host_name>;<notification_time>
    def DELAY_HOST_NOTIFICATION(self, host, notification_time):
        host.first_notification_delay = notification_time
    
    #DELAY_SVC_NOTIFICATION;<host_name>;<service_description>;<notification_time>
    def DELAY_SVC_NOTIFICATION(self, service, notification_time):
        service.first_notification_delay = notification_time

    #DEL_ALL_HOST_COMMENTS;<host_name>
    def DEL_ALL_HOST_COMMENTS(self, host):
        pass
    
    #DEL_ALL_SVC_COMMENTS;<host_name>;<service_description>
    def DEL_ALL_SVC_COMMENTS(self, service):
        pass    

    #DEL_HOST_COMMENT;<comment_id>
    def DEL_HOST_COMMENT(self, comment_id):
        pass

    #DEL_HOST_DOWNTIME;<downtime_id>
    def DEL_HOST_DOWNTIME(self, downtime_id):
        pass

    #DEL_SVC_COMMENT;<comment_id>
    def DEL_SVC_COMMENT(self, comment_id):
        pass

    #DEL_SVC_DOWNTIME;<downtime_id>
    def DEL_SVC_DOWNTIME(self, downtime_id):
        pass

    #DISABLE_ALL_NOTIFICATIONS_BEYOND_HOST;<host_name>
    def DISABLE_ALL_NOTIFICATIONS_BEYOND_HOST(self, host):
        pass

    #DISABLE_CONTACTGROUP_HOST_NOTIFICATIONS;<contactgroup_name>
    def DISABLE_CONTACTGROUP_HOST_NOTIFICATIONS(self, contactgroup):
        pass

    #DISABLE_CONTACTGROUP_SVC_NOTIFICATIONS;<contactgroup_name>
    def DISABLE_CONTACTGROUP_SVC_NOTIFICATIONS(self, contactgroup):
        pass

    #DISABLE_CONTACT_HOST_NOTIFICATIONS;<contact_name>
    def DISABLE_CONTACT_HOST_NOTIFICATIONS(self, contact):
        contact.host_notifications_enabled = False

    #DISABLE_CONTACT_SVC_NOTIFICATIONS;<contact_name>
    def DISABLE_CONTACT_SVC_NOTIFICATIONS(self, contact):
        contact.service_notifications_enabled = False

    #DISABLE_EVENT_HANDLERS
    def DISABLE_EVENT_HANDLERS(self):
        self.conf.enable_event_handlers = False
        self.conf.explode_global_conf()

    #DISABLE_FAILURE_PREDICTION
    def DISABLE_FAILURE_PREDICTION(self):
        self.conf.enable_failure_prediction = False
        self.conf.explode_global_conf()

    #DISABLE_FLAP_DETECTION
    def DISABLE_FLAP_DETECTION(self):
        self.conf.enable_flap_detection = False
        self.conf.explode_global_conf()

    #DISABLE_HOSTGROUP_HOST_CHECKS;<hostgroup_name>
    def DISABLE_HOSTGROUP_HOST_CHECKS(self, hostgroup):
        pass

    #DISABLE_HOSTGROUP_HOST_NOTIFICATIONS;<hostgroup_name>
    def DISABLE_HOSTGROUP_HOST_NOTIFICATIONS(self, hostgroup):
        pass

    #DISABLE_HOSTGROUP_PASSIVE_HOST_CHECKS;<hostgroup_name>
    def DISABLE_HOSTGROUP_PASSIVE_HOST_CHECKS(self, hostgroup):
        pass

    #DISABLE_HOSTGROUP_PASSIVE_SVC_CHECKS;<hostgroup_name>
    def DISABLE_HOSTGROUP_PASSIVE_SVC_CHECKS(self, hostgroup):
        pass

    #DISABLE_HOSTGROUP_SVC_CHECKS;<hostgroup_name>
    def DISABLE_HOSTGROUP_SVC_CHECKS(self, hostgroup):
        pass

    #DISABLE_HOSTGROUP_SVC_NOTIFICATIONS;<hostgroup_name>
    def DISABLE_HOSTGROUP_SVC_NOTIFICATIONS(self, hostgroup):
        pass

    #DISABLE_HOST_AND_CHILD_NOTIFICATIONS;<host_name>
    def DISABLE_HOST_AND_CHILD_NOTIFICATIONS(self, host):
        pass

    #DISABLE_HOST_CHECK;<host_name>
    def DISABLE_HOST_CHECK(self, host):
        host.active_checks_enabled = False

    #DISABLE_HOST_EVENT_HANDLER;<host_name>
    def DISABLE_HOST_EVENT_HANDLER(self, host):
        host.event_handler_enabled = False

    #DISABLE_HOST_FLAP_DETECTION;<host_name>
    def DISABLE_HOST_FLAP_DETECTION(self, host):
        host.flap_detection_enabled = False

    #DISABLE_HOST_FRESHNESS_CHECKS
    def DISABLE_HOST_FRESHNESS_CHECKS(self):
        host.check_freshness = False

    #DISABLE_HOST_NOTIFICATIONS;<host_name>
    def DISABLE_HOST_NOTIFICATIONS(self, host):
        host.enable_notifications = False

    #DISABLE_HOST_SVC_CHECKS;<host_name>
    def DISABLE_HOST_SVC_CHECKS(self, host):
        for s in host.services:
            self.DISABLE_SVC_CHECK(s)

    #DISABLE_HOST_SVC_NOTIFICATIONS;<host_name>
    def DISABLE_HOST_SVC_NOTIFICATIONS(self, host):
        for s in host.services:
            self.DISABLE_SVC_NOTIFICATIONS(s)

    #DISABLE_NOTIFICATIONS
    def DISABLE_NOTIFICATIONS(self):
        self.conf.enable_notifications = False
        self.conf.explode_global_conf()

    #DISABLE_PASSIVE_HOST_CHECKS;<host_name>
    def DISABLE_PASSIVE_HOST_CHECKS(self, host):
        host.passive_checks_enabled = False

    #DISABLE_PASSIVE_SVC_CHECKS;<host_name>;<service_description>
    def DISABLE_PASSIVE_SVC_CHECKS(self, service):
        service.passive_checks_enabled = False

    #DISABLE_PERFORMANCE_DATA
    def DISABLE_PERFORMANCE_DATA(self):
        self.conf.process_performance_data = False
        self.conf.explode_global_conf()

    #DISABLE_SERVICEGROUP_HOST_CHECKS;<servicegroup_name>
    def DISABLE_SERVICEGROUP_HOST_CHECKS(self, servicegroup):
        pass

    #DISABLE_SERVICEGROUP_HOST_NOTIFICATIONS;<servicegroup_name>
    def DISABLE_SERVICEGROUP_HOST_NOTIFICATIONS(self, servicegroup):
        pass

    #DISABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS;<servicegroup_name>
    def DISABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS(self, servicegroup):
        pass

    #DISABLE_SERVICEGROUP_PASSIVE_SVC_CHECKS;<servicegroup_name>
    def DISABLE_SERVICEGROUP_PASSIVE_SVC_CHECKS(self, servicegroup):
        pass

    #DISABLE_SERVICEGROUP_SVC_CHECKS;<servicegroup_name>
    def DISABLE_SERVICEGROUP_SVC_CHECKS(self, servicegroup):
        pass

    #DISABLE_SERVICEGROUP_SVC_NOTIFICATIONS;<servicegroup_name>
    def DISABLE_SERVICEGROUP_SVC_NOTIFICATIONS(self, servicegroup):
        pass

    #DISABLE_SERVICE_FLAP_DETECTION;<host_name>;<service_description>
    def DISABLE_SERVICE_FLAP_DETECTION(self, service):
        service.enable_flap_detection = False

    #DISABLE_SERVICE_FRESHNESS_CHECKS
    def DISABLE_SERVICE_FRESHNESS_CHECKS(self):
        self.conf.check_service_freshness = False
        self.conf.explode_global_conf()

    #DISABLE_SVC_CHECK;<host_name>;<service_description>
    def DISABLE_SVC_CHECK(self, service):
        service.active_checks_enabled = False

    #DISABLE_SVC_EVENT_HANDLER;<host_name>;<service_description>
    def DISABLE_SVC_EVENT_HANDLER(self, service):
        service.enable_event_handlers = False

    #DISABLE_SVC_FLAP_DETECTION;<host_name>;<service_description>
    def DISABLE_SVC_FLAP_DETECTION(self, service):
        service.enable_flap_detection = False

    #DISABLE_SVC_NOTIFICATIONS;<host_name>;<service_description>
    def DISABLE_SVC_NOTIFICATIONS(self, service):
        service.enable_notifications = False

    #ENABLE_ALL_NOTIFICATIONS_BEYOND_HOST;<host_name>
    def ENABLE_ALL_NOTIFICATIONS_BEYOND_HOST(self, host):
        pass

    #ENABLE_CONTACTGROUP_HOST_NOTIFICATIONS;<contactgroup_name>
    def ENABLE_CONTACTGROUP_HOST_NOTIFICATIONS(self, contactgroup):
        pass

    #ENABLE_CONTACTGROUP_SVC_NOTIFICATIONS;<contactgroup_name>
    def ENABLE_CONTACTGROUP_SVC_NOTIFICATIONS(self, contactgroup):
        pass

    #ENABLE_CONTACT_HOST_NOTIFICATIONS;<contact_name>
    def ENABLE_CONTACT_HOST_NOTIFICATIONS(self, contact):
        contact.host_notifications_enabled = True

    #ENABLE_CONTACT_SVC_NOTIFICATIONS;<contact_name>
    def ENABLE_CONTACT_SVC_NOTIFICATIONS(self, contact):
        contact.service_notifications_enabled = True

    #ENABLE_EVENT_HANDLERS
    def ENABLE_EVENT_HANDLERS(self):
        self.conf.enable_event_handlers = True
        self.conf.explode_global_conf()

    #ENABLE_FAILURE_PREDICTION
    def ENABLE_FAILURE_PREDICTION(self):
        self.conf.enable_failure_prediction = True
        self.conf.explode_global_conf()

    #ENABLE_FLAP_DETECTION
    def ENABLE_FLAP_DETECTION(self):
        self.conf.enable_flap_detection = True
        self.conf.explode_global_conf()

    #ENABLE_HOSTGROUP_HOST_CHECKS;<hostgroup_name>
    def ENABLE_HOSTGROUP_HOST_CHECKS(self, hostgroup):
        pass

    #ENABLE_HOSTGROUP_HOST_NOTIFICATIONS;<hostgroup_name>
    def ENABLE_HOSTGROUP_HOST_NOTIFICATIONS(self, hostgroup):
        pass

    #ENABLE_HOSTGROUP_PASSIVE_HOST_CHECKS;<hostgroup_name>
    def ENABLE_HOSTGROUP_PASSIVE_HOST_CHECKS(self, hostgroup):
        pass

    #ENABLE_HOSTGROUP_PASSIVE_SVC_CHECKS;<hostgroup_name>
    def ENABLE_HOSTGROUP_PASSIVE_SVC_CHECKS(self, hostgroup):
        pass

    #ENABLE_HOSTGROUP_SVC_CHECKS;<hostgroup_name>
    def ENABLE_HOSTGROUP_SVC_CHECKS(self, hostgroup):
        pass

    #ENABLE_HOSTGROUP_SVC_NOTIFICATIONS;<hostgroup_name>
    def ENABLE_HOSTGROUP_SVC_NOTIFICATIONS(self, hostgroup):
        pass

    #ENABLE_HOST_AND_CHILD_NOTIFICATIONS;<host_name>
    def ENABLE_HOST_AND_CHILD_NOTIFICATIONS(self, host):
        pass

    #ENABLE_HOST_CHECK;<host_name>
    def ENABLE_HOST_CHECK(self, host):
        host.active_checks_enabled = True

    #ENABLE_HOST_EVENT_HANDLER;<host_name>
    def ENABLE_HOST_EVENT_HANDLER(self, host):
        host.enable_event_handlers = True

    #ENABLE_HOST_FLAP_DETECTION;<host_name>
    def ENABLE_HOST_FLAP_DETECTION(self, host):
        host.enable_flap_detection = True

    #ENABLE_HOST_FRESHNESS_CHECKS
    def ENABLE_HOST_FRESHNESS_CHECKS(self):
        host.check_freshness = True

    #ENABLE_HOST_NOTIFICATIONS;<host_name>
    def ENABLE_HOST_NOTIFICATIONS(self, host):
        host.enable_notifications = True

    #ENABLE_HOST_SVC_CHECKS;<host_name>
    def ENABLE_HOST_SVC_CHECKS(self, host):
        for s in host.services:
            self.ENABLE_SVC_CHECK(s)

    #ENABLE_HOST_SVC_NOTIFICATIONS;<host_name>
    def ENABLE_HOST_SVC_NOTIFICATIONS(self, host):
        for s in host.services:
            self.ENABLE_SVC_NOTIFICATIONS(s)
    
    #ENABLE_NOTIFICATIONS
    def ENABLE_NOTIFICATIONS(self):
        self.conf.enable_notifications = True
        self.conf.explode_global_conf()

    #ENABLE_PASSIVE_HOST_CHECKS;<host_name>
    def ENABLE_PASSIVE_HOST_CHECKS(self, host):
        host.passive_checks_enabled = True

    #ENABLE_PASSIVE_SVC_CHECKS;<host_name>;<service_description>
    def ENABLE_PASSIVE_SVC_CHECKS(self, service):
        service.passive_checks_enabled = True

    #ENABLE_PERFORMANCE_DATA
    def ENABLE_PERFORMANCE_DATA(self):
        self.conf.process_performance_data = True
        self.conf.explode_global_conf()
    
    #ENABLE_SERVICEGROUP_HOST_CHECKS;<servicegroup_name>
    def ENABLE_SERVICEGROUP_HOST_CHECKS(self, servicegroup):
        pass
    
    #ENABLE_SERVICEGROUP_HOST_NOTIFICATIONS;<servicegroup_name>
    def ENABLE_SERVICEGROUP_HOST_NOTIFICATIONS(self, servicegroup):
        pass
    
    #ENABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS;<servicegroup_name>
    def ENABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS(self, servicegroup):
        pass

    #ENABLE_SERVICEGROUP_PASSIVE_SVC_CHECKS;<servicegroup_name>
    def ENABLE_SERVICEGROUP_PASSIVE_SVC_CHECKS(self, servicegroup):
        pass

    #ENABLE_SERVICEGROUP_SVC_CHECKS;<servicegroup_name>
    def ENABLE_SERVICEGROUP_SVC_CHECKS(self, servicegroup):
        pass

    #ENABLE_SERVICEGROUP_SVC_NOTIFICATIONS;<servicegroup_name>
    def ENABLE_SERVICEGROUP_SVC_NOTIFICATIONS(self, servicegroup):
        pass

    #ENABLE_SERVICE_FRESHNESS_CHECKS
    def ENABLE_SERVICE_FRESHNESS_CHECKS(self):
        self.conf.check_service_freshness = True
        self.conf.explode_global_conf()

    #ENABLE_SVC_CHECK;<host_name>;<service_description>
    def ENABLE_SVC_CHECK(self, service):
        service.active_checks_enabled = True

    #ENABLE_SVC_EVENT_HANDLER;<host_name>;<service_description>
    def ENABLE_SVC_EVENT_HANDLER(self, service):
        service.enable_event_handlers = True

    #ENABLE_SVC_FLAP_DETECTION;<host_name>;<service_description>
    def ENABLE_SVC_FLAP_DETECTION(self, service):
        service.enable_flap_detection = True

    #ENABLE_SVC_NOTIFICATIONS;<host_name>;<service_description>
    def ENABLE_SVC_NOTIFICATIONS(self, service):
        service.enable_notifications = True

    #PROCESS_FILE;<file_name>;<delete>
    def PROCESS_FILE(self, file_name, delete):
        pass

    #PROCESS_HOST_CHECK_RESULT;<host_name>;<status_code>;<plugin_output>
    def PROCESS_HOST_CHECK_RESULT(self, host, status_code, plugin_output):
        now = time.time()
        cls = host.__class__
        #If globally disable OR locally, do not launch
        if cls.accept_passive_checks and host.passive_checks_enabled:
            c = host.launch_check(now)
            #Now we 'trasnform the check into a result'
            #So exit_status, output and status to be eat by the host
            c.exit_status = status_code
            c.get_outputs(plugin_output)
            c.status = 'waitconsume'
            #We add in the
            self.sched.add_or_update_check(c)


    #PROCESS_SERVICE_CHECK_RESULT;<host_name>;<service_description>;<return_code>;<plugin_output>
    def PROCESS_SERVICE_CHECK_RESULT(self, service, return_code, plugin_output):
        now = time.time()
        cls = service.__class__
        #If globally disable OR locally, do not launch
        if cls.accept_passive_checks and service.passive_checks_enabled:
            c = service.launch_check(now)
            #Now we 'trasnform the check into a result'
            #So exit_status, output and status to be eat by the service
            c.exit_status = return_code
            c.get_outputs(plugin_output)
            c.status = 'waitconsume'
            #We add in the 
            self.sched.add_or_update_check(c)


    #READ_STATE_INFORMATION
    def READ_STATE_INFORMATION(self):
        pass

    #REMOVE_HOST_ACKNOWLEDGEMENT;<host_name>
    def REMOVE_HOST_ACKNOWLEDGEMENT(self, host):
        pass

    #REMOVE_SVC_ACKNOWLEDGEMENT;<host_name>;<service_description>
    def REMOVE_SVC_ACKNOWLEDGEMENT(self, service):
        pass

    #RESTART_PROGRAM
    def RESTART_PROGRAM(self):
        pass

    #SAVE_STATE_INFORMATION
    def SAVE_STATE_INFORMATION(self):
        pass

    #SCHEDULE_AND_PROPAGATE_HOST_DOWNTIME;<host_name>;<start_time>;<end_time>;<fixed>;<trigger_id>;<duration>;<author>;<comment>
    def SCHEDULE_AND_PROPAGATE_HOST_DOWNTIME(self, host, start_time, end_time, fixed, trigger_id, duration, author, comment):
        pass

    #SCHEDULE_AND_PROPAGATE_TRIGGERED_HOST_DOWNTIME;<host_name>;<start_time>;<end_time>;<fixed>;<trigger_id>;<duration>;<author>;<comment>
    def SCHEDULE_AND_PROPAGATE_TRIGGERED_HOST_DOWNTIME(self, host, start_time, end_time, fixed, trigger_id, duration, author, comment):
        pass

    #SCHEDULE_FORCED_HOST_CHECK;<host_name>;<check_time>
    def SCHEDULE_FORCED_HOST_CHECK(self, host, check_time):
        c = host.schedule(force=True, force_time=check_time)
        self.sched.add_or_update_check(c)


    #SCHEDULE_FORCED_HOST_SVC_CHECKS;<host_name>;<check_time>
    def SCHEDULE_FORCED_HOST_SVC_CHECKS(self, host, check_time):
        for s in host.services:
            self.SCHEDULE_FORCED_SVC_CHECK(s, check_time)

    #SCHEDULE_FORCED_SVC_CHECK;<host_name>;<service_description>;<check_time>
    def SCHEDULE_FORCED_SVC_CHECK(self, service, check_time):
        c = service.schedule(force=True, force_time=check_time)
        self.sched.add_or_update_check(c)

    #SCHEDULE_HOSTGROUP_HOST_DOWNTIME;<hostgroup_name>;<start_time>;<end_time>;<fixed>;<trigger_id>;<duration>;<author>;<comment>
    def SCHEDULE_HOSTGROUP_HOST_DOWNTIME(self, hostgroup, start_time, end_time, fixed, trigger_id, duration, author, comment):
        pass

    #SCHEDULE_HOSTGROUP_SVC_DOWNTIME;<hostgroup_name>;<start_time>;<end_time>;<fixed>;<trigger_id>;<duration>;<author>;<comment>
    def SCHEDULE_HOSTGROUP_SVC_DOWNTIME(self, hostgroup, start_time, end_time, fixed, trigger_id, duration, author, comment):
        pass

    #SCHEDULE_HOST_CHECK;<host_name>;<check_time>
    def SCHEDULE_HOST_CHECK(self, host, check_time):
        c = host.schedule(force=False, force_time=check_time)
        self.sched.add_or_update_check(c)

    #SCHEDULE_HOST_DOWNTIME;<host_name>;<start_time>;<end_time>;<fixed>;<trigger_id>;<duration>;<author>;<comment>
    def SCHEDULE_HOST_DOWNTIME(self, host, start_time, end_time, fixed, trigger_id, duration, author, comment):
        dt = Downtime(host, start_time, end_time, fixed, trigger_id, duration, author, comment)
        host.add_downtime(dt)
        self.sched.add_downtime(dt)

    #SCHEDULE_HOST_SVC_CHECKS;<host_name>;<check_time>
    def SCHEDULE_HOST_SVC_CHECKS(self, host, check_time):
        for s in host.services:
            self.SCHEDULE_SVC_CHECK(s, check_time)

    #SCHEDULE_HOST_SVC_DOWNTIME;<host_name>;<start_time>;<end_time>;<fixed>;<trigger_id>;<duration>;<author>;<comment>
    def SCHEDULE_HOST_SVC_DOWNTIME(self, host, start_time, end_time, fixed, trigger_id, duration, author, comment):
        for s in host.services:
            self.SCHEDULE_SVC_DOWNTIME(s, start_time, end_time, fixed, trigger_id, duration, author, comment)

    #SCHEDULE_SERVICEGROUP_HOST_DOWNTIME;<servicegroup_name>;<start_time>;<end_time>;<fixed>;<trigger_id>;<duration>;<author>;<comment>
    def SCHEDULE_SERVICEGROUP_HOST_DOWNTIME(self, servicegroup, start_time, end_time, fixed, trigger_id, duration, author, comment):
        pass

    #SCHEDULE_SERVICEGROUP_SVC_DOWNTIME;<servicegroup_name>;<start_time>;<end_time>;<fixed>;<trigger_id>;<duration>;<author>;<comment>
    def SCHEDULE_SERVICEGROUP_SVC_DOWNTIME(self, servicegroup, start_time, end_time, fixed, trigger_id, duration, author, comment):
        pass

    #SCHEDULE_SVC_CHECK;<host_name>;<service_description>;<check_time>
    def SCHEDULE_SVC_CHECK(self, service, check_time):
        c = service.schedule(force=False, force_time=check_time)
        self.sched.add_or_update_check(c)

    #SCHEDULE_SVC_DOWNTIME;<host_name>;<service_desription><start_time>;<end_time>;<fixed>;<trigger_id>;<duration>;<author>;<comment>
    def SCHEDULE_SVC_DOWNTIME(self, service, start_time, end_time, fixed, trigger_id, duration, author, comment):
        dt = Downtime(service, start_time, end_time, fixed, trigger_id, duration, author, comment)
        host.add_downtime(dt)
        self.sched.add_downtime(dt)

    #SEND_CUSTOM_HOST_NOTIFICATION;<host_name>;<options>;<author>;<comment>
    def SEND_CUSTOM_HOST_NOTIFICATION(self, host, options, author, comment):
        pass

    #SEND_CUSTOM_SVC_NOTIFICATION;<host_name>;<service_description>;<options>;<author>;<comment>
    def SEND_CUSTOM_SVC_NOTIFICATION(self, service, options, author, comment):
        pass

    #SET_HOST_NOTIFICATION_NUMBER;<host_name>;<notification_number>
    def SET_HOST_NOTIFICATION_NUMBER(self, host, notification_number):
        pass

    #SET_SVC_NOTIFICATION_NUMBER;<host_name>;<service_description>;<notification_number>
    def SET_SVC_NOTIFICATION_NUMBER(self, service, notification_number):
        pass

    #SHUTDOWN_PROGRAM
    def SHUTDOWN_PROGRAM(self):
        pass

    #START_ACCEPTING_PASSIVE_HOST_CHECKS
    def START_ACCEPTING_PASSIVE_HOST_CHECKS(self):
        self.conf.accept_passive_host_checks = True
        self.conf.explode_global_conf()

    #START_ACCEPTING_PASSIVE_SVC_CHECKS
    def START_ACCEPTING_PASSIVE_SVC_CHECKS(self):
        self.conf.accept_passive_service_checks = True
        self.conf.explode_global_conf()

    #START_EXECUTING_HOST_CHECKS
    def START_EXECUTING_HOST_CHECKS(self):
        self.conf.execute_host_checks = True
        self.conf.explode_global_conf()

    #START_EXECUTING_SVC_CHECKS
    def START_EXECUTING_SVC_CHECKS(self):
        self.conf.execute_service_checks = True
        self.conf.explode_global_conf()

    #START_OBSESSING_OVER_HOST;<host_name>
    def START_OBSESSING_OVER_HOST(self, host):
        host.obsess_over = True

    #START_OBSESSING_OVER_HOST_CHECKS
    def START_OBSESSING_OVER_HOST_CHECKS(self):
        self.conf.obsess_over_hosts = True
        self.conf.explode_global_conf()

    #START_OBSESSING_OVER_SVC;<host_name>;<service_description>
    def START_OBSESSING_OVER_SVC(self, service):
        service.obsess_over = True

    #START_OBSESSING_OVER_SVC_CHECKS
    def START_OBSESSING_OVER_SVC_CHECKS(self):
        self.conf.obsess_over_services = True
        self.conf.explode_global_conf()

    #STOP_ACCEPTING_PASSIVE_HOST_CHECKS
    def STOP_ACCEPTING_PASSIVE_HOST_CHECKS(self):
        self.accept_passive_host_checks = False
        self.conf.explode_global_conf()

    #STOP_ACCEPTING_PASSIVE_SVC_CHECKS
    def STOP_ACCEPTING_PASSIVE_SVC_CHECKS(self):
        self.accept_passive_service_checks = False
        self.conf.explode_global_conf()

    #STOP_EXECUTING_HOST_CHECKS
    def STOP_EXECUTING_HOST_CHECKS(self):
        self.conf.execute_host_checks = False
        self.conf.explode_global_conf()

    #STOP_EXECUTING_SVC_CHECKS
    def STOP_EXECUTING_SVC_CHECKS(self):
        self.conf.execute_service_checks = False
        self.conf.explode_global_conf()

    #STOP_OBSESSING_OVER_HOST;<host_name>
    def STOP_OBSESSING_OVER_HOST(self, host):
        host.obsess_over = False

    #STOP_OBSESSING_OVER_HOST_CHECKS
    def STOP_OBSESSING_OVER_HOST_CHECKS(self):
        self.obsess_over_hosts = False
        self.conf.explode_global_conf()

    #STOP_OBSESSING_OVER_SVC;<host_name>;<service_description>
    def STOP_OBSESSING_OVER_SVC(self, service):
        service.obsess_over = False

    #STOP_OBSESSING_OVER_SVC_CHECKS
    def STOP_OBSESSING_OVER_SVC_CHECKS(self):
        self.obsess_over_services = False
        self.conf.explode_global_conf()
    
    
    
if __name__ == '__main__':
    import os
    
    FIFO_PATH = '/tmp/my_fifo'
    
    if os.path.exists(FIFO_PATH):
        os.unlink(FIFO_PATH)
        
    if not os.path.exists(FIFO_PATH):
        os.umask(0)
        os.mkfifo(FIFO_PATH, 0660)
        my_fifo = open(FIFO_PATH, 'w+')
        print "my_fifo:", my_fifo
    
    print open(FIFO_PATH, 'r').readline()
