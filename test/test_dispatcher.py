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

from shinken_test import *


class GoodArbiter(ArbiterLink):

    # To lie about satellites
    def ping(self):
        print "Dummy OK for", self.get_name()
        self.set_alive()

    def have_conf(self, i):
        return True

    def do_not_run(self):
        pass


class GoodScheduler(SchedulerLink):

    # To lie about satellites
    def ping(self):
        print "Dummy OK for", self.get_name()
        self.set_alive()

    def have_conf(self, i):
        return True

    def put_conf(self, conf):
        return True


class BadScheduler(SchedulerLink):
    def ping(self):
        print "Dummy bad ping", self.get_name()
        self.add_failed_check_attempt()

    def have_conf(self, i):
        return False


class GoodPoller(PollerLink):

    # To lie about satellites
    def ping(self):
        print "Dummy OK for", self.get_name()
        self.set_alive()

    def put_conf(self, conf):
        return True


class BadPoller(PollerLink):
    def ping(self):
        print "Dummy bad ping", self.get_name()
        self.add_failed_check_attempt()


class GoodReactionner(ReactionnerLink):

    # To lie about satellites
    def ping(self):
        print "Dummy OK for", self.get_name()
        self.set_alive()

    def put_conf(self, conf):
        return True


class BadReactionner(ReactionnerLink):
    def ping(self):
        print "Dummy bad ping", self.get_name()
        self.add_failed_check_attempt()


class GoodBroker(BrokerLink):

    # To lie about satellites
    def ping(self):
        print "Dummy OK for", self.get_name()
        self.set_alive()

    def put_conf(self, conf):
        return True


class BadBroker(BrokerLink):
    def ping(self):
        print "Dummy bad ping", self.get_name()
        self.add_failed_check_attempt()


class TestDispatcher(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_dispatcher.cfg')

    def test_simple_dispatch(self):
        for r in self.conf.realms:
            print r.get_name()
        r = self.conf.realms.find_by_name('All')
        print "The dispatcher", self.dispatcher
        # dummy for the arbiter
        for a in self.conf.arbiters:
            a.__class__ = GoodArbiter
        elts_types = ['schedulers', 'pollers', 'reactionners', 'brokers', 'receivers']
        for t in elts_types:
            lst = getattr(self.conf, t)
            for s in lst:
                print "TAG s", s
                s.realm = r

        print "Preparing schedulers"
        scheduler1 = self.conf.schedulers.find_by_name('scheduler-all-1')
        self.assertIsNot(scheduler1, None)
        scheduler1.__class__ = GoodScheduler
        scheduler2 = self.conf.schedulers.find_by_name('scheduler-all-2')
        self.assertIsNot(scheduler2, None)
        scheduler2.__class__ = BadScheduler

        print "Preparing pollers"
        poller1 = self.conf.pollers.find_by_name('poller-all-1')
        self.assertIsNot(poller1, None)
        poller1.__class__ = GoodPoller
        poller2 = self.conf.pollers.find_by_name('poller-all-2')
        self.assertIsNot(poller2, None)
        poller2.__class__ = BadPoller

        print "Preparing reactionners"
        reactionner1 = self.conf.reactionners.find_by_name('reactionner-all-1')
        self.assertIsNot(reactionner1, None)
        reactionner1.__class__ = GoodReactionner
        reactionner2 = self.conf.reactionners.find_by_name('reactionner-all-2')
        self.assertIsNot(reactionner2, None)
        reactionner2.__class__ = BadReactionner

        print "Preparing brokers"
        broker1 = self.conf.brokers.find_by_name('broker-all-1')
        self.assertIsNot(broker1, None)
        broker1.__class__ = GoodBroker
        broker2 = self.conf.brokers.find_by_name('broker-all-2')
        self.assertIsNot(broker2, None)
        broker2.__class__ = BadBroker

        # Ping all elements. Should have 1 as OK, 2 as
        # one bad attempt (3 max)
        self.dispatcher.check_alive()

        # Check good values
        self.assertEqual(True, scheduler1.alive)
        self.assertEqual(0, scheduler1.attempt)
        self.assertEqual(True, scheduler1.reachable)
        # still alive, just unreach
        self.assertEqual(True, scheduler2.alive)
        self.assertEqual(1, scheduler2.attempt)
        self.assertEqual(False, scheduler2.reachable)

        # and others satellites too
        self.assertEqual(True, poller1.alive)
        self.assertEqual(0, poller1.attempt)
        self.assertEqual(True, poller1.reachable)
        # still alive, just unreach
        self.assertEqual(True, poller2.alive)
        self.assertEqual(1, poller2.attempt)
        self.assertEqual(False, poller2.reachable)

        # and others satellites too
        self.assertEqual(True, reactionner1.alive)
        self.assertEqual(0, reactionner1.attempt)
        self.assertEqual(True, reactionner1.reachable)
        # still alive, just unreach
        self.assertEqual(True, reactionner2.alive)
        self.assertEqual(1, reactionner2.attempt)
        self.assertEqual(False, reactionner2.reachable)

        # and others satellites too
        self.assertEqual(True, broker1.alive)
        self.assertEqual(0, broker1.attempt)
        self.assertEqual(True, broker1.reachable)
        # still alive, just unreach
        self.assertEqual(True, broker2.alive)
        self.assertEqual(1, broker2.attempt)
        self.assertEqual(False, broker2.reachable)
        ### Now add another attempt, still alive, but attemp=2/3

        print "CheckAlive " * 10
        # We reset check time for the test
        elts = [scheduler1, scheduler2, poller1, poller2, broker1, broker2, reactionner1, reactionner2]
        for i in elts:
            i.last_check = 0.0

        self.dispatcher.check_alive()

        # Check good values
        self.assertEqual(True, scheduler1.alive)
        self.assertEqual(0, scheduler1.attempt)
        self.assertEqual(True, scheduler1.reachable)
        # still alive, just unreach
        self.assertEqual(True, scheduler2.alive)
        self.assertEqual(2, scheduler2.attempt)
        self.assertEqual(False, scheduler2.reachable)

        # and others satellites too
        self.assertEqual(True, poller1.alive)
        self.assertEqual(0, poller1.attempt)
        self.assertEqual(True, poller1.reachable)
        # still alive, just unreach
        self.assertEqual(True, poller2.alive)
        self.assertEqual(2, poller2.attempt)
        self.assertEqual(False, poller2.reachable)

        # and others satellites too
        self.assertEqual(True, reactionner1.alive)
        self.assertEqual(0, reactionner1.attempt)
        self.assertEqual(True, reactionner1.reachable)
        # still alive, just unreach
        self.assertEqual(True, reactionner2.alive)
        self.assertEqual(2, reactionner2.attempt)
        self.assertEqual(False, reactionner2.reachable)

        # and others satellites too
        self.assertEqual(True, broker1.alive)
        self.assertEqual(0, broker1.attempt)
        self.assertEqual(True, broker1.reachable)
        # still alive, just unreach
        self.assertEqual(True, broker2.alive)
        self.assertEqual(2, broker2.attempt)
        self.assertEqual(False, broker2.reachable)

        ### Now we get BAD, We go DEAD for N2!
        print "CheckAlive " * 10
        # We reset check time for the test
        elts = [scheduler1, scheduler2, poller1, poller2, broker1, broker2, reactionner1, reactionner2]
        for i in elts:
            i.last_check = 0.0
        self.dispatcher.check_alive()

        # Check good values
        self.assertEqual(True, scheduler1.alive)
        self.assertEqual(0, scheduler1.attempt)
        self.assertEqual(True, scheduler1.reachable)
        # still alive, just unreach
        self.assertEqual(False, scheduler2.alive)
        self.assertEqual(3, scheduler2.attempt)
        self.assertEqual(False, scheduler2.reachable)

        # and others satellites too
        self.assertEqual(True, poller1.alive)
        self.assertEqual(0, poller1.attempt)
        self.assertEqual(True, poller1.reachable)
        # still alive, just unreach
        self.assertEqual(False, poller2.alive)
        self.assertEqual(3, poller2.attempt)
        self.assertEqual(False, poller2.reachable)

        # and others satellites too
        self.assertEqual(True, reactionner1.alive)
        self.assertEqual(0, reactionner1.attempt)
        self.assertEqual(True, reactionner1.reachable)
        # still alive, just unreach
        self.assertEqual(False, reactionner2.alive)
        self.assertEqual(3, reactionner2.attempt)
        self.assertEqual(False, reactionner2.reachable)

        # and others satellites too
        self.assertEqual(True, broker1.alive)
        self.assertEqual(0, broker1.attempt)
        self.assertEqual(True, broker1.reachable)
        # still alive, just unreach
        self.assertEqual(False, broker2.alive)
        self.assertEqual(3, broker2.attempt)
        self.assertEqual(False, broker2.reachable)

        # Now we check how we should dispatch confs
        self.dispatcher.check_dispatch()
        # the conf should not be in a good shape
        self.assertEqual(False, self.dispatcher.dispatch_ok)

        # Now we really dispatch them!
        self.dispatcher.dispatch()
        self.assert_any_log_match('Dispatch OK of conf in scheduler scheduler-all-1')
        self.assert_any_log_match('Dispatch OK of configuration 0 to reactionner reactionner-all-1')
        self.assert_any_log_match('Dispatch OK of configuration 0 to poller poller-all-1')
        self.assert_any_log_match('Dispatch OK of configuration 0 to broker broker-all-1')
        self.clear_logs()

        # And look if we really dispatch conf as we should
        for r in self.conf.realms:
            for cfg in r.confs.values():
                self.assertEqual(True, cfg.is_assigned)
                self.assertEqual(scheduler1, cfg.assigned_to)


class TestDispatcherMultiBroker(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_dispatcher_multibrokers.cfg')

    def test_simple_dispatch(self):
        print "The dispatcher", self.dispatcher
        # dummy for the arbiter
        for a in self.conf.arbiters:
            a.__class__ = GoodArbiter
        print "Preparing schedulers"
        scheduler1 = self.conf.schedulers.find_by_name('scheduler-all-1')
        self.assertIsNot(scheduler1, None)
        scheduler1.__class__ = GoodScheduler
        scheduler2 = self.conf.schedulers.find_by_name('scheduler-all-2')
        self.assertIsNot(scheduler2, None)
        scheduler2.__class__ = GoodScheduler

        print "Preparing pollers"
        poller1 = self.conf.pollers.find_by_name('poller-all-1')
        self.assertIsNot(poller1, None)
        poller1.__class__ = GoodPoller
        poller2 = self.conf.pollers.find_by_name('poller-all-2')
        self.assertIsNot(poller2, None)
        poller2.__class__ = BadPoller

        print "Preparing reactionners"
        reactionner1 = self.conf.reactionners.find_by_name('reactionner-all-1')
        self.assertIsNot(reactionner1, None)
        reactionner1.__class__ = GoodReactionner
        reactionner2 = self.conf.reactionners.find_by_name('reactionner-all-2')
        self.assertIsNot(reactionner2, None)
        reactionner2.__class__ = BadReactionner

        print "Preparing brokers"
        broker1 = self.conf.brokers.find_by_name('broker-all-1')
        self.assertIsNot(broker1, None)
        broker1.__class__ = GoodBroker
        broker2 = self.conf.brokers.find_by_name('broker-all-2')
        self.assertIsNot(broker2, None)
        broker2.__class__ = GoodBroker

        # Ping all elements. Should have 1 as OK, 2 as
        # one bad attempt (3 max)
        self.dispatcher.check_alive()

        # Check good values
        self.assertEqual(True, scheduler1.alive)
        self.assertEqual(0, scheduler1.attempt)
        self.assertEqual(True, scheduler1.reachable)
        # still alive, just unreach
        self.assertEqual(True, scheduler2.alive)
        self.assertEqual(0, scheduler2.attempt)
        self.assertEqual(True, scheduler2.reachable)

        # and others satellites too
        self.assertEqual(True, poller1.alive)
        self.assertEqual(0, poller1.attempt)
        self.assertEqual(True, poller1.reachable)
        # still alive, just unreach
        self.assertEqual(True, poller2.alive)
        self.assertEqual(1, poller2.attempt)
        self.assertEqual(False, poller2.reachable)

        # and others satellites too
        self.assertEqual(True, reactionner1.alive)
        self.assertEqual(0, reactionner1.attempt)
        self.assertEqual(True, reactionner1.reachable)
        # still alive, just unreach
        self.assertEqual(True, reactionner2.alive)
        self.assertEqual(1, reactionner2.attempt)
        self.assertEqual(False, reactionner2.reachable)

        # and others satellites too
        self.assertEqual(True, broker1.alive)
        self.assertEqual(0, broker1.attempt)
        self.assertEqual(True, broker1.reachable)
        # still alive, just unreach
        self.assertEqual(True, broker2.alive)
        self.assertEqual(0, broker2.attempt)
        self.assertEqual(True, broker2.reachable)

        ### Now add another attempt, still alive, but attemp=2/3
        print "CheckAlive " * 10
        # We reset check time for the test
        elts = [scheduler1, scheduler2, poller1, poller2, broker1, broker2, reactionner1, reactionner2]
        for i in elts:
            i.last_check = 0.0
        self.dispatcher.check_alive()

        # Check good values
        self.assertEqual(True, scheduler1.alive)
        self.assertEqual(0, scheduler1.attempt)
        self.assertEqual(True, scheduler1.reachable)
        # still alive, just unreach
        self.assertEqual(True, scheduler2.alive)
        self.assertEqual(0, scheduler2.attempt)
        self.assertEqual(True, scheduler2.reachable)

        # and others satellites too
        self.assertEqual(True, poller1.alive)
        self.assertEqual(0, poller1.attempt)
        self.assertEqual(True, poller1.reachable)
        # still alive, just unreach
        self.assertEqual(True, poller2.alive)
        self.assertEqual(2, poller2.attempt)
        self.assertEqual(False, poller2.reachable)

        # and others satellites too
        self.assertEqual(True, reactionner1.alive)
        self.assertEqual(0, reactionner1.attempt)
        self.assertEqual(True, reactionner1.reachable)
        # still alive, just unreach
        self.assertEqual(True, reactionner2.alive)
        self.assertEqual(2, reactionner2.attempt)
        self.assertEqual(False, reactionner2.reachable)

        # and others satellites too
        self.assertEqual(True, broker1.alive)
        self.assertEqual(0, broker1.attempt)
        self.assertEqual(True, broker1.reachable)
        # still alive, just unreach
        self.assertEqual(True, broker2.alive)
        self.assertEqual(0, broker2.attempt)
        self.assertEqual(True, broker2.reachable)

        ### Now we get BAD, We go DEAD for N2!
        print "CheckAlive " * 10
        # We reset check time for the test
        elts = [scheduler1, scheduler2, poller1, poller2, broker1, broker2, reactionner1, reactionner2]
        for i in elts:
            i.last_check = 0.0
        self.dispatcher.check_alive()

        # Check good values
        self.assertEqual(True, scheduler1.alive)
        self.assertEqual(0, scheduler1.attempt)
        self.assertEqual(True, scheduler1.reachable)
        # still alive, just unreach
        self.assertEqual(True, scheduler2.alive)
        self.assertEqual(0, scheduler2.attempt)
        self.assertEqual(True, scheduler2.reachable)

        # and others satellites too
        self.assertEqual(True, poller1.alive)
        self.assertEqual(0, poller1.attempt)
        self.assertEqual(True, poller1.reachable)
        # still alive, just unreach
        self.assertEqual(False, poller2.alive)
        self.assertEqual(3, poller2.attempt)
        self.assertEqual(False, poller2.reachable)

        # and others satellites too
        self.assertEqual(True, reactionner1.alive)
        self.assertEqual(0, reactionner1.attempt)
        self.assertEqual(True, reactionner1.reachable)
        # still alive, just unreach
        self.assertEqual(False, reactionner2.alive)
        self.assertEqual(3, reactionner2.attempt)
        self.assertEqual(False, reactionner2.reachable)

        # and others satellites too
        self.assertEqual(True, broker1.alive)
        self.assertEqual(0, broker1.attempt)
        self.assertEqual(True, broker1.reachable)
        # still alive, just unreach
        self.assertEqual(True, broker2.alive)
        self.assertEqual(0, broker2.attempt)
        self.assertEqual(True, broker2.reachable)

        # Now we check how we should dispatch confs
        self.dispatcher.check_dispatch()
        # the conf should not be in a good shape
        self.assertEqual(False, self.dispatcher.dispatch_ok)

        # Now we really dispatch them!
        self.dispatcher.dispatch()
        self.assert_any_log_match('Dispatch OK of conf in scheduler scheduler-all-1')
        self.assert_any_log_match('Dispatch OK of configuration 0 to reactionner reactionner-all-1')
        self.assert_any_log_match('Dispatch OK of configuration 0 to poller poller-all-1')

        self.assert_any_log_match('Dispatch OK of configuration 1 to broker broker-all-1')
        self.assert_any_log_match('Dispatch OK of configuration 0 to broker broker-all-2')
        self.clear_logs()


        # And look if we really dispatch conf as we should
        for r in self.conf.realms:
            for cfg in r.confs.values():
                self.assertEqual(True, cfg.is_assigned)
                self.assertIn(cfg.assigned_to, [scheduler1, scheduler2])




if __name__ == '__main__':
    unittest.main()
