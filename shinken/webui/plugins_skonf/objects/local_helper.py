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

def find(lst, elt, prop):
    value = elt.get(prop, None)
    if value is None:
        return None

    for i in lst:
        v = i.get(prop, None)
        if v == value:
            return i
    return None


class Helper(object):
    def __init__(self, app):
        self.app = app

    # Return a simple string input
    def get_string_input(self, elt, prop, name):
        s = '''<span class="span10">
                  <span class="help-inline"> %s </span>
                  <input name="%s" type="text" value="%s" />
               </span>
               <script>properties.push({'name' : '%s', 'type' : 'string'});</script>
            ''' % (name, prop, elt.get(prop, ''), prop)
        return s


    def get_select_input(self, elt, prop, name, cls, key):
        t = getattr(self.app.db, cls)
        tps = list(t.find({}))
        
        elt_tp = find(tps, elt, prop)
        print 'Find a matching element for me?', elt_tp

        select_part = '''<SELECT name="%s">''' % prop
        if elt_tp:
            select_part += '<OPTION VALUE="%s">%s</OPTION>' % (tpname, tpname)
        else:
            select_part += '<OPTION VALUE=""></OPTION>'

        for tp in tps:
            if tp == elt_tp:
                continue

            if not key in tp:
                continue

            tpname = tp.get(key)
            select_part += '<OPTION VALUE="%s">%s</OPTION>' % (tpname, tpname)
        select_part += '</SELECT>'

        s = '''<span class="span10">
                  <span class="help-inline"> %s </span>
                  %s
               </span>
               <script>properties.push({'name' : '%s', 'type' : 'select'});</script>
            ''' % (name, select_part, prop)
        return s
        
