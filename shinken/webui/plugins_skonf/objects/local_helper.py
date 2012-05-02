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

from shinken.util import strip_and_uniq

def find(value, lst, key):
    print 'Finding the value', value
    print 'And in the list', lst, 'and key', key

    if value is None:
        return None

    for i in lst:
        v = i.get(key, None)
        print 'MAtch with', v, value
        if v == value:
            return i
    return None

# We will find in lst elements with the key that match elt.prop values (it's a list
# of elements wit the keys in lst[key])
def find_several(lst, elt, prop, key):
    print 'Find several in', lst, 'for element', elt, 'and property', prop
    value = elt.get(prop, None)
    if value is None:
        return []

    values = value.split(',')
    values = strip_and_uniq(values)
    print 'Our values are', values

    res = []
    # Now try to match what it got
    for dbi in lst:
        print 'Try to look at', dbi, 'for property', key
        v = dbi.get(key, None)
        if v is None:
            continue
        v = v.strip()
        print 'MAtch with db',v
        if v  in values:
            res.append(dbi)
    print "Return find_several::", res
    return res


class Helper(object):
    def __init__(self, app):
        self.app = app


    # Return a simple string input
    def get_string_input(self, elt, prop, name, span='span10', innerspan='span2' ,placeholder='', popover=None):
        p = ''
        if popover is not None:
            p = '<i id="popover-%s" class="icon-question-sign"></i>' % prop
            p += '<script>$("#popover-%s").popover({"title": "Help", "content" : "%s"});</script>' % (prop, popover)
        s = '''<span class="%s">
                  <span class="help-inline %s"> %s </span>
                  <input name="%s" type="text" value="%s" placeholder='%s' />
                  %s
               </span>
               <script>properties.push({'name' : '%s', 'type' : 'string'});</script>
            ''' % (span, innerspan, name, prop, elt.get(prop, ''), placeholder, p, prop)
        return s


    def get_bool_input(self, elt, prop, name):
        # Ok, let's try to see the value in db first
        v = elt.get(prop, '')

        on = ''
        if v == '1':
            on = 'active'
        off = ''
        if v == '0':
            off = 'active'
        unset = ''
        if not on and not off:
            unset = 'active'

        s = '''
        <span class="span10">
           <span class="help-inline span2"> %s </span>

        <script>properties.push({'name' : '%s', 'type' : 'bool'});</script>
	<div class="btn-group span9" data-toggle="buttons-radio">
	  <button class="btn %s" type="button" name="%s" value="1" >On</button>
	  <button class="btn %s" type="button" name="%s" value="0" >Off</button>
	  <button class="btn %s" type="button" name="%s" value="" >Unset</button>
	</div>
        </span>''' % (name, prop, on, prop, off, prop, unset, prop)
        return s



    def get_percent_input(self, elt, prop, name):
        # Ok, let's try to see the value in db first
        v = elt.get(prop, '')
        value = 0
        active = '0'
        if v != '':
            value = int(v)
            active = '1'

        s = '''
        <span class="span10">
           <span class="help-inline span2"> %s </span>
           <script>properties.push({'name' : '%s', 'type' : 'percent'});</script>
           <span class='span1' id='slider_log_%s'>%s%%</span>
           <div id='slider_%s' class='slider span5' data-log='#slider_log_%s' data-prop='%s' data-min=0 data-max=100 data-unit='%%' data-value=0 data-active=%s></div>
           <a id='btn-slider_%s' href='javascript:toggle_slider("%s");' class='btn btn-mini'>Set/Unset</a>
        </span>''' % (name, prop, prop, value ,prop, prop, prop, active, prop, prop)
        return s


    def get_select_input(self, elt, prop, name, cls, key):
        t = getattr(self.app.db, cls)
        tps = list(t.find({}))
        
        value = elt.get(prop, None)
        elt_tp = find(value, tps, key)
        print 'Find a matching element for me?', elt.get(prop), elt_tp

        select_part = '''<SELECT name="%s">''' % prop
        if elt_tp:
            tpname = elt_tp.get(key)
            select_part += '<OPTION VALUE="%s">%s</OPTION>' % (tpname, tpname)
        # Always add avoid value if need
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
                  <span class="help-inline span2"> %s </span>
                  %s
               </span>
               <script>properties.push({'name' : '%s', 'type' : 'select'});</script>
            ''' % (name, select_part, prop)
        return s


    def get_command_input(self, elt, prop, name, cls, key):
        t = getattr(self.app.db, cls)
        tps = list(t.find({}))
        
        value = elt.get(prop, None)
        args = ''
        # We split on the first ! of the data
        if value is not None:
            elts = value.split('!',1)
            value = elts[0]
            if len(elts) > 1:
                args = '!'+elts[1]
            
        elt_tp = find(value, tps, key)
        print 'Find a matching element for me?', elt.get(prop), elt_tp

        select_part = '''<SELECT name="%s">''' % prop
        if elt_tp:
            tpname = elt_tp.get(key)
            select_part += '<OPTION VALUE="%s">%s</OPTION>' % (tpname, tpname)
        # Always add a void option if need
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
                  <span class="help-inline span2"> %s </span>
                  %s
                 Args <input name='args-%s' value='%s'></input>
               </span>
               <script>properties.push({'name' : '%s', 'type' : 'command'});</script>
            ''' % (name, select_part, prop, args, prop)
        return s
        

    def get_multiselect_input(self, elt, prop, name, cls, key):
        t = getattr(self.app.db, cls)
        tps = list(t.find({}))
        
        elts_tp = find_several(tps, elt, prop, key)
        print 'Find a matching element for me?', elts_tp

        select_part = '''<SELECT name="%s" multiple="multiple">''' % prop
        #if elt_tp:
        #    select_part += '<OPTION VALUE="%s">%s</OPTION>' % (tpname, tpname)
        #else:
        #    select_part += '<OPTION VALUE=""></OPTION>'

        for tp in tps:
            if not key in tp:
                continue

            tpname = tp.get(key)
            if tp in elts_tp:
                select_part += '<OPTION VALUE="%s" selected="selected" >%s</OPTION>' % (tpname, tpname)
            else:
                select_part += '<OPTION VALUE="%s">%s</OPTION>' % (tpname, tpname)
        select_part += '</SELECT>'

        s = '''<span class="span10">
                  <span class="help-inline span2"> %s </span>
                  %s
               </span>
               <script>properties.push({'name' : '%s', 'type' : 'multiselect'});</script>
            ''' % (name, select_part, prop)
        return s
        




    def get_poller_tag_input(self, elt, prop, name):
        
        value = elt.get(prop, None)
        all_poller_tags = set()
        for p in self.app.conf.pollers:
            print 'Look at poller?', p.__dict__
            for t in p.poller_tags:
                all_poller_tags.add(t)
        
        select_part = '''<SELECT name="%s">''' % prop
        if value in all_poller_tags:
            select_part += '<OPTION VALUE="%s">%s</OPTION>' % (value, value)
        # Always add a void value, to unset if need
        select_part += '<OPTION VALUE=""></OPTION>'

        for pt in all_poller_tags:
            if value == pt:
                continue

            select_part += '<OPTION VALUE="%s">%s</OPTION>' % (pt, pt)
        select_part += '</SELECT>'

        s = '''<span class="span10">
                  <span class="help-inline span2"> %s </span>
                  %s
               </span>
               <script>properties.push({'name' : '%s', 'type' : 'select'});</script>
            ''' % (name, select_part, prop)
        return s



    def get_realm_input(self, elt, prop, name):
        
        value = elt.get(prop, None)
        all_realms = set()
        for r in self.app.conf.realms:
            print 'Look at realm?', r.__dict__
            all_realms.add(r.get_name())
        
        select_part = '''<SELECT name="%s">''' % prop
        if value in all_realms:
            select_part += '<OPTION VALUE="%s">%s</OPTION>' % (value, value)
        # Always add a void value, to unset if need
        select_part += '<OPTION VALUE=""></OPTION>'

        for pt in all_realms:
            if value == pt:
                continue

            select_part += '<OPTION VALUE="%s">%s</OPTION>' % (pt, pt)
        select_part += '</SELECT>'

        s = '''<span class="span10">
                  <span class="help-inline span2"> %s </span>
                  %s
               </span>
               <script>properties.push({'name' : '%s', 'type' : 'select'});</script>
            ''' % (name, select_part, prop)
        return s
