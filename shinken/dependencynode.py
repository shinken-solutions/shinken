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

import re
from shinken.util import filter_any, filter_none
from shinken.util import filter_host_by_name, filter_host_by_regex, filter_host_by_group,\
    filter_host_by_tag
from shinken.util import filter_service_by_name
from shinken.util import filter_service_by_regex_name
from shinken.util import filter_service_by_regex_host_name
from shinken.util import filter_service_by_host_name
from shinken.util import filter_service_by_bp_rule_label
from shinken.util import filter_service_by_hostgroup_name
from shinken.util import filter_service_by_host_tag_name
from shinken.util import filter_service_by_servicegroup_name
from shinken.util import filter_host_by_bp_rule_label
from shinken.util import filter_service_by_host_bp_rule_label


"""
Here is a node class for dependency_node(s) and a factory to create them
"""
class DependencyNode(object):
    def __init__(self):
        self.operand = None
        self.sons = []
        # Of: values are a triple OK,WARN,CRIT
        self.of_values = ('0', '0', '0')
        self.is_of_mul = False
        self.configuration_errors = []
        self.not_value = False

    def __str__(self):
        return "Op:'%s' Val:'%s' Sons:'[%s]' IsNot:'%s'" % (self.operand, self.of_values,
                                                            ','.join([str(s) for s in self.sons]),
                                                            self.not_value)


    def get_reverse_state(self, state):
        # Warning is still warning
        if state == 1:
            return 1
        if state == 0:
            return 2
        if state == 2:
            return 0
        # should not go here...
        return state


    # We will get the state of this node, by looking at the state of
    # our sons, and apply our operand
    def get_state(self):
        # print "Ask state of me", self

        # If we are a host or a service, wee just got the host/service
        # hard state
        if self.operand in ['host', 'service']:
            return self.get_simple_node_state()
        else:
            return self.get_complex_node_state()


    # Returns a simple node direct state (such as a host or a service). No
    # calculation is needed
    def get_simple_node_state(self):
        state = self.sons[0].last_hard_state_id
        # print "Get the hard state (%s) for the object %s" % (state, self.sons[0].get_name())
        # Make DOWN look as CRITICAL (2 instead of 1)
        if self.operand == 'host' and state == 1:
            state = 2
        # Maybe we are a NOT node, so manage this
        if self.not_value:
            # We inverse our states
            if self.operand == 'host' and state == 1:
                return 0
            if self.operand == 'host' and state == 0:
                return 1
            # Critical -> OK
            if self.operand == 'service' and state == 2:
                return 0
            # OK -> CRITICAL (warning is untouched)
            if self.operand == 'service' and state == 0:
                return 2
        return state


    # Calculates a complex node state based on its sons state, and its operator
    def get_complex_node_state(self):
        if self.operand == '|':
            return self.get_complex_or_node_state()

        elif self.operand == '&':
            return self.get_complex_and_node_state()

        #  It's an Xof rule
        else:
            return self.get_complex_xof_node_state()


    # Calculates a complex node state with an | operand
    def get_complex_or_node_state(self):
        # First we get the state of all our sons
        states = [s.get_state() for s in self.sons]
        # Next we calculate the best state
        best_state = min(states)
        # Then we handle eventual not value
        if self.not_value:
            return self.get_reverse_state(best_state)
        return best_state


    # Calculates a complex node state with an & operand
    def get_complex_and_node_state(self):
        # First we get the state of all our sons
        states = [s.get_state() for s in self.sons]
        # Next we calculate the worst state
        if 2 in states:
            worst_state = 2
        else:
            worst_state = max(states)
        # Then we handle eventual not value
        if self.not_value:
            return self.get_reverse_state(worst_state)
        return worst_state


    # Calculates a complex node state with an Xof operand
    def get_complex_xof_node_state(self):
        # First we get the state of all our sons
        states = [s.get_state() for s in self.sons]

        # We search for OK, WARN or CRIT applications
        # And we will choice between them
        nb_search_ok = self.of_values[0]
        nb_search_warn = self.of_values[1]
        nb_search_crit = self.of_values[2]

        # We look for each application
        nb_sons = len(states)
        nb_ok = len([s for s in states if s == 0])
        nb_warn = len([s for s in states if s == 1])
        nb_crit = len([s for s in states if s == 2])

        # print "NB:", nb_ok, nb_warn, nb_crit

        # Ok and Crit apply with their own values
        # Warn can apply with warn or crit values
        # so a W C can raise a Warning, but not enough for
        # a critical
        def get_state_for(nb_tot, nb_real, nb_search):
            if nb_search.endswith('%'):
                nb_search = int(nb_search[:-1])
                if nb_search < 0:
                    # nb_search is negative, so +
                    nb_search = max(100 + nb_search, 0)
                apply_for = float(nb_real) / nb_tot * 100 >= nb_search
            else:
                nb_search = int(nb_search)
                if nb_search < 0:
                    # nb_search is negative, so +
                    nb_search = max(nb_tot + nb_search, 0)
                apply_for = nb_real >= nb_search
            return apply_for

        ok_apply = get_state_for(nb_sons, nb_ok, nb_search_ok)
        warn_apply = get_state_for(nb_sons, nb_warn + nb_crit, nb_search_warn)
        crit_apply = get_state_for(nb_sons, nb_crit, nb_search_crit)

        # print "What apply?", ok_apply, warn_apply, crit_apply

        # return the worst state that apply
        if crit_apply:
            if self.not_value:
                return self.get_reverse_state(2)
            return 2

        if warn_apply:
            if self.not_value:
                return self.get_reverse_state(1)
            return 1

        if ok_apply:
            if self.not_value:
                return self.get_reverse_state(0)
            return 0

        # Maybe even OK is not possible, if so, it depends if the admin
        # ask a simple form Xof: or a multiple one A,B,Cof:
        # the simple should give OK, the mult should give the worst state
        if self.is_of_mul:
            # print "Is mul, send 0"
            if self.not_value:
                return self.get_reverse_state(0)
            return 0
        else:
            # print "not mul, return worst", worse_state
            if 2 in states:
                worst_state = 2
            else:
                worst_state = max(states)
            if self.not_value:
                return self.get_reverse_state(worst_state)
            return worst_state


    # return a list of all host/service in our node and below
    def list_all_elements(self):
        r = []

        # We are a host/service
        if self.operand in ['host', 'service']:
            return [self.sons[0]]

        for s in self.sons:
            r.extend(s.list_all_elements())

        # and uniq the result
        return list(set(r))


    # If we are a of: rule, we can get some 0 in of_values,
    # if so, change them with NB sons instead
    def switch_zeros_of_values(self):
        nb_sons = len(self.sons)
        # Need a list for assignment
        self.of_values = list(self.of_values)
        for i in [0, 1, 2]:
            if self.of_values[i] == '0':
                self.of_values[i] = str(nb_sons)
        self.of_values = tuple(self.of_values)


    # Check for empty (= not found) leaf nodes
    def is_valid(self):

        valid = True
        if not self.sons:
            valid = False
        else:
            for s in self.sons:
                if isinstance(s, DependencyNode) and not s.is_valid():
                    self.configuration_errors.extend(s.configuration_errors)
                    valid = False
        return valid



""" TODO: Add some comment about this class for the doc"""
class DependencyNodeFactory(object):

    host_flags = "grlt"
    service_flags = "grl"

    def __init__(self, bound_item):
        self.bound_item = bound_item


    # the () will be eval in a recursiv way, only one level of ()
    def eval_cor_pattern(self, pattern, hosts, services, running=False):
        pattern = pattern.strip()
        # print "***** EVAL ", pattern
        complex_node = False

        # Look if it's a complex pattern (with rule) or
        # if it's a leaf ofit, like a host/service
        for m in '()&|':
            if m in pattern:
                complex_node = True

        # If it's a simple node, evaluate it directly
        if complex_node is False:
            return self.eval_simple_cor_pattern(pattern, hosts, services, running)
        else:
            return self.eval_complex_cor_pattern(pattern, hosts, services, running)


    # Checks if an expression is an Xof pattern, and parses its components if
    # so. In such a case, once parsed, returns the cleaned patten.
    def eval_xof_pattern(self, node, pattern):
        p = "^(-?\d+%?),*(-?\d*%?),*(-?\d*%?) *of: *(.+)"
        r = re.compile(p)
        m = r.search(pattern)
        if m is not None:
            # print "Match the of: thing N=", m.groups()
            node.operand = 'of:'
            g = m.groups()
            # We can have a Aof: rule, or a multiple A,B,Cof: rule.
            mul_of = (g[1] != u'' and g[2] != u'')
            # If multi got (A,B,C)
            if mul_of:
                node.is_of_mul = True
                node.of_values = (g[0], g[1], g[2])
            else:  # if not, use A,0,0, we will change 0 after to put MAX
                node.of_values = (g[0], '0', '0')
            pattern = m.groups()[3]
        return pattern


    # Evaluate a complex correlation expression, such as an &, |, nested
    # expressions in par, and so on.
    def eval_complex_cor_pattern(self, pattern, hosts, services, running=False):
        node = DependencyNode()
        pattern = self.eval_xof_pattern(node, pattern)

        in_par = False
        tmp = ''
        son_is_not = False  # We keep is the next son will be not or not
        stacked_par = 0
        for c in pattern:
            if c == '(':
                stacked_par += 1
                # print "INCREASING STACK TO", stacked_par

                in_par = True
                tmp = tmp.strip()
                # Maybe we just start a par, but we got some things in tmp
                # that should not be good in fact !
                if stacked_par == 1 and tmp != '':
                    # TODO : real error
                    print "ERROR : bad expression near", tmp
                    continue

                # If we are already in a par, add this (
                # but not if it's the first one so
                if stacked_par > 1:
                    tmp += c

            elif c == ')':
                # print "Need closeing a sub expression?", tmp
                stacked_par -= 1

                if stacked_par < 0:
                    # TODO : real error
                    print "Error : bad expression near", tmp, "too much ')'"
                    continue

                if stacked_par == 0:
                    # print "THIS is closing a sub compress expression", tmp
                    tmp = tmp.strip()
                    o = self.eval_cor_pattern(tmp, hosts, services, running)
                    # Maybe our son was notted
                    if son_is_not:
                        o.not_value = True
                        son_is_not = False
                    node.sons.append(o)
                    in_par = False
                    # OK now clean the tmp so we start clean
                    tmp = ''
                    continue

                # ok here we are still in a huge par, we just close one sub one
                tmp += c

            # Expressions in par will be parsed in a sub node after. So just
            # stack pattern
            elif in_par:
                tmp += c

            # Until here, we're not in par

            # Manage the NOT for an expression. Only allow ! at the beginning
            # of a host or a host,service expression.
            elif c == '!':
                tmp = tmp.strip()
                if tmp and tmp[0] != '!':
                    print "Error : bad expression near", tmp, "wrong position for '!'"
                    continue
                # Flags next node not state
                son_is_not = True
                # DO NOT keep the c in tmp, we consumed it

            # print "MATCHING", c, pattern
            elif c == '&' or c == '|':
                # Oh we got a real cut in an expression, if so, cut it
                # print "REAL & for cutting"
                tmp = tmp.strip()
                # Look at the rule viability
                if node.operand is not None and node.operand != 'of:' and c != node.operand:
                    # Should be logged as a warning / info? :)
                    return None

                if node.operand != 'of:':
                    node.operand = c
                if tmp != '':
                    # print "Will analyse the current str", tmp
                    o = self.eval_cor_pattern(tmp, hosts, services, running)
                    # Maybe our son was notted
                    if son_is_not:
                        o.not_value = True
                        son_is_not = False
                    node.sons.append(o)
                tmp = ''

            # Maybe it's a classic character or we're in par, if so, continue
            else:
                tmp += c

        # Be sure to manage the trainling part when the line is done
        tmp = tmp.strip()
        if tmp != '':
            # print "Managing trainling part", tmp
            o = self.eval_cor_pattern(tmp, hosts, services, running)
            # Maybe our son was notted
            if son_is_not:
                o.not_value = True
                son_is_not = False
            # print "4end I've %s got new sons" % pattern , o
            node.sons.append(o)

        # We got our nodes, so we can update 0 values of of_values
        # with the number of sons
        node.switch_zeros_of_values()

        return node


    # Evaluate a simple correlation expression, such as a host, a host + a
    # service, or expand a host or service expression.
    def eval_simple_cor_pattern(self, pattern, hosts, services, running=False):
        node = DependencyNode()
        pattern = self.eval_xof_pattern(node, pattern)

        # print "Try to find?", pattern
        # If it's a not value, tag the node and find
        # the name without this ! operator
        if pattern.startswith('!'):
            node.not_value = True
            pattern = pattern[1:]
        # Is the pattern an expression to be expanded?
        if re.search(r"^([%s]+|\*):" % self.host_flags, pattern) or \
                re.search(r",\s*([%s]+:.*|\*)$" % self.service_flags, pattern):
            # o is just extracted its attributes, then trashed.
            o = self.expand_expression(pattern, hosts, services, running)
            if node.operand != 'of:':
                node.operand = '&'
            node.sons.extend(o.sons)
            node.configuration_errors.extend(o.configuration_errors)
            node.switch_zeros_of_values()
        else:
            node.operand = 'object'
            obj, error = self.find_object(pattern, hosts, services)
            if obj is not None:
                # Set host or service
                node.operand = obj.__class__.my_type
                node.sons.append(obj)
            else:
                if running is False:
                    node.configuration_errors.append(error)
                else:
                    # As business rules are re-evaluated at run time on
                    # each scheduling loop, if the rule becomes invalid
                    # because of a badly written macro modulation, it
                    # should be notified upper for the error to be
                    # displayed in the check output.
                    raise Exception(error)
        return node


    # We've got an object, like h1,db1 that mean the
    # db1 service of the host db1, or just h1, that mean
    # the host h1.
    def find_object(self, pattern, hosts, services):
        # print "Finding object", pattern
        obj = None
        error = None
        is_service = False
        # h_name, service_desc are , separated
        elts = pattern.split(',')
        host_name = elts[0].strip()
        # If host_name is empty, use the host_name the business rule is bound to
        if not host_name:
            host_name = self.bound_item.host_name
        # Look if we have a service
        if len(elts) > 1:
            is_service = True
            service_description = elts[1].strip()
        if is_service:
            obj = services.find_srv_by_name_and_hostname(host_name, service_description)
            if not obj:
                error = "Business rule uses unknown service %s/%s"\
                        % (host_name, service_description)
        else:
            obj = hosts.find_by_name(host_name)
            if not obj:
                error = "Business rule uses unknown host %s" % (host_name,)
        return obj, error


    # Tries to expand a host or service expression into a dependency node tree
    # using (host|service)group membership, regex, or labels as item selector.
    def expand_expression(self, pattern, hosts, services, running=False):
        error = None
        node = DependencyNode()
        node.operand = '&'
        elts = [e.strip() for e in pattern.split(',')]
        # If host_name is empty, use the host_name the business rule is bound to
        if not elts[0]:
            elts[0] = self.bound_item.host_name
        filters = []
        # Looks for hosts/services using appropriate filters
        try:
            if len(elts) > 1:
                # We got a service expression
                host_expr, service_expr = elts
                filters.extend(self.get_srv_host_filters(host_expr))
                filters.extend(self.get_srv_service_filters(service_expr))
                items = services.find_by_filter(filters)
            else:
                # We got a host expression
                host_expr = elts[0]
                filters.extend(self.get_host_filters(host_expr))
                items = hosts.find_by_filter(filters)
        except re.error, e:
            error = "Business rule uses invalid regex %s: %s" % (pattern, e)
        else:
            if not items:
                error = "Business rule got an empty result for pattern %s" % pattern

        # Checks if we got result
        if error:
            if running is False:
                node.configuration_errors.append(error)
            else:
                # As business rules are re-evaluated at run time on
                # each scheduling loop, if the rule becomes invalid
                # because of a badly written macro modulation, it
                # should be notified upper for the error to be
                # displayed in the check output.
                raise Exception(error)
            return node

        # Creates dependency node subtree
        for item in items:
            # Creates a host/service node
            son = DependencyNode()
            son.operand = item.__class__.my_type
            son.sons.append(item)
            # Appends it to wrapping node
            node.sons.append(son)

        node.switch_zeros_of_values()
        return node


    # Generates filter list on a hosts host_name
    def get_host_filters(self, expr):
        if expr == "*":
            return [filter_any]
        match = re.search(r"^([%s]+):(.*)" % self.host_flags, expr)

        if match is None:
            return [filter_host_by_name(expr)]
        flags, expr = match.groups()
        if "g" in flags:
            return [filter_host_by_group(expr)]
        elif "r" in flags:
            return [filter_host_by_regex(expr)]
        elif "l" in flags:
            return [filter_host_by_bp_rule_label(expr)]
        elif "t" in flags:
            return [filter_host_by_tag(expr)]
        else:
            return [filter_none]


    # Generates filter list on services host_name
    def get_srv_host_filters(self, expr):
        if expr == "*":
            return [filter_any]
        match = re.search(r"^([%s]+):(.*)" % self.host_flags, expr)
        if match is None:
            return [filter_service_by_host_name(expr)]
        flags, expr = match.groups()

        if "g" in flags:
            return [filter_service_by_hostgroup_name(expr)]
        elif "r" in flags:
            return [filter_service_by_regex_host_name(expr)]
        elif "l" in flags:
            return [filter_service_by_host_bp_rule_label(expr)]
        elif "t" in flags:
            return [filter_service_by_host_tag_name(expr)]
        else:
            return [filter_none]


    # Generates filter list on services service_description
    def get_srv_service_filters(self, expr):
        if expr == "*":
            return [filter_any]
        match = re.search(r"^([%s]+):(.*)" % self.service_flags, expr)
        if match is None:
            return [filter_service_by_name(expr)]
        flags, expr = match.groups()

        if "g" in flags:
            return [filter_service_by_servicegroup_name(expr)]
        elif "r" in flags:
            return [filter_service_by_regex_name(expr)]
        elif "l" in flags:
            return [filter_service_by_bp_rule_label(expr)]
        else:
            return [filter_none]
