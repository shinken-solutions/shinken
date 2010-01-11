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


#Config is the class to read, load and manipulate the user
#configuration. It read a main cfg (nagios.cfg) and get all informations
#from it. It create objects, make link between them, clean them, and cut
#them into independant parts. The main user of this is Arbiter, but schedulers
#use it too (but far less)

import re, string, copy, os
import itertools

from timeperiod import Timeperiod, Timeperiods
from service import Service, Services
from command import Command, Commands
from resultmodulation import Resultmodulation, Resultmodulations
from escalation import Escalation, Escalations
from host import Host, Hosts
from hostgroup import Hostgroup, Hostgroups
from realm import Realm, Realms
from contact import Contact, Contacts
from contactgroup import Contactgroup, Contactgroups
from servicegroup import Servicegroup, Servicegroups
from item import Item
from macroresolver import MacroResolver
from servicedependency import Servicedependency, Servicedependencies
from hostdependency import Hostdependency, Hostdependencies
from schedulerlink import SchedulerLink, SchedulerLinks
from reactionnerlink import ReactionnerLink, ReactionnerLinks
from brokerlink import BrokerLink, BrokerLinks
from pollerlink import PollerLink, PollerLinks
from module import Module, Modules
from graph import Graph

from util import to_int, to_char, to_bool
#import psyco
#psyco.full()


class Config(Item):
    cache_path = "objects.cache"
    my_type = "config"

    #Properties: 
    #required : if True, there is not default, and the config must put them
    #default: if not set, take this value
    #pythonize : function call to 
    #class_inherit : (Service, 'blabla') : must set this propertie to the 
    #Service class with name blabla
    #if (Service, None) : must set this properti to the Service class with
    #same name
    properties={'log_file' : {'required':False, 'default' : '/tmp/log.txt'},
                'object_cache_file' : {'required':False, 'default' : '/tmp/object.dat'},
                'precached_object_file' : {'required':False , 'default' : '/tmp/object.precache'},
                'resource_file' : {'required':False , 'default':'/tmp/ressources.txt'},
                'temp_file' : {'required':False, 'default':'/tmp/temp_file.txt'},
                'status_file' : {'required':False, 'default':'/tmp/status.dat'},
                'status_update_interval' : {'required':False, 'default':'15', 'pythonize': to_int},
                'nagios_user' : {'required':False, 'default':'nap'},
                'nagios_group' : {'required':False, 'default':'nap'},
                'enable_notifications' : {'required':False, 'default':'1', 'pythonize': to_bool, 'class_inherit' : [(Host, None), (Service, None), (Contact, None)]},
                'execute_service_checks' : {'required':False, 'default':'1', 'pythonize': to_bool, 'class_inherit' : [(Service, 'execute_checks')]},
                'accept_passive_service_checks' : {'required':False, 'default':'1', 'pythonize': to_bool, 'class_inherit' : [(Service, 'accept_passive_checks')]},
                'execute_host_checks' : {'required':False, 'default':'1', 'pythonize': to_bool, 'class_inherit' : [(Host, 'execute_checks')]},
                'accept_passive_host_checks' : {'required':False, 'default':'1', 'pythonize': to_bool, 'class_inherit' : [(Host, 'accept_passive_checks')]},
                'enable_event_handlers' : {'required':False, 'default':'1', 'pythonize': to_bool, 'class_inherit' : [(Host, None), (Service, None)]},
                'log_rotation_method' : {'required':False, 'default':'d', 'pythonize': to_char},
                'log_archive_path' : {'required':False, 'default':'/tmp/'},
                'check_external_commands' : {'required':False, 'default':'1', 'pythonize': to_bool},
                'command_check_interval' : {'required':False, 'default':'-1'},
                'command_file' : {'required':False, 'default':'/tmp/command.cmd'},
                'external_command_buffer_slots' : {'required':False, 'default':'512', 'pythonize': to_int},
                'check_for_updates' : {'required':False, 'default':'1', 'pythonize': to_bool},
                'bare_update_checks' : {'required':False, 'default':'1', 'pythonize': to_bool},
                'lock_file' : {'required':False, 'default':'/tmp/lock.lock'},
                'retain_state_information' : {'required':False, 'default':'1', 'pythonize': to_bool},
                'state_retention_file' : {'required':False, 'default':'/tmp/retention.dat'},
                'retention_update_interval' : {'required':False, 'default':'60', 'pythonize': to_int},
                'use_retained_program_state' : {'required':False, 'default':'1', 'pythonize': to_bool},
                'use_retained_scheduling_info' : {'required':False, 'default':'1', 'pythonize': to_bool},
                'retained_host_attribute_mask' : {'required':False, 'default':'0', 'class_inherit' : [(Host, 'retained_attribute_mask')]},
                'retained_service_attribute_mask' : {'required':False, 'default':'0', 'class_inherit' : [(Service, 'retained_attribute_mask')]},
                'retained_process_host_attribute_mask' : {'required':False, 'default':'0', 'class_inherit' : [(Host, 'retained_process_attribute_mask')]},
                'retained_process_service_attribute_mask' : {'required':False, 'default':'0', 'class_inherit' : [(Host, 'retained_process_attribute_mask')]},
                'retained_contact_host_attribute_mask' : {'required':False, 'default':'0', 'class_inherit' : [(Host, 'retained_contact_attribute_mask')]},
                'retained_contact_service_attribute_mask' : {'required':False, 'default':'0', 'class_inherit' : [(Service, 'retained_contact_attribute_mask')]},
                'use_syslog' : {'required':False, 'default':'0', 'pythonize': to_bool},
                'log_notifications' : {'required':False, 'default':'1', 'pythonize': to_bool, 'class_inherit' : [(Host, None), (Service, None)]},
                'log_service_retries' : {'required':False, 'default':'1', 'pythonize': to_bool, 'class_inherit' : [(Service, 'log_retries')]},
                'log_host_retries' : {'required':False, 'default':'1', 'pythonize': to_bool, 'class_inherit' : [(Host, 'log_retries')]},
                'log_event_handlers' : {'required':False, 'default':'1', 'pythonize': to_bool, 'class_inherit' : [(Host, None), (Service, None)]},
                'log_initial_states' : {'required':False, 'default':'1', 'pythonize': to_bool},
                'log_external_commands' : {'required':False, 'default':'1', 'pythonize': to_bool},
                'log_passive_checks' : {'required':False, 'default':'1', 'pythonize': to_bool},
                'global_host_event_handler' : {'required':False, 'default':'', 'class_inherit' : [(Host, 'global_event_handler')]},
                'global_service_event_handler' : {'required':False, 'default':'', 'class_inherit' : [(Service, 'global_event_handler')]},
                'sleep_time' : {'required':False, 'default':'1', 'pythonize': to_int},
                'service_inter_check_delay_method' : {'required':False, 'default':'s', 'class_inherit' : [(Service, 'inter_check_delay_method')]},
                'max_service_check_spread' : {'required':False, 'default':'30', 'pythonize': to_int, 'class_inherit' : [(Service, 'max_check_spread')]},
                'service_interleave_factor' : {'required':False, 'default':'s', 'class_inherit' : [(Service, 'interleave_factor')]},
                'max_concurrent_checks' : {'required':False, 'default':'200', 'pythonize': to_int},
                'check_result_reaper_frequency' : {'required':False, 'default':'5', 'pythonize': to_int},
                'max_check_result_reaper_time' : {'required':False, 'default':'30', 'pythonize': to_int},
                'check_result_path' : {'required':False, 'default':'/tmp/'},
                'max_check_result_file_age' : {'required':False, 'default':'3600', 'pythonize': to_int},
                'host_inter_check_delay_method' : {'required':False, 'default':'s', 'class_inherit' : [(Host, 'inter_check_delay_method')]},
                'max_host_check_spread' : {'required':False, 'default':'30', 'pythonize': to_int, 'class_inherit' : [(Host, 'max_check_spread')]},
                'interval_length' : {'required':False, 'default':'60', 'pythonize': to_int, 'class_inherit' : [(Host, None), (Service, None)]},
                'auto_reschedule_checks' : {'required':False, 'default':'1', 'pythonize': to_bool, 'class_inherit' : [(Host, None), (Service, None)]},
                'auto_rescheduling_interval' : {'required':False, 'default':'30', 'pythonize': to_int, 'class_inherit' : [(Host, None), (Service, None)]},
                'auto_rescheduling_window' : {'required':False, 'default':'180', 'pythonize': to_int, 'class_inherit' : [(Host, None), (Service, None)]},
                'use_aggressive_host_checking' : {'required':False, 'default':'1', 'pythonize': to_bool, 'class_inherit' : [(Host, None)]},
                'translate_passive_host_checks' : {'required':False, 'default':'1', 'pythonize': to_bool, 'class_inherit' : [(Host, 'translate_passive_checks')]},
                'passive_host_checks_are_soft' : {'required':False, 'default':'1', 'pythonize': to_bool, 'class_inherit' : [(Host, 'passive_checks_are_soft')]},
                'enable_predictive_host_dependency_checks' : {'required':False, 'default':'1', 'pythonize': to_bool, 'class_inherit' : [(Host, 'enable_predictive_dependency_checks')]},
                'enable_predictive_service_dependency_checks' : {'required':False, 'default':'1', 'class_inherit' : [(Service, 'enable_predictive_dependency_checks')]},
                'cached_host_check_horizon' : {'required':False, 'default':'0', 'pythonize': to_int, 'class_inherit' : [(Host, 'cached_check_horizon')]},
                'cached_service_check_horizon' : {'required':False, 'default':'0', 'pythonize': to_int, 'class_inherit' : [(Service, 'cached_check_horizon')]},
                'use_large_installation_tweaks' : {'required':False, 'default':'0', 'pythonize': to_bool},
                'free_child_process_memory' : {'required':False, 'default':'1', 'pythonize': to_bool},
                'child_processes_fork_twice' : {'required':False, 'default':'1', 'pythonize': to_bool},
                'enable_environment_macros' : {'required':False, 'default':'1', 'pythonize': to_bool, 'class_inherit' : [(Host, None), (Service, None)]},
                'enable_flap_detection' : {'required':False, 'default':'1', 'pythonize': to_bool, 'class_inherit' : [(Host, None), (Service, None)]},
                'low_service_flap_threshold' : {'required':False, 'default':'25', 'pythonize': to_int, 'class_inherit' : [(Service, 'low_flap_threshold')]},
                'high_service_flap_threshold' : {'required':False, 'default':'50', 'pythonize': to_int, 'class_inherit' : [(Service, 'high_flap_threshold')]},
                'low_host_flap_threshold' : {'required':False, 'default':'25', 'pythonize': to_int, 'class_inherit' : [(Host, 'low_flap_threshold')]},
                'high_host_flap_threshold' : {'required':False, 'default':'50', 'pythonize': to_int, 'class_inherit' : [(Host, 'high_flap_threshold')]},
                'soft_state_dependencies' : {'required':False, 'default':'0', 'pythonize': to_bool, 'class_inherit' : [(Host, None), (Service, None)]},
                'service_check_timeout' : {'required':False, 'default':'10', 'pythonize': to_int, 'class_inherit' : [(Service, 'check_timeout')]},
                'host_check_timeout' : {'required':False, 'default':'10', 'pythonize': to_int, 'class_inherit' : [(Host, 'check_timeout')]},
                'event_handler_timeout' : {'required':False, 'default':'10', 'pythonize': to_int, 'class_inherit' : [(Host, None), (Service, None)]},
                'notification_timeout' : {'required':False, 'default':'5', 'pythonize': to_int, 'class_inherit' : [(Host, None), (Service, None)]},
                'ocsp_timeout' : {'required':False, 'default':'5', 'pythonize': to_int, 'class_inherit' : [(Service, None)]},
                'ochp_timeout' : {'required':False, 'default':'5', 'pythonize': to_int, 'class_inherit' : [(Host, None)]},
                'perfdata_timeout' : {'required':False, 'default':'2', 'pythonize': to_int, 'class_inherit' : [(Host, None), (Service, None)]},
                'obsess_over_services' : {'required':False, 'default':'0', 'pythonize': to_bool, 'class_inherit' : [(Service, 'obsess_over')]},
                'ocsp_command' : {'required':False, 'default':'', 'class_inherit' : [(Service, None)]},
                'obsess_over_hosts' : {'required':False, 'default':'0', 'pythonize': to_bool, 'class_inherit' : [(Host, 'obsess_over')]},
                'ochp_command' : {'required':False, 'default':'', 'class_inherit' : [(Host, None)]},
                'process_performance_data' : {'required':False, 'default':'1', 'pythonize': to_bool , 'class_inherit' : [(Host, None), (Service, None)]},
                'host_perfdata_command' : {'required':False, 'default':'' , 'class_inherit' : [(Host, 'perfdata_command')]},
                'service_perfdata_command' : {'required':False, 'default':'', 'class_inherit' : [(Service, 'perfdata_command')]},
                'host_perfdata_file' : {'required':False, 'default':'/tmp/host.perf' , 'class_inherit' : [(Host, 'perfdata_file')]},
                'service_perfdata_file' : {'required':False, 'default':'/tmp/service.perf' , 'class_inherit' : [(Service, 'perfdata_file')]},
                'host_perfdata_file_template' : {'required':False, 'default':'/tmp/host.perf', 'class_inherit' : [(Host, 'perfdata_file_template')]},
                'service_perfdata_file_template' : {'required':False, 'default':'/tmp/host.perf', 'class_inherit' : [(Service, 'perfdata_file_template')]},
                'host_perfdata_file_mode' : {'required':False, 'default':'a', 'pythonize': to_char, 'class_inherit' : [(Host, 'perfdata_file_mode')]},
                'service_perfdata_file_mode' : {'required':False, 'default':'a', 'pythonize': to_char, 'class_inherit' : [(Service, 'perfdata_file_mode')]},
                'host_perfdata_file_processing_interval' : {'required':False, 'default':'15', 'pythonize': to_int},
                'service_perfdata_file_processing_interval' : {'required':False, 'default':'15', 'pythonize': to_int},
                'host_perfdata_file_processing_command' : {'required':False, 'default':'', 'class_inherit' : [(Host, 'perfdata_file_processing_command')]},
                'service_perfdata_file_processing_command' : {'required':False, 'default':'', 'class_inherit' : [(Service, 'perfdata_file_processing_command')]},
                'check_for_orphaned_services' : {'required':False, 'default':'1', 'pythonize': to_bool, 'class_inherit' : [(Service, 'check_for_orphaned')]},
                'check_for_orphaned_hosts' : {'required':False, 'default':'1', 'pythonize': to_bool, 'class_inherit' : [(Host, 'check_for_orphaned')]},
                'check_service_freshness' : {'required':False, 'default':'1', 'pythonize': to_bool, 'class_inherit' : [(Service, 'check_freshness')]},
                'service_freshness_check_interval' : {'required':False, 'default':'60', 'pythonize': to_int},
                'check_host_freshness' : {'required':False, 'default':'1', 'pythonize': to_bool, 'class_inherit' : [(Host, 'check_freshness')]},
                'host_freshness_check_interval' : {'required':False, 'default':'60', 'pythonize': to_int},
                'additional_freshness_latency' : {'required':False, 'default':'15', 'pythonize': to_int, 'class_inherit' : [(Host, None), (Service, None)]},
                'enable_embedded_perl' : {'required':False, 'default':'1', 'pythonize': to_bool},
                'use_embedded_perl_implicitly' : {'required':False, 'default':'0', 'pythonize': to_bool},
                'date_format' : {'required':False, 'default':'us', 'class_inherit' : [(Host, None), (Service, None), (Contact, None)]},
                'use_timezone' : {'required':False, 'default':'FR/Paris', 'class_inherit' : [(Host, None), (Service, None), (Contact, None)]},
                'illegal_object_name_chars' : {'required':False, 'default':'/tmp/'},
                'illegal_macro_output_chars' : {'required':False, 'default':'', 'class_inherit' : [(Host, None), (Service, None), (Contact, None)]},
                'use_regexp_matching' : {'required':False, 'default':'1', 'pythonize': to_bool, 'class_inherit' : [(Host, None), (Service, None), (Contact, None)]},
                'use_true_regexp_matching' : {'required':False, 'default':'0', 'pythonize': to_bool, 'class_inherit' : [(Host, None), (Service, None), (Contact, None)]},
                'admin_email' : {'required':False, 'default':'admin@localhost'},
                'admin_pager' : {'required':False, 'default':''},
                'event_broker_options' : {'required':False, 'default':''},
                'broker_module' : {'required':False, 'default':''},
                'debug_file' : {'required':False, 'default':'/tmp/debug.txt'},
                'debug_level' : {'required':False, 'default':'0'},
                'debug_verbosity' : {'required':False, 'default':'1'},
                'max_debug_file_size' : {'required':False, 'default':'10000', 'pythonize': to_int},
                #'$USERn$ : {'required':False, 'default':''} # Add at run in __init__
                
                #SHINKEN SPECIFIC
                'idontcareaboutsecurity' : {'required':False, 'default':'0', 'pythonize': to_bool},
                'conf_is_correct' : {'required' : False, 'default' : '1', 'pythonize': to_bool},
    }


    macros = {
        'MAINCONFIGFILE' : '',
        'STATUSDATAFILE' : '',
        'COMMENTDATAFILE' : '',
        'DOWNTIMEDATAFILE' : '',
        'RETENTIONDATAFILE' : '',
        'OBJECTCACHEFILE' : '',
        'TEMPFILE' : '',
        'TEMPPATH' : '',
        'LOGFILE' : '',
        'RESOURCEFILE' : '',
        'COMMANDFILE' : '',
        'HOSTPERFDATAFILE' : '',
        'SERVICEPERFDATAFILE' : '',
        'ADMINEMAIL' : '',
        'ADMINPAGER' : ''
        #'USERn' : '$USERn$' # Add at run in __init__
        }


    def __init__(self):
        self.params = {}


    def fill_usern_macros(cls):
        #Now the ressource file part
        properties = cls.properties
        macros = cls.macros
        for n in xrange(1, 256):
            n = str(n)
            properties['$USER'+n+'$'] = {'required':False, 'default':''}
            macros['USER'+n] = '$USER'+n+'$'
    #Set this a Class method
    fill_usern_macros = classmethod(fill_usern_macros)



    def load_params(self, params):
        for elt in params:
            elts = elt.split('=')
            self.params[elts[0]] = elts[1]
            setattr(self, elts[0], elts[1])


    def _cut_line(self, line):
        #punct = '"#$%&\'()*+/<=>?@[\\]^`{|}~'
        tmp = re.split("[" + string.whitespace + "]+" , line)
        r = [elt for elt in tmp if elt != '']
        return r


    def _join_values(self, values):
        return ' '.join(values)


    def read_config(self, file):
        print "Opening config file", file
        #just a first pass to get the cfg_file and all files in a buf
        res = ''
        fd = open(file)
        buf = fd.readlines()
        fd.close()

        for line in buf:
            res += line
            line = line[:-1]
            if re.search("^cfg_file", line) or re.search("^resource_file", line):
                elts = line.split('=')
                try:
                    fd = open(elts[1])
                    res += fd.read()
                    fd.close()
                except IOError ,exp:
                    print exp
            elif re.search("^cfg_dir", line):
                elts = line.split('=')
                for root, dirs, files in os.walk(elts[1]):
                    for file in files:
                        if re.search("\.cfg$", file):
                            try:
                                fd = open(os.path.join(root, file))
                                res += fd.read()
                                fd.close()
                            except IOError, exp:
                                print exp
        self.read_config_buf(res)
        

    def read_config_buf(self, buf):
        params = []
        objectscfg = {'void': [],
                    'timeperiod' : [],
                    'command' : [],
                    'contactgroup' : [],
                    'hostgroup' : [],
                    'contact' : [],
                    'host' : [],
                    'service' : [],
                    'servicegroup' : [],
                    'servicedependency' : [],
                    'hostdependency' : [],
                    'scheduler' : [],
                    'reactionner' : [],
                    'broker' : [],
                    'poller' : [],
                    'realm' : [],
                    'module' : [],
                    'resultmodulation' : [],
                    'escalation' : []
                    }
        tmp = []
        tmp_type = 'void'
        in_define = False
        continuation_line = False
        tmp_line = ''
        lines = buf.split('\n')
        for line in lines:
            line = line.split(';')[0]
            #A backslash means, there is more to come
            if re.search("\\\s*$", line):
                continuation_line = True
                line = re.sub("\\\s*$", "", line)
                line = re.sub("^\s+", " ", line)
                tmp_line += line
                continue
            elif continuation_line:
                #Now the continuation line is complete
                line = re.sub("^\s+", "", line)
                line = tmp_line + line
                tmp_line = ''
                continuation_line = False
            if re.search("}", line):
                in_define = False
            if re.search("^#|^\s*$|^\s*}", line):
                pass
                        
            #A define must be catch and the type save
            #The old entry must be save before
            elif re.search("^define", line):
                in_define = True
                if tmp_type not in objectscfg:
                    objectscfg[tmp_type] = []
                objectscfg[tmp_type].append(tmp)
                tmp = []
                #Get new type
                elts = re.split('\s', line)
                tmp_type = elts[1]
                tmp_type = tmp_type.split('{')[0]
            else:
                if in_define:
                    tmp.append(line)
                else:
                    params.append(line)
                    
        objectscfg[tmp_type].append(tmp)
        objects = {}
        
        print "Params", params
        self.load_params(params)
        
        for type in objectscfg:
            objects[type] = []
            for items in objectscfg[type]:
                tmp = {}
                for line in items:
                    elts = self._cut_line(line)
                    if elts !=  []:
                        prop = elts[0]
                        value = self._join_values(elts[1:])
                        tmp[prop] = value
                if tmp != {}:
                    objects[type].append(tmp)
        
        #We create dict of objects
        #Type: 'name in objects' : {Class of object, Class of objects, 
        #'property for self for the objects(config)'
        types_creations = {'timeperiod' : (Timeperiod, Timeperiods, 'timeperiods'),
                           'service' : (Service, Services, 'services'),
                           'servicegroup' : (Servicegroup, Servicegroups, 'servicegroups'),
                           'command' : (Command, Commands, 'commands'),
                           'host' : (Host, Hosts, 'hosts'),
                           'hostgroup' : (Hostgroup, Hostgroups, 'hostgroups'),
                           'contact' : (Contact, Contacts, 'contacts'),
                           'contactgroup' : (Contactgroup, Contactgroups, 'contactgroups'),
                           'servicedependency' : (Servicedependency, Servicedependencies, 'servicedependencies'),
                           'hostdependency' : (Hostdependency, Hostdependencies, 'hostdependencies'),
                           'scheduler' : (SchedulerLink, SchedulerLinks, 'schedulerlinks'),
                           'reactionner' : (ReactionnerLink, ReactionnerLinks, 'reactionners'),
                           'broker' : (BrokerLink, BrokerLinks, 'brokers'),
                           'poller' : (PollerLink, PollerLinks, 'pollers'),
                           'realm' : (Realm, Realms, 'realms'),
                           'module' : (Module, Modules, 'modules'),
                           'resultmodulation' : (Resultmodulation, Resultmodulations, 'resultmodulations'),
                           'escalation' : (Escalation, Escalations, 'escalations'),
                           }
        #Ex: the above code do for timeperiods:
        #timeperiods = []
        #for timeperiodcfg in objects['timeperiod']:
        #    t = Timeperiod(timeperiodcfg)
        #    t.clean()
        #    timeperiods.append(t)
        #self.timeperiods = Timeperiods(timeperiods)

        for t in types_creations:
            (cls, clss, prop) = types_creations[t]
            #List where we put objects
            lst = []
            for obj_cfg in objects[t]:
                #We create teh object
                o = cls(obj_cfg)
                o.clean()
                lst.append(o)
            #we create the objects Class and we set it in prop
            setattr(self, prop, clss(lst))


        

    #We use linkify to make the config more efficient : elements will be
    #linked, like pointers. For example, a host will have it's service,
    #and contacts directly in it's properties
    #REMEMBER: linkify AFTER explode...
    def linkify(self):
        #Do the simplify AFTER explode groups
        print "Hostgroups"
        #link hostgroups with hosts
        self.hostgroups.linkify(self.hosts)

        print "Hosts"
        #link hosts with timeperiodsand commands
        self.hosts.linkify(self.timeperiods, self.commands, self.contacts, self.realms, self.resultmodulations, self.escalations)

        print "Services"
        #link services with hosts, commands, timeperiods, contacts and resultmodulations
        self.services.linkify(self.hosts, self.commands, self.timeperiods, self.contacts, self.resultmodulations, self.escalations)

        print "Service groups"
        #link servicegroups members with services
        self.servicegroups.linkify(self.services)

        print "Contactgroups"
        #link contacgroups with contacts
        self.contactgroups.linkify(self.contacts)

        print "Contacts"
        #link contacts with timeperiods and commands
        self.contacts.linkify(self.timeperiods, self.commands)

        print "Timeperiods"
        #link timeperiods with timeperiods (exclude part)
        self.timeperiods.linkify()

        print "Servicedependancy"
        self.servicedependencies.linkify(self.hosts, self.services, self.timeperiods)

        print "Resultmodulations"
        self.resultmodulations.linkify(self.timeperiods)

        print "Escalations"
        self.escalations.linkify(self.timeperiods)

        print "Realms"
        self.realms.linkify()

        print "Schedulers and satellites"
        #Link all links with realms
        self.schedulerlinks.linkify(self.realms, self.modules)
        self.brokers.linkify(self.realms, self.modules)
        self.reactionners.linkify(self.realms, self.modules)
        self.pollers.linkify(self.realms, self.modules)


    def dump(self):
        #print 'Parameters:', self
        #print 'Hostgroups:',self.hostgroups,'\n'
        #print 'Services:', self.services
        print 'Hosts:'
        for h in self.hosts:
            print '\t',h.get_name()
        print 'Services:'
        for s in self.services:
            print '\t',s.get_name()
        #print 'Templates:', self.hosts_tpl
        #print 'Hosts:',self.hosts,'\n'
        #print 'Contacts:', self.contacts
        #print 'contactgroups',self.contactgroups
        #print 'Servicegroups:', self.servicegroups
        #print 'Timepriods:', self.timeperiods
        #print 'Commands:', self.commands
        #print "Number of services:", len(self.services.items)
        #print "Service Dep", self.servicedependencies
        #print "Schedulers", self.schedulerlinks


    #Use to fill groups values on hosts and create new services
    #(for host group ones)
    def explode(self):
        #first elements, after groups
        print "Contacts"
        self.contacts.explode(self.contactgroups)
        print "Contactgroups"
        self.contactgroups.explode()

        print "Hosts"
        self.hosts.explode(self.hostgroups, self.contactgroups)
        print "Hostgroups"
        self.hostgroups.explode()

        print "Services"
        print "Initialy got nb of services : %d" % len(self.services.items)
        self.services.explode(self.hostgroups, self.contactgroups, self.servicegroups)
        #print "finally got nb of services : %d" % len(self.services.items)
        print "Servicegroups"
        self.servicegroups.explode()

        print "Timeperiods"
        self.timeperiods.explode()

        print "Servicedependancy"
        self.servicedependencies.explode()

        #Now the architecture part
        print "Realms"
        self.realms.explode()
        

    #Remove elements will the same name, so twins :)
    def remove_twins(self):
        self.hosts.remove_twins()
        self.services.remove_twins()
        self.contacts.remove_twins()
        self.timeperiods.remove_twins()


    #Dependancies are importants for scheduling
    #This function create dependencies linked between elements.
    def apply_dependancies(self):
        self.hosts.apply_dependancies()
        self.services.apply_dependancies()


    #Use to apply inheritance (template and implicit ones)
    #So elements wil have their configured properties
    def apply_inheritance(self):
        #inheritance properties by template
        print "Hosts"
        self.hosts.apply_inheritance()
        print "Contacts"
        self.contacts.apply_inheritance()
        print "Services"
        self.services.apply_inheritance(self.hosts)


    #Use to apply implicit inheritance
    def apply_implicit_inheritance(self):
        print "Services"
        self.services.apply_implicit_inheritance(self.hosts)


    #will fill propeties for elements so they wil have all theirs properties
    def fill_default(self):
        #Fill default for config (self)
        super(Config, self).fill_default()
        self.hosts.fill_default()
        self.hostgroups.fill_default()
        self.contacts.fill_default()
        self.contactgroups.fill_default()
        self.services.fill_default()
        self.servicegroups.fill_default()
        self.resultmodulations.fill_default()
        #first we create missing sat, so no other sat will
        #be created after this point
        self.fill_default_satellites()
        #now we have all elements, we can create a default 
        #realm if need and it will be taged to sat that do
        #not have an realm
        self.fill_default_realm()
        self.reactionners.fill_default()
        self.pollers.fill_default()
        self.brokers.fill_default()
        self.schedulerlinks.fill_default()


        
    #Will check if a realm is defined, if not
    #Create a new one (default) and tag everyone that do not have
    #a realm prop to be put in this realm
    def fill_default_realm(self):
        if len(self.realms) == 0:
            #Create a default realm with default value =1
            #so all hosts without realm wil be link with it
            default = Realm({'realm_name' : 'Default', 'default' : '1'})
            self.realms = Realms([default])
            print "I make a new realm", self.realms
            lists = [self.pollers, self.brokers, self.reactionners, self.schedulerlinks]
            for l in lists:
                for elt in l:
                    if not hasattr(elt, 'realm'):
                        elt.realm = 'Default'
                        print "Tagging ", elt.get_name(), 'with', default.get_name()
                    else:
                        print "Not tagging",  elt.get_name(), ' because it gots:', elt.realm


    #If a satellite is missing, we add them in the localhost
    #with defaults values
    def fill_default_satellites(self):
        if len(self.schedulerlinks) == 0:
            print "Warning : there is no scheduler, I add one in localhost:7768"
            s = SchedulerLink({'scheduler_name' : 'Default-Scheduler', 'address' : 'localhost', 'port' : '7768'})
            self.schedulerlinks = SchedulerLinks([s])
        if len(self.pollers) == 0:
            print "Warning : there is no poller, I add one in localhost:7771"
            p = PollerLink({'poller_name' : 'Default-Poller', 'address' : 'localhost', 'port' : '7771'})
            self.pollers = PollerLinks([p])
        if len(self.reactionners) == 0:
            print "Warning : there is no reactionner, I add one in localhost:7769"
            r = ReactionnerLink({'reactionner_name' : 'Default-Reactionner', 'address' : 'localhost', 'port' : '7769'})
            self.reactionners = ReactionnerLinks([r])
        if len(self.brokers) == 0:
            print "Warning : there is no broker, I add one in localhost:7772"
            b = BrokerLink({'broker_name' : 'Default-Broker', 'address' : 'localhost', 'port' : '7772'})
            self.brokers = BrokerLinks([b])


    #Link templates with elements
    def linkify_templates(self):
        self.hosts.linkify_templates()
        self.contacts.linkify_templates()
        self.services.linkify_templates()
        

    #Reversed list is a dist with name for quick search by name
    def create_reversed_list(self):
        self.hosts.create_reversed_list()
        self.contacts.create_reversed_list()
        self.services.create_reversed_list()
        self.timeperiods.create_reversed_list()
        self.modules.create_reversed_list()
        self.resultmodulations.create_reversed_list()
        self.escalations.create_reversed_list()
        #For services it's a special case
        #we search for hosts, then for services
        #it's quicker than search in al services
        self.services.optimize_service_search(self.hosts)


    #check if elements are correct or no (fill with defaults, etc)
    #Warning : this function call be called from a Arbiter AND
    #from and scheduler. The first one got everything, the second
    #do not have the satellites.
    def is_correct(self):
        r = self.conf_is_correct
        r &= self.hosts.is_correct()
        r &= self.hostgroups.is_correct()
        r &= self.contacts.is_correct()
        r &= self.contactgroups.is_correct()
        r &= self.schedulerlinks.is_correct()
        r &= self.services.is_correct()
        r &= self.servicegroups.is_correct()
        if hasattr(self, 'reactionners'):
            r &= self.reactionners.is_correct()
        if hasattr(self, 'pollers'):
            r &= self.pollers.is_correct()
        if hasattr(self, 'brokers'):
            r &= self.brokers.is_correct()
        r &= self.timeperiods.is_correct()
        self.conf_is_correct = r


    #We've got strings (like 1) but we want pthon elements, like True
    def pythonize(self):
        #call item pythonize for parameters
        super(Config, self).pythonize()
        self.hosts.pythonize()
        self.hostgroups.pythonize()
        self.contactgroups.pythonize()
        self.contacts.pythonize()
        self.services.pythonize()
        self.servicedependencies.pythonize()
        self.resultmodulations.pythonize()
        self.schedulerlinks.pythonize()
        self.realms.pythonize()
        self.reactionners.pythonize()
        self.pollers.pythonize()
        self.brokers.pythonize()


    #Explode parameters like cached_service_check_horizon in the
    #Service class in a cached_check_horizon manner
    def explode_global_conf(self):
        Service.load_global_conf(self)
        Host.load_global_conf(self)
        Contact.load_global_conf(self)


    #Clean useless elements like templates because they are not need anymore
    def clean_useless(self):
        self.hosts.clean_useless()
        self.contacts.clean_useless()
        self.services.clean_useless()


    #Create packs of hosts an services so in a pack, 
    #all dependencies are resolved
    #It create a graph. All hosts are connected to theyre
    #parents, and host witouht parent are connected to host 'root'
    #services are link to the host. Dependencies are managed
    def create_packs(self, nb_packs):
        #We create a grah with host in nodes
        g = Graph()
        g.add_nodes(self.hosts)
        
        #links will be used for relations between hosts
        links = set()

        #Now the relations
        for h in self.hosts:
            #Add parent relations
            for p in h.parents:
                if p is not None:
                    links.add((p, h))
            #Add the others dependencies
            for (dep, tmp, tmp2, tmp3) in h.act_depend_of:
                links.add((dep, h))
            for (dep, tmp, tmp2, tmp3) in h.chk_depend_of:
                links.add((dep, h))

        #For services : they are link woth their own host but we need
        #To have the hosts of service dep in the same pack too
        for s in self.services:
            for (dep, tmp, tmp2, tmp3) in s.act_depend_of:
                #I don't care about dep host: they are just the host
                #of the service...
                if hasattr(dep, 'host'):
                    links.add((dep.host, s.host))
            #The othe type of dep
            for (dep, tmp, tmp2, tmp3) in s.chk_depend_of:
                links.add((dep.host, s.host))
        
        #Now we create links in the graph. With links (set)
        #We are sure to call the less add_edge
        for (dep, h) in links:
            g.add_edge(dep, h)
            g.add_edge(h, dep)
        
        #Access_list from a node il all nodes that are connected
        #with it : it's a list of ours mini_packs
        tmp_packs = g.get_accessibility_packs()

        #Now We find the default realm (must be unique or
        #BAD THINGS MAY HAPPEN
        default_realm = None
        for r in self.realms:
            if hasattr(r, 'default') and r.default:
                default_realm = r

        #Now we look if all elements of all packs have the
        #same realm. If not, not good!
        for pack in tmp_packs:
            tmp_realms = set()
            for elt in pack:
                if elt.realm!= None:
                    tmp_realms.add(elt.realm)
            if len(tmp_realms) > 1:
                print "Error : the realm configuration of yours hosts if not good"
                for h in pack:
                    if h.realm == None:
                        print h.get_name(), None
                    else:
                        print h.get_name(), h.realm.get_name()
            if len(tmp_realms) == 1: # Ok, good
                r = tmp_realms.pop() #There is just one element
                print "Add to realm", r
                r.packs.append(pack)
            elif len(tmp_realms) == 0: #Hum.. no realm value? So default Realm
                if default_realm != None:
                    #print "I prefer add to default realm", default_realm.get_name()
                    default_realm.packs.append(pack)
                else:
                    print "Error : Hosts do not have a realm and you do not defined a default realm!"

        #The load balancing is for a loop, so all
        #hosts of a realm (in a pack) will be dispatch
        #in the schedulers of this realm
        for r in self.realms:
            print "Load balancing realm", r.get_name()
            packs = {}
            #create roundrobin iterator for id of cfg
            #So dispatching is loadbalanced in a realm
            #but add a entry in the roundrobin tourniquet for 
            #every weight point schedulers (so Weight round robin)
            weight_list = []
            no_spare_schedulers = [s for s in r.schedulers if not s.spare]
            nb_schedulers = len(no_spare_schedulers)
            
            #Maybe there is no scheduler in the realm, it's can be a
            #big problem if there are elements in packs
            nb_elements = len([elt for elt in [pack for pack in r.packs]])
            print "Number of hosts in the realm :", nb_elements
            if nb_schedulers == 0 and nb_elements != 0:
                print "ERROR : The realm", r.get_name(), "have hosts but no scheduler!"
                r.packs = [] #Dumb pack
                continue
            
            packindex = 0
            packindices = {}
            for s in no_spare_schedulers:
                packindices[s.id] = packindex
                packindex += 1
                for i in xrange(0, s.weight):
                    weight_list.append(s.id)

            rr = itertools.cycle(weight_list)
            
            #we must have nb_schedulers packs)
            for i in xrange(0, nb_schedulers):
                packs[i] = []
                
            #Now we explode the numerous packs into nb_packs reals packs:
            #we 'load balance' thems in a roundrobin way
            for pack in r.packs:
                i = rr.next()
                for elt in pack:
                    packs[packindices[i]].append(elt)
            #Now in packs we have the number of packs [h1, h2, etc]
            #equal to the number of schedulers.
            r.packs = packs



    #Use the self.conf and make nb_parts new confs.
    #nbparts is equal to the number of schedulerlink
    #New confs are independant whith checks. The only communication
    #That can be need is macro in commands
    def cut_into_parts(self):
        #print "Scheduler configurated :", self.schedulerlinks
        #I do not care about alive or not. User must have set a spare if need it
        nb_parts = len([s for s in self.schedulerlinks if not s.spare])

        if nb_parts == 0:
            nb_parts = 1

        print "Creating confs"
        self.confs = {}
        for i in xrange(0, nb_parts):
            print "Create Conf:", i, '/', nb_parts -1
            self.confs[i] = Config()

            #Now we copy all properties of conf into the new ones
            for prop in Config.properties:
                val = getattr(self, prop)
                setattr(self.confs[i], prop, val)
            
            #we need a deepcopy because each conf
            #will have new hostgroups
            self.confs[i].id = i
            self.confs[i].commands = self.commands
            self.confs[i].timeperiods = self.timeperiods
            #Create hostgroups with just the name and same id, but no members
            new_hostgroups = []
            for hg in self.hostgroups:
                new_hostgroups.append(hg.copy_shell())
            self.confs[i].hostgroups = Hostgroups(new_hostgroups)
            self.confs[i].contactgroups = self.contactgroups
            self.confs[i].contacts = self.contacts
            self.confs[i].schedulerlinks = copy.copy(self.schedulerlinks)
            #Create hostgroups with just the name and same id, but no members
            new_servicegroups = []
            for sg in self.servicegroups:
                new_servicegroups.append(sg.copy_shell())
            self.confs[i].servicegroups = Servicegroups(new_servicegroups)
            self.confs[i].hosts = [] #will be fill after
            self.confs[i].services = [] #will be fill after
            self.confs[i].other_elements = {} # The elements of the others
                                              #conf will be tag here
            self.confs[i].is_assigned = False #if a scheduler have
                                              #accepted the conf

        print "Creating packs"
        
        #Just create packs. There can be numerous ones
        #In pack we've got hosts and service
        #packs are in the realms
        self.create_packs(nb_parts)
        
        offset = 0
        for r in self.realms:
            for i in r.packs:
                pack = r.packs[i]
                for h in pack:
                    self.confs[i+offset].hosts.append(h)
                    for s in h.services:
                        self.confs[i+offset].services.append(s)
                #Now the conf can be link in the realm
                r.confs[i+offset] = self.confs[i+offset]
            offset += len(r.packs)
            del r.packs
        
        #We've nearly have hosts and services. Now we want REALS hosts (Class)
        #And we want groups too
        print "Finishing packs"
        for i in self.confs:
            print "Finishing pack Nb:", i
            cfg = self.confs[i]

            #Create ours classes
            cfg.hosts = Hosts(cfg.hosts)
            cfg.hosts.create_reversed_list()
            cfg.services = Services(cfg.services)
            cfg.services.create_reversed_list()
            #Fill host groups
            for ori_hg in self.hostgroups:
                hg = cfg.hostgroups.find_by_name(ori_hg.get_name())
                mbrs = ori_hg.members
                mbrs_id = []
                for h in mbrs:
                    if h is not None:
                        mbrs_id.append(h.id)
                for h in cfg.hosts:
                    if h.id in mbrs_id:
                        hg.members.append(h)
            #Fill servicegroup
            for ori_sg in self.servicegroups:
                sg = cfg.servicegroups.find_by_name(ori_sg.get_name())
                mbrs = ori_sg.members
                mbrs_id = []
                for s in mbrs:
                    if s is not None:
                        mbrs_id.append(s.id)
                for s in cfg.services:
                    if s.id in mbrs_id:
                        sg.members.append(s)

        #Now we fill other_elements by host (service are with their host
        #so they are not tagged)
        for i in self.confs:
            for h in self.confs[i].hosts:
                for j in [j for j in self.confs if j != i]: #So other than i
                    self.confs[i].other_elements[h.get_name()] = i

        #We tag conf with isntance_id
	#TODO : fix ninja/merlin so it manage more than instance_id == 0 ....
        for i in self.confs:
            self.confs[i].instance_id = 0#i

