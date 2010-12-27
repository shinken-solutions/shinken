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
    print "Using Pyro", Pyro.constants.VERSION
    pyro_version = 3
    protocol = 'PYROLOC'
    Pyro.errors.CommunicationError = Pyro.errors.ProtocolError


    def register(daemon, obj, name):
        return daemon.connect(obj, name)


    def unregister(daemon, obj):
        daemon.disconnect(obj)

    
    def get_sockets(daemon):
        return daemon.getServerSockets()


    def handleRequests(daemon, s):
        daemon.handleRequests()

    
    def init_daemon(host, port):
        Pyro.core.initServer()
        daemon = Pyro.core.Daemon(host=host, port=port)
        if daemon.port != port:
            print "Sorry, the port %d is not free" % port
            sys.exit(1)
        return daemon


    def create_uri(address, port, obj_name):
        return "PYROLOC://%s:%d/%s" % (address, port, obj_name)
    
    #Timeout way is also changed between 3 and 4
    #it's a method in 3, a property in 4
    def set_timeout(con, timeout):
        con._setTimeout(timeout)


except AttributeError:
    print "Using Pyro", Pyro.constants.VERSION
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


    def register(daemon, obj, name):
        daemon.register(obj)


    def unregister(daemon, obj, name):
        daemon.unregister(obj)

    
    def get_sockets(daemon):
        return daemon.sockets()

    
    def handleRequests(daemon, s):
        daemon.handleRequests([s])

    
    def init_daemon(host, port):
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


    def create_uri(address, port, obj_name):
        return "PYRO:%s@%s:%d" % (obj_name, address, port)

    
    def set_timeout(con, timeout):
        con._pyroTimeout = timeout

