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
# MERCHANTABILITY or FITNESS for A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

import re
import time
from heapq import nsmallest
from operator import itemgetter
from livestatus_query_metainfo import LiveStatusQueryMetainfo, CACHE_IMPOSSIBLE, CACHE_PROGRAM_STATIC, CACHE_GLOBAL_STATS, CACHE_GLOBAL_STATS_WITH_STATETYPE, CACHE_HOST_STATS, CACHE_SERVICE_STATS, CACHE_IRREVERSIBLE_HISTORY
from counter import Counter
from shinken.log import logger


class LFUCacheMiss(Exception):
    pass


class LFU(object):
    """
    This class implements a dictionary which has a limited number of elements.
    Whenever the maximum number of elements is reached during a write operation
    the element which was read least times is deleted.
    It was inspired by
    http://code.activestate.com/recipes/498245-lru-and-lfu-cache-decorators/
    but LFU is much more simpler.
    """

    def __init__(self, maxsize=100):
        self.storage = {}
        self.maxsize = maxsize
        self.hits = self.misses = 0
        self.use_count = Counter()           # times each key has been accessed

    def clear(self):
        self.storage = {}
        self.use_count = Counter()
        self.hits = self.misses = 0

    def get(self, key):
        self.use_count[key] += 1
        try:
            result = self.storage[key]
            logger.info("[Livestatus Broker Query Cache] cache HIT")
            self.hits += 1
        except KeyError:
            result = []
            self.misses += 1
            raise LFUCacheMiss
        return result

    def put(self, key, data):
        self.storage[key] = data
        if len(self.storage) > self.maxsize:
            for key, _ in nsmallest(self.maxsize // 10, self.use_count.iteritems(), key=itemgetter(1)):
                del self.storage[key], self.use_count[key]
        pass

    def __str__(self):
        text = 'LFU-------------------\n'
        try:
            text += 'hit rate %.2f%%\n' % (100 * self.hits / (self.hits + self.misses))
        except ZeroDivisionError:
            text += 'hit rate 0%\n'
        for k in self.storage:
            text += 'key %10s (%d used)\n' % (str(k), self.use_count[k])
        return text


class LiveStatusQueryCache(object):
    """
    A class describing a collection of livestatus query caches.
    As we have several categories of queries, we also have several caches.
    The validity of each of it can be influenced by different changes through
    update broks.
    """

    def __init__(self):
        self.categories = []
        # cache_GLOBAL_STATS
        self.categories.append(LFU())
        # cache_GLOBAL_STATS_WITH_STATEtype
        self.categories.append(LFU())
        self.categories.append(LFU())
        self.categories.append(LFU())
        self.categories.append(LFU())
        self.categories.append(LFU())
        self.categories.append(LFU())
        self.enabled = True

    def disable(self):
        self.enabled = False

    def invalidate_category(self, category):
        """
        Throw away all cached results of a certain class.
        For example, if there is a state change, we must recalculate
        the data for the tactical overview.
        """
        try:
            logger.debug("[Livestatus Broker Query Cache] I wipe sub-cache: %s" % str(category))
            self.categories[category].clear()
        except Exception:
            pass

    def wipeout(self):
        if not self.enabled:
            return
        for cat in range(len(self.categories)):
            self.categories[cat].clear()

    def get_cached_query(self, query):
        """
        query is only the metainfo part of the original query
        """
        if not self.enabled:
            return (False, False, [])
        logger.debug("[Livestatus Broker Query Cache] I search the cache for categories %s with key %s and data %s" % (str(query.cache_category), str(query.key), str(query.data)))
        try:
            return (query.cache_category != cache_IMPOSSIBLE, True, self.categories[query.cache_category].get(query.key))
        except LFUCacheMiss:
            return (query.cache_category != cache_IMPOSSIBLE, False, [])

    def cache_query(self, query, result):
        """Puts the result of a livestatus query (metainfo) into the cache."""

        if not self.enabled:
            return
        logger.info("[Livestatus Broker Query Cache] I put in the cache for %s with key %s" % (str(query.cache_category), str(query.key)))
        self.categories[query.cache_category].put(query.key, result)

    def impact_assessment(self, brok, obj):
        """
        Find out if there are changes to the object which will affect
        the validity of cached data.
        """
        if not self.enabled:
            return
        try:
            if brok.data['state_id'] != obj.state_id:
                logger.info("[Livestatus Broker Query Cache] Detected statechange: %s" % str(obj))
                self.invalidate_category(cache_GLOBAL_STATS)
                self.invalidate_category(cache_SERVICE_STATS)
            if brok.data['state_type_id'] != obj.state_type_id:
                logger.info("[Livestatus Broker Query Cache] Detected statetypechange: %s" % str(obj))
                self.invalidate_category(cache_GLOBAL_STATS_WITH_STATEtype)
                self.invalidate_category(cache_SERVICE_STATS)
            logger.debug("[Livestatus Broker Query Cache] Obj State id: %d and State type id: %d, Data state id: %d abd state type id: %d" % (obj.state_id, obj.state_type_id, brok.data['state_id'], brok.data['state_type_id']))
        except Exception:
            pass
