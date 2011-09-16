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



import Queue


class MyLifoQueue(Queue.Queue):
    """A class that implements a Fifo.
    
    Python versions < 2.5 do not have the Queue.LifoQueue class.
    MyLifoQueue overwrites methods of the Queue.Queue class and
    then behaves like Queue.LifoQueue.
    
    """
    
    def _init(self, maxsize):
        self.maxsize = maxsize
        self.queue = []


    def _qsize(self, len=len):
        return len(self.queue)


    def _put(self, item):
        self.queue.append(item)


    def _get(self):
        return self.queue.pop()



class LiveStatusStack:
    """A Lifo queue for filter functions.
    
    This class inherits either from MyLifoQueue or Queue.LifoQueue
    whatever is available with the current python version.
    
    Public functions:
    and_elements -- takes a certain number (given as argument)
    of filters from the stack, creates a new filter and puts
    this filter on the stack. If these filters are lambda functions,
    the new filter is a boolean and of the underlying filters.
    If the filters are sql where-conditions, they are also concatenated
    with and to form a new string containing a more complex where-condition.
    
    or_elements --- the same, only that the single filters are
    combined with a logical or.
    
    """
    
    def __init__(self, *args, **kw):
        self.type = 'lambda'
        self.__class__.__bases__[0].__init__(self, *args, **kw)


    def and_elements(self, num):
        """Take num filters from the stack, and them and put the result back"""
        if num > 1:
            filters = []
            for i in range(num):
                filters.append(self.get())
            # Take from the stack:
            # Make a combined anded function
            # Put it on the stack
            if self.type == 'sql':
                # Must be a SQL filter
                and_clause = '(' + (' AND ').join([ x()[0] for x in filters ]) + ')'
                and_values = reduce(lambda x, y: x+y, [ x()[1] for x in filters ])
                and_filter = lambda : [and_clause, and_values]
            else:
                # List of functions taking parameter ref
                def and_filter(ref):
                    myfilters = filters
                    failed = False
                    for filter in myfilters:
                        if not filter(ref):
                            failed = True
                            break
                        else:
                            pass
                    return not failed
            self.put(and_filter)


    def or_elements(self, num):
        """Take num filters from the stack, or them and put the result back"""
        if num > 1:
            filters = []
            for i in range(num):
                filters.append(self.get())
            if self.type == 'sql':
                or_clause = '(' + (' OR ').join([ x()[0] for x in filters ]) + ')'
                or_values = reduce(lambda x, y: x+y, [ x()[1] for x in filters ])
                or_filter = lambda : [or_clause, or_values]
            else:
                def or_filter(ref):
                    myfilters = filters
                    failed = True
                    for filter in myfilters:
                        if filter(ref):
                            failed = False
                            break
                        else:
                            pass
                    return not failed
            self.put(or_filter)


    def get_stack(self):
        """Return the top element from the stack or a filter which is always true"""
        if self.qsize() == 0:
            if self.type == 'sql':
                return lambda : ["1 = ?", [1]]
            else:
                return lambda x : True
        else:
            return self.get()


    def put_stack(self, element):
        """Wrapper for a stack put operation which corresponds to get_stack"""
        self.put(element)


try:
    Queue.LifoQueue
    LiveStatusStack.__bases__ = (Queue.LifoQueue,)
except AttributeError:
    # Ptyhon 2.4 and 2.5 do not have it.
    # Use our own implementation.
    LiveStatusStack.__bases__ = (MyLifoQueue,)
