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


# This Class is an Arbiter module for having a webservice
# wher you can push external commands


import os
import select


######################## WIP   don't launch it!


from shinken.basemodule import BaseModule
from shinken.external_command import ExternalCommand

from shinken.webui.bottle import Bottle, run, static_file, view, route, request, response, abort

properties = {
    'daemons' : ['arbiter', 'receiver'],
    'type' : 'ws_arbiter',
    'external' : True,
    }

#called by the plugin manager to get a broker
def get_instance(plugin): # plugin: dict de la conf
    print "aide en une ligne %s" % plugin.get_name()

    instance = Ws_arbiter(plugin)
    return instance


#Just print some stuff
class Ws_arbiter(BaseModule):
    def __init__(self, modconf):
        BaseModule.__init__(self, modconf)
        try:
            username = modconf.username
            password = modconf.password
            self.port = modconf.port
            self.host = '0.0.0.0'
        except AttributeError:
            print "Error : the module '%s' do not have a property"
            raise



    def get(self):
        buf = os.read(self.fifo, 8096)
        r = []
        fullbuf = len(buf) == 8096 and True or False
        # If the buffer ended with a fragment last time, prepend it here
        buf = self.cmd_fragments + buf
        buflen = len(buf)
        self.cmd_fragments = ''
        if fullbuf and buf[-1] != '\n':
            # The buffer was full but ends with a command fragment
            r.extend([ExternalCommand(s) for s in (buf.split('\n'))[:-1] if s])
            self.cmd_fragments = (buf.split('\n'))[-1]
        elif buflen:
            # The buffer is either half-filled or full with a '\n' at the end.
            r.extend([ExternalCommand(s) for s in buf.split('\n') if s])
        else:
            # The buffer is empty. We "reset" the fifo here. It will be
            # re-opened in the main loop.
            os.close(self.fifo)
        return r


    def get_page(self):
        print "On me demande la page /push"
        time_stamp = request.forms.get('time_stamp', 0)
        host_name = request.forms.get('host_name', None)
        service_description = request.forms.get('service_description', None)
        return_code = request.forms.get('return_code', -1)
        output = request.forms.get('output', None)

        if time_stamp==0 or not host_name or not service_description or not output or return_code == -1:
            print "Je ne suis pas content, je quitte"
            abort(400, "blalna")



    def init_http(self):
        print "Starting WebUI application"
        self.srv = run(host=self.host, port=self.port, server='wsgirefselect')
        print "Launch server", self.srv
        route('/push', callback=self.get_page,method='POST')


    # When you are in "external" mode, that is the main loop of your process
    def main(self):
        self.set_exit_handler()

        self.init_http()

        input = [self.srv.socket]


        # Main blocking loop
        while not self.interrupted:
            # _reader is the underliying file handle of the Queue()
            # so we can select it too :)
            input = [self.srv.socket]
            inputready,_,_ = select.select(input,[],[], 1)
            for s in inputready:
                # If it's a web request, ask the webserver to do it
                if s == self.srv.socket:
                    #print "Handle Web request"
                    self.srv.handle_request()

