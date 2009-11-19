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
#or pollers. It is responsible for hight avaibility part. If a scheduler
#is dead,
#it send it's conf to another if available.
#It also read order form users (nagios.cmd) and send orders to schedulers.

#import os
import re
import time
#import sys
import Pyro.core
#import signal
import select
#import random
#import copy

#from check import Check
from util import scheduler_no_spare_first
from scheduler import Scheduler
from config import Config
#from macroresolver import MacroResolver
from external_command import ExternalCommand
from dispatcher import Dispatcher


#Main Arbiter Class
class Arbiter:
    def __init__(self):
        pass


    #Load the external commander
    def load_external_command(self, e):
        self.external_command = e
        self.fifo = e.open()
        
        
    def main(self):
        print "Loading configuration"
        self.conf = Config()
        #The config Class must have the USERN macro
        #There are 256 of them, so we create online
        Config.fill_usern_macros()
        self.conf.read_config("etc/nagios.cfg")

        print "****************** Create Template links **********"
        self.conf.linkify_templates()

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

        #from guppy import hpy
        #hp=hpy()
        #print hp.heap()
        #print hp.heapu()

        print "Dump realms"
        for r in self.conf.realms:
            print r.get_name(), r.__dict__

        print "****************** Cut into parts ******************"
        self.confs = self.conf.cut_into_parts()

        #self.conf.debug()

        print "****************** Send Configuration to schedulers******************"
        self.dispatcher = Dispatcher(self.conf)
        self.dispatcher.check_alive()
        self.dispatcher.check_dispatch()
        self.dispatcher.dispatch()
        
	#Now create the external commander
	e = ExternalCommand(self.conf, 'dispatcher')

	#Scheduler need to know about external command to activate it 
        #if necessery
	self.load_external_command(e)
	
	print "Configuration Loaded"
        
        #Main loop
	self.run()
	

    #Main function
    def run(self):
        print "Run baby, run..."
        timeout = 1.0
        while True :
            socks = []
            avant = time.time()
            if self.fifo != None:
                socks.append(self.fifo)
            # 'foreign' event loop
            ins,outs,exs = select.select(socks,[],[],timeout)
            if ins != []:
                for s in socks:
                    if s in ins:
                        #If FIFO, read external command
                        if s == self.fifo:
                            self.external_command.read_and_interpret()
                            self.fifo = self.external_command.open()

            else:#Timeout
                print "Timeout"
                #if not self.are_all_conf_assigned:
                self.dispatcher.check_alive()
                self.dispatcher.check_dispatch()
                self.dispatcher.dispatch()
                self.dispatcher.check_bad_dispatch()
                #send_conf_to_schedulers()
                timeout = 1.0
						
            if timeout < 0:
                timeout = 1.0



if __name__ == '__main__':
	p = Arbiter()
        import cProfile
	#p.main()
        command = """p.main()"""
        cProfile.runctx( command, globals(), locals(), filename="var/Arbiter.profile" )
