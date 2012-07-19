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

# This Class is a plugin for the Shinken Broker. It's job is to write
# host and service perfdata to a file which can be processes by the
# npcd daemon (http://pnp4nagios.org). It is a reimplementation of npcdmod.c

import shutil
import os
import time
import re
import codecs

from shinken.basemodule import BaseModule
from shinken.message import Message

properties = {
    'daemons': ['broker'],
    'type': 'npcdmod',
    'external': True,
    'phases': ['running'],
    }


# called by the plugin manager to get a broker
def get_instance(plugin):
    print "Get a npcd broker for plugin %s" % plugin.get_name()
    config_file = getattr(plugin, 'config_file', None)
    perfdata_spool_dir = getattr(plugin, 'perfdata_spool_dir', None)
    perfdata_file = getattr(plugin, 'perfdata_file', '/usr/local/shinken/var/perfdata')
    perfdata_spool_filename = getattr(plugin, 'perfdata_spool_filename', 'perfdata')
    sleep_time = getattr(plugin, 'sleep_time', 15)

    instance = Npcd_broker(plugin, config_file, perfdata_file, perfdata_spool_dir, perfdata_spool_filename, sleep_time)
    return instance


# Class for the Npcd Broker
# Get broks and put them well-formatted in a spool file
class Npcd_broker(BaseModule):
    def __init__(self, modconf, config_file, perfdata_file, perfdata_spool_dir, perfdata_spool_filename, sleep_time):
        BaseModule.__init__(self, modconf)
        self.config_file = config_file
        self.perfdata_file = perfdata_file
        self.perfdata_spool_dir = perfdata_spool_dir
        self.perfdata_spool_filename = perfdata_spool_filename
        self.sleep_time = sleep_time
        self.process_performance_data = True  # this can be reset and set by program_status_broks
        self.processed_lines = 0
        self.host_commands = {}
        self.service_commands = {}

        if self.config_file and not self.process_config_file():
            print "npcdmod: An error occurred process your config file. Check your perfdata_file or perfdata_spool_dir"
            raise Exception('npcdmod: An error occurred process your config file. Check your perfdata_file or perfdata_spool_dir')
        if not self.perfdata_spool_dir and not self.perfdata_file:
            print "npcdmod: An error occurred while attempting to process module arguments"
            raise Exception('npcdmod: An error occurred while attempting to process module arguments')
        try:
            # We open the file with line buffering, so we can better watch it with tail -f
            self.logfile = codecs.open(self.perfdata_file, 'a', 'utf-8', 'replace', 1)
        except:
            print "could not open file %s" % self.perfdata_file
            raise Exception('could not open file %s" % self.perfdata_file')
        # use so we do nto ask a reinit ofan instance too quickly
        self.last_need_data_send = time.time()

    # Ask for a full reinit of a scheduler because we lost some data.... sorry
    def ask_reinit(self, c_id):
        # Do not ask data too quickly, very dangerous
        # one a minute
        if time.time() - self.last_need_data_send > 60:
            print "I ask the broker for instance id data:", c_id
            msg = Message(id=0, type='NeedData', data={'full_instance_id': c_id}, source=self.get_name())
            self.from_q.put(msg)
            self.last_need_data_send = time.time()
        return

    # Get a brok, parse it, and put in in database
    # We call functions like manage_ TYPEOFBROK _brok that return us queries
    def manage_brok(self, b):
        if self.process_performance_data or b.type in ('program_status', 'update_program_status'):
            BaseModule.manage_brok(self, b)

    # Handle the global process_performance_data setting. If it is not active, this module will not write
    # any lines to the perfdata_file
    def manage_program_status_brok(self, b):
        if self.process_performance_data and not b.data['process_performance_data']:
            self.process_performance_data = False
            print "npcdmod: I can not work with disabled performance data in shinken.cfg."
            print "npcdmod: Please enable it with 'process_performance_data=1' in shinken.cfg"

    def manage_update_program_status_brok(self, b):
        if self.process_performance_data and not b.data['process_performance_data']:
            self.process_performance_data = False
            print "npcdmod: I stop processing performance data"
        elif not self.process_performance_data and b.data['process_performance_data']:
            self.process_performance_data = True
            print "npcdmod: I start processing performance data"

    # also manage initial_broks, because of the check_command (which is not part of check_result_broks)
    # save it in service_commands[host/service]
    def manage_initial_host_status_brok(self, b):
        self.host_commands[b.data['host_name']] = b.data['check_command'].call

    def manage_initial_service_status_brok(self, b):
        if not b.data['host_name'] in self.service_commands:
            self.service_commands[b.data['host_name']] = {}
        self.service_commands[b.data['host_name']][b.data['service_description']] = b.data['check_command'].call

    # A host check has just arrived. Write the performance data to the file
    def manage_host_check_result_brok(self, b):
        # If we don't know about the host or the service, ask for a full init phase!
        if not b.data['host_name'] in self.host_commands:
            self.ask_reinit(b.data['instance_id'])
            return

        line = "DATATYPE::HOSTPERFDATA\tTIMET::%d\tHOSTNAME::%s\tHOSTPERFDATA::%s\tHOSTCHECKCOMMAND::%s\tHOSTSTATE::%d\tHOSTSTATETYPE::%d\n" % (\
            b.data['last_chk'],
            b.data['host_name'],
            b.data['perf_data'],
            self.host_commands[b.data['host_name']],
            b.data['state_id'],
            b.data['state_type_id'])
        self.logfile.write(line)
        self.processed_lines += 1

    # A service check has just arrived. Write the performance data to the file
    def manage_service_check_result_brok(self, b):
        # If we don't know about the host or the service, ask for a full init phase!
        if not b.data['host_name'] in self.service_commands or not b.data['service_description'] in self.service_commands[b.data['host_name']]:
            self.ask_reinit(b.data['instance_id'])
            return

        # check if we really got the host and service data
        line = "DATATYPE::SERVICEPERFDATA\tTIMET::%d\tHOSTNAME::%s\tSERVICEDESC::%s\tSERVICEPERFDATA::%s\tSERVICECHECKCOMMAND::%s\tSERVICESTATE::%d\tSERVICESTATETYPE::%d\n" % (\
            b.data['last_chk'],
            b.data['host_name'],
            b.data['service_description'],
            b.data['perf_data'],
            self.service_commands[b.data['host_name']][b.data['service_description']],
            b.data['state_id'],
            b.data['state_type_id'])
        self.logfile.write(line)
        self.processed_lines += 1

    def process_config_file(self):
        try:
            cfg_file = open(self.config_file)
            for line in cfg_file:
                mo = re.match(r'^(perfdata_spool_dir|perfdata_file|perfdata_spool_filename)\s*=\s*(.*?)\s*$', line)
                if mo:
                    key, value = mo.groups()
                    setattr(self, key, value)
            cfg_file.close()
            return True
        except:
            return False

    def rotate(self):
        target = '%s/%s.%s' % (self.perfdata_spool_dir, self.perfdata_spool_filename, int(time.time()))
        try:
            self.logfile.close()
            if os.path.exists(self.perfdata_file) and os.path.getsize(self.perfdata_file) > 0:
                print "moving perfdata_file %s (%d lines) to %s" % (self.perfdata_file, self.processed_lines, target)
                shutil.move(self.perfdata_file, target)
            self.logfile = codecs.open(self.perfdata_file, 'a', 'utf-8', 'replace', 1)
        except OSError:
            print "could not rotate perfdata_file to %s" % target
            raise
        self.processed_lines = 0

    # Wait for broks and rotate the perfdata_file in intervals of 15 seconds
    # This version does not use a signal-based timer yet. Rotation is triggered
    # by a constant flow of status update broks
    def main(self):
        self.set_exit_handler()
        self.rotate()
        last_rotated = time.time()
        while not self.interrupted:
            l = self.to_q.get()  # can block here :)
            for b in l:
                # unserialize the brok before use it
                b.prepare()
                self.manage_brok(b)
            if time.time() - last_rotated > self.sleep_time:
                self.rotate()
                last_rotated = time.time()
        self.logfile.close()
