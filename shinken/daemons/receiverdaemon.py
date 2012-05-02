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


import os
import time
import traceback
import sys

from multiprocessing import active_children
from Queue import Empty

from shinken.satellite import BaseSatellite

from shinken.property import PathProp, IntegerProp
from shinken.log import logger


from shinken.external_command import ExternalCommand


# Our main APP class
class Receiver(BaseSatellite):

    properties = BaseSatellite.properties.copy()
    properties.update({
        'pidfile':   PathProp(default='receiverd.pid'),
        'port':      IntegerProp(default='7773'),
        'local_log': PathProp(default='receiverd.log'),
    })


    def __init__(self, config_file, is_daemon, do_replace, debug, debug_file):
        
        super(Receiver, self).__init__('receiver', config_file, is_daemon, do_replace, debug, debug_file)

        # Our arbiters
        self.arbiters = {}

        # Our pollers and reactionners
        self.pollers = {}
        self.reactionners = {}

        # Modules are load one time
        self.have_modules = False

        # Can have a queue of external_commands give by modules
        # will be taken by arbiter to process
        self.external_commands = []

        # All broks to manage
        self.broks = [] # broks to manage
        # broks raised this turn and that need to be put in self.broks
        self.broks_internal_raised = []
        

    # Schedulers have some queues. We can simplify call by adding
    # elements into the proper queue just by looking at their type
    # Brok -> self.broks
    # TODO : better tag ID?
    # External commands -> self.external_commands
    def add(self, elt):
        cls_type = elt.__class__.my_type
        if cls_type == 'brok':
            # For brok, we TAG brok with our instance_id
            elt.instance_id = 0
            self.broks_internal_raised.append(elt)
            return
        elif cls_type == 'externalcommand':
            logger.debug("Enqueuing an external command: %s" % str(ExternalCommand.__dict__))
            self.external_commands.append(elt)


#    # Get the good tabs for links by the kind. If unknown, return None
#    def get_links_from_type(self, type):
#        t = {'scheduler' : self.schedulers, 'arbiter' : self.arbiters, \
#             'poller' : self.pollers, 'reactionner' : self.reactionners}
#        if type in t :
#            return t[type]
#        return None


    # Call by arbiter to get our external commands
    def get_external_commands(self):
        res = self.external_commands
        self.external_commands = []
        return res


    # Get a brok. Our role is to put it in the modules
    # THEY MUST DO NOT CHANGE data of b !!!
    # REF: doc/receiver-modules.png (4-5)
    def manage_brok(self, b):
        to_del = []
        # Call all modules if they catch the call
        for mod in self.modules_manager.get_internal_instances():
            try:
                mod.manage_brok(b)
            except Exception , exp:
                logger.warning("The mod %s raise an exception: %s, I kill it" % (mod.get_name(),str(exp)))
                logger.warning("Exception type : %s" % type(exp))
                logger.warning("Back trace of this kill: %s" % (traceback.format_exc()))
                to_del.append(mod)
        # Now remove mod that raise an exception
        self.modules_manager.clear_instances(to_del)


    # Get 'objects' from external modules
    # from now nobody use it, but it can be useful
    # for a moduel like livestatus to raise external
    # commandsfor example
    def get_objects_from_from_queues(self):
        for f in self.modules_manager.get_external_from_queues():
            full_queue = True
            while full_queue:
                try:
                    o = f.get(block=False)
                    self.add(o)
                except Empty :
                    full_queue = False


    def do_stop(self):
        act = active_children()
        for a in act:
            a.terminate()
            a.join(1)
        super(Receiver, self).do_stop()
        
        
    def setup_new_conf(self):
        conf = self.new_conf
        self.new_conf = None
        self.cur_conf = conf
        # Got our name from the globals
        if 'receiver_name' in conf['global']:
            name = conf['global']['receiver_name']
        else:
            name = 'Unnamed receiver'
        self.name = name
        self.log.load_obj(self, name)

        logger.debug("[%s] Sending us configuration %s" % (self.name, conf))

        if not self.have_modules:
            self.modules = mods = conf['global']['modules']
            self.have_modules = True
            logger.info("We received modules %s " % mods)

        # Set our giving timezone from arbiter
        use_timezone = conf['global']['use_timezone']
        if use_timezone != 'NOTSET':
            logger.info("Setting our timezone to %s" % use_timezone)
            os.environ['TZ'] = use_timezone
            time.tzset()
        
        

    def do_loop_turn(self):
        sys.stdout.write(".")
        sys.stdout.flush()

        # Begin to clean modules
        self.check_and_del_zombie_modules()

        # Now we check if arbiter speek to us in the pyro_daemon.
        # If so, we listen for it
        # When it push us conf, we reinit connections
        self.watch_for_new_conf(0.0)
        if self.new_conf:
            self.setup_new_conf()

#        # Maybe the last loop we raised some broks internally
#        # we should interger them in broks
#        self.interger_internal_broks()

#        # And from schedulers
#        self.get_new_broks(type='scheduler')
#        # And for other satellites
#        self.get_new_broks(type='poller')
#        self.get_new_broks(type='reactionner')

#        # Sort the brok list by id
#        self.broks.sort(sort_by_ids)

#        # and for external queues
#        # REF: doc/receiver-modules.png (3)
#        for b in self.broks:
#            # if b.type != 'log':
#            #     print "Receiver : put brok id : %d" % b.id
#            for q in self.modules_manager.get_external_to_queues():
#                q.put(b)

#        # We must had new broks at the end of the list, so we reverse the list
#        self.broks.reverse()

        start = time.time()
#        while len(self.broks) != 0:
#            now = time.time()
#            # Do not 'manage' more than 1s, we must get new broks
#            # every 1s
#            if now - start > 1:
#                break
#
#            b = self.broks.pop()
#            # Ok, we can get the brok, and doing something with it
#            # REF: doc/receiver-modules.png (4-5)
#            self.manage_brok(b)
#
#            nb_broks = len(self.broks)
#
#            # Ok we manage brok, but we still want to listen to arbiter
#            self.watch_for_new_conf(0.0)
#
#            # if we got new broks here from arbiter, we should breack the loop
#            # because such broks will not be managed by the
#            # external modules before this loop (we pop them!)
#            if len(self.broks) != nb_broks:
#                break
#
        # Maybe external modules raised 'objets'
        # we should get them
        self.get_objects_from_from_queues()

        # Maybe we do not have something to do, so we wait a little
        if len(self.broks) == 0:
            # print "watch new conf 1 : begin", len(self.broks)
            self.watch_for_new_conf(1.0)
            # print "get enw broks watch new conf 1 : end", len(self.broks)


    #  Main function, will loop forever
    def main(self):
        try:
            self.load_config_file()
        
            for line in self.get_header():
                self.log.info(line)

            logger.info("[Receiver] Using working directory : %s" % os.path.abspath(self.workdir))
        
            self.do_daemon_init_and_start()
            
            self.uri2 = self.pyro_daemon.register(self.interface, "ForArbiter")
            logger.debug("The Arbiter uri it at %s" % self.uri2)

            #  We wait for initial conf
            self.wait_for_initial_conf()
            if not self.new_conf:
                return

            self.setup_new_conf()

            self.modules_manager.set_modules(self.modules)
            self.do_load_modules()
            # and start external modules too
            self.modules_manager.start_external_instances()

            # Do the modules part, we have our modules in self.modules
            # REF: doc/receiver-modules.png (1)


            # Now the main loop
            self.do_mainloop()

        except Exception, exp:
            logger.critical("I got an unrecoverable error. I have to exit")
            logger.critical("You can log a bug ticket at https://github.com/naparuba/shinken/issues/new to get help")
            logger.critical("Back trace of it: %s" % (traceback.format_exc()))
            raise

