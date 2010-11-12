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

import time, calendar, re
try:
    from ClusterShell.NodeSet import NodeSet
except ImportError:
    NodeSet = None

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
    end_time_epoch = time.mktime(end_time)
    return end_time_epoch


#@memoized
def print_date(t):
    return time.asctime(time.localtime(t))


#@memoized
def get_day(t):
    return int(t - get_sec_from_morning(t))


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


#change a time in seconds like 3600 into a format : 0d 1h 0m 0s
def format_t_into_dhms_format(t):
    s = t
    m,s=divmod(s,60)
    h,m=divmod(m,60)
    d,h=divmod(h,24)
    return '%sd %sh %sm %ss' % (d, h, m, s)


################################# Pythonization ###########################
#first change to foat so manage for example 25.0 to 25
def to_int(val):
    return int(float(val))

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

def from_bool_to_int(b):
    if b :
        return 1
    else:
        return 0

def from_list_to_split(val):
    val = ','.join(['%s' % v for v in val])
    return val

def from_float_to_int(val):
    val = int(val)
    return val

#take a list of hosts and return a list
#of all host_names
def to_hostnames_list(tab):
    r = []
    for h in tab:
        if hasattr(h, 'host_name'):
            r.append(h.host_name)
    return r

#Wil lcreate a dict with 2 lists:
#*services : all services of the tab
#*hosts : all hosts of the tab
def to_svc_hst_distinct_lists(tab):
    r = {'hosts' : [], 'services' : []}
    for e in tab:
        cls = e.__class__
        if cls.my_type == 'service':
            name = e.get_dbg_name()
            r['services'].append(name)
        else:
            name = e.get_dbg_name()
            r['hosts'].append(name)
    return r

#Just get the string name of the object
#(like for realm)
def get_obj_name(obj):
    return obj.get_name()


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

#-1 is x first, 0 equal, 1 is y first
def sort_by_ids(x, y):
    if x.id < y.id:
        return -1
    if x.id > y.id:
        return 1
    #So is equal
    return 0
    


##################### Cleaning ##############
def strip_and_uniq(tab):
    new_tab = set()
    for elt in tab:
        new_tab.add(elt.strip())
    return list(new_tab)



#################### Patern change application (mainly for host) #######

def expand_xy_patern(pattern):
    ns = NodeSet(pattern)
    if len(ns) > 1:
        for elem in ns:
            for a in expand_xy_patern(elem):
                yield a
    else:
        yield pattern




#This function is used to generate all patern change as
#recursive list.
#for example, for a [(1,3),(1,4),(1,5)] xy_couples,
#it will generate a 60 item list with:
#Rule: [1, '[1-5]', [1, '[1-4]', [1, '[1-3]', []]]]
#Rule: [1, '[1-5]', [1, '[1-4]', [2, '[1-3]', []]]]
#...
def got_generation_rule_patern_change(xy_couples):
    res = []
    xy_cpl = xy_couples
    if xy_couples == []:
        return []
    (x, y) = xy_cpl[0]
    for i in xrange(x, y+1):
        n = got_generation_rule_patern_change(xy_cpl[1:])
        if n != []:
            for e in n:
                res.append( [i, '[%d-%d]'%(x,y), e])
        else:
            res.append( [i, '[%d-%d]'%(x,y), []])
    return res
    

#this fuction apply a recursive patern change
#generate by the got_generation_rule_patern_change
#function.
#It take one entry of this list, and apply
#recursivly the change to s like :
#s = "Unit [1-3] Port [1-4] Admin [1-5]"
#rule = [1, '[1-5]', [2, '[1-4]', [3, '[1-3]', []]]]
#output = Unit 3 Port 2 Admin 1
def apply_change_recursive_patern_change(s, rule):
    #print "Try to change %s" % s, 'with', rule
    new_s = s
    (i, m, t) = rule
    #print "replace %s by %s" % (r'%s' % m, str(i)), 'in', s
    s = s.replace(r'%s' % m, str(i))
    #print "And got", s
    if t == []:
        return s
    return apply_change_recursive_patern_change(s, t)


#For service generator, get dict from a _custom properties
#as _disks   C$(80%!90%),D$(80%!90%)$,E$(80%!90%)$
#return {'C' : '80%!90%', 'D' : '80%!90%', 'E' : '80%!90%'}
#And if we have a key that look like [X-Y] we will expand it
#into Y-X+1 keys
GET_KEY_VALUE_SEQUENCE_ERROR_NOERROR = 0
GET_KEY_VALUE_SEQUENCE_ERROR_SYNTAX = 1
GET_KEY_VALUE_SEQUENCE_ERROR_NODEFAULT = 2
GET_KEY_VALUE_SEQUENCE_ERROR_NODE= 3
def get_key_value_sequence(entry, default_value=None):
    #Look if we end with a "value" so a $
    #because we will have problem if we don't end
    #like it
    end_with_value = (entry[-1] == '$')
    print "End with value?", end_with_value

    conf_entry = entry
    #Here we need a special string to replace after
    long_and_random = "Z"*10
    #Now entry is a dict from outside, and inner key start with a '
    entry = "{'%s'}" % entry
    #first we make key look like C': 'blabla...
    entry = entry.replace('$(', "': '")
    #And the end of value with a '
    entry = entry.replace(')$', "'"+long_and_random)
    #Now we clean the ZZZ,D into a ,'D
    entry = entry.replace(long_and_random+",", ",'")
    #And clean the trailing ZZZ' because it's not useful, there is no key after
    entry = entry.replace(long_and_random+"'", '')

    #Now need to see the entry taht are alone, with no value
    #the last one will be a 'G'} with no value if not set, and
    #will raise an error
    if len(entry) >= 2 and not end_with_value:
        entry = entry[:-2]
        #And so add a None as value
        entry = entry + "': None}"

    #Ok we've got our dict, we can evel it (and pray)
    try:
        r = eval(entry)
    except SyntaxError:
        return (None, GET_KEY_VALUE_SEQUENCE_ERROR_SYNTAX)

    #special case : key with a , are in fact KEY1, KEY2, ... KEYN and KEY1,2 got not real value
    #only N got one
    keys_to_del = []
    keys_to_add = {}
    for key in r:
        if ',' in key:
            keys_to_del.append(key)
            value = r[key]
            elts = key.split(',')
            nb_elts = len(elts)
            non_value_keys = elts[:-1]
            for k in non_value_keys:
                keys_to_add[k] = None
            keys_to_add[elts[-1]] = value
    #clean/update what we got
    for k in keys_to_del:
        del r[k]
    for k in keys_to_add:
        r.update(keys_to_add)
    # now fill the empty values with the default value
    for key in r:
        if r[key] == None:
            if default_value == None:
                return (None, GET_KEY_VALUE_SEQUENCE_ERROR_NODEFAULT)
            else:
                r[key] = default_value

    #Now create new one but for [X-Y] matchs
    keys_to_del = []
    keys_to_add = {}
    #import time
    #t0 = time.time()
    #NodeSet = None
    if NodeSet == None:
        #The patern that will say if we have a [X-Y] key.
        pat = re.compile('\[(\d*)-(\d*)\]')

    for key in r:

        value = r[key]
        orig_key = key

        #We have no choice, we cannot use NodeSet, so we use the
        #simple regexp
        if NodeSet == None:
            m = pat.search(key)
            got_xy = (m != None)
        else: # Try to look with a nodeset check directly
            try:
                ns = NodeSet(key)
                #If we have more than 1 element, we have a xy thing
                got_xy = (len(ns) != 1)
            except NodeSetParseRangeError:
                return (None, GET_KEY_VALUE_SEQUENCE_ERROR_NODE)
                pass # go in the next key

        #Now we've got our couples of X-Y. If no void,
        #we were with a "key generator"

        if got_xy:
            #Ok 2 cases : we have the NodeSet lib or not.
            #if not, we use the dumb algo (quick, but manage less
            #cases like /N or , in paterns)
            if NodeSet == None: #us the old algo
                still_loop = True
                xy_couples = [] # will get all X-Y couples
                while still_loop:
                    m = pat.search(key)
                    if m != None: # we've find one X-Y
                        (x,y) = m.groups()
                        (x,y) = (int(x), int(y))
                        xy_couples.append((x,y))
                        #We must search if we've gotother X-Y, so
                        #we delete this one, and loop
                        key = key.replace('[%d-%d]' % (x,y), 'Z'*10)
                    else:#no more X-Y in it
                        still_loop = False

                #Now we have our xy_couples, we can manage them
                #The key was just a generator, we can remove it
                keys_to_del.append(orig_key)

                #We search all patern change rules
                rules = got_generation_rule_patern_change(xy_couples)

                #Then we apply them all to get ours final keys
                for rule in rules:
                    res = apply_change_recursive_patern_change(orig_key, rule)
                    keys_to_add[res] = value

            else:
                #The key was just a generator, we can remove it
                keys_to_del.append(orig_key)

                #We search all patern change rules
                #rules = got_generation_rule_patern_change(xy_couples)
                nodes_set = expand_xy_patern(orig_key)
                new_keys = list(nodes_set)

                #Then we apply them all to get ours final keys
                for new_key in new_keys:
                #res = apply_change_recursive_patern_change(orig_key, rule)
                    keys_to_add[new_key] = value


    #We apply it
    for k in keys_to_del:
        del r[k]
    for k in keys_to_add:
        r.update(keys_to_add)

    #t1 = time.time()
    #print "***********Diff", t1 -t0

    return (r, GET_KEY_VALUE_SEQUENCE_ERROR_NOERROR)


