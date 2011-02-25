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


#This class is a wrapper for managing Pyro 3 and 4 version

import select, errno

import Pyro.core


class InvalidWorkDir(Exception): pass
class PortNotFree(Exception): pass



#Try to see if we are Python 3 or 4
try:
    Pyro.core.ObjBase
    #Some one already go here, so we are in 4 if None
    if Pyro.core.ObjBase is None:
        raise AttributeError
    print "Using Pyro", Pyro.constants.VERSION
    
    Pyro.errors.CommunicationError = Pyro.errors.ProtocolError
    
    class Pyro3Daemon(Pyro.core.Daemon):
        pyro_version = 3
        protocol = 'PYROLOC'
        
        def __init__(self, host, port, use_ssl=False):
            try:
                Pyro.core.initServer()
            except OSError, e: # must be problem with workdir :
                raise InvalidWorkDir(e)
            if use_ssl:
                prtcol = 'PYROSSL'
            else:
                prtcol = 'PYRO'
            try:
                Pyro.core.Daemon.__init__(self, host=host, port=port, prtcol=prtcol, norange=True)
            except OSError, e:
                # must be problem with workdir :
                raise InvalidWorkDir(e)
            except Pyro.errors.DaemonError, e:
                msg = "Sorry, the port %d is not free: %s" % (port, e)
                raise PortNotFree(msg)

        def register(self, obj, name):
            return self.connect(obj, name)

        def unregister(self, obj):
            self.disconnect(obj)

        def get_sockets(self):
            return self.getServerSockets()

        def handleRequests(self, s):
            Pyro.core.Daemon.handleRequests(self)    

    def create_uri(address, port, obj_name, use_ssl):
        if not use_ssl:
            return "PYROLOC://%s:%d/%s" % (address, port, obj_name)
        else:
            return "PYROLOCSSL://%s:%d/%s" % (address, port, obj_name)

    # Timeout way is also changed between 3 and 4
    # it's a method in 3, a property in 4
    def set_timeout(con, timeout):
        con._setTimeout(timeout)

    def getProxy(uri):
        return Pyro.core.getProxyForURI(uri)


    PyroClass = Pyro3Daemon


except AttributeError:
    
    print "Using Pyro", Pyro.constants.VERSION
    
    # Ok, in Pyro 4, interface do not need to
    # inherit from ObjBase, just object is good
    Pyro.core.ObjBase = object
    Pyro.errors.URIError = Pyro.errors.ProtocolError
    Pyro.core.getProxyForURI = Pyro.core.Proxy
    
    # Hack for Pyro 4 : with it, there is
    # no more way to send huge packet!
    import socket
    if hasattr(socket, 'MSG_WAITALL'):
        del socket.MSG_WAITALL

    class Pyro4Daemon(Pyro.core.Daemon):
        pyro_version = 4
        protocol = 'PYRO'
        
        def __init__(self, host, port, use_ssl=False):
            #Pyro 4 i by default thread, should do select
            #(I hate threads!)
            Pyro.config.SERVERTYPE = "select"
            #And port already use now raise an exception
            try:
                Pyro.core.Daemon.__init__(self, host=host, port=port)
            except socket.error, exp:
                msg = "Sorry, the port %d is not free : %s" % (port, str(exp))
                raise PortNotFree(msg)
            except Exception, e:
                # must be problem with pyro workdir :
                raise InvalidWorkDir(e)

        ## same than this super class so no need:
        # def register(self, obj, name):
        # def unregister(self, obj, name):
    

        def get_sockets(self):
            return self.sockets()
    
        def handleRequests(self, s):
            Pyro.core.Daemon.handleRequests(self, [s])
    
    
    def create_uri(address, port, obj_name, use_ssl=False):
        return "PYRO:%s@%s:%d" % (obj_name, address, port)


    def set_timeout(con, timeout):
        con._pyroTimeout = timeout


    def getProxy(uri):
        return Pyro.core.Proxy(uri)


    PyroClass = Pyro4Daemon



class ShinkenPyroDaemon(PyroClass):
    
    def get_socks_activity(self, timeout):
        try:
            ins, _, _ = select.select(self.get_sockets(), [], [], timeout)
        except select.error, e:
            errnum, _ = e
            if errnum == errno.EINTR:
                return []
            raise
        return ins
