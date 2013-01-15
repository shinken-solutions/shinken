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

from shinken.webui.bottle import redirect, abort, static_file

### Will be populated by the UI with it's own value
app = None


def get_packs():
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    return {'app': app, 'user': user}


def get_pack(pid):
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    # Maybe we got a static uri with user-packname
    if '-' in pid:
        uname, packname = pid.split('-', 1)
        pack = app.datamgr.get_pack_by_user_packname(uname, packname)
    else:  # of the direct inner pack_id (will change for each push)
        pack = app.datamgr.get_pack_by_id(pid)

    return {'app': app, 'user': user, 'pack': pack}


def download_pack(pid):
    pack = app.datamgr.get_pack_by_id(pid)
    if not pack:
        abort(400, 'Unknown pack!')
    path = pack.get('filepath')
    filename = pack.get('filename')
    return static_file(path, root='/', download=filename)

pages = {
    get_packs: {'routes': ['/packs'], 'view': 'packs', 'static': True},
    get_pack: {'routes': ['/pack/:pid'], 'view': 'pack', 'static': True},
    download_pack: {'routes': ['/getpack/:pid'], 'static': True},
    }
