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
        try:
            print 'MAtch with', v, value
        except:
            pass
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
        try:
            print 'MAtch with db', v
        except:
            pass
        if v  in values:
            res.append(dbi)
    print "Return find_several::", res
    return res


class Helper(object):
    def __init__(self, app):
        self.app = app

    # Return a simple string input
    def get_string_input(self, elt, prop, name, span='span10', innerspan='span2', inputsize='', placeholder='', popover=None, editable=''):
        p = ''
        if popover is not None:
            p = '<i id="popover-%s" class="icon-question-sign"></i>' % prop
            p += '<script>$("#popover-%s").popover({"title": "Help", "content": "%s"});</script>' % (prop, popover)
        s = '''<span class="%s">
                  <span class="help-inline %s"> %s </span>
                  <input class="%s %s" name="%s" type="text" value="%s" placeholder='%s' %s/>
                  %s
               </span>
               <script>properties.push({'name': '%s', 'type': 'string'});</script>
            ''' % (span, innerspan, name, editable, inputsize, prop, elt.get(prop, ''), placeholder, editable, p, prop)
        return s

    def get_bool_input(self, elt, prop, name, editable=''):
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

        <script>properties.push({'name': '%s', 'type': 'bool'});</script>
        <div class="btn-group span9 %s" data-toggle="buttons-radio">
          <button class="btn %s %s" type="button" name="%s" value="1" >On</button>
          <button class="btn %s %s" type="button" name="%s" value="0" >Off</button>
          <button class="btn %s %s" type="button" name="%s" value="" >Unset</button>
        </div>
        </span>''' % (name, prop, editable, on, editable, prop, off, editable, prop, unset, editable, prop)
        return s

    def get_percent_input(self, elt, prop, name, editable='', placeholder='', popover=None):
        # Ok, let's try to see the value in db first
        v = elt.get(prop, '')
        # If not set, take the value from our templates?
        value = 0
        active = '0'
        if v != '':
            placeholder = value
            value = int(v)
            active = '1'

        p = ''
        if popover is not None:
            p = '<i id="popover-%s" class="icon-question-sign"></i>' % prop
            p += '<script>$("#popover-%s").popover({"title": "Help", "content": "%s"});</script>' % (prop, popover)

        s = '''
        <span class="span10">
           <span class="help-inline span2"> %s </span>
           <script>properties.push({'name': '%s', 'type': 'percent'});</script>
           <span class='span1' id='slider_log_%s'>%s%%</span>
           <div id='slider_%s' class='%s slider span5' data-log='#slider_log_%s' data-prop='%s' data-min=0 data-max=100 data-unit='%%' data-value=0 data-active=%s></div>
           <a id='btn-slider_%s' href='javascript:toggle_slider("%s");' class='btn btn-mini %s'>Set/Unset</a>
           %s
        </span>''' % (name, prop, prop, placeholder, prop, editable, prop, prop, active, prop, prop, editable, p)
        return s

    def get_select_input(self, elt, prop, name, cls, key, editable=''):
        t = getattr(self.app.db, cls)
        tps = list(t.find({}))

        value = elt.get(prop, None)
        elt_tp = find(value, tps, key)
        print 'Find a matching element for me?', elt.get(prop), elt_tp

        select_part = '''<SELECT class='%s' name="%s" %s>''' % (editable, prop, editable)
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
               <script>properties.push({'name': '%s', 'type': 'select'});</script>
            ''' % (name, select_part, prop)
        return s

    def get_command_input(self, elt, prop, name, cls, key, editable=''):
        t = getattr(self.app.db, cls)
        tps = list(t.find({}))

        value = elt.get(prop, None)
        args = ''
        # We split on the first ! of the data
        if value is not None:
            elts = value.split('!', 1)
            value = elts[0]
            if len(elts) > 1:
                args = '!' + elts[1]

        elt_tp = find(value, tps, key)
        print 'Find a matching element for me?', elt.get(prop), elt_tp

        select_part = '''<SELECT class='%s' name="%s" %s>''' % (editable, prop, editable)
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
                 Args <input class='%s' name='args-%s' value='%s' %s></input>
               </span>
               <script>properties.push({'name': '%s', 'type': 'command'});</script>
            ''' % (name, select_part, editable, prop, args, editable, prop)
        return s

    def get_multiselect_input(self, elt, prop, name, cls, key, editable=''):
        t = getattr(self.app.db, cls)
        tps = list(t.find({}))

        elts_tp = find_several(tps, elt, prop, key)
        print 'Find a matching element for me?', elts_tp

        select_part = '''<SELECT class='%s' name="%s" multiple="multiple" %s>''' % (editable, prop, editable)
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
               <script>properties.push({'name': '%s', 'type': 'multiselect'});</script>
            ''' % (name, select_part, prop)
        return s

    def get_poller_tag_input(self, elt, prop, name, editable=''):
        value = elt.get(prop, None)
        all_poller_tags = set()
        for p in self.app.conf.pollers:
            print 'Look at poller?', p.__dict__
            for t in getattr(p, 'poller_tags', '').split(','):
                all_poller_tags.add(t.strip())

        select_part = '''<SELECT class='%s' name="%s" %s>''' % (editable, prop, editable)
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
               <script>properties.push({'name': '%s', 'type': 'select'});</script>
            ''' % (name, select_part, prop)
        return s

    def get_realm_input(self, elt, prop, name, editable=''):

        value = elt.get(prop, None)
        all_realms = set()
        for r in self.app.conf.realms:
            print 'Look at realm?', r.__dict__
            all_realms.add(r.get_name())

        select_part = '''<SELECT class='%s' name="%s" %s>''' % (editable, prop, editable)
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
               <script>properties.push({'name': '%s', 'type': 'select'});</script>
            ''' % (name, select_part, prop)
        return s

    def get_customs_inputs(self, app, elt, editable=''):
        print "CUSTOM OF", elt
        s = ''
        customs = {}

        # Get our template names
        tnames = [t.strip() for t in elt.get('use', '').split(',')]

        # Look for our templates custom values, and get only the first one
        for t in tnames:
            for tpl in app.host_templates.values():
                tname = getattr(tpl, 'name', None)
                if tname == t:
                    for (k, v) in tpl.customs.iteritems():
                        print 'My template customs', k, v
                        if k not in customs:
                            customs[k] = {'from': tname, 'value': '', 'placeholder': v}

        # Now the item one, will overwrite any entry
        for (k, v) in elt.iteritems():
            if k.startswith('_') and k != '_id':
                customs[k] = {'from': '__ITEM__', 'value': v, 'placeholder': ''}

        # Get a sorted macro names
        sorted_names = [k for k in customs]
        sorted_names.sort()
        print 'Sorted names', sorted_names

        s += "<span><a class='btn btn-success pull-right %s' href='javascript:add_macro();'><i class='icon-plus'></i> Add macro</a></span>" % editable
        s += "<span id='new_macros'></span>"
        # We want to show the how element macros value first
        tnames.insert(0, '__ITEM__')
        for tname in tnames:
            new_template = True
            for k in sorted_names:
                v = customs[k]
                if v['from'] != tname:
                    continue
                if new_template and tname != '__ITEM__':
                    s += '<span class="span10"><span class="label label-info span2"><img class="imgsize1" onerror="$(this).hide()" src="/static/images/sets/%s/tag.png">%s</span></span>' % (tname, tname)
                    new_template = False
                print "Looping over template", tname, "customs"
                ctype = 'string'
                popover = None
                founded = False
                for p in app.packs:
                    if founded:
                        break
                    for (m, mv) in p.macros.iteritems():
                        print "COmpare", k, m
                        if k.upper() == m.upper():
                            print 'Match a pack', mv
                            ctype = mv.get('type', 'string').strip()
                            popover = mv.get('description', None)
                            founded = True
                            break

                if ctype == 'percent':
                    s += self.get_percent_input(elt, k, k[1:], editable=editable, placeholder=v['placeholder'], popover=popover)
                else:  # if not known, apply string
                    s += self.get_string_input(elt, k, k[1:], editable=editable, placeholder=v['placeholder'], popover=popover)

        return s
