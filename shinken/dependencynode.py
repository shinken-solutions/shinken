#!/usr/bin/env python

# -*- coding: utf-8 -*-

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

import re
from shinken.log import logger

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
        return "Op:'%s' Val:'%s' Sons:'[%s]' IsNot:'%s'" % (self.operand, self.of_values, ','.join([str(s) for s in self.sons]), self.not_value)


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
        #print "Ask state of me", self

        # If we are a host or a service, wee just got the host/service
        # hard state
        if self.operand in ['host', 'service']:
            state = self.sons[0].last_hard_state_id
            #print "Get the hard state (%s) for the object %s" % (state, self.sons[0].get_name())
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

        # First we get the state of all our sons
        states = []
        for s in self.sons:
            st = s.get_state()
            states.append(st)

        # We will surely need the worst state
        worst_state = max(states)

        # Suggestion: What about returning min(states) for the | operand?
        # We don't need make a difference between an 0 and another no?
        # If you do so, it may be more efficient with lots of services
        # or host to return OK, but otherwise I can't see the reason for
        # this subcase.

        # We look for the better state but not OK/UP
        no_ok = [s for s in states if s != 0]
        if len(no_ok) != 0:
            best_not_good = min(no_ok)

        # Now look at the rule. For a or
        if self.operand == '|':
            if 0 in states:
                if self.not_value:
                    return self.get_reverse_state(0)
                #print "We find a OK/UP match in an OR", states
                return 0
            # no ok/UP-> return worst state
            else:
                if self.not_value:
                    return self.get_reverse_state(best_not_good)
                #print "I send the best not good state...in an OR", best_not_good, states
                return best_not_good

        # With an AND, we just send the worst state
        if self.operand == '&':
            if self.not_value:
                return self.get_reverse_state(worst_state)
            #print "We raise worst state for a AND", worst_state,states
            return worst_state

        # Ok we've got a 'of:' rule
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

        #print "NB:", nb_ok, nb_warn, nb_crit

        # Ok and Crit apply with their own values
        # Warn can apply with warn or crit values
        # so a W C can raise a Warning, but not enough for
        # a critical
        if nb_search_ok.endswith('%'):
            nb_search_ok = int(nb_search_ok[:-1])
            ok_apply = float(nb_ok) / nb_sons * 100 >= nb_search_ok
        else:
            ok_apply = nb_ok >= int(nb_search_ok)

        if nb_search_warn.endswith('%'):
            nb_search_warn = int(nb_search_warn[:-1])
            warn_apply = float(nb_warn) / nb_sons * 100 >= nb_search_warn
        else:
            warn_apply = nb_warn + nb_crit >= int(nb_search_warn)

        if nb_search_crit.endswith('%'):
            nb_search_crit = int(nb_search_crit[:-1])
            crit_apply = float(nb_crit) / nb_sons * 100 >= nb_search_crit
        else:
            crit_apply = nb_crit >= int(nb_search_crit)

        #print "What apply?", ok_apply, warn_apply, crit_apply

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
            #print "Is mul, send 0"
            if self.not_value:
                return self.get_reverse_state(0)
            return 0
        else:
            #print "not mul, return worst", worse_state
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
    def __init__(self):
        pass

    # the () will be eval in a recursiv way, only one level of ()
    def eval_cor_pattern(self, pattern, hosts, services):
        pattern = pattern.strip()
        #print "***** EVAL ", pattern
        complex_node = False

        # Look if it's a complex pattern (with rule) or
        # if it's a leaf ofit, like a host/service
        for m in '()+&|':
            if m in pattern:
                complex_node = True

        is_of_nb = False

        node = DependencyNode()
        p = "^(\d+%?),*(\d*%?),*(\d*%?) *of: *(.+)"
        r = re.compile(p)
        m = r.search(pattern)
        if m is not None:
            #print "Match the of: thing N=", m.groups()
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

        #print "Is so complex?", pattern, complex_node

        # if it's a single host/service
        if not complex_node:
            #print "Try to find?", pattern
            # If it's a not value, tag the node and find
            # the name without this ! operator
            if pattern.startswith('!'):
                node.not_value = True
                pattern = pattern[1:]
            # Is the pattern an host expression to be expanded?
            if re.match("^[grp]+:", pattern):
                # o is just extracted its attributes, then trashed.
                o = self.expand_hosts_expression(pattern, hosts, services)
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
                    node.configuration_errors.append(error)
            return node
        #else:
        #    print "Is complex"

        in_par = False
        tmp = ''
        son_is_not = False # We keep is the next son will ne not or not
        stacked_par = 0
        for c in pattern:
            #print "MATCHING", c, pattern
            if c == '&' or c == '|':
                # Maybe we are in a par, if so, just stack it
                if in_par:
                    #print " & in a par, just staking it"
                    tmp += c
                else:
                    # Oh we got a real cut in an expression, if so, cut it
                    #print "REAL & for cutting"
                    tmp = tmp.strip()
                    # Look at the rule viability
                    current_rule = node.operand
                    if current_rule is not None and current_rule != 'of:' and c != current_rule:
                        # Should be logged as a warning / info? :)
                        return None

                    if current_rule != 'of:':
                        node.operand = c
                    if tmp != '':
                        #print "Will analyse the current str", tmp
                        o = self.eval_cor_pattern(tmp, hosts, services)
                        # Maybe our son was notted
                        if son_is_not:
                            o.not_value = True
                            son_is_not = False
                        node.sons.append(o)
                    tmp = ''
                    continue

            elif c == '(':
                stacked_par += 1
                #print "INCREASING STACK TO", stacked_par

                in_par = True
                tmp = tmp.strip()
                # Maybe we just start a par, but we got some things in tmp
                # that should not be good in fact !
                if stacked_par == 1 and tmp != '':
                    #TODO : real error
                    print "ERROR : bad expression near", tmp
                    continue

                # If we are already in a par, add this (
                # but not if it's the first one so
                if stacked_par > 1:
                    tmp += c
                    #o = self.eval_cor_pattern(tmp)
                    #print "1( I've %s got new sons" % pattern , o
                    #node.sons.append(o)

            elif c == ')':
                #print "Need closeing a sub expression?", tmp
                stacked_par -= 1

                if stacked_par < 0:
                    # TODO : real error
                    print "Error : bad expression near", tmp, "too much ')'"
                    continue

                if stacked_par == 0:
                    #print "THIS is closing a sub compress expression", tmp
                    tmp = tmp.strip()
                    o = self.eval_cor_pattern(tmp, hosts, services)
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
            # Manage the NOT for an expression. If we are in a starting bloc, put as
            # a NOT node, but if inside a bloc, don't
            elif c == '!':
                if stacked_par == 0:
                    son_is_not = True
                    # DO NOT keep the c in tmp, we consumed it
                else:
                    tmp += c
            # Maybe it's a classic character, if so, continue
            else:
                tmp += c

        # Be sure to manage the trainling part when the line is done
        tmp = tmp.strip()
        if tmp != '':
            #print "Managing trainling part", tmp
            o = self.eval_cor_pattern(tmp, hosts, services)
            # Maybe our son was notted
            if son_is_not:
                o.not_value = True
                son_is_not = False
            #print "4end I've %s got new sons" % pattern , o
            node.sons.append(o)


        # We got our nodes, so we can update 0 values of of_values
        # with the number of sons
        node.switch_zeros_of_values()

        #print "End, tmp", tmp
        #print "R %s:" % pattern
        #print "Node:", node
        return node



    # We've got an object, like h1,db1 that mean the
    # db1 service of the host db1, or just h1, that mean
    # the host h1.
    def find_object(self, pattern, hosts, services):
        #print "Finding object", pattern
        obj = None
        error = None
        is_service = False
        # h_name, service_desc are , separated
        elts = pattern.split(',')
        host_name = elts[0].strip()
        # Look if we have a service
        if len(elts) > 1:
            is_service = True
            service_description = elts[1].strip()
        if is_service:
            obj = services.find_srv_by_name_and_hostname(host_name, service_description)
            if not obj:
                error = "Business rule uses unknown service %s/%s" % (host_name, service_description)
        else:
            obj = hosts.find_by_name(host_name)
            if not obj:
                error = "Business rule uses unknown host %s" % (host_name,)
        return obj, error



    # Tries to expand a host expression into a dependency node tree using
    # hostgroup membership or regex on host name as host selector.
    # Returns a DependencyNode tree.
    def expand_hosts_expression(self, pattern, hosts, services):
        error = None
        node = DependencyNode()
        node.operand = '&'
        elts = pattern.split(',')
        # Flags is the left part of the first : charcter
        flags = elts[0].strip().split(":")[0]
        # Name is the right part of the first : charcter
        name = ":".join(elts[0].strip().split(":")[1:])
        permissive = "p" in flags

        # Look if we have a service
        if len(elts) > 1:
            got_service = True
            service_description = ",%s" % elts[1].strip()
        else:
            got_service = False
            service_description = ""

        if "g" in flags:
            expanded_hosts, error = self.lookup_hosts_by_group(name, hosts)
        elif "r" in flags:
            expanded_hosts, error = self.lookup_hosts_by_regex(name, hosts)
        else:
            error = "Business rule uses unknown host expansion type"

        if error is not None:
            node.configuration_errors.append(error)
            return node

        for host_name in expanded_hosts:
            expr = "%s%s" % (host_name, service_description)
            o = self.eval_cor_pattern(expr, hosts, services)

            if not o.is_valid():
                if got_service is True and permissive is True:
                    # Invalid node is not added (error is ignored).
                    logger.warning("Business rule got an unknown service for %s. Ignored." % host_name)
                else:
                    # Add the invalid node for error to be reported by arbiter.
                    node.sons.append(o)
            else:
                node.sons.append(o)

        return node



    # Looks for hosts having specified group name in their hostgroups.
    # Returns a list of Host objects and the error message if error an occurred.
    def lookup_hosts_by_group(self, group, hosts):
        error = None
        expanded_hosts = [h.host_name for h in hosts if group in [g.hostgroup_name for g in h.hostgroups]]

        if not expanded_hosts:
            error = "Business rule uses unknown or empty hostgroup %s" % group

        return expanded_hosts, error



    # Looks for hosts wchich name matches specified regex.
    # Returns a list of Host objects and the error message if error an occurred.
    def lookup_hosts_by_regex(self, pattern, hosts):
        error = None
        expanded_hosts = []

        try:
            host_re = re.compile(pattern)
            expanded_hosts = [h.host_name for h in hosts if host_re.match(h.host_name)]

            if not expanded_hosts:
                error = "Business rule uses regex that no host_name matches: %s" % pattern

        except re.error, e:
            error = "Business rule uses invalid regex %s: %s" % (pattern, e)

        return expanded_hosts, error
