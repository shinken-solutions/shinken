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



print "I am NDO Broker"


class Ndodb_broker:
    def __init__(self):
        pass

    #The classic has : do we have a prop or not?
    def has(self, prop):
        return hasattr(self, prop)


    def init(self):
        print "I do nothing, thanks"
    

    #Get a brok, parse it, and return the query for database
    def manage_initial_servicegroup_status_brok(self, b):
        print "(NDO)You call me? WHAT AN HONNOR! REALLY!"


    #Get a brok, parse it, and put in in database
    #We call functions like manage_ TYPEOFBROK _brok that return us queries
    def manage_brok(self, b):
        return
        type = b.type
        manager = 'manage_'+type+'_brok'
		
        if self.has(manager):
            f = getattr(self, manager)
            queries = f(b)
            for q in queries :
                self.execute_query(q)
            return
        print "(ndodb)I don't manage this brok type", b


def get_broker():
    broker = Ndodb_broker()
    return broker
