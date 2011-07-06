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



if __name__ == "__main__":
    c = LSConnection()
    print c.launch_query('GET hosts\nColumns name')
