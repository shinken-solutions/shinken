#!/usr/bin/python
#Copyright (C) 2009 Gabes Jean, naparuba@gmail.com
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


#This is the class of the Arbiter. It's role is to read configuration,
#cuts it, and send it to other elements like schedulers, reactionner 
#or pollers. It is responsible for hight avaibility part. If a scheduler is dead,
#it send it's conf to another if available.
#It also read order form users (nagios.cmd) and send orders to schedulers.

import os
import re
import time
import sys
import Pyro.core
import signal
import select
import random
import copy

from check import Check
from util import get_sequence, scheduler_no_spare_first
from scheduler import Scheduler
from config import Config
from macroresolver import MacroResolver
from external_command import ExternalCommand


#Main Arbiter Class
class Arbiter:
    def __init__(self):
        pass


    def send_conf_to_schedulers(self):
        
        self.conf.schedulerlinks.items.values().sort(scheduler_no_spare_first)

        for sched in self.conf.schedulerlinks.items.values():
            print "sched", sched, "is alive ?", sched.is_alive()

        for reactionner in self.conf.reactionners.items.values():
            print "Reactionner", reactionner, "is alive ?", reactionner.is_alive()
        

        for broker in self.conf.brokers.items.values():
            print "Broker", broker, "is alive ?", broker.is_alive()

        
        #self.conf.schedulerlinks.sort(scheduler_no_spare_first)
        #no_spare_sched = [s for s in self.conf.schedulerlinks if not s.spare]
        
        #conf_association = zip(self.conf.schedulerlinks, self.conf.confs.values())
        nb_error = 0
        #for (sched, conf) in conf_association:
        print "Dispatching ", len(self.conf.confs), "configurations"
        for conf in self.conf.confs.values():
            if not conf.is_assigned:
                for sched in self.conf.schedulerlinks:
                    if not sched.is_active and not conf.is_assigned:
                        print sched.id
                        try:
                            sched.put_conf(conf)
                            sched.is_active = True
                            conf.is_assigned = True
                            conf.assigned_to = sched
                        except Pyro.errors.URIError as exp:
                            print exp
                        except Pyro.errors.ProtocolError as exp:
                            print exp

        #TODO : more python and change ID
        tmp_conf = {}
        tmp_conf['schedulers'] = {}
        i = 0
        for sched in self.conf.schedulerlinks:
            tmp_conf['schedulers'][i] = {'port' : sched.port, 'address' : sched.address, 'name' : sched.name, 'instance_id' : 0}
            i += 1
            
        for reactionner in self.conf.reactionners.items.values():
            reactionner.put_conf(tmp_conf)

        for broker in self.conf.brokers.items.values():
            broker.put_conf(tmp_conf)


        #TODO : clean and link
        #Now Poller
        tmp_conf = {}
        tmp_conf['schedulers'] = {}
        i = 0
        sched = self.conf.schedulerlinks[0]
        tmp_conf['schedulers'][i] = {'port' : sched.port, 'address' : sched.address}
        

        for poller in self.conf.pollers.items.values():
            poller.put_conf(tmp_conf)


        nb_confs = len(self.conf.confs)
        nb_assigned_confs = len([c for c in self.conf.confs.values() if c.is_assigned])

        self.are_all_conf_assigned = nb_assigned_confs == nb_confs
        if not self.are_all_conf_assigned:
            print "WARNING : All configurations are not dispatched ", nb_confs - nb_assigned_confs, "are missing (only ", nb_assigned_confs ," assigned)"
        else:
            print "OK, all configuratiosn are dispatched :)"


    #Load the external commander
    def load_external_command(self, e):
        self.external_command = e
        self.fifo = e.open()
        
        
    def main(self):
        print "Loading configuration"
        self.conf = Config()
        g_config = self.conf
        self.conf.read_config("nagios.cfg")

        print "****************** Create Template list **********"
        self.conf.create_templates_list()

        print "****************** Inheritance *******************"
        self.conf.apply_inheritance()
        
        print "****************** Explode ***********************"
        self.conf.explode()

        print "***************** Create Name reversed list ******"
        self.conf.create_reversed_list()

        print "***************** Cleaning Twins *****************"
        self.conf.remove_twins()

        print "****************** Implicit inheritance *******************"
        self.conf.apply_implicit_inheritance()

        print "****************** Fill default ******************"
        self.conf.fill_default()
        
        print "****************** Clean templates ******************"
        self.conf.clean_useless()
        
        print "****************** Pythonize ******************"
        self.conf.pythonize()
        
        print "****************** Linkify ******************"
        self.conf.linkify()
        
        print "*************** applying dependancies ************"
        self.conf.apply_dependancies()
        
        print "************** Exlode global conf ****************"
        self.conf.explode_global_conf()
        
        print "****************** Correct ?******************"
        self.conf.is_correct()


        print "****************** Cut into parts ******************"
        self.confs = self.conf.cut_into_parts()

        print "****************** Send Configuration to schedulers******************"
        self.send_conf_to_schedulers()
        
	#Now create the external commander
	e = ExternalCommand(self.conf, 'dispatcher')

	#Scheduler need to know about external command to activate it if necessery
	self.load_external_command(e)
	
	print "Configuration Loaded"
	self.run()
	

    #Main function
    def run(self):
        print "Run baby, run..."
        timeout = 1.0
        while True :
            socks=[]
            avant=time.time()
            
            socks.append(self.fifo)
            
            ins,outs,exs=select.select(socks,[],[],timeout)   # 'foreign' event loop
            if ins != []:
                for s in socks:
                    if s in ins:
                        #If FIFO, read external command
                        if s == self.fifo:
                            self.external_command.read_and_interpret()
                            self.fifo = self.external_command.open()

            else:#Timeout
                print "Timeout"
                if not self.are_all_conf_assigned:
                    self.send_conf_to_schedulers()
                timeout = 1.0
						
            if timeout < 0:
                timeout = 1.0



if __name__ == '__main__':
	p = Arbiter()
        import cProfile
	#p.main()
        command = """p.main()"""
        cProfile.runctx( command, globals(), locals(), filename="Arbiter.profile" )
