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


# This Class is a plugin for the Shinken Arbiter. It read a json file
# with all links between objects. Update them (create/delete) at the
# launch or at fly

import time
import os
import subprocess
from shinken.log import logger
# Try to load the json (2.5 and higher) or
# the simplejson if failed (python2.4)
try:
    import json
except ImportError:
    # For old Python version, load
    # simple json (it can be hard json?! It's 2 functions guy!)
    try:
        import simplejson as json
    except ImportError:
        logger.error("[Hot dependencies] Error: you need the json or simplejson module for this script")
        raise

from shinken.basemodule import BaseModule
from shinken.external_command import ExternalCommand

properties = {
    'daemons': ['arbiter'],
    'type': 'hot_dependencies',
    'external': False,
    'phases': ['late_configuration'],
    }


# called by the plugin manager to get a broker
def get_instance(plugin):
    logger.info("[Hot dependencies] Get a Hot dependencies module for arbiter with plugin %s" % plugin.get_name())
    mapping_file = getattr(plugin, 'mapping_file', '')
    mapping_command = getattr(plugin, 'mapping_command', '')
    mapping_command_interval = int(getattr(plugin, 'mapping_command_interval', '60'))
    mapping_command_timeout = int(getattr(plugin, 'mapping_command_timeout', '300'))
    in_debug = getattr(plugin, 'debug', '0') == '1'
    instance = Hot_dependencies_arbiter(plugin, mapping_file, mapping_command, mapping_command_interval, mapping_command_timeout, in_debug)
    return instance


# Get hosts and/or services dep by launching a command
# or read a flat file as json format that got theses links
class Hot_dependencies_arbiter(BaseModule):
    def __init__(self, modconf, mapping_file, mapping_command, mapping_command_interval, mapping_command_timeout, in_debug=False):
        BaseModule.__init__(self, modconf)
        self.mapping_file = mapping_file
        self.last_update = 0
        self.last_mapping = set()
        self.mapping = set()
        # The external process part
        self.mapping_command = mapping_command
        self.mapping_command_interval = mapping_command_interval
        self.last_cmd_launch = 0
        self.process = None
        self.mapping_command_timeout = mapping_command_timeout
        self.in_debug = in_debug

    # Called by Arbiter to say 'let's prepare yourself guy'
    def init(self):
        logger.info("I open the HOT dependency module")
        # Remember what we add

    def _is_file_existing(self):
        return os.path.exists(self.mapping_file)

    # Look is the mapping filechanged since the last lookup
    def _is_mapping_file_changed(self):
        try:
            last_update = os.path.getmtime(self.mapping_file)
            if last_update > self.last_update:
                self.last_update = last_update
                return True
        except OSError, exp:  # Maybe the file got problem, we bypass here
            logger.error("[Hot dependencies] Error: %s" % str(exp))
        return False

    # Read the mapping file and update our internal mappings
    def _update_mapping(self):
        f = open(self.mapping_file, 'rb')
        mapping = json.loads(f.read())
        f.close()
        self.last_mapping = self.mapping
        # mapping is a list of list, we want a set of tuples
        # because list cannot be hased for a set pass
        self.mapping = set()
        for e in mapping:
            son, father = e
            self.mapping.add((tuple(son), tuple(father)))

    # Maybe the file is updated, but the mapping is the same
    # if not, look at addition and remove objects
    def _got_mapping_changes(self):
        additions = self.mapping - self.last_mapping
        removed = self.last_mapping - self.mapping

        return additions, removed

    # Launch the external command to generate the file
    def _launch_command(self):
        logger.debug("[Hot dependencies] Launching command %s" % self.mapping_command)
        self.last_cmd_launch = int(time.time())

        # windows subprocess do not want us to close fd
        do_close_fd = (not os.name == 'nt')
        try:
            self.process = subprocess.Popen(
                self.mapping_command,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                close_fds=do_close_fd, shell=True)
        except OSError, exp:
            self.error("Fail Launching the command %s: %s" % (self.mapping_command, exp))

    # Look if the command is finished or not
    def _watch_command_finished(self):
        if self.process.poll() is None:
            # Ok, still unfinished, look if in timeout
            now = time.time()
            if (now - self.last_cmd_launch) > self.mapping_command_timeout:
                logger.debug("[Hot dependencies] The external command go in timeout!")
        else:
            logger.info("The external command is done!")
            # it's finished! Cool
            (stdoutdata, stderrdata) = self.process.communicate()
            if self.process.returncode != 0:
                logger.debug("[Hot dependencies] The command return in error: %s \n %s" % (stderrdata, stdoutdata))
            self.process = None

    def tick_external_command(self):
        now = int(time.time())

        # If we got no in progress command, look if we should launch a new one
        if self.process is None:
            if now - self.last_cmd_launch > self.mapping_command_interval:
                if self.mapping_command_interval != 0 and self.mapping_command != '':
                    logger.debug("[Hot dependencies] The command launch is too old, launch a new one")
                    self._launch_command()
#            else:
#                print "The last cmd launch is too early", now - self.last_cmd_launch, self.mapping_command_interval
        else:
            # We got one in progress, we should look if it's finished or not
            self._watch_command_finished()

    # Ok, main function that will load dep from a json file
    def hook_late_configuration(self, arb):
        # We will return external commands to the arbiter, so
        # it can just manage it easily and in a generic way
        ext_cmds = []

        # If the file do not exist, we launch the command
        # and we bail out
        if not self._is_file_existing():
            self._launch_command()
            return

        self._is_mapping_file_changed()
        self._update_mapping()
        additions, removed = self._got_mapping_changes()

        for (father_k, son_k) in additions:
            son_type, son_name = son_k
            father_type, father_name = father_k
            logger.info("[Hot dependencies] Linked son : %s and its father: %s" % (son_name, father_name))
            if son_type == 'host' and father_type == 'host':
                son = arb.conf.hosts.find_by_name(son_name)
                father = arb.conf.hosts.find_by_name(father_name)
                if son is not None and father is not None:
                    logger.debug("[Hot dependencies] Found! %s %s" % (son_name, father_name))
                    if not son.is_linked_with_host(father):
                        logger.debug("[Hot dependencies] Doing simple link between %s and %s" % (son.get_name(), father.get_name()))
                        # Add a dep link between the son and the father
                        son.add_host_act_dependency(father, ['w', 'u', 'd'], None, True)
                else:
                    logger.debug("[Hot dependencies] Missing one of %s %s" % (son_name, father_name))

    def hook_tick(self, arb):
        now = int(time.time())
        self.tick_external_command()
        logger.debug("[Hot dependencies] Tick tick for hot dependency")
        # If the mapping file changed, we reload it and update our links
        # if we need it
        if self._is_mapping_file_changed():
            logger.debug("[Hot dependencies] The mapping file changed, I update it")
            self._update_mapping()
            additions, removed = self._got_mapping_changes()
            logger.debug("[Hot dependencies] Additions: %s" % additions)
            logger.debug("[Hot dependencies] Remove: %s " % removed)
            for father_k, son_k in additions:
                son_type, son_name = son_k
                father_type, father_name = father_k
                logger.debug("[Hot dependencies] Got new add %s %s %s %s" % (son_type, son_name, father_type, father_name))
                son = arb.conf.hosts.find_by_name(son_name.strip())
                father = arb.conf.hosts.find_by_name(father_name.strip())
                # if we cannot find them in the conf, bypass them
                if son is None or father is None:
                    logger.debug("[Hot dependencies] not find dumbass!")
                    continue
                logger.info("[Hot dependencies] Linked son : %s and its father: %s" % (son_name, father_name))
                if son_type == 'host' and father_type == 'host':
                    # We just raise the external command, arbiter will do the job
                    # to dispatch them
                    extcmd = "[%lu] ADD_SIMPLE_HOST_DEPENDENCY;%s;%s\n" % (now, son_name, father_name)
                    e = ExternalCommand(extcmd)

                    logger.debug('[Hot dependencies] Raising external command: %s' % extcmd)
                    arb.add(e)
            # And now the deletion part
            for father_k, son_k in removed:
                son_type, son_name = son_k
                father_type, father_name = father_k
                logger.debug("[Hot dependencies] Got new del %s %s %s %s" % (son_type, son_name, father_type, father_name))
                son = arb.conf.hosts.find_by_name(son_name.strip())
                father = arb.conf.hosts.find_by_name(father_name.strip())
                # if we cannot find them in the conf, bypass them
                if son is None or father is None:
                    logger.debug("[Hot dependencies] not find dumbass!")
                    continue
                logger.info("[Hot dependencies] Linked son : %s and its father: %s" % (son_name, father_name))
                if son_type == 'host' and father_type == 'host':
                    # We just raise the external command, arbiter will do the job
                    # to dispatch them
                    extcmd = "[%lu] DEL_HOST_DEPENDENCY;%s;%s\n" % (now, son_name, father_name)
                    e = ExternalCommand(extcmd)

                    logger.debug('[Hot dependencies] Raising external command %s' % extcmd)
                    arb.add(e)
