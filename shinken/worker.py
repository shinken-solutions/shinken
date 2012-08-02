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
from log import logger


class Worker:
    """This class is used for poller and reactionner to work.
    The worker is a process launch by theses process and read Message in a Queue
    (self.s) (slave)
    They launch the Check and then send the result in the Queue self.m (master)
    they can die if they do not do anything (param timeout)

    """

    id = 0  # None
    _process = None
    _mortal = None
    _idletime = None
    _timeout = None
    _c = None

    def __init__(self, id, s, returns_queue, processes_by_worker, mortal=True, timeout=300, max_plugins_output_length=8192, target=None, loaded_into='unknown'):
        self.id = self.__class__.id
        self.__class__.id += 1

        self._mortal = mortal
        self._idletime = 0
        self._timeout = timeout
        self.processes_by_worker = processes_by_worker
        self.input_queue = s
        self._c = Queue()  # Private Control queue for the Worker
        # By default, take our own code
        if target is None:
            target = self.work
        self._process = Process(target=target, args=(s, returns_queue, self._c))
        self.returns_queue = returns_queue
        self.max_plugins_output_length = max_plugins_output_length
        self.i_am_dying = False
        # Keep a trace where the worker is launch from (poller or reactionner?)
        self.loaded_into = loaded_into
        

    def is_mortal(self):
        return self._mortal

    def start(self):
        self._process.start()

    # Kill the background process
    # AND close correctly the queues (input and output)
    # each queue got a thread, so close it too....
    def terminate(self):
        # We can just terminate process, not threads
        if not is_android:
            self._process.terminate()
        # Is we are with a Manager() way
        # there should be not such functions
        if hasattr(self._c, 'close'):
            self._c.close()
            self._c.join_thread()
        if hasattr(self.input_queue, 'close'):
            self.input_queue.close()
            self.input_queue.join_thread()

    def join(self, timeout=None):
        self._process.join(timeout)

    def is_alive(self):
        return self._process.is_alive()

    def is_killable(self):
        return self._mortal and self._idletime > self._timeout

    def add_idletime(self, time):
        self._idletime = self._idletime + time

    def reset_idle(self):
        self._idletime = 0

    def send_message(self, msg):
        self._c.put(msg)

    # A zombie is immortal, so kill not be kill anymore
    def set_zombie(self):
        self._mortal = False

    # Get new checks if less than nb_checks_max
    # If no new checks got and no check in queue,
    # sleep for 1 sec
    # REF: doc/shinken-action-queues.png (3)
    def get_new_checks(self):
        try:
            while(len(self.checks) < self.processes_by_worker):
                #print "I", self.id, "wait for a message"
                msg = self.s.get(block=False)
                if msg is not None:
                    self.checks.append(msg.get_data())
                #print "I", self.id, "I've got a message!"
        except Empty, exp:
            if len(self.checks) == 0:
                self._idletime = self._idletime + 1
                time.sleep(1)
        # Maybe the Queue() is not available, if so, just return
        # get back to work :)
        except IOError, exp:
            return

    # Launch checks that are in status
    # REF: doc/shinken-action-queues.png (4)
    def launch_new_checks(self):
        # queue
        for chk in self.checks:
            if chk.status == 'queue':
                self._idletime = 0
                r = chk.execute()
                # Maybe we got a true big problem in the
                # action lanching
                if r == 'toomanyopenfiles':
                    # We should die as soon as we return all checks
                    self.i_am_dying = True

    # Check the status of checks
    # if done, return message finished :)
    # REF: doc/shinken-action-queues.png (5)
    def manage_finished_checks(self):
        to_del = []
        wait_time = 1
        now = time.time()
        for action in self.checks:
            if action.status == 'launched' and action.last_poll < now - action.wait_time:
                action.check_finished(self.max_plugins_output_length)
                wait_time = min(wait_time, action.wait_time)
                # If action done, we can launch a new one
            if action.status in ('done', 'timeout'):
                to_del.append(action)
                # We answer to the master
                #msg = Message(id=self.id, type='Result', data=action)
                try:
                    self.returns_queue.put(action)

                except IOError, exp:
                    logger.error("[%d] Exiting: %s" % (self.id, exp))
                    sys.exit(2)

        # Little sleep
        self.wait_time = wait_time

        for chk in to_del:
            self.checks.remove(chk)

        # Little sleep
        time.sleep(wait_time)

    # Check if our system time change. If so, change our
    def check_for_system_time_change(self):
        now = time.time()
        difference = now - self.t_each_loop

        # Now set the new value for the tick loop
        self.t_each_loop = now

        # return the diff if it need, of just 0
        if abs(difference) > 900:
            return difference
        else:
            return 0

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

        self.set_proctitle()

        timeout = 1.0
        self.checks = []
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
                # REF: doc/shinken-action-queues.png (3)
                self.get_new_checks()
                # REF: doc/shinken-action-queues.png (4)
                self.launch_new_checks()
            # REF: doc/shinken-action-queues.png (5)
            self.manage_finished_checks()

            # Now get order from master
            try:
                cmsg = c.get(block=False)
                if cmsg.get_type() == 'Die':
                    logger.debug("[%d] Dad say we are dying..." % self.id)
                    break
            except:
                pass

            if self._mortal == True and self._idletime > 2 * self._timeout:
                logger.warning("[%d] Timeout, Harakiri" % self.id)
                # The master must be dead and we are lonely, we must die
                break

            # Look if we are dying, and if we finishe all current checks
            # if so, we really die, our master poller will launch a new
            # worker because we were too weack to manage our job :(
            if len(self.checks) == 0 and self.i_am_dying:
                logger.warning("[%d] I DIE because I cannot do my job as I should (too many open files?)... forgot me please." % self.id)
                break

            # Manage a possible time change (our avant will be change with the diff)
            diff = self.check_for_system_time_change()
            begin += diff

            timeout -= time.time() - begin
            if timeout < 0:
                timeout = 1.0

    def set_proctitle(self):
        try:
            from setproctitle import setproctitle
            setproctitle("shinken-%s worker" % self.loaded_into)
        except:
            pass

