#!/usr/bin/env python2.6
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#
#This file is part of Shinken.
#
#Shinken is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Shinken is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

#
# This file is used to test reading and processing of config files
#

#It's ugly I know....
from shinken_test import *


class GoodScheduler(SchedulerLink):
    # To lie about satellites
    def ping(self):
        print "Dummy OK for", self.get_name()
        self.set_alive()

class BadScheduler(SchedulerLink):
    def ping(self):
        print "Dummy bad ping", self.get_name()
        self.add_failed_check_attempt()


class GoodPoller(PollerLink):
    # To lie about satellites
    def ping(self):
        print "Dummy OK for", self.get_name()
        self.set_alive()

class BadPoller(PollerLink):
    def ping(self):
        print "Dummy bad ping", self.get_name()
        self.add_failed_check_attempt()

class GoodReactionner(ReactionnerLink):
    # To lie about satellites
    def ping(self):
        print "Dummy OK for", self.get_name()
        self.set_alive()

class BadReactionner(ReactionnerLink):
    def ping(self):
        print "Dummy bad ping", self.get_name()
        self.add_failed_check_attempt()

class GoodBroker(BrokerLink):
    # To lie about satellites
    def ping(self):
        print "Dummy OK for", self.get_name()
        self.set_alive()

class BadBroker(BrokerLink):
    def ping(self):
        print "Dummy bad ping", self.get_name()
        self.add_failed_check_attempt()


class TestDispatcher(ShinkenTest):
    #Uncomment this is you want to use a specific configuration
    #for your test
    def setUp(self):
        self.setup_with_file('etc/nagios_dispatcher.cfg')
    
    
    #Change ME :)
    def test_simple_dispatch(self):
        print "The dispatcher", self.dispatcher
        print "Preparing schedulers"
        scheduler1 = self.conf.schedulerlinks.find_by_name('scheduler-all-1')
        self.assert_(scheduler1 != None)
        scheduler1.__class__ = GoodScheduler
        scheduler2 = self.conf.schedulerlinks.find_by_name('scheduler-all-2')
        self.assert_(scheduler2 != None)
        scheduler2.__class__ = BadScheduler        

        print "Preparing pollers"
        poller1 = self.conf.pollers.find_by_name('poller-all-1')
        self.assert_(poller1 != None)
        poller1.__class__ = GoodPoller
        poller2 = self.conf.pollers.find_by_name('poller-all-2')
        self.assert_(poller2 != None)
        poller2.__class__ = BadPoller        

        print "Preparing reactionners"
        reactionner1 = self.conf.reactionners.find_by_name('reactionner-all-1')
        self.assert_(reactionner1 != None)
        reactionner1.__class__ = GoodReactionner
        reactionner2 = self.conf.reactionners.find_by_name('reactionner-all-2')
        self.assert_(reactionner2 != None)
        reactionner2.__class__ = BadReactionner        

        print "Preparing brokers"
        broker1 = self.conf.brokers.find_by_name('broker-all-1')
        self.assert_(broker1 != None)
        broker1.__class__ = GoodBroker
        broker2 = self.conf.brokers.find_by_name('broker-all-2')
        self.assert_(broker2 != None)
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
        

if __name__ == '__main__':
    unittest.main()

