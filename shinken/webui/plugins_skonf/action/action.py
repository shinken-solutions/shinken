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

### Will be populated by the UI with it's own value
app = None

# We will need external commands here
import time
from shinken.external_command import ExternalCommand, ExternalCommandManager


# Our page
def get_page(cmd=None):

    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        return {'status': 401, 'text': 'Invalid session'}

    now = int(time.time())
    print "Ask us an /action page", cmd
    elts = cmd.split('/')
    cmd_name = elts[0]
    cmd_args = elts[1:]
    print "Got command", cmd_name
    print "And args", cmd_args

    # Check if the command exist in the external command list
    if cmd_name not in ExternalCommandManager.commands:
        return {'status': 404, 'text': 'Unknown command %s' % cmd_name}

    extcmd = '[%d] %s' % (now, ';'.join(elts))
    print "Got the; form", extcmd

    # Ok, if good, we can launch the command
    extcmd = extcmd.decode('utf8', 'replace')
    e = ExternalCommand(extcmd)
    print "Creating the command", e.__dict__
    app.push_external_command(e)

    return {'status': 200, 'text': 'Command launched'}

pages = {get_page: {'routes': ['/action/:cmd#.+#']}}
