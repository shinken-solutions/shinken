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

from shinken.util import strip_and_uniq


"""
Here is a node class for complex_expression(s) and a factory to create them
"""

class ComplexExpressionNode(object):
    def __init__(self):
        self.operand = None
        self.sons = []
        self.configuration_errors = []
        self.not_value = False
        # If leaf, the content will be the hostgroup or hosts
        # that are selected with this node
        self.leaf = False
        self.content = None

    def __str__(self):
        if not self.leaf:
            return "Op:'%s' Leaf:%s Sons:'[%s] IsNot:%s'" % \
                   (self.operand, self.leaf, ','.join([str(s) for s in self.sons]), self.not_value)
        else:
            return 'IS LEAF %s' % self.content

    def resolve_elements(self):
        # If it's a leaf, we just need to dump a set with the content of the node
        if self.leaf:
            # print "Is a leaf", self.content
            if not self.content:
                return set()

            return set(self.content)


        # first got the not ones in a list, and the other in the other list
        not_nodes = [s for s in self.sons if s.not_value]
        positiv_nodes = [s for s in self.sons if not s.not_value]  # ok a not not is hard to read..

        # print "Not nodes", not_nodes
        # print "Positiv nodes", positiv_nodes

        # By default we are using a OR rule
        if not self.operand:
            self.operand = '|'

        res = set()

        # print "Will now merge all of this", self.operand

        # The operand will change the positiv loop only
        i = 0
        for n in positiv_nodes:
            node_members = n.resolve_elements()
            if self.operand == '|':
                # print "OR rule", node_members
                res = res.union(node_members)
            elif self.operand == '&':
                # print "AND RULE", node_members
                # The first elements of an AND rule should be used
                if i == 0:
                    res = node_members
                else:
                    res = res.intersection(node_members)
            i += 1

        # And we finally remove all NOT elements from the result
        for n in not_nodes:
            node_members = n.resolve_elements()
            res = res.difference(node_members)
        return res

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
class ComplexExpressionFactory(object):
    def __init__(self, ctx='hostgroups', grps=None, all_elements=None):
        self.ctx = ctx
        self.grps = grps
        self.all_elements = all_elements

    # the () will be eval in a recursiv way, only one level of ()
    def eval_cor_pattern(self, pattern):
        pattern = pattern.strip()
        # print "eval_cor_pattern::", pattern
        complex_node = False

        # Look if it's a complex pattern (with rule) or
        # if it's a leaf ofit, like a host/service
        for m in '()+&|,':
            if m in pattern:
                complex_node = True

        node = ComplexExpressionNode()
        # print "Is so complex?", complex_node, pattern, node

        # if it's a single expression like !linux or production
        # we will get the objects from it and return a leaf node
        if not complex_node:
            # If it's a not value, tag the node and find
            # the name without this ! operator
            if pattern.startswith('!'):
                node.not_value = True
                pattern = pattern[1:]

            node.operand = self.ctx
            node.leaf = True
            obj, error = self.find_object(pattern)
            if obj is not None:
                node.content = obj
            else:
                node.configuration_errors.append(error)
            return node

        in_par = False
        tmp = ''
        stacked_par = 0
        for c in pattern:
            # print "MATCHING", c
            if c == ',' or c == '|':
                # Maybe we are in a par, if so, just stack it
                if in_par:
                    # print ", in a par, just staking it"
                    tmp += c
                else:
                    # Oh we got a real cut in an expression, if so, cut it
                    # print "REAL , for cutting"
                    tmp = tmp.strip()
                    node.operand = '|'
                    if tmp != '':
                        # print "Will analyse the current str", tmp
                        o = self.eval_cor_pattern(tmp)
                        node.sons.append(o)
                    tmp = ''

            elif c == '&' or c == '+':
                # Maybe we are in a par, if so, just stack it
                if in_par:
                    # print " & in a par, just staking it"
                    tmp += c
                else:
                    # Oh we got a real cut in an expression, if so, cut it
                    # print "REAL & for cutting"
                    tmp = tmp.strip()
                    node.operand = '&'
                    if tmp != '':
                        # print "Will analyse the current str", tmp
                        o = self.eval_cor_pattern(tmp)
                        node.sons.append(o)
                    tmp = ''

            elif c == '(':
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
                    # o = self.eval_cor_pattern(tmp)
                    # print "1( I've %s got new sons" % pattern , o
                    # node.sons.append(o)

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
                    o = self.eval_cor_pattern(tmp)
                    node.sons.append(o)
                    in_par = False
                    # OK now clean the tmp so we start clean
                    tmp = ''
                    continue

                # ok here we are still in a huge par, we just close one sub one
                tmp += c
            # Maybe it's a classic character, if so, continue
            else:
                tmp += c

        # Be sure to manage the trainling part when the line is done
        tmp = tmp.strip()
        if tmp != '':
            # print "Managing trainling part", tmp
            o = self.eval_cor_pattern(tmp)
            # print "4end I've %s got new sons" % pattern , o
            node.sons.append(o)

        # print "End, tmp", tmp
        # print "R %s:" % pattern, node
        return node

    # We've got an object, like super-grp, so we should link th group here
    def find_object(self, pattern):
        obj = None
        error = None
        pattern = pattern.strip()

        if pattern == '*':
            obj = [h.host_name for h in self.all_elements.items.values()
                   if getattr(h, 'host_name', '') != '' and not h.is_tpl()]
            return obj, error


        # Ok a more classic way

        # print "GRPS", self.grps

        if self.ctx == 'hostgroups':
            # Ok try to find this hostgroup
            hg = self.grps.find_by_name(pattern)
            # Maybe it's an known one?
            if not hg:
                error = "Error : cannot find the %s of the expression '%s'" % (self.ctx, pattern)
                return hg, error
            # Ok the group is found, get the elements!
            elts = hg.get_hosts()
            elts = strip_and_uniq(elts)

            # Maybe the hostgroup memebrs is '*', if so expand with all hosts
            if '*' in elts:
                elts.extend([h.host_name for h in self.all_elements.items.values()
                             if getattr(h, 'host_name', '') != '' and not h.is_tpl()])
                # And remove this strange hostname too :)
                elts.remove('*')
            return elts, error

        else:  # templates
            obj = self.grps.find_hosts_that_use_template(pattern)

        return obj, error
