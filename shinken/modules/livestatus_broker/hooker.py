#!/usr/bin/python
#Copyright (C) 2009 Gabes Jean, naparuba@gmail.com
#
#This file is part of Shinken.
#
#Shinken is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Shinken is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with Shinken.  If not, see <http://www.gnu.org/licenses/>.




# Class for giving LiveStatus and Live
class Hooker:
    def __init__(self):
        pass

    def make_hook(self, hook, prop, default, func, as_prop):

        def hook_get_prop(elt):
            return getattr(elt, prop, default)


        def hook_get_prop_depythonize(elt):
            try:
                attr = getattr(elt, prop)
                if callable(attr):
                    attr = attr()
                return func(attr)
            except Exception, e:
                print "i am an exception in hook_get_prop_depythonize for managing an object '%s' with the property '%s' and the value '%s'" % (type(elt), prop, getattr(elt, prop, '')), e
                return default


        def hook_get_prop_depythonize_notcallable(elt):
            #if hasattr(elt, prop):
            try:
                value = getattr(elt, prop)
                if value is None or value == 'none':
                    return default
                elif isinstance(value, list):
                    # Example: Service['comments'] = { type : 'list', depythonize : 'id' }
                    # 
                    value = [getattr(item, func)() for item in value if callable(getattr(item, func)) ] \
                        + [getattr(item, func) for item in value if not callable(getattr(item, func)) ]
                    return value
                else:
                    f = getattr(value, func)
                    if callable(f):
                        return f()
                    else:
                        return f
            #else:
            except Exception:
                return default


        def hook_get_prop_full_depythonize(elt):
            try:
                value = getattr(elt, prop)
                if callable(value):
                    value = value()
                if value is None or value == 'none':
                    raise
                elif isinstance(value, list):
                    return [func(item, elt, self) for item in value]
                else:
                    return func(value, elt, self)
            except Exception, e:
                print "i am an exception", e
                return default


        def hook_get_prop_delegate(elt):
            if not as_prop:
                new_prop = prop
            else:
                new_prop = as_prop
            #if hasattr(elt, func):
            try:
                attr = getattr(elt, func)
                if callable(attr):
                    attr = attr()
                new_hook = self.out_map[attr.__class__.__name__][new_prop]['hook']
                if 'fulldepythonize' in self.out_map[attr.__class__.__name__][new_prop]:
                    return new_hook(attr, self)
                return new_hook(attr)
            #else:
            except Exception:
                return default


        if hook == 'get_prop':
            return hook_get_prop
        elif hook == 'get_prop_depythonize':
            return hook_get_prop_depythonize
        elif hook == 'get_prop_depythonize_notcallable':
            return hook_get_prop_depythonize_notcallable
        elif hook == 'get_prop_full_depythonize':
            return hook_get_prop_full_depythonize
        elif hook == 'get_prop_delegate':
            return hook_get_prop_delegate


    def create_out_map_hooks(self):
        """Add hooks to the elements of the LiveStatus.out_map.
        
        This function analyzes the elements of the out_map.
        Depending on the existence of several keys like
        default, prop, depythonize, etc. it creates a function which
        resolves an attribute as fast as possible and adds this function
        as a new key called hook.
        
        """
        # CLS wil be the LiveStatus class
        cls = self.__class__
        for objtype in cls.out_map:
            for attribute in cls.out_map[objtype]:
                entry =  cls.out_map[objtype][attribute]
                if 'prop' not in entry or entry['prop'] is None:
                    prop = attribute
                else:
                    prop = entry['prop']
                if 'default' in entry:
                    default = entry['default']
                else:
                    try:
                        if entry['type'] == 'int' or entry['type'] == 'float':
                            default = 0
                        elif entry['type'] == 'list':
                            default = []
                        else:
                            raise
                    except:
                        default = ''
                if 'delegate' in entry: 
                    entry['hook'] = self.make_hook('get_prop_delegate', prop, default, entry['delegate'], entry.setdefault('as', None))
                else:
                    if 'depythonize' in entry:
                        func = entry['depythonize']
                        if callable(func):
                            entry['hook'] = self.make_hook('get_prop_depythonize', prop, default, func, None)
                        else:
                            entry['hook'] = self.make_hook('get_prop_depythonize_notcallable', prop, default, func, None)
                    elif 'fulldepythonize' in entry:
                        func = entry['fulldepythonize']
                        entry['hook'] = self.make_hook('get_prop_full_depythonize', prop, default, func, None)
                        entry['hooktype'] = 'depythonize'
                    else:
                        entry['hook'] = self.make_hook('get_prop', prop, default, None, None)
            # This hack is ugly, i should be beaten up for it. But whithout it
            # mapping of Downtime.host_name would not work if it's a
            # host downtime. It cannot automatically be delegated to ref,
            # because autom. delegation assumes ref is a Host then, so
            # service_description would not work.
            # So the request will be delegated to a host, but with the full
            # property "host_name" which is only possible with the 
            # following code.
            if objtype == 'Host':
                attributes = cls.out_map[objtype].keys()
                for attribute in attributes:
                    cls.out_map[objtype]['host_' + attribute] =  cls.out_map[objtype][attribute]
