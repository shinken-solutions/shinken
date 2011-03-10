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


#This text is print at the import
print "I am Ndo Mysql Broker"


properties = {
    'daemons' : ['broker'],
    'type' : 'ndodb_mysql',
    'phases' : ['running'],
    }


#called by the plugin manager to get a instance
def get_instance(mod_conf):

    print "Get a ndoDB instance for plugin %s" % mod_conf.get_name()

    #First try to import
    try:
        from ndodb_broker import Ndodb_broker
    except ImportError , exp:
        print "Warning : the plugin type %s is unavalable : %s" % ('ndo_mysql', exp)
        return None

    if not hasattr( mod_conf, 'character_set'):
        mod_conf.character_set = 'utf8'
    instance = Ndodb_broker(mod_conf)
    return instance
