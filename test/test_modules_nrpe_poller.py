#!/usr/bin/env python
# Copyright (C) 2009-2010:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
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


#
# This file is used to test reading and processing of config files
#

import os
from Queue import Empty
from multiprocessing import Queue, Manager, active_children

from shinken_test import *
from shinken.log import logger
from shinken.objects.module import Module
from shinken.modules.booster_nrpe import module as nrpe_poller
from shinken.modules.booster_nrpe.module import get_instance
from shinken.message import Message

modconf = Module()
modconf.module_name = "NrpePoller"
modconf.module_type = nrpe_poller.properties['type']
modconf.properties = nrpe_poller.properties.copy()


class TestNrpePoller(ShinkenTest):
    # Uncomment this is you want to use a specific configuration
    # for your test
    #def setUp(self):
    #    self.setup_with_file('etc/nagios_module_hack_cmd_poller_tag.cfg')

    def test_nrpe_poller(self):
        if os.name == 'nt':
            return
        

        mod = nrpe_poller.Nrpe_poller(modconf)

        sl = get_instance(mod)
        # Look if we really change our commands

        print sl.__dict__
        sl.id = 1
        sl.i_am_dying = False

        manager = Manager()
        to_queue = manager.Queue()
        from_queue = manager.Queue() # list()
        control_queue = Queue()

        # We prepare a check in the to_queue
        status = 'queue'
        command = "$USER1$/check_nrpe -H localhost33  -n -u -t 5 -c check_load3 -a 20" # -a arg1 arg2 arg3"
        ref = None
        t_to_to = time.time()
        c = Check(status, command, ref, t_to_to)

        msg = Message(id=0, type='Do', data=c)
        to_queue.put(msg)

        # The worker will read a message by loop. We want it to
        # do 2 loops, so we fake a message, adn the Number 2 is a real
        # exit one
        msg1 = Message(id=0, type='All is good, continue')
        msg2 = Message(id=0, type='Die')

        control_queue.put(msg1)
        for _ in xrange(1, 2):
            control_queue.put(msg1)
        # control_queue.put(msg1)
        # control_queue.put(msg1)
        # control_queue.put(msg1)
        # control_queue.put(msg1)
        control_queue.put(msg2)
        sl.work(to_queue, from_queue, control_queue)

        o = from_queue.get() # pop()
        print "O", o

        print o.__dict__
        self.assert_(o.status == 'done')
        self.assert_(o.exit_status == 2)

        # to_queue.close()
        # control_queue.close()




if __name__ == '__main__':
    unittest.main()
