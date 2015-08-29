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
import re
import copy
import sys
import os
import json

try:
    from ClusterShell.NodeSet import NodeSet, NodeSetParseRangeError
except ImportError:
    NodeSet = None

from shinken.macroresolver import MacroResolver
from shinken.log import logger

try:
    stdout_encoding = sys.stdout.encoding
    safe_stdout = (stdout_encoding == 'UTF-8')
except Exception, exp:
    logger.error('Encoding detection error= %s', exp)
    safe_stdout = False




# ########## Strings #############
# Try to print strings, but if there is an utf8 error, go in simple ascii mode
# (Like if the terminal do not have en_US.UTF8 as LANG for example)
def safe_print(*args):
    l = []
    for e in args:
        # If we got an str, go in unicode, and if we cannot print
        # utf8, go in ascii mode
        if isinstance(e, str):
            if safe_stdout:
                s = unicode(e, 'utf8', errors='ignore')
            else:
                s = e.decode('ascii', 'replace').encode('ascii', 'replace').\
                    decode('ascii', 'replace')
            l.append(s)
        # Same for unicode, but skip the unicode pass
        elif isinstance(e, unicode):
            if safe_stdout:
                s = e
            else:
                s = e.encode('ascii', 'replace')
            l.append(s)
        # Other types can be directly convert in unicode
        else:
            l.append(unicode(e))
    # Ok, now print it :)
    print u' '.join(l)


def split_semicolon(line, maxsplit=None):
    """Split a line on semicolons characters but not on the escaped semicolons
    """
    # Split on ';' character
    splitted_line = line.split(';')

    splitted_line_size = len(splitted_line)

    # if maxsplit is not specified, we set it to the number of part
    if maxsplit is None or 0 > maxsplit:
        maxsplit = splitted_line_size

    # Join parts  to the next one, if ends with a '\'
    # because we mustn't split if the semicolon is escaped
    i = 0
    while i < splitted_line_size - 1:

        # for each part, check if its ends with a '\'
        ends = splitted_line[i].endswith('\\')

        if ends:
            # remove the last character '\'
            splitted_line[i] = splitted_line[i][:-1]

        # append the next part to the current if it is not the last and the current
        # ends with '\' or if there is more than maxsplit parts
        if (ends or i >= maxsplit) and i < splitted_line_size - 1:

            splitted_line[i] = ";".join([splitted_line[i], splitted_line[i + 1]])

            # delete the next part
            del splitted_line[i + 1]
            splitted_line_size -= 1

        # increase i only if we don't have append because after append the new
        # string can end with '\'
        else:
            i += 1

    return splitted_line



# Json-ify the objects
def jsonify_r(obj):
    res = {}
    cls = obj.__class__
    if not hasattr(cls, 'properties'):
        try:
            json.dumps(obj)
            return obj
        except Exception, exp:
            return None
    properties = cls.properties.keys()
    if hasattr(cls, 'running_properties'):
        properties += cls.running_properties.keys()
    for prop in properties:
        if not hasattr(obj, prop):
            continue
        v = getattr(obj, prop)
        # Maybe the property is not jsonable
        try:
            if isinstance(v, set):
                v = list(v)
            if isinstance(v, list):
                v = sorted(v)
            json.dumps(v)
            res[prop] = v
        except Exception, exp:
            if isinstance(v, list):
                lst = []
                for _t in v:
                    t = getattr(_t.__class__, 'my_type', '')
                    if t == 'CommandCall':
                        try:
                            lst.append(_t.call)
                        except Exception:
                            pass
                        continue
                    if t and hasattr(_t, t + '_name'):
                        lst.append(getattr(_t, t + '_name'))
                    else:
                        pass
                        # print "CANNOT MANAGE OBJECT", _t, type(_t), t
                res[prop] = lst
            else:
                t = getattr(v.__class__, 'my_type', '')
                if t == 'CommandCall':
                    try:
                        res[prop] = v.call
                    except Exception:
                        pass
                    continue
                if t and hasattr(v, t + '_name'):
                    res[prop] = getattr(v, t + '_name')
                # else:
                #    print "CANNOT MANAGE OBJECT", v, type(v), t
    return res

# ################################## TIME ##################################
# @memoized
def get_end_of_day(year, month_id, day):
    end_time = (year, month_id, day, 23, 59, 59, 0, 0, -1)
    end_time_epoch = time.mktime(end_time)
    return end_time_epoch


# @memoized
def print_date(t):
    return time.asctime(time.localtime(t))


# @memoized
def get_day(t):
    return int(t - get_sec_from_morning(t))


# Same but for week day
def get_wday(t):
    t_lt = time.localtime(t)
    return t_lt.tm_wday


# @memoized
def get_sec_from_morning(t):
    t_lt = time.localtime(t)
    h = t_lt.tm_hour
    m = t_lt.tm_min
    s = t_lt.tm_sec
    return h * 3600 + m * 60 + s


# @memoized
def get_start_of_day(year, month_id, day):
    start_time = (year, month_id, day, 00, 00, 00, 0, 0, -1)
    try:
        start_time_epoch = time.mktime(start_time)
    except OverflowError:
        # Windows mktime sometimes crashes on (1970, 1, 1, ...)
        start_time_epoch = 0.0

    return start_time_epoch


# change a time in seconds like 3600 into a format: 0d 1h 0m 0s
def format_t_into_dhms_format(t):
    s = t
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    return '%sd %sh %sm %ss' % (d, h, m, s)


# ################################ Pythonization ###########################
# first change to float so manage for example 25.0 to 25
def to_int(val):
    return int(float(val))


def to_float(val):
    return float(val)


def to_char(val):
    return val[0]


def to_split(val, split_on_coma=True):
    if isinstance(val, list):
        return val
    if not split_on_coma:
        return [val]
    val = val.split(',')
    if val == ['']:
        val = []
    return val


def list_split(val, split_on_coma=True):
    if not split_on_coma:
        return val
    new_val = []
    for x in val:
        new_val.extend(x.split(','))
    return new_val


def to_best_int_float(val):
    i = int(float(val))
    f = float(val)
    # If the f is a .0 value,
    # best match is int
    if i == f:
        return i
    return f


# bool('0') = true, so...
def to_bool(val):
    if val == '1' or val == 'on' or val == 'true' or val == 'True':
        return True
    else:
        return False


def from_bool_to_string(b):
    if b:
        return '1'
    else:
        return '0'


def from_bool_to_int(b):
    if b:
        return 1
    else:
        return 0


def from_list_to_split(val):
    val = ','.join(['%s' % v for v in val])
    return val


def from_float_to_int(val):
    val = int(val)
    return val


# Functions for brok_transformations
# They take 2 parameters: ref, and a value
# ref is the item like a service, and value
# if the value to preprocess

# Just a string list of all names, with ,
def to_list_string_of_names(ref, tab):
    return ",".join([e.get_name() for e in tab])


# Just a list of names
def to_list_of_names(ref, tab):
    return [e.get_name() for e in tab]


# This will give a string if the value exists
# or '' if not
def to_name_if_possible(ref, value):
    if value:
        return value.get_name()
    return ''


# take a list of hosts and return a list
# of all host_names
def to_hostnames_list(ref, tab):
    r = []
    for h in tab:
        if hasattr(h, 'host_name'):
            r.append(h.host_name)
    return r


# Will create a dict with 2 lists:
# *services: all services of the tab
# *hosts: all hosts of the tab
def to_svc_hst_distinct_lists(ref, tab):
    r = {'hosts': [], 'services': []}
    for e in tab:
        cls = e.__class__
        if cls.my_type == 'service':
            name = e.get_dbg_name()
            r['services'].append(name)
        else:
            name = e.get_dbg_name()
            r['hosts'].append(name)
    return r


# Will expand the value with macros from the
# host/service ref before brok it
def expand_with_macros(ref, value):
    return MacroResolver().resolve_simple_macros_in_string(value, ref.get_data_for_checks())


# Just get the string name of the object
# (like for realm)
def get_obj_name(obj):
    # Maybe we do not have a real object but already a string. If so
    # return the string
    if isinstance(obj, basestring):
        return obj
    return obj.get_name()


# Same as before, but call with object,prop instead of just value
# But if we got an attribute error, return ''
def get_obj_name_two_args_and_void(obj, value):
    try:
        return value.get_name()
    except AttributeError:
        return ''


# Get the full name if there is one
def get_obj_full_name(obj):
    try:
        return obj.get_full_name()
    except Exception:
        return obj.get_name()


# return the list of keys of the custom dict
# but without the _ before
def get_customs_keys(d):
    return [k[1:] for k in d.keys()]


# return the values of the dict
def get_customs_values(d):
    return d.values()


# Checks that a parameter has an unique value. If it's a list, the last
# value set wins.
def unique_value(val):
    if isinstance(val, list):
        if val:
            return val[-1]
        else:
            return ''
    else:
        return val


# ##################### Sorting ################
def scheduler_no_spare_first(x, y):
    if x.spare and not y.spare:
        return 1
    elif x.spare and y.spare:
        return 0
    else:
        return -1


# -1 is x first, 0 equal, 1 is y first
def alive_then_spare_then_deads(x, y):
    # First are alive
    if x.alive and not y.alive:
        return -1
    if y.alive and not x.alive:
        return 0
    # if not alive both, I really don't care...
    if not x.alive and not y.alive:
        return -1
    # Ok, both are alive... now spare after no spare
    if not x.spare:
        return -1
    # x is a spare, so y must be before, even if
    # y is a spare
    if not y.spare:
        return 1
    return 0


# -1 is x first, 0 equal, 1 is y first
def sort_by_ids(x, y):
    if x.id < y.id:
        return -1
    if x.id > y.id:
        return 1
    # So is equal
    return 0


# From a tab, get the avg, min, max
# for the tab values, but not the lower ones
# and higher ones that are too distinct
# than major ones
def nighty_five_percent(t):
    t2 = copy.copy(t)
    t2.sort()

    l = len(t)

    # If void tab, wtf??
    if l == 0:
        return (None, None, None)

    t_reduce = t2
    # only take a part if we got more
    # than 100 elements, or it's a non sense
    if l > 100:
        offset = int(l * 0.05)
        t_reduce = t_reduce[offset:-offset]

    reduce_len = len(t_reduce)
    reduce_sum = sum(t_reduce)

    reduce_avg = float(reduce_sum) / reduce_len
    reduce_max = max(t_reduce)
    reduce_min = min(t_reduce)

    return (reduce_avg, reduce_min, reduce_max)


# #################### Cleaning ##############
def strip_and_uniq(tab):
    new_tab = set()
    for elt in tab:
        val = elt.strip()
        if (val != ''):
            new_tab.add(val)
    return list(new_tab)


# ################### Pattern change application (mainly for host) #######


def expand_xy_pattern(pattern):
    ns = NodeSet(str(pattern))
    if len(ns) > 1:
        for elem in ns:
            for a in expand_xy_pattern(elem):
                yield a
    else:
        yield pattern


# This function is used to generate all pattern change as
# recursive list.
# for example, for a [(1,3),(1,4),(1,5)] xy_couples,
# it will generate a 60 item list with:
# Rule: [1, '[1-5]', [1, '[1-4]', [1, '[1-3]', []]]]
# Rule: [1, '[1-5]', [1, '[1-4]', [2, '[1-3]', []]]]
# ...
def got_generation_rule_pattern_change(xy_couples):
    res = []
    xy_cpl = xy_couples
    if xy_couples == []:
        return []
    (x, y) = xy_cpl[0]
    for i in xrange(x, y + 1):
        n = got_generation_rule_pattern_change(xy_cpl[1:])
        if n != []:
            for e in n:
                res.append([i, '[%d-%d]' % (x, y), e])
        else:
            res.append([i, '[%d-%d]' % (x, y), []])
    return res


# this function apply a recursive pattern change
# generate by the got_generation_rule_pattern_change
# function.
# It take one entry of this list, and apply
# recursively the change to s like:
# s = "Unit [1-3] Port [1-4] Admin [1-5]"
# rule = [1, '[1-5]', [2, '[1-4]', [3, '[1-3]', []]]]
# output = Unit 3 Port 2 Admin 1
def apply_change_recursive_pattern_change(s, rule):
    # print "Try to change %s" % s, 'with', rule
    # new_s = s
    (i, m, t) = rule
    # print "replace %s by %s" % (r'%s' % m, str(i)), 'in', s
    s = s.replace(r'%s' % m, str(i))
    # print "And got", s
    if t == []:
        return s
    return apply_change_recursive_pattern_change(s, t)

# For service generator, get dict from a _custom properties
# as _disks   C$(80%!90%),D$(80%!90%)$,E$(80%!90%)$
# return {'C': '80%!90%', 'D': '80%!90%', 'E': '80%!90%'}
# And if we have a key that look like [X-Y] we will expand it
# into Y-X+1 keys
GET_KEY_VALUE_SEQUENCE_ERROR_NOERROR = 0
GET_KEY_VALUE_SEQUENCE_ERROR_SYNTAX = 1
GET_KEY_VALUE_SEQUENCE_ERROR_NODEFAULT = 2
GET_KEY_VALUE_SEQUENCE_ERROR_NODE = 3


def get_key_value_sequence(entry, default_value=None):
    array1 = []
    array2 = []
    conf_entry = entry

    # match a key$(value1..n)$
    keyval_pattern_txt = r"""
\s*(?P<key>[^,]+?)(?P<values>(\s*\$\(.*?\)\$\s*)*)(?:[,]|$)
"""
    keyval_pattern = re.compile('(?x)' + keyval_pattern_txt)
    # match a whole sequence of key$(value1..n)$
    all_keyval_pattern = re.compile('(?x)^(' + keyval_pattern_txt + ')+$')
    # match a single value
    value_pattern = re.compile('(?:\s*\$\((?P<val>.*?)\)\$\s*)')
    # match a sequence of values
    all_value_pattern = re.compile('^(?:\s*\$\(.*?\)\$\s*)+$')

    if all_keyval_pattern.match(conf_entry):
        for mat in re.finditer(keyval_pattern, conf_entry):
            r = {'KEY': mat.group('key')}
            # The key is in mat.group('key')
            # If there are also value(s)...
            if mat.group('values'):
                if all_value_pattern.match(mat.group('values')):
                    # If there are multiple values, loop over them
                    valnum = 1
                    for val in re.finditer(value_pattern, mat.group('values')):
                        r['VALUE' + str(valnum)] = val.group('val')
                        valnum += 1
                else:
                    # Value syntax error
                    return (None, GET_KEY_VALUE_SEQUENCE_ERROR_SYNTAX)
            else:
                r['VALUE1'] = None
            array1.append(r)
    else:
        # Something is wrong with the values. (Maybe unbalanced '$(')
        # TODO: count opening and closing brackets in the pattern
        return (None, GET_KEY_VALUE_SEQUENCE_ERROR_SYNTAX)

    # now fill the empty values with the default value
    for r in array1:
        if r['VALUE1'] is None:
            if default_value is None:
                return (None, GET_KEY_VALUE_SEQUENCE_ERROR_NODEFAULT)
            else:
                r['VALUE1'] = default_value
        r['VALUE'] = r['VALUE1']

    # Now create new one but for [X-Y] matchs
    #  array1 holds the original entries. Some of the keys may contain wildcards
    #  array2 is filled with originals and inflated wildcards

    if NodeSet is None:
        # The pattern that will say if we have a [X-Y] key.
        pat = re.compile('\[(\d*)-(\d*)\]')

    for r in array1:

        key = r['KEY']
        orig_key = r['KEY']

        # We have no choice, we cannot use NodeSet, so we use the
        # simple regexp
        if NodeSet is None:
            m = pat.search(key)
            got_xy = (m is not None)
        else:  # Try to look with a nodeset check directly
            try:
                ns = NodeSet(str(key))
                # If we have more than 1 element, we have a xy thing
                got_xy = (len(ns) != 1)
            except NodeSetParseRangeError:
                return (None, GET_KEY_VALUE_SEQUENCE_ERROR_NODE)
                pass  # go in the next key

        # Now we've got our couples of X-Y. If no void,
        # we were with a "key generator"

        if got_xy:
            # Ok 2 cases: we have the NodeSet lib or not.
            # if not, we use the dumb algo (quick, but manage less
            # cases like /N or , in patterns)
            if NodeSet is None:  # us the old algo
                still_loop = True
                xy_couples = []  # will get all X-Y couples
                while still_loop:
                    m = pat.search(key)
                    if m is not None:  # we've find one X-Y
                        (x, y) = m.groups()
                        (x, y) = (int(x), int(y))
                        xy_couples.append((x, y))
                        # We must search if we've gotother X-Y, so
                        # we delete this one, and loop
                        key = key.replace('[%d-%d]' % (x, y), 'Z' * 10)
                    else:  # no more X-Y in it
                        still_loop = False

                # Now we have our xy_couples, we can manage them

                # We search all pattern change rules
                rules = got_generation_rule_pattern_change(xy_couples)

                # Then we apply them all to get ours final keys
                for rule in rules:
                    res = apply_change_recursive_pattern_change(orig_key, rule)
                    new_r = {}
                    for key in r:
                        new_r[key] = r[key]
                    new_r['KEY'] = res
                    array2.append(new_r)

            else:
                # The key was just a generator, we can remove it
                # keys_to_del.append(orig_key)

                # We search all pattern change rules
                # rules = got_generation_rule_pattern_change(xy_couples)
                nodes_set = expand_xy_pattern(orig_key)
                new_keys = list(nodes_set)

                # Then we apply them all to get ours final keys
                for new_key in new_keys:
                    # res = apply_change_recursive_pattern_change(orig_key, rule)
                    new_r = {}
                    for key in r:
                        new_r[key] = r[key]
                    new_r['KEY'] = new_key
                    array2.append(new_r)
        else:
            # There were no wildcards
            array2.append(r)
    # t1 = time.time()
    # print "***********Diff", t1 -t0

    return (array2, GET_KEY_VALUE_SEQUENCE_ERROR_NOERROR)


# ############################## Files management #######################
# We got a file like /tmp/toto/toto2/bob.png And we want to be sure the dir
# /tmp/toto/toto2/ will really exists so we can copy it. Try to make if if need
# and return True/False if succeed
def expect_file_dirs(root, path):
    dirs = os.path.normpath(path).split('/')
    dirs = [d for d in dirs if d != '']
    # We will create all directory until the last one
    # so we are doing a mkdir -p .....
    # TODO: and windows????
    tmp_dir = root
    for d in dirs:
        _d = os.path.join(tmp_dir, d)
        logger.info('Verify the existence of file %s', _d)
        if not os.path.exists(_d):
            try:
                os.mkdir(_d)
            except Exception:
                return False
        tmp_dir = _d
    return True


# ####################### Services/hosts search filters  #######################
# Filters used in services or hosts find_by_filter method
# Return callback functions which are passed host or service instances, and
# should return a boolean value that indicates if the inscance mached the
# filter
def filter_any(name):

    def inner_filter(host):
        return True

    return inner_filter


def filter_none(name):

    def inner_filter(host):
        return False

    return inner_filter


def filter_host_by_name(name):

    def inner_filter(host):
        if host is None:
            return False
        return host.host_name == name

    return inner_filter


def filter_host_by_regex(regex):
    host_re = re.compile(regex)

    def inner_filter(host):
        if host is None:
            return False
        return host_re.match(host.host_name) is not None

    return inner_filter


def filter_host_by_group(group):

    def inner_filter(host):
        if host is None:
            return False
        return group in [g.hostgroup_name for g in host.hostgroups]

    return inner_filter


def filter_host_by_tag(tpl):

    def inner_filter(host):
        if host is None:
            return False
        return tpl in [t.strip() for t in host.tags]

    return inner_filter



def filter_service_by_name(name):

    def inner_filter(service):
        if service is None:
            return False
        return service.service_description == name

    return inner_filter


def filter_service_by_regex_name(regex):
    host_re = re.compile(regex)

    def inner_filter(service):
        if service is None:
            return False
        return host_re.match(service.service_description) is not None

    return inner_filter


def filter_service_by_host_name(host_name):

    def inner_filter(service):
        if service is None:
            return False
        return service.host_name == host_name

    return inner_filter


def filter_service_by_regex_host_name(regex):
    host_re = re.compile(regex)

    def inner_filter(service):
        if service is None:
            return False
        return host_re.match(service.host_name) is not None

    return inner_filter


def filter_service_by_hostgroup_name(group):

    def inner_filter(service):
        if service is None or service.host is None:
            return False
        return group in [g.hostgroup_name for g in service.host.hostgroups]

    return inner_filter


def filter_service_by_host_tag_name(tpl):

    def inner_filter(service):
        if service is None or service.host is None:
            return False
        return tpl in [t.strip() for t in service.host.tags]

    return inner_filter


def filter_service_by_servicegroup_name(group):

    def inner_filter(service):
        if service is None:
            return False
        return group in [g.servicegroup_name for g in service.servicegroups]

    return inner_filter


def filter_host_by_bp_rule_label(label):

    def inner_filter(host):
        if host is None:
            return False
        return label in host.labels

    return inner_filter


def filter_service_by_host_bp_rule_label(label):

    def inner_filter(service):
        if service is None or service.host is None:
            return False
        return label in service.host.labels

    return inner_filter


def filter_service_by_bp_rule_label(label):
    def inner_filter(service):
        if service is None:
            return False
        return label in service.labels

    return inner_filter


def is_complex_expr(expr):
    for m in '()&|!*':
        if m in expr:
            return True
    return False


def get_exclude_match_expr(pattern):
    if pattern == "*":
        return lambda d: True
    elif pattern.startswith("r:"):
        reg = re.compile(pattern[2:])
        return reg.match
    else:
        return lambda d: d == pattern
