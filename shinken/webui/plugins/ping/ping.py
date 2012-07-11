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

from shinken.webui.bottle import redirect

### Will be populated by the UI with it's own value
app = None


def forge_response(callback, status, text):
    if callback:
        return "%s({'status':%s,'text':'%s'})" % (callback, status, text)
    else:
        return "{'status':%s,'text':'%s'}" % (status, text)


# We will always answser pong to a ping.
def get_ping():

    app.response.content_type = 'application/json'
    callback = app.request.query.get('callback', None)

    # We do not need to look at the user, should be public
    return forge_response(callback, 200, 'Pong')


# We will say if we got at least the first data, like contacts
# so the UI can refresh without breaking all.
def get_gotfirstdata():
    app.response.content_type = 'application/json'
    callback = app.request.query.get('callback', None)

    if len(app.datamgr.get_contacts()) > 0:
        return forge_response(callback, 200, '1')
    else:
        return forge_response(callback, 200, '0')

pages = {get_ping: {'routes': ['/ping']},
         get_gotfirstdata: {'routes': ['/gotfirstdata']},
         }
