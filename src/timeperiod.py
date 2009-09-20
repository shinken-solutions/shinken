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


#Calendar date: '(\d{4})-(\d{2})-(\d{2}) - (\d{4})-(\d{2})-(\d{2}) / (\d+) ([0-9:, -]+)' => len = 8  => CALENDAR_DATE
#               '(\d{4})-(\d{2})-(\d{2}) / (\d+) ([0-9:, -]+)' => len = 5 => CALENDAR_DATE
#               '(\d{4})-(\d{2})-(\d{2}) - (\d{4})-(\d{2})-(\d{2}) ([0-9:, -]+)' => len = 7 => CALENDAR_DATE
#               '(\d{4})-(\d{2})-(\d{2}) ([0-9:, -]+)' => len = 4 => CALENDAR_DATE
#
#Month week day:'([a-z]*) (\d+) ([a-z]*) - ([a-z]*) (\d+) ([a-z]*) / (\d+) ([0-9:, -]+)' => len = 8 => MONTH WEEK DAY
#               ex: wednesday 1 january - thursday 2 july / 3
#
#               '([a-z]*) (\d+) - ([a-z]*) (\d+) / (\d+) ([0-9:, -]+)' => len = 6
#               ex: february 1 - march 15 / 3 => MONTH DATE
#               ex: monday 2 - thusday 3 / 2 => WEEK DAY
#               ex: day 2 - day 6 / 3 => MONTH DAY
#
#               '([a-z]*) (\d+) - (\d+) / (\d+) ([0-9:, -]+)' => len = 6
#               ex: february 1 - 15 / 3 => MONTH DATE
#               ex: thursday 2 - 4 => WEEK DAY
#               ex: day 1 - 4 => MONTH DAY
#
#               '([a-z]*) (\d+) ([a-z]*) - ([a-z]*) (\d+) ([a-z]*) ([0-9:, -]+)' => len = 7
#               ex: wednesday 1 january - thursday 2 july => MONTH WEEK DAY
#
#               '([a-z]*) (\d+) - (\d+) ([0-9:, -]+)' => len = 7
#               ex: thursday 2 - 4 => WEEK DAY
#               ex: february 1 - 15 / 3 => MONTH DATE
#               ex: day 1 - 4 => MONTH DAY
#
#               '([a-z]*) (\d+) - ([a-z]*) (\d+) ([0-9:, -]+)' => len = 5
#               ex: february 1 - march 15  => MONTH DATE
#               ex: monday 2 - thusday 3  => WEEK DAY
#               ex: day 2 - day 6  => MONTH DAY
#
#               '([a-z]*) (\d+) ([0-9:, -]+)' => len = 3
#               ex: february 3 => MONTH DATE
#               ex: thursday 2 => WEEK DAY
#               ex: day 3 => MONTH DAY
#
#               '([a-z]*) (\d+) ([a-z]*) ([0-9:, -]+)' => len = 4
#               ex: thusday 3 february => MONTH WEEK DAY
#
#               '([a-z]*) ([0-9:, -]+)' => len = 6
#               ex: thusday => normal values
#               
#Types: CALENDAR_DATE              
#       MONTH WEEK DAY        
#       WEEK DAY
#       MONTH DATE
#       MONTH DAY
#
import re, time, calendar
from item import Item, Items
from util import *
#from memoized import memoized
#import psyco
#psyco.full()


def find_day_by_weekday_offset(year, month, weekday, offset):
    weekday_id = Timeperiod.get_weekday_id(weekday)
    if weekday_id is None:
        return None
    month_id = Timeperiod.get_month_id(month)
    if month_id is None:
        return None
    
    cal = calendar.monthcalendar(year, month_id)
    if offset < 0:
        offset = abs(offset)
        for elt in cal:
            elt.reverse()
        cal.reverse()
    nb_found = 0

    try:
        for i in xrange(0, offset + 1):
            if cal[i][weekday_id] != 0:
                nb_found += 1
            if nb_found == offset:
                return cal[i][weekday_id]
        return None
    except:
        return None


def find_day_by_offset(year, month, offset):
    month_id = Timeperiod.get_month_id(month)
    if month_id is None:
        return None
    (tmp, days_in_month) =  calendar.monthrange(year, month_id)
    if offset >= 0:
        return min(offset, days_in_month)
    else:
        return max(1, days_in_month + offset + 1)



class Timerange:
    #entry is like 00:00-24:00
    def __init__(self, entry):
        entries = entry.split('-')
        start = entries[0]
        end = entries[1]
        sentries = start.split(':')
        self.hstart = int(sentries[0])
        self.mstart = int(sentries[1])
        eentries = end.split(':')
        self.hend = int(eentries[0])
        self.mend = int(eentries[1])
        
    def __str__(self):
        return str(self.__dict__)

    def get_sec_from_morning(self):
        return self.hstart*3600 + self.mstart*60

    def is_time_valid(self, t):
        sec_from_morning = get_sec_from_morning(t)
        morning = get_day(t)
        return self.hstart*3600 + self.mstart* 60  <= sec_from_morning <= self.hend*3600 + self.mend* 60
            
        
class Daterange:
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
        self.is_valid_today = False

        
    def __str__(self):
        return ''#str(self.__dict__)


    def check_time_against_period(self, test_time):
        pass


    def get_start_and_end_time(self):
        print "Not implemented"


    def is_timerange_valid(self, t):
        t = get_sec_from_morning(t)
        for tr in self.timeranges:
            if tr.is_time_valid(t):
                return True
        return False


    def is_time_valid(self, t):
        if self.is_time_day_valid(t):
            for tr in self.timeranges:
                if tr.is_time_valid(t):
                    return True
        return False


    def get_min_sec_from_morning(self):
        mins = []
        for tr in self.timeranges:
            mins.append(tr.get_sec_from_morning())
        return min(mins)


    def get_min_from_t(self, t):
        if self.is_time_valid(t):
            return t
        tr_mins = self.get_min_sec_from_morning(t)
        return t_day_epoch + tr_mins
        

    def is_time_day_valid(self, t):
        (start_time, end_time) = self.get_start_and_end_time(t)
        if start_time <= t <= end_time:
            return True
        else:
            return False


    def have_future_tiremange_valid(self, t):        
        starts = []
        for tr in self.timeranges:
            tr_start = tr.hstart * 3600 + tr.mstart * 3600
            if tr_start >= sec_from_morning:
                return True
        return False


    def get_next_future_timerange_valid(self, t): 
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


    def get_next_valid_day(self, t):
        if self.get_next_future_timerange_valid(t) is None:
            #this day is finish, we check for next period
            (start_time, end_time) = self.get_start_and_end_time(get_day(t)+86400)
        else:
            (start_time, end_time) = self.get_start_and_end_time(t)
        if t <= start_time:
            return start_time
        if self.is_time_day_valid(t):
            return t
        return None


    def get_next_valid_time_from_t(self, t):
        if self.is_time_valid(t):
            return t

        #First we search fot the day of t
        t_day = self.get_next_valid_day(t)
        sec_from_morning = self.get_min_sec_from_morning()

        #We search for the min of all tr.start > sec_from_morning
        starts = []
        for tr in self.timeranges:
            tr_start = tr.hstart * 3600 + tr.mstart * 3600
            if tr_start >= sec_from_morning:
                starts.append(tr_start)

        #tr can't be valid, or it will be return at the begining
        sec_from_morning = self.get_next_future_timerange_valid(t)
        if sec_from_morning is not None:
            if t_day is not None and sec_from_morning is not None:
                return t_day + sec_from_morning

        #Then we search for the next day of t
        #The sec will be the min of the day
        t = get_day(t)+86400
        t_day2 = self.get_next_valid_day(t)
        sec_from_morning = self.get_next_future_timerange_valid(t_day2)
        if t_day2 is not None and sec_from_morning is not None:
            return t_day2 + sec_from_morning
        else:
            #I'm not find any valid time
            return None
            


#ex: 2007-01-01 - 2008-02-01
class CalendarDaterange(Daterange):
    def get_start_and_end_time(self, ref=None):
        start_time = get_start_of_day(self.syear, int(self.smon), self.smday)
        end_time = get_end_of_day(self.eyear, int(self.emon), self.emday)
        return (start_time, end_time)



#Like tuesday 00:00-24:00
class StandardDaterange(Daterange):
    def __init__(self, day, other):
        self.other = other
        self.timeranges = []

        for timeinterval in other.split(','):
            self.timeranges.append(Timerange(timeinterval.strip()))
        self.day = day
        self.is_valid_today = False
    

    def get_start_and_end_time(self, ref=None):
        now = time.localtime(ref)
        self.syear = now.tm_year
        self.month = now.tm_mon
        month_start_id = now.tm_mon
        month_start = Timeperiod.get_month_by_id(month_start_id)
        self.wday = now.tm_wday
        day_id = Timeperiod.get_weekday_id(self.day)
        today_morning = get_start_of_day(now.tm_year, now.tm_mon, now.tm_mday)
        tonight = get_end_of_day(now.tm_year, now.tm_mon, now.tm_mday)
        day_diff = (day_id - now.tm_wday) % 7
        return (today_morning + day_diff*86400, tonight + day_diff*86400)


class MonthWeekDayDaterange(Daterange):
    def get_start_and_end_time(self, ref=None):
        now = time.localtime(ref)
        if self.syear == 0:
            self.syear = now.tm_year
        month_id = Timeperiod.get_month_id(self.smon)
        day_start = find_day_by_weekday_offset(self.syear, self.smon, self.swday, self.swday_offset)
        start_time = get_start_of_day(self.syear, month_id, day_start)

        if self.eyear == 0:
            self.eyear = now.tm_year
        month_end_id = Timeperiod.get_month_id(self.emon)
        day_end = find_day_by_weekday_offset(self.eyear, self.emon, self.ewday, self.ewday_offset)
        end_time = get_end_of_day(self.eyear, month_end_id, day_end)

        now_epoch = time.mktime(now)
        if start_time > end_time: #the period is between years
            if now_epoch > end_time:#check for next year
                day_end = find_day_by_weekday_offset(self.eyear + 1, self.emon, self.ewday, self.ewday_offset)
                end_time = get_end_of_day(self.eyear + 1, month_end_id, day_end)
            else:#it s just that start was the last year
                day_start = find_day_by_weekday_offset(self.syear - 1, self.smon, self.swday, self.swday_offset)
                start_time = get_start_of_day(self.syear - 1, month_id, day_start)
        else:
            if now_epoch > end_time:#just have to check for next year if necessery
                day_start = find_day_by_weekday_offset(self.syear + 1, self.smon, self.swday, self.swday_offset)
                start_time = get_start_of_day(self.syear + 1, month_id, day_start)
                day_end = find_day_by_weekday_offset(self.eyear + 1, self.emon, self.ewday, self.ewday_offset)
                end_time = get_end_of_day(self.eyear + 1, month_end_id, day_end)

        return (start_time, end_time)



class MonthDateDaterange(Daterange):
    def get_start_and_end_time(self, ref=None):
        now = time.localtime(ref)
        if self.syear == 0:
            self.syear = now.tm_year
        month_start_id = Timeperiod.get_month_id(self.smon)
        day_start = find_day_by_offset(self.syear, self.smon, self.smday)
        start_time = get_start_of_day(self.syear, month_start_id, day_start)

        if self.eyear == 0:
            self.eyear = now.tm_year
        month_end_id = Timeperiod.get_month_id(self.emon)
        day_end = find_day_by_offset(self.eyear, self.emon, self.emday)
        end_time = get_end_of_day(self.eyear, month_end_id, day_end)

        now_epoch =  time.mktime(now)
        if start_time > end_time: #the period is between years
            if now_epoch > end_time:#check for next year
                day_end = find_day_by_offset(self.eyear + 1, self.emon, self.emday)
                end_time = get_end_of_day(self.eyear + 1, month_end_id, day_end)
            else:#it s just that start was the last year
                day_start = find_day_by_offset(self.syear-1, self.smon, self.emday)
                start_time = get_start_of_day(self.syear-1, month_start_id, day_start)
        else:
            if now_epoch > end_time:#just have to check for next year if necessery
                day_start = find_day_by_offset(self.syear+1, self.smon, self.emday)
                start_time = get_start_of_day(self.syear+1, month_start_id, day_start)
                day_end = find_day_by_offset(self.eyear+1, self.emon, self.emday)
                end_time = get_end_of_day(self.eyear+1, month_end_id, day_end)

        return (start_time, end_time)
        

class WeekDayDaterange(Daterange):
    def get_start_and_end_time(self, ref=None):
        now = time.localtime(ref)
        if self.syear == 0:
            self.syear = now.tm_year
        month_start_id = now.tm_mon
        month_start = Timeperiod.get_month_by_id(month_start_id)
        day_start = find_day_by_weekday_offset(self.syear, month_start, self.swday, self.swday_offset)
        start_time = get_start_of_day(self.syear, month_start_id, day_start)

        if self.eyear == 0:
            self.eyear = now.tm_year
        month_end_id = now.tm_mon
        month_end = Timeperiod.get_month_by_id(month_end_id)
        day_end = find_day_by_weekday_offset(self.eyear, month_end, self.ewday, self.ewday_offset)
        end_time = get_end_of_day(self.eyear, month_end_id, day_end)

        if start_time > end_time:
            month_end_id = month_end_id + 1
            if month_end_id > 12:
                month_end_id = 1
                self.eyear += 1
            day_end = find_day_by_weekday_offset(self.eyear, month_end, self.ewday, self.ewday_offset)
            end_time = get_end_of_day(self.eyear, month_end_id, day_end)
        
        return (start_time, end_time)
        

class MonthDayDaterange(Daterange):
    def get_start_and_end_time(self, ref=None):
        now = time.localtime(ref)
        if self.syear == 0:
            self.syear = now.tm_year
        month_start_id = now.tm_mon
        month_start = Timeperiod.get_month_by_id(month_start_id)
        day_start = find_day_by_offset(self.syear, month_start, self.smday)
        start_time = get_start_of_day(self.syear, month_start_id, day_start)

        if self.eyear == 0:
            self.eyear = now.tm_year
        month_end_id = now.tm_mon
        month_end = Timeperiod.get_month_by_id(month_end_id)
        day_end = find_day_by_offset(self.eyear, month_end, self.emday)
        end_time = get_end_of_day(self.eyear, month_end_id, day_end)

        now_epoch =  time.mktime(now)
                
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
            day_start = find_day_by_offset(self.syear, month_start, self.smday)
            start_time = get_start_of_day(self.syear, month_start_id, day_start)
            day_end = find_day_by_offset(self.eyear, month_end, self.emday)
            end_time = get_end_of_day(self.eyear, month_end_id, day_end)
                    
        return (start_time, end_time)


class Timeperiod:
    id = 0
    weekdays = {'monday' : 0, 'tuesday' : 1, 'wednesday' : 2, 'thursday' : 3, 'friday' : 4, 'saturday' : 5, 'sunday': 6 }
    months = {'january' : 1,'february': 2,'march' : 3, 'april' : 4,'may' : 5,'june' : 6,'july' : 7,'august' : 8,'september' : 9,'october' : 10,'november' : 11,'december' : 12}
    my_type = 'timeperiod'
    
    def __init__(self, params={}):
        self.id = Timeperiod.id
        Timeperiod.id = Timeperiod.id + 1
        self.unresolved = []
        self.dateranges = []
        for key in params:
            if key in ['name', 'alias', 'timeperiod_name', 'exclude']:
                setattr(self, key, params[key])
            else:
                self.unresolved.append(key+' '+params[key])
        self.is_valid_today = False


    def get_name(self):
        return self.timeperiod_name
        

    def clean(self):
        pass


    def check_valid_for_today(self):
        self.is_valid_today = False
        for dr in self.dateranges:
            dr.check_valid_for_today()
            if dr.is_valid_today:
                self.is_valid_today = True
        
        if self.has('exclude'):
            for dr in self.exclude:
                dr.check_valid_for_today()
        

    def is_time_valid(self, t):
        if self.has('exclude'):
            for dr in self.exclude:
                if dr.is_time_valid(t):
                    return False
        for dr in self.dateranges:
            if dr.is_time_valid(t):
                return True
        return False


    #will give the first time > t which is valid
    def get_min_from_t(self, t):
        mins_incl = []
        for dr in self.dateranges:
            mins_incl.append(get_min_from_t(t))
        return min(mins_incl)


    #will give the first time > t which is not valid
    def get_not_in_min_from_t(self, f):
        pass


    def get_next_valid_time(self):
        now = time.mktime(time.localtime())
        dr_mins = []
        for dr in self.dateranges:
            dr_mins.append(dr.get_next_valid_time())
        local_min = min(dr_mins)
        if local_min < now:
            return 0
        else:
            return local_min


    def get_next_valid_time_from_t(self, t):
        dr_mins = []
        for dr in self.dateranges:
            dr_mins.append(dr.get_next_valid_time_from_t(t))
        local_min = min(dr_mins)
        return local_min

    
    def get_month_id(cls, month):
        try:
            return Timeperiod.months[month]
        except:
            return None
    get_month_id = classmethod(get_month_id)


    #@memoized
    def get_month_by_id(cls, id):
        id = id % 12
        for key in Timeperiod.months:
            if id == Timeperiod.months[key]:
                return key
        return None
    get_month_by_id = classmethod(get_month_by_id)


    def get_weekday_id(cls, weekday):
        try:
            return Timeperiod.weekdays[weekday]
        except:
            return None
    get_weekday_id = classmethod(get_weekday_id)


    def get_weekday_by_id(cls, id):
        id = id % 7
        for key in Timeperiod.weekdays:
            if id == Timeperiod.weekdays[key]:
                return key
        return None
    get_weekday_by_id = classmethod(get_weekday_by_id)


    def has(self, prop):
        try:
            getattr(self,prop)
        except:
            return False
        return True


    def __str__(self):
        s = ''
        s += str(self.__dict__)+'\n'
        for elt in self.dateranges:
            s += str(elt)
            (start,end) = elt.get_start_and_end_time()
            start = time.asctime(time.localtime(start))
            end = time.asctime(time.localtime(end))
            s += "\nStart and end:"+str((start, end))
        return s

        
    def resolve_daterange(self, dateranges, entry):
        #print "Trying to resolve ", entry
        values = None

        res = re.search('(\d{4})-(\d{2})-(\d{2}) - (\d{4})-(\d{2})-(\d{2}) / (\d+)[\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            #print "Googd catch 1"
            (syear, smon, smday, eyear, emon, emday, skip_interval, other) = res.groups()
            dateranges.append(CalendarDaterange(syear, smon, smday, 0, 0, eyear, emon, emday, 0, 0, skip_interval, other))
            return
        
        res = re.search('(\d{4})-(\d{2})-(\d{2}) / (\d+)[\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            #print "Good catch 2"
            (syear, smon, smday, skip_interval, other) = res.groups() 
            eyear = syear
            emon = smon
            emday = smday
            dateranges.append(CalendarDaterange(syear, smon, smday, 0, 0, eyear, emon, emday, 0, 0, skip_interval, other))
            return

        res = re.search('(\d{4})-(\d{2})-(\d{2}) - (\d{4})-(\d{2})-(\d{2})[\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            #print "Googd catch 3"
            (syear, smon, smday, eyear, emon, emday, other) = res.groups()
            dateranges.append(CalendarDaterange(syear, smon, smday, 0, 0, eyear, emon, emday, 0, 0, 0, other))
            return

        res = re.search('(\d{4})-(\d{2})-(\d{2})[\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            #print "Googd catch 4"
            (syear, smon, smday, other) = res.groups()
            eyear = syear
            emon = smon
            emday = smday
            dateranges.append(CalendarDaterange(syear, smon, smday, 0, 0, eyear, emon, emday, 0, 0, 0, other))
            return

        res = re.search('([a-z]*) ([\d-]+) ([a-z]*) - ([a-z]*) ([\d-]+) ([a-z]*) / (\d+)[\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            #print "Googd catch 5"
            (swday, swday_offset, smon, ewday, ewday_offset, emon, skip_interval, other) = res.groups()
            dateranges.append(MonthWeekDayDaterange(0, smon, 0, swday, swday_offset, 0, emon, 0, ewday, ewday_offset, skip_interval, other))
            return
        
        res = re.search('([a-z]*) ([\d-]+) - ([a-z]*) ([\d-]+) / (\d+)[\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            #print "Googd catch 6"
            (t0, smday, t1, emday, skip_interval, other) = res.groups()
            if t0 in Timeperiod.weekdays and t1 in Timeperiod.weekdays:
                swday = t0
                ewday = t1
                swday_offset = smday
                ewday_offset = emday
                dateranges.append(WeekDayDaterange(0, 0, 0, swday, swday_offset, 0,0,0, ewday, ewday_offset, skip_interval, other))
                return
            elif t0 in Timeperiod.months and t1 in Timeperiod.months:
                smon = t0
                emon = t1
                dateranges.append(MonthDateDaterange(0, smon, smday, 0,0,0,emon,emday,0,0,skip_interval,other))
                return
            elif t0 == 'day' and t1 == 'day':
                dateranges.append(MonthDayDaterange(0,0,smday,0,0,0,0,emday, 0,0,skip_interval, other))
                return

        res = re.search('([a-z]*) ([\d-]+) - ([\d-]+) / (\d+)[\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            #print "Googd catch 7"
            (t0, smday, emday, skip_interval, other) = res.groups()
            if t0 in Timeperiod.weekdays:
                swday = t0
                swday_offset = smday
                ewday = swday
                ewday_offset = emday
                dateranges.append(WeekDayDaterange(0, 0, 0, swday, swday_offset, 0,0,0, ewday, ewday_offset, skip_interval, other))
                return
            elif t0 in Timeperiod.months:
                smon = t0
                emon = smon
                dateranges.append(MonthDateDaterange(0, smon, smday, 0,0,0,emon,emday,0,0,skip_interval, other))
                return
            elif t0 == 'day':
                dateranges.append(MonthDayDaterange(0,0,smday,0,0,0,0,emday,0,0,skip_interval,other))
                return


        res = re.search('([a-z]*) ([\d-]+) ([a-z]*) - ([a-z]*) ([\d-]+) ([a-z]*) [\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            #print "Googd catch 8"
            (swday, swday_offset, smon, ewday, ewday_offset, emon, other) = res.groups()
            #print "Debug:", (swday, swday_offset, smon, ewday, ewday_offset, emon, other)
            dateranges.append(MonthWeekDayDaterange(0, smon, 0, swday, swday_offset, 0, emon, 0, ewday, ewday_offset, 0, other))
            return

        
        res = re.search('([a-z]*) ([\d-]+) - ([\d-]+)[\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            #print "Googd catch 9"
            (t0, smday, emday, other) = res.groups()
            if t0 in Timeperiod.weekdays:
                swday = t0
                swday_offset = smday
                ewday = swday
                ewday_offset = emday
                dateranges.append(WeekDayDaterange(0, 0, 0, swday, swday_offset, 0,0,0, ewday, ewday_offset, 0, other))
                return
            elif t0 in Timeperiod.months:
                smon = t0
                emon = smon
                dateranges.append(MonthDateDaterange(0, smon, smday, 0,0,0,emon,emday,0,0, 0, other))
                return
            elif t0 == 'day':
                dateranges.append(MonthDayDaterange(0,0,smday,0,0,0,0,emday,0,0,0,other))
                return

        res = re.search('([a-z]*) ([\d-]+) - ([a-z]*) ([\d-]+)[\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            #print "Googd catch 10"
            (t0, smday, t1, emday, other) = res.groups()
            if t0 in Timeperiod.weekdays and t1 in Timeperiod.weekdays:
                swday = t0
                ewday = t1
                swday_offset = smday
                ewday_offset = emday
                dateranges.append(WeekDayDaterange(0, 0, 0, swday, swday_offset, 0,0,0, ewday, ewday_offset, 0, other))
                return
            elif t0 in Timeperiod.months and t1 in Timeperiod.months:
                smon = t0
                emon = t1
                dateranges.append(MonthDateDaterange(0, smon, smday, 0,0,0,emon,emday,0,0, 0,other))
                return
            elif t0 == 'day' and t1 == 'day':
                dateranges.append(MonthDayDaterange(0,0,smday,0,0,0,0,emday, 0,0, 0, other))
                return

        res = re.search('([a-z]*) ([\d-]+) ([a-z]*)[\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            #print "Good catch 11"
            (t0, swday_offset, t1,other) = res.groups()
            if t0 in Timeperiod.weekdays and t1 in Timeperiod.months:
                swday = t0
                smon = t1
                emon = smon
                ewday = swday
                ewday_offset = swday_offset
                dateranges.append(MonthWeekDayDaterange(0, smon, 0, swday, swday_offset,0,emon,0,ewday,ewday_offset,0,other))
                return

        res = re.search('([a-z]*) ([\d-]+)[\s\t]+([0-9:, -]+)', entry)
        if res is not None:
            #print "Good catch 12"
            (t0, smday, other) = res.groups()
            if t0 in Timeperiod.weekdays:
                swday = t0
                swday_offset = smday
                ewday = swday
                ewday_offset = swday_offset
                dateranges.append(WeekDayDaterange(0,0,0,swday,swday_offset,0,0,0,ewday,ewday_offset,0,other))
                return
            if t0 in Timeperiod.months:
                smon = t0
                emon = smon
                emday = smday
                dateranges.append(MonthDateDaterange(0, smon, smday, 0,0,0,emon,emday,0,0, 0,other))
                return
            if t0 == 'day':
                emday = smday
                dateranges.append(MonthDayDaterange(0,0,smday,0,0,0,0,emday, 0,0, 0, other))
                return

        res = re.search('([a-z]*)[\s\t]+([0-9:, -]+)', entry)
        if res is not None:
            #print "Good catch 13"
            (t0, other) = res.groups()
            if t0 in Timeperiod.weekdays:
                day = t0
                dateranges.append(StandardDaterange(day, other))
                return
        print "No match for", entry

    
    #create daterange from unresolved param
    def explode(self, timeperiods):
        for entry in self.unresolved:
            #print "Revolving entry", entry
            self.resolve_daterange(self.dateranges, entry)
        self.unresolved = []


    #Will make tp in exclude with id of the timeperiods
    def linkify(self, timeperiods):
        new_exclude = []
        if self.has('exclude'):
            #print "I have excluded"
            excluded_tps = self.exclude.split(',')
            #print "I will exclude from:", excluded_tps
            for tp_name in excluded_tps:
                new_exclude.append(timeperiods.find_id_by_name(tp_name))
        self.exclude = new_exclude
        


class Timeperiods(Items):
    name_property = "timeperiod_name"
    inner_class = Timeperiod

                                   
    def explode(self):
        for id in self.items:
            tp = self.items[id]
            tp.explode(self)


    def check_valid_for_today(self):
        for id in self.items:
            tp = self.items[id]
            tp.check_valid_for_today()


    def linkify(self):
        for id in self.items:
            tp = self.items[id]
            tp.linkify(self)



if __name__ == '__main__':
    t = Timeperiod()
    test = ['1999-01-28	 00:00-24:00',
            'monday 3			00:00-24:00		',
            'day 2			00:00-24:00',
            'february 10		00:00-24:00',
            'february -1 00:00-24:00',
            'friday -2			00:00-24:00',
            'thursday -1 november 00:00-24:00',
            '2007-01-01 - 2008-02-01	00:00-24:00',
            'monday 3 - thursday 4	00:00-24:00',
            'day 1 - 15		00:00-24:00',
            'day 20 - -1		00:00-24:00',
            'july -10 - -1		00:00-24:00',
            'april 10 - may 15		00:00-24:00',
            'tuesday 1 april - friday 2 may 00:00-24:00',
            '2007-01-01 - 2008-02-01 / 3 00:00-24:00',
            '2008-04-01 / 7		00:00-24:00',
            'day 1 - 15 / 5		00:00-24:00',
            'july 10 - 15 / 2 00:00-24:00',
            'tuesday 1 april - friday 2 may / 6 00:00-24:00',
            'tuesday 1 october - friday 2 may / 6 00:00-24:00',
            'monday 3 - thursday 4 / 2 00:00-24:00',
            'monday 4 - thursday 3 / 2 00:00-24:00',
            'day -1 - 15 / 5		01:00-24:00,00:30-05:60',
            'tuesday 00:00-24:00',
            'sunday 00:00-24:00',
            'saturday 03:00-24:00,00:32-01:02',
            'wednesday 09:00-15:46,00:00-21:00',
            'may 7 - february 2 00:00-10:00',
            'day -1 - 5 00:00-10:00',
            'tuesday 1 february - friday 1 may 01:00-24:00,00:30-05:60',
            'december 2 - may -15		00:00-24:00',
            ]
    for entry in test:
        print "**********************"
        t=Timeperiod()
        t.resolve_daterange(t.dateranges, entry)
        #t.exclude = []
        #t.resolve_daterange(t.exclude, 'monday 00:00-19:00')
        #t.check_valid_for_today()
        now = time.time()
        #print "Is valid NOW?", t.is_time_valid(now)
        t_next = t.get_next_valid_time_from_t(now + 5*60)
        if t_next is not None:
            print "Get next valid for now + 5 min ==>", time.asctime(time.localtime(t_next)),"<=="
        else:
            print "===> No future time!!!"
        #print "Is valid?", t.is_valid_today
        #print "End date:", t.get_end_time()
        #print "Next valid", time.asctime(time.localtime(t.get_next_valid_time()))
        print str(t)+'\n\n'
    t=Timeperiod()
    t.resolve_daterange(t.dateranges, 'day -1 - 5 00:00-10:00')
    for i in xrange(1, 1000):
        t_next = t.get_next_valid_time_from_t(now + i*60)
