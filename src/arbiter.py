#!/usr/bin/python

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

seq_verif = get_sequence()

time_send = time.time()



class Arbiter:
    def __init__(self):
        pass


    def send_conf_to_schedulers(self):
        
        self.conf.schedulerlinks.items.values().sort(scheduler_no_spare_first)

        for sched in self.conf.schedulerlinks.items.values():
            print "sched", sched, "is alive ?", sched.is_alive()

        for reactionner in self.conf.reactionners.items.values():
            print "Reactionner", reactionner, "is alive ?", reactionner.is_alive()
        
        
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

        #TODO : more python
        tmp_conf = {}
        tmp_conf['schedulers'] = {}
        i = 0
        for sched in self.conf.schedulerlinks:
            tmp_conf['schedulers'][i] = {'port' : sched.port, 'address' : sched.address}
            i += 1
            
        for reactionner in self.conf.reactionners.items.values():
            reactionner.put_conf(tmp_conf)

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
        
        print "****************** Explode ***********************"
        self.conf.explode()
        
        print "****************** Inheritance *******************"
        self.conf.apply_inheritance()
        
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
        
        #self.conf.dump()
        #Creating the Macroresolver Class & unique instance
	#m = MacroResolver()
	#m.init(self.conf)
		
	#self.sched.load_conf(self.conf)

	#Now create the external commander
	e = ExternalCommand(self.conf, 'dispatcher')

	#Scheduler need to know about external command to activate it if necessery
	self.load_external_command(e)
	
	#External command need the sched because he can raise checks
	#e.load_scheduler(self.sched)
	
	print "Configuration Loaded"
	self.run()
	

    #Main function
    def run(self):
        print "First scheduling"
        #self.schedule()
        timeout = 1.0
        while True :
            socks=[]#self.daemon.getServerSockets()
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
                            #Must be paquet from poller
                        #else:
                        #    self.daemon.handleRequests()
                        #    apres=time.time()
                        #    diff = apres-avant
                        #    timeout = timeout - diff
                        #    break    # no need to continue with the for loop
            else:#Timeout
                print "Timeout"
                if not self.are_all_conf_assigned:
                    self.send_conf_to_schedulers()
                timeout = 1.0
						
            if timeout < 0:
                timeout = 1.0



if __name__ == '__main__':
	p = Arbiter()
	p.main()
