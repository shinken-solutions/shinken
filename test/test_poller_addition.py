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


class TestPollerAddition(ShinkenTest):
    def setUp(self):
        self.setup_with_file('etc/shinken_dispatcher.cfg')

    def test_simple_dispatch_and_addition(self):
        print "The dispatcher", self.dispatcher
        # dummy for the arbiter
        for a in self.conf.arbiters:
            a.__class__ = GoodArbiter
        print "Preparing schedulers"
        scheduler1 = self.conf.schedulers.find_by_name('scheduler-all-1')
        self.assert_(scheduler1 is not None)
        scheduler1.__class__ = GoodScheduler
        scheduler2 = self.conf.schedulers.find_by_name('scheduler-all-2')
        self.assert_(scheduler2 is not None)
        scheduler2.__class__ = BadScheduler

        print "Preparing pollers"
        poller1 = self.conf.pollers.find_by_name('poller-all-1')
        self.assert_(poller1 is not None)
        poller1.__class__ = GoodPoller
        poller2 = self.conf.pollers.find_by_name('poller-all-2')
        self.assert_(poller2 is not None)
        poller2.__class__ = BadPoller

        print "Preparing reactionners"
        reactionner1 = self.conf.reactionners.find_by_name('reactionner-all-1')
        self.assert_(reactionner1 is not None)
        reactionner1.__class__ = GoodReactionner
        reactionner2 = self.conf.reactionners.find_by_name('reactionner-all-2')
        self.assert_(reactionner2 is not None)
        reactionner2.__class__ = BadReactionner

        print "Preparing brokers"
        broker1 = self.conf.brokers.find_by_name('broker-all-1')
        self.assert_(broker1 is not None)
        broker1.__class__ = GoodBroker
        broker2 = self.conf.brokers.find_by_name('broker-all-2')
        self.assert_(broker2 is not None)
        broker2.__class__ = BadBroker

        # Ping all elements. Should have 1 as OK, 2 as
        # one bad attempt (3 max)
        self.dispatcher.check_alive()

        # Check good values
        self.assert_(scheduler1.alive == True)
        self.assert_(scheduler1.attempt == 0)
        self.assert_(scheduler1.reachable == True)
        # still alive, just unreach
        self.assert_(scheduler2.alive == True)
        self.assert_(scheduler2.attempt == 1)
        self.assert_(scheduler2.reachable == False)

        # and others satellites too
        self.assert_(poller1.alive == True)
        self.assert_(poller1.attempt == 0)
        self.assert_(poller1.reachable == True)
        # still alive, just unreach
        self.assert_(poller2.alive == True)
        self.assert_(poller2.attempt == 1)
        self.assert_(poller2.reachable == False)

        # and others satellites too
        self.assert_(reactionner1.alive == True)
        self.assert_(reactionner1.attempt == 0)
        self.assert_(reactionner1.reachable == True)
        # still alive, just unreach
        self.assert_(reactionner2.alive == True)
        self.assert_(reactionner2.attempt == 1)
        self.assert_(reactionner2.reachable == False)

        # and others satellites too
        self.assert_(broker1.alive == True)
        self.assert_(broker1.attempt == 0)
        self.assert_(broker1.reachable == True)
        # still alive, just unreach
        self.assert_(broker2.alive == True)
        self.assert_(broker2.attempt == 1)
        self.assert_(broker2.reachable == False)

        time.sleep(60)
        ### Now add another attempt, still alive, but attemp=2/3
        self.dispatcher.check_alive()

        # Check good values
        self.assert_(scheduler1.alive == True)
        self.assert_(scheduler1.attempt == 0)
        self.assert_(scheduler1.reachable == True)
        # still alive, just unreach
        self.assert_(scheduler2.alive == True)
        self.assert_(scheduler2.attempt == 2)
        self.assert_(scheduler2.reachable == False)

        # and others satellites too
        self.assert_(poller1.alive == True)
        self.assert_(poller1.attempt == 0)
        self.assert_(poller1.reachable == True)
        # still alive, just unreach
        self.assert_(poller2.alive == True)
        self.assert_(poller2.attempt == 2)
        self.assert_(poller2.reachable == False)

        # and others satellites too
        self.assert_(reactionner1.alive == True)
        self.assert_(reactionner1.attempt == 0)
        self.assert_(reactionner1.reachable == True)
        # still alive, just unreach
        self.assert_(reactionner2.alive == True)
        self.assert_(reactionner2.attempt == 2)
        self.assert_(reactionner2.reachable == False)

        # and others satellites too
        self.assert_(broker1.alive == True)
        self.assert_(broker1.attempt == 0)
        self.assert_(broker1.reachable == True)
        # still alive, just unreach
        self.assert_(broker2.alive == True)
        self.assert_(broker2.attempt == 2)
        self.assert_(broker2.reachable == False)

        time.sleep(60)
        ### Now we get BAD, We go DEAD for N2!
        self.dispatcher.check_alive()

        # Check good values
        self.assert_(scheduler1.alive == True)
        self.assert_(scheduler1.attempt == 0)
        self.assert_(scheduler1.reachable == True)
        # still alive, just unreach
        self.assert_(scheduler2.alive == False)
        self.assert_(scheduler2.attempt == 3)
        self.assert_(scheduler2.reachable == False)

        # and others satellites too
        self.assert_(poller1.alive == True)
        self.assert_(poller1.attempt == 0)
        self.assert_(poller1.reachable == True)
        # still alive, just unreach
        self.assert_(poller2.alive == False)
        self.assert_(poller2.attempt == 3)
        self.assert_(poller2.reachable == False)

        # and others satellites too
        self.assert_(reactionner1.alive == True)
        self.assert_(reactionner1.attempt == 0)
        self.assert_(reactionner1.reachable == True)
        # still alive, just unreach
        self.assert_(reactionner2.alive == False)
        self.assert_(reactionner2.attempt == 3)
        self.assert_(reactionner2.reachable == False)

        # and others satellites too
        self.assert_(broker1.alive == True)
        self.assert_(broker1.attempt == 0)
        self.assert_(broker1.reachable == True)
        # still alive, just unreach
        self.assert_(broker2.alive == False)
        self.assert_(broker2.attempt == 3)
        self.assert_(broker2.reachable == False)

        # Now we check how we should dispatch confs
        self.dispatcher.check_dispatch()
        # the conf should not be in a good shape
        self.assert_(self.dispatcher.dispatch_ok == False)

        # Now we really dispatch them!
        self.dispatcher.dispatch()
        self.assert_(self.any_log_match('Dispatch OK of conf in scheduler scheduler-all-1'))
        self.assert_(self.any_log_match('Dispatch OK of configuration 0 to reactionner reactionner-all-1'))
        self.assert_(self.any_log_match('Dispatch OK of configuration 0 to poller poller-all-1'))
        self.assert_(self.any_log_match('Dispatch OK of configuration 0 to broker broker-all-1'))
        self.clear_logs()

        # And look if we really dispatch conf as we should
        for r in self.conf.realms:
            for cfg in r.confs.values():
                self.assert_(cfg.is_assigned == True)
                self.assert_(cfg.assigned_to == scheduler1)

        cmd = "[%lu] ADD_SIMPLE_POLLER;All;newpoller;localhost;7771" % int(time.time())
        ext_cmd = ExternalCommand(cmd)
        self.external_command_dispatcher.resolve_command(ext_cmd)

        # Look for the poller now
        newpoller = self.conf.pollers.find_by_name('newpoller')
        self.assert_(newpoller is not None)
        newpoller.__class__ = GoodPoller

        ### Wht now with our new poller object?
        self.dispatcher.check_alive()

        # Check good values
        self.assert_(newpoller.alive == True)
        self.assert_(newpoller.attempt == 0)
        self.assert_(newpoller.reachable == True)

        # Now we check how we should dispatch confs
        self.dispatcher.check_bad_dispatch()
        self.dispatcher.dispatch()


if __name__ == '__main__':
    unittest.main()
