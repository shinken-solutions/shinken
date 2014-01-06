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

""" This Class is the service one, s it manage all service specific thing.
If you look at the scheduling part, look at the scheduling item class"""

import time
import re

try:
    from ClusterShell.NodeSet import NodeSet, NodeSetParseRangeError
except ImportError:
    NodeSet = None

from shinken.objects.item import Items
from shinken.objects.schedulingitem import SchedulingItem

from shinken.autoslots import AutoSlots
from shinken.util import strip_and_uniq, format_t_into_dhms_format, to_svc_hst_distinct_lists, \
    get_key_value_sequence, GET_KEY_VALUE_SEQUENCE_ERROR_SYNTAX, GET_KEY_VALUE_SEQUENCE_ERROR_NODEFAULT, \
    GET_KEY_VALUE_SEQUENCE_ERROR_NODE, to_list_string_of_names, to_list_of_names, to_name_if_possible
from shinken.property import BoolProp, IntegerProp, FloatProp, CharProp, StringProp, ListProp
from shinken.macroresolver import MacroResolver
from shinken.eventhandler import EventHandler
from shinken.log import logger, console_logger


class Service(SchedulingItem):
    # AutoSlots create the __slots__ with properties and
    # running_properties names
    __metaclass__ = AutoSlots

    # Every service have a unique ID, and 0 is always special in
    # database and co...
    id = 1
    # The host and service do not have the same 0 value, now yes :)
    ok_up = 'OK'
    # used by item class for format specific value like for Broks
    my_type = 'service'

    # properties defined by configuration
    # required: is required in conf
    # default: default value if no set in conf
    # pythonize: function to call when transforming string to python object
    # fill_brok: if set, send to broker. there are two categories:
    #  full_status for initial and update status, check_result for check results
    # no_slots: do not take this property for __slots__
    properties = SchedulingItem.properties.copy()
    properties.update({
        'host_name':              StringProp(fill_brok=['full_status', 'check_result', 'next_schedule']),
        'hostgroup_name':         StringProp(default='', fill_brok=['full_status'], merging='join'),
        'service_description':    StringProp(fill_brok=['full_status', 'check_result', 'next_schedule']),
        'display_name':           StringProp(default='', fill_brok=['full_status']),
        'servicegroups':          StringProp(default='', fill_brok=['full_status'], brok_transformation=to_list_string_of_names, merging='join'),
        'is_volatile':            BoolProp(default='0', fill_brok=['full_status']),
        'check_command':          StringProp(fill_brok=['full_status']),
        'initial_state':          CharProp(default='o', fill_brok=['full_status']),
        'max_check_attempts':     IntegerProp(default='1',fill_brok=['full_status']),
        'check_interval':         IntegerProp(fill_brok=['full_status']),
        'retry_interval':         IntegerProp(fill_brok=['full_status']),
        'active_checks_enabled':  BoolProp(default='1', fill_brok=['full_status'], retention=True),
        'passive_checks_enabled': BoolProp(default='1', fill_brok=['full_status'], retention=True),
        'check_period':           StringProp(brok_transformation=to_name_if_possible, fill_brok=['full_status']),
        'obsess_over_service':    BoolProp(default='0', fill_brok=['full_status'], retention=True),
        'check_freshness':        BoolProp(default='0', fill_brok=['full_status']),
        'freshness_threshold':    IntegerProp(default='0', fill_brok=['full_status']),
        'event_handler':          StringProp(default='', fill_brok=['full_status']),
        'event_handler_enabled':  BoolProp(default='0', fill_brok=['full_status'], retention=True),
        'low_flap_threshold':     IntegerProp(default='-1', fill_brok=['full_status']),
        'high_flap_threshold':    IntegerProp(default='-1', fill_brok=['full_status']),
        'flap_detection_enabled': BoolProp(default='1', fill_brok=['full_status'], retention=True),
        'flap_detection_options': ListProp(default='o,w,c,u', fill_brok=['full_status']),
        'process_perf_data':      BoolProp(default='1', fill_brok=['full_status'], retention=True),
        'retain_status_information': BoolProp(default='1', fill_brok=['full_status']),
        'retain_nonstatus_information': BoolProp(default='1', fill_brok=['full_status']),
        'notification_interval':  IntegerProp(default='60', fill_brok=['full_status']),
        'first_notification_delay': IntegerProp(default='0', fill_brok=['full_status']),
        'notification_period':    StringProp(brok_transformation=to_name_if_possible, fill_brok=['full_status']),
        'notification_options':   ListProp(default='w,u,c,r,f,s', fill_brok=['full_status']),
        'notifications_enabled':  BoolProp(default='1', fill_brok=['full_status'], retention=True),
        'contacts':               StringProp(default='', brok_transformation=to_list_of_names, fill_brok=['full_status'], merging='join'),
        'contact_groups':         StringProp(default='', fill_brok=['full_status'], merging='join'),
        'stalking_options':       ListProp(default='', fill_brok=['full_status'], merging='join'),
        'notes':                  StringProp(default='', fill_brok=['full_status']),
        'notes_url':              StringProp(default='', fill_brok=['full_status']),
        'action_url':             StringProp(default='', fill_brok=['full_status']),
        'icon_image':             StringProp(default='', fill_brok=['full_status']),
        'icon_image_alt':         StringProp(default='', fill_brok=['full_status']),
        'icon_set':               StringProp(default='', fill_brok=['full_status']),
        'failure_prediction_enabled': BoolProp(default='0', fill_brok=['full_status']),
        'parallelize_check':       BoolProp(default='1', fill_brok=['full_status']),

        # Shinken specific
        'poller_tag':              StringProp(default='None'),
        'reactionner_tag':         StringProp(default='None'),
        'resultmodulations':       StringProp(default='', merging='join'),
        'business_impact_modulations':    StringProp(default='', merging='join'),
        'escalations':             StringProp(default='', fill_brok=['full_status'], merging='join'),
        'maintenance_period':      StringProp(default='', brok_transformation=to_name_if_possible, fill_brok=['full_status']),
        'time_to_orphanage':       IntegerProp(default="300", fill_brok=['full_status']),
        'merge_host_contacts': 	   BoolProp(default='0', fill_brok=['full_status']),
        'labels':                  ListProp(default='', fill_brok=['full_status'], merging='join'),

        # BUSINESS CORRELATOR PART
        # Business rules output format template
        'business_rule_output_template': StringProp(default='', fill_brok=['full_status']),
        # Business rules notifications mode
        'business_rule_smart_notifications': BoolProp(default='0', fill_brok=['full_status']),
        # Treat downtimes as acknowledgements in smart notifications
        'business_rule_downtime_as_ack': BoolProp(default='0', fill_brok=['full_status']),
        # Enforces child nodes notification options
        'business_rule_host_notification_options':    ListProp(default='', fill_brok=['full_status']),
        'business_rule_service_notification_options': ListProp(default='', fill_brok=['full_status']),

        # Easy Service dep definition
        'service_dependencies':   ListProp(default='', merging='join'), # TODO: find a way to brok it?

        # service generator
        'duplicate_foreach':       StringProp(default=''),
        'default_value':           StringProp(default=''),

        # Business_Impact value
        'business_impact':         IntegerProp(default='2', fill_brok=['full_status']),

        # Load some triggers
        'trigger':         StringProp(default=''),
        'trigger_name':    ListProp(default=''),

        # Trending
        'trending_policies':    ListProp(default='', fill_brok=['full_status'], merging='join'),

        # Our check ways. By defualt void, but will filled by an inner if need
        'checkmodulations':       ListProp(default='', fill_brok=['full_status'], merging='join'),
        'macromodulations':       ListProp(default='', merging='join'),

        # Custom views
        'custom_views'     :    ListProp(default='', fill_brok=['full_status'], merging='join'),

        # UI aggregation
        'aggregation'      :    StringProp(default='', fill_brok=['full_status']),
    })

    # properties used in the running state
    running_properties = SchedulingItem.running_properties.copy()
    running_properties.update({
        'modified_attributes': IntegerProp(default=0L, fill_brok=['full_status'], retention=True),
        'last_chk':           IntegerProp(default=0, fill_brok=['full_status', 'check_result'], retention=True),
        'next_chk':           IntegerProp(default=0, fill_brok=['full_status', 'next_schedule'], retention=True),
        'in_checking':        BoolProp(default=False, fill_brok=['full_status', 'check_result', 'next_schedule'], retention=True),
        'latency':            FloatProp(default=0, fill_brok=['full_status', 'check_result'], retention=True,),
        'attempt':            IntegerProp(default=0, fill_brok=['full_status', 'check_result'], retention=True),
        'state':              StringProp(default='PENDING', fill_brok=['full_status', 'check_result'], retention=True),
        'state_id':           IntegerProp(default=0, fill_brok=['full_status', 'check_result'], retention=True),
        'current_event_id':   IntegerProp(default=0, fill_brok=['full_status', 'check_result'], retention=True),
        'last_event_id':      IntegerProp(default=0, fill_brok=['full_status', 'check_result'], retention=True),
        'last_state':         StringProp(default='PENDING', fill_brok=['full_status', 'check_result'], retention=True),
        'last_state_type':    StringProp(default='HARD', fill_brok=['full_status', 'check_result'], retention=True),
        'last_state_id':      IntegerProp(default=0, fill_brok=['full_status', 'check_result'], retention=True),
        'last_state_change':  FloatProp(default=0.0, fill_brok=['full_status', 'check_result'], retention=True),
        'last_hard_state_change': FloatProp(default=0.0, fill_brok=['full_status', 'check_result'], retention=True),
        'last_hard_state':    StringProp(default='PENDING', fill_brok=['full_status'], retention=True),
        'last_hard_state_id': IntegerProp(default=0, fill_brok=['full_status'], retention=True),
        'last_time_ok':       IntegerProp(default=0, fill_brok=['full_status', 'check_result'], retention=True),
        'last_time_warning':  IntegerProp(default=0, fill_brok=['full_status', 'check_result'], retention=True),
        'last_time_critical': IntegerProp(default=0, fill_brok=['full_status', 'check_result'], retention=True),
        'last_time_unknown':  IntegerProp(default=0, fill_brok=['full_status', 'check_result'], retention=True),
        'duration_sec':       IntegerProp(default=0, fill_brok=['full_status'], retention=True),
        'state_type':         StringProp(default='HARD', fill_brok=['full_status', 'check_result'], retention=True),
        'state_type_id':      IntegerProp(default=0, fill_brok=['full_status', 'check_result'], retention=True),
        'output':             StringProp(default='', fill_brok=['full_status', 'check_result'], retention=True),
        'long_output':        StringProp(default='', fill_brok=['full_status', 'check_result'], retention=True),
        'is_flapping':        BoolProp(default=False, fill_brok=['full_status'], retention=True),
        #  dependencies for actions like notif of event handler,
        # so AFTER check return
        'act_depend_of': ListProp(default=[]),
        # dependencies for checks raise, so BEFORE checks
        'chk_depend_of': ListProp(default=[]),
        # elements that depend of me, so the reverse than just upper
        'act_depend_of_me': ListProp(default=[]),
        # elements that depend of me
        'chk_depend_of_me': ListProp(default=[]),

        'last_state_update':  FloatProp(default=0.0, fill_brok=['full_status'], retention=True),
        'checks_in_progress': ListProp(default=[]), # no brok because checks are too linked
        'notifications_in_progress': ListProp(default={}, retention=True), # no broks because notifications are too linked
        'downtimes':          ListProp(default=[], fill_brok=['full_status'], retention=True),
        'comments':           ListProp(default=[], fill_brok=['full_status'], retention=True),
        'flapping_changes':   ListProp(default=[], fill_brok=['full_status'], retention=True),
        'flapping_comment_id': IntegerProp(default=0, fill_brok=['full_status'], retention=True),
        'percent_state_change': FloatProp(default=0.0, fill_brok=['full_status', 'check_result'], retention=True),
        'problem_has_been_acknowledged': BoolProp(default=False, fill_brok=['full_status'], retention=True),
        'acknowledgement':    StringProp(default=None, retention=True),
        'acknowledgement_type': IntegerProp(default=1, fill_brok=['full_status', 'check_result'], retention=True),
        'check_type':         IntegerProp(default=0, fill_brok=['full_status', 'check_result'], retention=True),
        'has_been_checked':   IntegerProp(default=0, fill_brok=['full_status', 'check_result'], retention=True),
        'should_be_scheduled': IntegerProp(default=1, fill_brok=['full_status'], retention=True),
        'last_problem_id':    IntegerProp(default=0, fill_brok=['full_status', 'check_result'], retention=True),
        'current_problem_id': IntegerProp(default=0, fill_brok=['full_status', 'check_result'], retention=True),
        'execution_time':     FloatProp(default=0.0, fill_brok=['full_status', 'check_result'], retention=True),
        'last_notification':  FloatProp(default=0.0, fill_brok=['full_status'], retention=True),
        'current_notification_number': IntegerProp(default=0, fill_brok=['full_status'], retention=True),
        'current_notification_id': IntegerProp(default=0, fill_brok=['full_status'], retention=True),
        'check_flapping_recovery_notification': BoolProp(default=True, fill_brok=['full_status'], retention=True),
        'scheduled_downtime_depth': IntegerProp(default=0, fill_brok=['full_status'], retention=True),
        'pending_flex_downtime': IntegerProp(default=0, fill_brok=['full_status'], retention=True),
        'timeout':            IntegerProp(default=0, fill_brok=['full_status', 'check_result'], retention=True),
        'start_time':         IntegerProp(default=0, fill_brok=['full_status', 'check_result'], retention=True),
        'end_time':           IntegerProp(default=0, fill_brok=['full_status', 'check_result'], retention=True),
        'early_timeout':      IntegerProp(default=0, fill_brok=['full_status', 'check_result'], retention=True),
        'return_code':        IntegerProp(default=0, fill_brok=['full_status', 'check_result'], retention=True),
        'perf_data':          StringProp(default='', fill_brok=['full_status', 'check_result'], retention=True),
        'last_perf_data':     StringProp(default='', retention=True),
        'host':               StringProp(default=None),
        'customs':            ListProp(default={}, fill_brok=['full_status']),
        # Warning: for the notified_contacts retention save, we save only the names of the contacts, and we should RELINK
        # them when we load it.
        'notified_contacts':  ListProp(default=set(), retention=True, retention_preparation=to_list_of_names), # use for having all contacts we have notified
        'in_scheduled_downtime': BoolProp(default=False, fill_brok=['full_status'], retention=True),
        'in_scheduled_downtime_during_last_check': BoolProp(default=False, retention=True),
        'actions':            ListProp(default=[]), # put here checks and notif raised
        'broks':              ListProp(default=[]), # and here broks raised


        # Problem/impact part
        'is_problem':         BoolProp(default=False, fill_brok=['full_status']),
        'is_impact':          BoolProp(default=False, fill_brok=['full_status']),
        # the save value of our business_impact for "problems"
        'my_own_business_impact':   IntegerProp(default=-1, fill_brok=['full_status']),
        # list of problems that make us an impact
        'source_problems':    ListProp(default=[], fill_brok=['full_status'], brok_transformation=to_svc_hst_distinct_lists),
        # list of the impact I'm the cause of
        'impacts':            ListProp(default=[], fill_brok=['full_status'], brok_transformation=to_svc_hst_distinct_lists),
        # keep a trace of the old state before being an impact
        'state_before_impact': StringProp(default='PENDING'),
        # keep a trace of the old state id before being an impact
        'state_id_before_impact': IntegerProp(default=0),
        # if the state change, we know so we do not revert it
        'state_changed_since_impact': BoolProp(default=False),

        # BUSINESS CORRELATOR PART
        # Say if we are business based rule or not
        'got_business_rule': BoolProp(default=False, fill_brok=['full_status']),
        # Previously processed business rule (with macro expanded)
        'processed_business_rule': StringProp(default="", fill_brok=['full_status']),
        # Our Dependency node for the business rule
        'business_rule': StringProp(default=None),


        # Here it's the elements we are depending on
        # so our parents as network relation, or a host
        # we are depending in a hostdependency
        # or even if we are business based.
        'parent_dependencies': StringProp(default=set(), brok_transformation=to_svc_hst_distinct_lists, fill_brok=['full_status']),
        # Here it's the guys that depend on us. So it's the total
        # opposite of the parent_dependencies
        'child_dependencies': StringProp(brok_transformation=to_svc_hst_distinct_lists, default=set(), fill_brok=['full_status']),

        # Manage the unknown/unreach during hard state
        'in_hard_unknown_reach_phase': BoolProp(default=False, retention=True),
        'was_in_hard_unknown_reach_phase': BoolProp(default=False, retention=True),
        'state_before_hard_unknown_reach_phase': StringProp(default='OK', retention=True),

        # Set if the element just change its father/son topology
        'topology_change': BoolProp(default=False, fill_brok=['full_status']),

        # Trigger list
        'triggers': StringProp(default=[])

    })

    # Mapping between Macros and properties (can be prop or a function)
    macros = {
        'SERVICEDESC':            'service_description',
        'SERVICEDISPLAYNAME':     'display_name',
        'SERVICESTATE':           'state',
        'SERVICESTATEID':         'state_id',
        'LASTSERVICESTATE':       'last_state',
        'LASTSERVICESTATEID':     'last_state_id',
        'SERVICESTATETYPE':       'state_type',
        'SERVICEATTEMPT':         'attempt',
        'MAXSERVICEATTEMPTS':     'max_check_attempts',
        'SERVICEISVOLATILE':      'is_volatile',
        'SERVICEEVENTID':         'current_event_id',
        'LASTSERVICEEVENTID':     'last_event_id',
        'SERVICEPROBLEMID':       'current_problem_id',
        'LASTSERVICEPROBLEMID':   'last_problem_id',
        'SERVICELATENCY':         'latency',
        'SERVICEEXECUTIONTIME':   'execution_time',
        'SERVICEDURATION':        'get_duration',
        'SERVICEDURATIONSEC':     'get_duration_sec',
        'SERVICEDOWNTIME':        'get_downtime',
        'SERVICEPERCENTCHANGE':   'percent_state_change',
        'SERVICEGROUPNAME':       'get_groupname',
        'SERVICEGROUPNAMES':      'get_groupnames',
        'LASTSERVICECHECK':       'last_chk',
        'LASTSERVICESTATECHANGE': 'last_state_change',
        'LASTSERVICEOK':          'last_time_ok',
        'LASTSERVICEWARNING':     'last_time_warning',
        'LASTSERVICEUNKNOWN':     'last_time_unknown',
        'LASTSERVICECRITICAL':    'last_time_critical',
        'SERVICEOUTPUT':          'output',
        'LONGSERVICEOUTPUT':      'long_output',
        'SERVICEPERFDATA':        'perf_data',
        'LASTSERVICEPERFDATA':    'last_perf_data',
        'SERVICECHECKCOMMAND':    'get_check_command',
        'SERVICEACKAUTHOR':       'get_ack_author_name',
        'SERVICEACKAUTHORNAME':   'get_ack_author_name',
        'SERVICEACKAUTHORALIAS':  'get_ack_author_name',
        'SERVICEACKCOMMENT':      'get_ack_comment',
        'SERVICEACTIONURL':       'action_url',
        'SERVICENOTESURL':        'notes_url',
        'SERVICENOTES':           'notes',
        'SERVICEBUSINESSIMPACT':  'business_impact'
    }

    # This tab is used to transform old parameters name into new ones
    # so from Nagios2 format, to Nagios3 ones.
    # Or Shinken deprecated names like criticity
    old_properties = {
        'normal_check_interval':    'check_interval',
        'retry_check_interval':    'retry_interval',
        'criticity':    'business_impact',
        'hostgroup':    'hostgroup_name',
        'hostgroups':    'hostgroup_name',
        ## 'criticitymodulations':    'business_impact_modulations',
    }

#######
#                   __ _                       _   _
#                  / _(_)                     | | (_)
#   ___ ___  _ __ | |_ _  __ _ _   _ _ __ __ _| |_ _  ___  _ __
#  / __/ _ \| '_ \|  _| |/ _` | | | | '__/ _` | __| |/ _ \| '_ \
# | (_| (_) | | | | | | | (_| | |_| | | | (_| | |_| | (_) | | | |
#  \___\___/|_| |_|_| |_|\__, |\__,_|_|  \__,_|\__|_|\___/|_| |_|
#                         __/ |
#                        |___/
######

    # Give a nice name output
    def get_name(self):
        if hasattr(self, 'service_description'):
            return self.service_description
        if hasattr(self, 'name'):
            return self.name
        return 'SERVICE-DESCRIPTION-MISSING'

    # Get the servicegroups names
    def get_groupnames(self):
        return ','.join([sg.get_name() for sg in self.servicegroups])

    # Need the whole name for debugging purpose
    def get_dbg_name(self):
        return "%s/%s" % (self.host.host_name, self.service_description)

    def get_full_name(self):
        if self.host and hasattr(self.host, 'host_name') and hasattr(self, 'service_description'):
            return "%s/%s" % (self.host.host_name, self.service_description)
        return 'UNKNOWN-SERVICE'

    # Get our realm, so in fact our host one
    def get_realm(self):
        return self.host.get_realm()

    def get_hostgroups(self):
        return self.host.hostgroups

    def get_host_tags(self):
        return self.host.tags

    # Check is required prop are set:
    # template are always correct
    # contacts OR contactgroups is need
    def is_correct(self):
        state = True
        cls = self.__class__

        source = getattr(self, 'imported_from', 'unknown')

        desc = getattr(self, 'service_description', 'unnamed')
        hname = getattr(self, 'host_name', 'unnamed')

        special_properties = ('check_period', 'notification_interval', 'host_name',
                              'hostgroup_name', 'notification_period')

        for prop, entry in cls.properties.items():
            if prop not in special_properties:
                if not hasattr(self, prop) and entry.required:
                    logger.error("The service %s on host '%s' does not have %s" % (desc, hname, prop))
                    state = False  # Bad boy...

        # Then look if we have some errors in the conf
        # Juts print warnings, but raise errors
        for err in self.configuration_warnings:
            logger.warning("[service::%s] %s" % (desc, err))

        # Raised all previously saw errors like unknown contacts and co
        if self.configuration_errors != []:
            state = False
            for err in self.configuration_errors:
                logger.error("[service::%s] %s" % (self.get_full_name(), err))

        # If no notif period, set it to None, mean 24x7
        if not hasattr(self, 'notification_period'):
            self.notification_period = None

        # Ok now we manage special cases...
        if self.notifications_enabled and self.contacts == []:
            logger.warning("The service '%s' in the host '%s' does not have contacts nor contact_groups in '%s'" % (desc, hname, source))

        # Set display_name if need
        if getattr(self, 'display_name', '') == '':
            self.display_name = getattr(self, 'service_description', '')

        # If we got an event handler, it should be valid
        if getattr(self, 'event_handler', None) and not self.event_handler.is_valid():
            logger.info("%s: my event_handler %s is invalid" % (self.get_name(), self.event_handler.command))
            state = False

        if not hasattr(self, 'check_command'):
            logger.info("%s: I've got no check_command" % self.get_name())
            state = False
        # Ok got a command, but maybe it's invalid
        else:
            if not self.check_command.is_valid():
                logger.info("%s: my check_command %s is invalid" % (self.get_name(), self.check_command.command))
                state = False
            if self.got_business_rule:
                if not self.business_rule.is_valid():
                    logger.info("%s: my business rule is invalid" % (self.get_name(),))
                    for bperror in self.business_rule.configuration_errors:
                        logger.info("%s: %s" % (self.get_name(), bperror))
                    state = False
        if not hasattr(self, 'notification_interval') \
                and  self.notifications_enabled == True:
            logger.info("%s: I've got no notification_interval but I've got notifications enabled" % self.get_name())
            state = False
        if self.host is None:
            logger.warning("The service '%s' got an unknown host_name '%s'." % (desc, self.host_name))
            # do not set tis a a true error, only we will delete this after
        if not hasattr(self, 'check_period'):
            self.check_period = None
        if hasattr(self, 'service_description'):
            for c in cls.illegal_object_name_chars:
                if c in self.service_description:
                    logger.info("%s: My service_description got the character %s that is not allowed." % (self.get_name(), c))
                    state = False
        return state

    # The service is dependent of his father dep
    # Must be AFTER linkify
    def fill_daddy_dependency(self):
        #  Depend of host, all status, is a networkdep
        # and do not have timeperiod, and follow parents dep
        if self.host is not None:
            # I add the dep in MY list
            self.act_depend_of.append((self.host,
                                        ['d', 'u', 's', 'f'],
                                        'network_dep',
                                        None, True))
            # I add the dep in Daddy list
            self.host.act_depend_of_me.append((self,
                                                ['d', 'u', 's', 'f'],
                                                'network_dep',
                                                None, True))

            # And the parent/child dep lists too
            self.host.register_son_in_parent_child_dependencies(self)

    # Register the dependency between 2 service for action (notification etc)
    def add_service_act_dependency(self, srv, status, timeperiod, inherits_parent):
        # first I add the other the I depend on in MY list
        self.act_depend_of.append((srv, status, 'logic_dep',
                                    timeperiod, inherits_parent))
        # then I register myself in the other service dep list
        srv.act_depend_of_me.append((self, status, 'logic_dep',
                                      timeperiod, inherits_parent))

        # And the parent/child dep lists too
        srv.register_son_in_parent_child_dependencies(self)

    # Register the dependency between 2 service for action (notification etc)
    # but based on a BUSINESS rule, so on fact:
    # ERP depend on database, so we fill just database.act_depend_of_me
    # because we will want ERP mails to go on! So call this
    # on the database service with the srv=ERP service
    def add_business_rule_act_dependency(self, srv, status, timeperiod, inherits_parent):
        # I only register so he know that I WILL be a impact
        self.act_depend_of_me.append((srv, status, 'business_dep',
                                      timeperiod, inherits_parent))

        # And the parent/child dep lists too
        self.register_son_in_parent_child_dependencies(srv)

    # Register the dependency between 2 service for checks
    def add_service_chk_dependency(self, srv, status, timeperiod, inherits_parent):
        # first I add the other the I depend on in MY list
        self.chk_depend_of.append((srv, status, 'logic_dep',
                                    timeperiod, inherits_parent))
        # then I register myself in the other service dep list
        srv.chk_depend_of_me.append((self, status, 'logic_dep',
                                      timeperiod, inherits_parent))

        # And the parent/child dep lists too
        srv.register_son_in_parent_child_dependencies(self)

    # For a given host, look for all copy we must
    # create for for_each property
    def duplicate(self, host):
        duplicates = []

        # In macro, it's all in UPPER case
        prop = self.duplicate_foreach.strip().upper()

        # If I do not have the property, we bail out
        if prop in host.customs:
            # Get the list entry, and the not one if there is one
            entry = host.customs[prop]
            # Look at the list of the key we do NOT want maybe,
            # for _disks it will be _!disks
            not_entry = host.customs.get('_' + '!' + prop[1:], '').split(',')
            not_keys = strip_and_uniq(not_entry)

            default_value = getattr(self, 'default_value', '')
            # Transform the generator string to a list
            # Missing values are filled with the default value
            (key_values, errcode) = get_key_value_sequence(entry, default_value)

            if key_values:
                for key_value in key_values:
                    key = key_value['KEY']
                    # Maybe this key is in the NOT list, if so, skip it
                    if key in not_keys:
                        continue
                    value = key_value['VALUE']
                    new_s = self.copy()
                    new_s.host_name = host.get_name()
                    if self.is_tpl():  # if template, the new one is not
                        new_s.register = 1
                    for key in key_value:
                        if key == 'KEY':
                            if hasattr(self, 'service_description'):
                                # We want to change all illegal chars to a _ sign. We can't use class.illegal_obj_char
                                # because in the "explode" phase, we do not have access to this data! :(
                                safe_key_value = re.sub(r'[' + "`~!$%^&*\"|'<>?,()=" + ']+', '_', key_value[key])
                                new_s.service_description = self.service_description.replace('$' + key + '$', safe_key_value)
                        # Here is a list of property where we will expand the $KEY$ by the value
                        _the_expandables = ['check_command', 'aggregation', 'service_dependencies', 'event_handler']
                        for prop in _the_expandables:
                            if hasattr(self, prop):
                                # here we can replace VALUE, VALUE1, VALUE2,...
                                setattr(new_s, prop, getattr(new_s, prop).replace('$' + key + '$', key_value[key]))
                        if hasattr(self, 'aggregation'):
                            new_s.aggregation = new_s.aggregation.replace('$' + key + '$', key_value[key])
                    # And then add in our list this new service
                    duplicates.append(new_s)
            else:
                # If error, we should link the error to the host, because self is a template, and so won't be checked not print!
                if errcode == GET_KEY_VALUE_SEQUENCE_ERROR_SYNTAX:
                    err = "The custom property '%s' of the host '%s' is not a valid entry %s for a service generator" % (self.duplicate_foreach.strip(), host.get_name(), entry)
                    logger.warning(err)
                    host.configuration_errors.append(err)
                elif errcode == GET_KEY_VALUE_SEQUENCE_ERROR_NODEFAULT:
                    err = "The custom property '%s 'of the host '%s' has empty values %s but the service %s has no default_value" % (self.duplicate_foreach.strip(), host.get_name(), entry, self.service_description)
                    logger.warning(err)
                    host.configuration_errors.append(err)
                elif errcode == GET_KEY_VALUE_SEQUENCE_ERROR_NODE:
                    err = "The custom property '%s' of the host '%s' has an invalid node range %s" % (self.duplicate_foreach.strip(), host.get_name(), entry)
                    logger.warning(err)
                    host.configuration_errors.append(err)
        return duplicates

#####
#                         _
#                        (_)
#  _ __ _   _ _ __  _ __  _ _ __   __ _
# | '__| | | | '_ \| '_ \| | '_ \ / _` |
# | |  | |_| | | | | | | | | | | | (_| |
# |_|   \__,_|_| |_|_| |_|_|_| |_|\__, |
#                                  __/ |
#                                 |___/
####

    # Set unreachable: our host is DOWN, but it mean nothing for a service
    def set_unreachable(self):
        pass

    # We just go an impact, so we go unreachable
    # but only if it's enable in the configuration
    def set_impact_state(self):
        cls = self.__class__
        if cls.enable_problem_impacts_states_change:
            # Keep a trace of the old state (problem came back before
            # a new checks)
            self.state_before_impact = self.state
            self.state_id_before_impact = self.state_id
            # this flag will know if we override the impact state
            self.state_changed_since_impact = False
            self.state = 'UNKNOWN'  # exit code UNDETERMINED
            self.state_id = 3

    # Ok, we are no more an impact, if no news checks
    # override the impact state, we came back to old
    # states
    # And only if we enable the state change for impacts
    def unset_impact_state(self):
        cls = self.__class__
        if cls.enable_problem_impacts_states_change and not self.state_changed_since_impact:
            self.state = self.state_before_impact
            self.state_id = self.state_id_before_impact

    # Set state with status return by the check
    # and update flapping state
    def set_state_from_exit_status(self, status):
        now = time.time()
        self.last_state_update = now

        # we should put in last_state the good last state:
        # if not just change the state by an problem/impact
        # we can take current state. But if it's the case, the
        # real old state is self.state_before_impact (it's the TRUE
        # state in fact)
        # but only if the global conf have enable the impact state change
        cls = self.__class__
        if cls.enable_problem_impacts_states_change \
                and self.is_impact \
                and not self.state_changed_since_impact:
            self.last_state = self.state_before_impact
        else:  # standard case
            self.last_state = self.state

        if status == 0:
            self.state = 'OK'
            self.state_id = 0
            self.last_time_ok = int(self.last_state_update)
            state_code = 'o'
        elif status == 1:
            self.state = 'WARNING'
            self.state_id = 1
            self.last_time_warning = int(self.last_state_update)
            state_code = 'w'
        elif status == 2:
            self.state = 'CRITICAL'
            self.state_id = 2
            self.last_time_critical = int(self.last_state_update)
            state_code = 'c'
        elif status == 3:
            self.state = 'UNKNOWN'
            self.state_id = 3
            self.last_time_unknown = int(self.last_state_update)
            state_code = 'u'
        else:
            self.state = 'CRITICAL'  # exit code UNDETERMINED
            self.state_id = 2
            self.last_time_critical = int(self.last_state_update)
            state_code = 'c'

        if state_code in self.flap_detection_options:
            self.add_flapping_change(self.state != self.last_state)

        if self.state != self.last_state:
            self.last_state_change = self.last_state_update

        self.duration_sec = now - self.last_state_change

    # Return True if status is the state (like OK) or small form like 'o'
    def is_state(self, status):
        if status == self.state:
            return True
        # Now low status
        elif status == 'o' and self.state == 'OK':
            return True
        elif status == 'c' and self.state == 'CRITICAL':
            return True
        elif status == 'w' and self.state == 'WARNING':
            return True
        elif status == 'u' and self.state == 'UNKNOWN':
            return True
        return False

    # The last time when the state was not OK
    def last_time_non_ok_or_up(self):
        non_ok_times = filter(lambda x: x > self.last_time_ok, [self.last_time_warning,
                                                                self.last_time_critical,
                                                                self.last_time_unknown])
        if len(non_ok_times) == 0:
            last_time_non_ok = 0  # program_start would be better
        else:
            last_time_non_ok = min(non_ok_times)
        return last_time_non_ok

    # Add a log entry with a SERVICE ALERT like:
    # SERVICE ALERT: server;Load;UNKNOWN;HARD;1;I don't know what to say...
    def raise_alert_log_entry(self):
        console_logger.alert('SERVICE ALERT: %s;%s;%s;%s;%d;%s'
                            % (self.host.get_name(), self.get_name(),
                               self.state, self.state_type,
                               self.attempt, self.output))

    # If the configuration allow it, raise an initial log like
    # CURRENT SERVICE STATE: server;Load;UNKNOWN;HARD;1;I don't know what to say...
    def raise_initial_state(self):
        if self.__class__.log_initial_states:
            console_logger.info('CURRENT SERVICE STATE: %s;%s;%s;%s;%d;%s'
                                % (self.host.get_name(), self.get_name(),
                                   self.state, self.state_type,
                                   self.attempt, self.output))

    # Add a log entry with a Freshness alert like:
    # Warning: The results of host 'Server' are stale by 0d 0h 0m 58s (threshold=0d 1h 0m 0s).
    # I'm forcing an immediate check of the host.
    def raise_freshness_log_entry(self, t_stale_by, t_threshold):
        logger.warning("The results of service '%s' on host '%s' are stale "
                       "by %s (threshold=%s).  I'm forcing an immediate check "
                       "of the service."
                       % (self.get_name(), self.host.get_name(),
                          format_t_into_dhms_format(t_stale_by),
                          format_t_into_dhms_format(t_threshold)))

    # Raise a log entry with a Notification alert like
    # SERVICE NOTIFICATION: superadmin;server;Load;OK;notify-by-rss;no output
    def raise_notification_log_entry(self, n):
        contact = n.contact
        command = n.command_call
        if n.type in ('DOWNTIMESTART', 'DOWNTIMEEND', 'DOWNTIMECANCELLED',
                      'CUSTOM', 'ACKNOWLEDGEMENT', 'FLAPPINGSTART',
                      'FLAPPINGSTOP', 'FLAPPINGDISABLED'):
            state = '%s (%s)' % (n.type, self.state)
        else:
            state = self.state
        if self.__class__.log_notifications:
            console_logger.alert("SERVICE NOTIFICATION: %s;%s;%s;%s;%s;%s"
                                % (contact.get_name(),
                                   self.host.get_name(), self.get_name(), state,
                                   command.get_name(), self.output))

    # Raise a log entry with a Eventhandler alert like
    # SERVICE EVENT HANDLER: test_host_0;test_ok_0;OK;SOFT;4;eventhandler
    def raise_event_handler_log_entry(self, command):
        if self.__class__.log_event_handlers:
            console_logger.alert("SERVICE EVENT HANDLER: %s;%s;%s;%s;%s;%s"
                                % (self.host.get_name(), self.get_name(),
                                   self.state, self.state_type,
                                   self.attempt, command.get_name()))

    # Raise a log entry with FLAPPING START alert like
    # SERVICE FLAPPING ALERT: server;LOAD;STARTED; Service appears to have started flapping (50.6% change >= 50.0% threshold)
    def raise_flapping_start_log_entry(self, change_ratio, threshold):
        console_logger.alert("SERVICE FLAPPING ALERT: %s;%s;STARTED; "
                            "Service appears to have started flapping "
                            "(%.1f%% change >= %.1f%% threshold)"
                            % (self.host.get_name(), self.get_name(),
                               change_ratio, threshold))

    # Raise a log entry with FLAPPING STOP alert like
    # SERVICE FLAPPING ALERT: server;LOAD;STOPPED; Service appears to have stopped flapping (23.0% change < 25.0% threshold)
    def raise_flapping_stop_log_entry(self, change_ratio, threshold):
        console_logger.alert("SERVICE FLAPPING ALERT: %s;%s;STOPPED; "
                            "Service appears to have stopped flapping "
                            "(%.1f%% change < %.1f%% threshold)"
                            % (self.host.get_name(), self.get_name(),
                               change_ratio, threshold))

    # If there is no valid time for next check, raise a log entry
    def raise_no_next_check_log_entry(self):
        logger.warning("I cannot schedule the check for the service '%s' on "
                       "host '%s' because there is not future valid time"
                       % (self.get_name(), self.host.get_name()))

    # Raise a log entry when a downtime begins
    # SERVICE DOWNTIME ALERT: test_host_0;test_ok_0;STARTED; Service has entered a period of scheduled downtime
    def raise_enter_downtime_log_entry(self):
        console_logger.alert("SERVICE DOWNTIME ALERT: %s;%s;STARTED; "
                            "Service has entered a period of scheduled "
                            "downtime"
                            % (self.host.get_name(), self.get_name()))

    # Raise a log entry when a downtime has finished
    # SERVICE DOWNTIME ALERT: test_host_0;test_ok_0;STOPPED; Service has exited from a period of scheduled downtime
    def raise_exit_downtime_log_entry(self):
        console_logger.alert("SERVICE DOWNTIME ALERT: %s;%s;STOPPED; Service "
                            "has exited from a period of scheduled downtime"
                            % (self.host.get_name(), self.get_name()))

    # Raise a log entry when a downtime prematurely ends
    # SERVICE DOWNTIME ALERT: test_host_0;test_ok_0;CANCELLED; Service has entered a period of scheduled downtime
    def raise_cancel_downtime_log_entry(self):
        console_logger.alert("SERVICE DOWNTIME ALERT: %s;%s;CANCELLED; "
                            "Scheduled downtime for service has been cancelled."
                            % (self.host.get_name(), self.get_name()))

    # Is stalking?
    # Launch if check is waitconsume==first time
    # and if c.status is in self.stalking_options
    def manage_stalking(self, c):
        need_stalk = False
        if c.status == 'waitconsume':
            if c.exit_status == 0 and 'o' in self.stalking_options:
                need_stalk = True
            elif c.exit_status == 1 and 'w' in self.stalking_options:
                need_stalk = True
            elif c.exit_status == 2 and 'c' in self.stalking_options:
                need_stalk = True
            elif c.exit_status == 3 and 'u' in self.stalking_options:
                need_stalk = True

            if c.output == self.output:
                need_stalk = False
        if need_stalk:
            logger.info("Stalking %s: %s" % (self.get_name(), c.output))

    # Give data for checks's macros
    def get_data_for_checks(self):
        return [self.host, self]

    # Give data for event handlers's macros
    def get_data_for_event_handler(self):
        return [self.host, self]

    # Give data for notifications'n macros
    def get_data_for_notifications(self, contact, n):
        return [self.host, self, contact, n]

    # See if the notification is launchable (time is OK and contact is OK too)
    def notification_is_blocked_by_contact(self, n, contact):
        return not contact.want_service_notification(self.last_chk, self.state, n.type, self.business_impact, n.command_call)

    def get_duration_sec(self):
        return str(int(self.duration_sec))

    def get_duration(self):
        m, s = divmod(self.duration_sec, 60)
        h, m = divmod(m, 60)
        return "%02dh %02dm %02ds" % (h, m, s)

    def get_ack_author_name(self):
        if self.acknowledgement is None:
            return ''
        return self.acknowledgement.author

    def get_ack_comment(self):
        if self.acknowledgement is None:
            return ''
        return self.acknowledgement.comment

    def get_check_command(self):
        return self.check_command.get_name()

    # Check if a notification for this service is suppressed at this time
    def notification_is_blocked_by_item(self, type, t_wished = None):
        if t_wished is None:
            t_wished = time.time()

        #  TODO
        # forced notification
        # pass if this is a custom notification

        # Block if notifications are program-wide disabled
        if not self.enable_notifications:
            return True

        # Does the notification period allow sending out this notification?
        if self.notification_period is not None and not self.notification_period.is_time_valid(t_wished):
            return True

        # Block if notifications are disabled for this service
        if not self.notifications_enabled:
            return True

        # Block if the current status is in the notification_options w,u,c,r,f,s
        if 'n' in self.notification_options:
            return True
        if type in ('PROBLEM', 'RECOVERY'):
            if self.state == 'UNKNOWN' and not 'u' in self.notification_options:
                return True
            if self.state == 'WARNING' and not 'w' in self.notification_options:
                return True
            if self.state == 'CRITICAL' and not 'c' in self.notification_options:
                return True
            if self.state == 'OK' and not 'r' in self.notification_options:
                return True
        if (type in ('FLAPPINGSTART', 'FLAPPINGSTOP', 'FLAPPINGDISABLED')
                and not 'f' in self.notification_options):
            return True
        if (type in ('DOWNTIMESTART', 'DOWNTIMEEND', 'DOWNTIMECANCELLED')
                and not 's' in self.notification_options):
            return True

        # Acknowledgements make no sense when the status is ok/up
        if type == 'ACKNOWLEDGEMENT':
            if self.state == self.ok_up:
                return True

        # When in downtime, only allow end-of-downtime notifications
        if self.scheduled_downtime_depth > 1 and type not in ('DOWNTIMEEND', 'DOWNTIMECANCELLED'):
            return True

        # Block if host is in a scheduled downtime
        if self.host.scheduled_downtime_depth > 0:
            return True

        # Block if in a scheduled downtime and a problem arises, or flapping event
        if self.scheduled_downtime_depth > 0 and type in ('PROBLEM', 'RECOVERY', 'FLAPPINGSTART', 'FLAPPINGSTOP', 'FLAPPINGDISABLED'):
            return True

        # Block if the status is SOFT
        if self.state_type == 'SOFT' and type == 'PROBLEM':
            return True

        # Block if the problem has already been acknowledged
        if self.problem_has_been_acknowledged and type != 'ACKNOWLEDGEMENT':
            return True

        # Block if flapping
        if self.is_flapping and type not in ('FLAPPINGSTART', 'FLAPPINGSTOP', 'FLAPPINGDISABLED'):
            return True

        # Block if host is down
        if self.host.state != self.host.ok_up:
            return True

        # Block if business rule smart notifications is enabled and all its
        # childs have been acknowledged or are under downtime.
        if self.got_business_rule is True \
                and self.business_rule_smart_notifications is True \
                and self.business_rule_notification_is_blocked() is True \
                and type == 'PROBLEM':
            return True

        return False

    # Get a oc*p command if item has obsess_over_*
    # command. It must be enabled locally and globally
    def get_obsessive_compulsive_processor_command(self):
        cls = self.__class__
        if not cls.obsess_over or not self.obsess_over_service:
            return

        m = MacroResolver()
        data = self.get_data_for_event_handler()
        cmd = m.resolve_command(cls.ocsp_command, data)
        e = EventHandler(cmd, timeout=cls.ocsp_timeout)

        # ok we can put it in our temp action queue
        self.actions.append(e)


# Class for list of services. It's mainly, mainly for configuration part
class Services(Items):
    inner_class = Service  # use for know what is in items

    # Create the reversed list for speedup search by host_name/name
    # We also tag service already in list: they are twins. It's a a bad things.
    # Hostgroups service have an ID higher than host service. So it we tag
    # an id that already are in the list, this service is already
    # exist, and is a host,
    # or a previous hostgroup, but define before.
    def create_reversed_list(self):
        self.reversed_list = {}
        self.twins = []
        for s in self:
            if hasattr(s, 'service_description') and hasattr(s, 'host_name'):
                s_desc = getattr(s, 'service_description')
                s_host_name = getattr(s, 'host_name')
                key = (s_host_name, s_desc)
                if key not in self.reversed_list:
                    self.reversed_list[key] = s.id
                else:
                    self.twins.append(s.id)
        # For service, the reversed_list is not used for
        # search, so we del it
        del self.reversed_list

    # TODO: finish search to use reversed
    # Search a service id by it's name and host_name
    def find_srv_id_by_name_and_hostname(self, host_name, name):
        # key = (host_name, name)
        # if key in self.reversed_list:
        #     return self.reversed_list[key]

        # if not, maybe in the whole list?
        for s in self:
            # Runtime first, available only after linkify
            if hasattr(s, 'service_description') and hasattr(s, 'host'):
                if s.service_description == name and s.host == host_name:
                    return s.id
            # At config part, available before linkify
            if hasattr(s, 'service_description') and hasattr(s, 'host_name'):
                if s.service_description == name and s.host_name == host_name:
                    return s.id
        return None

    # Search a service by it's name and hot_name
    def find_srv_by_name_and_hostname(self, host_name, name):
        if hasattr(self, 'hosts'):
            h = self.hosts.find_by_name(host_name)
            if h is None:
                return None
            return h.find_service_by_name(name)

        id = self.find_srv_id_by_name_and_hostname(host_name, name)
        if id is not None:
            return self.items[id]
        else:
            return None

    # Make link between elements:
    # service -> host
    # service -> command
    # service -> timeperiods
    # service -> contacts
    def linkify(self, hosts, commands, timeperiods, contacts,
                resultmodulations, businessimpactmodulations, escalations,
                servicegroups, triggers, checkmodulations, macromodulations):
        self.linkify_with_timeperiods(timeperiods, 'notification_period')
        self.linkify_with_timeperiods(timeperiods, 'check_period')
        self.linkify_with_timeperiods(timeperiods, 'maintenance_period')
        self.linkify_s_by_hst(hosts)
        self.linkify_s_by_sg(servicegroups)
        self.linkify_one_command_with_commands(commands, 'check_command')
        self.linkify_one_command_with_commands(commands, 'event_handler')
        self.linkify_with_contacts(contacts)
        self.linkify_with_resultmodulations(resultmodulations)
        self.linkify_with_business_impact_modulations(businessimpactmodulations)
        # WARNING: all escalations will not be link here
        # (just the escalation here, not serviceesca or hostesca).
        # This last one will be link in escalations linkify.
        self.linkify_with_escalations(escalations)
        self.linkify_with_triggers(triggers)
        self.linkify_with_checkmodulations(checkmodulations)
        self.linkify_with_macromodulations(macromodulations)

    def override_properties(self, hosts):
        for host in hosts:
            # We're only looking for hosts having service overrides defined
            if not hasattr(host, 'service_overrides') or not host.service_overrides:
                continue
            cache = {}
            if isinstance(host.service_overrides, list):
                service_overrides = host.service_overrides
            else:
                service_overrides = [host.service_overrides]
            for ovr in service_overrides:
                # Checks service override syntax
                match = re.match(r'^([^,]+),([^\s]+)\s+(.*)$', ovr)
                if match is None:
                    err = "Error: invalid service override syntax: %s" % ovr
                    host.configuration_errors.append(err)
                    continue
                name, prop, value = match.groups()
                # To speep up search if several properties are overriden on the
                # same service, we keep them in temporary cache
                key = "%s/%s" % (host.host_name, name)
                if key in cache:
                    service = cache[key]
                else:
                    # Looks for corresponding service
                    # As hosts and service are not yet linked, we have to walk
                    # through services to find which is associated to host.
                    service = None
                    for s in self:
                        if not hasattr(s, "host_name") or not hasattr(s, "service_description"):
                            # this is a template
                            continue
                        if s.host_name == host.host_name and s.service_description == name:
                            service = s
                            break
                    if service is None:
                        err = "Error: trying to override property '%s' on service '%s' but it's unknown for this host" % (prop, name)
                        host.configuration_errors.append(err)
                        continue
                    cache[key] = service
                # Checks if override is allowed
                excludes = ['host_name', 'service_description', 'use',
                            'servicegroups', 'trigger', 'trigger_name']
                if prop in excludes:
                    err = "Error: trying to override '%s', a forbidden property for service '%s'" % (prop, name)
                    host.configuration_errors.append(err)
                    continue
                setattr(service, prop, value)

    # We can link services with hosts so
    # We can search in O(hosts) instead
    # of O(services) for common cases
    def optimize_service_search(self, hosts):
        self.hosts = hosts

    # We just search for each host the id of the host
    # and replace the name by the id
    # + inform the host we are a service of him
    def linkify_s_by_hst(self, hosts):
        for s in self:
            # If we do not have an host_name, we set it as
            # a template element to delete. (like Nagios)
            if not hasattr(s, 'host_name'):
                s.host = None
                continue
            try:
                hst_name = s.host_name
                # The new member list, in id
                hst = hosts.find_by_name(hst_name)
                s.host = hst
                # Let the host know we are his service
                if s.host is not None:
                    hst.add_service_link(s)
                else:  # Ok, the host do not exists!
                    err = "Warning: the service '%s' got an invalid host_name '%s'" % (self.get_name(), hst_name)
                    s.configuration_warnings.append(err)
                    continue
            except AttributeError, exp:
                pass  # Will be catch at the is_correct moment

    # We look for servicegroups property in services and
    # link them
    def linkify_s_by_sg(self, servicegroups):
        for s in self:
            if not s.is_tpl():
                new_servicegroups = []
                if hasattr(s, 'servicegroups') and s.servicegroups != '':
                    sgs = s.servicegroups.split(',')
                    for sg_name in sgs:
                        sg_name = sg_name.strip()
                        sg = servicegroups.find_by_name(sg_name)
                        if sg is not None:
                            new_servicegroups.append(sg)
                        else:
                            err = "Error: the servicegroup '%s' of the service '%s' is unknown" % (sg_name, s.get_dbg_name())
                            s.configuration_errors.append(err)
                s.servicegroups = new_servicegroups

    # In the scheduler we need to relink the commandCall with
    # the real commands
    def late_linkify_s_by_commands(self, commands):
        props = ['check_command', 'event_handler']
        for s in self:
            for prop in props:
                cc = getattr(s, prop, None)
                if cc:
                    cc.late_linkify_with_command(commands)

    # Delete services by ids
    def delete_services_by_id(self, ids):
        for id in ids:
            del self[id]

    # Apply implicit inheritance for special properties:
    # contact_groups, notification_interval , notification_period
    # So service will take info from host if necessary
    def apply_implicit_inheritance(self, hosts):
        for prop in ('contacts', 'contact_groups', 'notification_interval',
                      'notification_period', 'resultmodulations', 'business_impact_modulations', 'escalations',
                      'poller_tag', 'reactionner_tag', 'check_period', 'business_impact', 'maintenance_period'):
            for s in self:
                if not s.is_tpl():
                    if not hasattr(s, prop) and hasattr(s, 'host_name'):
                        h = hosts.find_by_name(s.host_name)
                        if h is not None and hasattr(h, prop):
                            setattr(s, prop, getattr(h, prop))

    # Apply inheritance for all properties
    def apply_inheritance(self, hosts):
        # We check for all Host properties if the host has it
        # if not, it check all host templates for a value
        for prop in Service.properties:
            self.apply_partial_inheritance(prop)

        # Then implicit inheritance
        # self.apply_implicit_inheritance(hosts)
        for s in self:
            s.get_customs_properties_by_inheritance(self)

    # Create dependencies for services (daddy ones)
    def apply_dependencies(self):
        for s in self:
            s.fill_daddy_dependency()


    # For services the main clean is about service with bad hosts
    def clean(self):
        to_del = []
        for s in self:
            if not s.host:
                to_del.append(s.id)
        for sid in to_del:
            del self.items[sid]

    # Add in our queue a service create from another. Special case:
    # is a template: so hname is a name of template, so need to get all
    # hosts that inherit from it.
    def copy_create_service_from_another(self, hosts, s, hname):
        for_hosts_to_create = []
        # if we are not a template, it's easy: copy for all host_name
        # because they are our final host_name after all
        if not s.is_tpl():
            for_hosts_to_create.append(hname)
        else:
            # But for template it's more tricky: it's a template name
            # we've got, not a real host_name/ So we must get a list of host_name
            # that use this template
            # Use the complex expression manager for it, it will call find_hosts_that_use_template
            # for the templates it think it's useful
            hosts_from_tpl = self.evaluate_hostgroup_expression(hname.strip(), hosts, hosts.templates, look_in='templates')

            # And now copy our real services
            for n in hosts_from_tpl:
                for_hosts_to_create.append(n)

        if getattr(s, 'duplicate_foreach', '') == '':
            def _loop(name):
                new_s = s.copy()
                new_s.host_name = name
                if s.is_tpl():  # if template, the new one is not
                    new_s.register = 1
                self.items[new_s.id] = new_s
        else:
            def _loop(name):
                # the generator case, we must create several new services
                # we must find our host, and get all key:value we need
                h = hosts.find_by_name(name.strip())

                if h is not None:
                    for new_s in s.duplicate(h):
                        self.items[new_s.id] = new_s
                else:  # TODO: raise an error?
                    err = 'Error: The hostname %s is unknown for the service %s!' % (name, s.get_name())
                    s.configuration_errors.append(err)

        # Now really create the services
        for name in for_hosts_to_create:
            _loop(name)

    # We create new service if necessary (host groups and co)
    def explode(self, hosts, hostgroups, contactgroups,
                servicegroups, servicedependencies, triggers):
        # The "old" services will be removed. All services with
        # more than one host or a host group will be in it
        srv_to_remove = []

        # items::explode_trigger_string_into_triggers
        self.explode_trigger_string_into_triggers(triggers)

        # items::explode_host_groups_into_hosts
        # take all hosts from our hostgroup_name into our host_name property
        self.explode_host_groups_into_hosts(hosts, hostgroups)

        # items::explode_contact_groups_into_contacts
        # take all contacts from our contact_groups into our contact property
        self.explode_contact_groups_into_contacts(contactgroups)

        # Then for every host create a copy of the service with just the host
        # because we are adding services, we can't just loop in it
        service_to_check = self.items.keys()

        for id in service_to_check:
            s = self.items[id]
            duplicate_for_hosts = []  # get the list of our host_names if more than 1
            not_hosts = []  # the list of !host_name so we remove them after

            # If do not have an host_name, just delete it
            if not hasattr(s, 'host_name'):
                srv_to_remove.append(s.id)

            # if not s.is_tpl(): # Exploding template is useless
            # Explode for real service or template with a host_name
            if hasattr(s, 'host_name'):
                hnames = s.host_name.split(',')
                hnames = strip_and_uniq(hnames)
                # We will duplicate if we have multiple host_name
                # or if we are a template (so a clean service)
                if len(hnames) >= 2 or s.is_tpl() \
                        or (hasattr(s, 'duplicate_foreach') and s.duplicate_foreach != ''):
                    for hname in hnames:
                        hname = hname.strip()

                        # If the name begin with a !, we put it in
                        # the not list
                        if hname.startswith('!'):
                            not_hosts.append(hname[1:])
                        else:  # the standard list
                            duplicate_for_hosts.append(hname)

                    # remove duplicate items from duplicate_for_hosts:
                    duplicate_for_hosts = list(set(duplicate_for_hosts))

                    # Ok now we clean the duplicate_for_hosts with all hosts
                    # of the not
                    for hname in not_hosts:
                        if hname in duplicate_for_hosts:
                            duplicate_for_hosts.remove(hname)

                    # Now we duplicate the service for all host_names
                    for hname in duplicate_for_hosts:
                        self.copy_create_service_from_another(hosts, s, hname)

                    # Multiple host_name -> the original service
                    # must be delete. But template are clean else where
                    # and only the the service not got an error in it's conf
                    if not s.is_tpl() and s.configuration_errors == []:
                        srv_to_remove.append(id)

                else:  # Maybe the hnames was full of same host, so we must reset the name
                    for hname in hnames:  # So even if len == 0, we are protected
                        s.host_name = hname

        # We clean all service that was for multiple hosts.
        self.delete_services_by_id(srv_to_remove)

        # Servicegroups property need to be fullfill for got the informations
        # And then just register to this service_group
        for s in self:
            if not s.is_tpl() and hasattr(s, 'service_description'):
                sname = s.service_description
                shname = getattr(s, 'host_name', '')
                if hasattr(s, 'servicegroups'):
                    sgs = s.servicegroups.split(',')
                    for sg in sgs:
                        servicegroups.add_member(shname+','+sname, sg)


        # Now we explode service_dependencies into Servicedependency
        # We just create serviceDep with goods values (as STRING!),
        # the link pass will be done after
        for s in self:
            # Templates are useless here
            if not s.is_tpl():
                if hasattr(s, 'service_dependencies'):
                    if s.service_dependencies != '':
                        sdeps = s.service_dependencies.split(',')
                        # %2=0 are for hosts, !=0 are for service_description
                        i = 0
                        hname = ''
                        for elt in sdeps:
                            if i % 2 == 0:  # host
                                hname = elt.strip()
                            else:  # description
                                desc = elt.strip()
                                # we can register it (s) (depend on) -> (hname, desc)
                                # If we do not have enough data for s, it's no use
                                if hasattr(s, 'service_description') and hasattr(s, 'host_name'):
                                    if hname == '':
                                        hname = s.host_name
                                    servicedependencies.add_service_dependency(s.host_name, s.service_description, hname, desc)
                            i += 1


    # Will create all business tree for the
    # services
    def create_business_rules(self, hosts, services):
        for s in self:
            s.create_business_rules(hosts, services)


    # Will link all business service/host with theirs
    # dep for problem/impact link
    def create_business_rules_dependencies(self):
        for s in self:
            s.create_business_rules_dependencies()
