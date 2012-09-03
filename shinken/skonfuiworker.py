#!/usr/bin/env python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
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

from Queue import Empty

# In android, we sgould use threads, not process
is_android = True
try:
    import android
except ImportError:
    is_android = False

if not is_android:
    from multiprocessing import Process, Queue
else:
    from Queue import Queue
    from threading import Thread as Process

# Mongodb lib
try:
    from pymongo.connection import Connection
except ImportError:
    Connection = None

import time
import sys
import signal

from shinken.worker import Worker
from shinken.discovery.discoverymanager import DiscoveryManager

class SkonfUIWorker(Worker):
    """SkonfuiWorker class is a sub one for the Worker one of the poller/reactionners
     it just take it's jobs from the mongodb, instead of the queues()

    """

    id = 0
    _process = None
    _mortal = None
    _idletime = None
    _timeout = None
    _c = None


    def add_database_data(self, server):
        self.database_server = server

    def add_discovery_backend_module(self, discovery_backend_module):
        self.discovery_backend_module = discovery_backend_module


    def connect_database(self):
        con = Connection(self.database_server)
        self.db = con.shinken


    def get_scan_data(self):
        print "Info: I ask for a scan with the id", self.scan_asked
        scan_id = self.scan_asked.get('scan_id')
        # I search the scan entry in the asked_scans table
        cur = self.db.scans.find({'_id': scan_id})
        if cur.count() == 0:
            print "No scan found with id", scan_id
            return
        self.scan = cur[0]


    def launch_scan(self):
        print "Info: I try to launch scan", self.scan
        scan_id = self.scan.get('_id')
        names = self.scan.get('names')
        state = self.scan.get('state')
        runners = self.scan.get('runners')

        print "Info: IN SCAN WORKER:", runners, names, state

        # Updating the scan entry state
        self.db.scans.update({'_id': scan_id}, {'$set': {'state': 'preparing'}})


        elts = names.splitlines()
        targets = ' '.join(elts)
        print "Info: Launching Nmap with targets", targets
        macros = [('NMAPTARGETS', targets)]
        overwrite = False
        output_dir = None
        dbmod = self.discovery_backend_module

        # By default I want only hosts I never see
        # TODO: make this an option
        d = DiscoveryManager(self.discovery_cfg, macros, overwrite, runners, output_dir=output_dir, dbmod=dbmod, only_new_hosts=True)

        # Set the scan as launched state
        self.db.scans.update({'_id': scan_id}, {'$set': {'state': 'launched'}})

        # #Ok, let start the plugins that will give us the data
        d.launch_runners()
        d.wait_for_runners_ends()

        # We get the results, now we can reap the data
        d.get_runners_outputs()

        # and parse them
        d.read_disco_buf()

        # Now look for rules
        d.match_rules()

        # Ok, we know what to create, now do it!
        d.write_config()

        # Set the scan as done :)
        self.db.scans.update({'_id': scan_id}, {'$set': {'state': 'done'}})


    # id = id of the worker
    # s = Global Queue Master->Slave
    # m = Queue Slave->Master
    # return_queue = queue managed by manager
    # c = Control Queue for the worker
    def work(self, s, returns_queue, c):
        ## restore default signal handler for the workers:
        # but on android, we are a thread, so don't do it
        if not is_android:
            signal.signal(signal.SIGTERM, signal.SIG_DFL)
        timeout = 1.0
        self.scan_asked = None
        self.scan = None
        self.returns_queue = returns_queue
        self.s = s
        self.t_each_loop = time.time()

        self.connect_database()

        while True:
            begin = time.time()
            msg = None
            cmsg = None

            # If we are dying (big problem!) we do not
            # take new jobs, we just finished the current one
            if not self.i_am_dying:
                try:
                #print "I", self.id, "wait for a message"
                    msg = self.s.get(block=False)
                    print "Info: I", self.id, "I've got a message!", msg
                    if msg is not None and msg.get_type() == 'ScanAsk':
                        self.scan_asked = msg.get_data()
                        self.get_scan_data()
                        self.launch_scan()
                except Empty, exp:
                    #print "Info: UI worker go to sleep", self.id
                    time.sleep(1)

            # Now get order from master
            try:
                cmsg = c.get(block=False)
                if cmsg.get_type() == 'Die':
                    print "Info: [%d]Dad say we are dying..." % self.id
                    break

            except:
                pass

            # Manage a possible time change (our evant will be change with the diff)
            diff = self.check_for_system_time_change()
            begin += diff

            timeout -= time.time() - begin
            if timeout < 0:
                timeout = 1.0
