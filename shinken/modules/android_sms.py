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
"""
This module is an android reactionner module. I will get actions
for send SMS, and will use android lib for this.
"""

# very important: import android stuff
try:
    import android
except ImportError:
    android = None

import sys
import signal
import time
from Queue import Empty

from shinken.basemodule import BaseModule
from shinken.external_command import ExternalCommand
from shinken.log import logger

properties = {
    'daemons': ['reactionner'],
    'type': 'android_sms',
    'external': False,
    # To be a real worker module, you must set this
    'worker_capable': True,
}


# called by the plugin manager to get a worker
def get_instance(mod_conf):
    logger.debug("Get an Android reactionner module for plugin %s" % mod_conf.get_name())
    if not android:
        raise Exception('This is not an Android device.')
    instance = Android_reactionner(mod_conf)
    return instance


# Just print some stuff
class Android_reactionner(BaseModule):

    def __init__(self, mod_conf):
        BaseModule.__init__(self, mod_conf)
        self.i_am_dying = False

    # Called by poller to say 'let's prepare yourself guy'
    def init(self):
        print "Initilisation of the android module"

    # Get new checks if less than nb_checks_max
    # If no new checks got and no check in queue,
    # sleep for 1 sec
    # REF: doc/shinken-action-queues.png (3)
    def get_new_checks(self):
        try:
            while(True):
                #print "I", self.id, "wait for a message"
                msg = self.s.get(block=False)
                if msg is not None:
                    self.checks.append(msg.get_data())
                #print "I", self.id, "I've got a message!"
        except Empty, exp:
            if len(self.checks) == 0:
                time.sleep(1)

    # Launch checks that are in status
    # REF: doc/shinken-action-queues.png (4)
    def launch_new_checks(self):
        for chk in self.checks:
            if chk.status == 'queue':
                print "Launchng SMS for command %s" % chk.command

                elts = chk.command.split(' ')

                # Check the command call first
                if len(elts) < 3:
                    chk.exit_status = 2
                    chk.get_outputs('The android SMS call %s is not valid. should be android_sms PHONENUMBER TEXT', 8012)
                    chk.status = 'done'
                    chk.execution_time = 0.1
                    continue

                # Should be android_sms PHONE TEXT
                phone = elts[1]
                text = ' '.join(elts[2:])

                # Go call the SMS :)
                try:
                    self.android.smsSend(phone, text)
                except Exception, exp:
                    chk.exit_status = 2
                    chk.get_outputs('The android SMS to %s got an error %s' % (phone, exp), 8012)
                    chk.status = 'done'
                    chk.execution_time = 0.1
                    continue

                print "SEND SMS", phone, text
                # And finish the notification
                chk.exit_status = 1
                chk.get_outputs('SMS sent to %s' % phone, 8012)
                chk.status = 'done'
                chk.execution_time = 0.01

    # Check the status of checks
    # if done, return message finished :)
    # REF: doc/shinken-action-queues.png (5)
    def manage_finished_checks(self):
        to_del = []
        for action in self.checks:
            to_del.append(action)
            try:
                # Under android we got a queue here
                self.returns_queue.put(action)
            except IOError, exp:
                print "[%d]Exiting: %s" % (self.id, exp)
                sys.exit(2)
        for chk in to_del:
            self.checks.remove(chk)

    # We will read unread SMS and raise ACK if we read
    # something like 'ack host/service'
    def read_and_parse_sms(self):
        # Get only unread SMS of the inbox
        SMSmsgs = self.android.smsGetMessages(True, 'inbox').result
        to_mark = []
        cmds = []
        for message in SMSmsgs:
            # Read the message
            body = message['body'].encode('utf8', 'ignore')
            to_mark.append(message['_id'])
            print 'Addr', type(message['address'])
            print 'Message', type(body)
            print message
            if body.startswith(('ack', 'Ack', 'ACK')):
                elts = body.split(' ')

                if len(elts) <= 1:
                    print "Bad message length"
                    continue

                # Ok, look for host or host/service
                raw = elts[1]
                if '/' in raw:
                    elts = raw.split('/')
                    # If not service desc, bail out
                    if len(elts) == 1:
                        continue
                    hname = elts[0]
                    sdesc = ' '.join(elts[1:])
                    extcmd = 'ACKNOWLEDGE_SVC_PROBLEM;%s;%s;1;1;1;SMSPhoneAck;None\n' % (hname, sdesc)
                    e = ExternalCommand(extcmd)
                    cmds.append(e)
                else:
                    hname = raw
                    extcmd = 'ACKNOWLEDGE_HOST_PROBLEM;%s;1;1;1;SMSPhoneAck;None\n' % hname
                    e = ExternalCommand(extcmd)
                    cmds.append(e)

        # Mark all read messages as read
        r = self.android.smsMarkMessageRead(to_mark, True)

        print "Raise messages: "
        print cmds
        for cmd in cmds:
            try:
                # Under android we got a queue here
                self.returns_queue.put(cmd)
            except IOError, exp:
                print "[%d]Exiting: %s" % (self.id, exp)
                sys.exit(2)

    # id = id of the worker
    # s = Global Queue Master->Slave
    # m = Queue Slave->Master
    # return_queue = queue managed by manager
    # c = Control Queue for the worker
    def work(self, s, returns_queue, c):
        print "Module Android started!"
        self.set_proctitle(self.name)

        self.android = android.Android()
        timeout = 1.0
        self.checks = []
        self.returns_queue = returns_queue
        self.s = s
        self.t_each_loop = time.time()
        while True:
            begin = time.time()
            msg = None
            cmsg = None

            # If we are diyin (big problem!) we do not
            # take new jobs, we just finished the current one
            if not self.i_am_dying:
                # REF: doc/shinken-action-queues.png (3)
                self.get_new_checks()
                # REF: doc/shinken-action-queues.png (4)
                self.launch_new_checks()
            # REF: doc/shinken-action-queues.png (5)
            self.manage_finished_checks()

            # Got read SMS and raise ACK commands from it
            self.read_and_parse_sms()

            # Now get order from master
            try:
                cmsg = c.get(block=False)
                if cmsg.get_type() == 'Die':
                    print "[%d]Dad say we are diing..." % self.id
                    break
            except:
                pass

            timeout -= time.time() - begin
            if timeout < 0:
                timeout = 1.0
