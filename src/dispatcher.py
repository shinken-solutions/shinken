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


#This is the class of the dispatcher. It's role is to dispatch 
#configurations to other elements like schedulers, reactionner, 
#pollers and brokers. It is responsible for hight avaibility part. If an
#element die and the element type have a spare, it send the confi of the 
#dead to the spare


import Pyro.core

from util import scheduler_no_spare_first, alive_then_spare_then_deads


#Dispatcher Class
class Dispatcher:
    #Load all elements, set them no assigned
    # and add them to elements, so loop will be easier :)
    def __init__(self, conf):
        #Pointer to the whole conf
        self.conf = conf
        self.realms = conf.realms
        #Direct pointer to importants elements for us
        self.schedulers = self.conf.schedulerlinks
        self.reactionners = self.conf.reactionners
        self.brokers = self.conf.brokers
        self.pollers = self.conf.pollers
        self.dispatch_queue = {'schedulers' : [], 'reactionners' : [],
                               'brokers' : [], 'pollers' : []}
        self.elements = []
        for cfg in self.conf.confs.values():
            cfg.is_assigned = False
            cfg.assigned_to = None
            #self.elements.append(cfg)
        for sched in self.schedulers:
            sched.is_active = False
            sched.alive = False
            sched.conf = None
            sched.need_conf = True
            self.elements.append(sched)
        for reactionner in self.reactionners:
            reactionner.is_active = False
            reactionner.alive = False
            reactionner.need_conf = False
            self.elements.append(reactionner)
        for poller in self.pollers:
            poller.is_active = False
            poller.alive = False
            poller.need_conf = True
            self.elements.append(poller)
        for broker in self.brokers:
            broker.is_active = False
            broker.alive = False
            broker.need_conf = True
            self.elements.append(broker)
        self.dispatch_ok = False
        self.first_dispatch_done = False


        #Prepare the reactionners confs
        for reactionner in self.reactionners:
            reactionner.cfg = {'schedulers' : {}} #i : {'port' : sched.port, 'address' : sched.address, 'name' : sched.name, 'instance_id' : sched.id, 'active' : sched.conf!=None}

        #Now realm will have a cfg pool for reactionners
        for r in self.realms:
            r.to_reactionners = {}
            r.to_reactionners_nb_assigned = {}
            r.to_reactionners_need_dispatch = {}
            r.to_reactionners_managed_by = {}
            r.count_reactionners()
            r.fill_potential_reactionners()

    #checks alive elements
    def check_alive(self):
        for elt in self.elements:
            elt.alive = elt.is_alive()
            print "Element", elt.name, " alive:", elt.alive, ", active:", elt.is_active
            #Not alive need new need_conf
            #and spare too if they do not have already a conf
            if not elt.alive or hasattr(elt, 'conf') and elt.conf == None:
                elt.need_conf = True


    #Check if all active items are still alive
    #the result go into self.dispatch_ok
    #TODO : finish need conf
    def check_dispatch(self):
        #TODO: sup this loop and use the 2 loops below. It's far more readable to thinks
        #about conf dispatch and not by node dead -> cfg unavalable. So after the active
        #tag will no be usefull anymore I think.
        for elt in self.elements:
            #skip sched because it is managed by the new way
            if not hasattr(elt, 'conf'):
                if (elt.is_active and not elt.alive):
                    print "ELT:", elt.name, elt.is_active, elt.alive, elt.need_conf
                    self.dispatch_ok = False
                    print "Set dispatch False"
                    elt.is_active = False
                    if hasattr(elt, 'conf'):
                        if elt.conf != None:
                            elt.conf.assigned_to = None
                            elt.conf.is_assigned = False
                            elt.conf = None
                    else:
                        print 'No conf'

        #We check for confs to be dispatched on alive scheds. If not dispatch, need dispatch :)
        #and if dipatch on a failed node, remove the association, and need a new disaptch
        for r in self.realms:
            for cfg_id in r.confs:
                sched = r.confs[cfg_id].assigned_to
                if sched == None:
                    print "CFG", cfg_id, "is unmanaged!!"
                    self.dispatch_ok = False
                else:
                    if not sched.alive:
                        self.dispatch_ok = False #so we ask a new dispatching
                        print "Sched", sched.name, "had the conf", cfg_id, "but is dead, I am not happy!"
                        sched.conf.assigned_to = None
                        sched.conf.is_assigned = False
                        sched.conf = None
                    #Else: ok the conf is managed by a living scheduler

        #Maybe satelite are alive, but do not still have a cfg but
        #I think so. It is not good. I ask a global redispatch for
        #the cfg_id I think is not corectly dispatched.
        for r in self.realms:
            for cfg_id in r.confs:
                #DBG
                sched = r.confs[cfg_id].assigned_to
                if sched != None:
                    print "CFG", cfg_id, "is managed by", sched.get_name()
                else:
                    print "CFG", cfg_id, "is unmanaged!!"
                #END DBG
                try:
                    for reactionner in r.to_reactionners_managed_by[cfg_id]:
                    #Fu%k. I thought that this reactionner manage it
                    #but ot doesn't. I ask a full redispatch of these cfg
                        if reactionner.alive and cfg_id not in reactionner.what_i_managed():
                            self.dispatch_ok = False #so we will redispatch all
                            r.to_reactionners_nb_assigned[cfg_id] = 0
                            r.to_reactionners_need_dispatch[cfg_id]  = True
                            r.to_reactionners_managed_by[cfg_id] = []
                #At the first pass, there is no cfg_id in to_reactionners_managed_by
                except KeyError:
                    pass


    #Imagine a world where... oups...
    #Imagine a master got the conf, network down
    #a spare take it (good :) ). Like the Empire, the master
    #strike back! It was still alive! (like Elvis). It still got conf
    #and is running! not good!
    #Bad dispatch : a link that say have a conf but I do not allow this
    #so I ask it to wait a new conf and stop kidding.
    def check_bad_dispatch(self):
        for elt in self.elements:
            if hasattr(elt, 'conf'):
                #If element have a conf, I do not care, it's a good dispatch
                #If die : I do not ask it something, it won't respond..
                if elt.conf == None and elt.alive:
                    print "Ask", elt.name , 'if it got conf'
                    if elt.have_conf():
                        print 'True!'
                        elt.active = False
                        elt.wait_new_conf()
                        #I do not care about order not send or not. If not,
                        #The next loop wil resent it
                    else:
                        print "No conf"
        
        #I ask satellite witch sched_id they manage. If I am not agree, I ask
        #them to remove it
        for reactionner in self.reactionners:
            if reactionner.alive:
                cfg_ids = reactionner.what_i_managed()
                id_to_delete = []
                for cfg_id in cfg_ids:
                    print "Reactionner", reactionner.name, "manage cfg id:", cfg_id
                #Ok, we search for realm that have the conf
                    for r in self.realms:
                        if cfg_id in r.confs:
                        #Ok we've got the realm, we check it's to_reactionners_managed_by
                        #to see if reactionner is in. If not, we remove he sched_id for it
                            if not reactionner in r.to_reactionners_managed_by[cfg_id]:
                                id_to_delete.append(cfg_id)
            #Maybe we removed all cfg_id of this reactionner
            #We can make it idle, no active and wait_new_conf
                if len(id_to_delete) == len(cfg_ids):
                    reactionner.active = False
                    reactionner.wait_new_conf()
                else:#It is not fully idle, just less cfg
                    for id in id_to_delete:
                        print "I ask to remove cfg", cfg_id, "from", reactionner.name
                        reactionner.remove_from_conf(cfg_id)
    

    #Manage the dispatch
    def dispatch(self):
        #Is no need to dispatch, do not dispatch :)
        if not self.dispatch_ok:
            for r in self.realms:
                print "Dispatching Realm", r.get_name()
                conf_to_dispatch = [cfg for cfg in r.confs.values() if cfg.is_assigned==False]
                nb_conf = len(conf_to_dispatch)
                print '[',r.get_name(),']','Dispatching ', nb_conf, '/', len(r.confs), 'cfgs'
                #get scheds, alive and no spare first
                scheds =  []
                for s in r.schedulers:
                    scheds.append(s)
                #now the spare scheds of higher realms
                #they are after the sched of realm, so
                #they will be used after the spare of
                #the realm
                for higher_r in r.higher_realms:
                    for s in higher_r.schedulers:
                        if s.spare:
                            scheds.append(s)
                #Now we sort the scheds so we take master, then spare
                #the dead, but we do not care about thems
                scheds.sort(alive_then_spare_then_deads)
                scheds.reverse() #pop is last, I need first
                #DBG: dump
                for s in scheds:
                    print '[',r.get_name(),']',"Sched:",s.get_name()

                #Now we do the job
                every_one_need_conf = False
                for conf in conf_to_dispatch:
                    print '[',r.get_name(),']',"Dispatching one configuration"
                    #we need to loop until the conf is assigned
                    #or when there are no more schedulers available
                    need_loop = True
                    while need_loop:
                        try:
                            sched = scheds.pop()
                            print '[',r.get_name(),']',"Trying to send conf to sched", sched.name
                            if sched.need_conf:
                                every_one_need_conf = True
                                print '[',r.get_name(),']',"Dispatching conf", sched.id
                                is_sent = sched.put_conf(conf)
                                if is_sent:
                                    print '[',r.get_name(),']',"Dispatch OK of for conf in sched", sched.name
                                    sched.conf = conf
                                    sched.need_conf = False
                                    sched.is_active = True
                                    conf.is_assigned = True
                                    conf.assigned_to = sched
                                    #Ok, the conf is dispatch, no more loop for this
                                    #configuration
                                    need_loop = False
                                    
                                    #Now we generate the conf for reactionners:
                                    cfg_id = conf.id
                                    r.to_reactionners[cfg_id] = sched.give_satellite_cfg()
                                    r.to_reactionners_nb_assigned[cfg_id] = 0
                                    r.to_reactionners_need_dispatch[cfg_id]  = True
                                    r.to_reactionners_managed_by[cfg_id] = []
                                    print "Now to_reactionners:", r.nb_reactionners
                                    print r.to_reactionners
                                    print r.to_reactionners_nb_assigned
                                    print r.to_reactionners_need_dispatch
                                else:
                                    print '[',r.get_name(),']', "Dispatch fault for sched", sched.name
                            else:
                                print '[',r.get_name(),']',sched.name, "do not need conf, sorry"
                        except IndexError: #No more schedulers.. not good, no loop
                            need_loop = False

            #We pop conf to dispatch, so it must be no more conf...
            conf_to_dispatch = [cfg for cfg in self.conf.confs.values() if cfg.is_assigned==False]
            nb_missed = len(conf_to_dispatch)
            if nb_missed > 0:
                print "WARNING : All configurations are not dispatched ", nb_missed, "are missing"
            else:
                print "OK, all configurations are dispatched to schedulers :)"
                self.dispatch_ok = True
            
            #Sched without conf in a dispatch ok are set to no need_conf
            #so they do not raise dispatch where no use
            if self.dispatch_ok:
                for sched in self.schedulers.items.values():
                    if sched.conf == None:
                        print "Tagging sched", sched.get_name(), "so it do not ask anymore for conf"
                        sched.need_conf = False
            

            #We put the reactionners conf with the new way
            for r in self.realms:
                for cfg in r.confs.values():
                    cfg_id = cfg.id
                    if r.to_reactionners_need_dispatch[cfg_id]:
                        print "Dispatching", r.get_name(), "reactionners"
                        cfg_for_reactionner_part = r.to_reactionners[cfg_id]
                        cfg_for_reactionner = {'schedulers' : {cfg_id : cfg_for_reactionner_part}}
                        print "Config for reactionners:", cfg_for_reactionner
                        #make copies of potential_react lsit because we will pop items
                        reactionners = []
                        for reactionner in r.potential_reactionners:
                            reactionners.append(reactionner)
                        reactionners.sort(alive_then_spare_then_deads)
                        print "Order:"
                        for reactionner in reactionners:
                            print reactionner.name, ": is sprare?", reactionner.spare

                        #Now we dispatch cfg to evry one ask for it
                        nb_cfg_sent = 0
                        for reactionner in reactionners:
                            if nb_cfg_sent < r.nb_reactionners:
                                print '[',r.get_name(),']',"Trying to send conf to reactionner", reactionner.name
                                is_sent = reactionner.put_conf(cfg_for_reactionner)
                                if is_sent:
                                    reactionner.need_conf = False
                                    reactionner.active = True
                                    print '[',r.get_name(),']',"Dispatch OK of for conf", cfg_id," in reactionner", reactionner.name
                                    nb_cfg_sent += 1
                                    r.to_reactionners_managed_by[cfg_id].append(reactionner)
                            #else:
                            #    #I've got enouth reactionner, the next one are spare for me
                            #    print "Need to remove cfg", cfg_id, "from", reactionner.name
                            #    reactionner.remove_from_conf(cfg_id)
                        r.to_reactionners_nb_assigned[cfg_id] = nb_cfg_sent
                        if nb_cfg_sent == r.nb_reactionners:
                            print "OK, no more reactionner sent need"
                            r.to_reactionners_need_dispatch[cfg_id]  = False
                            

            #We put on the satellites only if every one need it 
            #(a new scheduler)
            #Of if a specific satellite needs it
            #TODO : more python
            #We create the conf for satellites : it's just schedulers
            tmp_conf = {}
            tmp_conf['schedulers'] = {}
            i = 0
            for sched in self.schedulers:
                tmp_conf['schedulers'][i] = {'port' : sched.port, 'address' : sched.address, 'name' : sched.name, 'instance_id' : sched.id, 'active' : sched.conf!=None}
                i += 1
            
            for broker in self.conf.brokers.items.values():
                if broker.alive:
                    if every_one_need_conf or broker.need_conf:
			print "Putting a Broker conf"
                        is_sent = broker.put_conf(tmp_conf)
                        if is_sent:
                            broker.is_active = True
                            broker.need_conf = False
            
            for poller in self.conf.pollers.items.values():
                if poller.alive:
                    if every_one_need_conf or poller.need_conf:
                        print "Putting a Poller conf"
                        is_sent = poller.put_conf(tmp_conf)
                        if is_sent:
                            poller.is_active = True
                            poller.need_conf = False

