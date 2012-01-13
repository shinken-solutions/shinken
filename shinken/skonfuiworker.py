#!/usr/bin/env python
# Copyright (C) 2009-2012 :
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


# This class is used for poller and reactionner to work.
# The worker is a process launch by theses process and read Message in a Queue
# (self.s) (slave)
# They launch the Check and then send the result in the Queue self.m (master)
# they can die if they do not do anything (param timeout)

from Queue import Empty

# In android, we sould use threads, not process
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

import time
import sys
import signal

from shinken.worker import Worker


# SkonfuiWorker class is a sub one for the Worker one of the poller/reactionners
# it just take it's jobs from the mongodb, instead of the queues()
class SkonfUIWorker(Worker):
    id = 0
    _process = None
    _mortal = None
    _idletime = None
    _timeout = None
    _c = None


    def get_new_scan(self):
       print "I ask for a scan"
       time.sleep(1)

    def launch_new_scan(self):
       print "I try to launch scan", self.scan
    

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
        self.scan = None
        self.returns_queue = returns_queue
        self.s = s
        self.t_each_loop = time.time()
        while True:
            begin = time.time()
            msg = None
            cmsg = None
            
            # If we are dying (big problem!) we do not
            # take new jobs, we just finished the current one
            if not self.i_am_dying:
                self.get_new_scan()
                self.launch_new_scan()

            # Now get order from master
            try:
                cmsg = c.get(block=False)
                if cmsg.get_type() == 'Die':
                   print "[%d]Dad say we are dying..." % self.id
                   break
            except :
                pass

            # Manage a possible time change (our avant will be change with the diff)
            diff = self.check_for_system_time_change()
            begin += diff

            timeout -= time.time() - begin
            if timeout < 0:
                timeout = 1.0
