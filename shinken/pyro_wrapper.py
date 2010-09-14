#!/usr/bin/env python
#Copyright (C) 2009-2010 : 
#    Gabes Jean, naparuba@gmail.com 
#    Gerhard Lausser, Gerhard.Lausser@consol.de
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


#This class is a wrapper for managing Pyro 3 and 4 version


import sys
import Pyro.core



#Try to see if we are Python 3 or 4
try:
    Pyro.core.ObjBase
    #Some one already go here, so we are in 4 if None
    if Pyro.core.ObjBase == None:
        raise AttributeError
    print "Using Pyro 3"
    pyro_version = 3
    protocol = 'PYROLOC'
    Pyro.errors.CommunicationError = Pyro.errors.ProtocolError
except AttributeError:
    print "Using Pyro 4"
    pyro_version = 4
    #Ok, in Pyro 4, interface do not need to
    #inherit from ObjBase, just object is good
    Pyro.core.ObjBase = object
    Pyro.errors.URIError = Pyro.errors.ProtocolError
    protocol = 'PYRO'
    Pyro.core.getProxyForURI = Pyro.core.Proxy
    #Hack for Pyro 4 : with it, there is 
    #no more way to send huge packet!
    import socket
    if hasattr(socket, 'MSG_WAITALL'):
        del socket.MSG_WAITALL


#Registering an object as an interface change between Pyro 3 and 4
#So this function know which one call
def register(daemon, obj, name):
    global pyro_version
    if pyro_version == 3:
        return daemon.connect(obj, name)
    else:
        return daemon.register(obj, name)


#Same that upper, but for deregister
def unregister(daemon, obj):
    global pyro_version
    if pyro_version == 3:
        daemon.disconnect(obj)
    else:
        daemon.unregister(obj)

#The method to get sockets are differents too
def get_sockets(daemon):
    global pyro_version
    if pyro_version == 3:
        return daemon.getServerSockets()
    else:
        return daemon.sockets()


#The method handleRequests take none in 3
#but [s] in 4
def handleRequests(daemon, s):
    global pyro_version
    if pyro_version == 3:
        daemon.handleRequests()
    else:
        daemon.handleRequests([s])

#The way we init daemons in 3 and 4 change
#So return the daemon in the good mode here
def init_daemon(host, port):
    global pyro_version
    if pyro_version == 3:
        Pyro.core.initServer()
        daemon = Pyro.core.Daemon(host=host, port=port)
        if daemon.port != port:
            print "Sorry, the port %d is not free" % port
            sys.exit(1)
    else:
        #Pyro 4 i by default thread, should do select
        #(I hate threads!)
        Pyro.config.SERVERTYPE="select"
        #And port already use now raise an exception
        try:
            daemon = Pyro.core.Daemon(host=host, port=port)
        except socket.error, exp:
            print "Sorry, the port %d is not free : %s" % (port, str(exp))
            sys.exit(1)
    return daemon


#Generate a URI with the good form
#for 3 and 4 version of Pyro
def create_uri(address, port, obj_name):
    global pyro_version
    if pyro_version == 3:
        return "PYROLOC://%s:%d/%s" % (address, port, obj_name)
    else:
        return "PYRO:%s@%s:%d" % (obj_name, address, port)


#Timeout way is also changed between 3 and 4
#it's a method in 3, a property in 4
def set_timeout(con, timeout):
    global pyro_version
    if pyro_version == 3:
        con._setTimeout(timeout)
    else:
        con._pyroTimeout = timeout

