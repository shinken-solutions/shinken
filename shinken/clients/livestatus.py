#!/usr/bin/env python
#Copyright (C) 2009-2011 :
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

import socket
import asyncore

class LSConnection:
    def __init__(self, addr='127.0.0.1', port=50000, path=None, timeout=10):
	self.addr = addr
        self.port = port
        self.path = path
        self.timeout = timeout

        # We must know if the socket is alive or not
        self.alive = False

        # Now we can inti the sockets
        if path:
            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.type = 'unix'
        else:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.type = 'tcp'

        # We can now set the socket timeout
        self.socket.settimeout(timeout)
        self.connect()

    def connect(self):
        if not self.alive:
            if self.type == 'unix':
                target = self.path
            else:
                target = (self.addr, self.port)
            try:
                self.socket.connect(target)
                self.alive = True
            except IOError, exp:
                self.alive = False
                print "Connexion problem", exp


    def read(self, size):
	res = ""
	while size > 0:
	    data = self.socket.recv(size)
            l = len(data)
	    if l == 0:
                print "WARNING, 0 size read"
                return res # : TODO raise an error
	    size = size - l
            res = res + data
	return res


    def launch_query(self, query):
        if not self.alive:
	    self.connect()
        if not query.endswith("\n"):
	    query += "\n"
        query += "OutputFormat: python\nKeepAlive: on\nResponseHeader: fixed16\n\n"

        try:
	    self.socket.send(query)
	    data = self.read(16)
	    code = data[0:3]
            print "RAW DATA", data
	    length = int(data[4:15])
            print "Len", length
	    data = self.read(length)
            print "DATA", data
	    if code == "200":
		try:
		    return eval(data)
		except:
                    print "BAD VALUE RETURN", data
                    return None
	    else:
                print "BAD RETURN CODE", code, data
                return None
        except IOError, exp:
	    self.alive = False
            print "SOCKET ERROR", exp
            return None


    def exec_command(self, command):
	if not self.alive:
	    self.connect()
	if not command.endswith("\n"):
	    command += "\n"
	try:
	    self.socket.send("COMMAND " + command + "\n")
	except IOError, exp:
	    self.alive = False
            print "COMMAND EXEC error:", exp


# Query class for define a query, and its states
class Query(object):
    def __init__(self, q):
        # The query string
        if not q.endswith("\n"):
            q += "\n"
        q += "OutputFormat: python\nKeepAlive: on\nResponseHeader: fixed16\n\n"

        self.q = q
        # Got some states PENDING -> PICKUP -> DONE
        self.state = 'PENDING'
        self.result = None
        #By default, an error :)
        self.return_code = '500'


    def get(self):
        print "Someone ask my query", self.q
        self.state = 'PICKUP'
        return self.q

    def put(self, r):
        self.result = r
        self.state = 'DONE'
        print "Got a result", r
    


class LSAsynConnection(asyncore.dispatcher):
    def __init__(self, addr='127.0.0.1', port=50000, path=None, timeout=10):
        asyncore.dispatcher.__init__(self)
	self.addr = addr
        self.port = port
        self.path = path
        self.timeout = timeout

        # We must know if the socket is alive or not
        self.alive = False

        # Now we can inti the sockets
        if path:
            self.create_socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.type = 'unix'
        else:
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.type = 'tcp'

        # We can now set the socket timeout
        self.socket.settimeout(timeout)
        self.do_connect()


        # And our queries
        q = Query('GET hosts\nColumns name\n')
        self.queries = [q]
        
        self.current = None


    # Get a query and put it in current
    def get_query(self):
        q = self.queries.pop()
        self.current = q
        return q


    def do_connect(self):
        if not self.alive:
            if self.type == 'unix':
                target = self.path
            else:
                target = (self.addr, self.port)
            try:
                self.connect(target)
                self.alive = True
            except IOError, exp:
                self.alive = False
                print "Connexion problem", exp


    def do_read(self, size):
	res = ""
	while size > 0:
	    data = self.socket.recv(size)
            l = len(data)
	    if l == 0:
                print "WARNING, 0 size read"
                return res # : TODO raise an error
	    size = size - l
            res = res + data
	return res


    def launch_query(self, query):
        if not self.alive:
	    self.do_connect()

        q = self.current

        try:
	    self.socket.send(query)
	    data = self.do_read(16)
	    code = data[0:3]
            print "RAW DATA", data
	    length = int(data[4:15])
            print "Len", length
	    data = self.do_read(length)
            print "DATA", data
            # We update the current query

            q.return_code = code
	    if code == "200":
		try:
                    r = eval(data)
                    q.put(r)
		except:
                    print "BAD VALUE RETURN", data
                    q.put(None)
	    else:
                print "BAD RETURN CODE", code, data
                q.put(None)
        except IOError, exp:
	    self.alive = False
            
            print "SOCKET ERROR", exp
            return None


    def exec_command(self, command):
	if not self.alive:
	    self.do_connect()
	if not command.endswith("\n"):
	    command += "\n"
	try:
	    self.socket.send("COMMAND " + command + "\n")
	except IOError, exp:
	    self.alive = False
            print "COMMAND EXEC error:", exp






    def handle_connect(self):
        print "In handle_connect"



    def handle_close(self):
        print "In close"
        self.close()

        
    # Check if we are in timeout. If so, just bailout
    # and set the correct return code from timeout
    # case
    def look_for_timeout(self):
        print "Look for timeout"
        now = time.time()
        if now - self.start_time > self.timeout:
            if self.unknown_on_timeout:
                rc = 3
            else:
                rc = 2
            message = 'Error : connection timeout after %d seconds' % self.timeout
            self.set_exit(rc, message)


    # We got a read for the socket. We do it if we do not already
    # finished. Maybe it's just a SSL handshake continuation, if so
    # we continue it and wait for handshake finish
    def handle_read(self):
        print "Handle read"

        q = self.current
        # get a read but no current query? Not normal!

        if not q:
            print "WARNING : got LS read while no current query in progress. I return"
            return

        try:
            data = self.do_read(16)
            code = data[0:3]
            print "RAW DATA", data
            length = int(data[4:15])
            print "Len", length
            data = self.do_read(length)
            print "DATA", data
            if code == "200":
                try:
                    v = eval(data)
                    print "Type?", type(v)
                    print v
                except:
                    print "BAD VALUE RETURN", data
                    return None
            else:
                print "BAD RETURN CODE", code, data
                return None
        except IOError, exp:
	    self.alive = False
            print "SOCKET ERROR", exp
            return None




    # Did we finished our job?
    def writable(self):
        b = (len(self.queries) != 0)
        print "Is writable?", b
        return (len(self.queries) > 0)


    # We can write to the socket. If we are in the ssl handshake phase
    # we just continue it and return. If we finished it, we can write our
    # query
    def handle_write(self):
        print "handle write"
        try :
            q = self.get_query()
            sent = self.send(q.get())
        except socket.error, exp:
            print "Fuck in write exception", exp
            return

        print "Sent", sent, "data"
    








if __name__ == "__main__":
    c = LSAsynConnection()
    asyncore.loop()

    #print c.launch_query('GET hosts\nColumns name')
