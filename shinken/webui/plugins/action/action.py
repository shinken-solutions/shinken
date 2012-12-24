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
import re


# Function handling $NOW$ macro
def subsNOW():
    return str(int(time.time()))

def subsSLASH():
    return '/'

# This dictionnary associate macros with expansion function
subs = {'$NOW$': subsNOW,
        '$SLASH$' : subsSLASH,
        # Add new macros here
       }


# Expand macro in a string. It returns the string with macros defined in subs dictionary expanded
def expand_macros(cmd=None):
    macros = re.findall(r'(\$\w+\$)', cmd)
    cmd_expanded = cmd
    for macro in macros:
        subfunc = subs.get(macro)
        if subfunc is None:
            print "Macro ", macro, " is unknown, do nothing"
            continue
        print "Expand macro ", macro, " in '", cmd_expanded, "'"
        cmd_expanded = cmd_expanded.replace(macro, subfunc())

    return cmd_expanded


def forge_response(callback, status, text):
    if callback:
        return "%s({'status':%s,'text':'%s'})" % (callback, status, text)
    else:
        return "{'status':%s,'text':'%s'}" % (status, text)


# Our page
def get_page(cmd=None):

    app.response.content_type = 'application/json'

    print app.request.query.__dict__
    callback = app.request.query.get('callback', None)

    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    # Maybe the user is not known at all
    if not user:
        return forge_response(callback, 401, 'Invalid session')

    # Or he is not allowed to launch commands?
    if app.manage_acl and not user.can_submit_commands:
        return forge_response(callback, 403, 'You are not authorized to launch commands')

    now = int(time.time())
    print "Ask us an /action page", cmd
    elts = cmd.split('/')
    cmd_name = elts[0]
    cmd_args = elts[1:]
    print "Got command", cmd_name
    print "And args", cmd_args

    # Check if the command exist in the external command list
    if cmd_name not in ExternalCommandManager.commands:
        return forge_response(callback, 404, 'Unknown command %s' % cmd_name)

    extcmd = '[%d] %s' % (now, ';'.join(elts))
    print "Got the; form", extcmd

    # Expand macros
    extcmd = expand_macros(extcmd)
    print "Got after macro expansion", extcmd

    # Ok, if good, we can launch the command
    extcmd = extcmd.decode('utf8', 'replace')
    e = ExternalCommand(extcmd)
    print "Creating the command", e.__dict__
    app.push_external_command(e)

    return forge_response(callback, 200, 'Command launched')

pages = {get_page: {'routes': ['/action/:cmd#.+#']}}
