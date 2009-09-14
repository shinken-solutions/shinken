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

import os, sys, re, time, string, copy
import pygraph
import itertools

from timeperiod import Timeperiod,Timeperiods
from service import Service,Services
from command import Command,Commands
from host import Host,Hosts
from hostgroup import Hostgroup,Hostgroups
from contact import Contact,Contacts
from contactgroup import Contactgroup,Contactgroups
from servicegroup import Servicegroup,Servicegroups
from item import Item
from macroresolver import MacroResolver
from borg import Borg
from singleton import Singleton
from servicedependency import Servicedependency, Servicedependencies
from hostdependency import Hostdependency, Hostdependencies
from schedulerlink import SchedulerLink, SchedulerLinks
from reactionnerlink import ReactionnerLink, ReactionnerLinks
from brokerlink import BrokerLink, BrokerLinks
from pollerlink import PollerLink, PollerLinks

from util import to_int, to_char, to_split, to_bool
#import psyco
#psyco.full()


class Config(Item):
    cache_path = "objects.cache"

    #Properties: 
    #required : if True, there is not default, and the config must put them
    #default: if not set, take this value
    #pythonize : function call to 
    #class_inherit : (Service, 'blabla') : must set this propertie to the Service class with name blabla
    #if (Service, None) : must set this properti to the Service class with same name
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
                'cached_host_check_horizon' : {'required':False, 'default':'15', 'pythonize': to_int, 'class_inherit' : [(Host, 'cached_check_horizon')]},
                'cached_service_check_horizon' : {'required':False, 'default':'15', 'pythonize': to_int, 'class_inherit' : [(Service, 'cached_check_horizon')]},
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
                'max_debug_file_size' : {'required':False, 'default':'10000', 'pythonize': to_int}
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
        }


    def __init__(self):
        self.params = {}


    def load_params(self, params):
        for elt in params:
            elts = elt.split('=')
            self.params[elts[0]] = elts[1]
            setattr(self, elts[0], elts[1])


    def _cut_line(self, line):
        punct = '"#$%&\'()*+/<=>?@[\\]^`{|}~'
        tmp = re.split("[" + string.whitespace + "]+" , line)
        r = [elt for elt in tmp if elt != '']
        return r


    def _join_values(self, values):
        return ' '.join(values)


    def read_config(self, file):
        print "Opening config file", file
        #just a first pass to get the cfg_file and all files in a buf
        res = ''
        fd=open(file)
        buf=fd.readlines()
        fd.close()
        #res += buf
        for line in buf:
            res += line
            line = line[:-1]
            if re.search("^cfg_file", line):
                elts = line.split('=')
                try:
                    fd = open(elts[1])
                    res += fd.read()
                    fd.close()
                except IOError ,exp:
                    print exp
        #print "Got", res
        self.read_config_buf(res)
        

    def read_config_buf(self, buf):
        params=[]
        objectscfg={'void': [],
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
                    'poller' : []
                    }
        
        
        #print "I search :", objectscfg
        tmp=[]
        tmp_type='void'
        in_define = False
        lines = buf.split('\n')
        for line in lines:#buf.readlines():
            #line = line[:-1]

            line=line.split(';')[0]
            if re.search("}",line):
                in_define = False
            if re.search("^#|^$|}", line):
                pass
                        
            #A define must be catch and the type save
            #The old entry must be save before
            elif re.search("^define", line):
                in_define = True
                
                objectscfg[tmp_type].append(tmp)
                tmp=[]
                #Get new type
                elts = re.split('\s', line)
                tmp_type = elts[1]
                #print "Add a", tmp_type, ":", tmp
                tmp_type = tmp_type.split('{')[0]
                #print "Add a", tmp_type, ":", tmp
            else:
                if in_define:
                    #if tmp_type == 'servicedependency':
                    #    print 'ADD A NEW LINE', line
                    tmp.append(line)
                else:
                    params.append(line)
                    
        objectscfg[tmp_type].append(tmp)
                #print 'Add line', line
        objects = {}
        
        #print "Debug:", objectscfg
        print "Params",params
        self.load_params(params)
        
        for type in objectscfg:
            #if type == 'servicedependency':
                #print "SERVICE DEP!", objectscfg[type]
            objects[type]=[]
            #print 'Doing type:',type
            for items in objectscfg[type]:
                #print 'Items:', items
                tmp={}
                for line in items:
                    elts = self._cut_line(line)
                    if elts !=  []:
                        #print "Got elts:", elts
                        prop = elts[0]
                        value = self._join_values(elts[1:])
                        tmp[prop] = value
                        #print 'Add', prop, 'Val:', value
                if tmp != {}:
                    #print 'Append:', tmp, '\n\n'
                    objects[type].append(tmp)
        
        #print 'Objects:', objects['service']
        #print "Nb of services:", len(objects['service'])
    
        #We create dict of objects
        timeperiods = []
        for timeperiodcfg in objects['timeperiod']:
            t = Timeperiod(timeperiodcfg)
            t.clean()
            timeperiods.append(t)
        self.timeperiods = Timeperiods(timeperiods)
        
        services = []
        #services_tpl = []
        for servicecfg in objects['service']:
            s = Service(servicecfg)
            s.clean()
            #if s.is_tpl():
            services.append(s)
            #else:
            #    services_tpl.append(s)
        self.services = Services(services)
        #self.services_tpl = Services(services_tpl)

        servicegroups = []
        #services_tpl = []
        for servicegroupcfg in objects['servicegroup']:
            sg = Servicegroup(servicegroupcfg)
            sg.clean()
            #if s.is_tpl():
            servicegroups.append(sg)
            #else:
            #    services_tpl.append(s)
        self.servicegroups = Servicegroups(servicegroups)
        #self.services_tpl = Services(services_tpl)

        
        commands = []
        for commandcfg in objects['command']:
            c = Command(commandcfg)
            c.clean()
            commands.append(c)
            #print "Creating command", c
        self.commands = Commands(commands)
        
        hosts = []
        #hosts_tpl = []
        for hostcfg in objects['host']:
            h = Host(hostcfg)
            h.clean()
            #if h.is_tpl():
            #    hosts_tpl.append(h)
            #else:
            hosts.append(h)
        self.hosts = Hosts(hosts)
        #self.hosts_tpl = Hosts(hosts_tpl)

        hostgroups = []
        for hostgroupcfg in objects['hostgroup']:
            hg = Hostgroup(hostgroupcfg)
            hg.clean()
            hostgroups.append(hg)
        self.hostgroups = Hostgroups(hostgroups)
        
        contacts = []
        for contactcfg in objects['contact']:
            c = Contact(contactcfg)
            c.clean()
            contacts.append(c)
        self.contacts = Contacts(contacts)
        
        contactgroups = []
        for contactgroupcfg in objects['contactgroup']:
            cg = Contactgroup(contactgroupcfg)
            cg.clean()
            contactgroups.append(cg)
        self.contactgroups = Contactgroups(contactgroups)

        servicedependencies = []
        #print objects
        for servicedependencycfg in objects['servicedependency']:
            sd = Servicedependency(servicedependencycfg)
            sd.clean()
            servicedependencies.append(sd)
        self.servicedependencies = Servicedependencies(servicedependencies)

        hostdependencies = []
        for hostdependencycfg in objects['hostdependency']:
            hd = Servicedependency(hostdependencycfg)
            hd.clean()
            hostdependencies.append(hd)
        self.hostdependencies = Hostdependencies(hostdependencies)

        schedulerlinks = []
        for sched_link in objects['scheduler']:
            sl = SchedulerLink(sched_link)
            sl.clean()
            schedulerlinks.append(sl)
        self.schedulerlinks = SchedulerLinks(schedulerlinks)

        reactionners = []
        for reactionner_link in objects['reactionner']:
            ral = ReactionnerLink(reactionner_link)
            ral.clean()
            reactionners.append(ral)
        self.reactionners = ReactionnerLinks(reactionners)

        brokers = []
        for broker_link in objects['broker']:
            rbl = BrokerLink(broker_link)
            rbl.clean()
            brokers.append(rbl)
        self.brokers = BrokerLinks(brokers)

        pollerlinks = []
        for poller_link in objects['poller']:
            pl = PollerLink(poller_link)
            pl.clean()
            pollerlinks.append(pl)
        self.pollers = PollerLinks(pollerlinks)


    #We use linkify to make the config smaller (not name but direct link when possible)
    def linkify(self):
        #Do the simplify AFTER explode groups
        print "Hostgroups"
        #link hostgroups with hosts
        self.hostgroups.linkify(self.hosts)

        print "Hosts"
        #link hosts with timeperiodsand commands
        self.hosts.linkify(self.timeperiods, self.commands, self.contacts)

        print "Service groups"
        #link servicegroups members with services
        self.servicegroups.linkify(self.services)

        print "Services"
        #link services with hosts, commands, timeperiods and contacts
        self.services.linkify(self.hosts, self.commands, self.timeperiods, self.contacts)

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
        

    def dump(self):
        #print 'Parameters:', self
        #print 'Hostgroups:',self.hostgroups,'\n'
        print 'Services:', self.services
        #print 'Templates:', self.hosts_tpl
        #print 'Hosts:',self.hosts,'\n'
        #print 'Contacts:', self.contacts
        #print 'contactgroups',self.contactgroups
        #print 'Servicegroups:', self.servicegroups
        #print 'Timepriods:', self.timeperiods
        #print 'Commands:', self.commands
        #print "Number of services:", len(self.services.items)
        #print "Service Dep", self.servicedependencies
        print "Schedulers", self.schedulerlinks
        pass

    #Use to fill groups values on hosts and create new services (for host group ones)
    def explode(self):
        #first elements, after groups

        #hosts = time.time()
        #self.contactgroups.explode()
        #contactgroups = time.time()

        print "Contacts"
        self.contacts.explode(self.contactgroups)

        print "Contactgroups"
        self.contactgroups.explode()
        #contacts = time.time()

        print "Hosts"
        self.hosts.explode(self.hostgroups, self.contactgroups)
        print "Hostgroups"
        self.hostgroups.explode()

        print "Services"
        print "Initialy got nb of services : %d" % len(self.services.items)
        self.services.explode(self.hostgroups, self.contactgroups, self.servicegroups)
        print "finally got nb of services : %d" % len(self.services.items)

        print "Servicegroups"
        self.servicegroups.explode()

        print "Timeperiods"
        self.timeperiods.explode()

        print "Servicedependancy"
        self.servicedependencies.explode()
        #services = time.time()
        #print "Time: Overall Explode :", services-begin, " (hosts:",hosts-begin," ) (contactgroups:",contactgroups-hosts," ) (contacts:",contacts-contactgroups," ) (services:",services-contacts,")"        


    def apply_dependancies(self):
        self.hosts.apply_dependancies()
        self.services.apply_dependancies()


    #Use to apply inheritance (template and implicit ones)
    def apply_inheritance(self):
        #inheritance properties by template
        #begin = time.time()
        print "Hosts"
        self.hosts.apply_inheritance()
        #hosts = time.time()
        print "Contacts"
        self.contacts.apply_inheritance()
        #contacts = time.time()
        print "Services"
        self.services.apply_inheritance(self.hosts)
        #services = time.time()
        #print "Time: Overall Inheritance :", services-begin, " (hosts:",hosts-begin," ) (contacts:",contacts-hosts," ) (services:",services-contacts,")"

    def fill_default(self):
        super(Config, self).fill_default()
        self.hosts.fill_default()
        self.contacts.fill_default()
        self.services.fill_default()


    def create_templates_list(self):
        self.hosts.create_tpl_list()
        self.contacts.create_tpl_list()
        self.services.create_tpl_list()
        

    def create_reversed_list(self):
        self.hosts.create_reversed_list()
        self.contacts.create_reversed_list()
        self.services.create_reversed_list()
        self.timeperiods.create_reversed_list()


    def is_correct(self):
        self.hosts.is_correct()
        self.hostgroups.is_correct()
        self.contacts.is_correct()
        self.contactgroups.is_correct()
        self.schedulerlinks.is_correct()
        self.services.is_correct()


    def pythonize(self):
        #call item pythonize for parameters
        super(Config, self).pythonize()
        #begin = time.time()
        self.hosts.pythonize()
        #hosts = time.time()
        self.hostgroups.pythonize()
        #hostgroups = time.time()
        self.contactgroups.pythonize()
        #contactgroups = time.time()
        self.contacts.pythonize()
        #contacts = time.time()
        self.services.pythonize()
        self.servicedependencies.pythonize()
        self.schedulerlinks.pythonize()
        #services = time.time()
        #print "Time: Overall Pythonize :", services-begin, " (hosts:",hosts-begin," ) (hostgroups:",hostgroups-hosts,") (contactgroups:",contactgroups-hostgroups," ) (contacts:",contacts-contactgroups," ) (services:",services-contacts,")"

    #Explode parameters like cached_service_check_horizon in the Service class in a cached_check_horizon manner
    def explode_global_conf(self):
        Service.load_global_conf(self)
        Host.load_global_conf(self)
        Contact.load_global_conf(self)


    def clean_useless(self):
        self.hosts.clean_useless()
        self.contacts.clean_useless()
        self.services.clean_useless()


    #Create packs of hosts an services so in a pack, 
    #all dependencies are resolved
    #It create a graph. All hosts are connected to theyre
    #parents, and host witouht parent are connected to host 'root'
    #services are link to the host. Dependencies are managed
    def create_packs(self):
        g = pygraph.digraph()
        #The master node
        g.add_node('root')

        #Node that are not directy connected to the root
        indirect_nodes = set()#[]#Spped up instead of []

        for h in self.hosts:
            #print "Doing host", h.host_name, h.id
            #if h not in g:
            #    print "Adding", h.host_name
            g.add_node(h)
            g.add_edge('root', h)

            for p in h.parents:
                if p is not None:
                    if p not in g:
                        #print "Adding", p.host_name
                        g.add_node(p)
                    g.add_edge(p, h)
                    #print "My parent:", p.host_name
                    #if h not in indirect_nodes:
                        #indirect_nodes.append(h)
                    indirect_nodes.add(h)

            for (dep, tmp, tmp2, tp3) in h.act_depend_of:
                #print "My dep", dep.host_name
                #if dep not in g:
                #    print "Adding", dep.host_name
                g.add_node(dep)
                g.add_edge(dep, h)
                #if h not in indirect_nodes:
                    #indirect_nodes.append(h)
                indirect_nodes.add(h)

            for (dep, tmp, tmp2, tp3) in h.chk_depend_of:
                #print "My dep", dep.host_name
                #if dep not in g:
                #    print "Adding", dep.host_name
                g.add_node(dep)
                g.add_edge(dep, h)
                #if h not in indirect_nodes:
                    #indirect_nodes.append(h)
                indirect_nodes.add(h)            

            for s in h.services:
                #if s not in g:
                g.add_node(s)
                g.add_edge(h,s)

        for s in self.services:
            #print "Doing Service:", s.get_name()
            #if s not in g:
            g.add_node(s) # Not a pb if already exist
            for (dep, tmp, tmp2, tp3) in s.act_depend_of:
                #if dep not in g:
                g.add_node(dep)
                g.add_edge(dep, s)
            for (dep, tmp, tmp2, tp3) in s.chk_depend_of:
                #if dep not in g:
                g.add_node(dep)
                g.add_edge(dep, s)

        #print "G:", len(g), g.nodes()

        #We delete link between indirect node and the root
        for h in indirect_nodes:
            g.del_edge('root', h)

        #print "Indirect:"
        #for h in indirect_nodes:
        #    print "Indirect node:", h.host_name
        #print "Nb hosts:", len(self.hosts)
        #print 'first level'
        packs = []
        for h in g.neighbors('root'): # First level nodes
            (tmp, pack, tmp2) = pygraph.algorithms.searching.depth_first_search(g, root=h)#self.parents)#.find_cycle()g.depth_first_search(h)
            #print "TMP:", pack
            packs.append(pack)

        #print "G:", g
        #print "*******Dumping All Packs*****", "Number of packs:", len(packs)
        #for pack in packs:
            #print "Pack", pack, "len:", len(pack)
            #for h in pack:
            #    print h.get_name()
        #print "Fin all packs"
        return packs


    #Use the self.conf and make nb_parts new confs.
    #nbparts is equal to the number of schedulerlink
    #New confs are independant whith checks. The only communication
    #That can be need is macro in commands
    def cut_into_parts(self):
        #print "Scheduler configurated :", self.schedulerlinks
        nb_parts = len([s for s in self.schedulerlinks if not s.spare and s.is_alive()])
        #print "Cutting into", nb_parts, "parts"

        if nb_parts == 0:
            nb_parts = 1
        
        self.confs = {}
        for i in xrange(0, nb_parts):
            #print "Create Conf:", i, nb_parts
            self.confs[i] = Config()
            
            #Now we copy all properties of conf into the new ones
            for prop in Config.properties:
                val = getattr(self, prop)
                setattr(self.confs[i], prop, val)
            
            #we need a deepcopy because each conf
            #will have new hostgroups
            self.confs[i].commands = self.commands
            self.confs[i].timeperiods = self.timeperiods
            self.confs[i].hostgroups = copy.deepcopy(self.hostgroups) #TODO just copy?
            self.confs[i].contactgroups = self.contactgroups
            self.confs[i].contacts = self.contacts
            self.confs[i].schedulerlinks = copy.copy(self.schedulerlinks)
            self.confs[i].servicegroups = copy.deepcopy(self.servicegroups)#TODO just copy?
            self.confs[i].hosts = []#will be Classified after
            self.confs[i].services = []
            self.confs[i].other_elements = {}
            self.confs[i].is_assigned = False #if a scheduler have accepted the conf

        #just create packs. There can be numerous ones
        packs = self.create_packs()

        #create roundrobin iterator for id of cfg
        rr = itertools.cycle(list(xrange(0, nb_parts)))

        #Now we explode packs into confs, and we 'load balance' thems
        for pack in packs:
            i = rr.next()
            #print "Load balancing conf ", i
            for elt in pack:
                if isinstance(elt, Service):
                    self.confs[i].services.append(elt)
                else:
                    self.confs[i].hosts.append(elt)
        
        for i in self.confs:
            #print "Finishing packs", i
            cfg = self.confs[i]

            for hg in cfg.hostgroups:
                mbrs = hg.members
                hg.members = []

                for h in cfg.hosts:
                    if h in mbrs:
                        hg.members.append(h)
                        #print "Set", h.get_name(), "to be add"
                #print "Removing hosts in hostgroup", hosts_to_del
                #for h in hg.members:
                #    print "We've got member:", h.host_name
            
            for sg in cfg.servicegroups:
                mbrs = sg.members
                sg.members = []
                for s in cfg.services:
                    if s in mbrs:
                        sg.members.append(s)
                        #print "Set", s.get_name(), "to be add"
                #print "Removing hosts in hostgroup", hosts_to_del
                #for s in sg.members:
                #    print "We've got member:", s.get_name()

            cfg.hosts = Hosts(cfg.hosts)
            cfg.services = Services(cfg.services)
            #print "CFG:", cfg, "Nb elments:", len(cfg.hosts) + len(cfg.services)
            #print cfg.hostgroups

        #print "Finishing Conf"

        #Now we fill other_elements by host (service are with their host)
        for i in self.confs:
            #print "Doing",  i
            for h in self.confs[i].hosts:
                #print "Doing h", h.get_name(), [j for j in self.confs if j != i]
                for j in [j for j in self.confs if j != i]:
                    #print "*********Add", h.get_name(), "in the conf", j
                    self.confs[i].other_elements[h.get_name()] = i

        #We tag conf with isntance_id
        for i in self.confs:
            self.confs[i].instance_id = i

        #print "HeheConf:", self, "Confs:", self.confs
        #for cfg in self.confs.values():
            #for h in cfg.hosts:
                #print "DBG: host", h
                #print "DBG2: ", h.get_name(), h.check_command, h.check_command.is_valid(), h.is_correct()
        #return new_confs


#The config main part is use only for testing purpose
if __name__ == '__main__':
    c = Config()
    #c.read_cache(c.cache_path)
    
    print "****************** Read ******************"
    c.read_config("nagios.cfg")
    #c.idfy()
    #c.dump()
    
    print "****************** Explode ******************"
    #create or update new hostgroup or service by looking at
    c.explode()
    c.dump()

    print "****************** Inheritance ******************"
    #We apply all inheritance
    c.apply_inheritance()
    c.dump()
    
    
    print "****************** Fill default ******************"
    #After inheritance is ok, we can fill defaults
    #values not set by inheritance
    c.fill_default()
    c.dump()
    
    print "****************** Clean templates ******************"
    #We can clean the tpl now
    c.clean_useless()
    c.dump()
    
    
    print "****************** Pythonize ******************"
    #We pythonize every data
    c.pythonize()
    c.dump()
    
    
    print "****************** Linkify ******************"
    #Now we can make relations between elements
    #relations = id
    c.linkify()
    c.dump()
    
    
    print "*************** applying dependancies ************"
    c.apply_dependancies()


    print "************** Exlode global conf ****************"
    c.explode_global_conf()
    
    print "****************** Correct ?******************"
    #We check if the config is OK
    c.is_correct()
    dump = getattr(c, 'dump')
    #print dump
    dump()
    #c.dump()

    c.cut_into_parts()
    
    m = MacroResolver()
    m.init(c)
    h = c.hosts.items[6]
    #print h
    #print c

    s = c.services.items[3]
    #print s
    com = s.check_command
    #print com
    con = c.contacts.items[2]
    #for i in xrange(1 ,1000):
    m.resolve_command(com, h, s, con, None)
    #dump()
    print "finish!!"

    

