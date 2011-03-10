#!/usr/bin/env python
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
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


#This is the class of the dispatcher. It's role is to dispatch
#configurations to other elements like schedulers, reactionner,
#pollers and brokers. It is responsible for hight avaibility part. If an
#element die and the element type have a spare, it send the confi of the
#dead to the spare


from shinken.util import alive_then_spare_then_deads
from shinken.log import logger

#Dispatcher Class
class Dispatcher:
    #Load all elements, set them no assigned
    #and add them to elements, so loop will be easier :)
    def __init__(self, conf, arbiter):
        self.arbiter = arbiter
        #Pointer to the whole conf
        self.conf = conf
        self.realms = conf.realms
        #Direct pointer to importants elements for us
        self.arbiters = self.conf.arbiterlinks
        self.schedulers = self.conf.schedulerlinks
        self.reactionners = self.conf.reactionners
        self.brokers = self.conf.brokers
        self.receivers = self.conf.receivers
        self.pollers = self.conf.pollers
        self.dispatch_queue = { 'schedulers': [], 'reactionners': [],
                                'brokers': [], 'pollers': [] , 'receivers' : []}
        self.elements = [] #all elements, sched and satellites
        self.satellites = [] #only satellites not schedulers

        for cfg in self.conf.confs.values():
            cfg.is_assigned = False
            cfg.assigned_to = None

        #Add satellites in the good lists
        self.elements.extend(self.schedulers)

        #Others are in 2 lists
        self.elements.extend(self.reactionners)
        self.satellites.extend(self.reactionners)
        self.elements.extend(self.pollers)
        self.satellites.extend(self.pollers)
        self.elements.extend(self.brokers)
        self.satellites.extend(self.brokers)
        self.elements.extend(self.receivers)
        self.satellites.extend(self.receivers)

        #Some flag about dispatch need or not
        self.dispatch_ok = False
        self.first_dispatch_done = False


        #Prepare the satellites confs
        for satellite in self.satellites:
            satellite.prepare_for_conf()
            #print ""*5,satellite.get_name(), "Spare?", satellite.spare, "manage_sub_realms?", satellite.manage_sub_realms

        #Some properties must be give to satellites from global
        #configuration, like the max_plugins_output_length to pollers
        parameters = {'max_plugins_output_length' : self.conf.max_plugins_output_length}
        for poller in self.pollers:
            poller.add_global_conf_parameters(parameters)

        #Now realm will have a cfg pool for satellites
        for r in self.realms:
            r.prepare_for_satellites_conf()

        # Reset need_conf for all schedulers.
        for s in self.schedulers:
            s.need_conf = True

    #checks alive elements
    def check_alive(self):
        for elt in self.elements:
            elt.ping()
            #print "Element", elt.get_name(), " alive:", elt.alive, "

            #Not alive need new need_conf
            #and spare too if they do not have already a conf
            #REF: doc/shinken-scheduler-lost.png (1)
            if not elt.alive or hasattr(elt, 'conf') and elt.conf is None:
                elt.need_conf = True

        for arb in self.arbiters:
            #If not me...
            if arb != self.arbiter:
                arb.ping()
                #print "Arb", arb.get_name(), "alive?", arb.alive, arb.__dict__


    #Check if all active items are still alive
    #the result go into self.dispatch_ok
    #TODO : finish need conf
    def check_dispatch(self):
        #Check if the other arbiter have a conf
        for arb in self.arbiters:
            #If not me...
            if arb != self.arbiter:
                if not arb.have_conf(self.conf.magic_hash):
                    arb.put_conf(self.conf)
                else:
                    #Ok, he already have the conf. I remember him that
                    #he do not have to run, I'm stil alive!
                    arb.do_not_run()

        #We check for confs to be dispatched on alive scheds. If not dispatch, need dispatch :)
        #and if dipatch on a failed node, remove the association, and need a new disaptch
        for r in self.realms:
            for cfg_id in r.confs:
                sched = r.confs[cfg_id].assigned_to
                if sched is None:
                    if self.first_dispatch_done:
                        logger.log("Scheduler configuration %d is unmanaged!!" % cfg_id)
                    self.dispatch_ok = False
                else:
                    if not sched.alive:
                        self.dispatch_ok = False #so we ask a new dispatching
                        logger.log("Warning : Scheduler %s had the configuration %d but is dead, I am not happy." % (sched.get_name(), cfg_id))
                        sched.conf.assigned_to = None
                        sched.conf.is_assigned = False
                        sched.conf = None
                    #Else: ok the conf is managed by a living scheduler

        # Maybe satelite are alive, but do not still have a cfg but
        # I think so. It is not good. I ask a global redispatch for
        # the cfg_id I think is not corectly dispatched.
        for r in self.realms:
            for cfg_id in r.confs:
                try:
                    for kind in ( 'reactionner', 'poller', 'broker' ):
                        # We must have the good number of satellite or we are not happy
                        # So we are sure to raise a dispatch every loop a satellite is missing
                        if len(r.to_satellites_managed_by[kind][cfg_id]) < r.get_nb_of_must_have_satellites(kind):
                            logger.log("Warning : Missing satellite %s for configuration %d :" % (kind, cfg_id))

                            # TODO : less violent! Must resent to just who need?
                            # must be catch by satellite who see that it already have the conf (hash)
                            # and do nothing
                            self.dispatch_ok = False #so we will redispatch all
                            r.to_satellites_nb_assigned[kind][cfg_id] = 0
                            r.to_satellites_need_dispatch[kind][cfg_id]  = True
                            r.to_satellites_managed_by[kind][cfg_id] = []
                        for satellite in r.to_satellites_managed_by[kind][cfg_id]:
                            # Maybe the sat was mark not alive, but still in
                            # to_satellites_managed_by that mean that a new dispatch
                            # is need
                            # Or maybe it is alive but I thought that this reactionner manage the conf
                            # but ot doesn't. I ask a full redispatch of these cfg for both cases
                            # DBG:
                            try :
                                satellite.reachable and cfg_id not in satellite.what_i_managed()
                            except TypeError, exp:
                                print "DBG: ERROR: (%s) for satellite %s" % (exp, satellite.__dict__)
                                satellite.reachable = False

                            if not satellite.alive or (satellite.reachable and cfg_id not in satellite.what_i_managed()):
                                logger.log('[%s] Warning : The %s %s seems to be down, I must re-dispatch its role to someone else.' % (r.get_name(), kind, satellite.get_name()))
                                self.dispatch_ok = False #so we will redispatch all
                                r.to_satellites_nb_assigned[kind][cfg_id] = 0
                                r.to_satellites_need_dispatch[kind][cfg_id]  = True
                                r.to_satellites_managed_by[kind][cfg_id] = []
                # At the first pass, there is no cfg_id in to_satellites_managed_by
                except KeyError:
                    pass


    # Imagine a world where... oups...
    # Imagine a master got the conf, network down
    # a spare take it (good :) ). Like the Empire, the master
    # strike back! It was still alive! (like Elvis). It still got conf
    # and is running! not good!
    # Bad dispatch : a link that say have a conf but I do not allow this
    # so I ask it to wait a new conf and stop kidding.
    def check_bad_dispatch(self):
        for elt in self.elements:
            if hasattr(elt, 'conf'):
                # If element have a conf, I do not care, it's a good dispatch
                # If die : I do not ask it something, it won't respond..
                if elt.conf is None and elt.reachable:
                    # print "Ask", elt.get_name() , 'if it got conf'
                    if elt.have_conf():
                        logger.log('Warning : The element %s have a conf and should not have one! I ask it to idle now' % elt.get_name())
                        elt.active = False
                        elt.wait_new_conf()
                        # I do not care about order not send or not. If not,
                        # The next loop wil resent it
                    # else:
                    #    print "No conf"

        # I ask satellite witch sched_id they manage. If I am not agree, I ask
        # them to remove it
        for satellite in self.satellites:
            kind = satellite.get_my_type()
            if satellite.reachable:
                cfg_ids = satellite.what_i_managed()
                # I do nto care about satellites that do nothing, it already
                # do what I want :)
                if len(cfg_ids) != 0:
                    id_to_delete = []
                    for cfg_id in cfg_ids:
                        # DBG print kind, ":", satellite.get_name(), "manage cfg id:", cfg_id
                        # Ok, we search for realm that have the conf
                        for r in self.realms:
                            if cfg_id in r.confs:
                                # Ok we've got the realm, we check it's to_satellites_managed_by
                                # to see if reactionner is in. If not, we remove he sched_id for it
                                if not satellite in r.to_satellites_managed_by[kind][cfg_id]:
                                    id_to_delete.append(cfg_id)
                    # Maybe we removed all cfg_id of this reactionner
                    # We can make it idle, no active and wait_new_conf
                    if len(id_to_delete) == len(cfg_ids):
                        satellite.active = False
                        logger.log("I ask %s to wait a new conf" % satellite.get_name())
                        satellite.wait_new_conf()
                    else:#It is not fully idle, just less cfg
                        for id in id_to_delete:
                            logger.log("I ask to remove configuration N%d from %s" %(cfg_id, satellite.get_name()))
                            satellite.remove_from_conf(cfg_id)


    # Make a ORDERED list of schedulers so we can
    # send them conf in this order for a specific realm
    def get_scheduler_ordered_list(self, r):
        # get scheds, alive and no spare first
        scheds =  []
        for s in r.schedulers:
            scheds.append(s)

        # now the spare scheds of higher realms
        # they are after the sched of realm, so
        # they will be used after the spare of
        # the realm
        for higher_r in r.higher_realms:
            for s in higher_r.schedulers:
                if s.spare:
                    scheds.append(s)

        # Now we sort the scheds so we take master, then spare
        # the dead, but we do not care about thems
        scheds.sort(alive_then_spare_then_deads)
        scheds.reverse() #pop is last, I need first

        #DBG: dump
        print_sched = [s.get_name() for s in scheds]
        print_sched.reverse()
        print_string = '[%s] Schedulers order : ' % r.get_name()
        for s in print_sched:
            print_string += '%s ' % s
        logger.log(print_string)
        #END DBG

        return scheds


    # Manage the dispatch
    # REF: doc/shinken-conf-dispatching.png (3)
    def dispatch(self):
        # Ok, we pass at least one time in dispatch, so now errors are True errors
        self.first_dispatch_done = True

        # Is no need to dispatch, do not dispatch :)
        if not self.dispatch_ok:
            for r in self.realms:
                logger.log("Dispatching Realm %s" % r.get_name())
                conf_to_dispatch = [ cfg for cfg in r.confs.values() if not cfg.is_assigned ]
                nb_conf = len(conf_to_dispatch)
                logger.log('[%s] Dispatching %d/%d configurations' % (r.get_name(), nb_conf, len(r.confs)))

                # Now we get in scheds all scheduler of this realm and upper so
                # we will send them conf (in this order)
                scheds = self.get_scheduler_ordered_list(r)

                # Try to send only for alive members
                scheds = [ s for s in scheds if s.alive ]

                # Now we do the real job
                # every_one_need_conf = False
                for conf in conf_to_dispatch:
                    logger.log('[%s] Dispatching one configuration' % r.get_name())

                    # If there is no alive schedulers, not good...
                    if len(scheds) == 0:
                        logger.log('[%s] but there a no alive schedulers in this realm!' % r.get_name())

                    # we need to loop until the conf is assigned
                    # or when there are no more schedulers available
                    while True:
                        try:
                            sched = scheds.pop()
                        except IndexError: #No more schedulers.. not good, no loop
                            # need_loop = False
                            # The conf do not need to be dispatch
                            cfg_id = conf.id
                            for kind in ( 'reactionner', 'poller', 'broker' ):
                                r.to_satellites[kind][cfg_id] = None
                                r.to_satellites_nb_assigned[kind][cfg_id] = 0
                                r.to_satellites_need_dispatch[kind][cfg_id]  = False
                                r.to_satellites_managed_by[kind][cfg_id] = []
                            break
                        
                        logger.log('[%s] Trying to send conf %d to scheduler %s' % (r.get_name(), conf.id, sched.get_name()))
                        if not sched.need_conf:
                            logger.log('[%s] The scheduler %s do not need conf, sorry' % (r.get_name(), sched.get_name()))
                            continue
                        
                        #every_one_need_conf = True

                        # We tag conf with the instance_name = scheduler_name
                        conf.instance_name = sched.scheduler_name
                        # REF: doc/shinken-conf-dispatching.png (3)
                        # REF: doc/shinken-scheduler-lost.png (2)
                        override_conf = sched.get_override_configuration()
                        satellites_for_sched = r.get_satellites_links_for_scheduler()
                        print "Want to give a satellites pack for the scheduler", satellites_for_sched
                        conf_package = (conf, override_conf, sched.modules, satellites_for_sched)
                        print "Try to put the conf", conf_package
                        is_sent = sched.put_conf(conf_package)
                        if not is_sent:
                            logger.log('[%s] Warning : Dispatch fault for scheduler %s' %(r.get_name(), sched.get_name()))
                            continue
                        
                        logger.log('[%s] Dispatch OK of for conf in scheduler %s' % (r.get_name(), sched.get_name()))
                        sched.conf = conf
                        sched.need_conf = False
                        conf.is_assigned = True
                        conf.assigned_to = sched

                        # Now we generate the conf for satellites:
                        cfg_id = conf.id
                        for kind in ( 'reactionner', 'poller', 'broker' ):
                            r.to_satellites[kind][cfg_id] = sched.give_satellite_cfg()
                            r.to_satellites_nb_assigned[kind][cfg_id] = 0
                            r.to_satellites_need_dispatch[kind][cfg_id]  = True
                            r.to_satellites_managed_by[kind][cfg_id] = []

                        # Ok, the conf is dispatch, no more loop for this
                        # configuration
                        break

            # We pop conf to dispatch, so it must be no more conf...
            conf_to_dispatch = [ cfg for cfg in self.conf.confs.values() if not cfg.is_assigned ]
            nb_missed = len(conf_to_dispatch)
            if nb_missed > 0:
                logger.log("WARNING : All schedulers configurations are not dispatched, %d are missing" % nb_missed)
            else:
                logger.log("OK, all schedulers configurations are dispatched :)")
                self.dispatch_ok = True

            # Sched without conf in a dispatch ok are set to no need_conf
            # so they do not raise dispatch where no use
            if self.dispatch_ok:
                for sched in self.schedulers.items.values():
                    if sched.conf is None:
                        # print "Tagging sched", sched.get_name(), "so it do not ask anymore for conf"
                        sched.need_conf = False


            arbiters_cfg = {}
            for arb in self.arbiters:
                arbiters_cfg[arb.id] = arb.give_satellite_cfg()

            # We put the satellites conf with the "new" way so they see only what we want
            for r in self.realms:
                for cfg in r.confs.values():
                    cfg_id = cfg.id
                    for kind in ( 'reactionner', 'poller', 'broker' ):
                        if r.to_satellites_need_dispatch[kind][cfg_id]:
                            logger.log('[%s] Dispatching %s' % (r.get_name(),kind) + 's')
                            cfg_for_satellite_part = r.to_satellites[kind][cfg_id]
                            print "*"*10, "DBG: cfg_for_satellite_part", cfg_for_satellite_part, r.get_name(), cfg_id

                            # print "Sched Config part for ", kind+'s',":", cfg_for_satellite_part
                            # make copies of potential_react list for sort
                            satellites = []
                            for satellite in r.get_potential_satellites_by_type(kind):
                                satellites.append(satellite)
                            satellites.sort(alive_then_spare_then_deads)
                            satellite_string = "[%s] %s satellite order : " % (r.get_name(), kind)
                            for satellite in satellites:
                                satellite_string += '%s (spare:%s), ' % (satellite.get_name(), str(satellite.spare))

                            logger.log(satellite_string)

                            # Now we dispatch cfg to every one ask for it
                            nb_cfg_sent = 0
                            for satellite in satellites:
                                # Send only if we need, and if we can
                                if nb_cfg_sent < r.get_nb_of_must_have_satellites(kind) and satellite.alive:
                                    logger.log('[%s] Trying to send configuration to %s %s' %(r.get_name(), kind, satellite.get_name()))
                                    satellite.cfg['schedulers'][cfg_id] = cfg_for_satellite_part
                                    if satellite.manage_arbiters:
                                        satellite.cfg['arbiters'] = arbiters_cfg

                                    # Brokers should have poller/reactionners links too
                                    if kind == "broker":
                                        r.fill_broker_with_poller_reactionner_links(satellite)

                                    is_sent = satellite.put_conf(satellite.cfg)#_for_satellite)
                                    if is_sent:
                                        satellite.active = True
                                        logger.log('[%s] Dispatch OK of for configuration %s to %s %s' %(r.get_name(), cfg_id, kind, satellite.get_name()))
                                        nb_cfg_sent += 1
                                        r.to_satellites_managed_by[kind][cfg_id].append(satellite)
                            # else:
                            #    #I've got enouth satellite, the next one are spare for me
                            r.to_satellites_nb_assigned[kind][cfg_id] = nb_cfg_sent
                            if nb_cfg_sent == r.get_nb_of_must_have_satellites(kind):
                                logger.log("[%s] OK, no more %s sent need" % (r.get_name(), kind))
                                r.to_satellites_need_dispatch[kind][cfg_id]  = False
