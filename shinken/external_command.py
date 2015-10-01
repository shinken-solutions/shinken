#!/usr/bin/env python

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

import os
import time
import re

from shinken.util import to_int, to_bool, split_semicolon
from shinken.downtime import Downtime
from shinken.contactdowntime import ContactDowntime
from shinken.comment import Comment
from shinken.commandcall import CommandCall
from shinken.log import logger, naglog_result
from shinken.objects.pollerlink import PollerLink
from shinken.eventhandler import EventHandler
from shinken.brok import Brok
from shinken.misc.common import DICT_MODATTR


""" TODO: Add some comment about this class for the doc"""
class ExternalCommand:
    my_type = 'externalcommand'

    def __init__(self, cmd_line):
        self.cmd_line = cmd_line


""" TODO: Add some comment about this class for the doc"""
class ExternalCommandManager:

    commands = {
        'CHANGE_CONTACT_MODSATTR':
            {'global': True, 'args': ['contact', None]},
        'CHANGE_CONTACT_MODHATTR':
            {'global': True, 'args': ['contact', None]},
        'CHANGE_CONTACT_MODATTR':
            {'global': True, 'args': ['contact', None]},
        'CHANGE_CONTACT_HOST_NOTIFICATION_TIMEPERIOD':
            {'global': True, 'args': ['contact', 'time_period']},
        'ADD_SVC_COMMENT':
            {'global': False, 'args': ['service', 'to_bool', 'author', None]},
        'ADD_HOST_COMMENT':
            {'global': False, 'args': ['host', 'to_bool', 'author', None]},
        'ACKNOWLEDGE_SVC_PROBLEM':
            {'global': False, 'args': ['service', 'to_int', 'to_bool', 'to_bool', 'author', None]},
        'ACKNOWLEDGE_HOST_PROBLEM':
            {'global': False, 'args': ['host', 'to_int', 'to_bool', 'to_bool', 'author', None]},
        'ACKNOWLEDGE_SVC_PROBLEM_EXPIRE':
            {'global': False, 'args': ['service', 'to_int', 'to_bool',
                                       'to_bool', 'to_int', 'author', None]},
        'ACKNOWLEDGE_HOST_PROBLEM_EXPIRE':
            {'global': False,
             'args': ['host', 'to_int', 'to_bool', 'to_bool', 'to_int', 'author', None]},
        'CHANGE_CONTACT_SVC_NOTIFICATION_TIMEPERIOD':
            {'global': True, 'args': ['contact', 'time_period']},
        'CHANGE_CUSTOM_CONTACT_VAR':
            {'global': True, 'args': ['contact', None, None]},
        'CHANGE_CUSTOM_HOST_VAR':
            {'global': False, 'args': ['host', None, None]},
        'CHANGE_CUSTOM_SVC_VAR':
            {'global': False, 'args': ['service', None, None]},
        'CHANGE_GLOBAL_HOST_EVENT_HANDLER':
            {'global': True, 'args': ['command']},
        'CHANGE_GLOBAL_SVC_EVENT_HANDLER':
            {'global': True, 'args': ['command']},
        'CHANGE_HOST_CHECK_COMMAND':
            {'global': False, 'args': ['host', 'command']},
        'CHANGE_HOST_CHECK_TIMEPERIOD':
            {'global': False, 'args': ['host', 'time_period']},
        'CHANGE_HOST_EVENT_HANDLER':
            {'global': False, 'args': ['host', 'command']},
        'CHANGE_HOST_MODATTR':
            {'global': False, 'args': ['host', 'to_int']},
        'CHANGE_MAX_HOST_CHECK_ATTEMPTS':
            {'global': False, 'args': ['host', 'to_int']},
        'CHANGE_MAX_SVC_CHECK_ATTEMPTS':
            {'global': False, 'args': ['service', 'to_int']},
        'CHANGE_NORMAL_HOST_CHECK_INTERVAL':
            {'global': False, 'args': ['host', 'to_int']},
        'CHANGE_NORMAL_SVC_CHECK_INTERVAL':
            {'global': False, 'args': ['service', 'to_int']},
        'CHANGE_RETRY_HOST_CHECK_INTERVAL':
            {'global': False, 'args': ['host', 'to_int']},
        'CHANGE_RETRY_SVC_CHECK_INTERVAL':
            {'global': False, 'args': ['service', 'to_int']},
        'CHANGE_SVC_CHECK_COMMAND':
            {'global': False, 'args': ['service', 'command']},
        'CHANGE_SVC_CHECK_TIMEPERIOD':
            {'global': False, 'args': ['service', 'time_period']},
        'CHANGE_SVC_EVENT_HANDLER':
            {'global': False, 'args': ['service', 'command']},
        'CHANGE_SVC_MODATTR':
            {'global': False, 'args': ['service', 'to_int']},
        'CHANGE_SVC_NOTIFICATION_TIMEPERIOD':
            {'global': False, 'args': ['service', 'time_period']},
        'DELAY_HOST_NOTIFICATION':
            {'global': False, 'args': ['host', 'to_int']},
        'DELAY_SVC_NOTIFICATION':
            {'global': False, 'args': ['service', 'to_int']},
        'DEL_ALL_HOST_COMMENTS':
            {'global': False, 'args': ['host']},
        'DEL_ALL_HOST_DOWNTIMES':
            {'global': False, 'args': ['host']},
        'DEL_ALL_SVC_COMMENTS':
            {'global': False, 'args': ['service']},
        'DEL_ALL_SVC_DOWNTIMES':
            {'global': False, 'args': ['service']},
        'DEL_CONTACT_DOWNTIME':
            {'global': True, 'args': ['to_int']},
        'DEL_HOST_COMMENT':
            {'global': True, 'args': ['to_int']},
        'DEL_HOST_DOWNTIME':
            {'global': True, 'args': ['to_int']},
        'DEL_SVC_COMMENT':
            {'global': True, 'args': ['to_int']},
        'DEL_SVC_DOWNTIME':
            {'global': True, 'args': ['to_int']},
        'DISABLE_ALL_NOTIFICATIONS_BEYOND_HOST':
            {'global': False, 'args': ['host']},
        'DISABLE_CONTACTGROUP_HOST_NOTIFICATIONS':
            {'global': True, 'args': ['contact_group']},
        'DISABLE_CONTACTGROUP_SVC_NOTIFICATIONS':
            {'global': True, 'args': ['contact_group']},
        'DISABLE_CONTACT_HOST_NOTIFICATIONS':
            {'global': True, 'args': ['contact']},
        'DISABLE_CONTACT_SVC_NOTIFICATIONS':
            {'global': True, 'args': ['contact']},
        'DISABLE_EVENT_HANDLERS':
            {'global': True, 'args': []},
        'DISABLE_FAILURE_PREDICTION':
            {'global': True, 'args': []},
        'DISABLE_FLAP_DETECTION':
            {'global': True, 'args': []},
        'DISABLE_HOSTGROUP_HOST_CHECKS':
            {'global': True, 'args': ['host_group']},
        'DISABLE_HOSTGROUP_HOST_NOTIFICATIONS':
            {'global': True, 'args': ['host_group']},
        'DISABLE_HOSTGROUP_PASSIVE_HOST_CHECKS':
            {'global': True, 'args': ['host_group']},
        'DISABLE_HOSTGROUP_PASSIVE_SVC_CHECKS':
            {'global': True, 'args': ['host_group']},
        'DISABLE_HOSTGROUP_SVC_CHECKS':
            {'global': True, 'args': ['host_group']},
        'DISABLE_HOSTGROUP_SVC_NOTIFICATIONS':
            {'global': True, 'args': ['host_group']},
        'DISABLE_HOST_AND_CHILD_NOTIFICATIONS':
            {'global': False, 'args': ['host']},
        'DISABLE_HOST_CHECK':
            {'global': False, 'args': ['host']},
        'DISABLE_HOST_EVENT_HANDLER':
            {'global': False, 'args': ['host']},
        'DISABLE_HOST_FLAP_DETECTION':
            {'global': False, 'args': ['host']},
        'DISABLE_HOST_FRESHNESS_CHECKS':
            {'global': True, 'args': []},
        'DISABLE_HOST_NOTIFICATIONS':
            {'global': False, 'args': ['host']},
        'DISABLE_HOST_SVC_CHECKS':
            {'global': False, 'args': ['host']},
        'DISABLE_HOST_SVC_NOTIFICATIONS':
            {'global': False, 'args': ['host']},
        'DISABLE_NOTIFICATIONS':
            {'global': True, 'args': []},
        'DISABLE_PASSIVE_HOST_CHECKS':
            {'global': False, 'args': ['host']},
        'DISABLE_PASSIVE_SVC_CHECKS':
            {'global': False, 'args': ['service']},
        'DISABLE_PERFORMANCE_DATA':
            {'global': True, 'args': []},
        'DISABLE_SERVICEGROUP_HOST_CHECKS':
            {'global': True, 'args': ['service_group']},
        'DISABLE_SERVICEGROUP_HOST_NOTIFICATIONS':
            {'global': True, 'args': ['service_group']},
        'DISABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS':
            {'global': True, 'args': ['service_group']},
        'DISABLE_SERVICEGROUP_PASSIVE_SVC_CHECKS':
            {'global': True, 'args': ['service_group']},
        'DISABLE_SERVICEGROUP_SVC_CHECKS':
            {'global': True, 'args': ['service_group']},
        'DISABLE_SERVICEGROUP_SVC_NOTIFICATIONS':
            {'global': True, 'args': ['service_group']},
        'DISABLE_SERVICE_FLAP_DETECTION':
            {'global': False, 'args': ['service']},
        'DISABLE_SERVICE_FRESHNESS_CHECKS':
            {'global': True, 'args': []},
        'DISABLE_SVC_CHECK':
            {'global': False, 'args': ['service']},
        'DISABLE_SVC_EVENT_HANDLER':
            {'global': False, 'args': ['service']},
        'DISABLE_SVC_FLAP_DETECTION':
            {'global': False, 'args': ['service']},
        'DISABLE_SVC_NOTIFICATIONS':
            {'global': False, 'args': ['service']},
        'ENABLE_ALL_NOTIFICATIONS_BEYOND_HOST':
            {'global': False, 'args': ['host']},
        'ENABLE_CONTACTGROUP_HOST_NOTIFICATIONS':
            {'global': True, 'args': ['contact_group']},
        'ENABLE_CONTACTGROUP_SVC_NOTIFICATIONS':
            {'global': True, 'args': ['contact_group']},
        'ENABLE_CONTACT_HOST_NOTIFICATIONS':
            {'global': True, 'args': ['contact']},
        'ENABLE_CONTACT_SVC_NOTIFICATIONS':
            {'global': True, 'args': ['contact']},
        'ENABLE_EVENT_HANDLERS':
            {'global': True, 'args': []},
        'ENABLE_FAILURE_PREDICTION':
            {'global': True, 'args': []},
        'ENABLE_FLAP_DETECTION':
            {'global': True, 'args': []},
        'ENABLE_HOSTGROUP_HOST_CHECKS':
            {'global': True, 'args': ['host_group']},
        'ENABLE_HOSTGROUP_HOST_NOTIFICATIONS':
            {'global': True, 'args': ['host_group']},
        'ENABLE_HOSTGROUP_PASSIVE_HOST_CHECKS':
            {'global': True, 'args': ['host_group']},
        'ENABLE_HOSTGROUP_PASSIVE_SVC_CHECKS':
            {'global': True, 'args': ['host_group']},
        'ENABLE_HOSTGROUP_SVC_CHECKS':
            {'global': True, 'args': ['host_group']},
        'ENABLE_HOSTGROUP_SVC_NOTIFICATIONS':
            {'global': True, 'args': ['host_group']},
        'ENABLE_HOST_AND_CHILD_NOTIFICATIONS':
            {'global': False, 'args': ['host']},
        'ENABLE_HOST_CHECK':
            {'global': False, 'args': ['host']},
        'ENABLE_HOST_EVENT_HANDLER':
            {'global': False, 'args': ['host']},
        'ENABLE_HOST_FLAP_DETECTION':
            {'global': False, 'args': ['host']},
        'ENABLE_HOST_FRESHNESS_CHECKS':
            {'global': True, 'args': []},
        'ENABLE_HOST_NOTIFICATIONS':
            {'global': False, 'args': ['host']},
        'ENABLE_HOST_SVC_CHECKS':
            {'global': False, 'args': ['host']},
        'ENABLE_HOST_SVC_NOTIFICATIONS':
            {'global': False, 'args': ['host']},
        'ENABLE_NOTIFICATIONS':
            {'global': True, 'args': []},
        'ENABLE_PASSIVE_HOST_CHECKS':
            {'global': False, 'args': ['host']},
        'ENABLE_PASSIVE_SVC_CHECKS':
            {'global': False, 'args': ['service']},
        'ENABLE_PERFORMANCE_DATA':
            {'global': True, 'args': []},
        'ENABLE_SERVICEGROUP_HOST_CHECKS':
            {'global': True, 'args': ['service_group']},
        'ENABLE_SERVICEGROUP_HOST_NOTIFICATIONS':
            {'global': True, 'args': ['service_group']},
        'ENABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS':
            {'global': True, 'args': ['service_group']},
        'ENABLE_SERVICEGROUP_PASSIVE_SVC_CHECKS':
            {'global': True, 'args': ['service_group']},
        'ENABLE_SERVICEGROUP_SVC_CHECKS':
            {'global': True, 'args': ['service_group']},
        'ENABLE_SERVICEGROUP_SVC_NOTIFICATIONS':
            {'global': True, 'args': ['service_group']},
        'ENABLE_SERVICE_FRESHNESS_CHECKS':
            {'global': True, 'args': []},
        'ENABLE_SVC_CHECK':
            {'global': False, 'args': ['service']},
        'ENABLE_SVC_EVENT_HANDLER':
            {'global': False, 'args': ['service']},
        'ENABLE_SVC_FLAP_DETECTION':
            {'global': False, 'args': ['service']},
        'ENABLE_SVC_NOTIFICATIONS':
            {'global': False, 'args': ['service']},
        'PROCESS_FILE':
            {'global': True, 'args': [None, 'to_bool']},
        'PROCESS_HOST_CHECK_RESULT':
            {'global': False, 'args': ['host', 'to_int', None]},
        'PROCESS_HOST_OUTPUT':
            {'global': False, 'args': ['host', None]},
        'PROCESS_SERVICE_CHECK_RESULT':
            {'global': False, 'args': ['service', 'to_int', None]},
        'PROCESS_SERVICE_OUTPUT':
            {'global': False, 'args': ['service', None]},
        'READ_STATE_INFORMATION':
            {'global': True, 'args': []},
        'REMOVE_HOST_ACKNOWLEDGEMENT':
            {'global': False, 'args': ['host']},
        'REMOVE_SVC_ACKNOWLEDGEMENT':
            {'global': False, 'args': ['service']},
        'RESTART_PROGRAM':
            {'global': True, 'internal': True, 'args': []},
        'RELOAD_CONFIG':
            {'global': True, 'internal': True, 'args': []},
        'SAVE_STATE_INFORMATION':
            {'global': True, 'args': []},
        'SCHEDULE_AND_PROPAGATE_HOST_DOWNTIME':
            {'global': False, 'args': ['host', 'to_int', 'to_int', 'to_bool',
                                       'to_int', 'to_int', 'author', None]},
        'SCHEDULE_AND_PROPAGATE_TRIGGERED_HOST_DOWNTIME':
            {'global': False, 'args': ['host', 'to_int', 'to_int', 'to_bool',
                                       'to_int', 'to_int', 'author', None]},
        'SCHEDULE_CONTACT_DOWNTIME':
            {'global': True, 'args': ['contact', 'to_int', 'to_int', 'author', None]},
        'SCHEDULE_FORCED_HOST_CHECK':
            {'global': False, 'args': ['host', 'to_int']},
        'SCHEDULE_FORCED_HOST_SVC_CHECKS':
            {'global': False, 'args': ['host', 'to_int']},
        'SCHEDULE_FORCED_SVC_CHECK':
            {'global': False, 'args': ['service', 'to_int']},
        'SCHEDULE_HOSTGROUP_HOST_DOWNTIME':
            {'global': True, 'args': ['host_group', 'to_int', 'to_int',
                                      'to_bool', 'to_int', 'to_int', 'author', None]},
        'SCHEDULE_HOSTGROUP_SVC_DOWNTIME':
            {'global': True, 'args': ['host_group', 'to_int', 'to_int', 'to_bool',
                                      'to_int', 'to_int', 'author', None]},
        'SCHEDULE_HOST_CHECK':
            {'global': False, 'args': ['host', 'to_int']},
        'SCHEDULE_HOST_DOWNTIME':
            {'global': False, 'args': ['host', 'to_int', 'to_int', 'to_bool',
                                       'to_int', 'to_int', 'author', None]},
        'SCHEDULE_HOST_SVC_CHECKS':
            {'global': False, 'args': ['host', 'to_int']},
        'SCHEDULE_HOST_SVC_DOWNTIME':
            {'global': False, 'args': ['host', 'to_int', 'to_int', 'to_bool',
                                       'to_int', 'to_int', 'author', None]},
        'SCHEDULE_SERVICEGROUP_HOST_DOWNTIME':
            {'global': True, 'args': ['service_group', 'to_int', 'to_int', 'to_bool',
                                      'to_int', 'to_int', 'author', None]},
        'SCHEDULE_SERVICEGROUP_SVC_DOWNTIME':
            {'global': True, 'args': ['service_group', 'to_int', 'to_int', 'to_bool',
                                      'to_int', 'to_int', 'author', None]},
        'SCHEDULE_SVC_CHECK':
            {'global': False, 'args': ['service', 'to_int']},
        'SCHEDULE_SVC_DOWNTIME': {'global': False, 'args': ['service', 'to_int', 'to_int',
                                                            'to_bool', 'to_int', 'to_int',
                                                            'author', None]},
        'SEND_CUSTOM_HOST_NOTIFICATION':
            {'global': False, 'args': ['host', 'to_int', 'author', None]},
        'SEND_CUSTOM_SVC_NOTIFICATION':
            {'global': False, 'args': ['service', 'to_int', 'author', None]},
        'SET_HOST_NOTIFICATION_NUMBER':
            {'global': False, 'args': ['host', 'to_int']},
        'SET_SVC_NOTIFICATION_NUMBER':
            {'global': False, 'args': ['service', 'to_int']},
        'SHUTDOWN_PROGRAM':
            {'global': True, 'args': []},
        'START_ACCEPTING_PASSIVE_HOST_CHECKS':
            {'global': True, 'args': []},
        'START_ACCEPTING_PASSIVE_SVC_CHECKS':
            {'global': True, 'args': []},
        'START_EXECUTING_HOST_CHECKS':
            {'global': True, 'args': []},
        'START_EXECUTING_SVC_CHECKS':
            {'global': True, 'args': []},
        'START_OBSESSING_OVER_HOST':
            {'global': False, 'args': ['host']},
        'START_OBSESSING_OVER_HOST_CHECKS':
            {'global': True, 'args': []},
        'START_OBSESSING_OVER_SVC':
            {'global': False, 'args': ['service']},
        'START_OBSESSING_OVER_SVC_CHECKS':
            {'global': True, 'args': []},
        'STOP_ACCEPTING_PASSIVE_HOST_CHECKS':
            {'global': True, 'args': []},
        'STOP_ACCEPTING_PASSIVE_SVC_CHECKS':
            {'global': True, 'args': []},
        'STOP_EXECUTING_HOST_CHECKS':
            {'global': True, 'args': []},
        'STOP_EXECUTING_SVC_CHECKS':
            {'global': True, 'args': []},
        'STOP_OBSESSING_OVER_HOST':
            {'global': False, 'args': ['host']},
        'STOP_OBSESSING_OVER_HOST_CHECKS':
            {'global': True, 'args': []},
        'STOP_OBSESSING_OVER_SVC':
            {'global': False, 'args': ['service']},
        'STOP_OBSESSING_OVER_SVC_CHECKS':
            {'global': True, 'args': []},
        'LAUNCH_SVC_EVENT_HANDLER':
            {'global': False, 'args': ['service']},
        'LAUNCH_HOST_EVENT_HANDLER':
            {'global': False, 'args': ['host']},
        # Now internal calls
        'ADD_SIMPLE_HOST_DEPENDENCY':
            {'global': False, 'args': ['host', 'host']},
        'DEL_HOST_DEPENDENCY':
            {'global': False, 'args': ['host', 'host']},
        'ADD_SIMPLE_POLLER':
            {'global': True, 'internal': True, 'args': [None, None, None, None]},
    }

    def __init__(self, conf, mode):
        self.mode = mode
        if conf:
            self.conf = conf
            self.hosts = conf.hosts
            self.services = conf.services
            self.contacts = conf.contacts
            self.hostgroups = conf.hostgroups
            self.commands = conf.commands
            self.servicegroups = conf.servicegroups
            self.contactgroups = conf.contactgroups
            self.timeperiods = conf.timeperiods
            self.pipe_path = conf.command_file

        self.fifo = None
        self.cmd_fragments = ''
        if self.mode == 'dispatcher':
            self.confs = conf.confs
        # Will change for each command read, so if a command need it,
        # it can get it
        self.current_timestamp = 0

    def load_scheduler(self, scheduler):
        self.sched = scheduler

    def load_arbiter(self, arbiter):
        self.arbiter = arbiter

    def load_receiver(self, receiver):
        self.receiver = receiver


    def open(self):
        # At the first open del and create the fifo
        if self.fifo is None:
            if os.path.exists(self.pipe_path):
                os.unlink(self.pipe_path)

            if not os.path.exists(self.pipe_path):
                os.umask(0)
                try:
                    os.mkfifo(self.pipe_path, 0660)
                    open(self.pipe_path, 'w+', os.O_NONBLOCK)
                except OSError, exp:
                    self.error("Pipe creation failed (%s): %s" % (self.pipe_path, str(exp)))
                    return None
        self.fifo = os.open(self.pipe_path, os.O_NONBLOCK)
        return self.fifo


    def get(self):
        buf = os.read(self.fifo, 8096)
        r = []
        fullbuf = len(buf) == 8096 and True or False
        # If the buffer ended with a fragment last time, prepend it here
        buf = self.cmd_fragments + buf
        buflen = len(buf)
        self.cmd_fragments = ''
        if fullbuf and buf[-1] != '\n':
            # The buffer was full but ends with a command fragment
            r.extend([ExternalCommand(s) for s in (buf.split('\n'))[:-1] if s])
            self.cmd_fragments = (buf.split('\n'))[-1]
        elif buflen:
            # The buffer is either half-filled or full with a '\n' at the end.
            r.extend([ExternalCommand(s) for s in buf.split('\n') if s])
        else:
            # The buffer is empty. We "reset" the fifo here. It will be
            # re-opened in the main loop.
            os.close(self.fifo)
        return r


    def resolve_command(self, excmd):
        # Maybe the command is invalid. Bailout
        try:
            command = excmd.cmd_line
        except AttributeError, exp:
            logger.debug("resolve_command:: error with command %s: %s", excmd, exp)
            return

        # Strip and get utf8 only strings
        command = command.strip()

        # Only log if we are in the Arbiter
        if self.mode == 'dispatcher' and self.conf.log_external_commands:
            # Fix #1263
            # logger.info('EXTERNAL COMMAND: ' + command.rstrip())
            naglog_result('info', 'EXTERNAL COMMAND: ' + command.rstrip())
        r = self.get_command_and_args(command, excmd)

        # If we are a receiver, bail out here
        if self.mode == 'receiver':
            return

        if r is not None:
            is_global = r['global']
            if not is_global:
                c_name = r['c_name']
                args = r['args']
                logger.debug("Got commands %s %s", c_name, str(args))
                f = getattr(self, c_name)
                apply(f, args)
            else:
                command = r['cmd']
                self.dispatch_global_command(command)


    # Ok the command is not for every one, so we search
    # by the hostname which scheduler have the host. Then send
    # the command
    def search_host_and_dispatch(self, host_name, command, extcmd):
        logger.debug("Calling search_host_and_dispatch for %s", host_name)
        host_found = False

        # If we are a receiver, just look in the receiver
        if self.mode == 'receiver':
            logger.info("Receiver looking a scheduler for the external command %s %s",
                        host_name, command)
            sched = self.receiver.get_sched_from_hname(host_name)
            if sched:
                host_found = True
                logger.debug("Receiver found a scheduler: %s", sched)
                logger.info("Receiver pushing external command to scheduler %s", sched)
                sched['external_commands'].append(extcmd)
        else:
            for cfg in self.confs.values():
                if cfg.hosts.find_by_name(host_name) is not None:
                    logger.debug("Host %s found in a configuration", host_name)
                    if cfg.is_assigned:
                        host_found = True
                        sched = cfg.assigned_to
                        logger.debug("Sending command to the scheduler %s", sched.get_name())
                        # sched.run_external_command(command)
                        sched.external_commands.append(command)
                        break
                    else:
                        logger.warning("Problem: a configuration is found, but is not assigned!")
        if not host_found:
            if getattr(self, 'receiver',
                       getattr(self, 'arbiter', None)).accept_passive_unknown_check_results:
                b = self.get_unknown_check_result_brok(command)
                getattr(self, 'receiver', getattr(self, 'arbiter', None)).add(b)
            else:
                logger.warning("Passive check result was received for host '%s', "
                               "but the host could not be found!", host_name)

    # Takes a PROCESS_SERVICE_CHECK_RESULT
    #  external command line and returns an unknown_[type]_check_result brok
    @staticmethod
    def get_unknown_check_result_brok(cmd_line):

        match = re.match(
            '^\[([0-9]{10})] PROCESS_(SERVICE)_CHECK_RESULT;'
            '([^\;]*);([^\;]*);([^\;]*);([^\|]*)(?:\|(.*))?', cmd_line)
        if not match:
            match = re.match(
                '^\[([0-9]{10})] PROCESS_(HOST)_CHECK_RESULT;'
                '([^\;]*);([^\;]*);([^\|]*)(?:\|(.*))?', cmd_line)

        if not match:
            return None

        data = {
            'time_stamp': int(match.group(1)),
            'host_name': match.group(3),
        }

        if match.group(2) == 'SERVICE':
            data['service_description'] = match.group(4)
            data['return_code'] = match.group(5)
            data['output'] = match.group(6)
            data['perf_data'] = match.group(7)
        else:
            data['return_code'] = match.group(4)
            data['output'] = match.group(5)
            data['perf_data'] = match.group(6)

        b = Brok('unknown_%s_check_result' % match.group(2).lower(), data)

        return b

    # The command is global, so sent it to every schedulers
    def dispatch_global_command(self, command):
        for sched in self.conf.schedulers:
            logger.debug("Sending a command '%s' to scheduler %s", command, sched)
            if sched.alive:
                # sched.run_external_command(command)
                sched.external_commands.append(command)


    # We need to get the first part, the command name, and the reference ext command object
    def get_command_and_args(self, command, extcmd=None):
        # safe_print("Trying to resolve", command)
        command = command.rstrip()
        elts = split_semicolon(command)  # danger!!! passive checkresults with perfdata
        part1 = elts[0]

        elts2 = part1.split(' ')
        # print "Elts2:", elts2
        if len(elts2) != 2:
            logger.debug("Malformed command '%s'", command)
            return None
        ts = elts2[0]
        # Now we will get the timestamps as [123456]
        if not ts.startswith('[') or not ts.endswith(']'):
            logger.debug("Malformed command '%s'", command)
            return None
        # Ok we remove the [ ]
        ts = ts[1:-1]
        try:  # is an int or not?
            self.current_timestamp = to_int(ts)
        except ValueError:
            logger.debug("Malformed command '%s'", command)
            return None

        # Now get the command
        c_name = elts2[1]

        # safe_print("Get command name", c_name)
        if c_name not in ExternalCommandManager.commands:
            logger.debug("Command '%s' is not recognized, sorry", c_name)
            return None

        # Split again based on the number of args we expect. We cannot split
        # on every ; because this character may appear in the perfdata of
        # passive check results.
        entry = ExternalCommandManager.commands[c_name]

        # Look if the command is purely internal or not
        internal = False
        if 'internal' in entry and entry['internal']:
            internal = True

        numargs = len(entry['args'])
        if numargs and 'service' in entry['args']:
            numargs += 1
        elts = split_semicolon(command, numargs)

        logger.debug("mode= %s, global= %s", self.mode, str(entry['global']))
        if self.mode == 'dispatcher' and entry['global']:
            if not internal:
                logger.debug("Command '%s' is a global one, we resent it to all schedulers", c_name)
                return {'global': True, 'cmd': command}

        # print "Is global?", c_name, entry['global']
        # print "Mode:", self.mode
        # print "This command have arguments:", entry['args'], len(entry['args'])

        args = []
        i = 1
        in_service = False
        tmp_host = ''
        try:
            for elt in elts[1:]:
                logger.debug("Searching for a new arg: %s (%d)", elt, i)
                val = elt.strip()
                if val.endswith('\n'):
                    val = val[:-1]

                logger.debug("For command arg: %s", val)

                if not in_service:
                    type_searched = entry['args'][i - 1]
                    # safe_print("Search for a arg", type_searched)

                    if type_searched == 'host':
                        if self.mode == 'dispatcher' or self.mode == 'receiver':
                            self.search_host_and_dispatch(val, command, extcmd)
                            return None
                        h = self.hosts.find_by_name(val)
                        if h is not None:
                            args.append(h)
                        elif self.conf.accept_passive_unknown_check_results:
                            b = self.get_unknown_check_result_brok(command)
                            self.sched.add_Brok(b)

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

                    elif type_searched in ('author', None):
                        args.append(val)

                    elif type_searched == 'command':
                        c = self.commands.find_by_name(val)
                        if c is not None:
                            # the find will be redone by
                            # the commandCall creation, but != None
                            # is useful so a bad command will be caught
                            args.append(val)

                    elif type_searched == 'host_group':
                        hg = self.hostgroups.find_by_name(val)
                        if hg is not None:
                            args.append(hg)

                    elif type_searched == 'service_group':
                        sg = self.servicegroups.find_by_name(val)
                        if sg is not None:
                            args.append(sg)

                    elif type_searched == 'contact_group':
                        cg = self.contact_groups.find_by_name(val)
                        if cg is not None:
                            args.append(cg)

                    # special case: service are TWO args host;service, so one more loop
                    # to get the two parts
                    elif type_searched == 'service':
                        in_service = True
                        tmp_host = elt.strip()
                        # safe_print("TMP HOST", tmp_host)
                        if tmp_host[-1] == '\n':
                            tmp_host = tmp_host[:-1]
                        if self.mode == 'dispatcher':
                            self.search_host_and_dispatch(tmp_host, command, extcmd)
                            return None

                    i += 1
                else:
                    in_service = False
                    srv_name = elt
                    if srv_name[-1] == '\n':
                        srv_name = srv_name[:-1]
                    # If we are in a receiver, bailout now.
                    if self.mode == 'receiver':
                        self.search_host_and_dispatch(tmp_host, command, extcmd)
                        return None

                    # safe_print("Got service full", tmp_host, srv_name)
                    s = self.services.find_srv_by_name_and_hostname(tmp_host, srv_name)
                    if s is not None:
                        args.append(s)
                    elif self.conf.accept_passive_unknown_check_results:
                        b = self.get_unknown_check_result_brok(command)
                        self.sched.add_Brok(b)
                    else:
                        logger.warning(
                            "A command was received for service '%s' on host '%s', "
                            "but the service could not be found!", srv_name, tmp_host)

        except IndexError:
            logger.debug("Sorry, the arguments are not corrects")
            return None
        # safe_print('Finally got ARGS:', args)
        if len(args) == len(entry['args']):
            # safe_print("OK, we can call the command", c_name, "with", args)
            return {'global': False, 'c_name': c_name, 'args': args}
            # f = getattr(self, c_name)
            # apply(f, args)
        else:
            logger.debug("Sorry, the arguments are not corrects (%s)", str(args))
            return None

    # CHANGE_CONTACT_MODSATTR;<contact_name>;<value>
    def CHANGE_CONTACT_MODSATTR(self, contact, value):  # TODO
        contact.modified_service_attributes = long(value)

    # CHANGE_CONTACT_MODHATTR;<contact_name>;<value>
    def CHANGE_CONTACT_MODHATTR(self, contact, value):  # TODO
        contact.modified_host_attributes = long(value)

    # CHANGE_CONTACT_MODATTR;<contact_name>;<value>
    def CHANGE_CONTACT_MODATTR(self, contact, value):
        contact.modified_attributes = long(value)

    # CHANGE_CONTACT_HOST_NOTIFICATION_TIMEPERIOD;<contact_name>;<notification_timeperiod>
    def CHANGE_CONTACT_HOST_NOTIFICATION_TIMEPERIOD(self, contact, notification_timeperiod):
        contact.modified_host_attributes |= DICT_MODATTR["MODATTR_NOTIFICATION_TIMEPERIOD"].value
        contact.host_notification_period = notification_timeperiod
        self.sched.get_and_register_status_brok(contact)

    # ADD_SVC_COMMENT;<host_name>;<service_description>;<persistent>;<author>;<comment>
    def ADD_SVC_COMMENT(self, service, persistent, author, comment):
        c = Comment(service, persistent, author, comment, 2, 1, 1, False, 0)
        service.add_comment(c)
        self.sched.add(c)

    # ADD_HOST_COMMENT;<host_name>;<persistent>;<author>;<comment>
    def ADD_HOST_COMMENT(self, host, persistent, author, comment):
        c = Comment(host, persistent, author, comment, 1, 1, 1, False, 0)
        host.add_comment(c)
        self.sched.add(c)

    # ACKNOWLEDGE_SVC_PROBLEM;<host_name>;<service_description>;
    # <sticky>;<notify>;<persistent>;<author>;<comment>
    def ACKNOWLEDGE_SVC_PROBLEM(self, service, sticky, notify, persistent, author, comment):
        service.acknowledge_problem(sticky, notify, persistent, author, comment)

    # ACKNOWLEDGE_HOST_PROBLEM;<host_name>;<sticky>;<notify>;<persistent>;<author>;<comment>
    # TODO: add a better ACK management
    def ACKNOWLEDGE_HOST_PROBLEM(self, host, sticky, notify, persistent, author, comment):
        host.acknowledge_problem(sticky, notify, persistent, author, comment)

    # ACKNOWLEDGE_SVC_PROBLEM_EXPIRE;<host_name>;<service_description>;
    # <sticky>;<notify>;<persistent>;<end_time>;<author>;<comment>
    def ACKNOWLEDGE_SVC_PROBLEM_EXPIRE(self, service, sticky, notify,
                                       persistent, end_time, author, comment):
        service.acknowledge_problem(sticky, notify, persistent, author, comment, end_time=end_time)

    # ACKNOWLEDGE_HOST_PROBLEM_EXPIRE;<host_name>;<sticky>;
    # <notify>;<persistent>;<end_time>;<author>;<comment>
    # TODO: add a better ACK management
    def ACKNOWLEDGE_HOST_PROBLEM_EXPIRE(self, host, sticky, notify,
                                        persistent, end_time, author, comment):
        host.acknowledge_problem(sticky, notify, persistent, author, comment, end_time=end_time)

    # CHANGE_CONTACT_SVC_NOTIFICATION_TIMEPERIOD;<contact_name>;<notification_timeperiod>
    def CHANGE_CONTACT_SVC_NOTIFICATION_TIMEPERIOD(self, contact, notification_timeperiod):
        contact.modified_service_attributes |= \
            DICT_MODATTR["MODATTR_NOTIFICATION_TIMEPERIOD"].value
        contact.service_notification_period = notification_timeperiod
        self.sched.get_and_register_status_brok(contact)

    # CHANGE_CUSTOM_CONTACT_VAR;<contact_name>;<varname>;<varvalue>
    def CHANGE_CUSTOM_CONTACT_VAR(self, contact, varname, varvalue):
        contact.modified_attributes |= DICT_MODATTR["MODATTR_CUSTOM_VARIABLE"].value
        contact.customs[varname.upper()] = varvalue

    # CHANGE_CUSTOM_HOST_VAR;<host_name>;<varname>;<varvalue>
    def CHANGE_CUSTOM_HOST_VAR(self, host, varname, varvalue):
        host.modified_attributes |= DICT_MODATTR["MODATTR_CUSTOM_VARIABLE"].value
        host.customs[varname.upper()] = varvalue

    # CHANGE_CUSTOM_SVC_VAR;<host_name>;<service_description>;<varname>;<varvalue>
    def CHANGE_CUSTOM_SVC_VAR(self, service, varname, varvalue):
        service.modified_attributes |= DICT_MODATTR["MODATTR_CUSTOM_VARIABLE"].value
        service.customs[varname.upper()] = varvalue

    # CHANGE_GLOBAL_HOST_EVENT_HANDLER;<event_handler_command>
    def CHANGE_GLOBAL_HOST_EVENT_HANDLER(self, event_handler_command):
        # TODO: DICT_MODATTR["MODATTR_EVENT_HANDLER_COMMAND"].value
        pass

    # CHANGE_GLOBAL_SVC_EVENT_HANDLER;<event_handler_command> # TODO
    def CHANGE_GLOBAL_SVC_EVENT_HANDLER(self, event_handler_command):
        # TODO: DICT_MODATTR["MODATTR_EVENT_HANDLER_COMMAND"].value
        pass

    # CHANGE_HOST_CHECK_COMMAND;<host_name>;<check_command>
    def CHANGE_HOST_CHECK_COMMAND(self, host, check_command):
        host.modified_attributes |= DICT_MODATTR["MODATTR_CHECK_COMMAND"].value
        host.check_command = CommandCall(self.commands, check_command, poller_tag=host.poller_tag)
        self.sched.get_and_register_status_brok(host)

    # CHANGE_HOST_CHECK_TIMEPERIOD;<host_name>;<timeperiod>
    def CHANGE_HOST_CHECK_TIMEPERIOD(self, host, timeperiod):
        # TODO is timeperiod a string or a Timeperiod object?
        host.modified_attributes |= DICT_MODATTR["MODATTR_CHECK_TIMEPERIOD"].value
        host.check_period = timeperiod
        self.sched.get_and_register_status_brok(host)

    # CHANGE_HOST_EVENT_HANDLER;<host_name>;<event_handler_command>
    def CHANGE_HOST_EVENT_HANDLER(self, host, event_handler_command):
        host.modified_attributes |= DICT_MODATTR["MODATTR_EVENT_HANDLER_COMMAND"].value
        host.event_handler = CommandCall(self.commands, event_handler_command)
        self.sched.get_and_register_status_brok(host)

    # CHANGE_HOST_MODATTR;<host_name>;<value>
    def CHANGE_HOST_MODATTR(self, host, value):
        host.modified_attributes = long(value)

    # CHANGE_MAX_HOST_CHECK_ATTEMPTS;<host_name>;<check_attempts>
    def CHANGE_MAX_HOST_CHECK_ATTEMPTS(self, host, check_attempts):
        host.modified_attributes |= DICT_MODATTR["MODATTR_MAX_CHECK_ATTEMPTS"].value
        host.max_check_attempts = check_attempts
        if host.state_type == 'HARD' and host.state == 'UP' and host.attempt > 1:
            host.attempt = host.max_check_attempts
        self.sched.get_and_register_status_brok(host)

    # CHANGE_MAX_SVC_CHECK_ATTEMPTS;<host_name>;<service_description>;<check_attempts>
    def CHANGE_MAX_SVC_CHECK_ATTEMPTS(self, service, check_attempts):
        service.modified_attributes |= DICT_MODATTR["MODATTR_MAX_CHECK_ATTEMPTS"].value
        service.max_check_attempts = check_attempts
        if service.state_type == 'HARD' and service.state == 'OK' and service.attempt > 1:
            service.attempt = service.max_check_attempts
        self.sched.get_and_register_status_brok(service)

    # CHANGE_NORMAL_HOST_CHECK_INTERVAL;<host_name>;<check_interval>
    def CHANGE_NORMAL_HOST_CHECK_INTERVAL(self, host, check_interval):
        host.modified_attributes |= DICT_MODATTR["MODATTR_NORMAL_CHECK_INTERVAL"].value
        old_interval = host.check_interval
        host.check_interval = check_interval
        # If there were no regular checks (interval=0), then schedule
        # a check immediately.
        if old_interval == 0 and host.checks_enabled:
            host.schedule(force=False, force_time=int(time.time()))
        self.sched.get_and_register_status_brok(host)

    # CHANGE_NORMAL_SVC_CHECK_INTERVAL;<host_name>;<service_description>;<check_interval>
    def CHANGE_NORMAL_SVC_CHECK_INTERVAL(self, service, check_interval):
        service.modified_attributes |= DICT_MODATTR["MODATTR_NORMAL_CHECK_INTERVAL"].value
        old_interval = service.check_interval
        service.check_interval = check_interval
        # If there were no regular checks (interval=0), then schedule
        # a check immediately.
        if old_interval == 0 and service.checks_enabled:
            service.schedule(force=False, force_time=int(time.time()))
        self.sched.get_and_register_status_brok(service)

    # CHANGE_RETRY_HOST_CHECK_INTERVAL;<host_name>;<check_interval>
    def CHANGE_RETRY_HOST_CHECK_INTERVAL(self, host, check_interval):
        host.modified_attributes |= DICT_MODATTR["MODATTR_RETRY_CHECK_INTERVAL"].value
        host.retry_interval = check_interval
        self.sched.get_and_register_status_brok(host)

    # CHANGE_RETRY_SVC_CHECK_INTERVAL;<host_name>;<service_description>;<check_interval>
    def CHANGE_RETRY_SVC_CHECK_INTERVAL(self, service, check_interval):
        service.modified_attributes |= DICT_MODATTR["MODATTR_RETRY_CHECK_INTERVAL"].value
        service.retry_interval = check_interval
        self.sched.get_and_register_status_brok(service)

    # CHANGE_SVC_CHECK_COMMAND;<host_name>;<service_description>;<check_command>
    def CHANGE_SVC_CHECK_COMMAND(self, service, check_command):
        service.modified_attributes |= DICT_MODATTR["MODATTR_CHECK_COMMAND"].value
        service.check_command = CommandCall(self.commands, check_command,
                                            poller_tag=service.poller_tag)
        self.sched.get_and_register_status_brok(service)

    # CHANGE_SVC_CHECK_TIMEPERIOD;<host_name>;<service_description>;<check_timeperiod>
    def CHANGE_SVC_CHECK_TIMEPERIOD(self, service, check_timeperiod):
        service.modified_attributes |= DICT_MODATTR["MODATTR_CHECK_TIMEPERIOD"].value
        service.check_period = check_timeperiod
        self.sched.get_and_register_status_brok(service)

    # CHANGE_SVC_EVENT_HANDLER;<host_name>;<service_description>;<event_handler_command>
    def CHANGE_SVC_EVENT_HANDLER(self, service, event_handler_command):
        service.modified_attributes |= DICT_MODATTR["MODATTR_EVENT_HANDLER_COMMAND"].value
        service.event_handler = CommandCall(self.commands, event_handler_command)
        self.sched.get_and_register_status_brok(service)

    # CHANGE_SVC_MODATTR;<host_name>;<service_description>;<value>
    def CHANGE_SVC_MODATTR(self, service, value):
        # This is not enough.
        # We need to also change each of the needed attributes.
        previous_value = service.modified_attributes
        future_value = long(value)
        changes = future_value ^ previous_value

        for modattr in [
                "MODATTR_NOTIFICATIONS_ENABLED", "MODATTR_ACTIVE_CHECKS_ENABLED",
                "MODATTR_PASSIVE_CHECKS_ENABLED", "MODATTR_EVENT_HANDLER_ENABLED",
                "MODATTR_FLAP_DETECTION_ENABLED", "MODATTR_PERFORMANCE_DATA_ENABLED",
                "MODATTR_OBSESSIVE_HANDLER_ENABLED", "MODATTR_FRESHNESS_CHECKS_ENABLED"]:
            if changes & DICT_MODATTR[modattr].value:
                logger.info("[CHANGE_SVC_MODATTR] Reset %s", modattr)
                setattr(service, DICT_MODATTR[modattr].attribute, not
                        getattr(service, DICT_MODATTR[modattr].attribute))

        # TODO : Handle not boolean attributes.
        # ["MODATTR_EVENT_HANDLER_COMMAND",
        # "MODATTR_CHECK_COMMAND", "MODATTR_NORMAL_CHECK_INTERVAL",
        # "MODATTR_RETRY_CHECK_INTERVAL",
        # "MODATTR_MAX_CHECK_ATTEMPTS", "MODATTR_FRESHNESS_CHECKS_ENABLED",
        # "MODATTR_CHECK_TIMEPERIOD", "MODATTR_CUSTOM_VARIABLE", "MODATTR_NOTIFICATION_TIMEPERIOD"]

        service.modified_attributes = future_value

        # And we need to push the information to the scheduler.
        self.sched.get_and_register_status_brok(service)

    # CHANGE_SVC_NOTIFICATION_TIMEPERIOD;<host_name>;
    # <service_description>;<notification_timeperiod>
    def CHANGE_SVC_NOTIFICATION_TIMEPERIOD(self, service, notification_timeperiod):
        service.modified_attributes |= DICT_MODATTR["MODATTR_NOTIFICATION_TIMEPERIOD"].value
        service.notification_period = notification_timeperiod
        self.sched.get_and_register_status_brok(service)

    # DELAY_HOST_NOTIFICATION;<host_name>;<notification_time>
    def DELAY_HOST_NOTIFICATION(self, host, notification_time):
        host.first_notification_delay = notification_time
        self.sched.get_and_register_status_brok(host)

    # DELAY_SVC_NOTIFICATION;<host_name>;<service_description>;<notification_time>
    def DELAY_SVC_NOTIFICATION(self, service, notification_time):
        service.first_notification_delay = notification_time
        self.sched.get_and_register_status_brok(service)

    # DEL_ALL_HOST_COMMENTS;<host_name>
    def DEL_ALL_HOST_COMMENTS(self, host):
        for c in host.comments:
            self.DEL_HOST_COMMENT(c.id)

    # DEL_ALL_HOST_COMMENTS;<host_name>
    def DEL_ALL_HOST_DOWNTIMES(self, host):
        for dt in host.downtimes:
            self.DEL_HOST_DOWNTIME(dt.id)

    # DEL_ALL_SVC_COMMENTS;<host_name>;<service_description>
    def DEL_ALL_SVC_COMMENTS(self, service):
        for c in service.comments:
            self.DEL_SVC_COMMENT(c.id)

    # DEL_ALL_SVC_COMMENTS;<host_name>;<service_description>
    def DEL_ALL_SVC_DOWNTIMES(self, service):
        for dt in service.downtimes:
            self.DEL_SVC_DOWNTIME(dt.id)

    # DEL_CONTACT_DOWNTIME;<downtime_id>
    def DEL_CONTACT_DOWNTIME(self, downtime_id):
        if downtime_id in self.sched.contact_downtimes:
            self.sched.contact_downtimes[downtime_id].cancel()

    # DEL_HOST_COMMENT;<comment_id>
    def DEL_HOST_COMMENT(self, comment_id):
        if comment_id in self.sched.comments:
            self.sched.comments[comment_id].can_be_deleted = True

    # DEL_HOST_DOWNTIME;<downtime_id>
    def DEL_HOST_DOWNTIME(self, downtime_id):
        if downtime_id in self.sched.downtimes:
            self.sched.downtimes[downtime_id].cancel()

    # DEL_SVC_COMMENT;<comment_id>
    def DEL_SVC_COMMENT(self, comment_id):
        if comment_id in self.sched.comments:
            self.sched.comments[comment_id].can_be_deleted = True

    # DEL_SVC_DOWNTIME;<downtime_id>
    def DEL_SVC_DOWNTIME(self, downtime_id):
        if downtime_id in self.sched.downtimes:
            self.sched.downtimes[downtime_id].cancel()

    # DISABLE_ALL_NOTIFICATIONS_BEYOND_HOST;<host_name>
    def DISABLE_ALL_NOTIFICATIONS_BEYOND_HOST(self, host):
        pass

    # DISABLE_CONTACTGROUP_HOST_NOTIFICATIONS;<contactgroup_name>
    def DISABLE_CONTACTGROUP_HOST_NOTIFICATIONS(self, contactgroup):
        for contact in contactgroup:
            self.DISABLE_CONTACT_HOST_NOTIFICATIONS(contact)

    # DISABLE_CONTACTGROUP_SVC_NOTIFICATIONS;<contactgroup_name>
    def DISABLE_CONTACTGROUP_SVC_NOTIFICATIONS(self, contactgroup):
        for contact in contactgroup:
            self.DISABLE_CONTACT_SVC_NOTIFICATIONS(contact)

    # DISABLE_CONTACT_HOST_NOTIFICATIONS;<contact_name>
    def DISABLE_CONTACT_HOST_NOTIFICATIONS(self, contact):
        if contact.host_notifications_enabled:
            contact.modified_attributes |= DICT_MODATTR["MODATTR_NOTIFICATIONS_ENABLED"].value
            contact.host_notifications_enabled = False
            self.sched.get_and_register_status_brok(contact)

    # DISABLE_CONTACT_SVC_NOTIFICATIONS;<contact_name>
    def DISABLE_CONTACT_SVC_NOTIFICATIONS(self, contact):
        if contact.service_notifications_enabled:
            contact.modified_attributes |= DICT_MODATTR["MODATTR_NOTIFICATIONS_ENABLED"].value
            contact.service_notifications_enabled = False
            self.sched.get_and_register_status_brok(contact)

    # DISABLE_EVENT_HANDLERS
    def DISABLE_EVENT_HANDLERS(self):
        if self.conf.enable_event_handlers:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_EVENT_HANDLER_ENABLED"].value
            self.conf.enable_event_handlers = False
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    # DISABLE_FAILURE_PREDICTION
    def DISABLE_FAILURE_PREDICTION(self):
        if self.conf.enable_failure_prediction:
            self.conf.modified_attributes |= \
                DICT_MODATTR["MODATTR_FAILURE_PREDICTION_ENABLED"].value
            self.conf.enable_failure_prediction = False
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    # DISABLE_FLAP_DETECTION
    def DISABLE_FLAP_DETECTION(self):
        if self.conf.enable_flap_detection:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_FLAP_DETECTION_ENABLED"].value
            self.conf.enable_flap_detection = False
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()
            # Is need, disable flap state for hosts and services
            for service in self.conf.services:
                if service.is_flapping:
                    service.is_flapping = False
                    service.flapping_changes = []
                    self.sched.get_and_register_status_brok(service)
            for host in self.conf.hosts:
                if host.is_flapping:
                    host.is_flapping = False
                    host.flapping_changes = []
                    self.sched.get_and_register_status_brok(host)

    # DISABLE_HOSTGROUP_HOST_CHECKS;<hostgroup_name>
    def DISABLE_HOSTGROUP_HOST_CHECKS(self, hostgroup):
        for host in hostgroup:
            self.DISABLE_HOST_CHECK(host)

    # DISABLE_HOSTGROUP_HOST_NOTIFICATIONS;<hostgroup_name>
    def DISABLE_HOSTGROUP_HOST_NOTIFICATIONS(self, hostgroup):
        for host in hostgroup:
            self.DISABLE_HOST_NOTIFICATIONS(host)

    # DISABLE_HOSTGROUP_PASSIVE_HOST_CHECKS;<hostgroup_name>
    def DISABLE_HOSTGROUP_PASSIVE_HOST_CHECKS(self, hostgroup):
        for host in hostgroup:
            self.DISABLE_PASSIVE_HOST_CHECKS(host)

    # DISABLE_HOSTGROUP_PASSIVE_SVC_CHECKS;<hostgroup_name>
    def DISABLE_HOSTGROUP_PASSIVE_SVC_CHECKS(self, hostgroup):
        for host in hostgroup:
            for service in host.services:
                self.DISABLE_PASSIVE_SVC_CHECKS(service)

    # DISABLE_HOSTGROUP_SVC_CHECKS;<hostgroup_name>
    def DISABLE_HOSTGROUP_SVC_CHECKS(self, hostgroup):
        for host in hostgroup:
            for service in host.services:
                self.DISABLE_SVC_CHECK(service)

    # DISABLE_HOSTGROUP_SVC_NOTIFICATIONS;<hostgroup_name>
    def DISABLE_HOSTGROUP_SVC_NOTIFICATIONS(self, hostgroup):
        for host in hostgroup:
            for service in host.services:
                self.DISABLE_SVC_NOTIFICATIONS(service)

    # DISABLE_HOST_AND_CHILD_NOTIFICATIONS;<host_name>
    def DISABLE_HOST_AND_CHILD_NOTIFICATIONS(self, host):
        pass

    # DISABLE_HOST_CHECK;<host_name>
    def DISABLE_HOST_CHECK(self, host):
        if host.active_checks_enabled:
            host.modified_attributes |= DICT_MODATTR["MODATTR_ACTIVE_CHECKS_ENABLED"].value
            host.disable_active_checks()
            self.sched.get_and_register_status_brok(host)

    # DISABLE_HOST_EVENT_HANDLER;<host_name>
    def DISABLE_HOST_EVENT_HANDLER(self, host):
        if host.event_handler_enabled:
            host.modified_attributes |= DICT_MODATTR["MODATTR_EVENT_HANDLER_ENABLED"].value
            host.event_handler_enabled = False
            self.sched.get_and_register_status_brok(host)

    # DISABLE_HOST_FLAP_DETECTION;<host_name>
    def DISABLE_HOST_FLAP_DETECTION(self, host):
        if host.flap_detection_enabled:
            host.modified_attributes |= DICT_MODATTR["MODATTR_FLAP_DETECTION_ENABLED"].value
            host.flap_detection_enabled = False
            # Maybe the host was flapping, if so, stop flapping
            if host.is_flapping:
                host.is_flapping = False
                host.flapping_changes = []
            self.sched.get_and_register_status_brok(host)

    # DISABLE_HOST_FRESHNESS_CHECKS
    def DISABLE_HOST_FRESHNESS_CHECKS(self):
        if self.conf.check_host_freshness:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_FRESHNESS_CHECKS_ENABLED"].value
            self.conf.check_host_freshness = False
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    # DISABLE_HOST_NOTIFICATIONS;<host_name>
    def DISABLE_HOST_NOTIFICATIONS(self, host):
        if host.notifications_enabled:
            host.modified_attributes |= DICT_MODATTR["MODATTR_NOTIFICATIONS_ENABLED"].value
            host.notifications_enabled = False
            self.sched.get_and_register_status_brok(host)

    # DISABLE_HOST_SVC_CHECKS;<host_name>
    def DISABLE_HOST_SVC_CHECKS(self, host):
        for s in host.services:
            self.DISABLE_SVC_CHECK(s)

    # DISABLE_HOST_SVC_NOTIFICATIONS;<host_name>
    def DISABLE_HOST_SVC_NOTIFICATIONS(self, host):
        for s in host.services:
            self.DISABLE_SVC_NOTIFICATIONS(s)
            self.sched.get_and_register_status_brok(s)

    # DISABLE_NOTIFICATIONS
    def DISABLE_NOTIFICATIONS(self):
        if self.conf.enable_notifications:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_NOTIFICATIONS_ENABLED"].value
            self.conf.enable_notifications = False
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    # DISABLE_PASSIVE_HOST_CHECKS;<host_name>
    def DISABLE_PASSIVE_HOST_CHECKS(self, host):
        if host.passive_checks_enabled:
            host.modified_attributes |= DICT_MODATTR["MODATTR_PASSIVE_CHECKS_ENABLED"].value
            host.passive_checks_enabled = False
            self.sched.get_and_register_status_brok(host)

    # DISABLE_PASSIVE_SVC_CHECKS;<host_name>;<service_description>
    def DISABLE_PASSIVE_SVC_CHECKS(self, service):
        if service.passive_checks_enabled:
            service.modified_attributes |= DICT_MODATTR["MODATTR_PASSIVE_CHECKS_ENABLED"].value
            service.passive_checks_enabled = False
            self.sched.get_and_register_status_brok(service)

    # DISABLE_PERFORMANCE_DATA
    def DISABLE_PERFORMANCE_DATA(self):
        if self.conf.process_performance_data:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_PERFORMANCE_DATA_ENABLED"].value
            self.conf.process_performance_data = False
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    # DISABLE_SERVICEGROUP_HOST_CHECKS;<servicegroup_name>
    def DISABLE_SERVICEGROUP_HOST_CHECKS(self, servicegroup):
        for service in servicegroup:
            self.DISABLE_HOST_CHECK(service.host)

    # DISABLE_SERVICEGROUP_HOST_NOTIFICATIONS;<servicegroup_name>
    def DISABLE_SERVICEGROUP_HOST_NOTIFICATIONS(self, servicegroup):
        for service in servicegroup:
            self.DISABLE_HOST_NOTIFICATIONS(service.host)

    # DISABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS;<servicegroup_name>
    def DISABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS(self, servicegroup):
        for service in servicegroup:
            self.DISABLE_PASSIVE_HOST_CHECKS(service.host)

    # DISABLE_SERVICEGROUP_PASSIVE_SVC_CHECKS;<servicegroup_name>
    def DISABLE_SERVICEGROUP_PASSIVE_SVC_CHECKS(self, servicegroup):
        for service in servicegroup:
            self.DISABLE_PASSIVE_SVC_CHECKS(service)

    # DISABLE_SERVICEGROUP_SVC_CHECKS;<servicegroup_name>
    def DISABLE_SERVICEGROUP_SVC_CHECKS(self, servicegroup):
        for service in servicegroup:
            self.DISABLE_SVC_CHECK(service)

    # DISABLE_SERVICEGROUP_SVC_NOTIFICATIONS;<servicegroup_name>
    def DISABLE_SERVICEGROUP_SVC_NOTIFICATIONS(self, servicegroup):
        for service in servicegroup:
            self.DISABLE_SVC_NOTIFICATIONS(service)

    # DISABLE_SERVICE_FLAP_DETECTION;<host_name>;<service_description>
    def DISABLE_SERVICE_FLAP_DETECTION(self, service):
        if service.flap_detection_enabled:
            service.modified_attributes |= DICT_MODATTR["MODATTR_FLAP_DETECTION_ENABLED"].value
            service.flap_detection_enabled = False
            # Maybe the service was flapping, if so, stop flapping
            if service.is_flapping:
                service.is_flapping = False
                service.flapping_changes = []
            self.sched.get_and_register_status_brok(service)

    # DISABLE_SERVICE_FRESHNESS_CHECKS
    def DISABLE_SERVICE_FRESHNESS_CHECKS(self):
        if self.conf.check_service_freshness:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_FRESHNESS_CHECKS_ENABLED"].value
            self.conf.check_service_freshness = False
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    # DISABLE_SVC_CHECK;<host_name>;<service_description>
    def DISABLE_SVC_CHECK(self, service):
        if service.active_checks_enabled:
            service.disable_active_checks()
            service.modified_attributes |= DICT_MODATTR["MODATTR_ACTIVE_CHECKS_ENABLED"].value
            self.sched.get_and_register_status_brok(service)

    # DISABLE_SVC_EVENT_HANDLER;<host_name>;<service_description>
    def DISABLE_SVC_EVENT_HANDLER(self, service):
        if service.event_handler_enabled:
            service.modified_attributes |= DICT_MODATTR["MODATTR_EVENT_HANDLER_ENABLED"].value
            service.event_handler_enabled = False
            self.sched.get_and_register_status_brok(service)

    # DISABLE_SVC_FLAP_DETECTION;<host_name>;<service_description>
    def DISABLE_SVC_FLAP_DETECTION(self, service):
        self.DISABLE_SERVICE_FLAP_DETECTION(service)

    # DISABLE_SVC_NOTIFICATIONS;<host_name>;<service_description>
    def DISABLE_SVC_NOTIFICATIONS(self, service):
        if service.notifications_enabled:
            service.modified_attributes |= DICT_MODATTR["MODATTR_NOTIFICATIONS_ENABLED"].value
            service.notifications_enabled = False
            self.sched.get_and_register_status_brok(service)

    # ENABLE_ALL_NOTIFICATIONS_BEYOND_HOST;<host_name>
    def ENABLE_ALL_NOTIFICATIONS_BEYOND_HOST(self, host):
        pass

    # ENABLE_CONTACTGROUP_HOST_NOTIFICATIONS;<contactgroup_name>
    def ENABLE_CONTACTGROUP_HOST_NOTIFICATIONS(self, contactgroup):
        for contact in contactgroup:
            self.ENABLE_CONTACT_HOST_NOTIFICATIONS(contact)

    # ENABLE_CONTACTGROUP_SVC_NOTIFICATIONS;<contactgroup_name>
    def ENABLE_CONTACTGROUP_SVC_NOTIFICATIONS(self, contactgroup):
        for contact in contactgroup:
            self.ENABLE_CONTACT_SVC_NOTIFICATIONS(contact)

    # ENABLE_CONTACT_HOST_NOTIFICATIONS;<contact_name>
    def ENABLE_CONTACT_HOST_NOTIFICATIONS(self, contact):
        if not contact.host_notifications_enabled:
            contact.modified_attributes |= DICT_MODATTR["MODATTR_NOTIFICATIONS_ENABLED"].value
            contact.host_notifications_enabled = True
            self.sched.get_and_register_status_brok(contact)

    # ENABLE_CONTACT_SVC_NOTIFICATIONS;<contact_name>
    def ENABLE_CONTACT_SVC_NOTIFICATIONS(self, contact):
        if not contact.service_notifications_enabled:
            contact.modified_attributes |= DICT_MODATTR["MODATTR_NOTIFICATIONS_ENABLED"].value
            contact.service_notifications_enabled = True
            self.sched.get_and_register_status_brok(contact)

    # ENABLE_EVENT_HANDLERS
    def ENABLE_EVENT_HANDLERS(self):
        if not self.conf.enable_event_handlers:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_EVENT_HANDLER_ENABLED"].value
            self.conf.enable_event_handlers = True
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    # ENABLE_FAILURE_PREDICTION
    def ENABLE_FAILURE_PREDICTION(self):
        if not self.conf.enable_failure_prediction:
            self.conf.modified_attributes |= \
                DICT_MODATTR["MODATTR_FAILURE_PREDICTION_ENABLED"].value
            self.conf.enable_failure_prediction = True
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    # ENABLE_FLAP_DETECTION
    def ENABLE_FLAP_DETECTION(self):
        if not self.conf.enable_flap_detection:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_FLAP_DETECTION_ENABLED"].value
            self.conf.enable_flap_detection = True
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    # ENABLE_HOSTGROUP_HOST_CHECKS;<hostgroup_name>
    def ENABLE_HOSTGROUP_HOST_CHECKS(self, hostgroup):
        for host in hostgroup:
            self.ENABLE_HOST_CHECK(host)

    # ENABLE_HOSTGROUP_HOST_NOTIFICATIONS;<hostgroup_name>
    def ENABLE_HOSTGROUP_HOST_NOTIFICATIONS(self, hostgroup):
        for host in hostgroup:
            self.ENABLE_HOST_NOTIFICATIONS(host)

    # ENABLE_HOSTGROUP_PASSIVE_HOST_CHECKS;<hostgroup_name>
    def ENABLE_HOSTGROUP_PASSIVE_HOST_CHECKS(self, hostgroup):
        for host in hostgroup:
            self.ENABLE_PASSIVE_HOST_CHECKS(host)

    # ENABLE_HOSTGROUP_PASSIVE_SVC_CHECKS;<hostgroup_name>
    def ENABLE_HOSTGROUP_PASSIVE_SVC_CHECKS(self, hostgroup):
        for host in hostgroup:
            for service in host.services:
                self.ENABLE_PASSIVE_SVC_CHECKS(service)

    # ENABLE_HOSTGROUP_SVC_CHECKS;<hostgroup_name>
    def ENABLE_HOSTGROUP_SVC_CHECKS(self, hostgroup):
        for host in hostgroup:
            for service in host.services:
                self.ENABLE_SVC_CHECK(service)

    # ENABLE_HOSTGROUP_SVC_NOTIFICATIONS;<hostgroup_name>
    def ENABLE_HOSTGROUP_SVC_NOTIFICATIONS(self, hostgroup):
        for host in hostgroup:
            for service in host.services:
                self.ENABLE_SVC_NOTIFICATIONS(service)

    # ENABLE_HOST_AND_CHILD_NOTIFICATIONS;<host_name>
    def ENABLE_HOST_AND_CHILD_NOTIFICATIONS(self, host):
        pass

    # ENABLE_HOST_CHECK;<host_name>
    def ENABLE_HOST_CHECK(self, host):
        if not host.active_checks_enabled:
            host.active_checks_enabled = True
            host.modified_attributes |= DICT_MODATTR["MODATTR_ACTIVE_CHECKS_ENABLED"].value
            self.sched.get_and_register_status_brok(host)

    # ENABLE_HOST_EVENT_HANDLER;<host_name>
    def ENABLE_HOST_EVENT_HANDLER(self, host):
        if not host.event_handler_enabled:
            host.modified_attributes |= DICT_MODATTR["MODATTR_EVENT_HANDLER_ENABLED"].value
            host.event_handler_enabled = True
            self.sched.get_and_register_status_brok(host)

    # ENABLE_HOST_FLAP_DETECTION;<host_name>
    def ENABLE_HOST_FLAP_DETECTION(self, host):
        if not host.flap_detection_enabled:
            host.modified_attributes |= DICT_MODATTR["MODATTR_FLAP_DETECTION_ENABLED"].value
            host.flap_detection_enabled = True
            self.sched.get_and_register_status_brok(host)

    # ENABLE_HOST_FRESHNESS_CHECKS
    def ENABLE_HOST_FRESHNESS_CHECKS(self):
        if not self.conf.check_host_freshness:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_FRESHNESS_CHECKS_ENABLED"].value
            self.conf.check_host_freshness = True
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    # ENABLE_HOST_NOTIFICATIONS;<host_name>
    def ENABLE_HOST_NOTIFICATIONS(self, host):
        if not host.notifications_enabled:
            host.modified_attributes |= DICT_MODATTR["MODATTR_NOTIFICATIONS_ENABLED"].value
            host.notifications_enabled = True
            self.sched.get_and_register_status_brok(host)

    # ENABLE_HOST_SVC_CHECKS;<host_name>
    def ENABLE_HOST_SVC_CHECKS(self, host):
        for s in host.services:
            self.ENABLE_SVC_CHECK(s)

    # ENABLE_HOST_SVC_NOTIFICATIONS;<host_name>
    def ENABLE_HOST_SVC_NOTIFICATIONS(self, host):
        for s in host.services:
            self.ENABLE_SVC_NOTIFICATIONS(s)
            self.sched.get_and_register_status_brok(s)

    # ENABLE_NOTIFICATIONS
    def ENABLE_NOTIFICATIONS(self):
        if not self.conf.enable_notifications:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_NOTIFICATIONS_ENABLED"].value
            self.conf.enable_notifications = True
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    # ENABLE_PASSIVE_HOST_CHECKS;<host_name>
    def ENABLE_PASSIVE_HOST_CHECKS(self, host):
        if not host.passive_checks_enabled:
            host.modified_attributes |= DICT_MODATTR["MODATTR_PASSIVE_CHECKS_ENABLED"].value
            host.passive_checks_enabled = True
            self.sched.get_and_register_status_brok(host)

    # ENABLE_PASSIVE_SVC_CHECKS;<host_name>;<service_description>
    def ENABLE_PASSIVE_SVC_CHECKS(self, service):
        if not service.passive_checks_enabled:
            service.modified_attributes |= DICT_MODATTR["MODATTR_PASSIVE_CHECKS_ENABLED"].value
            service.passive_checks_enabled = True
            self.sched.get_and_register_status_brok(service)

    # ENABLE_PERFORMANCE_DATA
    def ENABLE_PERFORMANCE_DATA(self):
        if not self.conf.process_performance_data:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_PERFORMANCE_DATA_ENABLED"].value
            self.conf.process_performance_data = True
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    # ENABLE_SERVICEGROUP_HOST_CHECKS;<servicegroup_name>
    def ENABLE_SERVICEGROUP_HOST_CHECKS(self, servicegroup):
        for service in servicegroup:
            self.ENABLE_HOST_CHECK(service.host)

    # ENABLE_SERVICEGROUP_HOST_NOTIFICATIONS;<servicegroup_name>
    def ENABLE_SERVICEGROUP_HOST_NOTIFICATIONS(self, servicegroup):
        for service in servicegroup:
            self.ENABLE_HOST_NOTIFICATIONS(service.host)

    # ENABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS;<servicegroup_name>
    def ENABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS(self, servicegroup):
        for service in servicegroup:
            self.ENABLE_PASSIVE_HOST_CHECKS(service.host)

    # ENABLE_SERVICEGROUP_PASSIVE_SVC_CHECKS;<servicegroup_name>
    def ENABLE_SERVICEGROUP_PASSIVE_SVC_CHECKS(self, servicegroup):
        for service in servicegroup:
            self.ENABLE_PASSIVE_SVC_CHECKS(service)

    # ENABLE_SERVICEGROUP_SVC_CHECKS;<servicegroup_name>
    def ENABLE_SERVICEGROUP_SVC_CHECKS(self, servicegroup):
        for service in servicegroup:
            self.ENABLE_SVC_CHECK(service)

    # ENABLE_SERVICEGROUP_SVC_NOTIFICATIONS;<servicegroup_name>
    def ENABLE_SERVICEGROUP_SVC_NOTIFICATIONS(self, servicegroup):
        for service in servicegroup:
            self.ENABLE_SVC_NOTIFICATIONS(service)

    # ENABLE_SERVICE_FRESHNESS_CHECKS
    def ENABLE_SERVICE_FRESHNESS_CHECKS(self):
        if not self.conf.check_service_freshness:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_FRESHNESS_CHECKS_ENABLED"].value
            self.conf.check_service_freshness = True
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    # ENABLE_SVC_CHECK;<host_name>;<service_description>
    def ENABLE_SVC_CHECK(self, service):
        if not service.active_checks_enabled:
            service.modified_attributes |= DICT_MODATTR["MODATTR_ACTIVE_CHECKS_ENABLED"].value
            service.active_checks_enabled = True
            self.sched.get_and_register_status_brok(service)

    # ENABLE_SVC_EVENT_HANDLER;<host_name>;<service_description>
    def ENABLE_SVC_EVENT_HANDLER(self, service):
        if not service.event_handler_enabled:
            service.modified_attributes |= DICT_MODATTR["MODATTR_EVENT_HANDLER_ENABLED"].value
            service.event_handler_enabled = True
            self.sched.get_and_register_status_brok(service)

    # ENABLE_SVC_FLAP_DETECTION;<host_name>;<service_description>
    def ENABLE_SVC_FLAP_DETECTION(self, service):
        if not service.flap_detection_enabled:
            service.modified_attributes |= DICT_MODATTR["MODATTR_FLAP_DETECTION_ENABLED"].value
            service.flap_detection_enabled = True
            self.sched.get_and_register_status_brok(service)

    # ENABLE_SVC_NOTIFICATIONS;<host_name>;<service_description>
    def ENABLE_SVC_NOTIFICATIONS(self, service):
        if not service.notifications_enabled:
            service.modified_attributes |= DICT_MODATTR["MODATTR_NOTIFICATIONS_ENABLED"].value
            service.notifications_enabled = True
            self.sched.get_and_register_status_brok(service)

    # PROCESS_FILE;<file_name>;<delete>
    def PROCESS_FILE(self, file_name, delete):
        pass

    # TODO: say that check is PASSIVE
    # PROCESS_HOST_CHECK_RESULT;<host_name>;<status_code>;<plugin_output>
    def PROCESS_HOST_CHECK_RESULT(self, host, status_code, plugin_output):
        # raise a PASSIVE check only if needed
        if self.conf.log_passive_checks:
            naglog_result(
                'info', 'PASSIVE HOST CHECK: %s;%d;%s'
                % (host.get_name().decode('utf8', 'ignore'),
                   status_code, plugin_output.decode('utf8', 'ignore'))
            )
        now = time.time()
        cls = host.__class__
        # If globally disable OR locally, do not launch
        if cls.accept_passive_checks and host.passive_checks_enabled:
            # Maybe the check is just too old, if so, bail out!
            if self.current_timestamp < host.last_chk:
                return

            i = host.launch_check(now, force=True)
            c = None
            for chk in host.checks_in_progress:
                if chk.id == i:
                    c = chk
            # Should not be possible to not find the check, but if so, don't crash
            if not c:
                logger.error('Passive host check failed. Cannot find the check id %s', i)
                return
            # Now we 'transform the check into a result'
            # So exit_status, output and status is eaten by the host
            c.exit_status = status_code
            c.get_outputs(plugin_output, host.max_plugins_output_length)
            c.status = 'waitconsume'
            c.check_time = self.current_timestamp  # we are using the external command timestamps
            # Set the corresponding host's check_type to passive=1
            c.set_type_passive()
            self.sched.nb_check_received += 1
            # Ok now this result will be read by scheduler the next loop

    # PROCESS_HOST_OUTPUT;<host_name>;<plugin_output>
    def PROCESS_HOST_OUTPUT(self, host, plugin_output):
        self.PROCESS_HOST_CHECK_RESULT(host, host.state_id, plugin_output)

    # PROCESS_SERVICE_CHECK_RESULT;<host_name>;<service_description>;<return_code>;<plugin_output>
    def PROCESS_SERVICE_CHECK_RESULT(self, service, return_code, plugin_output):
        # raise a PASSIVE check only if needed
        if self.conf.log_passive_checks:
            naglog_result('info', 'PASSIVE SERVICE CHECK: %s;%s;%d;%s'
                          % (service.host.get_name().decode('utf8', 'ignore'),
                             service.get_name().decode('utf8', 'ignore'),
                             return_code, plugin_output.decode('utf8', 'ignore')))
        now = time.time()
        cls = service.__class__
        # If globally disable OR locally, do not launch
        if cls.accept_passive_checks and service.passive_checks_enabled:
            # Maybe the check is just too old, if so, bail out!
            if self.current_timestamp < service.last_chk:
                return

            c = None
            i = service.launch_check(now, force=True)
            for chk in service.checks_in_progress:
                if chk.id == i:
                    c = chk
            # Should not be possible to not find the check, but if so, don't crash
            if not c:
                logger.error('Passive service check failed. Cannot find the check id %s', i)
                return
            # Now we 'transform the check into a result'
            # So exit_status, output and status is eaten by the service
            c.exit_status = return_code
            c.get_outputs(plugin_output, service.max_plugins_output_length)
            c.status = 'waitconsume'
            c.check_time = self.current_timestamp  # we are using the external command timestamps
            # Set the corresponding service's check_type to passive=1
            c.set_type_passive()
            self.sched.nb_check_received += 1
            # Ok now this result will be reap by scheduler the next loop


    # PROCESS_SERVICE_CHECK_RESULT;<host_name>;<service_description>;<plugin_output>
    def PROCESS_SERVICE_OUTPUT(self, service, plugin_output):
        self.PROCESS_SERVICE_CHECK_RESULT(service, service.state_id, plugin_output)

    # READ_STATE_INFORMATION
    def READ_STATE_INFORMATION(self):
        pass

    # REMOVE_HOST_ACKNOWLEDGEMENT;<host_name>
    def REMOVE_HOST_ACKNOWLEDGEMENT(self, host):
        host.unacknowledge_problem()

    # REMOVE_SVC_ACKNOWLEDGEMENT;<host_name>;<service_description>
    def REMOVE_SVC_ACKNOWLEDGEMENT(self, service):
        service.unacknowledge_problem()

    # RESTART_PROGRAM
    def RESTART_PROGRAM(self):
        restart_cmd = self.commands.find_by_name('restart-shinken')
        if not restart_cmd:
            logger.error("Cannot restart Shinken : missing command named"
                         " 'restart-shinken'. Please add one")
            return
        restart_cmd_line = restart_cmd.command_line
        logger.warning("RESTART command : %s", restart_cmd_line)

        # Ok get an event handler command that will run in 15min max
        e = EventHandler(restart_cmd_line, timeout=900)
        # Ok now run it
        e.execute()
        # And wait for the command to finish
        while e.status not in ('done', 'timeout'):
            e.check_finished(64000)
        if e.status == 'timeout' or e.exit_status != 0:
            logger.error("Cannot restart Shinken : the 'restart-shinken' command failed with"
                         " the error code '%d' and the text '%s'.", e.exit_status, e.output)
            return
        # Ok here the command succeed, we can now wait our death
        naglog_result('info', "%s" % (e.output))

    # RELOAD_CONFIG
    def RELOAD_CONFIG(self):
        reload_cmd = self.commands.find_by_name('reload-shinken')
        if not reload_cmd:
            logger.error("Cannot restart Shinken : missing command"
                         " named 'reload-shinken'. Please add one")
            return
        reload_cmd_line = reload_cmd.command_line
        logger.warning("RELOAD command : %s", reload_cmd_line)

        # Ok get an event handler command that will run in 15min max
        e = EventHandler(reload_cmd_line, timeout=900)
        # Ok now run it
        e.execute()
        # And wait for the command to finish
        while e.status not in ('done', 'timeout'):
            e.check_finished(64000)
        if e.status == 'timeout' or e.exit_status != 0:
            logger.error("Cannot reload Shinken configuration: the 'reload-shinken' command failed"
                         " with the error code '%d' and the text '%s'." % (e.exit_status, e.output))
            return
        # Ok here the command succeed, we can now wait our death
        naglog_result('info', "%s" % (e.output))

    # SAVE_STATE_INFORMATION
    def SAVE_STATE_INFORMATION(self):
        pass

    # SCHEDULE_AND_PROPAGATE_HOST_DOWNTIME;<host_name>;<start_time>;<end_time>;
    # <fixed>;<trigger_id>;<duration>;<author>;<comment>
    def SCHEDULE_AND_PROPAGATE_HOST_DOWNTIME(self, host, start_time, end_time,
                                             fixed, trigger_id, duration, author, comment):
        pass

    # SCHEDULE_AND_PROPAGATE_TRIGGERED_HOST_DOWNTIME;<host_name>;<start_time>;<end_time>;<fixed>;
    # <trigger_id>;<duration>;<author>;<comment>
    def SCHEDULE_AND_PROPAGATE_TRIGGERED_HOST_DOWNTIME(self, host, start_time, end_time, fixed,
                                                       trigger_id, duration, author, comment):
        pass

    # SCHEDULE_CONTACT_DOWNTIME;<contact_name>;<start_time>;<end_time>;<author>;<comment>
    def SCHEDULE_CONTACT_DOWNTIME(self, contact, start_time, end_time, author, comment):
        dt = ContactDowntime(contact, start_time, end_time, author, comment)
        contact.add_downtime(dt)
        self.sched.add(dt)
        self.sched.get_and_register_status_brok(contact)

    # SCHEDULE_FORCED_HOST_CHECK;<host_name>;<check_time>
    def SCHEDULE_FORCED_HOST_CHECK(self, host, check_time):
        host.schedule(force=True, force_time=check_time)
        self.sched.get_and_register_status_brok(host)

    # SCHEDULE_FORCED_HOST_SVC_CHECKS;<host_name>;<check_time>
    def SCHEDULE_FORCED_HOST_SVC_CHECKS(self, host, check_time):
        for s in host.services:
            self.SCHEDULE_FORCED_SVC_CHECK(s, check_time)
            self.sched.get_and_register_status_brok(s)

    # SCHEDULE_FORCED_SVC_CHECK;<host_name>;<service_description>;<check_time>
    def SCHEDULE_FORCED_SVC_CHECK(self, service, check_time):
        service.schedule(force=True, force_time=check_time)
        self.sched.get_and_register_status_brok(service)

    # SCHEDULE_HOSTGROUP_HOST_DOWNTIME;<hostgroup_name>;<start_time>;<end_time>;
    # <fixed>;<trigger_id>;<duration>;<author>;<comment>
    def SCHEDULE_HOSTGROUP_HOST_DOWNTIME(self, hostgroup, start_time, end_time, fixed,
                                         trigger_id, duration, author, comment):
        for host in hostgroup:
            self.SCHEDULE_HOST_DOWNTIME(host, start_time, end_time, fixed,
                                        trigger_id, duration, author, comment)

    # SCHEDULE_HOSTGROUP_SVC_DOWNTIME;<hostgroup_name>;<start_time>;<end_time>;<fixed>;
    # <trigger_id>;<duration>;<author>;<comment>
    def SCHEDULE_HOSTGROUP_SVC_DOWNTIME(self, hostgroup, start_time, end_time, fixed,
                                        trigger_id, duration, author, comment):
        for host in hostgroup:
            for s in host.services:
                self.SCHEDULE_SVC_DOWNTIME(s, start_time, end_time, fixed,
                                           trigger_id, duration, author, comment)

    # SCHEDULE_HOST_CHECK;<host_name>;<check_time>
    def SCHEDULE_HOST_CHECK(self, host, check_time):
        host.schedule(force=False, force_time=check_time)
        self.sched.get_and_register_status_brok(host)

    # SCHEDULE_HOST_DOWNTIME;<host_name>;<start_time>;<end_time>;<fixed>;
    # <trigger_id>;<duration>;<author>;<comment>
    def SCHEDULE_HOST_DOWNTIME(self, host, start_time, end_time, fixed,
                               trigger_id, duration, author, comment):
        dt = Downtime(host, start_time, end_time, fixed, trigger_id, duration, author, comment)
        host.add_downtime(dt)
        self.sched.add(dt)
        self.sched.get_and_register_status_brok(host)
        if trigger_id != 0 and trigger_id in self.sched.downtimes:
            self.sched.downtimes[trigger_id].trigger_me(dt)
            
        data = {
            'host_name': host.get_name(),
            'start_time': start_time,
            'end_time': end_time, 
            'fixed': fixed,
            'trigger_id': trigger_id,
            'duration': duration,
            'author': author,
            'comment': comment
        }

        self.sched.add_Brok(Brok('schedule_host_downtime', data))

    # SCHEDULE_HOST_SVC_CHECKS;<host_name>;<check_time>
    def SCHEDULE_HOST_SVC_CHECKS(self, host, check_time):
        for s in host.services:
            self.SCHEDULE_SVC_CHECK(s, check_time)
            self.sched.get_and_register_status_brok(s)

    # SCHEDULE_HOST_SVC_DOWNTIME;<host_name>;<start_time>;<end_time>;
    # <fixed>;<trigger_id>;<duration>;<author>;<comment>
    def SCHEDULE_HOST_SVC_DOWNTIME(self, host, start_time, end_time, fixed,
                                   trigger_id, duration, author, comment):
        for s in host.services:
            self.SCHEDULE_SVC_DOWNTIME(s, start_time, end_time, fixed,
                                       trigger_id, duration, author, comment)

    # SCHEDULE_SERVICEGROUP_HOST_DOWNTIME;<servicegroup_name>;<start_time>;<end_time>;<fixed>;
    # <trigger_id>;<duration>;<author>;<comment>
    def SCHEDULE_SERVICEGROUP_HOST_DOWNTIME(self, servicegroup, start_time, end_time,
                                            fixed, trigger_id, duration, author, comment):
        for h in [s.host for s in servicegroup.get_services()]:
            self.SCHEDULE_HOST_DOWNTIME(h, start_time, end_time, fixed,
                                        trigger_id, duration, author, comment)

    # SCHEDULE_SERVICEGROUP_SVC_DOWNTIME;<servicegroup_name>;<start_time>;<end_time>;
    # <fixed>;<trigger_id>;<duration>;<author>;<comment>
    def SCHEDULE_SERVICEGROUP_SVC_DOWNTIME(self, servicegroup, start_time, end_time,
                                           fixed, trigger_id, duration, author, comment):
        for s in servicegroup.get_services():
            self.SCHEDULE_SVC_DOWNTIME(s, start_time, end_time, fixed,
                                       trigger_id, duration, author, comment)

    # SCHEDULE_SVC_CHECK;<host_name>;<service_description>;<check_time>
    def SCHEDULE_SVC_CHECK(self, service, check_time):
        service.schedule(force=False, force_time=check_time)
        self.sched.get_and_register_status_brok(service)


    # SCHEDULE_SVC_DOWNTIME;<host_name>;<service_description><start_time>;<end_time>;
    # <fixed>;<trigger_id>;<duration>;<author>;<comment>
    def SCHEDULE_SVC_DOWNTIME(self, service, start_time, end_time, fixed,
                              trigger_id, duration, author, comment):
        dt = Downtime(service, start_time, end_time, fixed, trigger_id, duration, author, comment)
        service.add_downtime(dt)
        self.sched.add(dt)
        self.sched.get_and_register_status_brok(service)
        if trigger_id != 0 and trigger_id in self.sched.downtimes:
            self.sched.downtimes[trigger_id].trigger_me(dt)
            
        data = {
            'host_name': service.host_name,
            'service_description': service.service_description,
            'start_time': start_time,
            'end_time': end_time, 
            'fixed': fixed,
            'trigger_id': trigger_id,
            'duration': duration,
            'author': author,
            'comment': comment
        }

        self.sched.add_Brok(Brok('schedule_service_downtime', data))

    # SEND_CUSTOM_HOST_NOTIFICATION;<host_name>;<options>;<author>;<comment>
    def SEND_CUSTOM_HOST_NOTIFICATION(self, host, options, author, comment):
        pass

    # SEND_CUSTOM_SVC_NOTIFICATION;<host_name>;<service_description>;<options>;<author>;<comment>
    def SEND_CUSTOM_SVC_NOTIFICATION(self, service, options, author, comment):
        pass

    # SET_HOST_NOTIFICATION_NUMBER;<host_name>;<notification_number>
    def SET_HOST_NOTIFICATION_NUMBER(self, host, notification_number):
        pass

    # SET_SVC_NOTIFICATION_NUMBER;<host_name>;<service_description>;<notification_number>
    def SET_SVC_NOTIFICATION_NUMBER(self, service, notification_number):
        pass

    # SHUTDOWN_PROGRAM
    def SHUTDOWN_PROGRAM(self):
        pass

    # START_ACCEPTING_PASSIVE_HOST_CHECKS
    def START_ACCEPTING_PASSIVE_HOST_CHECKS(self):
        if not self.conf.accept_passive_host_checks:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_PASSIVE_CHECKS_ENABLED"].value
            self.conf.accept_passive_host_checks = True
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    # START_ACCEPTING_PASSIVE_SVC_CHECKS
    def START_ACCEPTING_PASSIVE_SVC_CHECKS(self):
        if not self.conf.accept_passive_service_checks:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_PASSIVE_CHECKS_ENABLED"].value
            self.conf.accept_passive_service_checks = True
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    # START_EXECUTING_HOST_CHECKS
    def START_EXECUTING_HOST_CHECKS(self):
        if not self.conf.execute_host_checks:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_ACTIVE_CHECKS_ENABLED"].value
            self.conf.execute_host_checks = True
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    # START_EXECUTING_SVC_CHECKS
    def START_EXECUTING_SVC_CHECKS(self):
        if not self.conf.execute_service_checks:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_ACTIVE_CHECKS_ENABLED"].value
            self.conf.execute_service_checks = True
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    # START_OBSESSING_OVER_HOST;<host_name>
    def START_OBSESSING_OVER_HOST(self, host):
        if not host.obsess_over_host:
            host.modified_attributes |= DICT_MODATTR["MODATTR_OBSESSIVE_HANDLER_ENABLED"].value
            host.obsess_over_host = True
            self.sched.get_and_register_status_brok(host)

    # START_OBSESSING_OVER_HOST_CHECKS
    def START_OBSESSING_OVER_HOST_CHECKS(self):
        if not self.conf.obsess_over_hosts:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_OBSESSIVE_HANDLER_ENABLED"].value
            self.conf.obsess_over_hosts = True
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    # START_OBSESSING_OVER_SVC;<host_name>;<service_description>
    def START_OBSESSING_OVER_SVC(self, service):
        if not service.obsess_over_service:
            service.modified_attributes |= DICT_MODATTR["MODATTR_OBSESSIVE_HANDLER_ENABLED"].value
            service.obsess_over_service = True
            self.sched.get_and_register_status_brok(service)

    # START_OBSESSING_OVER_SVC_CHECKS
    def START_OBSESSING_OVER_SVC_CHECKS(self):
        if not self.conf.obsess_over_services:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_OBSESSIVE_HANDLER_ENABLED"].value
            self.conf.obsess_over_services = True
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    # STOP_ACCEPTING_PASSIVE_HOST_CHECKS
    def STOP_ACCEPTING_PASSIVE_HOST_CHECKS(self):
        if self.conf.accept_passive_host_checks:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_PASSIVE_CHECKS_ENABLED"].value
            self.conf.accept_passive_host_checks = False
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    # STOP_ACCEPTING_PASSIVE_SVC_CHECKS
    def STOP_ACCEPTING_PASSIVE_SVC_CHECKS(self):
        if self.conf.accept_passive_service_checks:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_PASSIVE_CHECKS_ENABLED"].value
            self.conf.accept_passive_service_checks = False
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    # STOP_EXECUTING_HOST_CHECKS
    def STOP_EXECUTING_HOST_CHECKS(self):
        if self.conf.execute_host_checks:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_ACTIVE_CHECKS_ENABLED"].value
            self.conf.execute_host_checks = False
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    # STOP_EXECUTING_SVC_CHECKS
    def STOP_EXECUTING_SVC_CHECKS(self):
        if self.conf.execute_service_checks:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_ACTIVE_CHECKS_ENABLED"].value
            self.conf.execute_service_checks = False
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    # STOP_OBSESSING_OVER_HOST;<host_name>
    def STOP_OBSESSING_OVER_HOST(self, host):
        if host.obsess_over_host:
            host.modified_attributes |= DICT_MODATTR["MODATTR_OBSESSIVE_HANDLER_ENABLED"].value
            host.obsess_over_host = False
            self.sched.get_and_register_status_brok(host)

    # STOP_OBSESSING_OVER_HOST_CHECKS
    def STOP_OBSESSING_OVER_HOST_CHECKS(self):
        if self.conf.obsess_over_hosts:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_OBSESSIVE_HANDLER_ENABLED"].value
            self.conf.obsess_over_hosts = False
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    # STOP_OBSESSING_OVER_SVC;<host_name>;<service_description>
    def STOP_OBSESSING_OVER_SVC(self, service):
        if service.obsess_over_service:
            service.modified_attributes |= DICT_MODATTR["MODATTR_OBSESSIVE_HANDLER_ENABLED"].value
            service.obsess_over_service = False
            self.sched.get_and_register_status_brok(service)

    # STOP_OBSESSING_OVER_SVC_CHECKS
    def STOP_OBSESSING_OVER_SVC_CHECKS(self):
        if self.conf.obsess_over_services:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_OBSESSIVE_HANDLER_ENABLED"].value
            self.conf.obsess_over_services = False
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    # Now the shinken specific ones
    # LAUNCH_SVC_EVENT_HANDLER;<host_name>;<service_description>
    def LAUNCH_SVC_EVENT_HANDLER(self, service):
        service.get_event_handlers(externalcmd=True)

    # LAUNCH_SVC_EVENT_HANDLER;<host_name>;<service_description>
    def LAUNCH_HOST_EVENT_HANDLER(self, host):
        host.get_event_handlers(externalcmd=True)

    # ADD_SIMPLE_HOST_DEPENDENCY;<host_name>;<host_name>
    def ADD_SIMPLE_HOST_DEPENDENCY(self, son, father):
        if not son.is_linked_with_host(father):
            logger.debug("Doing simple link between %s and %s", son.get_name(), father.get_name())
            # Flag them so the modules will know that a topology change
            # happened
            son.topology_change = True
            father.topology_change = True
            # Now do the work
            # Add a dep link between the son and the father
            son.add_host_act_dependency(father, ['w', 'u', 'd'], None, True)
            self.sched.get_and_register_status_brok(son)
            self.sched.get_and_register_status_brok(father)

    # DEL_SIMPLE_HOST_DEPENDENCY;<host_name>;<host_name>
    def DEL_HOST_DEPENDENCY(self, son, father):
        if son.is_linked_with_host(father):
            logger.debug("Removing simple link between %s and %s",
                         son.get_name(), father.get_name())
            # Flag them so the modules will know that a topology change
            # happened
            son.topology_change = True
            father.topology_change = True
            # Now do the work
            son.del_host_act_dependency(father)
            self.sched.get_and_register_status_brok(son)
            self.sched.get_and_register_status_brok(father)

    # ADD_SIMPLE_POLLER;realm_name;poller_name;address;port
    def ADD_SIMPLE_POLLER(self, realm_name, poller_name, address, port):
        logger.debug("I need to add the poller (%s, %s, %s, %s)",
                     realm_name, poller_name, address, port)

        # First we look for the realm
        r = self.conf.realms.find_by_name(realm_name)
        if r is None:
            logger.debug("Sorry, the realm %s is unknown", realm_name)
            return

        logger.debug("We found the realm: %s", str(r))
        # TODO: backport this in the config class?
        # We create the PollerLink object
        t = {'poller_name': poller_name, 'address': address, 'port': port}
        p = PollerLink(t)
        p.fill_default()
        p.prepare_for_conf()
        parameters = {'max_plugins_output_length': self.conf.max_plugins_output_length}
        p.add_global_conf_parameters(parameters)
        self.arbiter.conf.pollers[p.id] = p
        self.arbiter.dispatcher.elements.append(p)
        self.arbiter.dispatcher.satellites.append(p)
        r.pollers.append(p)
        r.count_pollers()
        r.fill_potential_satellites_by_type('pollers')
        logger.debug("Poller %s added", poller_name)
        logger.debug("Potential %s", str(r.get_potential_satellites_by_type('poller')))


if __name__ == '__main__':

    FIFO_PATH = '/tmp/my_fifo'

    if os.path.exists(FIFO_PATH):
        os.unlink(FIFO_PATH)

    if not os.path.exists(FIFO_PATH):
        os.umask(0)
        os.mkfifo(FIFO_PATH, 0660)
        my_fifo = open(FIFO_PATH, 'w+')
        logger.debug("my_fifo: %s", my_fifo)

    logger.debug(open(FIFO_PATH, 'r').readline())
