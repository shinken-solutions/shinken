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

import Queue
from shinken.log import logger


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


class TopBaseLiveStatusStack(object):
    pass


class LiveStatusStack(TopBaseLiveStatusStack):
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

    def __xinit__(self, *args, **kw):
        self.type = 'lambda'
        logger.info("[Livestatus Stack] I am a %s" % type(self))
        logger.info("[Livestatus Stack] My parents are %s" % str([c.__name__ for c in self.__class__.__bases__]))
        logger.info("[Livestatus Stack] My first parent is %s", str(self.__class__.__bases__[0].__name__))
        if self.__class__.__name__ == 'LiveStatusStack':
            self.__class__.__bases__[0].__init__(self, *args, **kw)

    def not_elements(self):
        top_filter = self.get_stack()
        def negate_filter(ref):
            return not top_filter(ref)
        self.put_stack(negate_filter)

    def and_elements(self, num):
        """Take num filters from the stack, and them and put the result back"""
        if num > 1:
            filters = []
            for _ in range(num):
                filters.append(self.get_stack())

            # Take from the stack:
            # Make a combined anded function
            # Put it on the stack
            # List of functions taking parameter ref
            def and_filter(ref):
                myfilters = filters
                failed = False
                for filt in myfilters:
                    if not filt(ref):
                        failed = True
                        break
                    else:
                        pass
                return not failed
            self.put_stack(and_filter)

    def or_elements(self, num):
        """Take num filters from the stack, or them and put the result back"""
        if num > 1:
            filters = []
            for _ in range(num):
                filters.append(self.get_stack())

            def or_filter(ref):
                myfilters = filters
                failed = True
                # Applying the filters in reversed order is faster. (Shown by measuring runtime)
                for filt in reversed(myfilters):
                    if filt(ref):
                        failed = False
                        break
                    else:
                        pass
                return not failed
            self.put_stack(or_filter)

    def get_stack(self):
        """Return the top element from the stack or a filter which is always true"""
        if self.qsize() == 0:
            return lambda x: True
        else:
            return self.get()

    def put_stack(self, element):
        """Wrapper for a stack put operation which corresponds to get_stack"""
        self.put(element)


try:
    Queue.LifoQueue
    TopBaseLiveStatusStack.__bases__ = (Queue.LifoQueue, object)
    #LiveStatusStack.__bases__ += (Queue.LifoQueue, )
except AttributeError:
    # Python 2.4 and 2.5 do not have it.
    # Use our own implementation.
    TopBaseLiveStatusStack.__bases__ = (MyLifoQueue, object)
    #LiveStatusStack.__bases__ += (MyLifoQueue, )
