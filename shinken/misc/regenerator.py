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

import time

# Import all obejcts we will need
from shinken.objects import Host, Hosts
from shinken.objects import Hostgroup, Hostgroups
from shinken.objects import Service, Services
from shinken.objects import Servicegroup, Servicegroups
from shinken.objects import Contact, Contacts
from shinken.objects import Contactgroup, Contactgroups
from shinken.objects import Timeperiod, Timeperiods
from shinken.objects import Command, Commands
from shinken.objects import Config
from shinken.schedulerlink import SchedulerLink, SchedulerLinks
from shinken.reactionnerlink import ReactionnerLink, ReactionnerLinks
from shinken.pollerlink import PollerLink, PollerLinks
from shinken.brokerlink import BrokerLink, BrokerLinks




# Class for a Regenerator. It will get broks, and "regenerate" real obejcts
# from them :)
class Regenerator:
    def __init__(self):

        # Our datas
        self.configs = {}
        self.hosts = Hosts([])
        self.services = Services([])
        self.contacts = Contacts([])
        self.hostgroups = Hostgroups([])
        self.servicegroups = Servicegroups([])
        self.contactgroups = Contactgroups([])
        self.timeperiods = Timeperiods([])
        self.commands = Commands([])

        # Now satellites
        self.schedulers = SchedulerLinks([])
        self.pollers = PollerLinks([])
        self.reactionners = ReactionnerLinks([])
        self.brokers = BrokerLinks([])
        
        self.last_need_data_send = time.time()


    def manage_program_status_brok(self, b):
        data = b.data
        c_id = data['instance_id']
        print "Creating config:", c_id, data
        c = Config()
        for prop in data:
            setattr(c, prop, data[prop])
        #print "CFG:", c
        self.configs[0] = c
        # And we save that we got data from this instance_id
        self.instance_ids.append(c_id)

        # We should clean all previously added hosts and services
        inst_id = data['instance_id']
        to_del = []
        to_del_srv = []
        for h in self.hosts.values():
            # If the host was in this instance, del it
            if h.instance_id == inst_id:
                to_del.append(h.host_name)

                
        for s in self.services.values():
            if s.instance_id == inst_id:
                to_del_srv.append(s.host_name + s.service_description)

        # Now clean hostgroups too
        for hg in self.hostgroups.values():
            print "Len before exclude", len(hg.members)
            # Exclude from members the hosts with this inst_id
            hg.members = [h for h in hg.members if h.instance_id != inst_id]
            print "Len after", len(hg.members)

        # Now clean service groups
        for sg in self.servicegroups.values():
            sg.members = [s for s in sg.members if s.instance_id != inst_id]

        # Ok, really clean the hosts
        for i in to_del:
            try:
                del self.hosts[i]
            except KeyError: # maybe it was not inserted in a good way, pass it
                pass

        # And services
        for i in to_del_srv:
            try:
                del self.services[i]
            except KeyError: # maybe it was not inserted in a good way, pass it
                pass



    def manage_update_program_status_brok(self, b):
        data = b.data
        c_id = data['instance_id']

        if c_id not in self.instance_ids:
            # Do not ask data too quickly, very dangerous
            # one a minute
            if time.time() - self.last_need_data_send > 60:
                print "I ask the broker for instance id data :", c_id
                msg = Message(id=0, type='NeedData', data={'full_instance_id' : c_id})
                self.from_q.put(msg)
                self.last_need_data_send = time.time()
            return

        # We have only one config here, with id 0
        c = self.configs[0]
        self.update_element(c, data)
    

    def set_schedulingitem_values(self, i):
        i.check_period = self.get_timeperiod(i.check_period)
        i.notification_period = self.get_timeperiod(i.notification_period)
        i.contacts = self.get_contacts(i.contacts)
        i.rebuild_ref()
        #Escalations is not use for status_dat
        del i.escalations
        

    def manage_initial_host_status_brok(self, b):
        data = b.data
        
        host_name = data['host_name']
        inst_id = data['instance_id']
        #print "Creating host:", h_id, b
        h = Host({})
        self.update_element(h, data)        
        self.set_schedulingitem_values(h)
        
        h.service_ids = []
        h.services = []
        h.instance_id = inst_id
        # We need to rebuild Downtime and Comment relationship
        for dtc in h.downtimes + h.comments:
            dtc.ref = h
        self.hosts[host_name] = h
        self.number_of_objects += 1


    #In fact, an update of a host is like a check return
    def manage_update_host_status_brok(self, b):
        self.manage_host_check_result_brok(b)
        data = b.data
        host_name = data['host_name']
        #In the status, we've got duplicated item, we must relink thems
        try:
            h = self.hosts[host_name]
        except KeyError:
            print "Warning : the host %s is unknown!" % host_name
            return
        self.update_element(h, data)
        self.set_schedulingitem_values(h)
        for dtc in h.downtimes + h.comments:
            dtc.ref = h
        self.livestatus.count_event('host_checks')


    def manage_initial_hostgroup_status_brok(self, b):
        data = b.data
        hostgroup_name = data['hostgroup_name']
        members = data['members']
        del data['members']
        
        # Maybe we already got this hostgroup. If so, use the existing object
        # because in different instance, we will ahve the same group with different
        # elements
        try:
            hg = self.hostgroups[hostgroup_name]
        except KeyError:
            # If we got none, create a new one
            #print "Creating hostgroup:", hg_id, data
            hg = Hostgroup()
            # Set by default members to a void list
            setattr(hg, 'members', [])

        self.update_element(hg, data)

        for (h_id, h_name) in members:
            if h_name in self.hosts:
                hg.members.append(self.hosts[h_name])
                # Should got uniq value, do uniq this list
                hg.members = list(set(hg.members))

        #print "HG:", hg
        self.hostgroups[hostgroup_name] = hg
        self.number_of_objects += 1


    def manage_initial_service_status_brok(self, b):
        data = b.data
        s_id = data['id']
        host_name = data['host_name']
        service_description = data['service_description']
        inst_id = data['instance_id']
        
        #print "Creating Service:", s_id, data
        s = Service({})
        s.instance_id = inst_id

        self.update_element(s, data)
        self.set_schedulingitem_values(s)
        
        try:
            h = self.hosts[host_name]
            # Reconstruct the connection between hosts and services
            h.services.append(s)
            # There is already a s.host_name, but a reference to the h object can be useful too
            s.host = h
        except Exception:
            return
        for dtc in s.downtimes + s.comments:
            dtc.ref = s
        self.services[host_name+service_description] = s
        self.number_of_objects += 1
        # We need this for manage_initial_servicegroup_status_brok where it
        # will speed things up dramatically
        self.service_id_cache[s.id] = s


    #In fact, an update of a service is like a check return
    def manage_update_service_status_brok(self, b):
        self.manage_service_check_result_brok(b)
        data = b.data
        host_name = data['host_name']
        service_description = data['service_description']
        #In the status, we've got duplicated item, we must relink thems
        try:
            s = self.services[host_name+service_description]
        except KeyError:
            print "Warning : the service %s/%s is unknown!" % (host_name, service_description)
            return
        self.update_element(s, data)
        self.set_schedulingitem_values(s)
        for dtc in s.downtimes + s.comments:
            dtc.ref = s
        self.livestatus.count_event('service_checks')
   


    def manage_initial_servicegroup_status_brok(self, b):
        data = b.data
        sg_id = data['id']
        servicegroup_name = data['servicegroup_name']
        members = data['members']
        del data['members']

        # Like for hostgroups, maybe we already got this
        # service group from another instance, need to
        # factorize all
        try:
            sg = self.servicegroups[servicegroup_name]
        except KeyError:
            #print "Creating servicegroup:", sg_id, data
            sg = Servicegroup()
            # By default set members as a void list
            setattr(sg, 'members', [])

        self.update_element(sg, data)

        for (s_id, s_name) in members:
            # A direct lookup by s_host_name+s_name is not possible
            # because we don't have the host_name in members, only ids.
            try:
                sg.members.append(self.service_id_cache[s_id])
            except Exception:
                pass

        sg.members = list(set(sg.members))
        self.servicegroups[servicegroup_name] = sg
        self.number_of_objects += 1


    def manage_initial_contact_status_brok(self, b):
        data = b.data
        contact_name = data['contact_name']
        #print "Creating Contact:", c_id, data
        c = Contact({})
        self.update_element(c, data)
        #print "C:", c
        self.contacts[contact_name] = c
        self.number_of_objects += 1


    def manage_initial_contactgroup_status_brok(self, b):
        data = b.data
        contactgroup_name = data['contactgroup_name']
        members = data['members']
        del data['members']
        #print "Creating contactgroup:", cg_id, data
        cg = Contactgroup()
        self.update_element(cg, data)
        setattr(cg, 'members', [])
        for (c_id, c_name) in members:
            if c_name in self.contacts:
                cg.members.append(self.contacts[c_name])
        #print "CG:", cg
        self.contactgroups[contactgroup_name] = cg
        self.number_of_objects += 1


    def manage_initial_timeperiod_status_brok(self, b):
        data = b.data
        timeperiod_name = data['timeperiod_name']
        #print "Creating Timeperiod:", tp_id, data
        tp = Timeperiod({})
        self.update_element(tp, data)
        #print "TP:", tp
        self.timeperiods[timeperiod_name] = tp
        self.number_of_objects += 1


    def manage_initial_command_status_brok(self, b):
        data = b.data
        command_name = data['command_name']
        #print "Creating Command:", c_id, data
        c = Command({})
        self.update_element(c, data)
        #print "CMD:", c
        self.commands[command_name] = c
        self.number_of_objects += 1


    def manage_initial_scheduler_status_brok(self, b):
        data = b.data
        scheduler_name = data['scheduler_name']
        print "Creating Scheduler:", scheduler_name, data
        sched = SchedulerLink({})
        print "Created a new scheduler", sched
        self.update_element(sched, data)
        print "Updated scheduler"
        #print "CMD:", c
        self.schedulers[scheduler_name] = sched
        print "scheduler added"
        #print "MONCUL: Add a new scheduler ", sched
        self.number_of_objects += 1


    def manage_update_scheduler_status_brok(self, b):
        data = b.data
        scheduler_name = data['scheduler_name']
        try:
            s = self.schedulers[scheduler_name]
            self.update_element(s, data)
            #print "S:", s
        except Exception:
            pass


    def manage_initial_poller_status_brok(self, b):
        data = b.data
        poller_name = data['poller_name']
        print "Creating Poller:", poller_name, data
        poller = PollerLink({})
        print "Created a new poller", poller
        self.update_element(poller, data)
        print "Updated poller"
        #print "CMD:", c
        self.pollers[poller_name] = poller
        print "poller added"
        #print "MONCUL: Add a new scheduler ", sched
        self.number_of_objects += 1


    def manage_update_poller_status_brok(self, b):
        data = b.data
        poller_name = data['poller_name']
        try:
            s = self.pollers[poller_name]
            self.update_element(s, data)
        except Exception:
            pass


    def manage_initial_reactionner_status_brok(self, b):
        data = b.data
        reactionner_name = data['reactionner_name']
        print "Creating Reactionner:", reactionner_name, data
        reac = ReactionnerLink({})
        print "Created a new reactionner", reac
        self.update_element(reac, data)
        print "Updated reactionner"
        #print "CMD:", c
        self.reactionners[reactionner_name] = reac
        print "reactionner added"
        #print "MONCUL: Add a new scheduler ", sched
        self.number_of_objects += 1


    def manage_update_reactionner_status_brok(self, b):
        data = b.data
        reactionner_name = data['reactionner_name']
        try:
            s = self.reactionners[reactionner_name]
            self.update_element(s, data)
        except Exception:
            pass


    def manage_initial_broker_status_brok(self, b):
        data = b.data
        broker_name = data['broker_name']
        print "Creating Broker:", broker_name, data
        broker = BrokerLink({})
        print "Created a new broker", broker
        self.update_element(broker, data)
        print "Updated broker"
        #print "CMD:", c
        self.brokers[broker_name] = broker
        print "broker added"
        #print "MONCUL: Add a new scheduler ", sched
        self.number_of_objects += 1


    def manage_update_broker_status_brok(self, b):
        data = b.data
        broker_name = data['broker_name']
        try:
            s = self.brokers[broker_name]
            self.update_element(s, data)
        except Exception:
            pass


    #A service check have just arrived, we UPDATE data info with this
    def manage_service_check_result_brok(self, b):
        data = b.data
        host_name = data['host_name']
        service_description = data['service_description']
        try:
            s = self.services[host_name+service_description]
            self.update_element(s, data)
        except Exception:
            pass


    #A service check update have just arrived, we UPDATE data info with this
    def manage_service_next_schedule_brok(self, b):
        self.manage_service_check_result_brok(b)


    def manage_host_check_result_brok(self, b):
        data = b.data
        host_name = data['host_name']
        try:
            h = self.hosts[host_name]
            self.update_element(h, data)
        except Exception:
            pass


    # this brok should arrive within a second after the host_check_result_brok
    def manage_host_next_schedule_brok(self, b):
        self.manage_host_check_result_brok(b)

