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

import re, time, calendar
#from memoized import memoized

############################### SEQUENCES ###############################
def get_sequence():
    i = 0
    while True:
        i = i + 1
        yield i
                            

################################### TIME ##################################
#@memoized
def get_end_of_day(year, month_id, day):
    end_time = (year, month_id, day, 23, 59, 59, 0, 0, -1)
    end_time_epoch = time.mktime(end_time)+1.0
    return end_time_epoch


#@memoized
def print_date(t):
    return time.asctime(time.localtime(t))


#@memoized
def get_day(t):
    return t - get_sec_from_morning(t)


#@memoized
def get_sec_from_morning(t):
    t_lt = time.localtime(t)
    h = t_lt.tm_hour
    m = t_lt.tm_min
    s = t_lt.tm_sec
    return h * 3600 + m * 60 + s


#@memoized
def get_start_of_day(year, month_id, day):
    start_time = (year, month_id, day, 00, 00, 00, 0, 0, -1)
    start_time_epoch = time.mktime(start_time)
    return start_time_epoch

################################# Pythonization ###########################

def to_int(val):
    return int(val)

def to_char(val):
    return val[0]

def to_split(val):
    val = val.split(',')
    if val == ['']:
        val = []
    return val

#bool('0') = true, so...
def to_bool(val):
    if val == '1':
        return True
    else:
        return False

def from_bool_to_string(b):
    if b :
        return '1'
    else:
        return '0'


###################### Sorting ################
def scheduler_no_spare_first(x, y):
    if x.spare and not y.spare:
        return 1
    elif x.spare and y.spare:
        return 0
    else:
        return -1


#-1 is x first, 0 equal, 1 is y first 
def alive_then_spare_then_deads(x, y):
    print "Alive_then for", x, y
    #First are alive
    if x.alive and not y.alive:
        return -1
    if y.alive and not x.alive:
        return 0
    #if not alive both, I really don't care...
    if not x.alive and not y.alive:
        return -1
    #Ok, both are alive... now spare after no spare
    if not x.spare:
        return -1
    #x is a spare, so y must be before, even if
    #y is a spare
    if not y.spare:
        return 1
    return 0
        


##################### Cleaning ##############
def strip_and_uniq(tab):
    new_tab = set()
    for elt in tab:
        new_tab.add(elt.strip())
    return list(new_tab)
