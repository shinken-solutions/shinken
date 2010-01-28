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


#This Class is a plugin for the Shinken Broker. It is in charge
#to brok information of the service perfdata into the file
#var/service-perfdata
#So it just manage the service_check_return
#Maybe one day host data will be usefull too
#It will need just a new file, and a new manager :)

import time

from host import Host
from service import Service
from contact import Contact
from status import StatusFile
from objectscache import ObjectsCacheFile



#Class for the Merlindb Broker
#Get broks and puts them in merlin database
class Status_dat_broker:
    def __init__(self, name, path, opath, update_interval):
        self.path = path
        self.opath = opath
        self.name = name
        self.update_interval = update_interval
        
        #Warning :
        #self.properties will be add by the modulesmanager !!
        

    #Called by Broker so we can do init stuff
    #TODO : add conf param to get pass with init
    #Conf from arbiter!
    def init(self):
        print "I am init"
        self.q = self.properties['to_queue']
    
        #Our datas
        self.hosts = {}
        self.services = {}
        self.contacts = {}

        self.status = StatusFile(self.path, self.hosts, self.services, self.contacts)
        self.objects_cache = ObjectsCacheFile(self.opath, self.hosts, self.services, self.contacts)
    

    def is_external(self):
        return True


    def get_name(self):
        return self.name


    #Get a brok, parse it, and put in in database
    #We call functions like manage_ TYPEOFBROK _brok that return us queries
    def manage_brok(self, b):
        type = b.type
        manager = 'manage_'+type+'_brok'
        if hasattr(self, manager):
            f = getattr(self, manager)
            f(b)


    def manage_program_status_brok(self, b):
        pass


    #A service check have just arrived, we UPDATE data info with this
    def manage_initial_host_status_brok(self, b):
        data = b.data
        h_id = data['id']
        #print "Creating host:", h_id, data
        h = Host({})
        for prop in data:
            setattr(h, prop, data[prop])
        #print "H:", h
        self.hosts[h_id] = h


    #A service check have just arrived, we UPDATE data info with this
    def manage_initial_service_status_brok(self, b):
        data = b.data
        s_id = data['id']
        #print "Creating Service:", s_id, data
        s = Service({})
        self.update_element(s, data)
        #print "S:", s
        self.services[s_id] = s


    #A service check have just arrived, we UPDATE data info with this
    def manage_initial_contact_status_brok(self, b):
        data = b.data
        c_id = data['id']
        #print "Creating Contact:", c_id, data
        c = Contact({})
        self.update_element(c, data)
        #print "C:", c
        self.contacts[c_id] = c



    def manage_service_check_result_brok(self, b):
        data = b.data
        s = self.find_service(data['host_name'], data['service_description'])
        if s != None:
            self.update_element(s, data)
            #print "S:", s


    #In fact, an update of a service is like a check return
    def manage_update_service_status_brok(self, b):
        self.manage_service_check_result_brok(b)


    def manage_host_check_result_brok(self, b):
        data = b.data
        h = self.find_host(data['host_name'])
        if h != None:
            self.update_element(h, data)
            #print "H:", h


    #In fact, an update of a service is like a check return
    def manage_update_host_status_brok(self, b):
        self.manage_host_check_result_brok(b)



    def find_host(self, host_name):
        for h in self.hosts.values():
            if h.host_name == host_name:
                return h
        return None


    def find_service(self, host_name, service_description):
        for s in self.services.values():
            if s.host_name == host_name and s.service_description == service_description:
                return s
        return None

        
    def update_element(self, e, data):
        for prop in data:
            setattr(e, prop, data[prop])


    def main(self):
        last_generation = time.time()
        objects_cache_written = False
        while True:
            b = self.q.get() # can block here :)
            self.manage_brok(b)
            
            if time.time() - last_generation > self.update_interval:
                if not objects_cache_written:
                    self.objects_cache.create_or_update()
                    objects_cache_written = True
                print "Generating status file!"
                r = self.status.create_or_update()
                #if we get an error (an exception in fact) we bail out
                if r != None:
                    print "[status_dat] Error :", r
                    break
                last_generation = time.time()
            

