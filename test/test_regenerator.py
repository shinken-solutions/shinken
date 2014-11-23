#!/usr/bin/env python
# Copyright (C) 2009-2014:
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

import time

from shinken_test import ShinkenTest, unittest

from shinken.objects import Service
from shinken.misc.regenerator import Regenerator


class TestRegenerator(ShinkenTest):
    def setUp(self):
        self.setup_with_file('etc/shinken_regenerator.cfg')

    def look_for_same_values(self):
        # Look at Regenerator values
        print "Hosts:", self.rg.hosts.__dict__
        for h in self.rg.hosts:
            orig_h = self.sched.hosts.find_by_name(h.host_name)
            print h.state, orig_h.state
            # Look for same states
            self.assertEqual(orig_h.state, h.state)
            self.assertEqual(orig_h.state_type, h.state_type)
            # Look for same impacts
            for i in h.impacts:
                print "Got impact", i.get_name()
                same_impacts = i.get_name() in [j.get_name() for j in orig_h.impacts]
                self.assertTrue(same_impacts)
            # And look for same source problems
            for i in h.source_problems:
                print "Got source pb", i.get_name()
                same_pbs = i.get_name() in [j.get_name() for j in orig_h.source_problems]
                self.assertTrue(same_pbs)

        print "Services:", self.rg.services.__dict__
        for s in self.rg.services:
            orig_s = self.sched.services.find_srv_by_name_and_hostname(s.host.host_name, s.service_description)
            print s.state, orig_s.state
            self.assertEqual(orig_s.state, s.state)
            self.assertEqual(orig_s.state_type, s.state_type)
            # Look for same impacts too
            for i in s.impacts:
                print "Got impact", i.get_name()
                same_impacts = i.get_name() in [j.get_name() for j in orig_s.impacts]
                self.assertTrue(same_impacts)
            # And look for same source problems
            for i in s.source_problems:
                print "Got source pb", i.get_name()
                same_pbs = i.get_name() in [j.get_name() for j in orig_s.source_problems]
                self.assertTrue(same_pbs)
            # Look for same host
            self.assertEqual(orig_s.host.get_name(), s.host.get_name())

    def test_regenerator(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        # for h in self.sched.hosts:
        #    h.realm = h.realm.get_name()
        self.sched.conf.skip_initial_broks = False
        self.sched.brokers['Default-Broker'] = {'broks' : {}, 'has_full_broks' : False}
        self.sched.fill_initial_broks('Default-Broker')
        self.rg = Regenerator()

        # Got the initial creation ones
        ids = self.sched.broks.keys()
        ids.sort()
        t0 = time.time()
        for i in ids:
            b = self.sched.broks[i]
            print "Manage b", b.type
            b.prepare()
            self.rg.manage_brok(b)
        t1 = time.time()
        print 'First inc', t1 - t0, len(self.sched.broks)
        self.sched.broks.clear()

        self.look_for_same_values()

        print "Get the hosts and services"
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults
        self.scheduler_loop(3, [[host, 2, 'DOWN | value1=1 value2=2'], [router, 0, 'UP | rtt=10'], [svc, 2, 'BAD | value1=0 value2=0']])
        self.assertEqual('DOWN', host.state)
        self.assertEqual('HARD', host.state_type)

        ids = self.sched.broks.keys()
        ids.sort()
        t0 = time.time()
        for i in ids:
            b = self.sched.broks[i]
            print "Manage b", b.type
            b.prepare()
            self.rg.manage_brok(b)
        t1 = time.time()
        print 'Time', t1 - t0
        self.sched.broks.clear()

        self.look_for_same_values()

        print 'Time', t1 - t0

        b = svc.get_initial_status_brok()
        b.prepare()
        print "GO BENCH!"
        t0 = time.time()
        for i in xrange(1, 1000):
            b = svc.get_initial_status_brok()
            b.prepare()
            s = Service({})
            for (prop, value) in b.data.iteritems():
                setattr(s, prop, value)
        t1 = time.time()
        print "Bench end:", t1 - t0

        times = {}
        sizes = {}
        import cPickle
        data = {}
        cls = svc.__class__
        start = time.time()
        for i in xrange(1, 10000):
            for prop, entry in svc.__class__.properties.items():
                # Is this property intended for brokking?
                if 'full_status' in entry.fill_brok:
                    data[prop] = svc.get_property_value_for_brok(prop, cls.properties)
                    if not prop in times:
                        times[prop] = 0
                        sizes[prop] = 0
                    t0 = time.time()
                    tmp = cPickle.dumps(data[prop], 0)
                    sizes[prop] += len(tmp)
                    times[prop] += time.time() - t0

        print "Times"
        for (k, v) in times.iteritems():
            print "\t%s: %s" % (k, v)
        print "\n\n"
        print "Sizes"
        for (k, v) in sizes.iteritems():
            print "\t%s: %s" % (k, v)
        print "\n"
        print "total time", time.time() - start

    def test_regenerator_load_from_scheduler(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        # for h in self.sched.hosts:
        #    h.realm = h.realm.get_name()

        self.rg = Regenerator()
        self.rg.load_from_scheduler(self.sched)

        self.sched.conf.skip_initial_broks = False
        self.sched.brokers['Default-Broker'] = {'broks' : {}, 'has_full_broks' : False}
        self.sched.fill_initial_broks('Default-Broker')
        # Got the initial creation ones
        ids = self.sched.broks.keys()
        ids.sort()
        t0 = time.time()
        for i in ids:
            b = self.sched.broks[i]
            print "Manage b", b.type
            b.prepare()
            self.rg.manage_brok(b)
        t1 = time.time()
        print 'First inc', t1 - t0, len(self.sched.broks)
        self.sched.broks.clear()

        self.look_for_same_values()




if __name__ == '__main__':
    unittest.main()
