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


# This Class is an example of an Arbiter module
# Here for the configuration phase AND running one

import os
import time
import select

from shinken.basemodule import BaseModule
from shinken.external_command import ExternalCommand

properties = {
    'daemons': ['arbiter', 'receiver', 'poller'],
    'type': 'named_pipe',
    'external': True,
    'worker_capable': False,
    }


# called by the plugin manager to get a broker
def get_instance(plugin):
    print "Get a Named pipe module for plugin %s" % plugin.get_name()

    try:
        path = plugin.command_file
    except AttributeError:
        print "Error: the plugin '%s' do not have a command_file property"
        raise
    instance = Named_Pipe_arbiter(plugin, path)
    return instance


# Just print some stuff
class Named_Pipe_arbiter(BaseModule):
    def __init__(self, modconf, path):
        BaseModule.__init__(self, modconf)
        self.pipe_path = path
        self.fifo = None
        self.cmd_fragments = ''

    def open(self):
        # At the first open del and create the fifo
        if self.fifo is None:
            if os.path.exists(self.pipe_path):
                os.unlink(self.pipe_path)

            if not os.path.exists(self.pipe_path):
                os.umask(0)
                try:
                    if not os.path.exists(os.path.dirname(self.pipe_path)):
                        os.mkdir(os.path.dirname(self.pipe_path))
                    os.mkfifo(self.pipe_path, 0660)
                    open(self.pipe_path, 'w+', os.O_NONBLOCK)
                except OSError, exp:
                    print "Error: pipe creation failed (", self.pipe_path, ')', exp, os.getcwd()
                    return None
        print "[%s] Trying to open the named pipe '%s'" % (self.get_name(), self.pipe_path)
        self.fifo = os.open(self.pipe_path, os.O_NONBLOCK)
        print "[%s] The named pipe '%s' is open" % (self.get_name(), self.pipe_path)
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

    # When you are in "external" mode, that is the main loop of your process
    def main(self):
        self.set_exit_handler()

        self.open()

        input = [self.fifo]

        while not self.interrupted:
            if input == []:
                time.sleep(1)
                continue
            inputready, outputready, exceptready = select.select(input, [], [], 1)
            for s in inputready:
                ext_cmds = self.get()

                if ext_cmds:
                    for ext_cmd in ext_cmds:
                        self.from_q.put(ext_cmd)
                else:
                    self.fifo = self.open()
                    if self.fifo is not None:
                        input = [self.fifo]
                    else:
                        input = []
