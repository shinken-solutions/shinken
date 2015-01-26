# -*- coding: utf-8 -*-

from __future__ import division


import os
import random
from random import randint
import socket
import threading
import time

from shinken.objects.module import Module
from shinken.external_command import ExternalCommand

from shinken_test import time_hacker, unittest, ShinkenTest
from test_livestatus import LiveStatus_Template


from shinken.modules.livestatus_broker.livestatus_wait_query import LiveStatusWaitQuery
from shinken.modules.livestatus_broker.livestatus_query import LiveStatusQuery



class Test_WaitQuery(LiveStatus_Template):

    _setup_config_file = 'etc/nagios_1r_1h_1s.cfg'

    def test_wait_query(self):
        request = b'''GET hosts
WaitObject: gstarck_test
WaitCondition: last_check >= 1419007690
WaitTimeout: 10000
WaitTrigger: check
Columns: last_check state plugin_output
Filter: host_name = gstarck_test
Localtime: 1419007690
OutputFormat: python
KeepAlive: on
ResponseHeader: fixed16
ColumnHeaders: off

'''

        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        self.assertEqual(2, len(response), 'should contains Wait + Query')
        self.assertIsInstance(response[0], LiveStatusWaitQuery)
        self.assertIsInstance(response[1], LiveStatusQuery)



class TestFull_WaitQuery(LiveStatus_Template):
    ''' "Full" test : that is with connection to livestatus socket
    And so we have to start a thread to execute the actual main livestatus function (manage_lql_thread),
    which will handle new connections as it would do in real life.
    '''

    _setup_config_file = 'etc/nagios_1r_1h_1s.cfg'

    def setUp(self):
        super(TestFull_WaitQuery, self).setUp()
        # otherwise this can make test_wait_query_1() to fail from time to time
        # (on data = self.livestatus_broker.from_q.get(block=False)),
        # because the queue (from_q) isn't yet filled while it should be if we had
        # not hacked on time module..
        time_hacker.set_real_time()

    def tearDown(self):
        # stop thread
        self.livestatus_broker.interrupted = True
        self.lql_thread.join()
        super(TestFull_WaitQuery, self).tearDown()

    def init_livestatus(self, modconf=None, dbmodconf=None):
        super(TestFull_WaitQuery, self).init_livestatus(modconf=modconf, dbmodconf=dbmodconf)
        self.sched.brokers['Default-Broker'] = {'broks' : {}, 'has_full_broks' : False}
        self.sched.fill_initial_broks('Default-Broker')
        self.update_broker()
        # execute the livestatus by starting a dedicated thread to run the manage_lql_thread function:
        self.lql_thread = threading.Thread(target=self.livestatus_broker.manage_lql_thread, name='lqlthread')
        self.lql_thread.start()
        time_hacker.set_real_time()
        t0 = time.time()
        # give some time for the thread to init and creates its listener socket(s) :
        while True:
            if self.livestatus_broker.listeners:
                break # but as soon as listeners is truth(== non-empty), we can continue,
                # the listening thread has created the input socket so we can connect to it.
            elif time.time() - t0 > 10:
                self.livestatus_broker.interrupted = True
                raise RuntimeError('Livestatus listening thread should have created its input socket(s) quite quickly !!')
            time.sleep(0.5)
        time_hacker.set_my_time()

    def query_livestatus(self, data, ip=None, port=None, timeout=60):
        if ip is None:
            ip = self.modconf.host
        if port is None:
            port = self.modconf.port
        port = int(port)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.settimeout(timeout)
            s.connect((ip, port))
            s.send(data)
            s.shutdown(socket.SHUT_WR)
            ret = []
            while True:
                data = s.recv(1024)
                #print("received: %r" % data)
                if not data:
                    return b''.join(ret)
                ret.append(data)
        finally:
            s.close()


    def test_wait_query_1(self):

        ## NB NB NB:
        # if there was a scheduler and a poller running and connected to `self.livestatus_broker.from_q´
        # then the prepended command would be processed and the livestatus **could** return a different response,
        # **depending** on :
        # the wait_timeout_sec we use (which then should be greater than the randint(1,3) actually used)
        # and on how fast the command would be processed by the poller
        # and on how fast the host status would be updated after while within the livestatus process/thread.

        now = int( time.time() ) # current livestatus wants an INTEGER value for WaitTimeout ..
        host = 'test_host_0'
        # following request is nearly exactly what check_mk send (modulo the timestamps/hostname)
        # when you reschedule an immediate host check :
        command = b'[{now}] SCHEDULE_FORCED_HOST_CHECK;{host};{now}'.format(
                    now=now, host=host)
        wait_timeout_sec = randint(1, 3)
        request = b'''COMMAND {cmd}
GET hosts
WaitObject: {host}
WaitCondition: last_check >= {last_check}
WaitTimeout: {wait_timeout}
WaitTrigger: check
Columns: last_check state plugin_output
Filter: host_name = {host}
Localtime: {localtime}
OutputFormat: python
KeepAlive: on
ResponseHeader: fixed16
ColumnHeaders: true

'''.format(last_check=now, localtime=now, host=host, now=now, cmd=command,
           wait_timeout=wait_timeout_sec * 1000, # WaitTimeout header field is in millisecs
        )

        t0 = time.time()
        response = self.query_livestatus(request)
        t1 = time.time()
        self.assertLess(wait_timeout_sec, t1 - t0,
                        '(actually and in this very specific case) livestatus should take at least the requested WaitTimeout (%s sec) to complete ; response=%s' %
                        (wait_timeout_sec, response))
        goodresponse = "200          13\n[[0, 0, '']]\n"
        self.assertEqual(goodresponse, response)
        data = self.livestatus_broker.from_q.get(block=False)
        self.assertIsInstance(data, ExternalCommand)
        self.assertEqual(command, data.cmd_line)


if __name__ == '__main__':
    unittest.main()
