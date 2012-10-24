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


# Our page. If the user call /worldmap
def get_page():
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()
    if not user:
        redirect("/user/login")
        return

    # We are looking for hosts taht got valid GPS coordonates,
    # and we just give them to the template to print them.
    all_hosts = app.datamgr.get_hosts()
    valid_hosts = []
    for h in all_hosts:
        _lat = h.customs.get('_LAT', None)
        _long = h.customs.get('_LONG', None)

        try:
            print "Host", h.get_name(), _lat, _long, h.customs
        except:
            pass
        if _lat and _long:
            try:
                _lat = float(_lat)
                _long = float(_long)
            # Maybe the customs are set, but with invalid float?
            except ValueError:
                continue
            # Look for good range, lat/long must be between -180/180
            if -180 <= _lat <= 180 and -180 <= _long <= 180:
                print "GOOD VALUES FOR HOST", h.get_name()
                valid_hosts.append(h)

    # So now we can just send the valid hosts to the template
    return {'app': app, 'user': user, 'hosts' : valid_hosts}


# We export our properties to the webui
pages = {get_page: {'routes': ['/worldmap'], 'view': 'worldmap', 'static': True}}
