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


#File for create the objects.cache file
import time
import os
import tempfile

from service import Service
from host import Host
from contact import Contact

from util import from_bool_to_string,from_list_to_split


class ObjectsCacheFile:
    #prop : is the internal name if it is different than the name in the output file
    #required : 
    #depythonize : 
    #default :
    out_map = {Host : {
            'host_name' : {'required' : True},
            'alias' : {'required' : False},
            'address' : {'required' : True},
            'parents' : {'required' : False, 'depythonize' : 'get_name'},
            'check_period' : {'required' : True, 'depythonize' : 'get_name'},
            'check_command' : {'required' : True, 'depythonize' : 'call'},
            #'contact_groups' : ,
            'contacts' : {'required' : True, 'depythonize' : 'contact_name'},
            'notification_period' : {'required' : True, 'depythonize' : 'get_name'},
            'initial_state' : {'required' : True},
            'check_interval' : {'required' : True},
            'retry_interval' : {'required' : True},
            'max_check_attempts' : {'required' : True},
            'active_checks_enabled' : {'required' : False, 'depythonize' : from_bool_to_string, 'default' : '0'},
            'passive_checks_enabled' : {'required' : False, 'depythonize' : from_bool_to_string, 'default' : '0'},
            'obsess_over_host' : {'required' : False, 'depythonize' : from_bool_to_string, 'default' : '0'},
            'event_handler_enabled' : {'required' : False, 'depythonize' : from_bool_to_string, 'default' : '0'},
            'low_flap_threshold' : {'required' : False, 'default' : '0'},
            'high_flap_threshold' : {'required' : False, 'default' : '0'},
            'flap_detection_enabled' : {'required' : False, 'depythonize' : from_bool_to_string, 'default' : '0'},
            'flap_detection_options' : {'required' : True, 'depythonize' : from_list_to_split},
            'freshness_threshold' : {'required' : False, 'default' : '0'},
            'check_freshness' : {'required' : False, 'depythonize' : from_bool_to_string, 'default' : '0'},
            'notification_options' : {'required' : True, 'depythonize' : from_list_to_split},
            'notifications_enabled' : {'required' : False, 'depythonize' : from_bool_to_string, 'default' : '0'},
            'notification_interval' : {'required' : True},
            'first_notification_delay' : {'required' : False, 'default' : '0'},
            'stalking_options' : {'required' : False, 'depythonize' : from_list_to_split, 'default' : 'n'},
            'process_perf_data' : {'required' : False, 'depythonize' : from_bool_to_string, 'default' : '0'},
            'failure_prediction_enabled' : {'required' : False, 'depythonize' : from_bool_to_string, 'default' : '0'},
            'retain_status_information' : {'required' : False, 'depythonize' : from_bool_to_string, 'default' : '0'},
            'retain_nonstatus_information' : {'required' : False, 'depythonize' : from_bool_to_string, 'default' : '0'},
            },
        Service : {
            'host_name' : {'required' : True},
            'service_description' : {'required' : True},
            'check_period' : {'required' : True, 'depythonize' : 'get_name'},
            'check_command' : {'required' : True, 'depythonize' : 'call'},
            #'contact_groups' : {'required' : True, 'depythonize' : 'get_name'},
            'contacts' : {'required' : True, 'depythonize' : 'contact_name'},
            'notification_period' : {'required' : True, 'depythonize' : 'get_name'},
            'initial_state' : {'required' : True},
            'check_interval' : {'required' : True},
            'retry_interval' : {'required' : True},
            'max_check_attempts' : {'required' : True},
            'is_volatile' : {'required' : False, 'default' : '0'},
            'parallelize_check' : {'required' : False, 'depythonize' : from_bool_to_string, 'default' : '0'},
            'active_checks_enabled' : {'required' : False, 'depythonize' : from_bool_to_string, 'default' : '0'},
            'passive_checks_enabled' : {'required' : False, 'depythonize' : from_bool_to_string, 'default' : '0'},
            'obsess_over_service' : {'required' : False, 'depythonize' : from_bool_to_string, 'default' : '0'},
            'event_handler_enabled' : {'required' : False, 'depythonize' : from_bool_to_string, 'default' : '0'},
            'low_flap_threshold' : {'required' : False, 'default' : '0'},
            'high_flap_threshold' : {'required' : False, 'default' : '0'},
            'flap_detection_enabled' : {'required' : False, 'depythonize' : from_bool_to_string, 'default' : '0'},
            'flap_detection_options' : {'required' : True, 'depythonize' : from_list_to_split},
            'freshness_threshold' : {'required' : False, 'default' : '0'},
            'check_freshness' : {'required' : False, 'depythonize' : from_bool_to_string, 'default' : '0'},
            'notification_options' : {'required' : True, 'depythonize' : from_list_to_split},
            'notifications_enabled' : {'required' : False, 'depythonize' : from_bool_to_string, 'default' : '0'},
            'notification_interval' : {'required' : True},
            'first_notification_delay' : {'required' : False, 'default' : '0'},
            'stalking_options' : {'required' : False, 'depythonize' : from_list_to_split, 'default' : 'n'},
            'process_perf_data' : {'required' : False, 'depythonize' : from_bool_to_string, 'default' : '0'},
            'failure_prediction_enabled' : {'required' : False, 'depythonize' : from_bool_to_string, 'default' : '0'},
            'notes_url' : {'required' : False},
            'action_url' : {'required' : False},
            'retain_status_information' : {'required' : False, 'depythonize' : from_bool_to_string, 'default' : '0'},
            'retain_nonstatus_information' : {'required' : False, 'depythonize' : from_bool_to_string, 'default' : '0'},
            },
              
        Contact : {
            'contact_name' : {'required' : True, 'default' : '0'},
            'alias' : {'required' : False, 'default' : '0'},
            'host_notifications_enabled' : {'required' : True, 'depythonize' : from_bool_to_string},
            'service_notifications_enabled' : {'required' : True, 'depythonize' : from_bool_to_string},
            'host_notification_period' : {'required' : True, 'depythonize' : 'get_name'},
            'service_notification_period' : {'required' : True, 'depythonize' : 'get_name'},
            'host_notification_options' : {'required' : True, 'depythonize' : from_list_to_split, 'default' : 'd,u,r,f,s,n'},
            'service_notification_options' : {'required' : True, 'depythonize' : from_list_to_split, 'default' : 'w,u,c,r,f,s,n'},
            'host_notification_commands' : {'required' : True, 'depythonize' : 'call'},
            'service_notification_commands' : {'required' : True, 'depythonize' : 'call'},
            'email' : {'required' : False},
            'pager' : {'required' : False},
            'address1' : {'required' : False},
            'address2' : {'required' : False},
            'address3' : {'required' : False},
            'address4' : {'required' : False},
            'address5' : {'required' : False},
            'address6' : {'required' : False},
            'can_submit_commands' : {'required' : False, 'depythonize' : from_bool_to_string, 'default' : '0'},
            'retain_status_information' : {'required' : False, 'depythonize' : from_bool_to_string, 'default' : '0'},
            'retain_nonstatus_information' : {'required' : False, 'depythonize' : from_bool_to_string, 'default' : '0'},
            },

#               Scheduler : {
#            'modified_host_attributes' : {'prop' : None, 'default' : '0'},
#            'modified_service_attributes' : {'prop' : None, 'default' : '0'},
#            'nagios_pid' : {'prop' : None, 'default' : '0'},
#            'daemon_mode' : {'prop' : None, 'default' : '0'},
#            'program_start' : {'prop' : None, 'default' : '0'},
#            'last_command_check' : {'prop' : None, 'default' : '0'},
#            'last_log_rotation' : {'prop' : None, 'default' : '0'},
#            'enable_notifications' : {'prop' : None, 'default' : '0'},
#            'active_service_checks_enabled' : {'prop' : None, 'default' : '0'},
#            'passive_service_checks_enabled' : {'prop' : None, 'default' : '0'},
#            'active_host_checks_enabled' : {'prop' : None, 'default' : '0'},
#            'passive_host_checks_enabled' : {'prop' : None, 'default' : '0'},
#            'enable_event_handlers' : {'prop' : None, 'default' : '0'},
#            'obsess_over_services' : {'prop' : None, 'default' : '0'},
#            'obsess_over_hosts' : {'prop' : None, 'default' : '0'},
#            'check_service_freshness' : {'prop' : None, 'default' : '0'},
#            'check_host_freshness' : {'prop' : None, 'default' : '0'},
#            'enable_flap_detection' : {'prop' : None, 'default' : '0'},
#            'enable_failure_prediction' : {'prop' : None, 'default' : '0'},
#            'process_performance_data' : {'prop' : None, 'default' : '0'},
#            'global_host_event_handler' : {'prop' : None, 'default' : '0'},
#            'global_service_event_handler' : {'prop' : None, 'default' : '0'},
#            'next_comment_id' : {'prop' : None, 'default' : '0'},
#            'next_downtime_id' : {'prop' : None, 'default' : '0'},
#            'next_event_id' : {'prop' : None, 'default' : '0'},
#            'next_problem_id' : {'prop' : None, 'default' : '0'},
#            'next_notification_id'  : {'prop' : None, 'default' : '0'},
#            'total_external_command_buffer_slots' : {'prop' : None, 'default' : '0'},
#            'used_external_command_buffer_slots' : {'prop' : None, 'default' : '0'},
#            'high_external_command_buffer_slots' : {'prop' : None, 'default' : '0'},
#            'active_scheduled_host_check_stats' : {'prop' : None, 'default' : '0'},
#            'active_ondemand_host_check_stats' : {'prop' : None, 'default' : '0'},
#            'passive_host_check_stats' : {'prop' : None, 'default' : '0'},
#            'active_scheduled_service_check_stats' : {'prop' : None, 'default' : '0'},
#            'active_ondemand_service_check_stats' : {'prop' : None, 'default' : '0'},
#            'passive_service_check_stats' : {'prop' : None, 'default' : '0'},
#            'cached_host_check_stats' : {'prop' : None, 'default' : '0'},
#            'cached_service_check_stats' : {'prop' : None, 'default' : '0'},
#            'external_command_stats' : {'prop' : None, 'default' : '0'},
#            'parallel_host_check_stats' : {'prop' : None, 'default' : '0'},
#            'serial_host_check_stats' : {'prop' : None, 'default' : '0'}
#            }
    }
               
                   

    def __init__(self, path, hosts, services, contacts):
        #self.conf = scheduler.conf
        #self.scheduler = scheduler
        self.path = path
        self.hosts = hosts
        self.services = services
        self.contacts = contacts


    def create_output(self, elt):
        import sys
        output = ''
        elt_type = elt.__class__
        if elt_type in ObjectsCacheFile.out_map:
            type_map = ObjectsCacheFile.out_map[elt_type]
            for display in type_map:
                value = ''
                if 'prop' not in type_map[display]:
                    prop = display
                else:
                    prop = type_map[display]['prop']
                    
                if prop is not None and hasattr(elt, prop):
                    value = getattr(elt, prop)
                
                    #Maybe it's not a value, but a function link
                    if callable(value):
                        value = value()
                            
                    if 'depythonize' in type_map[display]:
                        f = type_map[display]['depythonize']
                        if callable(f):
                            value = f(value)
                        else:
                            if isinstance(value, list):
                                # ex. list of commands. command.call,command.call,command.call
                                value = ','.join(['%s' % getattr(item, str(f)) for item in value])
                            else:
                                print "Elt: ", elt, "prop", prop, "type", type(elt)
                                print "val:", value, "type", type(value)
                                #ok not a direct function, maybe a functin provided by value...
                                f = getattr(value, f)
                                if callable(f):
                                    value = f()
                                else:
                                    value = f

                    if len(str(value)) == 0:
                        value = ''
                elif 'required' in type_map[display] and type_map[display]['required'] == True:
                    try:
                        value = type_map[display]['default']
                    except KeyError:  #Fuck!
                        value = ''
                if value == 'none':
                    value = ''
                if len(str(value)) > 0:
                    output += '\t' + display + '\t' + str(value) + '\n'
                        
        return output


    def create_or_update(self):
        
        output = ''
        now = time.time()
        output += '''########################################
#       NAGIOS OBJECT CACHE FILE
#
# THIS FILE IS AUTOMATICALLY GENERATED
# BY NAGIOS.  DO NOT MODIFY THIS FILE!
#
'''
        output += '# Created: %s\n' % time.ctime()
        output += '########################################\n\n'
        #print "Create output :", output
        
        for h in self.hosts.values():
            tmp = self.create_output(h)
            output += 'define host {\n' + tmp + '\t}\n\n'

        for s in self.services.values():
            print "cache service", s
            tmp = self.create_output(s)
            output += 'define service {\n' + tmp + '\t}\n\n'

        for c in self.contacts.values():
            print "cache contact", c
            tmp = self.create_output(c)
            output += 'define contact {\n' + tmp + '\t}\n\n'


        #print "Create output :", output
        
        try :
            temp_fh, temp_objects_cache_file = tempfile.mkstemp(dir=os.path.dirname(self.path))
            os.write(temp_fh, output)
            os.close(temp_fh)
            os.chmod(temp_objects_cache_file, 0640)
            os.rename(temp_objects_cache_file, self.path)
        except OSError as exp:
            return exp
