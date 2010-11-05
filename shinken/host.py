#!/usr/bin/env python
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
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

import time

from autoslots import AutoSlots
from item import Items
from schedulingitem import SchedulingItem
from util import to_int, to_char, to_split, to_bool, format_t_into_dhms_format, to_hostnames_list, get_obj_name, to_svc_hst_distinct_lists
#from macroresolver import MacroResolver
#from check import Check
#from notification import Notification
from graph import Graph
from macroresolver import MacroResolver
from eventhandler import EventHandler
from log import Log

class Host(SchedulingItem):
    #AutoSlots create the __slots__ with properties and
    #running_properties names
    __metaclass__ = AutoSlots

    id = 1 #0 is reserved for host (primary node for parents)
    ok_up = 'UP'
    my_type = 'host'


    #properties defined by configuration
    #*required : is required in conf
    #*default : default value if no set in conf
    #*pythonize : function to call when transfort string to python object
    #*fill_brok : if set, send to broker. there are two categories: full_status for initial and update status, check_result for check results
    #*no_slots : do not take this property for __slots__
    # Only for the inital call
    #conf_send_preparation : if set, will pass the property to this function. It's used to "flatten"
    # some dangerous properties like realms that are too 'linked' to be send like that.
    #brok_transformation : if set, will call the function with the value of the property
    # the major times it will be to flatten the data (like realm_name instead of the realm object).
    properties={
        'host_name' : {'required' : True, 'fill_brok' : ['full_status', 'check_result', 'next_schedule']},
        'alias' : {'required' : True, 'fill_brok' : ['full_status']},
        'display_name' : {'required' : False, 'default' : 'none', 'fill_brok' : ['full_status']},
        'address' : {'required' : True, 'fill_brok' : ['full_status']},
        'parents' : {'required' : False, 'default' : '', 'pythonize' : to_split, 'fill_brok' : ['full_status'], 'brok_transformation' : to_hostnames_list},
        'hostgroups' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'check_command' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'initial_state' : {'required' : False, 'default' : 'u', 'pythonize' : to_char, 'fill_brok' : ['full_status']},
        'max_check_attempts' : {'required' : True, 'pythonize' : to_int, 'fill_brok' : ['full_status']},
        'check_interval' : {'required' : False, 'default' : '0', 'pythonize' : to_int, 'fill_brok' : ['full_status']},
        'retry_interval' : {'required' : False, 'default' : '0', 'pythonize' : to_int, 'fill_brok' : ['full_status']},
        'active_checks_enabled' : {'required' : False, 'default' : '1', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'passive_checks_enabled' : {'required' : False, 'default' : '1', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'check_period' : {'required' : True, 'fill_brok' : ['full_status']},
        'obsess_over_host' : {'required' : False, 'default' : '0', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'check_freshness' : {'required' : False, 'default' : '0', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'freshness_threshold' : {'required' : False, 'default' : '0', 'pythonize' : to_int, 'fill_brok' : ['full_status']},
        'event_handler' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'event_handler_enabled' : {'required' : False, 'default' : '0', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'low_flap_threshold' : {'required' : False, 'default' : '25', 'pythonize' : to_int, 'fill_brok' : ['full_status']},
        'high_flap_threshold' : {'required' : False, 'default' : '50', 'pythonize' : to_int, 'fill_brok' : ['full_status']},
        'flap_detection_enabled' : {'required' : False, 'default' : '1', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'flap_detection_options' : {'required' : False, 'default' : 'o,d,u', 'pythonize' : to_split, 'fill_brok' : ['full_status']},
        'process_perf_data' : {'required' : False, 'default' : '1', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'retain_status_information' : {'required' : False, 'default' : '1', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'retain_nonstatus_information' : {'required' : False, 'default' : '1', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'contacts' : {'required' : True, 'default' : '', 'fill_brok' : ['full_status']},
        'contact_groups' : {'required' : True, 'default' : '', 'fill_brok' : ['full_status']},
        'notification_interval' : {'required' : False, 'default' : '60', 'pythonize' : to_int, 'fill_brok' : ['full_status']},
        'first_notification_delay' : {'required' : False, 'default' : '0', 'pythonize' : to_int, 'fill_brok' : ['full_status']},
        'notification_period' : {'required' : True, 'fill_brok' : ['full_status']},
        'notification_options' : {'required' : False, 'default' : 'd,u,r,f', 'pythonize' : to_split, 'fill_brok' : ['full_status']},
        'notifications_enabled' : {'required' : False, 'default' : '1', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'stalking_options' : {'required' : False, 'default' : '', 'pythonize' : to_split, 'fill_brok' : ['full_status']},
        'notes' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'notes_url' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'action_url' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'icon_image' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'icon_image_alt' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'vrml_image' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'statusmap_image' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        #No slots for this 2 because begin property by a number seems bad (stupid!)
        '2d_coords' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status'], 'no_slots' : True},
        '3d_coords' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status'], 'no_slots' : True},
        'failure_prediction_enabled' : {'required' : False, 'default' : '0', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},

        #New to shinken
        'realm' : {'required' : False, 'default' : None, 'conf_send_preparation' : get_obj_name, 'fill_brok' : ['full_status']}, #'fill_brok' is ok because in scheduler it's already a string from conf_send_preparation
        'poller_tag' : {'required' : False, 'default' : None},

        #Shinken specific
        'resultmodulations' : {'required' : False, 'default' : ''},
        'escalations' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'maintenance_period' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},

        #Importance value
        'importance' : {'required' : False, 'default' : '3', 'pythonize' : to_int, 'fill_brok' : ['full_status']},
        }


    #properties set only for running purpose
    #retention : save/load this property from retention
    running_properties = {
        'last_chk' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'next_chk' : {'default' : 0, 'fill_brok' : ['full_status', 'next_schedule']},
        'in_checking' : {'default' : False, 'fill_brok' : ['full_status']},
        'latency' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'attempt' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'state' : {'default' : 'PENDING', 'fill_brok' : ['full_status'], 'retention' : True},
        'state_id' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'state_type' : {'default' : 'HARD', 'fill_brok' : ['full_status'], 'retention' : True},
        'state_type_id' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'current_event_id' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'last_event_id' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'last_state' : {'default' : 'PENDING', 'fill_brok' : ['full_status'], 'retention' : True},
        'last_state_id' : {'default' : 0, 'fill_brok' : ['full_status'], 'retention' : True},
        'last_state_change' : {'default' : time.time(), 'fill_brok' : ['full_status'], 'retention' : True},
        'last_hard_state_change' : {'default' : time.time(), 'fill_brok' : ['full_status'], 'retention' : True},
        'last_hard_state' : {'default' : time.time(), 'fill_brok' : ['full_status'], 'retention' : True},
        'last_time_up' : {'default' : int(time.time()), 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'last_time_down' : {'default' : int(time.time()), 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'last_time_unreachable' : {'default' : int(time.time()), 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'duration_sec' : {'default' : 0, 'fill_brok' : ['full_status'], 'retention' : True},
        'output' : {'default' : '', 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'long_output' : {'default' : '', 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'is_flapping' : {'default' : False, 'fill_brok' : ['full_status'], 'retention' : True},
        'flapping_comment_id' : {'default' : 0, 'fill_brok' : ['full_status'], 'retention' : True},
        #No broks for _depend_of because of to much links to hsots/services
        'act_depend_of' : {'default' : []}, #dependencies for actions like notif of event handler, so AFTER check return
        'chk_depend_of' : {'default' : []}, #dependencies for checks raise, so BEFORE checks

        'act_depend_of_me' : {'default' : [] }, #elements that depend of me, so the reverse than just uppper
        'chk_depend_of_me' : {'default' : []}, #elements that depend of me

        'last_state_update' : {'default' : time.time(), 'fill_brok' : ['full_status'], 'retention' : True},
        'services' : {'default' : []}, #no brok ,to much links
        'checks_in_progress' : {'default' : []},#No broks, it's just internal, and checks have too links
        'notifications_in_progress' : {'default' : {}, 'retention' : True},#No broks, it's just internal, and checks have too links
        'downtimes' : {'default' : [], 'fill_brok' : ['full_status']},
        'comments' : {'default' : [], 'fill_brok' : ['full_status'], 'retention' : True},
        'flapping_changes' : {'default' : [], 'fill_brok' : ['full_status'], 'retention' : True},
        'percent_state_change' : {'default' : 0.0, 'fill_brok' : ['full_status'], 'retention' : True},
        'problem_has_been_acknowledged' : {'default' : False, 'fill_brok' : ['full_status'], 'retention' : True},
        'acknowledgement' : {'default' : None, 'retention' : True},
        'acknowledgement_type' : {'default' : 1, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'check_type' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'has_been_checked' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'should_be_scheduled' : {'default' : 1, 'fill_brok' : ['full_status'], 'retention' : True},
        'last_problem_id' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'current_problem_id' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'execution_time' : {'default' : 0.0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'last_notification' : {'default' : time.time(), 'fill_brok' : ['full_status'], 'retention' : True},
        'current_notification_number' : {'default' : 0, 'fill_brok' : ['full_status'], 'retention' : True},
        'current_notification_id' : {'default' : 0, 'fill_brok' : ['full_status'], 'retention' : True},
        'check_flapping_recovery_notification' : {'default' : True, 'fill_brok' : ['full_status'], 'retention' : True},
        'scheduled_downtime_depth' : {'default' : 0, 'fill_brok' : ['full_status'], 'retention' : True},
        'pending_flex_downtime' : {'default' : 0, 'fill_brok' : ['full_status'], 'retention' : True},
        'timeout' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'start_time' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'end_time' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'early_timeout' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'return_code' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'perf_data' : {'default' : '', 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'last_perf_data' : {'default' : '', 'retention' : True},
        'customs' : {'default' : {}},
        'notified_contacts' : {'default' : set()}, #use for having all contacts we have notified
        'in_scheduled_downtime' : {'default' : False, 'retention' : True},
        'in_scheduled_downtime_during_last_check' : {'default' : False, 'retention' : True},
        'actions' : {'default' : []}, #put here checks and notif raised
        'broks' : {'default' : []}, #and here broks raised

        #All errors and warning raised during the configuration parsing
        #and taht will raised real warning/errors during the is_correct
        'configuration_warnings' : {'default' : []},
        'configuration_errors' : {'default' : []},

        #Issue/impact part
        'is_problem' : {'default' : False, 'fill_brok' : ['full_status']},
        'is_impact' : {'default' : False, 'fill_brok' : ['full_status']},
        'source_problems' : {'default' : [], 'fill_brok' : ['full_status'], 'brok_transformation' : to_svc_hst_distinct_lists}, # list of problems that make us an impact
        'impacts' : {'default' : [], 'fill_brok' : ['full_status'], 'brok_transformation' : to_svc_hst_distinct_lists}, #list of the impact I'm the cause of
        'state_before_impact' : {'default' : 'PENDING'}, #keep a trace of the old state before being an impact
        'state_id_before_impact' : {'default' : 0}, #keep a trace of the old state id before being an impact
        'state_changed_since_impact' : {'default' : False}, #if teh state change, we know so we do not revert it
        }

    #Hosts macros and prop that give the information
    #the prop can be callable or not
    macros = {'HOSTNAME' : 'host_name',
              'HOSTDISPLAYNAME' : 'display_name',
              'HOSTALIAS' :  'alias',
              'HOSTADDRESS' : 'address',
              'HOSTSTATE' : 'state',
              'HOSTSTATEID' : 'state_id',
              'LASTHOSTSTATE' : 'last_state',
              'LASTHOSTSTATEID' : 'last_state_id',
              'HOSTSTATETYPE' : 'state_type',
              'HOSTATTEMPT' : 'attempt',
              'MAXHOSTATTEMPTS' : 'max_check_attempts',
              'HOSTEVENTID' : 'current_event_id',
              'LASTHOSTEVENTID' : 'last_event_id',
              'HOSTPROBLEMID' : 'current_problem_id',
              'LASTHOSTPROBLEMID' : 'last_problem_id',
              'HOSTLATENCY' : 'latency',
              'HOSTEXECUTIONTIME' : 'execution_time',
              'HOSTDURATION' : 'get_duration',
              'HOSTDURATIONSEC' : 'get_duration_sec',
              'HOSTDOWNTIME' : 'get_downtime',
              'HOSTPERCENTCHANGE' : 'percent_state_change',
              'HOSTGROUPNAME' : 'get_groupname',
              'HOSTGROUPNAMES' : 'get_groupnames',
              'LASTHOSTCHECK' : 'last_chk',
              'LASTHOSTSTATECHANGE' : 'last_state_change',
              'LASTHOSTUP' : 'last_time_up',
              'LASTHOSTDOWN' : 'last_time_down',
              'LASTHOSTUNREACHABLE' : 'last_time_unreachable',
              'HOSTOUTPUT' : 'output',
              'LONGHOSTOUTPUT' : 'long_output',
              'HOSTPERFDATA' : 'perf_data',
              'LASTHOSTPERFDATA' : 'last_perf_data',
              'HOSTCHECKCOMMAND' : 'get_check_command',
              'HOSTACKAUTHOR' : 'get_ack_author_name',
              'HOSTACKAUTHORNAME' : 'get_ack_author_name',
              'HOSTACKAUTHORALIAS' : 'get_ack_author_name',
              'HOSTACKCOMMENT' : 'get_ack_comment',
              'HOSTACTIONURL' : 'action_url',
              'HOSTNOTESURL' : 'notes_url',
              'HOSTNOTES' : 'notes',
              'TOTALHOSTSERVICES' : 'get_total_services',
              'TOTALHOSTSERVICESOK' : 'get_total_services_ok',
              'TOTALHOSTSERVICESWARNING' : 'get_total_services_warning',
              'TOTALHOSTSERVICESUNKNOWN' : 'get_total_services_unknown',
              'TOTALHOSTSERVICESCRITICAL' : 'get_total_services_critical'
        }


    #This tab is used to transform old parameters name into new ones
    #so from Nagios2 format, to Nagios3 ones
    old_properties = {
        'normal_check_interval' : 'check_interval',
        'retry_check_interval' : 'retry_interval'
        }


    def clean(self):
        pass


    #Call by picle for dataify service
    #Here we do not want a dict, it's too heavy
    #We create a list with properties inlined
    #The setstate function do the inverse
    def __getstate__(self):
        cls = self.__class__
        #id is not in *_properties
        res = [self.id]
        for prop in cls.properties:
            res.append(getattr(self, prop))
        for prop in cls.running_properties:
            res.append(getattr(self, prop))
        #We reverse because we want to recreate
        #By check at properties in the same order
        res.reverse()
        return res


    #Inversed funtion of getstate
    def __setstate__(self, state):
        cls = self.__class__
        self.id = state.pop()
        for prop in cls.properties:
            setattr(self, prop, state.pop())
        for prop in cls.running_properties:
            setattr(self, prop, state.pop())



    #Fill adresse with host_name if not already set
    def fill_predictive_missing_parameters(self):
        if hasattr(self, 'host_name') and not hasattr(self, 'address'):
            self.address = self.host_name


    #Check is required prop are set:
    #contacts OR contactgroups is need
    def is_correct(self):
        state = True #guilty or not? :)
        cls = self.__class__

        special_properties = ['contacts', 'contact_groups', 'check_period', \
                                  'notification_interval', 'check_period']
        for prop in cls.properties:
            if prop not in special_properties:
                if not hasattr(self, prop) and cls.properties[prop]['required']:
                    Log().log("%s : I do not have %s" % (self.get_name(), prop))
                    state = False #Bad boy...

        #Raised all previously saw errors like unknown contacts and co
        if self.configuration_errors != []:
            state = False
            for err in self.configuration_errors:
                Log().log(err)

        #Ok now we manage special cases...
        if not hasattr(self, 'contacts') and not hasattr(self, 'contacgroups') and self.notifications_enabled == True:
            Log().log("%s : I do not have contacts nor contacgroups" % self.get_name())
            state = False
        if not hasattr(self, 'check_command') or self.check_command == None:
            Log().log("%s : I've got no check_command" % self.get_name())
            state = False
        #Ok got a command, but maybe it's invalid
        else:
            if not self.check_command.is_valid():
                Log().log("%s : my check_command %s is invalid" % (self.get_name(), self.check_command.command))
                state = False
        if not hasattr(self, 'notification_interval') and self.notifications_enabled == True:
            Log().log("%s : I've got no notification_interval but I've got notifications enabled" % self.get_name())
            state = False
        #If active check is enabled with a check_interval!=0, we must have a check_period
        if (hasattr(self, 'active_checks_enabled') and self.active_checks_enabled) and (not hasattr(self, 'check_period') or self.check_period == None) and (hasattr(self, 'check_interval') and self.check_interval!=0):
            Log().log("%s : My check_period is not correct" % self.get_name())
            state = False
        if not hasattr(self, 'realm') or self.realm == None:
            Log().log("%s : My realm is not correct" % self.get_name())
            state = False
        if not hasattr(self, 'check_period'):
            self.check_period = None
        if hasattr(self, 'host_name'):
            for c in cls.illegal_object_name_chars:
                if c in self.host_name:
                    Log().log("%s : My host_name got the caracter %s that is not allowed." % (self.get_name(), c))
                    state = False
        return state


    #Search in my service if I've got the service
    def find_service_by_name(self, service_description):
        for s in self.services:
            if s.service_description == service_description:
                return s
        return None


    #For service generator, get dict from a _custom properties
    #as _disks   C$(80%!90%),D$(80%!90%)$,E$(80%!90%)$
    #return {'C' : '80%!90%', 'D' : '80%!90%', 'E' : '80%!90%'}
    def get_key_value_from_property(self, property):
        print "My customs"
        print self.customs

        property = property.strip()
        

        #In macro, it's all in UPPER case
        prop = property.upper()

        #If I do not have the property, we bail out
        if not prop in self.customs:
            return None

        entry = self.customs[prop]

        print "Property", entry

        #Look if we end with a "value" so a $
        #because we will have problem if we don't end
        #like it
        end_with_value = (entry[-1] == '$')
        print "End with value?", end_with_value

        conf_entry = entry
        #Here we need a special string to replace after
        long_and_random = "Z"*10
        print "My entry", entry
        #Now entry is a dict from outside, and inner key start with a '
        entry = "{'%s'}" % entry
        print "Entry 1", entry
        #first we make key look like C': 'blabla...
        entry = entry.replace('$(', "': '")
        print "Entry 2", entry
        #And the end of value with a '
        entry = entry.replace(')$', "'"+long_and_random)
        print "Entry 3", entry
        #Now we clean the ZZZ,D into a ,'D
        entry = entry.replace(long_and_random+",", ",'")
        print "Entry 4", entry
        #And clean the trailing ZZZ' because it's not useful, there is no key after
        entry = entry.replace(long_and_random+"'", '')
        print "Entry 5", entry
        #Now need to see the entry taht are alone, with no value
        #the last one will be a 'G'} with no value if not set, and
        #will raise an error
        if len(entry) >= 2 and not end_with_value:
            entry = entry[:-2]
            #And so add a None as value
            entry = entry + "': None}"
            print "Entry 6", entry

        
        try:
            r = eval(entry)
        except SyntaxError:
            err = "The custom property '%s 'of the host '%s' is not a valid entry %s for a service generator" % (property, self.get_name(), conf_entry)
            self.configuration_errors.append(err)
            return None
 
        #special case : key with a , are in fact KEY1, KEY2, ... KEYN and KEY1,2 got not real value
        #only N got one
        keys_to_del = []
        keys_to_add = {}
        for key in r:
            if ',' in key:
                keys_to_del.append(key)
                value = r[key]
                elts = key.split(',')
                nb_elts = len(elts)
                non_value_keys = elts[:-1]
                for k in non_value_keys:
                    keys_to_add[k] = None
                keys_to_add[elts[-1]] = value

        for k in keys_to_del:
            del r[k]

        for k in keys_to_add:
            r.update(keys_to_add)

        print "Final R", r
       
        return r
                
#        return {'C' : '80%!90%', 'D' : '80%!90%', 'E' : '80%!90%'}


    #Macro part
    def get_total_services(self):
        return str(len(self.services))


    def get_total_services_ok(self):
        return str(len([s for s in self.services if s.state_id == 0]))


    def get_total_services_warning(self):
        return str(len([s for s in self.services if s.state_id == 1]))


    def get_total_services_critical(self):
        return str(len([s for s in self.services if s.state_id == 2]))


    def get_total_services_unknown(self):
        return str(len([s for s in self.services if s.state_id == 3]))


    def get_ack_author_name(self):
        if self.acknowledgement == None:
            return ''
        return self.acknowledgement.author


    def get_ack_comment(self):
        if self.acknowledgement == None:
            return ''
        return self.acknowledgement.comment


    def get_check_command(self):
        return self.check_command.get_name()


    #For get a nice name
    def get_name(self):
        return self.host_name


    #For debugin purpose only
    def get_dbg_name(self):
        return self.host_name


    #Add a dependancy for action event handler, notification, etc)
    #and add ourself in it's dep list
    def add_host_act_dependancy(self, h, status, timeperiod, inherits_parent):
        #I add him in MY list
        self.act_depend_of.append( (h, status, 'logic_dep', timeperiod, inherits_parent) )
        #And I add me in it's list
        h.act_depend_of_me.append( (self, status, 'logic_dep', timeperiod, inherits_parent) )


    #Add a dependancy for check (so before launch)
    def add_host_chk_dependancy(self, h, status, timeperiod, inherits_parent):
        #I add him in MY list
        self.chk_depend_of.append( (h, status, 'logic_dep', timeperiod, inherits_parent) )
        #And I add me in it's list
        h.chk_depend_of_me.append( (self, status, 'logic_dep', timeperiod, inherits_parent) )


    #add one of our service to services (at linkify)
    def add_service_link(self, service):
        self.services.append(service)


    #Set unreachable : all our parents are down!
    #We have a special state, but state was already set, we just need to
    #update it. We are no DOWN, we are UNREACHABLE and
    #got a state id is 2
    def set_unreachable(self):
        now = time.time()
        self.state_id = 2
        self.state = 'UNREACHABLE'
        self.last_time_unreachable = int(now)


    #We just go an impact, so we go unreachable
    #But only if we enable this stte change in the conf
    def set_impact_state(self):
        cls = self.__class__
        if cls.enable_problem_impacts_states_change:
            #Keep a trace of the old state (problem came back before
            #a new checks)
            self.state_before_impact = self.state
            self.state_id_before_impact = self.state_id
            #this flag will know if we overide the impact state
            self.state_changed_since_impact = False
            self.state = 'UNREACHABLE'#exit code UNDETERMINED
            self.state_id = 2


    #Ok, we are no more an impact, if no news checks
    #overide the impact state, we came back to old
    #states
    #And only if impact state change is set in configuration
    def unset_impact_state(self):
        cls = self.__class__
        if cls.enable_problem_impacts_states_change and not self.state_changed_since_impact:
            self.state = self.state_before_impact
            self.state_id = self.state_id_before_impact
            #print "Reverting ME %s states to %s %s" % (self.get_dbg_name(), self.state, self.state_id)


    #set the state in UP, DOWN, or UNDETERMINED
    #with the status of a check. Also update last_state
    def set_state_from_exit_status(self, status):
        now = time.time()
        self.last_state_update = now

        #we should put in last_state the good last state:
        #if not just change the state by an problem/impact
        #we can take current state. But if it's the case, the
        #real old state is self.state_before_impact (it's teh TRUE
        #state in fact)
        #And only if we enable the impact state change
        cls = self.__class__
        if cls.enable_problem_impacts_states_change and self.is_impact and not self.state_changed_since_impact:
            #print "Me %s take standard state %s" % (self.get_dbg_name(), self.state)
            self.last_state = self.state_before_impact
        else:
            #print "Me %s take impact state %s and not %s" % (self.get_dbg_name(), self.state_before_impact, self.state)
            self.last_state = self.state

        if status == 0:
            self.state = 'UP'
            self.state_id = 0
            self.last_time_up = int(self.last_state_update)
            state_code = 'u'
        elif status == 1 or status == 2 or status == 3:
            self.state = 'DOWN'
            self.state_id = 1
            self.last_time_down = int(self.last_state_update)
            state_code = 'd'
        else:
            self.state = 'DOWN'#exit code UNDETERMINED
            self.state_id = 1
            self.last_time_down = int(self.last_state_update)
            state_code = 'd'
        if state_code in self.flap_detection_options:
            self.add_flapping_change(self.state != self.last_state)
        if self.state != self.last_state:
            self.last_state_change = self.last_state_update
        self.duration_sec = now - self.last_state_change


    #See if status is status. Can be low of high format (o/UP, d/DOWN, ...)
    def is_state(self, status):
        if status == self.state:
            return True
        #Now low status
        elif status == 'o' and self.state == 'UP':
            return True
        elif status == 'd' and self.state == 'DOWN':
            return True
        elif status == 'u' and self.state == 'UNREACHABLE':
            return True
        return False


    #The last time when the state was not UP
    def last_time_non_ok_or_up(self):
        if self.last_time_down > self.last_time_up:
            last_time_non_up = self.last_time_down
        else:
            last_time_non_up = 0
        return last_time_non_up


    #Add a log entry with a HOST ALERT like:
    #HOST ALERT: server;DOWN;HARD;1;I don't know what to say...
    def raise_alert_log_entry(self):
        Log().log('HOST ALERT: %s;%s;%s;%d;%s' % (self.get_name(), self.state, self.state_type, self.attempt, self.output))


    #Add a log entry with a Freshness alert like:
    #Warning: The results of host 'Server' are stale by 0d 0h 0m 58s (threshold=0d 1h 0m 0s).
    #I'm forcing an immediate check of the host.
    def raise_freshness_log_entry(self, t_stale_by, t_threshold):
        Log().log("Warning: The results of host '%s' are stale by %s (threshold=%s).  I'm forcing an immediate check of the host." \
                      % (self.get_name(), format_t_into_dhms_format(t_stale_by), format_t_into_dhms_format(t_threshold)))


    #Raise a log entry with a Notification alert like
    #HOST NOTIFICATION: superadmin;server;UP;notify-by-rss;no output
    def raise_notification_log_entry(self, n):
        contact = n.contact
        command = n.command_call
        if n.type in ('DOWNTIMESTART', 'DOWNTIMEEND', 'CUSTOM', 'ACKNOWLEDGEMENT', 'FLAPPINGSTART', 'FLAPPINGSTOP', 'FLAPPINGDISABLED'):
            state = '%s (%s)' % (n.type, self.state)
        else:
            state = self.state
        if self.__class__.log_notifications:
            Log().log("HOST NOTIFICATION: %s;%s;%s;%s;%s" % (contact.get_name(), self.get_name(), state, \
                                                                 command.get_name(), self.output))

    #Raise a log entry with a Eventhandler alert like
    #HOST NOTIFICATION: superadmin;server;UP;notify-by-rss;no output
    def raise_event_handler_log_entry(self, command):
        if self.__class__.log_event_handlers:
            Log().log("HOST EVENT HANDLER: %s;%s;%s;%s;%s" % (self.get_name(), self.state, self.state_type, self.attempt, \
                                                                 command.get_name()))


    #Raise a log entry with FLAPPING START alert like
    #HOST FLAPPING ALERT: server;STARTED; Host appears to have started flapping (50.6% change >= 50.0% threshold)
    def raise_flapping_start_log_entry(self, change_ratio, threshold):
        Log().log("HOST FLAPPING ALERT: %s;STARTED; Host appears to have started flapping (%.1f% change >= %.1% threshold)" % \
                      (self.get_name(), change_ratio, threshold))


    #Raise a log entry with FLAPPING STOP alert like
    #HOST FLAPPING ALERT: server;STOPPED; host appears to have stopped flapping (23.0% change < 25.0% threshold)
    def raise_flapping_stop_log_entry(self, change_ratio, threshold):
        Log().log("HOST FLAPPING ALERT: %s;STOPPED; Host appears to have stopped flapping (%.1f% change < %.1% threshold)" % \
                      (self.get_name(), change_ratio, threshold))


    #If there is no valid time for next check, raise a log entry
    def raise_no_next_check_log_entry(self):
        Log().log("Warning : I cannot schedule the check for the host '%s' because there is not future valid time" % \
                      (self.get_name()))

    #Raise a log entry when a downtime begins
    #HOST DOWNTIME ALERT: test_host_0;STARTED; Host has entered a period of scheduled downtime
    def raise_enter_downtime_log_entry(self):
        Log().log("HOST DOWNTIME ALERT: %s;STARTED; Host has entered a period of scheduled downtime" % \
                      (self.get_name()))


    #Raise a log entry when a downtime has finished
    #HOST DOWNTIME ALERT: test_host_0;STOPPED; Host has exited from a period of scheduled downtime
    def raise_exit_downtime_log_entry(self):
        Log().log("HOST DOWNTIME ALERT: %s;STOPPED; Host has exited from a period of scheduled downtime" % \
                      (self.get_name()))


    #Raise a log entry when a downtime prematurely ends
    #HOST DOWNTIME ALERT: test_host_0;CANCELLED; Service has entered a period of scheduled downtime
    def raise_cancel_downtime_log_entry(self):
        Log().log("HOST DOWNTIME ALERT: %s;CANCELLED; Scheduled downtime for host has been cancelled." % \
                      (self.get_name()))


    #Is stalking ?
    #Launch if check is waitconsume==first time
    #and if c.status is in self.stalking_options
    def manage_stalking(self, c):
        need_stalk = False
        if c.status == 'waitconsume':
            if c.exit_status == 0 and 'o' in self.stalking_options:
                need_stalk = True
            elif c.exit_status == 1 and 'd' in self.stalking_options:
                need_stalk = True
            elif c.exit_status == 2 and 'd' in self.stalking_options:
                need_stalk = True
            elif c.exit_status == 3 and 'u' in self.stalking_options:
                need_stalk = True
            if c.output != self.output:
                need_stalk = False
        if need_stalk:
            Log().log("Stalking %s : %s", self.get_name(), self.output)


    #fill act_depend_of with my parents (so network dep)
    #and say parents they impact me, no timeperiod and folow parents of course
    def fill_parents_dependancie(self):
        for parent in self.parents:
            if parent is not None:
                #I add my parent in my list
                self.act_depend_of.append( (parent, ['d', 'u', 's', 'f'], 'network_dep', None, True) )
                #And I register myself in my parent list too
                parent.act_depend_of_me.append( (self, ['d', 'u', 's', 'f'], 'network_dep', None, True) )


    #Give data for checks's macros
    def get_data_for_checks(self):
        return [self]

    #Give data for event handler's macro
    def get_data_for_event_handler(self):
        return [self]

    #Give data for notifications'n macros
    def get_data_for_notifications(self, contact, n):
        return [self, contact, n]


    #See if the notification is launchable (time is OK and contact is OK too)
    def notification_is_blocked_by_contact(self, n, contact):
        return not contact.want_host_notification(self.last_chk, self.state, n.type)


    #MACRO PART
    def get_duration_sec(self):
        return str(int(self.duration_sec))


    def get_duration(self):
        m, s = divmod(self.duration_sec, 60)
        h, m = divmod(m, 60)
        return "%02dh %02dm %02ds" % (h, m, s)


    #Check if a notification for this host is suppressed at this time
    #This is a check at the host level. Do not look at contacts here
    def notification_is_blocked_by_item(self, type, t_wished = None):
        if t_wished == None:
            t_wished = time.time()

        # TODO
        # forced notification -> false
        # custom notification -> false

        # Block if notifications are program-wide disabled
        if not self.enable_notifications:
            return True

        # Does the notification period allow sending out this notification?
        if not self.notification_period.is_time_valid(t_wished):
            return True

        # Block if notifications are disabled for this host
        if not self.notifications_enabled:
            return True

        # Block if the current status is in the notification_options d,u,r,f,s
        if 'n' in self.notification_options:
            return True

        if type == 'PROBLEM' or type == 'RECOVERY':
            if self.state == 'DOWN' and not 'd' in self.notification_options:
                return True
            if self.state == 'UP' and not 'r' in self.notification_options:
                return True
            if self.state == 'UNREACHABLE' and not 'u' in self.notification_options:
                return True
        if (type == 'FLAPPINGSTART' or type == 'FLAPPINGSTOP' or type == 'FLAPPINGDISABLED') and not 'f' in self.notification_options:
            return True
        if (type == 'DOWNTIMESTART' or type == 'DOWNTIMEEND' or type == 'DOWNTIMECANCELLED') and not 's' in self.notification_options:
            return True

        # Acknowledgements make no sense when the status is ok/up
        if type == 'ACKNOWLEDGEMENT':
            if self.state == self.ok_up:
                return True

        # Flapping
        if type == 'FLAPPINGSTART' or type == 'FLAPPINGSTOP' or type == 'FLAPPINGDISABLED':
        # todo    block if not notify_on_flapping
            if self.scheduled_downtime_depth > 0:
                return True

        # When in deep downtime, only allow end-of-downtime notifications
        # In depth 1 the downtime just started and can be notified
        if self.scheduled_downtime_depth > 1 and (type != 'DOWNTIMEEND' or type != 'DOWNTIMECANCELLED'):
            return True

        # Block if in a scheduled downtime and a problem arises
        if self.scheduled_downtime_depth > 0 and (type == 'PROBLEM' or type == 'RECOVERY'):
            return True

        # Block if the status is SOFT
        if self.state_type == 'SOFT' and type == 'PROBLEM':
            return True

        # Block if the problem has already been acknowledged
        if self.problem_has_been_acknowledged and type != 'ACKNOWLEDGEMENT':
            return True

        # Block if flapping
        if self.is_flapping:
            return True

        return False


    #Get a oc*p command if item has obsess_over_*
    #command. It must be enabled locally and globally
    def get_obsessive_compulsive_processor_command(self):
        cls = self.__class__
        if not cls.obsess_over or not self.obsess_over_host:
            return

        m = MacroResolver()
        data = self.get_data_for_event_handler()
        cmd = m.resolve_command(cls.ochp_command, data)
        e = EventHandler(cmd, timeout=cls.ochp_timeout)

        #ok we can put it in our temp action queue
        self.actions.append(e)




class Hosts(Items):
    name_property = "host_name" #use for the search by name
    inner_class = Host #use for know what is in items


    #prepare_for_conf_sending to flatten some properties
    def prepare_for_sending(self):
        for h in self:
            h.prepare_for_conf_sending()


    #Create link between elements:
    #hosts -> timeperiods
    #hosts -> hosts (parents, etc)
    #hosts -> commands (check_command)
    #hosts -> contacts
    def linkify(self, timeperiods=None, commands=None, contacts=None, realms=None, resultmodulations=None, escalations=None):
        self.linkify_with_timeperiods(timeperiods, 'notification_period')
        self.linkify_with_timeperiods(timeperiods, 'check_period')
        self.linkify_with_timeperiods(timeperiods, 'maintenance_period')
        self.linkify_h_by_h()
        self.linkify_one_command_with_commands(commands, 'check_command')
        self.linkify_one_command_with_commands(commands, 'event_handler')

        self.linkify_with_contacts(contacts)
        self.linkify_h_by_realms(realms)
        self.linkify_with_resultmodulations(resultmodulations)
        #WARNING: all escalations will not be link here
        #(just the escalation here, not serviceesca or hostesca).
        #This last one will be link in escalations linkify.
        self.linkify_with_escalations(escalations)


    #Fill adress by host_name if not set
    def fill_predictive_missing_parameters(self):
        for h in self:
            h.fill_predictive_missing_parameters()


    #Link host with hosts (parents)
    def linkify_h_by_h(self):
        for h in self:
            parents = h.parents
            #The new member list
            new_parents = []
            for parent in parents:
                new_parents.append(self.find_by_name(parent))
            #print "Me,", h.host_name, "define my parents", new_parents
            #We find the id, we remplace the names
            h.parents = new_parents


    #Link with realms and set a default realm if none
    def linkify_h_by_realms(self, realms):
        default_realm = None
        for r in realms:
            if hasattr(r, 'default') and r.default:
                default_realm = r
        if default_realm == None:
            print "Error : there is no default realm defined!"
        for h in self:
            #print h.get_name(), h.realm
            if h.realm != None:
                p = realms.find_by_name(h.realm.strip())
                if p != None:
                    h.realm = p
                    print "Host", h.get_name(), "is in the realm", p.get_name()
                else:
                    print "Warning : the host %s git a invalid realm (%s)!" % (h.get_name(), h.realm)
                    h.realm = None
            else:
                print "Notice : applying default realm %s to host %s" % (default_realm.get_name(), h.get_name())
                h.realm = default_realm


    #It's used to change old Nagios2 names to
    #Nagios3 ones
    def old_properties_names_to_new(self):
        for h in self:
            h.old_properties_names_to_new()



    #We look for hostgroups property in hosts and
    def explode(self, hostgroups, contactgroups):
        #Hostgroups property need to be fullfill for got the informations
        #self.apply_partial_inheritance('hostgroups')
        #self.apply_partial_inheritance('contact_groups')

        #Register host in the hostgroups
        for h in self:
            if not h.is_tpl():
                hname = h.host_name
                if hasattr(h, 'hostgroups'):
                    hgs = h.hostgroups.split(',')
                    for hg in hgs:
                        hostgroups.add_member(hname, hg.strip())

        #items::explode_contact_groups_into_contacts
        #take all contacts from our contact_groups into our contact property
        self.explode_contact_groups_into_contacts(contactgroups)



    #Create depenancies:
    #Depencies at the host level: host parent
    def apply_dependancies(self):
        for h in self:
            h.fill_parents_dependancie()


    #Parent graph: use to find quickly relations between all host, and loop
    #return True if tehre is a loop
    def no_loop_in_parents(self):
        #Ok, we say "from now, no loop :) "
        r = True

        #Create parent graph
        parents = Graph()

        #With all hosts as nodes
        for h in self:
            if h != None:
                parents.add_node(h)

        #And now fill edges
        for h in self:
            for p in h.parents:
                if p != None:
                    parents.add_edge(p, h)

        #Now get the list of all hosts in a loop
        host_in_loops = parents.loop_check()

        #and raise errors about it
        for h in host_in_loops:
            Log().log("Error: The host '%s' is part of a circular parent/child chain!" % h.get_name())
            r = False

        return r


    #Return a list of the host_name of the hosts
    #that gotthe template with name=tpl_name
    def find_hosts_that_use_template(self, tpl_name):
        res = []
        #first find the template
        tpl = None
        for h in self:
            #Look fortemplate with the good name
            if h.is_tpl() and hasattr(h, 'name') and h.name == tpl_name:
                tpl = h

        #If we find noone, we return nothing (easy case:) )
        if tpl == None:
            return []

        #Ok, we find the tpl
        for h in self:
            if tpl in h.templates and hasattr(h, 'host_name'):
                res.append(h.host_name)
        
        return res
        
