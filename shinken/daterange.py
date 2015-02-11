#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2009-2014:
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
import calendar
import re

from shinken.util import get_sec_from_morning, get_day, get_start_of_day, get_end_of_day
from shinken.log import logger

# Get the day number (like 27 in July Tuesday 27 2010 for call:
# 2010, July, Tuesday, -1 (last Tuesday of July 2010)
def find_day_by_weekday_offset(year, month, weekday, offset):
    # get the id of the weekday (1 for Tuesday)
    weekday_id = Daterange.get_weekday_id(weekday)
    if weekday_id is None:
        return None

    # same for month
    month_id = Daterange.get_month_id(month)
    if month_id is None:
        return None

    # thanks calendar :)
    cal = calendar.monthcalendar(year, month_id)

    # If we ask for a -1 day, just reverse cal
    if offset < 0:
        offset = abs(offset)
        cal.reverse()

    # ok go for it
    nb_found = 0
    try:
        for i in xrange(0, offset + 1):
            # in cal 0 mean "there are no day here :)"
            if cal[i][weekday_id] != 0:
                nb_found += 1
            if nb_found == offset:
                return cal[i][weekday_id]
        return None
    except Exception:
        return None


def find_day_by_offset(year, month, offset):
    month_id = Daterange.get_month_id(month)
    if month_id is None:
        return None
    (tmp, days_in_month) = calendar.monthrange(year, month_id)
    if offset >= 0:
        return min(offset, days_in_month)
    else:
        return max(1, days_in_month + offset + 1)


class Timerange(object):

    # entry is like 00:00-24:00
    def __init__(self, entry):
        pattern = r'(\d\d):(\d\d)-(\d\d):(\d\d)'
        m = re.match(pattern, entry)
        self.is_valid = m is not None
        if self.is_valid:
            self.hstart, self.mstart, self.hend, self.mend = map(int, m.groups())

    def __str__(self):
        return str(self.__dict__)

    def get_sec_from_morning(self):
        return self.hstart * 3600 + self.mstart * 60

    def get_first_sec_out_from_morning(self):
        # If start at 0:0, the min out is the end
        if self.hstart == 0 and self.mstart == 0:
            return self.hend * 3600 + self.mend * 60
        return 0

    def is_time_valid(self, t):
        sec_from_morning = get_sec_from_morning(t)
        return (self.is_valid and
                self.hstart * 3600 + self.mstart * 60 <=
                sec_from_morning <=
                self.hend * 3600 + self.mend * 60)

    def is_correct(self):
        return self.is_valid



""" TODO: Add some comment about this class for the doc"""
class Daterange(object):

    weekdays = {  # NB : 0 based : 0 == monday
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6
    }
    months = {  # NB : 1 based : 1 == january..
        'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5,
        'june': 6, 'july': 7, 'august': 8, 'september': 9,
        'october': 10, 'november': 11, 'december': 12
    }
    rev_weekdays = dict((v, k) for k, v in weekdays.items())
    rev_months = dict((v, k) for k, v in months.items())

    def __init__(self, syear, smon, smday, swday, swday_offset,
                 eyear, emon, emday, ewday, ewday_offset, skip_interval, other):
        self.syear = int(syear)
        self.smon = smon
        self.smday = int(smday)
        self.swday = swday
        self.swday_offset = int(swday_offset)
        self.eyear = int(eyear)
        self.emon = emon
        self.emday = int(emday)
        self.ewday = ewday
        self.ewday_offset = int(ewday_offset)
        self.skip_interval = int(skip_interval)
        self.other = other
        self.timeranges = []

        for timeinterval in other.split(','):
            self.timeranges.append(Timerange(timeinterval.strip()))

    def __str__(self):
        return ''  # str(self.__dict__)


    def is_correct(self):
        for tr in self.timeranges:
            if not tr.is_correct():
                return False
        return True

    @classmethod
    def get_month_id(cls, month):
        return Daterange.months[month]

    @classmethod
    def get_month_by_id(cls, month_id):
        return Daterange.rev_months[month_id]

    @classmethod
    def get_weekday_id(cls, weekday):
        return Daterange.weekdays[weekday]

    @classmethod
    def get_weekday_by_id(cls, weekday_id):
        return Daterange.rev_weekdays[weekday_id]

    def get_start_and_end_time(self, ref=None):
        logger.warning("Calling function get_start_and_end_time which is not implemented")
        raise NotImplementedError()

    def is_time_valid(self, t):
        # print "****Look for time valid for", time.asctime(time.localtime(t))
        if self.is_time_day_valid(t):
            # print "is time day valid"
            for tr in self.timeranges:
                # print tr, "is valid?", tr.is_time_valid(t)
                if tr.is_time_valid(t):
                    # print "return True"
                    return True
        return False

    def get_min_sec_from_morning(self):
        mins = []
        for tr in self.timeranges:
            mins.append(tr.get_sec_from_morning())
        return min(mins)

    def get_min_sec_out_from_morning(self):
        mins = []
        for tr in self.timeranges:
            mins.append(tr.get_first_sec_out_from_morning())
        return min(mins)

    def get_min_from_t(self, t):
        if self.is_time_valid(t):
            return t
        t_day_epoch = get_day(t)
        tr_mins = self.get_min_sec_from_morning()
        return t_day_epoch + tr_mins

    def is_time_day_valid(self, t):
        (start_time, end_time) = self.get_start_and_end_time(t)
        if start_time <= t <= end_time:
            return True
        else:
            return False

    def is_time_day_invalid(self, t):
        (start_time, end_time) = self.get_start_and_end_time(t)
        if start_time <= t <= end_time:
            return False
        else:
            return True

    def get_next_future_timerange_valid(self, t):
        # print "Look for get_next_future_timerange_valid for t", t, time.asctime(time.localtime(t))
        sec_from_morning = get_sec_from_morning(t)
        starts = []
        for tr in self.timeranges:
            tr_start = tr.hstart * 3600 + tr.mstart * 60
            if tr_start >= sec_from_morning:
                starts.append(tr_start)
        if starts != []:
            return min(starts)
        else:
            return None

    def get_next_future_timerange_invalid(self, t):
        # print 'Call for get_next_future_timerange_invalid from ', time.asctime(time.localtime(t))
        sec_from_morning = get_sec_from_morning(t)
        # print 'sec from morning', sec_from_morning
        ends = []
        for tr in self.timeranges:
            tr_start = tr.hstart * 3600 + tr.mstart * 60
            if tr_start >= sec_from_morning:
                ends.append(tr_start)
            tr_end = tr.hend * 3600 + tr.mend * 60
            if tr_end >= sec_from_morning:
                ends.append(tr_end)
        # print "Ends:", ends
        # Remove the last second of the day for 00->24h"
        if 86400 in ends:
            ends.remove(86400)
        if ends != []:
            return min(ends)
        else:
            return None

    def get_next_valid_day(self, t):
        if self.get_next_future_timerange_valid(t) is None:
            # this day is finish, we check for next period
            (start_time, end_time) = self.get_start_and_end_time(get_day(t) + 86400)
        else:
            (start_time, end_time) = self.get_start_and_end_time(t)

        if t <= start_time:
            return get_day(start_time)

        if self.is_time_day_valid(t):
            return get_day(t)
        return None

    def get_next_valid_time_from_t(self, t):
        # print "\tDR Get next valid from:", time.asctime(time.localtime(t))
        # print "DR Get next valid from:", t
        if self.is_time_valid(t):
            return t

        # print "DR Get next valid from:", time.asctime(time.localtime(t))
        # First we search fot the day of t
        t_day = self.get_next_valid_day(t)

        # print "DR: T next valid day", time.asctime(time.localtime(t_day))

        # We search for the min of all tr.start > sec_from_morning
        # if it's the next day, use a start of the day search for timerange
        if t < t_day:
            sec_from_morning = self.get_next_future_timerange_valid(t_day)
        else:  # t is in this day, so look from t (can be in the evening or so)
            sec_from_morning = self.get_next_future_timerange_valid(t)
        # print "DR: sec from morning", sec_from_morning

        if sec_from_morning is not None:
            if t_day is not None and sec_from_morning is not None:
                return t_day + sec_from_morning

        # Then we search for the next day of t
        # The sec will be the min of the day
        t = get_day(t) + 86400
        t_day2 = self.get_next_valid_day(t)
        sec_from_morning = self.get_next_future_timerange_valid(t_day2)
        if t_day2 is not None and sec_from_morning is not None:
            return t_day2 + sec_from_morning
        else:
            # I'm not find any valid time
            return None

    def get_next_invalid_day(self, t):
        # print "Look in", self.__dict__
        # print 'DR: get_next_invalid_day for', time.asctime(time.localtime(t))
        if self.is_time_day_invalid(t):
            # print "EARLY RETURN"
            return t

        next_future_timerange_invalid = self.get_next_future_timerange_invalid(t)
        # print "next_future_timerange_invalid:", next_future_timerange_invalid

        # If today there is no more unavailable timerange, search the next day
        if next_future_timerange_invalid is None:
            # print 'DR: get_next_future_timerange_invalid is None'
            # this day is finish, we check for next period
            (start_time, end_time) = self.get_start_and_end_time(get_day(t))
        else:
            # print 'DR: get_next_future_timerange_invalid is',
            # print time.asctime(time.localtime(next_future_timerange_invalid))
            (start_time, end_time) = self.get_start_and_end_time(t)

        # (start_time, end_time) = self.get_start_and_end_time(t)

        # print "START", time.asctime(time.localtime(start_time)),
        # print "END", time.asctime(time.localtime(end_time))
        # The next invalid day can be t day if there a possible
        # invalid time range (timerange is not 00->24
        if next_future_timerange_invalid is not None:
            if start_time <= t <= end_time:
                # print "Early Return next invalid day:", time.asctime(time.localtime(get_day(t)))
                return get_day(t)
            if start_time >= t:
                # print "start_time >= t:", time.asctime(time.localtime(get_day(start_time)))
                return get_day(start_time)
        else:
            # Else, there is no possibility than in our start_time<->end_time we got
            # any invalid time (full period out). So it's end_time+1 sec (tomorrow of end_time)
            return get_day(end_time + 1)

        return None

    def get_next_invalid_time_from_t(self, t):
        if not self.is_time_valid(t):
            return t

        # First we search fot the day of t
        t_day = self.get_next_invalid_day(t)
        # print "FUCK NEXT DAY", time.asctime(time.localtime(t_day))

        # We search for the min of all tr.start > sec_from_morning
        # if it's the next day, use a start of the day search for timerange
        if t < t_day:
            sec_from_morning = self.get_next_future_timerange_invalid(t_day)
        else:  # t is in this day, so look from t (can be in the evening or so)
            sec_from_morning = self.get_next_future_timerange_invalid(t)
        # print "DR: sec from morning", sec_from_morning

        # tr can't be valid, or it will be return at the beginning
        # sec_from_morning = self.get_next_future_timerange_invalid(t)

        # Ok we've got a next invalid day and a invalid possibility in
        # timerange, so the next invalid is this day+sec_from_morning
        # print "T_day", t_day, "Sec from morning", sec_from_morning
        if t_day is not None and sec_from_morning is not None:
            return t_day + sec_from_morning + 1

        # We've got a day but no sec_from_morning: the timerange is full (0->24h)
        # so the next invalid is this day at the day_start
        if t_day is not None and sec_from_morning is None:
            return t_day

        # Then we search for the next day of t
        # The sec will be the min of the day
        t = get_day(t) + 86400
        t_day2 = self.get_next_invalid_day(t)
        sec_from_morning = self.get_next_future_timerange_invalid(t_day2)
        if t_day2 is not None and sec_from_morning is not None:
            return t_day2 + sec_from_morning + 1

        if t_day2 is not None and sec_from_morning is None:
            return t_day2
        else:
            # I'm not find any valid time
            return None




""" TODO: Add some comment about this class for the doc"""
class CalendarDaterange(Daterange):
    def get_start_and_end_time(self, ref=None):
        start_time = get_start_of_day(self.syear, int(self.smon), self.smday)
        end_time = get_end_of_day(self.eyear, int(self.emon), self.emday)
        return (start_time, end_time)



""" TODO: Add some comment about this class for the doc"""
class StandardDaterange(Daterange):
    def __init__(self, day, other):
        self.other = other
        self.timeranges = []

        for timeinterval in other.split(','):
            self.timeranges.append(Timerange(timeinterval.strip()))
        self.day = day

    # It's correct only if the weekday (Sunday, etc) is a valid one
    def is_correct(self):
        b = self.day in Daterange.weekdays
        if not b:
            logger.error("Error: %s is not a valid day", self.day)
        # Check also if Daterange is correct.
        b &= Daterange.is_correct(self)
        return b

    def get_start_and_end_time(self, ref=None):
        now = time.localtime(ref)
        self.syear = now.tm_year
        self.month = now.tm_mon
        # month_start_id = now.tm_mon
        # month_start = Daterange.get_month_by_id(month_start_id)
        self.wday = now.tm_wday
        day_id = Daterange.get_weekday_id(self.day)
        today_morning = get_start_of_day(now.tm_year, now.tm_mon, now.tm_mday)
        tonight = get_end_of_day(now.tm_year, now.tm_mon, now.tm_mday)
        day_diff = (day_id - now.tm_wday) % 7
        return (today_morning + day_diff * 86400, tonight + day_diff * 86400)


""" TODO: Add some comment about this class for the doc"""
class MonthWeekDayDaterange(Daterange):

    # It's correct only if the weekday (Sunday, etc) is a valid one
    def is_correct(self):
        b = True
        b &= self.swday in Daterange.weekdays
        if not b:
            logger.error("Error: %s is not a valid day", self.swday)

        b &= self.ewday in Daterange.weekdays
        if not b:
            logger.error("Error: %s is not a valid day", self.ewday)

        return b

    def get_start_and_end_time(self, ref=None):
        now = time.localtime(ref)

        if self.syear == 0:
            self.syear = now.tm_year
        month_id = Daterange.get_month_id(self.smon)
        day_start = find_day_by_weekday_offset(self.syear, self.smon, self.swday, self.swday_offset)
        start_time = get_start_of_day(self.syear, month_id, day_start)

        if self.eyear == 0:
            self.eyear = now.tm_year
        month_end_id = Daterange.get_month_id(self.emon)
        day_end = find_day_by_weekday_offset(self.eyear, self.emon, self.ewday, self.ewday_offset)
        end_time = get_end_of_day(self.eyear, month_end_id, day_end)

        now_epoch = time.mktime(now)
        if start_time > end_time:  # the period is between years
            if now_epoch > end_time:  # check for next year
                day_end = find_day_by_weekday_offset(self.eyear + 1,
                                                     self.emon, self.ewday, self.ewday_offset)
                end_time = get_end_of_day(self.eyear + 1, month_end_id, day_end)
            else:
                # it s just that the start was the last year
                day_start = find_day_by_weekday_offset(self.syear - 1,
                                                       self.smon, self.swday, self.swday_offset)
                start_time = get_start_of_day(self.syear - 1, month_id, day_start)
        else:
            if now_epoch > end_time:
                # just have to check for next year if necessary
                day_start = find_day_by_weekday_offset(self.syear + 1,
                                                       self.smon, self.swday, self.swday_offset)
                start_time = get_start_of_day(self.syear + 1, month_id, day_start)
                day_end = find_day_by_weekday_offset(self.eyear + 1,
                                                     self.emon, self.ewday, self.ewday_offset)
                end_time = get_end_of_day(self.eyear + 1, month_end_id, day_end)

        return (start_time, end_time)


""" TODO: Add some comment about this class for the doc"""
class MonthDateDaterange(Daterange):
    def get_start_and_end_time(self, ref=None):
        now = time.localtime(ref)
        if self.syear == 0:
            self.syear = now.tm_year
        month_start_id = Daterange.get_month_id(self.smon)
        day_start = find_day_by_offset(self.syear, self.smon, self.smday)
        start_time = get_start_of_day(self.syear, month_start_id, day_start)

        if self.eyear == 0:
            self.eyear = now.tm_year
        month_end_id = Daterange.get_month_id(self.emon)
        day_end = find_day_by_offset(self.eyear, self.emon, self.emday)
        end_time = get_end_of_day(self.eyear, month_end_id, day_end)

        now_epoch = time.mktime(now)
        if start_time > end_time:  # the period is between years
            if now_epoch > end_time:
                # check for next year
                day_end = find_day_by_offset(self.eyear + 1, self.emon, self.emday)
                end_time = get_end_of_day(self.eyear + 1, month_end_id, day_end)
            else:
                # it s just that start was the last year
                day_start = find_day_by_offset(self.syear - 1, self.smon, self.emday)
                start_time = get_start_of_day(self.syear - 1, month_start_id, day_start)
        else:
            if now_epoch > end_time:
                # just have to check for next year if necessary
                day_start = find_day_by_offset(self.syear + 1, self.smon, self.emday)
                start_time = get_start_of_day(self.syear + 1, month_start_id, day_start)
                day_end = find_day_by_offset(self.eyear + 1, self.emon, self.emday)
                end_time = get_end_of_day(self.eyear + 1, month_end_id, day_end)

        return (start_time, end_time)


""" TODO: Add some comment about this class for the doc"""
class WeekDayDaterange(Daterange):
    def get_start_and_end_time(self, ref=None):
        now = time.localtime(ref)

        # If no year, it's our year
        if self.syear == 0:
            self.syear = now.tm_year
        month_start_id = now.tm_mon
        month_start = Daterange.get_month_by_id(month_start_id)
        day_start = find_day_by_weekday_offset(self.syear,
                                               month_start, self.swday, self.swday_offset)
        start_time = get_start_of_day(self.syear, month_start_id, day_start)

        # Same for end year
        if self.eyear == 0:
            self.eyear = now.tm_year
        month_end_id = now.tm_mon
        month_end = Daterange.get_month_by_id(month_end_id)
        day_end = find_day_by_weekday_offset(self.eyear, month_end, self.ewday, self.ewday_offset)
        end_time = get_end_of_day(self.eyear, month_end_id, day_end)

        # Maybe end_time is before start. So look for the
        # next month
        if start_time > end_time:
            month_end_id = month_end_id + 1
            if month_end_id > 12:
                month_end_id = 1
                self.eyear += 1
            month_end = Daterange.get_month_by_id(month_end_id)
            day_end = find_day_by_weekday_offset(self.eyear,
                                                 month_end, self.ewday, self.ewday_offset)
            end_time = get_end_of_day(self.eyear, month_end_id, day_end)

        now_epoch = time.mktime(now)
        # But maybe we look not enought far. We should add a month
        if end_time < now_epoch:
            month_end_id = month_end_id + 1
            month_start_id = month_start_id + 1
            if month_end_id > 12:
                month_end_id = 1
                self.eyear += 1
            if month_start_id > 12:
                month_start_id = 1
                self.syear += 1
            # First start
            month_start = Daterange.get_month_by_id(month_start_id)
            day_start = find_day_by_weekday_offset(self.syear,
                                                   month_start, self.swday, self.swday_offset)
            start_time = get_start_of_day(self.syear, month_start_id, day_start)
            # Then end
            month_end = Daterange.get_month_by_id(month_end_id)
            day_end = find_day_by_weekday_offset(self.eyear,
                                                 month_end, self.ewday, self.ewday_offset)
            end_time = get_end_of_day(self.eyear, month_end_id, day_end)

        return (start_time, end_time)


""" TODO: Add some comment about this class for the doc"""
class MonthDayDaterange(Daterange):
    def get_start_and_end_time(self, ref=None):
        now = time.localtime(ref)
        if self.syear == 0:
            self.syear = now.tm_year
        month_start_id = now.tm_mon
        month_start = Daterange.get_month_by_id(month_start_id)
        day_start = find_day_by_offset(self.syear, month_start, self.smday)
        start_time = get_start_of_day(self.syear, month_start_id, day_start)

        if self.eyear == 0:
            self.eyear = now.tm_year
        month_end_id = now.tm_mon
        month_end = Daterange.get_month_by_id(month_end_id)
        day_end = find_day_by_offset(self.eyear, month_end, self.emday)
        end_time = get_end_of_day(self.eyear, month_end_id, day_end)

        now_epoch = time.mktime(now)

        if start_time > end_time:
            month_end_id = month_end_id + 1
            if month_end_id > 12:
                month_end_id = 1
                self.eyear += 1
            day_end = find_day_by_offset(self.eyear, month_end, self.emday)
            end_time = get_end_of_day(self.eyear, month_end_id, day_end)

        if end_time < now_epoch:
            month_end_id = month_end_id + 1
            month_start_id = month_start_id + 1
            if month_end_id > 12:
                month_end_id = 1
                self.eyear += 1
            if month_start_id > 12:
                month_start_id = 1
                self.syear += 1

            # For the start
            month_start = Daterange.get_month_by_id(month_start_id)
            day_start = find_day_by_offset(self.syear, month_start, self.smday)
            start_time = get_start_of_day(self.syear, month_start_id, day_start)

            # For the end
            month_end = Daterange.get_month_by_id(month_end_id)
            day_end = find_day_by_offset(self.eyear, month_end, self.emday)
            end_time = get_end_of_day(self.eyear, month_end_id, day_end)

        return (start_time, end_time)
