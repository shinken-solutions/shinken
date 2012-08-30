#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

# This Class is an Arbiter module for having a webservice
# wher you can push external commands

import os
import sys
import select
import time
######################## WIP   don't launch it!

from shinken.basemodule import BaseModule
from shinken.external_command import ExternalCommand
from shinken.log import logger

from shinken.webui.bottle import Bottle, run, static_file, view, route, request, response, abort, parse_auth

properties = {
    'daemons': ['arbiter', 'receiver'],
    'type': 'ws_arbiter',
    'external': True,
    }


# called by the plugin manager to get a broker
def get_instance(plugin):
    instance = Ws_arbiter(plugin)
    return instance

# Main app var. Will be fill with our running module instance
app = None


def get_page():
    # We get all value we want
    time_stamp = request.forms.get('time_stamp', int(time.time()))
    host_name = request.forms.get('host_name', None)
    service_description = request.forms.get('service_description', None)
    return_code = request.forms.get('return_code', -1)
    output = request.forms.get('output', None)

    # We check for auth if it's not anonymously allowed
    if app.username != 'anonymous':
        basic = parse_auth(request.environ.get('HTTP_AUTHORIZATION', ''))
        # Maybe the user not even ask for user/pass. If so, bail out
        if not basic:
            abort(401, 'Authentication required')
        # Maybe he do not give the good credential?
        if basic[0] != app.username or basic[1] != app.password:
            abort(403, 'Authentication denied')

    # Ok, here it's an anonymouscall, or a registred one, but mayeb teh query is false
    if time_stamp == 0 or not host_name or not output or return_code == -1:
        abort(400, "Incorrect syntax")

    # Maybe we got an host, maybe a service :)
    if not service_description:
        cmd = '[%s] PROCESS_HOST_CHECK_RESULT;%s;%s;%s' % (time_stamp, host_name, return_code, output)
    else:
        cmd = '[%s] PROCESS_SERVICE_CHECK_RESULT;%s;%s;%s;%s' % (time_stamp, host_name, service_description, return_code, output)

    # Now create the external command and put it in our main queue()
    # so the arbiter will read it :)
    ext = ExternalCommand(cmd)
    app.from_q.put(ext)

    # OK here it's ok, it will return a 200 code



# This module will open an HTTP service, where a user can send a command, like a check
# return.
class Ws_arbiter(BaseModule):
    def __init__(self, modconf):
        BaseModule.__init__(self, modconf)
        try:
            self.username = getattr(modconf, 'username', 'anonymous')
            self.password = getattr(modconf, 'password', '')
            self.port = int(getattr(modconf, 'port', '7760'))
            self.host = getattr(modconf, 'host', '0.0.0.0')
        except AttributeError:
            logger.error("[Ws_arbiter] The module is missing a property, check module declaration in shinken-specific.cfg")
            raise

    # We initialise the HTTP part. It's a simple wsgi backend
    # with a select hack so we can still exit if someone ask it
    def init_http(self):
        logger.info("[Ws_arbiter] Starting WS arbiter http socket")
        self.srv = run(host=self.host, port=self.port, server='wsgirefselect')
        # And we link our page
        route('/push_check_result', callback=get_page, method='POST')

    # When you are in "external" mode, that is the main loop of your process
    def main(self):
        global app

        # Change process name (seen in ps or top)
        self.set_proctitle(self.name)

        # It's an external module, so we need to be sure that we manage
        # the signals
        self.set_exit_handler()

        # Go for Http open :)
        self.init_http()

        # We fill the global variable with our Queue() link
        # with the arbiter, because the page should be a non-class
        # one function
        app = self

        # We will loop forever on the http socket
        input = [self.srv.socket]

        # Main blocking loop
        while not self.interrupted:
            input = [self.srv.socket]
            inputready, _, _ = select.select(input, [], [], 1)
            for s in inputready:
                # If it's a web request, ask the webserver to do it
                if s == self.srv.socket:
                    self.srv.handle_request()
