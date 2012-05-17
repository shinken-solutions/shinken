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


from shinken.webui.bottle import redirect, abort

### Will be populated by the UI with it's own value
app = None


def push_new_pack():
    print "FUCK",app.request.forms.__dict__
    key = app.request.forms.get('key')
    data = app.request.files.get('data')
    print "KEY", key
    print "DATA", data.file
    if not key:
        print "NOT KEY"
    if not data.file:
        print "NO FILE"
    if key and data.file:
        print "READING A FILE"
        # LIMIT AT 5MB
        raw = data.file.read(5000000)
        over = data.file.read(1)
        filename = data.filename
        if over:
            abort(400, 'Sorry your file is too big!')
        app.save_new_pack('jean', filename, raw)
        return "Hello %s! You uploaded %s (%d bytes)." % (key, filename, len(raw))
    abort(400, 'You missed a field.')

pages = {push_new_pack : { 'routes' : ['/push'], 'method' : 'POST', 'view' : None, 'static' : True}}

