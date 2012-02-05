# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2012:
#     Gabes Jean, naparuba@gmail.com
#     Gerhard Lausser, Gerhard.Lausser@consol.de
#     Gregory Starck, g.starck@gmail.com
#     Hartmut Goebel, h.goebel@goebel-consult.de
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


import time
import re

from livestatus_query import LiveStatusQuery
from livestatus_wait_query import LiveStatusWaitQuery
from livestatus_command_query import LiveStatusCommandQuery

CACHE_GLOBAL_STATS = 0
CACHE_GLOBAL_STATS_WITH_STATETYPE = 1
CACHE_HOST_STATS = 2
CACHE_SERVICE_STATS = 3

class LiveStatusQueryCache:

    """A class describing a livestatus query cache."""

    def __init__(self):
        self.categories = [{}, {}, {}]
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
            print "i wipe sub-cache", category
            self.categories[category] = {}
        except Exception:
            pass

    def wipeout(self):
        if not self.enabled:
            return
        for cat in range(len(self.categories)):
            print "WIPEOUT CAT", cat
            self.categories[cat] = {}

    def get_cached_query(self, data):
        if not self.enabled:
            return (False, [])
        print "I SEARCH THE CACHE FOR", data
        cacheable, category, key = self.strip_query(data)
        if self.categories[category].get(key, []):
            print "CACHE HIT"
        return (cacheable, self.categories[category].get(key, []))

    def strip_query(self, data):
        cacheable = True
        category = CACHE_GLOBAL_STATS
        for line in [l.strip() for l in data.splitlines()]:
            if ':' in line and not ' ' in line:
                line = line.replace(':', ': ')
            keyword = line.split(' ')[0].rstrip(':')
            if len(line) == 0:
                pass
            if keyword in ('Localtime'):
                # i dont't like this Localtime, but we usually can ignore it
                pass
            elif keyword == 'Columns':
                _, columns = re.split(r"[\s]+", line, 1)
                if [c for c in re.compile(r'\s+').split(columns) if c.endswith('state_type')]:
                    category = CACHE_GLOBAL_STATS_WITH_STATETYPE
            elif keyword == 'Stats':
                pass
            elif keyword == 'Filter':
                try:
                    _, attribute, operator, reference = re.split(r"[\s]+", line, 3)
                except:
                    _, attribute, operator = re.split(r"[\s]+", line, 2)
                    reference = ''
                if attribute == 'time':
                    # That's a showstopper. We can't cache time-critical
                    # informations, because within one second a lot of things
                    # can change.
                    cacheable = False
        if cacheable:
            return (cacheable, category, hash(data))
        else:
            return (False, None, None)

            

    def find_query(self, data):
        pass

    def query_hash(self, data):
        pass

    def query_hash_with_time(self, data):
        pass

    def cache_query(self, data, result):
        """Puts the result of a livestatus query into the cache."""

        if not self.enabled:
            return
        cacheable, category, key = self.strip_query(data)
        print "I PUT IN THE CACHE FOR", key
        self.categories[category][key] = result

    def judge_situation(self, brok, obj):
        if not self.enabled:
            return
        try:
            if brok.data['state_id'] != obj.state_id:
                print "DETECTED STATECHANGE", obj
                self.invalidate_category(CACHE_GLOBAL_STATS)
            if brok.data['state_type_id'] != obj.state_type_id:
                print "DETECTED STATETYPECHANGE", obj
                self.invalidate_category(CACHE_GLOBAL_STATS_WITH_STATETYPE)
            print obj.state_id, obj.state_type_id, brok.data['state_id'], brok.data['state_type_id']
        except Exception:
            pass

