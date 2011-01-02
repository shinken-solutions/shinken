#!/usr/bin/env python
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
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


class memoized(object):
    """Decorator that caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned, and
    not re-evaluated.
    """
    def __init__(self, func):
        self.func = func
        self.cache = {}
    def __call__(self, *args):
        try:
            return self.cache[args]
        except KeyError:
            self.cache[args] = value = self.func(*args)
            return value
        except TypeError:
            # uncachable -- for instance, passing a list as an argument.
            # Better to not cache than to blow up entirely.
            return self.func(*args)
    def __repr__(self):
        """Return the function's docstring."""
        return self.func.__doc__

#import cPickle



#def memoized(function, limit=None):
#    if isinstance(function, int):
#        def memoize_wrapper(f):
#            return memoized(f, function)
#
#        return memoize_wrapper
#
#    dict = {}
#    list = []
#    def memoize_wrapper(*args, **kwargs):
#       key = cPickle.dumps((args, kwargs))
#       try:
#          list.append(list.pop(list.index(key)))
#       except ValueError:
#          dict[key] = function(*args, **kwargs)
#          list.append(key)
#          if limit is not None and len(list) > limit:
#             del dict[list.pop(0)]
#
#       return dict[key]

#    memoize_wrapper._memoize_dict = dict
#    memoize_wrapper._memoize_list = list
#    memoize_wrapper._memoize_limit = limit
#    memoize_wrapper._memoize_origfunc = function
#    memoize_wrapper.func_name = function.func_name
#    return memoize_wrapper



#@memoized
#def fibonacci(n):
#   "Return the nth fibonacci number."
#   print n
#   if n in (0, 1):
#      return n
#   val = fibonacci(n-1) + fibonacci(n-2)
#   return val#
#
#fibonacci(5)
#fibonacci(12)
